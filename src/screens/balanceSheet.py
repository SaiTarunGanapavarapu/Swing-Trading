from ..scoringCommon import RuleResult, scoreTiered, scoreTieredZScore


def score(data: dict) -> tuple[float, list[RuleResult]]:
    results = []
    total = 0

    # === HARD GUARDRAILS (Absolute Risk Thresholds) ===
    # These are hard caps/fails, not soft z-score tiers.
    
    de = data.get("debtToEquity")
    if de is not None and de > 2.0:
        # Hard fail: excessive debt
        pts, grade = 0, "CRITICAL_DEBT"
        results.append(RuleResult("B1", "Debt/Equity", "Buffett/Graham", de, pts, 5, grade))
        total += pts
    else:
        # Try z-score for D/E ratio
        zscore = data.get("_zscores", {}).get("debtToEquity_zscore")
        if zscore is not None:
            # For D/E (inverse): lower z-scores are better
            pts, grade = scoreTieredZScore(zscore, [(-1.0, 5, "excellent"), (-0.5, 4, "good"), (0.5, 2, "fair")], inverse=True)
            display_value = zscore
            display_name = "D/E Ratio Z-Score"
        else:
            de_val = de if de is not None else 999
            pts, grade = scoreTiered(de_val, [(0.1, 5, "excellent"), (0.5, 4, "good"), (1.0, 2, "fair")], inverse=True)
            display_value = de_val
            display_name = "Debt/Equity"
        
        total += pts
        results.append(RuleResult("B1", display_name, "Buffett/Graham", display_value, pts, 5, grade))

    cr = data.get("currentRatio")
    if cr is not None and cr < 1.0 and cr > 0:
        # Hard fail: liquidity crisis
        pts, grade = 0, "LIQUIDITY_CRISIS"
        results.append(RuleResult("B2", "Current Ratio", "Graham", cr, pts, 4, grade))
        total += pts
    else:
        # Try z-score for current ratio
        zscore = data.get("_zscores", {}).get("currentRatio_zscore")
        if zscore is not None:
            # For current ratio (higher is better): z > 0.5 is excellent
            pts, grade = scoreTieredZScore(zscore, [(0.5, 4, "excellent"), (0.0, 3, "good"), (-0.5, 2, "fair")], inverse=False)
            display_value = zscore
            display_name = "Current Ratio Z-Score"
        else:
            cr_val = cr if cr is not None else 0
            pts, grade = scoreTiered(cr_val, [(2.5, 4, "excellent"), (2.0, 3, "good"), (1.5, 2, "fair")], False)
            display_value = cr_val
            display_name = "Current Ratio"
        
        total += pts
        results.append(RuleResult("B2", display_name, "Graham", display_value, pts, 4, grade))

    ic = data.get("interestCoverage", 0)
    pts, grade = scoreTiered(ic, [(10, 4, "excellent"), (5, 3, "good"), (3, 1, "fair")], False)
    total += pts
    results.append(RuleResult("B3", "Interest Coverage", "Graham", ic, pts, 4, grade))

    nd = data.get("netDebtToEbitda")
    if nd is not None and nd > 3.0:
        # Hard cap: excessive leverage
        pts, grade = 0, "EXCESSIVE_LEVERAGE"
        results.append(RuleResult("B4", "Net Debt/EBITDA", "Lynch", nd, pts, 4, grade))
        total += pts
    else:
        # Try z-score for Net Debt/EBITDA
        zscore = data.get("_zscores", {}).get("netDebtToEbitda_zscore")
        if zscore is not None:
            # For ND/E (inverse): lower z-scores are better
            pts, grade = scoreTieredZScore(zscore, [(-1.0, 4, "excellent"), (-0.5, 3, "good"), (0.5, 1, "fair")], inverse=True)
            display_value = zscore
            display_name = "Net Debt/EBITDA Z-Score"
        else:
            nd_val = nd if nd is not None else 999
            pts, grade = scoreTiered(nd_val, [(0, 4, "excellent"), (1.0, 3, "good"), (2.0, 1, "fair")], inverse=True)
            display_value = nd_val
            display_name = "Net Debt/EBITDA"
        
        total += pts
        results.append(RuleResult("B4", display_name, "Lynch", display_value, pts, 4, grade))

    fy = data.get("fcfPositiveYears", 0)
    pts, grade = scoreTiered(fy, [(5, 3, "excellent"), (4, 2, "good"), (3, 1, "fair")], False)
    total += pts
    results.append(RuleResult("B5", "FCF Positive Years", "Buffett", fy, pts, 3, grade))

    return total, results
