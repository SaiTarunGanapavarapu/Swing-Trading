from .screens import balance_sheet, profitability, quality, red_flags, technicals, valuation


def isMissing(value) -> bool:
    return value is None or (isinstance(value, float) and value != value)


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
        "macd_bullish": "macdBullish",
    }

    for sourceKey, targetKey in keyMap.items():
        if targetKey not in normalizedData and sourceKey in normalizedData:
            normalizedData[targetKey] = normalizedData.get(sourceKey)

    return normalizedData


def scoreStock(data: dict) -> dict:
    if data.get("error"):
        return data

    data = normalizeScoringInput(data)

    profitabilityScore, _ = profitability.score(data)
    balanceSheetScore, _ = balance_sheet.score(data)
    valuationScore, _ = valuation.score(data)
    qualityScore, _ = quality.score(data)
    technicalScore, _ = technicals.score(data)
    flags = red_flags.detect(data)

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
        "promoterHolding",
        "promoterPledge",
        "above200Sma",
        "above50Sma",
        "goldenAlignment",
        "rsi14",
        "volumeRatio",
        "pctFrom52wHigh",
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
        "promoterHolding": 1.0,
        "promoterPledge": 1.0,
        "above200Sma": 1.0,
        "above50Sma": 1.0,
        "goldenAlignment": 1.0,
        "rsi14": 1.0,
        "volumeRatio": 1.0,
        "pctFrom52wHigh": 1.0,
        "macdBullish": 1.0,
    }
    weightTotal = sum(confidenceWeights.values())
    weightedAvailable = sum(weight for key, weight in confidenceWeights.items() if not isMissing(data.get(key)))
    dataConfidence = round((100.0 * weightedAvailable / weightTotal), 1) if weightTotal > 0 else 0.0

    intrinsicScore = totalScore
    scoreOutOf = round(100.0 * (dataCoveragePct / 100.0), 1)
    finalScore = round(intrinsicScore * (0.5 + 0.5 * (dataConfidence / 100.0)), 1)

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
            "finalScore": finalScore,
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
    return scoredData
