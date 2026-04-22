from ..scoringCommon import RuleResult, scoreTiered


def score(data: dict) -> tuple[float, list[RuleResult]]:
    results = []
    total = 0

    de = data.get("debtToEquity", 999)
    if de is None:
        de = 999
    pts, grade = scoreTiered(de, [(0.1, 5, "excellent"), (0.5, 4, "good"), (1.0, 2, "fair")], inverse=True)
    total += pts
    results.append(RuleResult("B1", "Debt/Equity", "Buffett/Graham", de, pts, 5, grade))

    cr = data.get("currentRatio", 0)
    pts, grade = scoreTiered(cr, [(2.5, 4, "excellent"), (2.0, 3, "good"), (1.5, 2, "fair")], False)
    total += pts
    results.append(RuleResult("B2", "Current Ratio", "Graham", cr, pts, 4, grade))

    ic = data.get("interestCoverage", 0)
    pts, grade = scoreTiered(ic, [(10, 4, "excellent"), (5, 3, "good"), (3, 1, "fair")], False)
    total += pts
    results.append(RuleResult("B3", "Interest Coverage", "Graham", ic, pts, 4, grade))

    nd = data.get("netDebtToEbitda", 999)
    if nd is None:
        nd = 999
    pts, grade = scoreTiered(nd, [(0, 4, "excellent"), (1.0, 3, "good"), (2.0, 1, "fair")], inverse=True)
    total += pts
    results.append(RuleResult("B4", "Net Debt/EBITDA", "Lynch", nd, pts, 4, grade))

    fy = data.get("fcfPositiveYears", 0)
    pts, grade = scoreTiered(fy, [(5, 3, "excellent"), (4, 2, "good"), (3, 1, "fair")], False)
    total += pts
    results.append(RuleResult("B5", "FCF Positive Years", "Buffett", fy, pts, 3, grade))

    return total, results
