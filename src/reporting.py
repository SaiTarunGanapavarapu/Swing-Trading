import pandas as pd
from datetime import datetime


def printResults(df: pd.DataFrame):
    if df is None or df.empty:
        return

    print("\n" + "=" * 100)
    print(f"  SWING TRADE CANDIDATES — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 100)

    displayCols = [
        "symbol",
        "total_score",
        "score_out_of",
        "data_coverage_pct",
        "grade",
        "intrinsicScore",
        "dataConfidence",
        "finalScore",
        "profitability",
        "balance_sheet",
        "valuation",
        "quality",
        "technicals",
        "market_cap_cr",
        "pe",
        "roe",
        "de",
        "rsi",
        "red_flags",
    ]
    availableCols = [col for col in displayCols if col in df.columns]
    displayDf = df[availableCols].copy()
    displayDf = displayDf.rename(
        columns={
            "symbol": "Symbol",
            "total_score": "Score",
            "score_out_of": "OutOf",
            "data_coverage_pct": "Coverage%",
            "grade": "Grade",
            "intrinsicScore": "Intrinsic",
            "dataConfidence": "Confidence%",
            "finalScore": "Final",
            "profitability": "Prof/30",
            "balance_sheet": "BS/20",
            "valuation": "Val/25",
            "quality": "Qual/15",
            "technicals": "Tech/10",
            "market_cap_cr": "MCapCr",
            "pe": "PE",
            "roe": "ROE",
            "de": "D/E",
            "rsi": "RSI",
            "red_flags": "Flags",
        }
    )
    print(displayDf.to_string())

    print("\n" + "-" * 60)
    strong = len(df[df["total_score"] >= 80])
    buy = len(df[(df["total_score"] >= 70) & (df["total_score"] < 80)])
    watch = len(df[(df["total_score"] >= 60) & (df["total_score"] < 70)])
    print(f"  🟢 Strong Buy: {strong}  |  🟢 Buy: {buy}  |  🟡 Watchlist: {watch}")
    print(f"  Total screened: {len(df)}  |  Avg score: {df['total_score'].mean():.1f}")
    print("-" * 60)


def exportToExcel(df: pd.DataFrame, filename: str = "swingCandidates.xlsx"):
    if df is None or df.empty:
        print("\n⚠️ No data to export.")
        return
    try:
        from openpyxl.styles import PatternFill

        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            exportDf = df.drop(columns=["details"], errors="ignore")
            exportDf.to_excel(writer, sheet_name="Rankings", index=True)

            worksheet = writer.sheets["Rankings"]
            scoreColumn = None
            for colIndex, columnName in enumerate(exportDf.columns, start=2):
                if columnName == "total_score":
                    scoreColumn = colIndex
                    break

            if scoreColumn:
                for rowIndex in range(2, len(exportDf) + 2):
                    cell = worksheet.cell(row=rowIndex, column=scoreColumn)
                    try:
                        value = float(cell.value)
                        if value >= 80:
                            cell.fill = PatternFill("solid", fgColor="00C853")
                        elif value >= 70:
                            cell.fill = PatternFill("solid", fgColor="64DD17")
                        elif value >= 60:
                            cell.fill = PatternFill("solid", fgColor="FFD600")
                        elif value >= 50:
                            cell.fill = PatternFill("solid", fgColor="FF9100")
                        else:
                            cell.fill = PatternFill("solid", fgColor="FF1744")
                    except Exception:
                        pass

            for column in worksheet.columns:
                maxLen = max(len(str(cell.value or "")) for cell in column)
                worksheet.column_dimensions[column[0].column_letter].width = min(maxLen + 2, 30)

        print(f"\n📊 Exported to {filename}")
    except ImportError:
        csvName = filename.replace(".xlsx", ".csv")
        df.to_csv(csvName)
        print(f"\n📊 Exported to {csvName} (install openpyxl for Excel format)")
