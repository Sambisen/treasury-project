"""
Configuration module for Onyx Terminal.
Contains theme, paths, rules, and mappings.
"""
import platform
from pathlib import Path

# ============================================================================
# DEVELOPMENT MODE
# ============================================================================
DEVELOPMENT_MODE = False  # Set True for testing without Bloomberg/Excel

FUNDING_SPREADS = {
    "1w": 0.15,  # 15 bps
    "1m": 0.20,  # 20 bps
    "2m": 0.20,
    "3m": 0.20,
    "6m": 0.20
}

# ==============================================================================
#  APP META
# ==============================================================================
APP_VERSION = "3.8.1-tk"

# ==============================================================================
#  THEME (ONYX PRIME)
# ==============================================================================
THEME = {
    "bg_main": "#050505",
    "bg_panel": "#0A0A0A",
    "bg_card": "#141414",
    "bg_card_2": "#1F1F1F",
    "bg_nav": "#050505",
    "bg_nav_sel": "#141414",
    "border": "#333333",
    "border_2": "#3A3A3A",
    "text": "#E6E8EC",
    "muted": "#9AA3AF",
    "muted2": "#6B7280",
    "accent": "#FF9F1C",
    "accent2": "#FFB75A",
    "good": "#10B981",
    "bad": "#EF4444",
    "warn": "#F59E0B",
    "yellow": "#FCD34D",
    "chip": "#141414",
    "chip2": "#1F1F1F",
    "shadow": "#000000",
    "row_even": "#0F0F0F",
    "row_odd": "#121212",
    "row_hover": "#1B1B1B",
    "tree_sel_bg": "#2B2B2B",
}

CURRENT_MODE = {"type": "OFFICE", "pad": 18, "hpad": 26, "title": 22, "h2": 14, "body": 12, "small": 10}


def set_mode(mode: str):
    if mode == "OFFICE":
        CURRENT_MODE.update({"type": "OFFICE", "pad": 18, "hpad": 26, "title": 22, "h2": 14, "body": 12, "small": 10})
    else:
        CURRENT_MODE.update({"type": "LAPTOP", "pad": 12, "hpad": 18, "title": 18, "h2": 13, "body": 11, "small": 9})


# ==============================================================================
#  DYNAMIC ENVIRONMENT DETECTION
# ==============================================================================
def _detect_environment() -> tuple[Path, bool]:
    """
    Detect the runtime environment and return appropriate paths.

    Returns:
        tuple: (BASE_DIR path, USE_MOCK_DATA flag)

    Windows (Office):
        - Looks for "OneDrive - Swedbank" folder in user home
        - Sets BASE_DIR to OneDrive path + GroupTreasury documents
        - USE_MOCK_DATA = False

    Linux (Codespaces/Cloud) or OneDrive not found:
        - Uses local "data" folder
        - USE_MOCK_DATA = True
    """
    home = Path.home()
    is_windows = platform.system() == "Windows"

    if is_windows:
        onedrive_path = home / "OneDrive - Swedbank"
        if onedrive_path.exists():
            base_dir = onedrive_path / "GroupTreasury-ShortTermFunding - Documents"
            return base_dir, False
        # Fallback for Windows without OneDrive
        app_dir = Path(__file__).resolve().parent
        return app_dir / "data", True
    else:
        # Linux/Codespaces environment
        app_dir = Path(__file__).resolve().parent
        return app_dir / "data", True


# Detect environment on module load
BASE_DIR, USE_MOCK_DATA = _detect_environment()

# ==============================================================================
#  PATHS
# ==============================================================================
APP_DIR = Path(__file__).resolve().parent
ASSETS_DIR = APP_DIR / "assets"

DATA_DIR = BASE_DIR  # Use dynamically detected path

# Skapa data-mappen om den inte finns
DATA_DIR.mkdir(parents=True, exist_ok=True)

EXCEL_LOGO_CANDIDATES = [
    DATA_DIR / "Bilder" / "Excel.png",
    DATA_DIR / "Bilder" / "Excel.jpg",
    ASSETS_DIR / "Excel.png",
    ASSETS_DIR / "Excel.jpg",
]
BBG_LOGO_CANDIDATES = [
    DATA_DIR / "Bilder" / "Bloomberg.png",
    DATA_DIR / "Bilder" / "Bloomberg.jpg",
    ASSETS_DIR / "Bloomberg.png",
    ASSETS_DIR / "Bloomberg.jpg",
]

BASE_HISTORY_PATH = DATA_DIR / "Referensräntor" / "Nibor" / "Historik Nibor"
STIBOR_GRSS_PATH = DATA_DIR / "Referensräntor" / "Stibor" / "GRSS Spreadsheet"

DAY_FILES = [
    DATA_DIR / "Referensräntor" / "Stibor" / "GRSS Spreadsheet" / "Nibor days 2025.xlsx",
    DATA_DIR / "Referensräntor" / "Stibor" / "GRSS Spreadsheet" / "Nibor days 2026.xlsx"
]
RECON_FILE = DATA_DIR / "Referensräntor" / "Nibor" / "Historik Nibor" / "2025" / "Nibor fixing Testing Workbook.xlsx"

# WEIGHTS (Monthly control)
WEIGHTS_FILE = DATA_DIR / "Nibor" / "Vikter" / "Weights.xlsx"

CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ==============================================================================
#  RULES / MAPPINGS
# ==============================================================================
RULES_DB = [
    ("1", "A6", "A29", "Exakt Match", "Cell Mismatch"), ("2", "A7", "A30", "Exakt Match", "Cell Mismatch"),
    ("3", "A8", "A31", "Exakt Match", "Cell Mismatch"), ("4", "A9", "A32", "Exakt Match", "Cell Mismatch"),
    ("5", "A10", "A33", "Exakt Match", "Cell Mismatch"), ("6", "B6", "B29", "Exakt Match", "Cell Mismatch"),
    ("7", "B7", "B30", "Exakt Match", "Cell Mismatch"), ("8", "B8", "B31", "Exakt Match", "Cell Mismatch"),
    ("9", "B9", "B32", "Exakt Match", "Cell Mismatch"), ("10", "B10", "B33", "Exakt Match", "Cell Mismatch"),
    ("11", "C6", "C29", "Exakt Match", "Cell Mismatch"), ("12", "C7", "C30", "Exakt Match", "Cell Mismatch"),
    ("13", "C8", "C31", "Exakt Match", "Cell Mismatch"), ("14", "C9", "C32", "Exakt Match", "Cell Mismatch"),
    ("15", "C10", "C33", "Exakt Match", "Cell Mismatch"), ("16", "D6", "D29", "Exakt Match", "Cell Mismatch"),
    ("17", "D7", "D30", "Exakt Match", "Cell Mismatch"), ("18", "D8", "D31", "Exakt Match", "Cell Mismatch"),
    ("19", "D9", "D32", "Exakt Match", "Cell Mismatch"), ("20", "D10", "D33", "Exakt Match", "Cell Mismatch"),
    ("21", "E6", "E29", "Exakt Match", "Cell Mismatch"), ("22", "E7", "E30", "Exakt Match", "Cell Mismatch"),
    ("23", "E8", "E31", "Exakt Match", "Cell Mismatch"), ("24", "E9", "E32", "Exakt Match", "Cell Mismatch"),
    ("25", "E10", "E33", "Exakt Match", "Cell Mismatch"), ("26", "F6", "F29", "Exakt Match", "Cell Mismatch"),
    ("27", "F7", "F30", "Exakt Match", "Cell Mismatch"), ("28", "F8", "F31", "Exakt Match", "Cell Mismatch"),
    ("29", "F9", "F32", "Exakt Match", "Cell Mismatch"), ("30", "F10", "F33", "Exakt Match", "Cell Mismatch"),
    ("31", "G6", "G29", "Exakt Match", "Cell Mismatch"), ("32", "G7", "G30", "Exakt Match", "Cell Mismatch"),
    ("33", "G8", "G31", "Exakt Match", "Cell Mismatch"), ("34", "G9", "G32", "Exakt Match", "Cell Mismatch"),
    ("35", "G10", "G33", "Exakt Match", "Cell Mismatch"), ("36", "H6", "H29", "Exakt Match", "Cell Mismatch"),
    ("37", "H7", "H30", "Exakt Match", "Cell Mismatch"), ("38", "H8", "H31", "Exakt Match", "Cell Mismatch"),
    ("39", "H9", "H32", "Exakt Match", "Cell Mismatch"), ("40", "H10", "H33", "Exakt Match", "Cell Mismatch"),
    ("41", "I6", "I29", "Exakt Match", "Cell Mismatch"), ("42", "I7", "I30", "Exakt Match", "Cell Mismatch"),
    ("43", "I8", "I31", "Exakt Match", "Cell Mismatch"), ("44", "I9", "I32", "Exakt Match", "Cell Mismatch"),
    ("45", "I10", "I33", "Exakt Match", "Cell Mismatch"), ("46", "J6", "J29", "Exakt Match", "Cell Mismatch"),
    ("47", "J7", "J30", "Exakt Match", "Cell Mismatch"), ("48", "J8", "J31", "Exakt Match", "Cell Mismatch"),
    ("49", "J9", "J32", "Exakt Match", "Cell Mismatch"), ("50", "J10", "J33", "Exakt Match", "Cell Mismatch"),
    ("51", "K6", "K29", "Exakt Match", "Cell Mismatch"), ("52", "K7", "K30", "Exakt Match", "Cell Mismatch"),
    ("53", "K8", "K31", "Exakt Match", "Cell Mismatch"), ("54", "K9", "K32", "Exakt Match", "Cell Mismatch"),
    ("55", "K10", "K33", "Exakt Match", "Cell Mismatch"), ("56", "L6", "L29", "Exakt Match", "Cell Mismatch"),
    ("57", "L7", "L30", "Exakt Match", "Cell Mismatch"), ("58", "L8", "L31", "Exakt Match", "Cell Mismatch"),
    ("59", "L9", "L32", "Exakt Match", "Cell Mismatch"), ("60", "L10", "L33", "Exakt Match", "Cell Mismatch"),
    ("61", "N6", "N29", "Exakt Match", "Cell Mismatch"), ("62", "N7", "N30", "Exakt Match", "Cell Mismatch"),
    ("63", "N8", "N31", "Exakt Match", "Cell Mismatch"), ("64", "N9", "N32", "Exakt Match", "Cell Mismatch"),
    ("65", "N10", "N33", "Exakt Match", "Cell Mismatch"), ("66", "O6", "O29", "Exakt Match", "Cell Mismatch"),
    ("67", "O7", "O30", "Exakt Match", "Cell Mismatch"), ("68", "O8", "O31", "Exakt Match", "Cell Mismatch"),
    ("69", "O9", "O32", "Exakt Match", "Cell Mismatch"), ("70", "O10", "O33", "Exakt Match", "Cell Mismatch"),
    ("71", "Q6", "Q29", "Exakt Match", "Cell Mismatch"), ("72", "Q7", "Q30", "Exakt Match", "Cell Mismatch"),
    ("73", "Q8", "Q31", "Exakt Match", "Cell Mismatch"), ("74", "Q9", "Q32", "Exakt Match", "Cell Mismatch"),
    ("75", "Q10", "Q33", "Exakt Match", "Cell Mismatch"), ("76", "S6", "S29", "Exakt Match", "Cell Mismatch"),
    ("77", "S7", "S30", "Exakt Match", "Cell Mismatch"), ("78", "S8", "S31", "Exakt Match", "Cell Mismatch"),
    ("79", "S9", "S32", "Exakt Match", "Cell Mismatch"), ("80", "S10", "S33", "Exakt Match", "Cell Mismatch"),
    ("81", "T6", "T29", "Exakt Match", "Cell Mismatch"), ("82", "T7", "T30", "Exakt Match", "Cell Mismatch"),
    ("83", "T8", "T31", "Exakt Match", "Cell Mismatch"), ("84", "T9", "T32", "Exakt Match", "Cell Mismatch"),
    ("85", "T10", "T33", "Exakt Match", "Cell Mismatch"), ("86", "V6", "V29", "Exakt Match", "Cell Mismatch"),
    ("87", "V7", "V30", "Exakt Match", "Cell Mismatch"), ("88", "V8", "V31", "Exakt Match", "Cell Mismatch"),
    ("89", "V9", "V32", "Exakt Match", "Cell Mismatch"), ("90", "V10", "V33", "Exakt Match", "Cell Mismatch"),
    ("91", "W6", "W29", "Exakt Match", "Cell Mismatch"), ("92", "W7", "W30", "Exakt Match", "Cell Mismatch"),
    ("93", "W8", "W31", "Exakt Match", "Cell Mismatch"), ("94", "W9", "W32", "Exakt Match", "Cell Mismatch"),
    ("95", "W10", "W33", "Exakt Match", "Cell Mismatch"), ("96", "AB6", "AB29", "Exakt Match", "Cell Mismatch"),
    ("97", "AB7", "AB30", "Exakt Match", "Cell Mismatch"), ("98", "AB8", "AB31", "Exakt Match", "Cell Mismatch"),
    ("99", "AB9", "AB32", "Exakt Match", "Cell Mismatch"), ("100", "AB10", "AB33", "Exakt Match", "Cell Mismatch"),
    ("101", "AC6", "AC29", "Exakt Match", "Cell Mismatch"), ("102", "AC7", "AC30", "Exakt Match", "Cell Mismatch"),
    ("103", "AC8", "AC31", "Exakt Match", "Cell Mismatch"), ("104", "AC9", "AC32", "Exakt Match", "Cell Mismatch"),
    ("105", "AC10", "AC33", "Exakt Match", "Cell Mismatch"),
    ("106", "AD6", "AD29", "Exakt Match", "Pid doesnt match"),
    ("107", "AD7", "AD30", "Exakt Match", "Pid doesnt match"),
    ("108", "AD8", "AD31", "Exakt Match", "Pid doesnt match"),
    ("109", "AD9", "AD32", "Exakt Match", "Pid doesnt match"),
    ("110", "AD10", "AD33", "Exakt Match", "Pid doesnt match"),
    ("111", "Z7", "Z30", "Avrundat 2 dec", "1 Month Nibor contribution differ"),
    ("112", "Z8", "Z31", "Avrundat 2 dec", "2 Month Nibor contribution differ"),
    ("113", "Z9", "Z32", "Avrundat 2 dec", "3 Month Nibor contribution differ"),
    ("114", "Z10", "Z33", "Avrundat 2 dec", "6 Month Nibor contribution differ"),
    ("115", "AA7", "AA30", "Avrundat 2 dec", "1 Month Nibor contribution differ"),
    ("116", "AA8", "AA31", "Avrundat 2 dec", "2 Month Nibor contribution differ"),
    ("117", "AA9", "AA32", "Avrundat 2 dec", "3 Month Nibor contribution differ"),
    ("118", "AA10", "AA33", "Avrundat 2 dec", "6 Month Nibor contribution differ"),
    ("119", "Y6", "-", "0.10-0.20", "Spread not within range (!) must be < 0.10-0.20>"),
    ("120", "Y7", "-", "0.15-0.25", "Spread not within range (!) must be < 0.15-0.25>"),
    ("121", "Y8", "-", "0.15-0.25", "Spread not within range (!) must be < 0.15-0.25>"),
    ("122", "Y9", "-", "0.15-0.25", "Spread not within range (!) must be < 0.15-0.25>"),
    ("123", "Y10", "-", "0.15-0.25", "Spread not within range (!) must be < 0.15-0.25>"),
    ("124", "Y29", "-", "Exakt 0.15", "Shall Always be 0,15. Fixed spread"),
    ("125", "Y30", "-", "Exakt 0.20", "Shall Always be 0,20. Fixed spread"),
    ("126", "Y31", "-", "Exakt 0.20", "Shall Always be 0,20. Fixed spread"),
    ("127", "Y32", "-", "Exakt 0.20", "Shall Always be 0,20. Fixed spread"),
    ("128", "Y33", "-", "Exakt 0.20", "Shall Always be 0,20. Fixed spread")
]

RECON_MAPPING = [
    ("N6", "EURNOK Spot", "NKEU F033 Curncy"), ("N7", "EURNOK Spot", "NKEU F033 Curncy"),
    ("N8", "EURNOK Spot", "NKEU F033 Curncy"), ("N9", "EURNOK Spot", "NKEU F033 Curncy"),
    ("N10", "EURNOK Spot", "NKEU F033 Curncy"),
    ("S6", "USDNOK Spot", "NOK F033 Curncy"), ("S7", "USDNOK Spot", "NOK F033 Curncy"),
    ("S8", "USDNOK Spot", "NOK F033 Curncy"), ("S9", "USDNOK Spot", "NOK F033 Curncy"),
    ("S10", "USDNOK Spot", "NOK F033 Curncy"),
    ("O6", "EURNOK Fwd (1w)", "NKEU1W F033 Curncy"), ("O7", "EURNOK Fwd (1m)", "NKEU1M F033 Curncy"),
    ("O8", "EURNOK Fwd (2m)", "NKEU2M F033 Curncy"), ("O9", "EURNOK Fwd (3m)", "NKEU3M F033 Curncy"),
    ("O10", "EURNOK Fwd (6m)", "NKEU6M F033 Curncy"),
    ("T6", "USDNOK Fwd (1w)", "NK1W F033 Curncy"), ("T7", "USDNOK Fwd (1m)", "NK1M F033 Curncy"),
    ("T8", "USDNOK Fwd (2m)", "NK2M F033 Curncy"), ("T9", "USDNOK Fwd (3m)", "NK3M F033 Curncy"),
    ("T10", "USDNOK Fwd (6m)", "NK6M F033 Curncy"),
]

DAYS_MAPPING = [
    ("C6", "Days (1w)", "1w"), ("C7", "Days (1m)", "1m"), ("C8", "Days (2m)", "2m"),
    ("C9", "Days (3m)", "3m"), ("C10", "Days (6m)", "6m")
]

# WEIGHTS mapping (EXACT cells)
WEIGHTS_FILE_CELLS = {"H3": "H3", "H4": "H4", "H5": "H5", "H6": "H6", "USD": "I3", "EUR": "J3", "NOK": "K3"}
WEIGHTS_MODEL_CELLS = {"DATE": "A41", "USD": "B43", "EUR": "B44", "NOK": "B45"}

# Excel CM rates mapping (from Nibor fixing Testing Workbook.xlsx)
# EUR CM: M30-M33 (1M, 2M, 3M, 6M)
# USD CM: R30-R33 (1M, 2M, 3M, 6M)
EXCEL_CM_RATES_MAPPING = {
    "EUR_1M": "M30", "EUR_2M": "M31", "EUR_3M": "M32", "EUR_6M": "M33",
    "USD_1M": "R30", "USD_2M": "R31", "USD_3M": "R32", "USD_6M": "R33",
}

MARKET_STRUCTURE = {
    "SPOT RATES": [
        ("NOK F033 Curncy", "USDNOK Spot"),
        ("NKEU F033 Curncy", "EURNOK Spot"),
    ],
    "USDNOK FORWARDS": [
        ("NK1W F033 Curncy", "1w"),
        ("NK1M F033 Curncy", "1m"),
        ("NK2M F033 Curncy", "2m"),
        ("NK3M F033 Curncy", "3m"),
        ("NK6M F033 Curncy", "6m"),
    ],
    "EURNOK FORWARDS": [
        ("NKEU1W F033 Curncy", "1w"),
        ("NKEU1M F033 Curncy", "1m"),
        ("NKEU2M F033 Curncy", "2m"),
        ("NKEU3M F033 Curncy", "3m"),
        ("NKEU6M F033 Curncy", "6m"),
    ],
    "SWET CM CURVES": [
        ("EUCM1M SWET Curncy", "EUR CM 1M"),
        ("EUCM2M SWET Curncy", "EUR CM 2M"),
        ("EUCM3M SWET Curncy", "EUR CM 3M"),
        ("EUCM6M SWET Curncy", "EUR CM 6M"),
        ("USCM1M SWET Curncy", "USD CM 1M"),
        ("USCM2M SWET Curncy", "USD CM 2M"),
        ("USCM3M SWET Curncy", "USD CM 3M"),
        ("USCM6M SWET Curncy", "USD CM 6M"),
    ],
    "NIBOR FIXINGS (MARKET)": [
        ("NKCM1M SWET Curncy", "NOK CM 1M"),
        ("NKCM2M SWET Curncy", "NOK CM 2M"),
        ("NKCM3M SWET Curncy", "NOK CM 3M"),
        ("NKCM6M SWET Curncy", "NOK CM 6M"),
    ]
}

ALL_REAL_TICKERS = sorted(list(set(
    [t for sec in MARKET_STRUCTURE.values() for t, _ in sec] +
    [m[2] for m in RECON_MAPPING] +
    ["USCM6M SWET Curncy"]
)))

SWET_CM_RECON_MAPPING: list[tuple[str, str, str]] = []
