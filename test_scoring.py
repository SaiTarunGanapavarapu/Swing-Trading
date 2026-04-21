import yfinance as yf
from src.fetcher import fetchStockData

# Test a single stock
result = fetchStockData('TCS.NS')
print("Symbol:", result.get('symbol'))
print("Score:", result.get('score'))
print("Grade:", result.get('grade'))
print("\nTechnical Score:", result.get('technicalScore'))
print("\nATR:", result.get('atr'))
print("ADX:", result.get('adx'))
print("+DI:", result.get('plus_di'))
print("-DI:", result.get('minus_di'))
