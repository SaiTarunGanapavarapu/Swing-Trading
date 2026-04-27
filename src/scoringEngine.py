from .screens import balanceSheet, profitability, quality, redFlags, technicals, valuation
from .scoringCommon import RuleResult, scoreTiered
from .stockClassifier import isFinancialStock


def isMissing(value) -> bool:
    return value is None or (isinstance(value, float) and value != value)


def normalizeScore(rawScore: float, rawMaxScore: float, targetMaxScore: float) -> float:
    if rawMaxScore <= 0:
        return 0.0
    return round((rawScore / rawMaxScore) * targetMaxScore, 1)


def getRawMaxScore(ruleResults: list, excludedRuleIds: set[str] | None = None) -> float:
    excluded = excludedRuleIds or set()
    return float(sum(rule.maxScore for rule in ruleResults if rule.ruleId not in excluded))


def normalizeScoringInput(data: dict) -> dict:
    normalizedData = dict(data)
    keyMap = {
        "market_cap_cr": "marketCapCr",
        "current_price": "currentPrice",
        "gross_margin": "grossMargin",
        "operating_margin": "operatingMargin",
        "net_margin": "netMargin",
        "eps_growth_5yr": "epsGrowth5yr",
        "revenue_growth_3yr": "revenueGrowth3yr",
        "fcf_margin": "fcfMargin",
        "debt_to_equity": "debtToEquity",
        "current_ratio": "currentRatio",
        "interest_coverage": "interestCoverage",
        "net_debt_to_ebitda": "netDebtToEbitda",
        "fcf_positive_years": "fcfPositiveYears",
        "pe_ratio": "peRatio",
        "peg_ratio": "pegRatio",
        "pb_ratio": "pbRatio",
        "ev_to_ebitda": "evToEbitda",
        "earnings_yield": "earningsYield",
        "dividend_yield": "dividendYield",
        "graham_number": "grahamNumber",
        "graham_number_ratio": "grahamNumberRatio",
        "profitable_years": "profitableYears",
        "dividend_years": "dividendYears",
        "promoter_holding": "promoterHolding",
        "promoter_pledge": "promoterPledge",
        "above_200sma": "above200Sma",
        "above_50sma": "above50Sma",
        "golden_alignment": "goldenAlignment",
        "rsi_14": "rsi14",
        "volume_ratio": "volumeRatio",
        "pct_from_52w_high": "pctFrom52wHigh",
        "momentum_6m_1m": "momentum6m1m",
        "momentum6m1m": "momentum6m1m",
        "macd_bullish": "macdBullish",
        "atr": "atr",
        "adx": "adx",
        "plus_di": "plusDi",
        "minus_di": "minusDi",
        "strong_trend": "strongTrend",
        "buy_signal": "buySignal",
    }

    for sourceKey, targetKey in keyMap.items():
        if targetKey not in normalizedData and sourceKey in normalizedData:
            normalizedData[targetKey] = normalizedData.get(sourceKey)

    return normalizedData


def scoreFinancialProfitability(data: dict) -> tuple[float, list[RuleResult]]:
    results = []
    total = 0.0

    roe = data.get("roe")
    points, grade = scoreTiered(roe, [(18, 5, "excellent"), (15, 3, "good"), (12, 1, "fair")], False)
    total += points
    results.append(RuleResult("FP1", "ROE", "Buffett", roe, points, 5, grade))

    netMargin = data.get("netMargin")
    points, grade = scoreTiered(netMargin, [(20, 4, "excellent"), (15, 3, "good"), (8, 1, "fair")], False)
    total += points
    results.append(RuleResult("FP2", "Net Margin", "Buffett", netMargin, points, 4, grade))

    epsGrowth = data.get("epsGrowth5yr")
    points, grade = scoreTiered(epsGrowth, [(20, 4, "excellent"), (15, 3, "good"), (10, 1, "fair")], False)
    if epsGrowth and epsGrowth > 30:
        points = min(points, 2)
        grade = "caution"
    total += points
    results.append(RuleResult("FP3", "EPS Growth", "Lynch", epsGrowth, points, 4, grade))

    revenueGrowth = data.get("revenueGrowth3yr")
    points, grade = scoreTiered(revenueGrowth, [(20, 2, "excellent"), (10, 1.5, "good"), (5, 0.5, "fair")], False)
    total += points
    results.append(RuleResult("FP4", "Revenue Growth 3Y", "Lynch", revenueGrowth, points, 2, grade))

    return total, results


def scoreFinancialBalanceSheet(data: dict) -> tuple[float, list[RuleResult]]:
    results = []
    total = 0.0

    financialLeverage = data.get("financialLeverage")
    if financialLeverage is not None:
        if financialLeverage > 16:
            points, grade = 0, "CRITICAL_LEVERAGE"
        elif financialLeverage <= 4.5:
            points, grade = 4, "conservative"
        elif financialLeverage <= 8.5:
            points, grade = 3, "moderate"
        elif financialLeverage <= 11.0:
            points, grade = 1, "aggressive"
        else:
            points, grade = 0, "very_aggressive"
    else:
        debtToEquity = data.get("debtToEquity")
        if debtToEquity is not None and debtToEquity > 15.0:
            points, grade = 0, "CRITICAL_LEVERAGE"
        elif debtToEquity is not None:
            if debtToEquity <= 6:
                points, grade = 4, "conservative"
            elif debtToEquity <= 9:
                points, grade = 3, "moderate"
            elif debtToEquity <= 12:
                points, grade = 1, "aggressive"
            else:
                points, grade = 0, "very_aggressive"
        else:
            points, grade = 2, "unknown"
    total += points
    displayValue = financialLeverage if financialLeverage is not None else data.get("debtToEquity")
    displayName = "Financial Leverage (Assets/Equity)" if financialLeverage is not None else "D/E (Bank Scale)"
    results.append(RuleResult("FB1", displayName, "Graham", displayValue, points, 4, grade))

    return total, results


def scoreFinancialValuation(data: dict) -> tuple[float, list[RuleResult]]:
    results = []
    total = 0.0

    pbRatio = data.get("pbRatio")
    if pbRatio and pbRatio > 0:
        points, grade = scoreTiered(pbRatio, [(1.2, 5, "excellent"), (2.0, 3, "good"), (3.5, 1, "fair")], True)
    else:
        points, grade = 0, "N/A"
    total += points
    results.append(RuleResult("FV1", "P/B Ratio", "Graham", pbRatio, points, 5, grade))

    peRatio = data.get("peRatio")
    if peRatio and peRatio > 0:
        points, grade = scoreTiered(peRatio, [(12, 4, "excellent"), (18, 3, "good"), (25, 1, "fair")], True)
    elif peRatio and peRatio < 0:
        points, grade = 0, "loss_making"
    else:
        points, grade = 0, "N/A"
    total += points
    results.append(RuleResult("FV2", "P/E Ratio", "Graham", peRatio, points, 4, grade))

    pegRatio = data.get("pegRatio")
    if pegRatio and pegRatio > 0:
        points, grade = scoreTiered(pegRatio, [(0.5, 3, "excellent"), (1.0, 2, "good"), (1.5, 1, "fair")], True)
    else:
        points, grade = 0, "N/A"
    total += points
    results.append(RuleResult("FV3", "PEG Ratio", "Lynch", pegRatio, points, 3, grade))

    dividendYield = data.get("dividendYield")
    points, grade = scoreTiered(dividendYield, [(3.0, 2, "excellent"), (1.5, 1.5, "good"), (0.5, 0.5, "fair")], False)
    total += points
    results.append(RuleResult("FV4", "Dividend Yield", "Graham", dividendYield, points, 2, grade))

    return total, results


def scoreStock(data: dict) -> dict:
    if data.get("error"):
        return data

    data = normalizeScoringInput(data)
    isFinancial = bool(
        data.get("isFinancialStock")
        if data.get("isFinancialStock") is not None
        else isFinancialStock(data.get("symbol", ""), data.get("sector", ""), data.get("industry", ""))
    )
    data["isFinancial"] = isFinancial
    data["isFinancialStock"] = isFinancial

    if isFinancial:
        profitabilityScore, profitabilityRules = scoreFinancialProfitability(data)
        balanceSheetScore, balanceSheetRules = scoreFinancialBalanceSheet(data)
        valuationScore, valuationRules = scoreFinancialValuation(data)
    else:
        profitabilityScore, profitabilityRules = profitability.score(data)
        balanceSheetScore, balanceSheetRules = balanceSheet.score(data)
        valuationScore, valuationRules = valuation.score(data)
    qualityScore, qualityRules = quality.score(data)
    technicalScore, technicalRules = technicals.score(data)
    flags = redFlags.detect(data)

    profitabilityRawScore = float(sum(rule.score for rule in profitabilityRules))
    balanceSheetRawScore = float(sum(rule.score for rule in balanceSheetRules))
    valuationRawScore = float(sum(rule.score for rule in valuationRules))
    qualityRawScore = float(sum(rule.score for rule in qualityRules))
    technicalRawScore = float(sum(rule.score for rule in technicalRules))

    if isFinancial:
        profitabilityScore = normalizeScore(profitabilityRawScore, getRawMaxScore(profitabilityRules), 30.0)
        balanceSheetScore = normalizeScore(balanceSheetRawScore, getRawMaxScore(balanceSheetRules), 20.0)
        valuationScore = normalizeScore(valuationRawScore, getRawMaxScore(valuationRules), 25.0)
    else:
        profitabilityScore = normalizeScore(profitabilityRawScore, getRawMaxScore(profitabilityRules), 30.0)
        balanceSheetScore = normalizeScore(balanceSheetRawScore, getRawMaxScore(balanceSheetRules, {"B1"}), 20.0)
        valuationScore = normalizeScore(valuationRawScore, getRawMaxScore(valuationRules, {"V1", "V6"}), 25.0)

    qualityScore = normalizeScore(qualityRawScore, getRawMaxScore(qualityRules), 15.0)
    technicalScore = normalizeScore(technicalRawScore, getRawMaxScore(technicalRules), 10.0)

    totalRawScore = profitabilityScore + balanceSheetScore + valuationScore + qualityScore + technicalScore
    penalty = 2.0 * sum(1 for flag in flags if "🚨" in flag)
    totalScore = max(0.0, round(totalRawScore - penalty, 1))

    if totalScore >= 70:
        grade = "🟢 Buy"
    elif totalScore >= 55:
        grade = "🟠 Hold"
    elif totalScore >= 40:
        grade = "🟡 Watchlist"
    else:
        grade = "🔴 Avoid"

    coverageKeys = [
        "marketCapCr",
        "currentPrice",
        "grossMargin",
        "operatingMargin",
        "netMargin",
        "roe",
        "roce",
        "epsGrowth5yr",
        "revenueGrowth3yr",
        "fcfMargin",
        "debtToEquity",
        "currentRatio",
        "interestCoverage",
        "netDebtToEbitda",
        "fcfPositiveYears",
        "peRatio",
        "pegRatio",
        "pbRatio",
        "evToEbitda",
        "earningsYield",
        "dividendYield",
        "grahamNumber",
        "grahamNumberRatio",
        "profitableYears",
        "dividendYears",
        # "promoterHolding",
        # "promoterPledge",
        "above200Sma",
        "above50Sma",
        "goldenAlignment",
        "rsi14",
        "volumeRatio",
        "momentum6m1m",
        "macdBullish",
    ]

    availableCount = sum(1 for key in coverageKeys if not isMissing(data.get(key)))
    dataCoveragePct = round((100.0 * availableCount / len(coverageKeys)), 1) if coverageKeys else 0.0

    confidenceWeights = {
        "marketCapCr": 3.0,
        "currentPrice": 1.0,
        "grossMargin": 2.0,
        "operatingMargin": 2.0,
        "netMargin": 2.0,
        "roe": 3.0,
        "roce": 2.0,
        "epsGrowth5yr": 2.0,
        "revenueGrowth3yr": 2.0,
        "fcfMargin": 2.0,
        "debtToEquity": 3.0,
        "currentRatio": 3.0,
        "interestCoverage": 2.0,
        "netDebtToEbitda": 2.0,
        "fcfPositiveYears": 1.5,
        "peRatio": 3.0,
        "pegRatio": 2.0,
        "pbRatio": 2.0,
        "evToEbitda": 2.5,
        "earningsYield": 1.5,
        "dividendYield": 1.5,
        "grahamNumber": 1.5,
        "grahamNumberRatio": 1.5,
        "profitableYears": 1.5,
        "dividendYears": 1.0,
        # "promoterHolding": 1.0,
        # "promoterPledge": 1.0,
        "above200Sma": 1.0,
        "above50Sma": 1.0,
        "goldenAlignment": 1.0,
        "rsi14": 1.0,
        "volumeRatio": 1.0,
        "momentum6m1m": 1.0,
        "macdBullish": 1.0,
    }
    weightTotal = sum(confidenceWeights.values())
    weightedAvailable = sum(weight for key, weight in confidenceWeights.items() if not isMissing(data.get(key)))
    dataConfidence = round((100.0 * weightedAvailable / weightTotal), 1) if weightTotal > 0 else 0.0

    intrinsicScore = totalScore
    scoreOutOf = round(100.0 * (dataCoveragePct / 100.0), 1)
    # finalScore is intentionally disabled because ranking uses totalScore.
    # finalScore = round(intrinsicScore * (0.5 + 0.5 * (dataConfidence / 100.0)), 1)

    # Flatten z-scores from _zscores dict into individual columns for reporting
    zScoresFlat = {}
    zscoresDict = data.get("_zscores", {})
    for metricKey, zscoreValue in zscoresDict.items():
        if zscoreValue is not None:
            zScoresFlat[metricKey] = round(zscoreValue, 2)

    scoredData = dict(data)
    scoredData.update(
        {
            "totalScore": totalScore,
            "total_score": totalScore,
            "scoreOutOf": scoreOutOf,
            "score_out_of": scoreOutOf,
            "dataCoveragePct": dataCoveragePct,
            "data_coverage_pct": dataCoveragePct,
            "grade": grade,
            "intrinsicScore": intrinsicScore,
            "dataConfidence": dataConfidence,
            "data_confidence": dataConfidence,
            # "finalScore": finalScore,
            "profitabilityScore": round(profitabilityScore, 1),
            "profitability": round(profitabilityScore, 1),
            "balanceSheetScore": round(balanceSheetScore, 1),
            "balance_sheet": round(balanceSheetScore, 1),
            "valuationScore": round(valuationScore, 1),
            "valuation": round(valuationScore, 1),
            "qualityScore": round(qualityScore, 1),
            "quality": round(qualityScore, 1),
            "technicalScore": round(technicalScore, 1),
            "technicals": round(technicalScore, 1),
            "flags": " | ".join(flags),
            "red_flags": " | ".join(flags),

            # Reporting compatibility aliases.
            "pe": data.get("peRatio"),
            "de": data.get("debtToEquity"),
            "rsi": data.get("rsi14"),
            "isFinancial": isFinancial,
        }
    )
    scoredData.update(zScoresFlat)
    return scoredData
