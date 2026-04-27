from ..scoringCommon import RuleResult


def score(data: dict) -> tuple[float, list[RuleResult]]:
    results = []
    total = 0

    # T1/T2/T3 stacking disabled in favor of one mutually exclusive trend alignment rule.
    # val = data.get("above200Sma")
    # pts = 1.5 if val else 0
    # total += pts
    # results.append(RuleResult("T1", "Above 200 SMA", "Technical", val, pts, 1.5, "yes" if val else "no"))
    #
    # val = data.get("above50Sma")
    # pts = 1.0 if val else 0
    # total += pts
    # results.append(RuleResult("T2", "Above 50 SMA", "Technical", val, pts, 1.0, "yes" if val else "no"))
    #
    # val = data.get("goldenAlignment")
    # pts = 1.5 if val else 0
    # total += pts
    # results.append(RuleResult("T3", "Golden Alignment", "Technical", val, pts, 1.5, "yes" if val else "no"))

    above200Sma = data.get("above200Sma")
    above50Sma = data.get("above50Sma")
    goldenAlignment = data.get("goldenAlignment")

    if goldenAlignment:
        pts, grade = 5, "excellent"
    elif above50Sma:
        pts, grade = 3, "good"
    elif above200Sma:
        pts, grade = 1, "fair"
    else:
        pts, grade = 0, "fail"
    total += pts
    results.append(RuleResult("T1", "Trend Alignment", "Technical", goldenAlignment if goldenAlignment is not None else above50Sma if above50Sma is not None else above200Sma, pts, 5, grade))

    rsi = data.get("rsi14", 50)
    if rsi is None:
        rsi = 50
    if 40 <= rsi <= 60:
        pts, grade = 1.5, "ideal"
    elif 30 <= rsi < 40 or 60 < rsi <= 70:
        pts, grade = 1, "acceptable"
    elif rsi < 30:
        pts, grade = 0.5, "oversold"
    else:
        pts, grade = 0, "overbought"
    total += pts
    results.append(RuleResult("T4", "RSI Zone", "Technical", rsi, pts, 1.5, grade))

    vr = data.get("volumeRatio", 1)
    if vr is None:
        vr = 1
    if vr >= 2.0:
        pts, grade = 1.0, "strong"
    elif vr >= 1.5:
        pts, grade = 0.75, "moderate"
    elif vr >= 1.0:
        pts, grade = 0.4, "normal"
    else:
        pts, grade = 0, "weak"
    total += pts
    results.append(RuleResult("T5", "Volume Surge", "Technical", vr, pts, 1.0, grade))

    # T6: 6-Month Momentum (excluding the most recent month)
    mom = data.get("momentum6m1m")
    if mom is None:
        pts, grade = 0, "no_data"
    elif mom > 30:
        pts, grade = 2.5, "strong"
    elif mom > 15:
        pts, grade = 2, "good"
    elif mom > 5:
        pts, grade = 1, "mild"
    elif mom > 0:
        pts, grade = 0.5, "flat"
    else:
        pts, grade = 0, "negative"
    total += pts
    results.append(RuleResult("T6", "6M Momentum", "Momentum", mom, pts, 2.5, grade))

    # ========== ATR/ADX Rules ==========
    # T7: ADX (Trend Strength)
    adx = data.get("adx")
    if adx is None:
        pts, grade = 0, "no_data"
    elif adx >= 30:
        pts, grade = 1.5, "very_strong"
    elif adx >= 25:
        pts, grade = 1.2, "strong"
    elif adx >= 20:
        pts, grade = 0.9, "moderate"
    elif adx >= 14:
        pts, grade = 0.5, "weak"
    else:
        pts, grade = 0, "very_weak"
    total += pts
    results.append(RuleResult("T7", "ADX Trend Strength", "Technical", adx, pts, 1.5, grade))

    # T8: Direction Signal (Bullish/Bearish confirmation)
    plusDi = data.get("plusDi")
    minusDi = data.get("minusDi")
    if plusDi is None or minusDi is None:
        pts, grade = 0, "no_data"
    else:
        diDiff = plusDi - minusDi
        if diDiff > 10:
            pts, grade = 1.5, "strong_bullish"
        elif diDiff > 5:
            pts, grade = 1.0, "moderate_bullish"
        elif diDiff > 0:
            pts, grade = 0.5, "weak_bullish"
        elif diDiff > -5:
            pts, grade = 0, "neutral"
        elif diDiff > -10:
            pts, grade = 0.5, "weak_bearish"
        else:
            pts, grade = 0, "strong_bearish"
    total += pts
    results.append(RuleResult("T8", "Direction Signal (+DI vs -DI)", "Technical", plusDi, pts, 1.5, grade))

    return total, results
