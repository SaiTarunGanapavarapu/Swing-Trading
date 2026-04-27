import math

import pandas as pd
import yfinance as yf

from .indicators import computeFcfMetrics, computeInterestCoverage, computeTechnicals, estimateProfitableYears
from .stockClassifier import isFinancialStock


def isNoneOrNan(value):
    return value is None or (isinstance(value, float) and math.isnan(value))


def toFloatOrNone(value):
    if isNoneOrNan(value):
        return None
    try:
        return float(value)
    except Exception:
        return None


def percentOrNone(value):
    if isNoneOrNan(value):
        return None
    try:
        valueFloat = float(value)
    except Exception:
        return None
    if abs(valueFloat) <= 1:
        return valueFloat * 100
    return valueFloat


def _getStatementMetric(frame: pd.DataFrame, candidateRows: list) -> float | None:
    if frame is None or frame.empty:
        return None
    rowLookup = {str(idx).strip().lower(): idx for idx in frame.index}
    for candidate in candidateRows:
        key = candidate.strip().lower()
        if key in rowLookup:
            row = frame.loc[rowLookup[key]]
            if isinstance(row, pd.Series):
                for v in row.tolist():
                    if pd.notna(v):
                        try:
                            return float(v)
                        except Exception:
                            continue
    return None


def _getStatementSeries(frame: pd.DataFrame, candidateRows: list) -> list:
    if frame is None or frame.empty:
        return []
    rowLookup = {str(idx).strip().lower(): idx for idx in frame.index}
    for candidate in candidateRows:
        key = candidate.strip().lower()
        if key in rowLookup:
            row = frame.loc[rowLookup[key]]
            if isinstance(row, pd.Series):
                values = []
                for v in row.tolist():
                    if pd.notna(v):
                        try:
                            values.append(float(v))
                        except Exception:
                            continue
                return values
    return []


def _computeCagr(values: list) -> float | None:
    if len(values) < 2:
        return None
    latest, oldest = values[0], values[-1]
    periods = len(values) - 1
    if periods <= 0 or latest <= 0 or oldest <= 0:
        return None
    try:
        return (latest / oldest) ** (1.0 / periods) - 1.0
    except Exception:
        return None


def _fillDerivedMetrics(ticker, raw: dict, info: dict) -> None:
    """Fill missing yfinance info metrics from financial statements."""
    try:
        inc = ticker.financials
    except Exception:
        inc = pd.DataFrame()
    try:
        bs = ticker.balance_sheet
    except Exception:
        bs = pd.DataFrame()
    try:
        cf = ticker.cashflow
    except Exception:
        cf = pd.DataFrame()

    marketCap = raw.get("marketCap") if not isNoneOrNan(raw.get("marketCap")) else None
    totalDebt = raw.get("totalDebt") if not isNoneOrNan(raw.get("totalDebt")) else None
    totalCash = raw.get("totalCash") if not isNoneOrNan(raw.get("totalCash")) else None
    ebitda = raw.get("ebitda") if not isNoneOrNan(raw.get("ebitda")) else None
    enterpriseValue = info.get("enterpriseValue") if not isNoneOrNan(info.get("enterpriseValue")) else None

    operatingIncome = _getStatementMetric(inc, ["Operating Income", "Operating Income Or Loss"])
    ebit = _getStatementMetric(inc, ["EBIT", "Ebit", "Operating Income", "Operating Income Or Loss"])
    grossProfit = _getStatementMetric(inc, ["Gross Profit"])
    totalRevenue = _getStatementMetric(inc, ["Total Revenue", "Operating Revenue", "Revenue"])
    netIncome = _getStatementMetric(inc, ["Net Income", "Net Income Common Stockholders"])
    depreciation = _getStatementMetric(cf, ["Depreciation And Amortization", "Depreciation", "Depreciation Amortization Depletion"])

    if totalDebt is None:
        totalDebt = _getStatementMetric(bs, ["Total Debt", "Total debt", "Long Term Debt", "Long Term Debt And Capital Lease Obligation", "Current Debt", "Current Debt And Capital Lease Obligation"])
    if totalCash is None:
        totalCash = _getStatementMetric(bs, ["Cash And Cash Equivalents", "Cash", "Cash Cash Equivalents And Short Term Investments"])
    if ebitda is None:
        ebitda = _getStatementMetric(inc, ["EBITDA", "Ebitda"])
    if ebitda is None and operatingIncome is not None and depreciation is not None:
        ebitda = float(operatingIncome) + abs(float(depreciation))
    if ebitda is None and operatingIncome is not None:
        ebitda = float(operatingIncome)

    if isNoneOrNan(raw.get("grossMargins")) and grossProfit is not None and totalRevenue and totalRevenue > 0:
        raw["grossMargins"] = float(grossProfit) / float(totalRevenue)

    if isNoneOrNan(raw.get("operatingMargins")) and operatingIncome is not None and totalRevenue and totalRevenue > 0:
        raw["operatingMargins"] = float(operatingIncome) / float(totalRevenue)

    if isNoneOrNan(raw.get("profitMargins")) and netIncome is not None and totalRevenue and totalRevenue > 0:
        raw["profitMargins"] = float(netIncome) / float(totalRevenue)

    if isNoneOrNan(raw.get("revenueGrowth")):
        cagr = _computeCagr(_getStatementSeries(inc, ["Total Revenue", "Operating Revenue", "Revenue"]))
        if cagr is not None:
            raw["revenueGrowth"] = cagr

    if isNoneOrNan(raw.get("earningsGrowth")):
        cagr = _computeCagr(_getStatementSeries(inc, ["Net Income", "Net Income Common Stockholders"]))
        if cagr is not None:
            raw["earningsGrowth"] = cagr
        elif not isNoneOrNan(info.get("earningsQuarterlyGrowth")):
            raw["earningsGrowth"] = float(info["earningsQuarterlyGrowth"])

    if isNoneOrNan(raw.get("currentRatio")):
        ca = _getStatementMetric(bs, ["Current Assets", "Total Current Assets"])
        cl = _getStatementMetric(bs, ["Current Liabilities", "Total Current Liabilities"])
        if ca and cl and cl > 0:
            raw["currentRatio"] = float(ca) / float(cl)
        elif not isNoneOrNan(info.get("quickRatio")):
            raw["currentRatio"] = float(info["quickRatio"])

    if isNoneOrNan(raw.get("debtToEquity")):
        equity = _getStatementMetric(bs, ["Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"])
        if totalDebt and equity and equity > 0:
            raw["debtToEquity"] = float(totalDebt) / float(equity)
        else:
            liabilities = _getStatementMetric(bs, ["Total Liabilities Net Minority Interest", "Total Liabilities"])
            if liabilities and equity and equity > 0:
                raw["debtToEquity"] = float(liabilities) / float(equity)

    if isNoneOrNan(raw.get("returnOnEquity")):
        equity = _getStatementMetric(bs, ["Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"])
        if netIncome is not None and equity and equity > 0:
            raw["returnOnEquity"] = float(netIncome) / float(equity)

    if isNoneOrNan(raw.get("financialLeverage")):
        totalAssets = _getStatementMetric(bs, ["Total Assets"])
        equity = _getStatementMetric(bs, ["Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"])
        if totalAssets is not None and equity and equity > 0:
            raw["financialLeverage"] = float(totalAssets) / float(equity)

    if isNoneOrNan(raw.get("returnOnCapitalEmployed")):
        totalAssets = _getStatementMetric(bs, ["Total Assets"])
        currentLiabilities = _getStatementMetric(bs, ["Current Liabilities", "Total Current Liabilities"])
        if ebit is not None and totalAssets is not None and currentLiabilities is not None:
            capitalEmployed = float(totalAssets) - float(currentLiabilities)
            if capitalEmployed > 0:
                raw["returnOnCapitalEmployed"] = float(ebit) / capitalEmployed

    if isNoneOrNan(raw.get("pegRatio")):
        pe = raw.get("trailingPE")
        eg = raw.get("earningsGrowth")
        if not isNoneOrNan(pe) and pe and pe > 0 and not isNoneOrNan(eg) and eg:
            growthPct = eg * 100.0 if eg <= 1 else eg
            if growthPct != 0:
                raw["pegRatio"] = float(pe) / float(growthPct)

    if isNoneOrNan(raw.get("enterpriseToEbitda")):
        if enterpriseValue and ebitda and ebitda > 0:
            raw["enterpriseToEbitda"] = float(enterpriseValue) / float(ebitda)
        elif marketCap and totalDebt is not None and totalCash is not None and ebitda and ebitda > 0:
            ev = float(marketCap) + float(totalDebt) - float(totalCash)
            raw["enterpriseToEbitda"] = ev / float(ebitda)

    if isNoneOrNan(raw.get("dividendYield")):
        price = raw.get("currentPrice") if not isNoneOrNan(raw.get("currentPrice")) else raw.get("regularMarketPrice")
        rate = info.get("trailingAnnualDividendRate") or info.get("dividendRate")
        if price and not isNoneOrNan(price) and price > 0 and rate and not isNoneOrNan(rate):
            raw["dividendYield"] = float(rate) / float(price)

    if totalDebt is not None and isNoneOrNan(raw.get("totalDebt")):
        raw["totalDebt"] = totalDebt
    if totalCash is not None and isNoneOrNan(raw.get("totalCash")):
        raw["totalCash"] = totalCash
    if ebitda is not None and isNoneOrNan(raw.get("ebitda")):
        raw["ebitda"] = ebitda


def computeDividendYears(ticker) -> int:
    try:
        dividends = ticker.dividends
        if dividends is None or dividends.empty:
            return 0
        byYear = dividends.groupby(dividends.index.year).sum()
        return int((byYear > 0).sum())
    except Exception:
        return 0


def fetchStockData(symbol: str) -> dict:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info if isinstance(ticker.info, dict) else {}

        rawInfoKeys = [
            "marketCap", "grossMargins", "operatingMargins", "profitMargins", "returnOnEquity",
            "returnOnCapitalEmployed",
            "financialLeverage",
            "trailingPE", "pegRatio", "priceToBook", "enterpriseToEbitda", "debtToEquity",
            "currentRatio", "dividendYield", "revenueGrowth", "earningsGrowth", "trailingEps",
            "bookValue", "totalDebt", "totalCash", "ebitda", "currentPrice", "regularMarketPrice",
        ]
        raw = {k: (math.nan if isNoneOrNan(info.get(k)) else info.get(k)) for k in rawInfoKeys}

        _fillDerivedMetrics(ticker, raw, info)

        def getRaw(key, default=0.0):
            v = raw.get(key, default)
            return default if isNoneOrNan(v) else v

        if not info.get("regularMarketPrice") and not info.get("currentPrice"):
            return {"symbol": symbol, "error": "No data available"}

        hist = ticker.history(period="1y")
        technicals = computeTechnicals(hist)
        technicals = {k: (math.nan if isNoneOrNan(v) else v) for k, v in technicals.items()}
        fcfMetrics = computeFcfMetrics(ticker)
        interestCoverage = computeInterestCoverage(ticker)
        profitableYears = estimateProfitableYears(ticker)
        dividendYears = computeDividendYears(ticker)

        currentPrice = getRaw("currentPrice") or getRaw("regularMarketPrice")
        if not currentPrice and hist is not None and not hist.empty:
            currentPrice = toFloatOrNone(hist["Close"].dropna().iloc[-1]) or 0.0

        marketCap = getRaw("marketCap", 0.0)
        marketCapCr = marketCap / 1e7
        sector = info.get("sector", "")
        industry = info.get("industry", "")
        isFinancial = isFinancialStock(symbol, sector, industry)

        grossMargins = getRaw("grossMargins", 0.0)
        operatingMargins = getRaw("operatingMargins", 0.0)
        profitMargins = getRaw("profitMargins", 0.0)
        roe = getRaw("returnOnEquity", 0.0)

        grossMargin = grossMargins * 100 if grossMargins else 0.0
        operatingMargin = operatingMargins * 100 if operatingMargins else 0.0
        netMargin = profitMargins * 100 if profitMargins else 0.0
        roePct = roe * 100 if roe else 0.0
        roce = toFloatOrNone(getRaw("returnOnCapitalEmployed", None))
        rocePct = percentOrNone(roce)
        if rocePct is None:
            rocePct = 0.0

        revenueGrowth = toFloatOrNone(getRaw("revenueGrowth", None))
        earningsGrowth = toFloatOrNone(getRaw("earningsGrowth", None))
        revenueGrowthPct = revenueGrowth * 100 if revenueGrowth is not None else None
        earningsGrowthPct = earningsGrowth * 100 if earningsGrowth is not None else None

        deRaw = toFloatOrNone(getRaw("debtToEquity", None))
        if deRaw is not None:
            if isFinancial:
                # Financial names can come through as values like 70-120, which map to ~7-12x leverage.
                if deRaw > 100:
                    deRaw = deRaw / 10.0
            else:
                # Non-financial D/E sometimes arrives as a percentage-style number.
                if deRaw > 5:
                    deRaw = deRaw / 100.0

        peRatio = toFloatOrNone(getRaw("trailingPE", None))
        earningsYield = (100.0 / peRatio) if peRatio and peRatio > 0 else 0.0

        eps = toFloatOrNone(getRaw("trailingEps", None))
        bookValue = toFloatOrNone(getRaw("bookValue", None))
        grahamNumber = None
        if eps and bookValue and eps > 0 and bookValue > 0:
            grahamNumber = math.sqrt(22.5 * eps * bookValue)
        grahamNumberRatio = (currentPrice / grahamNumber) if currentPrice and grahamNumber and grahamNumber > 0 else None

        totalDebt = getRaw("totalDebt", 0.0) or 0.0
        totalCash = getRaw("totalCash", 0.0) or 0.0
        ebitda = getRaw("ebitda", 0.0) or 0.0
        netDebt = totalDebt - totalCash
        netDebtToEbitda = netDebt / ebitda if ebitda > 0 else None

        dividendRate = toFloatOrNone(info.get("trailingAnnualDividendRate") or info.get("dividendRate"))
        divYield = toFloatOrNone(getRaw("dividendYield", None))
        if dividendRate is not None and currentPrice and currentPrice > 0:
            dividendYieldPct = (dividendRate / currentPrice) * 100.0
        elif divYield is None:
            dividendYieldPct = 0.0
        elif divYield <= 0.05:
            dividendYieldPct = divYield * 100.0
        elif divYield <= 20:
            dividendYieldPct = divYield
        else:
            dividendYieldPct = divYield / 100.0

        evToEbitda = toFloatOrNone(getRaw("enterpriseToEbitda", None))
        financialLeverage = toFloatOrNone(getRaw("financialLeverage", None))

        return {
            "symbol": symbol,
            "name": info.get("longName", symbol),
            "sector": sector,
            "industry": industry,
            "isFinancialStock": isFinancial,
            "financialLeverage": financialLeverage,
            "marketCapCr": marketCapCr,
            "currentPrice": currentPrice,
            "grossMargin": grossMargin,
            "operatingMargin": operatingMargin,
            "netMargin": netMargin,
            "roe": roePct,
            "roce": rocePct,
            "epsGrowth5yr": earningsGrowthPct,
            "revenueGrowth3yr": revenueGrowthPct,
            "fcfMargin": toFloatOrNone(fcfMetrics.get("fcfMargin")) or 0.0,
            "debtToEquity": deRaw,
            "currentRatio": toFloatOrNone(getRaw("currentRatio", None)),
            "interestCoverage": toFloatOrNone(interestCoverage) or 0.0,
            "netDebtToEbitda": netDebtToEbitda,
            "fcfPositiveYears": int(toFloatOrNone(fcfMetrics.get("fcfPositiveYears")) or 0),
            "peRatio": peRatio,
            "pegRatio": toFloatOrNone(getRaw("pegRatio", None)),
            "pbRatio": toFloatOrNone(getRaw("priceToBook", None)),
            "evToEbitda": evToEbitda,
            "earningsYield": earningsYield,
            "dividendYield": dividendYieldPct,
            "grahamNumber": grahamNumber,
            "grahamNumberRatio": grahamNumberRatio,
            "profitableYears": int(profitableYears or 0),
            "dividendYears": int(dividendYears),
            "promoterHolding": None,
            "promoterPledge": None,
            "error": None,
            "histRows": int(len(hist)) if hist is not None else 0,
            **technicals,
        }
    except Exception as exc:
        return {"symbol": symbol, "error": str(exc)}
