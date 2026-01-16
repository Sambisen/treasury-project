"""
History module for Nibor Calculation Terminal.
Handles saving and loading NIBOR calculation snapshots.
Includes NIBOR fixing backfill functionality.
"""
import json
import os
import getpass
import platform
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from config import DEVELOPMENT_MODE, NIBOR_FIXING_TICKERS, get_logger

log = get_logger("history")

# ============================================================================
# OVERRIDE: Force history file location (PROD) to the user-specified path
# ============================================================================
NIBOR_LOG_FILE_OVERRIDE = Path(
    r"C:\Users\p901sbf\OneDrive - Swedbank\GroupTreasury-ShortTermFunding - Documents\Referensräntor\Nibor\Nibor logg\nibor_log.json"
)

# History directory derived from the override file
HISTORY_DIR = NIBOR_LOG_FILE_OVERRIDE.parent


def get_history_file_path() -> Path:
    r"""
    Get the history file path - ALWAYS the same file regardless of mode.

    Returns:
      ...\Nibor logg\nibor_log.json
    """
    # Always use the same file for both PROD and DEV mode
    return NIBOR_LOG_FILE_OVERRIDE


# For backwards compatibility
HISTORY_FILE = get_history_file_path()


def ensure_history_dir():
    """Ensure history directory exists."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def get_user_info():
    """Get current user and machine info."""
    try:
        user = getpass.getuser()
        machine = platform.node()
        return user, machine
    except Exception:
        return "unknown", "unknown"


def load_history() -> dict:
    """Load all history from JSON file."""
    ensure_history_dir()
    history_file = get_history_file_path()

    mode_str = "TEST" if DEVELOPMENT_MODE else "PROD"
    log.info(f"[{mode_str}] Loading history from: {history_file}")

    if not history_file.exists():
        log.info(f"[{mode_str}] No history file found, starting fresh")
        return {}

    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            log.info(f"[{mode_str}] Loaded {len(data)} snapshots from history")
            return data
    except Exception as e:
        log.error(f"[{mode_str}] Failed to load history: {e}")
        return {}


def save_history(history: dict):
    """Save history to JSON file."""
    ensure_history_dir()
    history_file = get_history_file_path()

    mode_str = "TEST" if DEVELOPMENT_MODE else "PROD"

    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False, default=str)
        log.info(f"[{mode_str}] Saved {len(history)} snapshots to: {history_file}")
    except Exception as e:
        log.error(f"[{mode_str}] Failed to save history: {e}")


def create_snapshot(app) -> dict:
    """Create a snapshot of current NIBOR calculation state."""
    user, machine = get_user_info()
    timestamp = datetime.now().isoformat()

    # Get funding calc data
    funding_data = getattr(app, 'funding_calc_data', {})

    # Build rates dict
    rates = {}
    for tenor in ['1m', '2m', '3m', '6m']:
        tenor_data = funding_data.get(tenor, {})
        rates[tenor] = {
            'funding': tenor_data.get('funding_rate'),
            'spread': tenor_data.get('spread'),
            'nibor': tenor_data.get('final_rate'),
            'eur_impl': tenor_data.get('eur_impl'),
            'usd_impl': tenor_data.get('usd_impl'),
            'nok_cm': tenor_data.get('nok_cm')
        }

    # Get weights
    weights = {}
    if hasattr(app, 'funding_calc_data') and '1m' in app.funding_calc_data:
        w = app.funding_calc_data['1m'].get('weights', {})
        weights = {'USD': w.get('USD'), 'EUR': w.get('EUR'), 'NOK': w.get('NOK')}

    # Get ALL market data from Bloomberg
    market_data = {}
    cached_market = getattr(app, 'cached_market_data', {}) or {}
    for ticker, data in cached_market.items():
        if isinstance(data, dict):
            market_data[ticker] = data.get('price')
        else:
            market_data[ticker] = data

    # Get Excel CM rates (EUR and USD per tenor)
    excel_cm_rates = {}
    if hasattr(app, 'excel_engine') and app.excel_engine:
        excel_cm_rates = getattr(app.excel_engine, 'excel_cm_rates', {}) or {}

    # Get alerts
    alerts = [a.get('msg', str(a)) for a in getattr(app, 'active_alerts', [])]

    # Get model
    model = getattr(app, 'selected_calc_model', 'unknown')

    snapshot = {
        'timestamp': timestamp,
        'user': user,
        'machine': machine,
        'model': model,
        'rates': rates,
        'weights': weights,
        'market_data': market_data,
        'excel_cm_rates': excel_cm_rates,
        'alerts': alerts
    }

    return snapshot


def save_snapshot(app) -> str:
    """Create and save a snapshot, return the timestamp key."""
    snapshot = create_snapshot(app)
    timestamp = snapshot['timestamp']

    # Load existing history
    history = load_history()

    # Add new snapshot (use date as key for easy lookup)
    date_key = timestamp[:10]  # YYYY-MM-DD

    # Store with full timestamp but indexed by date
    # If multiple snapshots same day, keep the latest
    history[date_key] = snapshot

    # Save
    save_history(history)

    log.info(f"Snapshot saved for {date_key}")
    return date_key


def get_snapshot(date_key: str) -> dict | None:
    """Get a specific snapshot by date key (YYYY-MM-DD)."""
    history = load_history()
    return history.get(date_key)


def get_previous_day_rates(date_key: str = None) -> dict | None:
    """Get NIBOR rates from previous business day."""
    history = load_history()

    if not history:
        return None

    # Get sorted dates
    dates = sorted(history.keys(), reverse=True)

    if date_key is None:
        # Get today's date
        date_key = datetime.now().strftime("%Y-%m-%d")

    # Find previous date
    try:
        if date_key in dates:
            idx = dates.index(date_key)
            if idx + 1 < len(dates):
                prev_date = dates[idx + 1]
                return history[prev_date].get('rates')
        else:
            # date_key not in history, find closest previous
            for d in dates:
                if d < date_key:
                    return history[d].get('rates')
    except Exception as e:
        log.error(f"Error getting previous day rates: {e}")

    return None


def get_rate_change(current_rates: dict, previous_rates: dict) -> dict:
    """Calculate change between current and previous rates."""
    changes = {}

    if not previous_rates:
        return changes

    for tenor in ['1m', '2m', '3m', '6m']:
        current = current_rates.get(tenor, {}).get('nibor')
        previous = previous_rates.get(tenor, {}).get('nibor')

        if current is not None and previous is not None:
            changes[tenor] = round(current - previous, 4)
        else:
            changes[tenor] = None

    return changes


def get_all_dates() -> list:
    """Get all snapshot dates, sorted newest first."""
    history = load_history()
    return sorted(history.keys(), reverse=True)


def get_rates_table_data(limit: int = 30) -> list:
    """Get data formatted for rates history table."""
    history = load_history()
    dates = sorted(history.keys(), reverse=True)[:limit]

    table_data = []
    prev_rates = None

    # Process in chronological order for change calculation
    for date_key in reversed(dates):
        snapshot = history[date_key]
        rates = snapshot.get('rates', {})

        row = {
            'date': date_key,
            'timestamp': snapshot.get('timestamp', ''),
            'user': snapshot.get('user', ''),
            'model': snapshot.get('model', ''),
            '1m': rates.get('1m', {}).get('nibor'),
            '2m': rates.get('2m', {}).get('nibor'),
            '3m': rates.get('3m', {}).get('nibor'),
            '6m': rates.get('6m', {}).get('nibor'),
            '1m_chg': None,
            '2m_chg': None,
            '3m_chg': None,
            '6m_chg': None
        }

        # Calculate changes
        if prev_rates:
            for tenor in ['1m', '2m', '3m', '6m']:
                current = rates.get(tenor, {}).get('nibor')
                previous = prev_rates.get(tenor, {}).get('nibor')
                if current is not None and previous is not None:
                    row[f'{tenor}_chg'] = round(current - previous, 4)

        prev_rates = rates
        table_data.append(row)

    # Reverse to get newest first
    return list(reversed(table_data))


# ============================================================================
# NIBOR FIXING BACKFILL FUNCTIONS
# ============================================================================

def load_fixings_from_excel(excel_path: Path = None, num_dates: int = 3) -> dict:
    """
    Load NIBOR fixings from the Excel file (fallback when Bloomberg is unavailable).
    """
    from config import DATA_DIR

    if excel_path is None:
        excel_path = DATA_DIR / "Nibor history - wide.xlsx"

    if not excel_path.exists():
        log.warning(f"NIBOR history Excel file not found: {excel_path}")
        return {}

    try:
        df = pd.read_excel(excel_path)
        log.info(f"Loaded NIBOR history Excel with {len(df)} rows")

        # Sort by date descending to get most recent first
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.dropna(subset=['Date'])
            df = df.sort_values('Date', ascending=False)
            log.info(f"Sorted by date. Most recent: {df.iloc[0]['Date'] if len(df) > 0 else 'N/A'}")

        # Column mapping: Excel columns -> JSON keys
        col_map = {
            '1 Week': '1w',
            '1 Month': '1m',
            '2 Months': '2m',
            '3 Months': '3m',
            '6 Months': '6m'
        }

        fixings = {}

        # Get the most recent num_dates rows
        for i in range(min(num_dates, len(df))):
            row = df.iloc[i]
            date_val = row['Date']

            # Convert date to string format YYYY-MM-DD
            if isinstance(date_val, pd.Timestamp):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                date_str = str(date_val)[:10]

            # Extract rates for all tenors
            rates = {}
            all_valid = True

            for excel_col, json_key in col_map.items():
                if excel_col in df.columns:
                    val = row[excel_col]
                    if pd.notna(val):
                        rates[json_key] = float(val)
                    else:
                        all_valid = False
                        log.warning(f"Missing {json_key} for {date_str}")
                else:
                    all_valid = False
                    log.warning(f"Column {excel_col} not found in Excel")

            if all_valid and len(rates) == 5:
                fixings[date_str] = rates
                log.info(f"Loaded fixing for {date_str}: {rates}")
            else:
                log.warning(f"Skipping {date_str}: incomplete data (got {len(rates)}/5 tenors)")

        return fixings

    except Exception as e:
        log.error(f"Failed to load fixings from Excel: {e}")
        return {}


def should_save_fixing(history: dict, date_key: str) -> bool:
    """
    Determine if fixing should be saved (idempotent check).
    """
    if date_key not in history:
        return True

    entry = history[date_key]

    if 'fixing_rates' not in entry:
        return True

    fixing_rates = entry['fixing_rates']
    required_tenors = ['1w', '1m', '2m', '3m', '6m']

    for tenor in required_tenors:
        if tenor not in fixing_rates or fixing_rates[tenor] is None:
            return True

    return False


def save_fixing_for_date(history: dict, date_key: str, fixing_rates: dict, force: bool = False) -> bool:
    """
    Save fixing rates for a specific date.

    Args:
        history: The history dict to update
        date_key: Date string (YYYY-MM-DD)
        fixing_rates: Dict with tenor rates
        force: If True, always overwrite existing data
    """
    mode_str = "TEST" if DEVELOPMENT_MODE else "PROD"

    # Check if we should save (skip if exists and not forcing)
    if not force and not should_save_fixing(history, date_key):
        log.info(f"[{mode_str}] SKIP: Fixing already exists for {date_key}")
        return False

    # Create entry if doesn't exist
    if date_key not in history:
        history[date_key] = {}

    # Add fixing data (merge with existing)
    history[date_key]['fixing_rates'] = fixing_rates
    history[date_key]['fixing_saved_at'] = datetime.now().isoformat()
    history[date_key]['fixing_source'] = 'BDH'

    action = "OVERWRITE" if force else "SAVED"
    log.info(f"[{mode_str}] {action}: Fixing for {date_key}: {fixing_rates}")
    return True


def backfill_fixings(engine=None, num_dates: int = 3) -> tuple[int, list[str]]:
    """
    Backfill NIBOR fixings for the last N dates.
    ALWAYS overwrites the most recent fixings to ensure fresh data.
    """
    mode_str = "TEST" if DEVELOPMENT_MODE else "PROD"
    log.info(f"[{mode_str}] Starting backfill for last {num_dates} fixing dates (FORCE OVERWRITE)...")

    # Load current history
    history = load_history()

    # Try to get fixings from Bloomberg BDH first
    fixings = {}

    if engine is not None:
        try:
            fixings = fetch_fixings_from_bloomberg(engine, num_dates)
            if fixings:
                log.info(f"[{mode_str}] Got {len(fixings)} fixings from Bloomberg BDH")
        except Exception as e:
            log.warning(f"Bloomberg BDH failed: {e}, falling back to Excel")

    # Fallback to Excel if Bloomberg didn't work
    if not fixings:
        log.info("Using Excel file as data source for fixings")
        fixings = load_fixings_from_excel(num_dates=num_dates)

    if not fixings:
        log.error("No fixing data available from any source")
        return 0, []

    # ALWAYS save/overwrite the most recent fixings (force=True)
    saved_count = 0
    saved_dates = []

    for date_key, rates in fixings.items():
        # Force overwrite to ensure we always have the latest data
        if save_fixing_for_date(history, date_key, rates, force=True):
            saved_count += 1
            saved_dates.append(date_key)

    # Always save since we're forcing overwrites
    if saved_count > 0:
        save_history(history)
        log.info(f"[{mode_str}] Backfill complete: {saved_count} dates updated ({saved_dates})")

    return saved_count, saved_dates


def fetch_fixings_from_bloomberg(engine, num_dates: int = 3) -> dict:
    """
    Fetch NIBOR fixings from Bloomberg using BDH (historical data).
    """
    mode_str = "TEST" if DEVELOPMENT_MODE else "PROD"
    log.info(f"[{mode_str}] Attempting to fetch NIBOR fixings from Bloomberg BDH...")

    if engine is None:
        log.warning(f"[{mode_str}] No Bloomberg engine provided")
        return {}

    if hasattr(engine, 'fetch_fixing_history'):
        log.info(f"[{mode_str}] Calling engine.fetch_fixing_history({num_dates})...")
        try:
            result = engine.fetch_fixing_history(num_dates)
            if result:
                log.info(f"[{mode_str}] Bloomberg BDH returned {len(result)} dates: {list(result.keys())}")
            else:
                log.warning(f"[{mode_str}] Bloomberg BDH returned empty result")
            return result
        except Exception as e:
            log.error(f"[{mode_str}] Bloomberg BDH error: {e}")
            import traceback
            traceback.print_exc()
            return {}
    else:
        log.warning(f"[{mode_str}] Engine does not have fetch_fixing_history method")
    return {}


def import_all_fixings_from_excel(excel_path: Path = None) -> tuple[int, int]:
    """
    Import ALL historical fixings from Excel file to JSON.
    """
    from config import DATA_DIR

    mode_str = "TEST" if DEVELOPMENT_MODE else "PROD"

    if excel_path is None:
        excel_path = DATA_DIR / "Nibor history - wide.xlsx"

    if not excel_path.exists():
        log.error(f"Excel file not found: {excel_path}")
        return 0, 0

    try:
        df = pd.read_excel(excel_path)
        log.info(f"[{mode_str}] Importing {len(df)} rows from {excel_path.name}")

        # Column mapping
        col_map = {
            '1 Week': '1w',
            '1 Month': '1m',
            '2 Months': '2m',
            '3 Months': '3m',
            '6 Months': '6m'
        }

        # Load current history
        history = load_history()
        saved_count = 0
        skipped_count = 0

        for i, row in df.iterrows():
            date_val = row['Date']

            # Convert date to string
            if isinstance(date_val, pd.Timestamp):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                date_str = str(date_val)[:10]

            # Extract rates
            rates = {}
            all_valid = True

            for excel_col, json_key in col_map.items():
                if excel_col in df.columns:
                    val = row[excel_col]
                    if pd.notna(val):
                        rates[json_key] = float(val)
                    else:
                        all_valid = False
                else:
                    all_valid = False

            if not all_valid or len(rates) != 5:
                continue

            # Save (idempotent)
            if save_fixing_for_date(history, date_str, rates):
                saved_count += 1
            else:
                skipped_count += 1

        # Save history if any changes
        if saved_count > 0:
            save_history(history)

        log.info(f"[{mode_str}] Import complete: {saved_count} saved, {skipped_count} skipped (already exist)")
        return len(df), saved_count

    except Exception as e:
        log.error(f"Failed to import fixings from Excel: {e}")
        return 0, 0


def get_fixing_history_for_charts(limit: int = 90) -> list[dict]:
    """
    Get fixing history formatted for charts.
    """
    history = load_history()

    chart_data = []

    for date_key, entry in history.items():
        if 'fixing_rates' not in entry:
            continue

        fixing = entry['fixing_rates']

        chart_data.append({
            'date': date_key,
            '1w': fixing.get('1w'),
            '1m': fixing.get('1m'),
            '2m': fixing.get('2m'),
            '3m': fixing.get('3m'),
            '6m': fixing.get('6m'),
        })

    chart_data.sort(key=lambda x: x['date'])

    if limit and len(chart_data) > limit:
        chart_data = chart_data[-limit:]

    return chart_data


def get_fixing_table_data(limit: int = 50) -> list[dict]:
    """
    Get fixing history formatted for table display.
    """
    history = load_history()

    entries = []

    for date_key, entry in history.items():
        if 'fixing_rates' not in entry:
            continue

        fixing = entry['fixing_rates']

        entries.append({
            'date': date_key,
            '1w': fixing.get('1w'),
            '1m': fixing.get('1m'),
            '2m': fixing.get('2m'),
            '3m': fixing.get('3m'),
            '6m': fixing.get('6m'),
            'source': entry.get('fixing_source', 'Unknown'),
            '1w_chg': None,
            '1m_chg': None,
            '2m_chg': None,
            '3m_chg': None,
            '6m_chg': None,
        })

    entries.sort(key=lambda x: x['date'])

    for i in range(1, len(entries)):
        prev = entries[i - 1]
        curr = entries[i]

        for tenor in ['1w', '1m', '2m', '3m', '6m']:
            if curr[tenor] is not None and prev[tenor] is not None:
                curr[f'{tenor}_chg'] = round(curr[tenor] - prev[tenor], 4)

    entries.reverse()

    if limit and len(entries) > limit:
        entries = entries[:limit]

    return entries


def confirm_rates(app) -> tuple[bool, str]:
    """
    Confirm rates: backfill fixings, save contribution snapshot, and write to Excel.
    """
    mode_str = "TEST" if DEVELOPMENT_MODE else "PROD"
    today = datetime.now().strftime("%Y-%m-%d")

    log.info(f"[{mode_str}] Confirm rates started for {today}")

    try:
        engine = getattr(app, 'engine', None)
        saved_count, saved_dates = backfill_fixings(engine, num_dates=5)

        date_key = save_snapshot(app)

        if saved_count > 0:
            msg = f"Rates confirmed and saved for {date_key}. Backfilled {saved_count} fixing dates."
        else:
            msg = f"Rates confirmed and saved for {date_key}. Fixings already up to date."

        log.info(f"[{mode_str}] {msg}")
        return True, msg

    except Exception as e:
        error_msg = f"Failed to confirm rates: {e}"
        log.error(f"[{mode_str}] {error_msg}")
        return False, error_msg
