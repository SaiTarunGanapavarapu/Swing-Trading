from ..scoring_common import RuleResult, scoreTiered


def score(data: dict) -> tuple[float, list[RuleResult]]:
    results = []
    total = 0

    py = data.get("profitableYears", 0)
    pts, grade = scoreTiered(py, [(4, 4, "excellent"), (3, 3, "good"), (2, 1, "fair")], False)
    total += pts
    results.append(RuleResult("Q1", "Profitable Years", "Graham", py, pts, 4, grade))

    dy = data.get("dividendYears", 0)
    pts, grade = scoreTiered(dy, [(10, 3, "excellent"), (5, 2, "good"), (3, 1, "fair")], False)
    total += pts
    results.append(RuleResult("Q2", "Dividend History", "Graham", dy, pts, 3, grade))

    ph = data.get("promoterHolding")
    if ph is not None:
        pts, grade = scoreTiered(ph, [(65, 3, "excellent"), (50, 2, "good"), (35, 1, "fair")], False)
    else:
        pts, grade = 1.5, "unknown"
    total += pts
    results.append(RuleResult("Q3", "Promoter Holding", "India", ph, pts, 3, grade))

    pp = data.get("promoterPledge")
    if pp is not None:
        if pp > 25:
            pts, grade = -2, "CRITICAL"
        elif pp > 10:
            pts, grade = 0, "poor"
        elif pp > 5:
            pts, grade = 1, "fair"
        elif pp > 1:
            pts, grade = 2, "good"
        else:
            pts, grade = 3, "excellent"
    else:
        pts, grade = 1.5, "unknown"
    total += pts
    results.append(RuleResult("Q4", "Promoter Pledge", "India", pp, pts, 3, grade))

    mc = data.get("marketCapCr", 0)
    pts, grade = scoreTiered(mc, [(10000, 2, "excellent"), (3000, 1.5, "good"), (1000, 1, "fair")], False)
    total += pts
    results.append(RuleResult("Q5", "Market Cap", "Graham", mc, pts, 2, grade))

    return total, results
