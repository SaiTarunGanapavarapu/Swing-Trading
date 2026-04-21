from src.fetcher import fetchStockData, computeTechnicals
import inspect

# Check signatures
print("fetchStockData signature:")
print(inspect.signature(fetchStockData))
print("\ncomputeTechnicals signature:")
print(inspect.signature(computeTechnicals))
