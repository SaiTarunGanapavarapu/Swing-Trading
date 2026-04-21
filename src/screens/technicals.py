from ..scoring_common import RuleResult


def score(data: dict) -> tuple[float, list[RuleResult]]:
    results = []
    total = 0

    val = data.get("above200Sma")
    pts = 2 if val else 0
    total += pts
    results.append(RuleResult("T1", "Above 200 SMA", "Technical", val, pts, 2, "yes" if val else "no"))

    val = data.get("above50Sma")
    pts = 1.5 if val else 0
    total += pts
    results.append(RuleResult("T2", "Above 50 SMA", "Technical", val, pts, 1.5, "yes" if val else "no"))

    val = data.get("goldenAlignment")
    pts = 2 if val else 0
    total += pts
    results.append(RuleResult("T3", "Golden Alignment", "Technical", val, pts, 2, "yes" if val else "no"))

    rsi = data.get("rsi14", 50)
    if rsi is None:
        rsi = 50
    if 40 <= rsi <= 60:
        pts, grade = 2, "ideal"
    elif 30 <= rsi < 40 or 60 < rsi <= 70:
        pts, grade = 1, "acceptable"
    elif rsi < 30:
        pts, grade = 0.5, "oversold"
    else:
        pts, grade = 0, "overbought"
    total += pts
    results.append(RuleResult("T4", "RSI Zone", "Technical", rsi, pts, 2, grade))

    vr = data.get("volumeRatio", 1)
    if vr is None:
        vr = 1
    if vr >= 2.0:
        pts, grade = 1.5, "strong"
    elif vr >= 1.5:
        pts, grade = 1, "moderate"
    elif vr >= 1.0:
        pts, grade = 0.5, "normal"
    else:
        pts, grade = 0, "weak"
    total += pts
    results.append(RuleResult("T5", "Volume Surge", "Technical", vr, pts, 1.5, grade))

    pct = data.get("pctFrom52wHigh", 100)
    if pct is None:
        pct = 100
    if pct <= 10:
        pts, grade = 1, "near_high"
    elif pct <= 20:
        pts, grade = 0.5, "moderate"
    else:
        pts, grade = 0, "far"
    total += pts
    results.append(RuleResult("T6", "Near 52W High", "Technical", pct, pts, 1, grade))

    return total, results
