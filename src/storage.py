import pandas as pd

from .reporting import exportToExcel


class ResultStorage:
    """Persist screener outputs to external files."""

    def exportRankings(self, rankingsDf: pd.DataFrame, exportFile: str) -> None:
        exportToExcel(rankingsDf, exportFile)
