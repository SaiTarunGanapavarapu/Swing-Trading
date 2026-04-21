from datetime import datetime
from pathlib import Path

import pandas as pd


def loadDataCache(cacheFile: str) -> dict[str, dict]:
    cachePath = Path(cacheFile)
    if not cachePath.exists():
        return {}
    try:
        cacheDf = pd.read_excel(cachePath)
    except Exception as exc:
        print(f"Warning: Could not read cache file {cacheFile}: {exc}")
        return {}

    if "symbol" not in cacheDf.columns:
        return {}

    cache = {}
    for _, row in cacheDf.iterrows():
        rowDict = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
        symbol = rowDict.get("symbol")
        if symbol:
            cache[str(symbol)] = rowDict
    return cache


def saveDataCache(cache: dict[str, dict], cacheFile: str):
    if not cache:
        return
    cacheDf = pd.DataFrame(cache.values())
    cacheDf = cacheDf.sort_values("symbol").reset_index(drop=True)
    cacheDf.to_excel(cacheFile, index=False)


def isCacheFresh(cacheRow: dict, cacheMaxAgeHours: float) -> bool:
    timestamp = cacheRow.get("_cache_timestamp")
    if not timestamp:
        return False
    try:
        tsDt = datetime.fromisoformat(str(timestamp))
    except Exception:
        return False

    ageHours = (datetime.now() - tsDt).total_seconds() / 3600
    return ageHours <= cacheMaxAgeHours


def stripCacheMeta(data: dict) -> dict:
    return {k: v for k, v in data.items() if not str(k).startswith("_")}
