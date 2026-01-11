"""
History module for Nibor Calculation Terminal.
Handles saving and loading NIBOR calculation snapshots.
"""
import json
import os
import getpass
import platform
from datetime import datetime, timedelta
from pathlib import Path

from config import NIBOR_LOG_PATH, get_logger

log = get_logger("history")

# History file path - uses OneDrive path from config
HISTORY_DIR = NIBOR_LOG_PATH
HISTORY_FILE = HISTORY_DIR / "nibor_log.json"


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

    if not HISTORY_FILE.exists():
        log.info("No history file found, starting fresh")
        return {}

    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            log.info(f"Loaded {len(data)} snapshots from history")
            return data
    except Exception as e:
        log.error(f"Failed to load history: {e}")
        return {}


def save_history(history: dict):
    """Save history to JSON file."""
    ensure_history_dir()

    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False, default=str)
        log.info(f"Saved {len(history)} snapshots to history")
    except Exception as e:
        log.error(f"Failed to save history: {e}")


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
