"""
Snapshot Engine for daily JSON exports.
Handles serialization of Bloomberg and Excel data.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from config import BASE_HISTORY_PATH


class SnapshotEngine:
    """Manages daily JSON snapshots for Nibor rates and Swedbank contributions."""

    def __init__(self):
        self.base_path = BASE_HISTORY_PATH

    def save_daily_snapshot(
        self,
        date_str: str,
        bloomberg_data: Dict[str, Any],
        swedbank_contribution: Dict[str, Any],
        excel_metadata: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Save daily snapshot to JSON file.

        Args:
            date_str: Date in YYYY-MM-DD format
            bloomberg_data: Dict with NIBOR tickers and their data
            swedbank_contribution: Dict with tenor -> {Z7, AA7, ...}
            excel_metadata: Workbook name, sheet name, timestamp

        Returns:
            (success: bool, message: str)
        """
        try:
            # Parse date to get year
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            year = dt.year

            # Create directory structure: data/Nibor/Historik/{year}/daily/
            daily_dir = self.base_path / str(year) / "daily"
            daily_dir.mkdir(parents=True, exist_ok=True)

            # File path: YYYY-MM-DD.json
            file_path = daily_dir / f"{date_str}.json"

            # Build snapshot data
            snapshot = {
                "metadata": {
                    "date": date_str,
                    "timestamp": datetime.now().isoformat(),
                    "source": "bloomberg_api",
                    "app_version": "3.8.1-tk"
                },
                "bloomberg": self._categorize_bloomberg_data(bloomberg_data),
                "swedbank_contribution": swedbank_contribution,
                "excel_metadata": excel_metadata
            }

            # Write JSON (pretty-printed for human readability)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)

            return True, f"Snapshot saved: {file_path}"

        except Exception as e:
            return False, f"Snapshot save failed: {str(e)}"

    def _categorize_bloomberg_data(self, raw_data: Dict) -> Dict:
        """Categorize Bloomberg tickers into nibor_rates, spot_rates, etc."""
        categorized = {
            "nibor_rates": {},
            "spot_rates": {},
            "forwards": {},
            "cm_curves": {}
        }

        for ticker, data in raw_data.items():
            if "NKCM" in ticker and "SWET" in ticker:
                categorized["nibor_rates"][ticker] = data
            elif "F033" in ticker and ("NOK" in ticker or "NKEU" in ticker):
                if any(x in ticker for x in ["1M", "2M", "3M", "6M", "1W"]):
                    categorized["forwards"][ticker] = data
                else:
                    categorized["spot_rates"][ticker] = data
            elif "SWET" in ticker:
                categorized["cm_curves"][ticker] = data

        return categorized

    def load_snapshot(self, date_str: str) -> Optional[Dict]:
        """Load snapshot for specific date."""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            year = dt.year
            file_path = self.base_path / str(year) / "daily" / f"{date_str}.json"

            if not file_path.exists():
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        except json.JSONDecodeError:
            print(f"[Snapshot] Corrupted JSON: {date_str}")
            return None
        except Exception:
            return None

    def list_available_snapshots(self, year: int) -> list[str]:
        """List all snapshot dates for a given year."""
        daily_dir = self.base_path / str(year) / "daily"
        if not daily_dir.exists():
            return []

        snapshots = []
        for file_path in sorted(daily_dir.glob("*.json")):
            # Extract date from filename
            date_str = file_path.stem  # YYYY-MM-DD
            snapshots.append(date_str)

        return snapshots
