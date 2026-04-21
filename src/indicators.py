import math

import pandas as pd

from .momentum_indicators import computeExtendedTechnicals


def computeTechnicals(hist: pd.DataFrame) -> dict:
    """
    Compute all technical indicators including ATR, ADX, RSI, MACD, and price action.
    Returns data in snake_case format for compatibility with existing code.
    """
    # Use the extended technicals which includes ATR/ADX
    result = computeExtendedTechnicals(hist)
    
    # Convert camelCase keys to snake_case for backward compatibility
    return {
        "above_200sma": result.get("above_200sma"),
        "above_50sma": result.get("above_50sma"),
        "golden_alignment": result.get("golden_alignment"),
        "rsi_14": result.get("rsi_14"),
        "volume_ratio": result.get("volume_ratio"),
        "pct_from_52w_high": result.get("pct_from_52w_high"),
        "macd_bullish": result.get("macd_bullish"),
        # New ATR/ADX fields
        "atr": result.get("atr"),
        "adx": result.get("adx"),
        "plus_di": result.get("plus_di"),
        "minus_di": result.get("minus_di"),
        "strong_trend": result.get("strong_trend"),
        "buy_signal": result.get("buy_signal"),
    }


def computeFcfMetrics(ticker) -> dict:
    try:
        cf = ticker.cashflow
        fin = ticker.financials
        if cf is None or cf.empty:
            return {"fcfMargin": 0, "fcfPositiveYears": 0}

        ocf = cf.loc["Operating Cash Flow"] if "Operating Cash Flow" in cf.index else None
        capex = cf.loc["Capital Expenditure"] if "Capital Expenditure" in cf.index else None

        if ocf is None:
            return {"fcfMargin": 0, "fcfPositiveYears": 0}

        if capex is not None:
            fcf = ocf + capex
        else:
            fcf = ocf

        positiveYears = (fcf > 0).sum()

        revenue = None
        if fin is not None and not fin.empty and "Total Revenue" in fin.index:
            revenue = fin.loc["Total Revenue"].iloc[0]

        fcfMargin = 0
        if revenue and revenue > 0 and len(fcf) > 0:
            fcfMargin = (fcf.iloc[0] / revenue) * 100

        return {"fcfMargin": fcfMargin, "fcfPositiveYears": int(positiveYears)}
    except Exception:
        return {"fcfMargin": 0, "fcfPositiveYears": 0}


def computeInterestCoverage(ticker) -> float:
    try:
        fin = ticker.financials
        if fin is None or fin.empty:
            return 99
        ebit = fin.loc["EBIT"].iloc[0] if "EBIT" in fin.index else None
        interest = fin.loc["Interest Expense"].iloc[0] if "Interest Expense" in fin.index else None
        if ebit and interest and interest < 0:
            return abs(ebit / interest)
        return 99
    except Exception:
        return 99


def estimateProfitableYears(ticker) -> int:
    try:
        fin = ticker.financials
        if fin is None or fin.empty:
            return 0
        if "Net Income" in fin.index:
            ni = fin.loc["Net Income"]
            return int((ni > 0).sum())
        return 0
    except Exception:
        return 0
