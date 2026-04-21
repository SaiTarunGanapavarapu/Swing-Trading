from datetime import datetime
import time

import pandas as pd

from .cache import isCacheFresh, loadDataCache, saveDataCache, stripCacheMeta
from .fetcher import fetchStockData
from .models import RunOptions
from .scoring_engine import scoreStock


class ScreeningService:
    """Run the screener engine with cache-aware options."""

    def run(self, symbols: list[str], options: RunOptions) -> pd.DataFrame:
        results = []
        useCache = options.cacheMode != "off"
        cacheData = loadDataCache(options.cacheFile) if useCache else {}
        cacheDirty = False

        for index, symbol in enumerate(symbols, start=1):
            source = "fetch"
            if not options.quiet:
                print(f"  [{index}/{len(symbols)}] Fetching {symbol}...", end=" ", flush=True)

            cachedRow = cacheData.get(symbol) if useCache else None

            shouldUseCache = False
            if cachedRow and not options.refreshCache:
                if options.cacheMode == "on":
                    shouldUseCache = True
                elif options.cacheMode == "auto" and isCacheFresh(cachedRow, options.cacheHours):
                    shouldUseCache = True

            if shouldUseCache:
                source = "cache"
                rowData = stripCacheMeta(cachedRow)
            else:
                rowData = fetchStockData(symbol)
                if useCache and not rowData.get("error"):
                    cacheData[symbol] = {
                        **rowData,
                        "_cache_timestamp": datetime.now().isoformat(timespec="seconds"),
                    }
                    cacheDirty = True

                if rowData.get("error") and cachedRow:
                    rowData = stripCacheMeta(cachedRow)
                    source = "stale-cache"

            scoredData = scoreStock(rowData)
            results.append(scoredData)

            if not options.quiet:
                if scoredData.get("error"):
                    print(f"❌ {scoredData['error']}")
                else:
                    suffix = ""
                    if source == "cache":
                        suffix = " (cache)"
                    elif source == "stale-cache":
                        suffix = " (stale cache)"
                    print(f"✅ Score: {scoredData.get('totalScore', 0):.1f}/100 {scoredData.get('grade', '')}{suffix}")

            time.sleep(1.2)

        if useCache and cacheDirty:
            saveDataCache(cacheData, options.cacheFile)

        rows = [row for row in results if not row.get("error")]
        if not rows:
            return pd.DataFrame()

        resultDf = pd.DataFrame(rows)
        sortKey = "totalScore" if "totalScore" in resultDf.columns else "total_score"
        if sortKey in resultDf.columns:
            resultDf = resultDf.sort_values(sortKey, ascending=False).reset_index(drop=True)
        return resultDf
