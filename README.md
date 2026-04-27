# Swing Trading Screener

A compact multi-factor stock screener for Indian equities. It ranks symbols using fundamentals, technical trend checks, and basic risk flags, then exports the results to Excel.

It also uses selective z-score normalization and rule cleanup to reduce duplicate credit for the same underlying factor, so the ranking stays tighter and less noisy.

## What It Does

- Screens built-in universes: `nifty50`, `nifty200`, `banknifty`, `allstocks`
- Accepts custom symbols or a CSV input
- Pulls market and financial data from yfinance
- Auto-detects financial stocks (banks, NBFCs, insurance, financial services)
- Scores stocks across five sections:
  - Profitability
  - Balance sheet
  - Valuation
  - Quality
  - Technicals
- Uses dedicated financial scoring rules when `isFinancial` is true
- Uses a 6-month momentum factor excluding the most recent month inside the technicals section
- Applies red-flag penalties for critical risk conditions
- Sorts results by total score and exports them for review

## Scoring At A Glance

The total score follows a 100-point layout across the five sections.

- Profitability: 30
- Balance sheet: 20
- Valuation: 25
- Quality: 15
- Technicals: 10

The engine uses a mix of absolute thresholds and relative ranking where it helps. The point is to avoid rewarding the same idea twice and to reduce multicollinearity across overlapping rules.

For financial names, the engine switches to an explicit financial model:

- Financial profitability uses ROE, Net Margin, EPS Growth, and Revenue Growth.
- Financial balance sheet uses `financialLeverage = Total Assets / Equity` (with D/E fallback).
- Financial valuation emphasizes P/B, then P/E, PEG, and dividend yield.
- Generic non-financial metrics like Current Ratio, Interest Coverage, and Net Debt/EBITDA are not used in the financial branch.

## Advanced Scoring Choices

The screener includes a few design choices to keep rankings cleaner and less biased:

- Selective z-score normalization:
  - Used on metrics where sector context matters (for example valuation multiples and growth rates).
  - Helps compare stocks relative to peers instead of using one global cutoff for every sector.
- Redundancy reduction (multicollinearity control):
  - Removed direct duplicates like Earnings Yield vs P/E (same signal in inverse form).
  - Kept EV/EBITDA as the primary cheapness score and shifted P/E to a guardrail role.
  - Collapsed margin stacking by focusing on Operating Margin as the core efficiency margin.
  - Dropped ROE scoring in favor of ROCE to reduce leverage-driven distortion.
- Technical stacking control:
  - Replaced additive trend rules with a mutually exclusive trend alignment ladder so one strong trend does not get triple-counted.
  - Added a separate 6M momentum (ex-1M) rule so trend direction and trend magnitude are scored independently.
- Leverage treatment cleanup:
  - Debt/Equity moved to guardrail behavior.
  - Net Debt/EBITDA kept as the primary solvency scoring metric.
  - For financial stocks, balance-sheet leverage is evaluated with `financialLeverage` first.

These changes keep the score on the same 100-point layout while reducing inflated scores from overlapping factors.

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the default screen:

```bash
python main.py
```

This runs the default universe and exports the ranked list to Excel.

## Common Commands

Screen Nifty 50 and export the top 25:

```bash
python main.py --universe nifty50 --top 25 --export nifty50Candidates.xlsx
```

Screen Bank Nifty with cached data when available:

```bash
python main.py --universe banknifty --cache auto --cache-hours 12 --export bankniftySwing.xlsx
```

Use explicit symbols:

```bash
python main.py --symbols TCS.NS INFY.NS ICICIBANK.NS --top 10 --export customSymbols.xlsx
```

Use a CSV file of symbols:

```bash
python main.py --csv symbols.csv --cache on --export csvRun.xlsx
```

Force a full refresh:

```bash
python main.py --universe nifty50 --cache on --refresh-cache --export refreshed.xlsx
```

## CLI Options

- `--symbols`: Space-separated ticker list
- `--csv`: CSV input path with a symbol column
- `--universe`: `nifty50 | nifty200 | banknifty | allstocks`
- `--export`: Excel output file name
- `--top`: Number of rows shown in the terminal
- `--quiet`: Reduce terminal output
- `--cache-file`: Cache Excel path
- `--cache-hours`: Freshness window for `auto`
- `--refresh-cache`: Ignore cache and refetch
- `--no-cache`: Disable cache entirely
- `--cache`: `auto | on | off`

## Output

The terminal shows the ranked shortlist with the main fields:

- Symbol
- Score
- Grade
- Market cap
- P/E
- ROE
- 6M momentum
- D/E
- IsFinancial
- RSI
- Flags

The Excel export includes the full score breakdown and the raw/derived metrics used by the screener.
Each run also creates a timestamped JSON file containing the same ranked rows and all per-stock fields/sub-scores.

## Notes

- Scores are heuristic, not investment advice.
- Data quality depends on yfinance coverage.
- Some metrics may be missing for certain symbols and are handled with fallback behavior.
- Z-scores are used internally where they improve relative comparison and help keep overlapping signals from overstating the same factor.

## Project Layout

```text
README.md
requirements.txt
main.py
main.ipynb

src/
  cache.py
  config.py
  dataLoader.py
  engine.py
  fetcher.py
  indicators.py
  models.py
  reporting.py
  scoringCommon.py
  scoringEngine.py
  screeningService.py
  stockClassifier.py
  storage.py
  universe.py

  screens/
    financialOverrides.py
    profitability.py
    balanceSheet.py
    valuation.py
    quality.py
    technicals.py
    redFlags.py
```

## Disclaimer

For research and educational use only. Always verify results independently before making trading decisions.
