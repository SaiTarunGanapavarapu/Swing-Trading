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
        choices=["nifty50", "nifty200", "banknifty", "allstocks"],
        default="nifty200",
        help="Default universe when --symbols/--csv are not provided",
    )
    parser.add_argument("--export", default="Nifty200Candidates.xlsx", help="Output Excel filename")
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
