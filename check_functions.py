from src.fetcher import *
import inspect

# List all available functions in the module
functions = [name for name, obj in locals().items() if callable(obj) and not name.startswith('_')]
print("Available functions in src.fetcher:")
for func in sorted(functions):
    print(f"  - {func}")
