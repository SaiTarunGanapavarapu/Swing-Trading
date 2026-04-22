from ..scoringCommon import RuleResult, scoreTiered, scoreTieredZScore


def _scoreMetric(data: dict, metricName: str, rawValue, tiers, maxPoints, source: str, inverse=False):
    """Helper to score a metric using z-score if available, otherwise use raw value."""
    zscore = data.get("_zscores", {}).get(f"{metricName}_zscore")
    
    if zscore is not None:
        # Z-score based tiers: use the same pattern but map to z-score ranges
        # For inverse (PE): lower z-scores are better
        # For non-inverse (growth): higher z-scores are better
        zscoreTiers = tiers  # Assumes tiers are already z-score thresholds
        pts, grade = scoreTieredZScore(zscore, zscoreTiers, inverse=inverse)
        return pts, grade, rawValue, zscore
    else:
        # Fallback to raw value scoring
        pts, grade = scoreTiered(rawValue, tiers, inverse=inverse)
        return pts, grade, rawValue, None


def score(data: dict) -> tuple[float, list[RuleResult]]:
    results = []
    total = 0

    # P/E Ratio - Z-score tiers: < -1.0 (excellent), -1.0 to 0 (good), 0 to 1.0 (fair), > 1.0 (poor)
    pe = data.get("peRatio", 0)
    if pe and pe > 0:
        zscore = data.get("_zscores", {}).get("peRatio_zscore")
        if zscore is not None:
            # For PE (inverse): lower z-scores are better (z < mean is good)
            pts, grade = scoreTieredZScore(zscore, [(-1.0, 5, "excellent"), (0.0, 3, "good"), (1.0, 1, "fair")], inverse=True)
            display_value = zscore
            display_label = f"P/E Ratio Z-Score"
        else:
            pts, grade = scoreTiered(pe, [(12, 5, "excellent"), (20, 3, "good"), (30, 1, "fair")], inverse=True)
            display_value = pe
            display_label = "P/E Ratio"
    else:
        pts, grade = 0, "loss-making"
        display_value = pe
        display_label = "P/E Ratio"
    total += pts
    results.append(RuleResult("V1", display_label, "Graham", display_value, pts, 5, grade))

    # PEG Ratio - Z-score tiers
    peg = data.get("pegRatio", 0)
    if peg and peg > 0:
        zscore = data.get("_zscores", {}).get("pegRatio_zscore")
        if zscore is not None:
            pts, grade = scoreTieredZScore(zscore, [(-1.0, 5, "excellent"), (-0.5, 4, "good"), (0.5, 2, "fair")], inverse=True)
            display_value = zscore
            display_label = "PEG Ratio Z-Score"
        else:
            pts, grade = scoreTiered(peg, [(0.5, 5, "excellent"), (1.0, 4, "good"), (1.5, 2, "fair")], inverse=True)
            display_value = peg
            display_label = "PEG Ratio"
    else:
        pts, grade = 0, "N/A"
        display_value = peg
        display_label = "PEG Ratio"
    total += pts
    results.append(RuleResult("V2", display_label, "Lynch", display_value, pts, 5, grade))

    # P/B Ratio - Z-score tiers
    pb = data.get("pbRatio", 0)
    if pb and pb > 0:
        zscore = data.get("_zscores", {}).get("pbRatio_zscore")
        if zscore is not None:
            pts, grade = scoreTieredZScore(zscore, [(-1.0, 4, "excellent"), (0.0, 2, "good"), (1.0, 1, "fair")], inverse=True)
            display_value = zscore
            display_label = "P/B Ratio Z-Score"
        else:
            pts, grade = scoreTiered(pb, [(1.5, 4, "excellent"), (3.0, 2, "good"), (5.0, 1, "fair")], inverse=True)
            display_value = pb
            display_label = "P/B Ratio"
    else:
        pts, grade = 0, "N/A"
        display_value = pb
        display_label = "P/B Ratio"
    total += pts
    results.append(RuleResult("V3", display_label, "Graham", display_value, pts, 4, grade))

    gr = data.get("grahamNumberRatio", 999)
    if gr and gr < 900:
        pts, grade = scoreTiered(gr, [(0.8, 3, "excellent"), (1.0, 2, "good"), (1.2, 1, "fair")], inverse=True)
    else:
        pts, grade = 0, "N/A"
    total += pts
    results.append(RuleResult("V4", "Graham Number", "Graham", gr, pts, 3, grade))

    # EV/EBITDA - Z-score tiers
    ev = data.get("evToEbitda", 0)
    if ev and ev > 0:
        zscore = data.get("_zscores", {}).get("evToEbitda_zscore")
        if zscore is not None:
            pts, grade = scoreTieredZScore(zscore, [(-1.0, 3, "excellent"), (0.0, 2, "good"), (1.0, 1, "fair")], inverse=True)
            display_value = zscore
            display_label = "EV/EBITDA Z-Score"
        else:
            pts, grade = scoreTiered(ev, [(8, 3, "excellent"), (12, 2, "good"), (18, 1, "fair")], inverse=True)
            display_value = ev
            display_label = "EV/EBITDA"
    else:
        pts, grade = 0, "N/A"
        display_value = ev
        display_label = "EV/EBITDA"
    total += pts
    results.append(RuleResult("V5", display_label, "Buffett", display_value, pts, 3, grade))

    ey = data.get("earningsYield", 0)
    pts, grade = scoreTiered(ey, [(10, 3, "excellent"), (7, 2, "good"), (4, 1, "fair")], False)
    total += pts
    results.append(RuleResult("V6", "Earnings Yield", "Graham", ey, pts, 3, grade))

    dy = data.get("dividendYield", 0)
    pts, grade = scoreTiered(dy, [(3.0, 2, "excellent"), (1.5, 1.5, "good"), (0.5, 0.5, "fair")], False)
    total += pts
    results.append(RuleResult("V7", "Dividend Yield", "Graham", dy, pts, 2, grade))

    return total, results
