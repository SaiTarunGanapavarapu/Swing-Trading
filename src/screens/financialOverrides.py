skipRulesForFinancials = {
    # Profitability
    "P3",  # Operating Margin
    "P5",  # ROCE
    "P8",  # FCF Margin

    # Balance sheet (not meaningful for banks/NBFCs)
    "B2",  # Current Ratio
    "B3",  # Interest Coverage
    "B4",  # Net Debt/EBITDA
    "B5",  # FCF Positive Years
}

# Replace generic P/B rule with a bank-focused one (higher max points).
replacedRulesForFinancials = {
    "V3",
}

financialReplacementRules = {
    "FP1": {
        "name": "ROE",
        "field": "roe",
        "maxPoints": 5,
        "tiers": [(18, 5, "excellent"), (15, 3, "good"), (12, 1, "fair")],
        "inverse": False,
        "section": "profitability",
    },
    "FP2": {
        "name": "Net Margin",
        "field": "netMargin",
        "maxPoints": 4,
        "tiers": [(20, 4, "excellent"), (15, 3, "good"), (8, 1, "fair")],
        "inverse": False,
        "section": "profitability",
    },
    "FV1": {
        "name": "P/B Ratio (Bank)",
        "field": "pbRatio",
        "maxPoints": 5,
        "tiers": [(1.5, 5, "excellent"), (2.5, 3, "good"), (4.0, 1, "fair")],
        "inverse": True,
        "section": "valuation",
    },
}
