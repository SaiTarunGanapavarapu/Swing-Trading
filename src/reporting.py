import pandas as pd
from tabulate import tabulate


def printResults(df: pd.DataFrame):
    if df is None or df.empty:
        print("\n⚠️ No stocks returned data. Check symbols and network.")
        return

    displayCols = [
        "symbol",
        "totalScore",
        "grade",
        "marketCapCr",
        "peRatio",
        "roe",
        "debtToEquity",
        "rsi14",
        "flags",
    ]
    availableCols = [col for col in displayCols if col in df.columns]
    displayDf = df[availableCols].copy()
    displayDf = displayDf.rename(
        columns={
            "symbol": "Symbol",
            "totalScore": "Score",
            "grade": "Grade",
            "marketCapCr": "MCapCr",
            "peRatio": "PE",
            "roe": "ROE",
            "debtToEquity": "D/E",
            "rsi14": "RSI",
            "flags": "Flags",
        }
    )
    print()
    print(tabulate(displayDf, headers="keys", tablefmt="github", showindex=True))


def exportToExcel(df: pd.DataFrame, filename: str = "swingCandidates.xlsx"):
    if df is None or df.empty:
        print("\n⚠️ No data to export.")
        return
    df.to_excel(filename, index=False)
    print(f"\n📊 Exported to {filename}")
