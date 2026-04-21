import pandas as pd

from .models import RunOptions
from .universe import loadDefaultSymbols


class DataLoader:
    """Resolve symbol universe from args/defaults and normalize tickers."""

    def resolveSymbols(self, options: RunOptions) -> list[str]:
        if options.symbols:
            return options.symbols

        if options.csvPath:
            csvDf = pd.read_csv(options.csvPath)
            symbolCols = [c for c in csvDf.columns if "symbol" in c.lower()]
            if not symbolCols:
                raise ValueError("CSV must contain a symbol-like column")
            symbols = csvDf[symbolCols[0]].tolist()
            return [s if ".NS" in s or ".BO" in s else f"{s}.NS" for s in symbols]

        return loadDefaultSymbols(universeName=options.universe)
