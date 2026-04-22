from datetime import datetime
import time
import math
from collections import defaultdict

import pandas as pd

from .cache import isCacheFresh, loadDataCache, saveDataCache, stripCacheMeta
from .fetcher import fetchStockData
from .models import RunOptions
from .scoringEngine import scoreStock


class ScreeningService:
    """Run the screener engine with cache-aware options."""

    @staticmethod
    def _computeSectorStats(allData: list[dict]) -> dict:
        """Compute z-score stats for each metric by sector."""
        sectorData = defaultdict(lambda: defaultdict(list))
        metrics = [
            "peRatio", "pegRatio", "pbRatio", "evToEbitda",
            "epsGrowth5yr", "revenueGrowth3yr", "fcfMargin",
            "debtToEquity", "netDebtToEbitda", "currentRatio"
        ]

        # Group data by sector and collect metrics
        for stock in allData:
            if stock.get("error"):
                continue
            sector = stock.get("sector", "Unknown")
            if not sector:
                continue
            for metric in metrics:
                value = stock.get(metric)
                if value is not None and isinstance(value, (int, float)) and not math.isnan(value):
                    sectorData[sector][metric].append(value)

        # Compute mean and std dev for each metric in each sector
        sectorStats = {}
        for sector, metrics_dict in sectorData.items():
            sectorStats[sector] = {}
            for metric, values in metrics_dict.items():
                if len(values) > 1:
                    mean = sum(values) / len(values)
                    variance = sum((x - mean) ** 2 for x in values) / len(values)
                    stddev = math.sqrt(variance)
                    sectorStats[sector][metric] = {"mean": mean, "std": stddev}

        return sectorStats

    @staticmethod
    def _getZScore(value, sector, metric, sectorStats):
        """Get z-score for a value in a sector."""
        if value is None or not isinstance(value, (int, float)) or math.isnan(value):
            return None
        
        sectorMetricStats = sectorStats.get(sector, {}).get(metric)
        if not sectorMetricStats:
            return None
        
        mean = sectorMetricStats.get("mean")
        std = sectorMetricStats.get("std")
        
        if std is None or std == 0:
            return None
        
        return (value - mean) / std

    def run(self, symbols: list[str], options: RunOptions) -> pd.DataFrame:
        results = []
        useCache = options.cacheMode != "off"
        cacheData = loadDataCache(options.cacheFile) if useCache else {}
        cacheDirty = False
        allData = []

        # First pass: Fetch all data
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

            allData.append((rowData, source))
            if not options.quiet:
                print(f"✓")

        # Compute sector statistics for z-scores
        sectorStats = self._computeSectorStats([d for d, _ in allData])

        # Second pass: Score with z-score context
        for rowData, source in allData:
            if not options.quiet:
                print(f"  Scoring {rowData.get('symbol', 'N/A')}...", end=" ", flush=True)

            # Add z-scores to the data for scoring
            if not rowData.get("error"):
                sector = rowData.get("sector", "Unknown")
                zScores = {}
                for metric in ["peRatio", "pegRatio", "pbRatio", "evToEbitda", 
                              "epsGrowth5yr", "revenueGrowth3yr", "fcfMargin",
                              "debtToEquity", "netDebtToEbitda", "currentRatio"]:
                    zscore = self._getZScore(rowData.get(metric), sector, metric, sectorStats)
                    if zscore is not None:
                        zScores[f"{metric}_zscore"] = zscore
                rowData["_zscores"] = zScores
                rowData["_sector_stats"] = sectorStats

            scoredData = scoreStock(rowData)
            results.append(scoredData)

            if not options.quiet:
                if scoredData.get("error"):
                    print(f"❌ {scoredData['error']}")
                else:
                    if source == "cache":
                        print(
                            f"📦 Score: {scoredData['total_score']}/{scoredData.get('score_out_of', 100)} "
                            f"{scoredData['grade']} | Coverage: {scoredData.get('data_coverage_pct', 0)}% (cache)"
                        )
                    elif source == "stale-cache":
                        print(
                            f"📦 Score: {scoredData['total_score']}/{scoredData.get('score_out_of', 100)} "
                            f"{scoredData['grade']} | Coverage: {scoredData.get('data_coverage_pct', 0)}% (stale cache)"
                        )
                    else:
                        print(
                            f"✅ Score: {scoredData['total_score']}/{scoredData.get('score_out_of', 100)} "
                            f"{scoredData['grade']} | Coverage: {scoredData.get('data_coverage_pct', 0)}%"
                        )

            time.sleep(1.2)

        if useCache and cacheDirty:
            saveDataCache(cacheData, options.cacheFile)

        rows = [row for row in results if not row.get("error")]
        if not rows:
            return pd.DataFrame()

        resultDf = pd.DataFrame(rows)
        if "details" in resultDf.columns:
            resultDf = resultDf.drop(columns=["details"])

        if "total_score" in resultDf.columns:
            resultDf = resultDf.sort_values("total_score", ascending=False).reset_index(drop=True)
            resultDf.index = resultDf.index + 1
            resultDf.index.name = "Rank"
        return resultDf
