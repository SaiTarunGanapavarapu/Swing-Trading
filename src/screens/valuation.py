from ..scoringCommon import RuleResult, scoreTiered


def score(data: dict) -> tuple[float, list[RuleResult]]:
    results = []
    total = 0

    pe = data.get("peRatio", 0)
    if pe and pe > 0:
        pts, grade = scoreTiered(pe, [(12, 5, "excellent"), (20, 3, "good"), (30, 1, "fair")], inverse=True)
    else:
        pts, grade = 0, "loss-making"
    total += pts
    results.append(RuleResult("V1", "P/E Ratio", "Graham", pe, pts, 5, grade))

    peg = data.get("pegRatio", 0)
    if peg and peg > 0:
        pts, grade = scoreTiered(peg, [(0.5, 5, "excellent"), (1.0, 4, "good"), (1.5, 2, "fair")], inverse=True)
    else:
        pts, grade = 0, "N/A"
    total += pts
    results.append(RuleResult("V2", "PEG Ratio", "Lynch", peg, pts, 5, grade))

    pb = data.get("pbRatio", 0)
    if pb and pb > 0:
        pts, grade = scoreTiered(pb, [(1.5, 4, "excellent"), (3.0, 2, "good"), (5.0, 1, "fair")], inverse=True)
    else:
        pts, grade = 0, "N/A"
    total += pts
    results.append(RuleResult("V3", "P/B Ratio", "Graham", pb, pts, 4, grade))

    gr = data.get("grahamNumberRatio", 999)
    if gr and gr < 900:
        pts, grade = scoreTiered(gr, [(0.8, 3, "excellent"), (1.0, 2, "good"), (1.2, 1, "fair")], inverse=True)
    else:
        pts, grade = 0, "N/A"
    total += pts
    results.append(RuleResult("V4", "Graham Number", "Graham", gr, pts, 3, grade))

    ev = data.get("evToEbitda", 0)
    if ev and ev > 0:
        pts, grade = scoreTiered(ev, [(8, 3, "excellent"), (12, 2, "good"), (18, 1, "fair")], inverse=True)
    else:
        pts, grade = 0, "N/A"
    total += pts
    results.append(RuleResult("V5", "EV/EBITDA", "Buffett", ev, pts, 3, grade))

    ey = data.get("earningsYield", 0)
    pts, grade = scoreTiered(ey, [(10, 3, "excellent"), (7, 2, "good"), (4, 1, "fair")], False)
    total += pts
    results.append(RuleResult("V6", "Earnings Yield", "Graham", ey, pts, 3, grade))

    dy = data.get("dividendYield", 0)
    pts, grade = scoreTiered(dy, [(3.0, 2, "excellent"), (1.5, 1.5, "good"), (0.5, 0.5, "fair")], False)
    total += pts
    results.append(RuleResult("V7", "Dividend Yield", "Graham", dy, pts, 2, grade))

    return total, results
