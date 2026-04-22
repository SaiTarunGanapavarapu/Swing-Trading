import pandas as pd


def _computeAtrAndAdx(hist: pd.DataFrame, period: int = 14) -> dict:
    if hist.empty or len(hist) < period + 1:
        return {
            "atr": None,
            "adx": None,
            "plusDi": None,
            "minusDi": None,
            "strongTrend": False,
            "buySignal": False,
        }

    df = hist.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(-1)

    prevClose = df["Close"].shift(1)
    trueRange = pd.concat(
        [
            df["High"] - df["Low"],
            (df["High"] - prevClose).abs(),
            (df["Low"] - prevClose).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = trueRange.rolling(window=period).mean()

    upMove = df["High"] - df["High"].shift(1)
    downMove = df["Low"].shift(1) - df["Low"]
    plusDm = upMove.where((upMove > downMove) & (upMove > 0), 0.0)
    minusDm = downMove.where((downMove > upMove) & (downMove > 0), 0.0)

    plusDmSmooth = plusDm.rolling(window=period).mean()
    minusDmSmooth = minusDm.rolling(window=period).mean()

    # Wilder-style recursive smoothing.
    for index in range(period, len(df)):
        atr.iloc[index] = ((atr.iloc[index - 1] * (period - 1)) + trueRange.iloc[index]) / period
        plusDmSmooth.iloc[index] = ((plusDmSmooth.iloc[index - 1] * (period - 1)) + plusDm.iloc[index]) / period
        minusDmSmooth.iloc[index] = ((minusDmSmooth.iloc[index - 1] * (period - 1)) + minusDm.iloc[index]) / period

    plusDi = (plusDmSmooth / atr) * 100
    minusDi = (minusDmSmooth / atr) * 100
    dx = ((plusDi - minusDi).abs() / (plusDi + minusDi)) * 100
    adx = dx.rolling(window=period).mean()

    firstAdxIndex = adx.first_valid_index()
    if firstAdxIndex is not None:
        firstAdxPosition = df.index.get_loc(firstAdxIndex)
        for index in range(firstAdxPosition + 1, len(df)):
            previousAdx = adx.iloc[index - 1]
            currentDx = dx.iloc[index]
            if pd.isna(previousAdx) or pd.isna(currentDx):
                continue
            adx.iloc[index] = ((previousAdx * (period - 1)) + currentDx) / period

    atrValue = None if pd.isna(atr.iloc[-1]) else float(atr.iloc[-1])
    adxValue = None if pd.isna(adx.iloc[-1]) else float(adx.iloc[-1])
    plusDiValue = None if pd.isna(plusDi.iloc[-1]) else float(plusDi.iloc[-1])
    minusDiValue = None if pd.isna(minusDi.iloc[-1]) else float(minusDi.iloc[-1])

    strongTrend = bool(adxValue and adxValue > 25)
    buySignal = bool(adxValue and plusDiValue and minusDiValue and adxValue > 25 and plusDiValue > minusDiValue)

    return {
        "atr": atrValue,
        "adx": adxValue,
        "plusDi": plusDiValue,
        "minusDi": minusDiValue,
        "strongTrend": strongTrend,
        "buySignal": buySignal,
    }


def computeTechnicalIndicators(hist: pd.DataFrame) -> dict:
    if hist.empty:
        return {
            "above200Sma": None,
            "above50Sma": None,
            "goldenAlignment": None,
            "rsi14": None,
            "volumeRatio": None,
            "pctFrom52wHigh": None,
            "macdBullish": None,
            "atr": None,
            "adx": None,
            "plusDi": None,
            "minusDi": None,
            "strongTrend": False,
            "buySignal": False,
        }

    histDf = hist.copy()
    if isinstance(histDf.columns, pd.MultiIndex):
        histDf.columns = histDf.columns.droplevel(-1)

    # yfinance can include a trailing in-progress row with missing OHLC values.
    # Drop incomplete rows so recursive ATR/ADX smoothing does not end on NaN.
    histDf = histDf.dropna(subset=["Close", "High", "Low"])

    if histDf.empty or len(histDf) < 50:
        return {
            "above200Sma": None,
            "above50Sma": None,
            "goldenAlignment": None,
            "rsi14": None,
            "volumeRatio": None,
            "pctFrom52wHigh": None,
            "macdBullish": None,
            "atr": None,
            "adx": None,
            "plusDi": None,
            "minusDi": None,
            "strongTrend": False,
            "buySignal": False,
        }

    close = histDf["Close"]
    volume = histDf["Volume"]

    sma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else close.mean()
    sma50 = close.rolling(50).mean().iloc[-1]
    ema21 = close.ewm(span=21).mean().iloc[-1]
    price = close.iloc[-1]

    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = (100 - (100 / (1 + rs))).iloc[-1]
    if pd.isna(rsi):
        rsi = 50

    volAvg = volume.rolling(20).mean().iloc[-1]
    volRatio = volume.iloc[-1] / volAvg if volAvg > 0 else 1

    high52w = histDf["High"].dropna().max()
    pctFromHigh = ((high52w - price) / high52w) * 100 if high52w > 0 else 0

    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    macdBull = macd.iloc[-1] > signal.iloc[-1]

    atrAdxData = _computeAtrAndAdx(histDf, period=14)

    return {
        "above200Sma": bool(price > sma200),
        "above50Sma": bool(price > sma50),
        "goldenAlignment": bool((ema21 > sma50) and (sma50 > sma200)) if len(close) >= 200 else False,
        "rsi14": float(rsi),
        "volumeRatio": float(volRatio),
        "pctFrom52wHigh": float(pctFromHigh),
        "macdBullish": bool(macdBull),
        "atr": atrAdxData.get("atr"),
        "adx": atrAdxData.get("adx"),
        "plusDi": atrAdxData.get("plusDi"),
        "minusDi": atrAdxData.get("minusDi"),
        "strongTrend": atrAdxData.get("strongTrend", False),
        "buySignal": atrAdxData.get("buySignal", False),
    }


def computeTechnicals(hist: pd.DataFrame) -> dict:
    # Backward-compatible wrapper used by fetcher.
    return computeTechnicalIndicators(hist)


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