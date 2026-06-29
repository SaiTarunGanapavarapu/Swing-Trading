#!/usr/bin/env python3
"""Main execution script for the modular swing screener."""

import argparse

from src.engine import SwingScreenerEngine
from src.models import RunOptions


def buildParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Indian Stock Swing Trading Screener")
    parser.add_argument("--symbols", nargs="+", help="Space-separated stock symbols (e.g., TCS.NS INFY.NS)")
    parser.add_argument("--csv", help="CSV file with a 'Symbol' column")
    parser.add_argument(
        "--universe",
        choices=["nifty50", "nifty200", "banknifty", "allstocksIndia", "dow", "nasdaq100", "sp500"],
        default="nifty50",
        help="Default universe when --symbols/--csv are not provided",
    )
    parser.add_argument("--export", default="Nifty50Candidates.xlsx", help="Output Excel filename")
    parser.add_argument("--top", type=int, default=100, help="Show top N results")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument("--cache-file", dest="cacheFile", default="yfinance_cache.xlsx", help="Excel cache file for fetched market data")
    parser.add_argument("--cache-hours", dest="cacheHours", type=float, default=24, help="Reuse cache entries newer than this many hours")
    parser.add_argument("--refresh-cache", dest="refreshCache", action="store_true", help="Ignore cache and refresh all symbols from yfinance")
    parser.add_argument("--no-cache", dest="noCache", action="store_true", help="Disable cache and always fetch from yfinance")
    parser.add_argument(
        "--cache",
        choices=["auto", "on", "off"],
        default="off",
        help="Cache mode: auto=fresh cache only, on=use cache whenever available, off=disable cache",
    )

    # Accumulation mode
    parser.add_argument(
        "--mode",
        choices=["screen", "accumulate"],
        default="screen",
        help="screen=rank only, accumulate=rank + position-adjusted allocation",
    )
    parser.add_argument("--budget", type=float, default=20000.0, help="Monthly budget for stock allocation (₹)")
    parser.add_argument("--portfolio", default="portfolio.json", help="Portfolio JSON file path")
    parser.add_argument("--decay-lambda", dest="decayLambda", type=float, default=1.5, help="Position penalty strength (higher=faster rotation)")
    parser.add_argument("--decay-floor", dest="decayFloor", type=float, default=0.3, help="Minimum penalty multiplier (0.0–1.0)")
    parser.add_argument("--max-position", dest="maxPositionFrac", type=float, default=0.40, help="Max fraction of budget in one stock")
    parser.add_argument("--min-position", dest="minPositionSize", type=float, default=2000.0, help="Min allocation per stock (₹)")
    parser.add_argument("--max-per-sector", dest="maxPerSector", type=int, default=2, help="Max stocks from one sector in buy list")
    parser.add_argument("--top-buy", dest="topBuy", type=int, default=5, help="Number of stocks in buy list")
    parser.add_argument("--min-buy-score", dest="minBuyScore", type=float, default=55.0, help="Minimum raw score to be buy-eligible")
    parser.add_argument("--confirm", dest="confirmBuy", action="store_true", help="Record purchases to portfolio file")

    return parser


def toRunOptions(args: argparse.Namespace) -> RunOptions:
    cacheMode = args.cache
    if args.noCache:
        cacheMode = "off"

    runOptions = RunOptions(
        symbols=args.symbols,
        csvPath=args.csv,
        universe=args.universe,
        exportFile=args.export,
        topN=args.top,
        quiet=args.quiet,
        cacheFile=args.cacheFile,
        cacheHours=args.cacheHours,
        refreshCache=args.refreshCache,
        noCache=args.noCache,
        cacheMode=cacheMode,
        mode=args.mode,
        budget=args.budget,
        portfolioFile=args.portfolio,
        decayLambda=args.decayLambda,
        decayFloor=args.decayFloor,
        maxPositionFrac=args.maxPositionFrac,
        minPositionSize=args.minPositionSize,
        maxPerSector=args.maxPerSector,
        topBuy=args.topBuy,
        minBuyScore=args.minBuyScore,
        confirmBuy=args.confirmBuy,
    )

    return runOptions


def main() -> int:
    parser = buildParser()
    args = parser.parse_args()

    try:
        options = toRunOptions(args)
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    engine = SwingScreenerEngine()
    engine.run(options)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())