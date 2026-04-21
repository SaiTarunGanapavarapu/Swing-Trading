#!/usr/bin/env python3
"""
Demo script showing ATR and ADX indicator usage.

This demonstrates:
1. Computing ATR/ADX for a single stock
2. Integrating with extended technicals
3. Using trend strength and direction signals
"""

import yfinance as yf
import pandas as pd

from src.atr_adx import computeATRAndADX, computeATR, computeADX
from src.momentum_indicators import (
    computeExtendedTechnicals,
    computeTrendStrength,
    computeDirectionSignal,
)


def demo_atr_adx_single_stock():
    """Demo: Compute ATR and ADX for a single stock."""
    print("=" * 70)
    print("DEMO 1: ATR & ADX for Single Stock (RELIANCE.NS)")
    print("=" * 70)
    
    # Fetch data
    ticker = "RELIANCE.NS"
    hist = yf.download(ticker, period="6mo", interval="1d", progress=False)
    hist = hist.dropna().copy()
    
    # Compute ATR/ADX
    result = computeATRAndADX(hist, period=14)
    
    print(f"\nTicker: {ticker}")
    print(f"Data points: {len(hist)}")
    print(f"\nATR: {result['atr']:.2f}" if result['atr'] else "ATR: N/A")
    print(f"ADX: {result['adx']:.2f}" if result['adx'] else "ADX: N/A")
    print(f"+DI: {result['plus_di']:.2f}" if result['plus_di'] else "+DI: N/A")
    print(f"-DI: {result['minus_di']:.2f}" if result['minus_di'] else "-DI: N/A")
    print(f"\nStrong Trend: {result['strong_trend']}")
    print(f"Buy Signal: {result['buy_signal']}")
    
    # Trend strength
    trend_strength = computeTrendStrength(result['adx'])
    direction = computeDirectionSignal(result['plus_di'], result['minus_di'])
    print(f"Trend Strength: {trend_strength}")
    print(f"Direction: {direction}")


def demo_extended_technicals():
    """Demo: Compute all technical indicators together."""
    print("\n" + "=" * 70)
    print("DEMO 2: Extended Technicals (All Indicators Together)")
    print("=" * 70)
    
    ticker = "TCS.NS"
    hist = yf.download(ticker, period="1y", interval="1d", progress=False)
    hist = hist.dropna().copy()
    
    # Compute extended technicals
    technicals = computeExtendedTechnicals(hist)
    
    print(f"\nTicker: {ticker}")
    print(f"\n--- Price Action ---")
    print(f"Above 50 SMA: {technicals['above_50sma']}")
    print(f"Above 200 SMA: {technicals['above_200sma']}")
    print(f"Golden Alignment: {technicals['golden_alignment']}")
    
    print(f"\n--- Momentum ---")
    print(f"RSI (14): {technicals['rsi_14']:.2f}" if technicals['rsi_14'] else "RSI: N/A")
    print(f"MACD Bullish: {technicals['macd_bullish']}")
    print(f"Volume Ratio: {technicals['volume_ratio']:.2f}" if technicals['volume_ratio'] else "N/A")
    print(f"% from 52W High: {technicals['pct_from_52w_high']:.2f}%" if technicals['pct_from_52w_high'] else "N/A")
    
    print(f"\n--- ATR/ADX ---")
    print(f"ATR: {technicals['atr']:.2f}" if technicals['atr'] else "ATR: N/A")
    print(f"ADX: {technicals['adx']:.2f}" if technicals['adx'] else "ADX: N/A")
    print(f"+DI: {technicals['plus_di']:.2f}" if technicals['plus_di'] else "+DI: N/A")
    print(f"-DI: {technicals['minus_di']:.2f}" if technicals['minus_di'] else "-DI: N/A")
    print(f"Strong Trend: {technicals['strong_trend']}")
    print(f"Buy Signal: {technicals['buy_signal']}")


def demo_multiple_stocks():
    """Demo: Scan multiple stocks for strong trends."""
    print("\n" + "=" * 70)
    print("DEMO 3: Scan Multiple Stocks for Strong Trends")
    print("=" * 70)
    
    symbols = ["TCS.NS", "INFY.NS", "RELIANCE.NS", "HDFC.NS", "BAJAJFINSV.NS"]
    
    results = []
    
    for symbol in symbols:
        try:
            hist = yf.download(symbol, period="1y", interval="1d", progress=False)
            hist = hist.dropna().copy()
            
            atr = computeATR(hist, period=14)
            adx = computeADX(hist, period=14)
            tech = computeExtendedTechnicals(hist)
            
            trend_strength = computeTrendStrength(adx)
            
            results.append({
                'Symbol': symbol,
                'ADX': f"{adx:.2f}" if adx else "N/A",
                'Trend': trend_strength,
                'Buy Signal': tech['buy_signal'],
                'Price > 50SMA': tech['above_50sma'],
                'Price > 200SMA': tech['above_200sma'],
            })
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
    
    df_results = pd.DataFrame(results)
    print("\n" + df_results.to_string(index=False))


if __name__ == "__main__":
    demo_atr_adx_single_stock()
    demo_extended_technicals()
    demo_multiple_stocks()
    
    print("\n" + "=" * 70)
    print("Demo completed!")
    print("=" * 70)
