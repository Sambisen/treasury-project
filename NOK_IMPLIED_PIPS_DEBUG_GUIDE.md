# NOK Implied Page - PIPS Data Debugging Guide

## 🔴 Critical Bug Fix: Missing PIPS Data + Excel Loading Issues

**Date:** 2026-01-07  
**Status:** Debugging Tools Implemented  
**Files Modified:** `ui_pages.py`, `main.py`

---

## Problem Summary

The NOK Implied page shows:
- ✅ USD RATE and EUR RATE columns populated (3.65%, 1.93%, etc.)
- ✅ BBG DAYS and EXC DAYS columns populated (30, 58, 90, 181)
- ❌ **PIPS BBG column shows all "-"** (should show forward pips)
- ❌ **PIPS EXC column shows all "-"** (should show adjusted pips)
- ❌ **IMPLIED column shows all "-"** (can't calculate without pips)
- ❌ Excel file doesn't load consistently on app startup

---

## Root Cause Analysis

### Issue 1: PIPS Calculation Depends on Excel Data

In `ui_pages.py` (line ~715), the code calculates pips like this:

```python
# USDNOK: Forward from T-column, Spot from S-column (same row)
usd_fwd_excel = self._get_pips_from_excel(f"T{row_num}")
usd_spot_excel = self._get_pips_from_excel(f"S{row_num}")
pips_bbg_usd = (usd_fwd_excel - usd_spot_excel) * 10000 if usd_fwd_excel and usd_spot_excel else None
```

The `_get_pips_from_excel()` method reads from `self.app.cached_excel_data`, which is populated ONLY after Excel loads successfully.

**Problem:** If Excel loading fails or is slow, `cached_excel_data` is empty → pips become None → columns show "-"

### Issue 2: Excel Loading Race Condition

The Excel loading happens in `main.py._worker_refresh_excel_then_bbg()`:
1. Bloomberg loads (fast, works)
2. Excel loads (slow, sometimes fails silently)
3. UI updates immediately (before Excel finishes)

**Result:** PIPS columns are empty because Excel data isn't ready yet.

---

## Debugging Tools Implemented

### 1. Excel Loading Debug Output (main.py)

**Location:** `_worker_refresh_excel_then_bbg()` method

```python
print("\n[Main] ===== REFRESH DATA WORKER STARTED =====")
print("[Main] Loading Excel data...")
excel_ok, excel_msg = self.excel_engine.load_recon_direct()
print(f"[Main] Excel load result: success={excel_ok}, msg={excel_msg}")

if excel_ok:
    print(f"[Main] Excel engine recon_data has {len(self.excel_engine.recon_data)} entries")
else:
    print(f"[Main] ❌ Excel load FAILED: {excel_msg}")
```

**What to look for:**
- `success=True` → Excel loaded correctly
- Entry count should be > 100 (typically 200-300 cells)
- If `success=False`, the error message will tell you why

### 2. Cache Population Debug Output (main.py)

**Location:** `_apply_excel_result()` method

```python
print(f"\n[Main._apply_excel_result] Called with excel_ok={excel_ok}, msg={excel_msg}")

if excel_ok:
    self.cached_excel_data = dict(self.excel_engine.recon_data)
    print(f"[Main._apply_excel_result] ✓ Excel data cached: {len(self.cached_excel_data)} cells")
    
    # Print sample cells to verify data
    sample_cells = list(self.cached_excel_data.items())[:5]
    print(f"[Main._apply_excel_result] Sample cached cells: {sample_cells}")
```

**What to look for:**
- Cached cell count should match recon_data count
- Sample cells should show format: `[(7, 19): 11.5234, (7, 20): 11.5389, ...]`
- If count is 0, caching failed

### 3. NOK Implied Page Load Check (ui_pages.py)

**Location:** `NokImpliedPage.update()` method

```python
print(f"\n[NOK Implied Page] ========== UPDATE STARTED ==========")
print(f"[NOK Implied Page] cached_excel_data length: {len(self.app.cached_excel_data)}")
print(f"[NOK Implied Page] cached_market_data length: {len(self.app.cached_market_data or {})}")

# Check if Excel data is loaded
if not self.app.cached_excel_data or len(self.app.cached_excel_data) < 10:
    print(f"[NOK Implied Page] ❌ Excel data not loaded or insufficient!")
    print(f"[NOK Implied Page] Excel data needs at least 10 cells, currently has: {len(self.app.cached_excel_data)}")
    return
```

**What to look for:**
- If Excel data is < 10 cells, the page will skip update and show why
- Checks if there's a sync issue between engine and cached data

### 4. Cell Lookup Detailed Debugging (ui_pages.py)

**Location:** `_get_pips_from_excel()` method

```python
print(f"[_get_pips_from_excel] Looking for cell {cell_address}")
print(f"[_get_pips_from_excel] Excel data keys count: {len(excel_data)}")

coord_tuple = coordinate_to_tuple(cell_address)
print(f"[_get_pips_from_excel] Converted to tuple: {coord_tuple}")

val = excel_data.get(coord_tuple, None)

if val is None:
    print(f"[_get_pips_from_excel] ❌ Cell {cell_address} ({coord_tuple}) not found")
    sample_keys = list(excel_data.keys())[:10]
    print(f"[_get_pips_from_excel] Sample keys (first 10): {sample_keys}")
else:
    print(f"[_get_pips_from_excel] ✓ Found {cell_address} = {val}")
```

**What to look for:**
- Shows exactly which cells are being looked up
- Shows the tuple conversion (e.g., "T7" → (7, 20))
- If cell not found, shows sample keys to compare format
- Reveals if cell addresses are correct

---

## How to Use These Debugging Tools

### Step 1: Run the Application

```bash
python main.py
```

### Step 2: Watch Console Output During Startup

Look for the initialization sequence:

```
[Main] ===== REFRESH DATA WORKER STARTED =====
[Main] Loading Excel data...
[Main] Excel load result: success=True, msg=OK
[Main] Excel engine recon_data has 287 entries

[Main._apply_excel_result] Called with excel_ok=True, msg=OK
[Main._apply_excel_result] ✓ Excel data cached: 287 cells
[Main._apply_excel_result] Sample cached cells: [((7, 19), 11.5234), ((7, 20), 11.5389), ...]
```

### Step 3: Navigate to NOK Implied Page

When you click on "NOK Implied" in the navigation, watch for:

```
[NOK Implied Page] ========== UPDATE STARTED ==========
[NOK Implied Page] cached_excel_data length: 287
[NOK Implied Page] cached_market_data length: 45
[NOK Implied Page] ✓ Excel data loaded with 287 cells
```

### Step 4: Check Cell Lookups

For each tenor (1M, 2M, 3M, 6M), you'll see lookups for 4 cells:

```
[_get_pips_from_excel] Looking for cell T7
[_get_pips_from_excel] Excel data keys count: 287
[_get_pips_from_excel] Converted to tuple: (7, 20)
[_get_pips_from_excel] ✓ Found T7 = 11.5389
[_get_pips_from_excel] Parsed to: 11.5389

[_get_pips_from_excel] Looking for cell S7
[_get_pips_from_excel] Excel data keys count: 287
[_get_pips_from_excel] Converted to tuple: (7, 19)
[_get_pips_from_excel] ✓ Found S7 = 11.5234
[_get_pips_from_excel] Parsed to: 11.5234
```

---

## Expected Cell Mappings

The code expects these Excel cells for PIPS calculation:

### USDNOK (Column S = Spot, Column T = Forward)
- **1M**: S7, T7 (row 7)
- **2M**: S8, T8 (row 8)
- **3M**: S9, T9 (row 9)
- **6M**: S10, T10 (row 10)

### EURNOK (Column N = Spot, Column O = Forward)
- **1M**: N7, O7 (row 7)
- **2M**: N8, O8 (row 8)
- **3M**: N9, O9 (row 9)
- **6M**: N10, O10 (row 10)

### Tuple Conversion Reference
```
Column S = column 19
Column T = column 20
Column N = column 14
Column O = column 15

So:
"S7" → (7, 19)
"T7" → (7, 20)
"N7" → (7, 14)
"O7" → (7, 15)
```

---

## Common Issues and Solutions

### Issue 1: Excel Data Not Loading

**Symptom:**
```
[Main] Excel load result: success=False, msg=File not found
[Main._apply_excel_result] ❌ Excel failed, cached_excel_data cleared
```

**Solution:**
- Verify Excel file exists at the expected path
- Check file permissions (not locked by another process)
- Ensure file path in `config.py` is correct

### Issue 2: Excel Loads But Cache Is Empty

**Symptom:**
```
[Main] Excel engine recon_data has 287 entries
[Main._apply_excel_result] ✓ Excel data cached: 0 cells
```

**Solution:**
- This indicates a bug in the caching logic
- Check if `dict(self.excel_engine.recon_data)` is failing
- Verify `recon_data` is a dict-like object

### Issue 3: Cells Not Found Despite Cache Being Populated

**Symptom:**
```
[_get_pips_from_excel] Looking for cell T7
[_get_pips_from_excel] Converted to tuple: (7, 20)
[_get_pips_from_excel] ❌ Cell T7 ((7, 20)) not found
[_get_pips_from_excel] Sample keys (first 10): [('T7', 11.5389), ('S7', 11.5234), ...]
```

**Solution:**
- Notice the sample keys are strings ("T7") not tuples!
- This means `recon_data` is storing keys as strings, not tuples
- The `coordinate_to_tuple()` conversion is creating a mismatch
- **FIX:** Change `_get_pips_from_excel` to NOT convert to tuple, or ensure `recon_data` uses tuple keys

### Issue 4: Page Updates Before Excel Finishes Loading

**Symptom:**
```
[NOK Implied Page] ========== UPDATE STARTED ==========
[NOK Implied Page] cached_excel_data length: 0
[NOK Implied Page] ❌ Excel data not loaded or insufficient!
```

**Solution:**
- Excel loading is asynchronous and hasn't finished yet
- Wait a moment and manually refresh the page (click "Recalculate" button)
- Or add a retry mechanism that polls for Excel data

---

## Verification Checklist

After implementing fixes, verify these outputs:

- [ ] Console shows `Excel load result: success=True`
- [ ] Console shows `Excel data cached: XXX cells` (where XXX > 100)
- [ ] Console shows sample cached cells in correct format
- [ ] NOK Implied page shows `✓ Excel data loaded with XXX cells`
- [ ] Console shows `✓ Found T7 = X.XXXX` for all cells (T7-T10, S7-S10, O7-O10, N7-N7)
- [ ] PIPS BBG column displays numeric values (not "-")
- [ ] PIPS EXC column displays adjusted values  (not "-")
- [ ] IMPLIED column displays calculated yields (not "-")

---

## Next Steps

1. **Run the application** with the debugging enabled
2. **Capture console output** to a log file:
   ```bash
   python main.py 2>&1 | tee nok_implied_debug.log
   ```
3. **Navigate to NOK Implied page** and wait for it to load
4. **Review the log file** using the patterns described above
5. **Identify the exact failure point** (Excel load, cache, or cell lookup)
6. **Apply the appropriate fix** based on the diagnostic output

---

## Files Modified

1. **ui_pages.py**
   - Added extensive debugging to `_get_pips_from_excel()` method
   - Added Excel data validation check in `NokImpliedPage.update()` method
   - Shows cell lookup process and identifies missing cells

2. **main.py**
   - Added Excel load status logging in `_worker_refresh_excel_then_bbg()`
   - Added cache population verification in `_apply_excel_result()`
   - Shows sample cached cells to verify data format

---

## Contact

If you see unexpected output or errors not covered in this guide, capture the full console log and review it against the patterns described above. The debugging output is designed to pinpoint exactly where the data flow breaks down.

**Good luck debugging! 🚀**
