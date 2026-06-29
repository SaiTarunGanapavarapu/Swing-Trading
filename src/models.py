from dataclasses import dataclass

from .config import (
    defaultCacheFile,
    defaultCacheHours,
    defaultExportFile,
    defaultBudget,
    defaultPortfolioFile,
    defaultDecayLambda,
    defaultDecayFloor,
    defaultMaxPositionFrac,
    defaultMinPositionSize,
    defaultMaxPerSector,
    defaultTopBuy,
    defaultMinBuyScore,
)


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

    # Accumulation mode
    mode: str = "screen"  # screen | accumulate
    budget: float = defaultBudget
    portfolioFile: str = defaultPortfolioFile
    decayLambda: float = defaultDecayLambda
    decayFloor: float = defaultDecayFloor
    maxPositionFrac: float = defaultMaxPositionFrac
    minPositionSize: float = defaultMinPositionSize
    maxPerSector: int = defaultMaxPerSector
    topBuy: int = defaultTopBuy
    minBuyScore: float = defaultMinBuyScore
    confirmBuy: bool = False  # if True, record purchases to portfolio