"""Position-adjusted scoring for accumulation mode.

Penalizes stocks you already hold heavily, so the optimizer naturally
rotates into new names while still allowing high-conviction winners
to keep accumulating.
"""


def computeAdjustedScores(
    screenerResults: list[dict],
    portfolioWeights: dict[str, float],
    decayLambda: float = 1.5,
    floor: float = 0.3,
    maxPerSector: int = 2,
) -> list[dict]:
    """Compute position-adjusted scores and apply sector caps.

    Args:
        screenerResults: List of scored stock dicts from the screener.
                         Each must have 'symbol', 'totalScore', 'sector', 'currentPrice'.
        portfolioWeights: {symbol: weight} from existing portfolio (0.0–1.0).
        decayLambda: Penalty strength. Higher = faster rotation.
        floor: Minimum multiplier so high-conviction names aren't killed entirely.
        maxPerSector: Max stocks from one sector in the buy list.

    Returns:
        Filtered and re-ranked list of stock dicts with 'adjustedScore' added.
    """
    adjusted = []
    for stock in screenerResults:
        symbol = stock.get("symbol", "")
        rawScore = stock.get("totalScore", 0.0)
        existingWeight = portfolioWeights.get(symbol, 0.0)

        multiplier = max(floor, 1.0 - decayLambda * existingWeight)
        adjustedScore = round(rawScore * multiplier, 2)

        entry = dict(stock)
        entry["adjustedScore"] = adjustedScore
        entry["existingWeight"] = round(existingWeight * 100, 2)
        entry["penaltyMultiplier"] = round(multiplier, 3)
        adjusted.append(entry)

    # Sort by adjusted score descending
    adjusted.sort(key=lambda x: x["adjustedScore"], reverse=True)

    # Apply sector cap
    if maxPerSector > 0:
        adjusted = _applySectorCap(adjusted, maxPerSector)

    return adjusted


def _applySectorCap(ranked: list[dict], maxPerSector: int) -> list[dict]:
    """Keep at most maxPerSector stocks from each sector in the buy list."""
    sectorCounts: dict[str, int] = {}
    filtered = []
    for stock in ranked:
        sector = stock.get("sector", "Unknown")
        count = sectorCounts.get(sector, 0)
        if count < maxPerSector:
            filtered.append(stock)
            sectorCounts[sector] = count + 1
        # Skip stocks beyond the sector cap — they're not removed from the
        # full output, just excluded from the buy-eligible list
    return filtered


def selectBuyCandidates(
    adjustedResults: list[dict],
    topN: int = 5,
    minScore: float = 55.0,
) -> list[dict]:
    """Pick the top N stocks by adjusted score that meet the minimum threshold.

    Args:
        adjustedResults: Output of computeAdjustedScores (already sector-capped).
        topN: Maximum stocks to include in buy list.
        minScore: Minimum raw screener score to be buy-eligible.
                  This filters on totalScore, not adjustedScore, so a good stock
                  with a high penalty doesn't get bought just because nothing else
                  is available.
    """
    eligible = [
        s for s in adjustedResults
        if s.get("totalScore", 0) >= minScore
    ]
    return eligible[:topN]