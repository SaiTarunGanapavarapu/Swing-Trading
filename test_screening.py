from src.screening_service import ScreeningService
from src.models import RunOptions

options = RunOptions(
    symbols=['TCS.NS', 'INFY.NS'],
    csvPath=None,
    universe='nifty50',
    exportFile='test.xlsx',
    topN=5,
    quiet=False,
    cacheFile='yfinance_cache.xlsx',
    cacheHours=24,
    refreshCache=False,
    noCache=False,
    cacheMode='off'
)

service = ScreeningService()
results = service.run(['TCS.NS', 'INFY.NS'], options)
print('✅ SCREENING PIPELINE RESULTS')
print('='*80)
print('Results shape:', results.shape)
print('\nSymbol | Price | RSI | ATR | ADX | +DI | -DI | Tech Score | Total Score | Grade')
print('-'*80)
for idx, row in results.iterrows():
    symbol = row['symbol']
    price = row['currentPrice']
    rsi = row['rsi14']
    atr = row['atr']
    adx = row['adx']
    plus_di = row['plusDi']
    minus_di = row['minusDi']
    tech_score = row['technicalScore']
    total_score = row['total_score']
    grade = row['grade']
    print(f"{symbol:10} | {price:>7.2f} | {rsi:>5.2f} | {atr:>6.2f} | {adx:>5.2f} | {plus_di:>5.2f} | {minus_di:>5.2f} | {tech_score:>10.2f} | {total_score:>11.2f} | {grade:>5}")

print('\nFull Technical Analysis for TCS.NS:')
print('  ATR (Average True Range):', results.iloc[0]['atr'])
print('  ADX (Average Directional Index):', results.iloc[0]['adx'])
print('  +DI (Plus Directional Indicator):', results.iloc[0]['plusDi'])
print('  -DI (Minus Directional Indicator):', results.iloc[0]['minusDi'])
print('  Strong Trend:', results.iloc[0]['strongTrend'])
print('  Technical Score:', results.iloc[0]['technicalScore'])
print('  Total Score:', results.iloc[0]['total_score'], '/', results.iloc[0]['score_out_of'])
print('  Grade:', results.iloc[0]['grade'])

print('\nFull Technical Analysis for INFY.NS:')
print('  ATR (Average True Range):', results.iloc[1]['atr'])
print('  ADX (Average Directional Index):', results.iloc[1]['adx'])
print('  +DI (Plus Directional Indicator):', results.iloc[1]['plusDi'])
print('  -DI (Minus Directional Indicator):', results.iloc[1]['minusDi'])
print('  Strong Trend:', results.iloc[1]['strongTrend'])
print('  Technical Score:', results.iloc[1]['technicalScore'])
print('  Total Score:', results.iloc[1]['total_score'], '/', results.iloc[1]['score_out_of'])
print('  Grade:', results.iloc[1]['grade'])
