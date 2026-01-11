"""
Settings management for Nibor Calculation Terminal.
Handles loading, saving, and accessing user preferences.
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

from config import NIBOR_LOG_PATH, get_logger

log = get_logger("settings")

# Default settings
DEFAULT_SETTINGS = {
    # Appearance
    "theme": "dark",  # dark, light
    "accent_color": "red",  # red, blue, green, orange
    "font_size": "normal",  # compact, normal, large
    "animations": True,

    # Data & Refresh
    "auto_refresh": False,
    "refresh_interval": 60,  # seconds
    "show_countdown": True,
    "stale_warning_minutes": 5,

    # Alerts & Notifications
    "rate_alerts_enabled": False,
    "rate_alert_threshold_bps": 5,  # basis points
    "sound_enabled": True,
    "toast_enabled": True,
    "tray_alerts_enabled": True,

    # Display
    "decimal_places": 4,  # 2, 4, 6
    "show_chg_column": True,
    "start_page": "dashboard",
    "compact_mode": False,

    # Connections
    "bloomberg_auto_connect": True,
    "bloomberg_timeout": 10,  # seconds
    "excel_path": "",
    "show_connection_status": True,

    # History & Logging
    "auto_save_snapshots": True,
    "history_retention_days": 90,
    "audit_log_level": "all",  # all, info, warning, error
    "max_log_entries": 5000,

    # System
    "minimize_to_tray": True,
    "start_with_windows": False,
    "confirm_on_close": True,
    "language": "sv",  # sv, en

    # Window state (auto-saved)
    "window_width": 1400,
    "window_height": 900,
    "window_x": None,
    "window_y": None,
    "window_maximized": False,
}

# Settings file path
SETTINGS_DIR = NIBOR_LOG_PATH
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


class Settings:
    """
    Singleton settings manager.

    Usage:
        settings = Settings()
        settings.get("theme")  # -> "dark"
        settings.set("theme", "light")
        settings.save()
    """

    _instance = None
    _settings: Dict[str, Any] = {}
    _callbacks: Dict[str, list] = {}  # For change notifications

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        """Load settings from file."""
        self._settings = DEFAULT_SETTINGS.copy()

        try:
            SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    # Merge with defaults (in case new settings were added)
                    self._settings.update(saved)
                log.info(f"Settings loaded from {SETTINGS_FILE}")
            else:
                log.info("No settings file found, using defaults")
                self.save()  # Create default settings file
        except Exception as e:
            log.error(f"Failed to load settings: {e}")

    def save(self):
        """Save settings to file."""
        try:
            SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            log.info("Settings saved")
        except Exception as e:
            log.error(f"Failed to save settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any, save: bool = False):
        """Set a setting value."""
        old_value = self._settings.get(key)
        self._settings[key] = value

        # Notify callbacks
        if key in self._callbacks and old_value != value:
            for callback in self._callbacks[key]:
                try:
                    callback(key, value, old_value)
                except Exception as e:
                    log.error(f"Settings callback error: {e}")

        if save:
            self.save()

    def get_all(self) -> Dict[str, Any]:
        """Get all settings."""
        return self._settings.copy()

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self._settings = DEFAULT_SETTINGS.copy()
        self.save()
        log.info("Settings reset to defaults")

    def on_change(self, key: str, callback):
        """Register a callback for when a setting changes."""
        if key not in self._callbacks:
            self._callbacks[key] = []
        self._callbacks[key].append(callback)

    def export_settings(self, filepath: Path) -> bool:
        """Export settings to a file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                export_data = {
                    "exported_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "settings": self._settings
                }
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            log.error(f"Failed to export settings: {e}")
            return False

    def import_settings(self, filepath: Path) -> bool:
        """Import settings from a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "settings" in data:
                    self._settings.update(data["settings"])
                else:
                    self._settings.update(data)
            self.save()
            return True
        except Exception as e:
            log.error(f"Failed to import settings: {e}")
            return False


# Convenience functions
_settings_instance = None

def get_settings() -> Settings:
    """Get the settings singleton instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def get_setting(key: str, default: Any = None) -> Any:
    """Get a setting value (convenience function)."""
    return get_settings().get(key, default)


def set_setting(key: str, value: Any, save: bool = False):
    """Set a setting value (convenience function)."""
    get_settings().set(key, value, save)


# Font size presets
FONT_SIZE_PRESETS = {
    "compact": {
        "h1": 16,
        "h2": 13,
        "h3": 11,
        "body": 9,
        "small": 8,
    },
    "normal": {
        "h1": 20,
        "h2": 15,
        "h3": 13,
        "body": 11,
        "small": 9,
    },
    "large": {
        "h1": 24,
        "h2": 18,
        "h3": 15,
        "body": 13,
        "small": 11,
    },
}

# Theme presets
THEME_PRESETS = {
    "dark": {
        "bg_main": "#0f0f17",
        "bg_panel": "#16161e",
        "bg_card": "#1e1e2e",
        "bg_card_2": "#252536",
        "text": "#e0e0e0",
        "muted": "#888888",
        "border": "#2d2d44",
    },
    "light": {
        "bg_main": "#f5f5f5",
        "bg_panel": "#ffffff",
        "bg_card": "#ffffff",
        "bg_card_2": "#f0f0f0",
        "text": "#1a1a1a",
        "muted": "#666666",
        "border": "#d0d0d0",
    },
}

# Accent color presets
ACCENT_COLORS = {
    "red": "#e94560",
    "blue": "#3b82f6",
    "green": "#4ade80",
    "orange": "#f59e0b",
    "purple": "#8b5cf6",
    "cyan": "#06b6d4",
}
