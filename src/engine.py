from .data_loader import DataLoader
from .models import RunOptions
from .reporting import printResults
from .screening_service import ScreeningService
from .storage import ResultStorage


class SwingScreenerEngine:
    """Main orchestration engine for swing screening."""

    def __init__(self):
        self.dataLoader = DataLoader()
        self.screeningService = ScreeningService()
        self.storage = ResultStorage()

    def run(self, options: RunOptions):
        symbols = self.dataLoader.resolveSymbols(options)
        print(f"\n🔍 Screening {len(symbols)} stocks through Buffett/Lynch/Graham rules...\n")

        rankingsDf = self.screeningService.run(symbols, options)

        if rankingsDf.empty:
            return rankingsDf

        printResults(rankingsDf.head(options.topN))
        self.storage.exportRankings(rankingsDf, options.exportFile)
        return rankingsDf
