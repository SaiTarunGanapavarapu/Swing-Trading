import math

import pandas as pd


def computeTechnicals(hist: pd.DataFrame) -> dict:
    if hist.empty or len(hist) < 50:
        return {
            "above_200sma": None,
            "above_50sma": None,
            "golden_alignment": None,
            "rsi_14": None,
            "volume_ratio": None,
            "pct_from_52w_high": None,
            "macd_bullish": None,
        }

    close = hist["Close"]
    volume = hist["Volume"]

    sma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else close.mean()
    sma50 = close.rolling(50).mean().iloc[-1]
    ema21 = close.ewm(span=21).mean().iloc[-1]
    price = close.iloc[-1]

    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = (100 - (100 / (1 + rs))).iloc[-1]

    volAvg = volume.rolling(20).mean().iloc[-1]
    volRatio = volume.iloc[-1] / volAvg if volAvg > 0 else 1

    high52w = hist["High"].dropna().max()
    pctFromHigh = ((high52w - price) / high52w) * 100 if high52w > 0 else 0

    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    macdBull = macd.iloc[-1] > signal.iloc[-1]

    return {
        "above_200sma": price > sma200,
        "above_50sma": price > sma50,
        "golden_alignment": (ema21 > sma50) and (sma50 > sma200) if len(close) >= 200 else False,
        "rsi_14": rsi if not math.isnan(rsi) else 50,
        "volume_ratio": volRatio,
        "pct_from_52w_high": pctFromHigh,
        "macd_bullish": macdBull,
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
