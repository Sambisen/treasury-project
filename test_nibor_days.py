"""
Test script to verify NIBOR Days data is loading correctly.
"""
import time
from engines import ExcelEngine

print("=" * 60)
print("NIBOR Days Data Loading Test")
print("=" * 60)

# Create engine instance
print("\n[1] Creating ExcelEngine instance...")
engine = ExcelEngine()

# Wait for background loading to complete
print("[2] Waiting for background loading (5 seconds)...")
time.sleep(5)

# Check loading status
print(f"\n[3] Loading status:")
print(f"    - Ready: {engine._day_data_ready}")
print(f"    - Error: {engine._day_data_err}")
print(f"    - Data shape: {engine.day_data.shape if not engine.day_data.empty else 'Empty'}")

if not engine.day_data.empty:
    print(f"\n[4] Data columns:")
    print(f"    {list(engine.day_data.columns)}")
    
    print(f"\n[5] First 5 rows:")
    print(engine.day_data.head().to_string())
    
    print(f"\n[6] Testing get_future_days_data(limit_rows=10):")
    future_data = engine.get_future_days_data(limit_rows=10)
    print(f"    - Returned shape: {future_data.shape}")
    if not future_data.empty:
        print(f"    - Columns: {list(future_data.columns)}")
        print(f"\n    First 5 rows of future data:")
        print(future_data.head().to_string())
    else:
        print("    - WARNING: Future data is empty!")
else:
    print("\n[ERROR] Day data is empty!")
    if engine._day_data_err:
        print(f"Error message: {engine._day_data_err}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
