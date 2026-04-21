import math

import yfinance as yf

from .indicators import computeFcfMetrics, computeInterestCoverage, computeTechnicals, estimateProfitableYears


def safeGet(d: dict, key: str, default=None):
    if isinstance(d, dict):
        value = d.get(key, default)
        return default if value is None else value
    return default


def isNoneOrNan(value):
    return value is None or (isinstance(value, float) and math.isnan(value))


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


def toFloatOrNone(value):
    if isNoneOrNan(value):
        return None
    try:
        return float(value)
    except Exception:
        return None


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
        hist = ticker.history(period="1y", auto_adjust=False)

        technicals = computeTechnicals(hist)
        fcfMetrics = computeFcfMetrics(ticker)
        interestCoverage = computeInterestCoverage(ticker)
        profitableYears = estimateProfitableYears(ticker)
        dividendYears = computeDividendYears(ticker)

        currentPrice = toFloatOrNone(safeGet(info, "currentPrice"))
        if currentPrice is None:
            currentPrice = toFloatOrNone(safeGet(info, "regularMarketPrice"))
        if currentPrice is None and hist is not None and not hist.empty:
            currentPrice = toFloatOrNone(hist["Close"].dropna().iloc[-1])

        peRatio = toFloatOrNone(safeGet(info, "trailingPE"))
        earningsYield = (100.0 / peRatio) if peRatio and peRatio > 0 else 0.0

        eps = toFloatOrNone(safeGet(info, "trailingEps"))
        bookValue = toFloatOrNone(safeGet(info, "bookValue"))
        grahamNumber = None
        if eps and bookValue and eps > 0 and bookValue > 0:
            grahamNumber = math.sqrt(22.5 * eps * bookValue)
        grahamNumberRatio = (currentPrice / grahamNumber) if currentPrice and grahamNumber and grahamNumber > 0 else None

        marketCap = toFloatOrNone(safeGet(info, "marketCap", 0.0)) or 0.0
        marketCapCr = marketCap / 1e7

        return {
            "symbol": symbol,
            "marketCapCr": marketCapCr,
            "currentPrice": currentPrice,
            "grossMargin": percentOrNone(safeGet(info, "grossMargins")) or 0.0,
            "operatingMargin": percentOrNone(safeGet(info, "operatingMargins")) or 0.0,
            "netMargin": percentOrNone(safeGet(info, "profitMargins")) or 0.0,
            "roe": percentOrNone(safeGet(info, "returnOnEquity")) or 0.0,
            "roce": percentOrNone(safeGet(info, "returnOnAssets")) or 0.0,
            "epsGrowth5yr": percentOrNone(safeGet(info, "earningsGrowth")) or 0.0,
            "revenueGrowth3yr": percentOrNone(safeGet(info, "revenueGrowth")) or 0.0,
            "fcfMargin": toFloatOrNone(fcfMetrics.get("fcfMargin")) or 0.0,
            "debtToEquity": toFloatOrNone(safeGet(info, "debtToEquity")),
            "currentRatio": toFloatOrNone(safeGet(info, "currentRatio")) or 0.0,
            "interestCoverage": toFloatOrNone(interestCoverage) or 0.0,
            "netDebtToEbitda": toFloatOrNone(safeGet(info, "enterpriseToEbitda")),
            "fcfPositiveYears": int(toFloatOrNone(fcfMetrics.get("fcfPositiveYears")) or 0),
            "peRatio": peRatio,
            "pegRatio": toFloatOrNone(safeGet(info, "pegRatio")),
            "pbRatio": toFloatOrNone(safeGet(info, "priceToBook")),
            "evToEbitda": toFloatOrNone(safeGet(info, "enterpriseToEbitda")),
            "earningsYield": earningsYield,
            "dividendYield": percentOrNone(safeGet(info, "dividendYield")) or 0.0,
            "grahamNumber": grahamNumber,
            "grahamNumberRatio": grahamNumberRatio,
            "profitableYears": int(profitableYears or 0),
            "dividendYears": int(dividendYears),
            "promoterHolding": None,
            "promoterPledge": None,
            **technicals,
        }
    except Exception as exc:
        return {"symbol": symbol, "error": str(exc)}
