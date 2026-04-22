from ..scoringCommon import RuleResult, scoreTiered, scoreTieredZScore


def score(data: dict) -> tuple[float, list[RuleResult]]:
    results = []
    total = 0

    # Helper function to score metrics with z-score fallback
    def scoreMetric(rid, name, source, value, maxPts, tiers, inverse, check_eps_caution=False):
        pts, grade = scoreTiered(value, tiers, inverse=inverse)
        display_value = value
        display_name = name
        
        # Special check for EPS growth caution
        if check_eps_caution and value and value > 30:
            pts = min(pts, 2)
            grade = "caution"
        
        return pts, display_name, display_value, grade

    rules = [
        ("P1", "Gross Margin", "Buffett", data.get("grossMargin", 0), 5,
         [(60, 5, "excellent"), (40, 3, "good"), (20, 1, "fair")], False, False),
        ("P2", "Net Margin", "Buffett", data.get("netMargin", 0), 4,
         [(25, 4, "excellent"), (20, 3, "good"), (10, 1, "fair")], False, False),
        ("P3", "Operating Margin", "Buffett", data.get("operatingMargin", 0), 4,
         [(25, 4, "excellent"), (15, 3, "good"), (10, 1, "fair")], False, False),
        ("P4", "ROE", "Buffett", data.get("roe", 0), 5,
         [(25, 5, "excellent"), (20, 3, "good"), (15, 1, "fair")], False, False),
        ("P5", "ROCE", "Buffett/Graham", data.get("roce", 0), 4,
         [(25, 4, "excellent"), (15, 3, "good"), (10, 1, "fair")], False, False),
        ("P6", "EPS Growth", "Lynch", data.get("epsGrowth5yr", 0), 4,
         [(20, 4, "excellent"), (15, 3, "good"), (10, 1, "fair")], False, True),
        ("P7", "Revenue Growth 3Y", "Lynch", data.get("revenueGrowth3yr", 0), 2,
         [(20, 2, "excellent"), (10, 1.5, "good"), (5, 0.5, "fair")], False, False),
        ("P8", "FCF Margin", "Buffett", data.get("fcfMargin", 0), 2,
         [(15, 2, "excellent"), (8, 1.5, "good"), (3, 0.5, "fair")], False, False),
    ]

    for rid, name, source, value, maxPts, tiers, inv, check_caution in rules:
        display_name = name
        display_value = value
        
        # Try z-score for growth metrics
        if rid in ["P6", "P7"]:
            metric_key = "epsGrowth5yr" if rid == "P6" else "revenueGrowth3yr"
            zscore = data.get("_zscores", {}).get(f"{metric_key}_zscore")
            
            if zscore is not None:
                # For growth metrics (higher is better): z > 0.5 is excellent, z > -0.5 is good
                if rid == "P6":
                    pts, grade = scoreTieredZScore(zscore, [(0.5, 4, "excellent"), (0.0, 3, "good"), (-0.5, 1, "fair")], inverse=False)
                    display_name = "EPS Growth Z-Score"
                else:
                    pts, grade = scoreTieredZScore(zscore, [(0.5, 2, "excellent"), (0.0, 1.5, "good"), (-0.5, 0.5, "fair")], inverse=False)
                    display_name = "Revenue Growth 3Y Z-Score"
                
                display_value = zscore
                
                # Check for EPS growth caution
                if check_caution and value and value > 30:
                    pts = min(pts, 2)
                    grade = "caution"
                    display_name = name
                    display_value = value
            else:
                # Fallback to raw value
                pts, grade = scoreTiered(value, tiers, inverse=inv)
                if check_caution and value and value > 30:
                    pts = min(pts, 2)
                    grade = "caution"
        else:
            # Non-growth metrics: always use raw value
            pts, grade = scoreTiered(value, tiers, inverse=inv)
        
        total += pts
        results.append(RuleResult(rid, display_name, source, display_value, pts, maxPts, grade))

    return total, results
