from ..scoringCommon import RuleResult, scoreTiered, scoreTieredZScore


def score(data: dict) -> tuple[float, list[RuleResult]]:
    results = []
    total = 0

    de = data.get("debtToEquity", 999)
    if de is None:
        de = 999
    
    # Try z-score for D/E ratio
    zscore = data.get("_zscores", {}).get("debtToEquity_zscore")
    if zscore is not None:
        # For D/E (inverse): lower z-scores are better
        pts, grade = scoreTieredZScore(zscore, [(-1.0, 5, "excellent"), (-0.5, 4, "good"), (0.5, 2, "fair")], inverse=True)
        display_value = zscore
        display_name = "D/E Ratio Z-Score"
    else:
        pts, grade = scoreTiered(de, [(0.1, 5, "excellent"), (0.5, 4, "good"), (1.0, 2, "fair")], inverse=True)
        display_value = de
        display_name = "Debt/Equity"
    
    total += pts
    results.append(RuleResult("B1", display_name, "Buffett/Graham", display_value, pts, 5, grade))

    cr = data.get("currentRatio", 0)
    # Try z-score for current ratio
    zscore = data.get("_zscores", {}).get("currentRatio_zscore")
    if zscore is not None:
        # For current ratio (higher is better): z > 0.5 is excellent
        pts, grade = scoreTieredZScore(zscore, [(0.5, 4, "excellent"), (0.0, 3, "good"), (-0.5, 2, "fair")], inverse=False)
        display_value = zscore
        display_name = "Current Ratio Z-Score"
    else:
        pts, grade = scoreTiered(cr, [(2.5, 4, "excellent"), (2.0, 3, "good"), (1.5, 2, "fair")], False)
        display_value = cr
        display_name = "Current Ratio"
    
    total += pts
    results.append(RuleResult("B2", display_name, "Graham", display_value, pts, 4, grade))

    ic = data.get("interestCoverage", 0)
    pts, grade = scoreTiered(ic, [(10, 4, "excellent"), (5, 3, "good"), (3, 1, "fair")], False)
    total += pts
    results.append(RuleResult("B3", "Interest Coverage", "Graham", ic, pts, 4, grade))

    nd = data.get("netDebtToEbitda", 999)
    if nd is None:
        nd = 999
    
    # Try z-score for Net Debt/EBITDA
    zscore = data.get("_zscores", {}).get("netDebtToEbitda_zscore")
    if zscore is not None:
        # For ND/E (inverse): lower z-scores are better
        pts, grade = scoreTieredZScore(zscore, [(-1.0, 4, "excellent"), (-0.5, 3, "good"), (0.5, 1, "fair")], inverse=True)
        display_value = zscore
        display_name = "Net Debt/EBITDA Z-Score"
    else:
        pts, grade = scoreTiered(nd, [(0, 4, "excellent"), (1.0, 3, "good"), (2.0, 1, "fair")], inverse=True)
        display_value = nd
        display_name = "Net Debt/EBITDA"
    
    total += pts
    results.append(RuleResult("B4", display_name, "Lynch", display_value, pts, 4, grade))

    fy = data.get("fcfPositiveYears", 0)
    pts, grade = scoreTiered(fy, [(5, 3, "excellent"), (4, 2, "good"), (3, 1, "fair")], False)
    total += pts
    results.append(RuleResult("B5", "FCF Positive Years", "Buffett", fy, pts, 3, grade))

    return total, results
