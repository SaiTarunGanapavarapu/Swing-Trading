import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from .reporting import exportToExcel


class ResultStorage:
    """Persist screener outputs to external files."""

    @staticmethod
    def buildJsonExportPath(exportFile: str) -> Path:
        exportPath = Path(exportFile)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return exportPath.with_name(f"{exportPath.stem}_{timestamp}.json")

    @staticmethod
    def exportToJson(rankingsDf: pd.DataFrame, exportFile: str) -> None:
        jsonPath = ResultStorage.buildJsonExportPath(exportFile)
        jsonPath.parent.mkdir(parents=True, exist_ok=True)

        cleanDf = rankingsDf.where(pd.notna(rankingsDf), None)
        stockRows = cleanDf.to_dict(orient="records")
        jsonPayload = {
            "generatedAt": datetime.now().isoformat(timespec="seconds"),
            "totalStocks": len(stockRows),
            "stocks": stockRows,
        }

        with jsonPath.open("w", encoding="utf-8") as fileHandle:
            json.dump(jsonPayload, fileHandle, indent=2)

        print(f"\nJSON exported to {jsonPath}")

    def exportRankings(self, rankingsDf: pd.DataFrame, exportFile: str) -> None:
        exportToExcel(rankingsDf, exportFile)
        self.exportToJson(rankingsDf, exportFile)
