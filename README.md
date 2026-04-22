# Swing Trading Screener

A modular, multi-factor quantitative screening framework for Indian equities. This repository combines fundamental quality filters (Buffett/Graham/Lynch style), technical trend checks, and risk flagging into a single rank-ordered candidate list for swing-trading research.

The project is designed for reproducible batch runs with cache-aware data ingestion, configurable universes, and export-ready output.

## Overview

This repository implements an end-to-end screening pipeline:

1. Data ingestion: fetches market and financial fields from yfinance.
2. Feature engineering: computes technical indicators (SMA, RSI, MACD, ATR, ADX, DI spread, volume surge, 52-week distance) and cash-flow proxies.
3. Multi-pillar scoring: evaluates each stock across profitability, balance-sheet strength, valuation, quality, and technical momentum.
4. Risk controls: applies explicit red-flag checks and score penalties for critical conditions.
5. Ranking and export: sorts by final score and exports a full table to Excel.

The architecture separates orchestration, data retrieval, scoring logic, and reporting to make the system easy to extend.

## Key Features

### Data + Universe Layer

- Supports three built-in universes:
  - `nifty50`
  - `nifty200`
  - `banknifty`
  - `allstocks` (broad India universe)
- Also supports custom stock lists via:
  - `--symbols` (space-separated symbols)
  - `--csv` (CSV file with any symbol-like column)
- Normal ticker suffix handling (`.NS` / `.BO`) in loader paths.

### Cache-Aware Execution

- Three cache policies through `--cache`:
  - `off`: always fetch live
  - `auto`: use only fresh cache entries (age-based)
  - `on`: always use cache if present, even if stale
- Additional cache controls:
  - `--cache-file`
  - `--cache-hours`
  - `--refresh-cache`
  - `--no-cache`
- Automatic fallback to stale cache when a live fetch fails for a symbol.

### Factor-Based Scoring

The screener computes a composite score out of 100 from five pillars:

- Profitability
- Balance sheet
- Valuation
- Quality
- Technicals

Each pillar is made of threshold-based rules with explicit max points and grading tiers (`excellent`, `good`, `fair`, etc.).

### Red-Flag Penalties

Critical flags reduce the final score:

- Each `🚨` flag applies a `-2.0` penalty.
- Non-critical warnings are reported in output but not penalized equally.

### Grading Buckets

Final grades are assigned from total score:

- `>= 70`: `🟢 Buy`
- `>= 55`: `🟠 Hold`
- `>= 40`: `🟡 Watchlist`
- `< 40`: `🔴 Avoid`

## Repository Structure

```text
src/
├── engine.py              # Main orchestration engine
├── data_loader.py         # Symbol resolution from args/CSV/default universes
├── universe.py            # Built-in universes and normalization helpers
├── fetcher.py             # yfinance extraction and raw feature assembly
├── indicators.py          # Technical + FCF + profitability history helpers
├── scoring_engine.py      # Composite score construction and grade mapping
├── scoring_common.py      # Shared scoring primitives (tiered scoring, rule result)
├── cache.py               # Read/write freshness-aware Excel cache
├── reporting.py           # Console table + Excel export helpers
├── storage.py             # Persistence wrapper around reporting export
├── models.py              # RunOptions dataclass
└── screens/
    ├── profitability.py   # P1-P8 profitability rule set
    ├── balance_sheet.py   # B1-B5 leverage/liquidity/cashflow rules
    ├── valuation.py       # V1-V7 valuation and yield rules
    ├── quality.py         # Q1-Q5 quality/ownership/size rules
    ├── technicals.py      # T1-T6 trend/momentum rules
    └── red_flags.py       # Critical and warning risk tags
main.py                    # CLI entry point
requirements.txt           # Runtime dependencies
```

## Scoring Model Details

## 1) Profitability Screen (P1-P8)

Evaluates margins, returns, growth, and cash-flow quality:

- `P1` Gross Margin
- `P2` Net Margin
- `P3` Operating Margin
- `P4` ROE
- `P5` ROCE (implemented using return on assets field in yfinance mapping)
- `P6` EPS Growth (with growth overheating cap: values above 30 reduce max contribution)
- `P7` Revenue Growth (3Y proxy)
- `P8` FCF Margin

## 2) Balance Sheet Screen (B1-B5)

Focuses on solvency and resilience:

- `B1` Debt/Equity (inverse scoring)
- `B2` Current Ratio
- `B3` Interest Coverage
- `B4` Net Debt/EBITDA proxy (inverse scoring)
- `B5` FCF Positive Years

## 3) Valuation Screen (V1-V7)

Blends absolute and relative valuation checks:

- `V1` P/E
- `V2` PEG
- `V3` P/B
- `V4` Price vs Graham Number (`grahamNumberRatio`)
- `V5` EV/EBITDA
- `V6` Earnings Yield (`100 / P/E`)
- `V7` Dividend Yield

## 4) Quality Screen (Q1-Q5)

Emphasizes consistency and ownership context:

- `Q1` Profitable Years
- `Q2` Dividend Years
- `Q3` Promoter Holding (neutral fallback score if unavailable)
- `Q4` Promoter Pledge (can be negative if critically high)
- `Q5` Market Cap thresholding

## 5) Technical Screen (T1-T8)

Momentum and trend confirmation:

- `T1` Above 200-day SMA
- `T2` Above 50-day SMA
- `T3` Golden Alignment (`EMA21 > SMA50 > SMA200`)
- `T4` RSI zone scoring
- `T5` Volume Surge (`volumeRatio`)
- `T6` Distance from 52-week high
- `T7` ADX trend-strength scoring
- `T8` Directional confirmation from `+DI` vs `-DI`

## 6) Red Flags

Current flag set:

- `🚨 CRITICAL_PLEDGE_RISK`
- `🚨 EXCESSIVE_DEBT`
- `🚨 LOSS_MAKING`
- `🚨 LIQUIDITY_CRISIS`
- `⚠️ MICRO_CAP`

Critical flags (`🚨`) reduce total score by penalty.

## Data Fields and Derived Metrics

Primary market/fundamental fields are pulled from yfinance `Ticker.info` + statement endpoints where available. The pipeline derives:

- `earningsYield = 100 / trailingPE` when `trailingPE > 0`
- `grahamNumber = sqrt(22.5 * trailingEps * bookValue)`
- `grahamNumberRatio = currentPrice / grahamNumber`
- `marketCapCr = marketCap / 1e7` (crores)
- RSI(14), SMA(50/200), EMA(12/21/26), MACD signal relation
- FCF margin and count of positive FCF years
- Estimated profitable years from `Net Income` history

## Quick Start

## Installation

```bash
pip install -r requirements.txt
```

## Basic Run

```bash
python main.py
```

This uses default universe (`nifty50`) and exports ranked results to Excel.

## Common CLI Examples

### 1) Run top 25 from Nifty50 and export

```bash
python main.py --universe nifty50 --top 25 --export nifty50Candidates.xlsx
```

### 2) Screen Bank Nifty with cache auto mode

```bash
python main.py --universe banknifty --cache auto --cache-hours 12 --export bankniftySwing.xlsx
```

### 3) Use explicit symbols

```bash
python main.py --symbols TCS.NS INFY.NS ICICIBANK.NS --top 10 --export customSymbols.xlsx
```

### 4) Use CSV symbol input

```bash
python main.py --csv symbols.csv --cache on --export csvRun.xlsx
```

### 5) Force refresh all cached entries

```bash
python main.py --universe nifty50 --cache on --refresh-cache --export refreshed.xlsx
```

## CLI Reference

- `--symbols`: Custom ticker list (space-separated)
- `--csv`: CSV input path with symbol-like column
- `--universe`: `nifty50 | banknifty | allstocks`
- `--export`: Output Excel file name
- `--top`: Number of rows shown in terminal
- `--quiet`: Reduce progress output
- `--cache-file`: Cache Excel path
- `--cache-hours`: Freshness threshold for `auto`
- `--refresh-cache`: Ignore cache and refetch
- `--no-cache`: Disable cache regardless of other flags
- `--cache`: `auto | on | off`

## Output Format

The console displays a ranked table with key columns such as:

- Symbol
- Score
- Grade
- MCapCr
- PE
- ROE
- D/E
- RSI
- Flags

A full result table is exported to Excel including component sub-scores:

- `profitabilityScore`
- `balanceSheetScore`
- `valuationScore`
- `qualityScore`
- `technicalScore`
- `totalScore`
- `grade`
- raw/derived feature columns

## Design Principles

- Modular: data, scoring, and reporting are decoupled.
- Transparent: rule thresholds and points are explicit in code.
- Extensible: new screens can be added under `src/screens` and included in `scoring_engine.py`.
- Practical: cache and fallback behavior is built for repeated market scans.

## Limitations and Notes

- Data quality is constrained by yfinance coverage and field availability.
- Some fields (for example promoter metrics) may be unavailable and are handled with neutral defaults.
- Current ROCE mapping uses an available proxy in fetched data.
- The tool is a screener, not a full execution or portfolio-management system.
- Scores are heuristic and intended for research workflow, not investment advice.

## Development Notes

Potential next upgrades:

- Add NSE/BSE direct fundamental enrichers for promoter/pledge accuracy.
- Expand technical suite (ATR, ADX, relative strength vs benchmark).
- Add sector-relative normalization and z-score based ranking.
- Add configurable rule weights from a YAML/JSON config.
- Add test coverage for each scoring module and edge-case data scenarios.

## Disclaimer

This project is for educational and research purposes only. It does not constitute financial advice or a recommendation to buy/sell securities. Always validate with independent analysis and risk controls before making live decisions.
