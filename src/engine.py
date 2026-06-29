from datetime import datetime

from .adjustedScore import computeAdjustedScores, selectBuyCandidates
from .allocator import allocate, printAllocation
from .dataLoader import DataLoader
from .models import RunOptions
from .portfolio import Portfolio
from .reporting import printResults
from .screeningService import ScreeningService
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

        if options.mode == "accumulate":
            self._runAccumulation(rankingsDf, options)

        return rankingsDf

    def _runAccumulation(self, rankingsDf, options: RunOptions):
        """Run the accumulation pipeline: adjust scores → optimize → show allocation."""
        portfolio = Portfolio(options.portfolioFile)

        # Build current prices dict from screener results
        currentPrices = {}
        screenerResults = []
        for _, row in rankingsDf.iterrows():
            symbol = row.get("symbol", "")
            price = row.get("currentPrice", 0)
            if symbol and price:
                currentPrices[symbol] = price
            screenerResults.append(row.to_dict())

        # Update hold status for existing holdings
        scoreMap = {
            row.get("symbol", ""): row.get("totalScore", 0)
            for row in screenerResults
        }
        currentMonth = datetime.now().strftime("%Y-%m")
        portfolio.updateHoldStatus(scoreMap, currentMonth)

        # Show sell candidates
        sellCandidates = portfolio.getSellCandidates()
        if sellCandidates:
            print(f"\n🔴 SELL SIGNALS: {', '.join(sellCandidates)}")
            print("   These stocks scored below threshold for 2+ consecutive months.")

        # Compute portfolio weights
        portfolioWeights = portfolio.weights(currentPrices)

        # Compute adjusted scores
        adjustedResults = computeAdjustedScores(
            screenerResults=screenerResults,
            portfolioWeights=portfolioWeights,
            decayLambda=options.decayLambda,
            floor=options.decayFloor,
            maxPerSector=options.maxPerSector,
        )

        # Select buy candidates
        buyCandidates = selectBuyCandidates(
            adjustedResults,
            topN=options.topBuy,
            minScore=options.minBuyScore,
        )

        if not buyCandidates:
            print("\n⚠️  No stocks meet the buy threshold after position adjustment.")
            return

        # Show adjusted scores
        print(f"\n{'─'*70}")
        print("  POSITION-ADJUSTED RANKINGS (top candidates)")
        print(f"{'─'*70}")
        print(f"  {'Symbol':<16} {'RawScore':>9} {'Weight%':>8} {'Penalty':>8} {'AdjScore':>9} {'Sector'}")
        print(f"  {'─'*64}")
        for c in buyCandidates:
            print(
                f"  {c['symbol']:<16} {c['totalScore']:>9.1f} "
                f"{c['existingWeight']:>7.1f}% {c['penaltyMultiplier']:>8.3f} "
                f"{c['adjustedScore']:>9.2f}  {c.get('sector', '')}"
            )

        # Run allocation optimizer
        allocationResults = allocate(
            candidates=buyCandidates,
            budget=options.budget,
            maxPositionFrac=options.maxPositionFrac,
            minPositionSize=options.minPositionSize,
        )
        printAllocation(allocationResults, options.budget)

        # Record purchases if confirmed
        if options.confirmBuy and allocationResults:
            for r in allocationResults:
                portfolio.recordPurchase(r.symbol, r.shares, r.price, r.sector)
            portfolio.save()
            print(f"\n✅ Portfolio updated → {options.portfolioFile}")

        # Print portfolio summary
        if portfolio.holdings:
            print(f"\n{'─'*70}")
            print("  PORTFOLIO SUMMARY")
            print(f"{'─'*70}")
            summary = portfolio.summary(currentPrices)
            print(f"  {'Symbol':<16} {'Shares':>6} {'AvgCost':>9} {'CurPrice':>9} {'P&L%':>7} {'Status'}")
            print(f"  {'─'*64}")
            for row in summary:
                print(
                    f"  {row['symbol']:<16} {row['shares']:>6} "
                    f"₹{row['avgCost']:>8,.2f} ₹{row['currentPrice']:>8,.2f} "
                    f"{row['pnlPct']:>6.1f}%  {row['holdStatus']}"
                )
            totalInvested = sum(r["totalInvested"] for r in summary)
            totalCurrent = sum(r["currentValue"] for r in summary)
            totalPnl = totalCurrent - totalInvested
            print(f"  {'─'*64}")
            print(f"  Total invested: ₹{totalInvested:,.0f}  |  Current: ₹{totalCurrent:,.0f}  |  P&L: ₹{totalPnl:,.0f}")

        portfolio.save()