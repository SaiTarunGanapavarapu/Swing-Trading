"""Extended momentum indicators combining ATR, ADX, RSI, MACD, and price action."""

import math

import pandas as pd

from .atr_adx import computeATRAndADX


def computeExtendedTechnicals(hist: pd.DataFrame) -> dict:
    """
    Compute comprehensive technical indicators including ATR, ADX, RSI, MACD, and price action.
    
    Returns a dictionary with all technical signals for scoring.
    """
    
    if hist.empty or len(hist) < 50:
        return {
            # Price action
            "above_200sma": None,
            "above_50sma": None,
            "golden_alignment": None,
            # Momentum
            "rsi_14": None,
            "volume_ratio": None,
            "pct_from_52w_high": None,
            "macd_bullish": None,
            # ATR/ADX
            "atr": None,
            "adx": None,
            "plus_di": None,
            "minus_di": None,
            "strong_trend": False,
            "buy_signal": False,
        }
    
    try:
        # Handle MultiIndex columns from yfinance (drop Ticker level, keep Price level)
        if isinstance(hist.columns, pd.MultiIndex):
            hist = hist.copy()
            hist.columns = hist.columns.droplevel(-1)
        
        close_series = hist["Close"]
        
        # ========== PRICE ACTION ==========
        # Extract scalars explicitly
        rolling_200 = close_series.rolling(200).mean()
        if len(close_series) >= 200:
            sma200_last = rolling_200.iloc[-1]
            if isinstance(sma200_last, pd.Series):
                sma200_last = sma200_last.iloc[0]
            sma200_val = float(sma200_last) if pd.notna(sma200_last) else float(close_series.mean())
        else:
            sma200_val = float(close_series.mean())
            
        rolling_50 = close_series.rolling(50).mean()
        sma50_last = rolling_50.iloc[-1]
        if isinstance(sma50_last, pd.Series):
            sma50_last = sma50_last.iloc[0]
        sma50_val = float(sma50_last) if pd.notna(sma50_last) else float(close_series.mean())
        
        ema21 = close_series.ewm(span=21).mean()
        ema21_last = ema21.iloc[-1]
        if isinstance(ema21_last, pd.Series):
            ema21_last = ema21_last.iloc[0]
        ema21_val = float(ema21_last) if pd.notna(ema21_last) else float(close_series.mean())
        
        price = float(close_series.iloc[-1])
        
        # ========== RSI ==========
        delta = close_series.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi_result = (100 - (100 / (1 + rs))).iloc[-1]
        if isinstance(rsi_result, pd.Series):
            rsi_result = rsi_result.iloc[0]
        rsi_val = float(rsi_result) if pd.notna(rsi_result) else 50.0
        
        # ========== VOLUME ==========
        volume_series = hist["Volume"]
        vol_avg_rolling = volume_series.rolling(20).mean()
        vol_avg_last = vol_avg_rolling.iloc[-1]
        if isinstance(vol_avg_last, pd.Series):
            vol_avg_last = vol_avg_last.iloc[0]
        vol_avg = float(vol_avg_last) if pd.notna(vol_avg_last) else 1.0
        vol_latest = float(volume_series.iloc[-1])
        vol_ratio = vol_latest / vol_avg if vol_avg > 0 else 1.0
        
        # ========== 52-WEEK ==========
        high_52w = float(hist["High"].max())
        pct_from_high = ((high_52w - price) / high_52w) * 100 if high_52w > 0 else 0.0
        
        # ========== MACD ==========
        ema12 = close_series.ewm(span=12).mean()
        ema26 = close_series.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        macd_val = float(macd.iloc[-1])
        signal_val = float(signal.iloc[-1])
        macd_bull = macd_val > signal_val
        
        # ========== ATR/ADX ==========
        atr_adx_result = computeATRAndADX(hist, period=14)
        
        # ========== BUILD RETURN DICT ==========
        return {
            # Price action
            "above_200sma": bool(price > sma200_val),
            "above_50sma": bool(price > sma50_val),
            "golden_alignment": bool(
                (len(close_series) >= 200) and (ema21_val > sma50_val) and (sma50_val > sma200_val)
            ),
            # Momentum
            "rsi_14": rsi_val if not pd.isna(rsi_val) else 50.0,
            "volume_ratio": vol_ratio,
            "pct_from_52w_high": pct_from_high,
            "macd_bullish": macd_bull,
            # ATR/ADX
            "atr": atr_adx_result.get("atr"),
            "adx": atr_adx_result.get("adx"),
            "plus_di": atr_adx_result.get("plus_di"),
            "minus_di": atr_adx_result.get("minus_di"),
            "strong_trend": atr_adx_result.get("strong_trend", False),
            "buy_signal": atr_adx_result.get("buy_signal", False),
        }
    
    except Exception as e:
        import traceback
        print(f"Error computing extended technicals: {e}")
        traceback.print_exc()
        return {
            "above_200sma": None,
            "above_50sma": None,
            "golden_alignment": None,
            "rsi_14": None,
            "volume_ratio": None,
            "pct_from_52w_high": None,
            "macd_bullish": None,
            "atr": None,
            "adx": None,
            "plus_di": None,
            "minus_di": None,
            "strong_trend": False,
            "buy_signal": False,
        }


def computeTrendStrength(adx: float) -> str:
    """
    Classify trend strength based on ADX value.
    
    Args:
        adx: ADX value
    
    Returns:
        Trend strength classification: "very_weak", "weak", "moderate", "strong", "very_strong"
    """
    if not adx or adx < 0:
        return "no_data"
    elif adx < 14:
        return "very_weak"
    elif adx < 20:
        return "weak"
    elif adx < 25:
        return "moderate"
    elif adx < 30:
        return "strong"
    else:
        return "very_strong"


def computeDirectionSignal(plus_di: float, minus_di: float) -> str:
    """
    Determine direction signal from +DI and -DI.
    
    Args:
        plus_di: +DI value
        minus_di: -DI value
    
    Returns:
        Direction signal: "bullish", "bearish", "neutral"
    """
    if not plus_di or not minus_di:
        return "neutral"
    
    diff = plus_di - minus_di
    
    if diff > 5:
        return "bullish"
    elif diff < -5:
        return "bearish"
    else:
        return "neutral"
