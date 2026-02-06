"""
NIBOR File Manager - Dynamic file discovery for NIBOR fixing workbooks.

Handles automatic searching for the right NIBOR file based on:
1. Current date (year + quarter)
2. Settings-based TEST vs PROD mode switching (GUI configurable)

File naming convention:
- PROD: "Nibor fixing Q1 2026.xlsx"
- TEST: "Nibor fixing Q1 2026_TEST.xlsx"
"""
import os
import platform
from datetime import datetime
from pathlib import Path

from config import get_logger, DATA_DIR, USE_MOCK_DATA

log = get_logger("nibor_file_manager")


def _get_development_mode() -> bool:
    """
    Get development mode setting from settings.py.

    Returns True for TEST mode, False for PROD mode.
    Uses lazy import to avoid circular dependencies.
    """
    try:
        from settings import get_setting
        return get_setting("development_mode", False)  # Default to PROD mode
    except ImportError:
        # Fallback to config if settings not available
        from config import DEVELOPMENT_MODE
        return DEVELOPMENT_MODE


class NiborFileManager:
    """
    Hanterar automatisk sokning av ratt NIBOR-fil baserat pa datum och mode.
    """

    # File prefix for NIBOR fixing files
    FILE_PREFIX = "Nibor fixing"

    def __init__(self, base_path: Path | None = None):
        """
        Initialize NiborFileManager.

        Args:
            base_path: Override base path. If None, uses DATA_DIR/Referensräntor/Nibor/Historik Nibor
        """
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = DATA_DIR / "Referensräntor" / "Nibor" / "Historik Nibor"

        log.info(f"[NiborFileManager] Initialized with base_path: {self.base_path}")

    def get_current_quarter(self) -> str:
        """
        Calculate current quarter from today's date.

        Returns:
            str: Quarter string (Q1, Q2, Q3, Q4)
        """
        month = datetime.now().month
        quarter = (month - 1) // 3 + 1
        return f"Q{quarter}"

    def get_current_year(self) -> int:
        """
        Get current year.

        Returns:
            int: Current year (e.g., 2026)
        """
        return datetime.now().year

    def get_previous_quarter(self, year: int, quarter: str) -> tuple[int, str]:
        """
        Calculate previous quarter.

        Args:
            year: Current year
            quarter: Current quarter (Q1, Q2, Q3, Q4)

        Returns:
            tuple: (previous_year, previous_quarter)
        """
        q_num = int(quarter[1])  # "Q1" -> 1

        if q_num == 1:
            return year - 1, "Q4"
        else:
            return year, f"Q{q_num - 1}"

    def construct_filename(self, quarter: str, year: int, mode: str = "PROD") -> str:
        """
        Construct filename according to format and mode.

        Args:
            quarter: Q1, Q2, Q3, Q4
            year: 2026, 2027, etc
            mode: "PROD" or "TEST"

        Returns:
            Filename with or without _TEST suffix

        Raises:
            ValueError: If mode is invalid
        """
        if mode == "TEST":
            return f"{self.FILE_PREFIX} {quarter} {year}_TEST.xlsx"
        elif mode == "PROD":
            return f"{self.FILE_PREFIX} {quarter} {year}.xlsx"
        else:
            raise ValueError(f"Invalid mode: {mode}. Use 'PROD' or 'TEST'")

    def validate_file(self, file_path: Path) -> bool:
        """
        Validate that file is OK to use.

        Checks:
        1. File exists
        2. File is not suspiciously small (OneDrive "online only" files)
        3. File has valid Excel extension

        Args:
            file_path: Path to validate

        Returns:
            bool: True if file is valid
        """
        # Check 1: Exists
        if not file_path.exists():
            log.debug(f"[NiborFileManager] File does not exist: {file_path}")
            return False

        # Check 2: Not empty (OneDrive can have "online only" placeholder files)
        try:
            file_size = file_path.stat().st_size
            if file_size < 5000:
                log.warning(f"[NiborFileManager] File is suspiciously small: {file_size} bytes - {file_path}")
                return False
        except OSError as e:
            log.warning(f"[NiborFileManager] Could not stat file: {e}")
            return False

        # Check 3: Is Excel file
        if file_path.suffix.lower() not in ['.xlsx', '.xlsm']:
            log.debug(f"[NiborFileManager] Not an Excel file: {file_path.suffix}")
            return False

        return True

    def find_current_file(self, mode: str = "PROD") -> Path:
        """
        Find the correct NIBOR file for the current quarter.

        Search order:
        1. Current quarter file
        2. Previous quarter file (fallback)

        Args:
            mode: "PROD" or "TEST" - which version to use

        Returns:
            Path: Full path to the file

        Raises:
            FileNotFoundError: If no file is found
        """
        # Step 1: Get current year and quarter
        year = self.get_current_year()
        quarter = self.get_current_quarter()

        mode_display = "TEST" if mode == "TEST" else "PRODUCTION"
        log.info(f"[NiborFileManager] Searching for: {quarter} {year} ({mode_display} mode)")

        # Step 2: Construct path for current quarter
        filename = self.construct_filename(quarter, year, mode)
        file_path = self.base_path / str(year) / filename

        log.info(f"[NiborFileManager] Looking in: {file_path}")

        # Step 3: Validate that file exists and is OK
        if self.validate_file(file_path):
            log.info(f"[NiborFileManager] Found file: {filename}")
            return file_path

        # Step 4: If not found, try previous quarter
        log.warning(f"[NiborFileManager] {quarter} {year} file not found, trying previous quarter...")

        prev_year, prev_quarter = self.get_previous_quarter(year, quarter)
        prev_filename = self.construct_filename(prev_quarter, prev_year, mode)
        prev_file_path = self.base_path / str(prev_year) / prev_filename

        log.info(f"[NiborFileManager] Looking in: {prev_file_path}")

        if self.validate_file(prev_file_path):
            log.info(f"[NiborFileManager] Using previous quarter: {prev_filename}")
            log.warning(f"[NiborFileManager] WARNING: Using {prev_quarter} data for {quarter}!")
            return prev_file_path

        # Step 5: Nothing works - error
        raise FileNotFoundError(
            f"No NIBOR file found in {mode} mode!\n"
            f"Searched for:\n"
            f"  - {file_path}\n"
            f"  - {prev_file_path}\n"
            f"\nCreate the file manually or switch mode."
        )

    def get_file_info(self, file_path: Path) -> dict:
        """
        Get metadata about a NIBOR file.

        Args:
            file_path: Path to the file

        Returns:
            dict: File info including year, quarter, mode, size, modified time
        """
        filename = file_path.name

        # Parse filename
        is_test = "_TEST" in filename
        mode = "TEST" if is_test else "PROD"

        # Extract quarter and year from filename
        # Format: "Nibor fixing Q1 2026.xlsx" or "Nibor fixing Q1 2026_TEST.xlsx"
        parts = filename.replace("_TEST", "").replace(".xlsx", "").split()
        quarter = parts[-2] if len(parts) >= 2 else "?"
        year = parts[-1] if len(parts) >= 1 else "?"

        try:
            stat = file_path.stat()
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime)
        except OSError:
            size = 0
            modified = None

        return {
            "path": str(file_path),
            "filename": filename,
            "year": year,
            "quarter": quarter,
            "mode": mode,
            "size_bytes": size,
            "modified": modified,
            "is_test": is_test,
        }


def _find_fallback_nibor_file() -> Path | None:
    """
    Search for fallback NIBOR file in known locations.

    Checks multiple possible locations for dev and prod environments.

    Returns:
        Path to fallback file, or None if not found
    """
    # Fallback locations to check (in order of preference)
    fallback_candidates = [
        # Dev environment: data/Nibor/Historik/{year}/
        DATA_DIR / "Nibor" / "Historik" / "2025" / "Nibor fixing Testing Workbook.xlsx",
        # Prod environment: data/Referensräntor/Nibor/Historik Nibor/{year}/
        DATA_DIR / "Referensräntor" / "Nibor" / "Historik Nibor" / "2025" / "Nibor fixing Testing Workbook.xlsx",
    ]

    for path in fallback_candidates:
        if path.exists():
            return path

    return None


def get_nibor_file(mode: str | None = None) -> str:
    """
    Wrapper function to get the correct NIBOR file path.

    Uses development_mode setting from settings.py if mode is not specified.

    Args:
        mode: "PROD" or "TEST". If None, uses development_mode from settings.

    Returns:
        str: Full path to the file

    Raises:
        ValueError: If invalid mode
        FileNotFoundError: If no file found
    """
    # Determine mode from settings if not specified
    if mode is None:
        dev_mode = _get_development_mode()

        # Option: In DEV mode, still read the PROD Excel workbook (no _TEST suffix)
        # This is useful when the TEST workbook is not maintained.
        dev_use_prod_excel = False
        try:
            from settings import get_setting
            dev_use_prod_excel = bool(get_setting("dev_use_prod_excel", True))
        except Exception:
            dev_use_prod_excel = True

        if dev_mode and dev_use_prod_excel:
            mode = "PROD"
            log.info(
                f"[get_nibor_file] DEV mode active but dev_use_prod_excel=True -> using PROD workbook"
            )
        else:
            mode = "TEST" if dev_mode else "PROD"

        log.info(f"[get_nibor_file] Using mode from settings: {mode} (development_mode={dev_mode})")

    if mode not in ["PROD", "TEST"]:
        raise ValueError(f"Invalid mode: {mode}. Use 'PROD' or 'TEST'")

    # In mock data mode (Codespaces/Linux), fall back to hardcoded test file
    if USE_MOCK_DATA:
        fallback_path = _find_fallback_nibor_file()
        if fallback_path:
            log.info(f"[get_nibor_file] Using mock data fallback: {fallback_path}")
            return str(fallback_path)

    try:
        manager = NiborFileManager()
        file_path = manager.find_current_file(mode=mode)
        return str(file_path)

    except FileNotFoundError:
        # Last resort fallback for dev environment
        fallback_path = _find_fallback_nibor_file()
        if fallback_path:
            log.warning(f"[get_nibor_file] Dynamic lookup failed, using fallback: {fallback_path}")
            return str(fallback_path)
        raise


def get_nibor_file_path(mode: str | None = None) -> Path:
    """
    Get NIBOR file path as a Path object.

    Args:
        mode: "PROD" or "TEST". If None, uses DEVELOPMENT_MODE from config.

    Returns:
        Path: Path object to the file
    """
    return Path(get_nibor_file(mode))
