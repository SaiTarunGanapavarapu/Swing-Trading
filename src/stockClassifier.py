_financialSectors = {
    "financial services",
    "financial",
}

_financialIndustries = {
    "banks",
    "bank",
    "insurance",
    "credit services",
    "capital markets",
    "financial data",
    "stock exchanges",
    "asset management",
    "financial conglomerates",
}

_forceFinancial = {
    "BAJAJFINSV.NS",
    "JIOFIN.NS",
}

_forceNonFinancial = {
    # Add symbols here if a stock is wrongly tagged as financial.
}


def isFinancialStock(symbol: str, sector: str = "", industry: str = "") -> bool:
    """Detect whether a stock should be treated as financial."""
    symbolUpper = symbol.upper().strip()

    if symbolUpper in _forceNonFinancial:
        return False
    if symbolUpper in _forceFinancial:
        return True

    sectorLower = (sector or "").lower().strip()
    industryLower = (industry or "").lower().strip()

    for keyword in _financialSectors:
        if keyword in sectorLower:
            return True

    for keyword in _financialIndustries:
        if keyword in industryLower:
            return True

    return False
