from .screens import balance_sheet, profitability, quality, red_flags, technicals, valuation


def isMissing(value) -> bool:
    return value is None or (isinstance(value, float) and value != value)


def scoreStock(data: dict) -> dict:
    if data.get("error"):
        return data

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

    scoredData = dict(data)
    scoredData.update(
        {
            "totalScore": totalScore,
            "total_score": totalScore,
            "scoreOutOf": 100.0,
            "dataCoveragePct": 100.0,
            "grade": grade,
            "intrinsicScore": totalScore,
            "dataConfidence": 100.0,
            "finalScore": totalScore,
            "profitabilityScore": round(profitabilityScore, 1),
            "balanceSheetScore": round(balanceSheetScore, 1),
            "valuationScore": round(valuationScore, 1),
            "qualityScore": round(qualityScore, 1),
            "technicalScore": round(technicalScore, 1),
            "flags": " | ".join(flags),
        }
    )
    return scoredData
