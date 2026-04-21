from dataclasses import dataclass

from .config import defaultCacheFile, defaultCacheHours, defaultExportFile


@dataclass
class RunOptions:
    symbols: list[str] | None = None
    csvPath: str | None = None
    universe: str = "nifty50"
    exportFile: str = defaultExportFile
    topN: int = 50
    quiet: bool = False
    cacheFile: str = defaultCacheFile
    cacheHours: float = defaultCacheHours
    refreshCache: bool = False
    noCache: bool = False
    cacheMode: str = "off"
