from .screens import balanceSheet, profitability, quality, redFlags, technicals, valuation


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


def scoreStock(data: dict) -> dict:
    if data.get("error"):
        return data

    data = normalizeScoringInput(data)

    profitabilityScore, profitabilityRules = profitability.score(data)
    balanceSheetScore, balanceSheetRules = balanceSheet.score(data)
    valuationScore, valuationRules = valuation.score(data)
    qualityScore, qualityRules = quality.score(data)
    technicalScore, technicalRules = technicals.score(data)
    flags = redFlags.detect(data)

    # Keep the public section scores normalized to the original 100-point layout,
    # but derive each section's raw max from active rule metadata.
    profitabilityScore = normalizeScore(profitabilityScore, getRawMaxScore(profitabilityRules), 30.0)
    balanceSheetScore = normalizeScore(balanceSheetScore, getRawMaxScore(balanceSheetRules, {"B1"}), 20.0)
    valuationScore = normalizeScore(valuationScore, getRawMaxScore(valuationRules, {"V1", "V6"}), 25.0)
    qualityScore = normalizeScore(qualityScore, getRawMaxScore(qualityRules), 15.0)
    technicalScore = normalizeScore(technicalScore, getRawMaxScore(technicalRules), 10.0)

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
        }
    )
    scoredData.update(zScoresFlat)
    return scoredData
