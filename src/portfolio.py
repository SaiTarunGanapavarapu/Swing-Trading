"""Persistent portfolio tracker for accumulation mode."""

import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict


@dataclass
class Holding:
    symbol: str
    shares: int = 0
    avgCost: float = 0.0
    totalInvested: float = 0.0
    sector: str = ""
    holdStatus: str = "accumulate"  # accumulate | hold | review
    reviewStartMonth: str | None = None  # ISO month when review started
    purchases: list[dict] = field(default_factory=list)

    @property
    def currentValue(self) -> float:
        """Placeholder — caller must set currentPrice on the holding dict."""
        return 0.0


class Portfolio:
    """Load, update, and persist portfolio holdings as JSON."""

    def __init__(self, filePath: str = "portfolio.json"):
        self.filePath = Path(filePath)
        self.holdings: dict[str, Holding] = {}
        self._load()

    def _load(self):
        if not self.filePath.exists():
            self.holdings = {}
            return
        with self.filePath.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        for symbol, data in raw.get("holdings", {}).items():
            self.holdings[symbol] = Holding(
                symbol=data.get("symbol", symbol),
                shares=data.get("shares", 0),
                avgCost=data.get("avgCost", 0.0),
                totalInvested=data.get("totalInvested", 0.0),
                sector=data.get("sector", ""),
                holdStatus=data.get("holdStatus", "accumulate"),
                reviewStartMonth=data.get("reviewStartMonth"),
                purchases=data.get("purchases", []),
            )

    def save(self):
        payload = {
            "updatedAt": datetime.now().isoformat(timespec="seconds"),
            "holdings": {sym: asdict(h) for sym, h in self.holdings.items()},
        }
        self.filePath.parent.mkdir(parents=True, exist_ok=True)
        with self.filePath.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def totalValue(self, currentPrices: dict[str, float]) -> float:
        total = 0.0
        for symbol, holding in self.holdings.items():
            price = currentPrices.get(symbol, holding.avgCost)
            total += holding.shares * price
        return total

    def weights(self, currentPrices: dict[str, float]) -> dict[str, float]:
        total = self.totalValue(currentPrices)
        if total <= 0:
            return {sym: 0.0 for sym in self.holdings}
        return {
            sym: (h.shares * currentPrices.get(sym, h.avgCost)) / total
            for sym, h in self.holdings.items()
        }

    def sectorWeights(self, currentPrices: dict[str, float]) -> dict[str, float]:
        total = self.totalValue(currentPrices)
        if total <= 0:
            return {}
        sectorTotals: dict[str, float] = {}
        for sym, h in self.holdings.items():
            price = currentPrices.get(sym, h.avgCost)
            sectorTotals[h.sector] = sectorTotals.get(h.sector, 0.0) + h.shares * price
        return {sector: val / total for sector, val in sectorTotals.items()}

    def recordPurchase(self, symbol: str, shares: int, price: float, sector: str = ""):
        if shares <= 0:
            return
        if symbol not in self.holdings:
            self.holdings[symbol] = Holding(symbol=symbol, sector=sector)

        h = self.holdings[symbol]
        oldTotal = h.shares * h.avgCost
        newTotal = shares * price
        h.shares += shares
        h.avgCost = round((oldTotal + newTotal) / h.shares, 2) if h.shares > 0 else 0.0
        h.totalInvested = round(h.totalInvested + newTotal, 2)
        if sector:
            h.sector = sector
        h.purchases.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "shares": shares,
            "price": price,
        })

    def recordSale(self, symbol: str, shares: int, price: float):
        if symbol not in self.holdings:
            return
        h = self.holdings[symbol]
        h.shares = max(0, h.shares - shares)
        h.purchases.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "shares": -shares,
            "price": price,
        })
        if h.shares == 0:
            del self.holdings[symbol]

    def updateHoldStatus(self, scores: dict[str, float], currentMonth: str):
        """Update hold status for all holdings based on latest screener scores.

        Rules:
            score >= 60  → accumulate
            50 <= score < 60 → hold (keep, don't buy more)
            score < 50 for 1 month → review (start clock)
            score < 50 for 2 consecutive months → sell signal
            stock not in scores at all or score < 40 → immediate sell signal
        """
        for symbol, holding in list(self.holdings.items()):
            score = scores.get(symbol)

            if score is None or score < 40:
                holding.holdStatus = "sell"
                continue

            if score >= 60:
                holding.holdStatus = "accumulate"
                holding.reviewStartMonth = None
            elif score >= 50:
                holding.holdStatus = "hold"
                holding.reviewStartMonth = None
            else:
                # score < 50
                if holding.holdStatus == "review" and holding.reviewStartMonth:
                    # Already in review — check if this is second consecutive month
                    if holding.reviewStartMonth != currentMonth:
                        holding.holdStatus = "sell"
                    # Same month re-run, keep as review
                else:
                    holding.holdStatus = "review"
                    holding.reviewStartMonth = currentMonth

    def getSellCandidates(self) -> list[str]:
        return [sym for sym, h in self.holdings.items() if h.holdStatus == "sell"]

    def getAccumulateCandidates(self) -> list[str]:
        return [sym for sym, h in self.holdings.items() if h.holdStatus == "accumulate"]

    def summary(self, currentPrices: dict[str, float]) -> list[dict]:
        rows = []
        for sym, h in self.holdings.items():
            price = currentPrices.get(sym, h.avgCost)
            currentVal = h.shares * price
            pnl = currentVal - h.totalInvested
            pnlPct = (pnl / h.totalInvested * 100) if h.totalInvested > 0 else 0.0
            rows.append({
                "symbol": sym,
                "shares": h.shares,
                "avgCost": h.avgCost,
                "currentPrice": price,
                "totalInvested": h.totalInvested,
                "currentValue": round(currentVal, 2),
                "pnl": round(pnl, 2),
                "pnlPct": round(pnlPct, 2),
                "sector": h.sector,
                "holdStatus": h.holdStatus,
            })
        return sorted(rows, key=lambda r: r["currentValue"], reverse=True)