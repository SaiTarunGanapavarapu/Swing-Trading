from ..scoringCommon import RuleResult, scoreTiered


def score(data: dict) -> tuple[float, list[RuleResult]]:
    results = []
    total = 0

    rules = [
        ("P1", "Gross Margin", "Buffett", data.get("grossMargin", 0), 5,
         [(60, 5, "excellent"), (40, 3, "good"), (20, 1, "fair")], False),
        ("P2", "Net Margin", "Buffett", data.get("netMargin", 0), 4,
         [(25, 4, "excellent"), (20, 3, "good"), (10, 1, "fair")], False),
        ("P3", "Operating Margin", "Buffett", data.get("operatingMargin", 0), 4,
         [(25, 4, "excellent"), (15, 3, "good"), (10, 1, "fair")], False),
        ("P4", "ROE", "Buffett", data.get("roe", 0), 5,
         [(25, 5, "excellent"), (20, 3, "good"), (15, 1, "fair")], False),
        ("P5", "ROCE", "Buffett/Graham", data.get("roce", 0), 4,
         [(25, 4, "excellent"), (15, 3, "good"), (10, 1, "fair")], False),
        ("P6", "EPS Growth", "Lynch", data.get("epsGrowth5yr", 0), 4,
         [(20, 4, "excellent"), (15, 3, "good"), (10, 1, "fair")], False),
        ("P7", "Revenue Growth 3Y", "Lynch", data.get("revenueGrowth3yr", 0), 2,
         [(20, 2, "excellent"), (10, 1.5, "good"), (5, 0.5, "fair")], False),
        ("P8", "FCF Margin", "Buffett", data.get("fcfMargin", 0), 2,
         [(15, 2, "excellent"), (8, 1.5, "good"), (3, 0.5, "fair")], False),
    ]

    for rid, name, source, value, maxPts, tiers, inv in rules:
        pts, grade = scoreTiered(value, tiers, inverse=inv)
        if rid == "P6" and value and value > 30:
            pts = min(pts, 2)
            grade = "caution"
        total += pts
        results.append(RuleResult(rid, name, source, value, pts, maxPts, grade))

    return total, results
