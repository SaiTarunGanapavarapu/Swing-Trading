"""Budget-constrained integer share allocation.

Solves: maximize  Σ adjustedScore_i × (n_i × price_i / budget)
        subject to Σ n_i × price_i ≤ budget
                   n_i ∈ Z≥0
                   n_i × price_i ≤ maxPositionFrac × budget  (per-stock cap)
                   n_i × price_i ≥ minPositionSize  OR  n_i = 0

Uses cvxpy with a MIP solver. Falls back to a greedy approach if
cvxpy is unavailable or the problem is infeasible.
"""

from dataclasses import dataclass


@dataclass
class AllocationResult:
    symbol: str
    shares: int
    price: float
    amount: float
    weight: float  # fraction of budget
    adjustedScore: float
    sector: str


def allocate(
    candidates: list[dict],
    budget: float = 20000.0,
    maxPositionFrac: float = 0.40,
    minPositionSize: float = 2000.0,
) -> list[AllocationResult]:
    """Allocate budget across candidates using integer share optimization.

    Args:
        candidates: List of dicts with 'symbol', 'adjustedScore', 'currentPrice', 'sector'.
        budget: Total capital to deploy this period (₹).
        maxPositionFrac: Max fraction of budget in any single stock.
        minPositionSize: Don't buy a stock unless allocation ≥ this amount (₹).

    Returns:
        List of AllocationResult with exact share counts.
    """
    # Filter out stocks with missing or zero prices
    valid = [
        c for c in candidates
        if c.get("currentPrice") and c["currentPrice"] > 0
    ]
    if not valid:
        return []

    try:
        return _solveCvxpy(valid, budget, maxPositionFrac, minPositionSize)
    except Exception:
        return _solveGreedy(valid, budget, maxPositionFrac, minPositionSize)


def _solveCvxpy(
    candidates: list[dict],
    budget: float,
    maxPositionFrac: float,
    minPositionSize: float,
) -> list[AllocationResult]:
    import cvxpy as cp

    n = len(candidates)
    prices = [c["currentPrice"] for c in candidates]
    scores = [c["adjustedScore"] for c in candidates]

    # Decision variable: integer shares for each stock
    shares = cp.Variable(n, integer=True)

    # Objective: maximize score-weighted allocation
    # Σ score_i × (shares_i × price_i) / budget
    allocation = cp.multiply(shares, prices)
    objective = cp.Maximize(cp.sum(cp.multiply(scores, allocation)) / budget)

    constraints = [
        shares >= 0,
        cp.sum(allocation) <= budget,
    ]

    # Per-stock max position — allow at least 1 share even if it exceeds
    # the percentage cap (at small budgets, the cap is wrong for ₹10k stocks)
    maxAmount = maxPositionFrac * budget
    for i in range(n):
        singleShareAmount = prices[i]
        effectiveMax = max(maxAmount, singleShareAmount)  # at least 1 share
        constraints.append(shares[i] * prices[i] <= effectiveMax)

    # Max shares anyone could hold (upper bound helps solver)
    for i in range(n):
        constraints.append(shares[i] <= int(budget / prices[i]) + 1)

    prob = cp.Problem(objective, constraints)
    prob.solve(solver=cp.GLPK_MI, verbose=False)

    if prob.status not in ("optimal", "optimal_inaccurate"):
        # Try without GLPK
        prob.solve(verbose=False)

    if prob.status not in ("optimal", "optimal_inaccurate"):
        raise RuntimeError(f"Solver status: {prob.status}")

    results = []
    shareValues = [max(0, int(round(s))) for s in shares.value]

    for i, c in enumerate(candidates):
        if shareValues[i] <= 0:
            continue
        amount = shareValues[i] * prices[i]
        # Enforce minimum position size post-solve
        if amount < minPositionSize:
            continue
        results.append(AllocationResult(
            symbol=c["symbol"],
            shares=shareValues[i],
            price=prices[i],
            amount=round(amount, 2),
            weight=round(amount / budget, 4),
            adjustedScore=c["adjustedScore"],
            sector=c.get("sector", ""),
        ))

    results.sort(key=lambda r: r.amount, reverse=True)
    return results


def _solveGreedy(
    candidates: list[dict],
    budget: float,
    maxPositionFrac: float,
    minPositionSize: float,
) -> list[AllocationResult]:
    """Greedy fallback: score-weighted allocation with integer share rounding.

    Handles expensive stocks (price > proportional target) by allowing
    1 share as long as it fits in the remaining budget — the percentage cap
    is relaxed for single-share positions since at small budgets it's the
    wrong constraint for high-priced stocks.
    """
    totalScore = sum(c["adjustedScore"] for c in candidates)
    if totalScore <= 0:
        return []

    maxAmount = maxPositionFrac * budget
    results = []
    allocated = set()
    remaining = budget

    # Sort by adjusted score descending
    ranked = sorted(candidates, key=lambda c: c["adjustedScore"], reverse=True)

    # First pass: proportional allocation
    for c in ranked:
        price = c["currentPrice"]
        targetAmount = min(
            (c["adjustedScore"] / totalScore) * budget,
            maxAmount,
            remaining,
        )

        shareCount = int(targetAmount / price)

        # If proportional target can't buy 1 share but 1 share fits in
        # remaining budget, buy 1 anyway — don't let expensive stocks
        # get zero allocation just because the proportional slice is small
        if shareCount == 0 and price <= remaining:
            shareCount = 1

        if shareCount <= 0:
            continue

        amount = shareCount * price
        if amount > remaining:
            shareCount = int(remaining / price)
            if shareCount <= 0:
                continue
            amount = shareCount * price

        results.append(AllocationResult(
            symbol=c["symbol"],
            shares=shareCount,
            price=price,
            amount=round(amount, 2),
            weight=round(amount / budget, 4),
            adjustedScore=c["adjustedScore"],
            sector=c.get("sector", ""),
        ))
        allocated.add(c["symbol"])
        remaining -= amount

    # Second pass: deploy residual cash into existing positions (cheapest first
    # so we can add more shares), respecting the max position cap
    if remaining > 0:
        for result in sorted(results, key=lambda r: r.price):
            if remaining < result.price:
                continue
            extraShares = int(remaining / result.price)
            newAmount = result.amount + extraShares * result.price
            # For stocks already above maxAmount (single expensive share),
            # don't add more — only top up stocks below the cap
            if result.amount < maxAmount and extraShares > 0:
                capRoom = int((maxAmount - result.amount) / result.price)
                extraShares = min(extraShares, capRoom)
                if extraShares > 0:
                    result.shares += extraShares
                    added = extraShares * result.price
                    result.amount = round(result.amount + added, 2)
                    result.weight = round(result.amount / budget, 4)
                    remaining -= added

    results.sort(key=lambda r: r.amount, reverse=True)
    return results


def printAllocation(results: list[AllocationResult], budget: float):
    """Pretty-print the allocation table."""
    if not results:
        print("\n⚠️  No allocation produced (no eligible candidates or budget too small).")
        return

    totalDeployed = sum(r.amount for r in results)
    residual = budget - totalDeployed

    print(f"\n{'='*70}")
    print(f"  MONTHLY ALLOCATION — Budget: ₹{budget:,.0f}")
    print(f"{'='*70}")
    print(f"  {'Symbol':<16} {'Shares':>6} {'Price':>10} {'Amount':>10} {'Weight':>8} {'AdjScore':>8}")
    print(f"  {'-'*64}")

    for r in results:
        print(
            f"  {r.symbol:<16} {r.shares:>6} {r.price:>10,.2f} "
            f"₹{r.amount:>9,.0f} {r.weight:>7.1%} {r.adjustedScore:>8.1f}"
        )

    print(f"  {'-'*64}")
    print(f"  {'Total deployed':<16} {'':>6} {'':>10} ₹{totalDeployed:>9,.0f} {totalDeployed/budget:>7.1%}")
    print(f"  {'Residual cash':<16} {'':>6} {'':>10} ₹{residual:>9,.0f}")
    print(f"{'='*70}")