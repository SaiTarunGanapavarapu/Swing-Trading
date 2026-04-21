"""ATR (Average True Range) and ADX (Average Directional Index) indicator calculations."""

import numpy as np
import pandas as pd


def computeATRAndADX(hist: pd.DataFrame, period: int = 14) -> dict:
    """
    Compute ATR (Average True Range) and ADX (Average Directional Index).
    
    Args:
        hist: DataFrame with OHLC data (Open, High, Low, Close)
        period: Lookback period (default 14)
    
    Returns:
        Dictionary with ATR, ADX, +DI, -DI values
    """
    
    if hist.empty or len(hist) < period + 1:
        return {
            "atr": None,
            "adx": None,
            "plus_di": None,
            "minus_di": None,
            "strong_trend": False,
            "buy_signal": False,
        }
    
    try:
        df = hist.copy()
        
        # Handle MultiIndex columns from yfinance (drop Ticker level, keep Price level)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(-1)
        
        # ========== TRUE RANGE ==========
        prev_close = df['Close'].shift(1)
        
        tr1 = df['High'] - df['Low']
        tr2 = (df['High'] - prev_close).abs()
        tr3 = (df['Low'] - prev_close).abs()
        
        df['TR'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # ========== ATR (Wilder Smoothing) ==========
        df['ATR'] = df['TR'].rolling(window=period).mean()
        
        # Apply Wilder's smoothing to ATR
        for i in range(period, len(df)):
            df.loc[df.index[i], 'ATR'] = (
                (df.loc[df.index[i-1], 'ATR'] * (period - 1) + df.loc[df.index[i], 'TR']) / period
            )
        
        # ========== DIRECTIONAL MOVEMENTS ==========
        df['up_move'] = df['High'] - df['High'].shift(1)
        df['down_move'] = df['Low'].shift(1) - df['Low']
        
        df['+DM'] = np.where(
            (df['up_move'] > df['down_move']) & (df['up_move'] > 0),
            df['up_move'],
            0
        )
        
        df['-DM'] = np.where(
            (df['down_move'] > df['up_move']) & (df['down_move'] > 0),
            df['down_move'],
            0
        )
        
        # ========== SMOOTH DIRECTIONAL MOVEMENTS ==========
        df['+DM_smooth'] = df['+DM'].rolling(window=period).mean()
        df['-DM_smooth'] = df['-DM'].rolling(window=period).mean()
        
        # Apply Wilder's smoothing to directional movements
        for i in range(period, len(df)):
            df.loc[df.index[i], '+DM_smooth'] = (
                (df.loc[df.index[i-1], '+DM_smooth'] * (period - 1) + df.loc[df.index[i], '+DM']) / period
            )
            df.loc[df.index[i], '-DM_smooth'] = (
                (df.loc[df.index[i-1], '-DM_smooth'] * (period - 1) + df.loc[df.index[i], '-DM']) / period
            )
        
        # ========== DIRECTIONAL INDICATORS ==========
        df['+DI'] = (df['+DM_smooth'] / df['ATR']) * 100
        df['-DI'] = (df['-DM_smooth'] / df['ATR']) * 100
        
        # ========== DX AND ADX ==========
        df['DX'] = (abs(df['+DI'] - df['-DI']) / (df['+DI'] + df['-DI'])) * 100
        
        df['ADX'] = df['DX'].rolling(window=period).mean()
        
        # Apply Wilder's smoothing to ADX
        for i in range(period, len(df)):
            df.loc[df.index[i], 'ADX'] = (
                (df.loc[df.index[i-1], 'ADX'] * (period - 1) + df.loc[df.index[i], 'DX']) / period
            )
        
        # ========== EXTRACT LATEST VALUES ==========
        atr = df['ATR'].iloc[-1]
        adx = df['ADX'].iloc[-1]
        plus_di = df['+DI'].iloc[-1]
        minus_di = df['-DI'].iloc[-1]
        
        # Handle NaN values
        atr = atr if pd.notna(atr) else None
        adx = adx if pd.notna(adx) else None
        plus_di = plus_di if pd.notna(plus_di) else None
        minus_di = minus_di if pd.notna(minus_di) else None
        
        # ========== SIGNALS ==========
        strong_trend = (adx > 25) if adx else False
        buy_signal = (plus_di > minus_di) and (adx > 25) if (adx and plus_di and minus_di) else False
        
        return {
            "atr": atr,
            "adx": adx,
            "plus_di": plus_di,
            "minus_di": minus_di,
            "strong_trend": strong_trend,
            "buy_signal": buy_signal,
        }
        
    except Exception as e:
        print(f"Error computing ATR/ADX: {e}")
        return {
            "atr": None,
            "adx": None,
            "plus_di": None,
            "minus_di": None,
            "strong_trend": False,
            "buy_signal": False,
        }


def computeATR(hist: pd.DataFrame, period: int = 14) -> float:
    """
    Compute ATR only.
    
    Args:
        hist: DataFrame with OHLC data
        period: Lookback period (default 14)
    
    Returns:
        ATR value (float)
    """
    result = computeATRAndADX(hist, period)
    return result.get("atr", None)


def computeADX(hist: pd.DataFrame, period: int = 14) -> float:
    """
    Compute ADX only.
    
    Args:
        hist: DataFrame with OHLC data
        period: Lookback period (default 14)
    
    Returns:
        ADX value (float)
    """
    result = computeATRAndADX(hist, period)
    return result.get("adx", None)
