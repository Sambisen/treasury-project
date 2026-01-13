"""
Data engines for Onyx Terminal.
Contains ExcelEngine and BloombergEngine.
"""
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import coordinate_to_tuple

from config import (
    BASE_HISTORY_PATH, DAY_FILES, RECON_FILE, WEIGHTS_FILE,
    RECON_MAPPING, DAYS_MAPPING, RULES_DB, SWET_CM_RECON_MAPPING,
    WEIGHTS_FILE_CELLS, WEIGHTS_MODEL_CELLS, USE_MOCK_DATA,
    EXCEL_CM_RATES_MAPPING, DEVELOPMENT_MODE
)
from utils import copy_to_cache_fast, safe_float, to_date

# Bloomberg API optional
try:
    import blpapi
except ImportError:
    blpapi = None


def build_required_cell_set() -> set[tuple[int, int]]:
    """Build set of all required cells for Excel reading."""
    needed = set()

    for cell, _, _ in RECON_MAPPING:
        needed.add(coordinate_to_tuple(cell))

    for cell, _, _ in DAYS_MAPPING:
        needed.add(coordinate_to_tuple(cell))

    for _, top_cell, ref_cell, logic, _ in RULES_DB:
        if top_cell and top_cell != "-":
            needed.add(coordinate_to_tuple(top_cell))
        if ref_cell and ref_cell != "-" and logic in ("Exakt Match", "Avrundat 2 dec"):
            needed.add(coordinate_to_tuple(ref_cell))

    for cell, _, _ in SWET_CM_RECON_MAPPING:
        needed.add(coordinate_to_tuple(cell))

    for c in WEIGHTS_MODEL_CELLS.values():
        needed.add(coordinate_to_tuple(c))

    return needed


REQUIRED_CELLS = build_required_cell_set()


class ExcelEngine:
    """Engine for reading and processing Excel files."""

    def __init__(self):
        self.day_data = pd.DataFrame()
        self._day_data_ready = False
        self._day_data_err = None

        self.recon_data = {}
        self.current_filename = ""
        self.current_folder_path = BASE_HISTORY_PATH
        self.current_year_loaded = ""
        self.last_loaded_ts: datetime | None = None

        self._last_src: Path | None = None
        self._last_mtime: float | None = None
        self._last_size: int | None = None

        # WEIGHTS file cache
        self.weights_ok: bool = False
        self.weights_err: str | None = "Not loaded"
        self.weights_last_loaded_ts: datetime | None = None
        self.weights_cells_raw: dict[str, object] = {}
        self.weights_cells_parsed: dict[str, object] = {}

        # Excel CM rates cache (from Nibor fixing workbook)
        self.excel_cm_rates: dict[str, float] = {}

        # Swedbank contribution data (from Nibor fixing workbook)
        self.swedbank_contribution: dict[str, dict] = {}

        threading.Thread(target=self._load_day_files_bg, daemon=True).start()

    def _load_day_files_bg(self):
        try:
            dfs = []
            for f_path in DAY_FILES:
                if not f_path.exists():
                    continue
                try:
                    df = pd.read_excel(f_path, engine="openpyxl")
                    dfs.append(df)
                except Exception:
                    try:
                        temp = copy_to_cache_fast(f_path)
                        df = pd.read_excel(temp, engine="openpyxl")
                        dfs.append(df)
                    except Exception:
                        continue

            if dfs:
                day_data = pd.concat(dfs, ignore_index=True)
                if "date" in day_data.columns:
                    day_data["date"] = pd.to_datetime(day_data["date"], errors="coerce")
                    day_data["date"] = day_data["date"].dt.normalize()
                    day_data = day_data.dropna(subset=["date"]).sort_values("date")
                self.day_data = day_data
            self._day_data_ready = True
        except Exception as e:
            self._day_data_err = str(e)
            self._day_data_ready = True

    def resolve_latest_path(self):
        if RECON_FILE.exists():
            self.current_folder_path = RECON_FILE.parent
            self.current_year_loaded = RECON_FILE.parent.name
            self.current_filename = RECON_FILE.name
            return RECON_FILE, "OK"
        return None, "File Not Found"

    def load_weights_file(self) -> bool:
        """Load EXACT cells from Weights.xlsx."""
        try:
            if not WEIGHTS_FILE.exists():
                self.weights_ok = False
                self.weights_err = f"Missing file: {WEIGHTS_FILE}"
                self.weights_cells_raw = {}
                self.weights_cells_parsed = {}
                return False

            wb = None
            try:
                wb = load_workbook(WEIGHTS_FILE, data_only=True, read_only=True)
            except Exception:
                temp_path = copy_to_cache_fast(WEIGHTS_FILE)
                wb = load_workbook(temp_path, data_only=True, read_only=True)

            ws = wb[wb.sheetnames[0]]

            raw = {}
            parsed = {}

            for k in ("H3", "H4", "H5", "H6"):
                cell = WEIGHTS_FILE_CELLS[k]
                v = ws[cell].value
                raw[k] = v
                parsed[k] = to_date(v)

            for k in ("USD", "EUR", "NOK"):
                cell = WEIGHTS_FILE_CELLS[k]
                v = ws[cell].value
                raw[k] = v
                parsed[k] = safe_float(v, None)

            wb.close()

            self.weights_cells_raw = dict(raw)
            self.weights_cells_parsed = dict(parsed)
            self.weights_ok = True
            self.weights_err = None
            self.weights_last_loaded_ts = datetime.now()
            return True
        except Exception as e:
            self.weights_ok = False
            self.weights_err = str(e)
            self.weights_cells_raw = {}
            self.weights_cells_parsed = {}
            return False

    def load_recon_direct(self):
        try:
            file_path, msg = self.resolve_latest_path()
            if not file_path:
                return False, msg

            try:
                st = file_path.stat()
                self._last_src = file_path
                self._last_mtime = st.st_mtime
                self._last_size = st.st_size
            except Exception:
                pass

            wb = None
            try:
                wb = load_workbook(file_path, data_only=True, read_only=True)
            except Exception:
                temp_path = copy_to_cache_fast(file_path)
                wb = load_workbook(temp_path, data_only=True, read_only=True)

            sheet_name = wb.sheetnames[-1]
            ws = wb[sheet_name]

            recon = {}
            for (r, c) in REQUIRED_CELLS:
                recon[(r, c)] = ws.cell(row=r, column=c).value

            # Read Excel CM rates (EUR and USD)
            cm_rates = {}
            for key, cell_ref in EXCEL_CM_RATES_MAPPING.items():
                val = ws[cell_ref].value
                cm_rates[key] = safe_float(val, None)

            # Extract Swedbank contribution data
            from config import SWEDBANK_CONTRIBUTION_CELLS
            swedbank_contrib = {}
            for tenor, cells in SWEDBANK_CONTRIBUTION_CELLS.items():
                swedbank_contrib[tenor] = {
                    "Z": safe_float(ws[cells["Z"]].value, None),
                    "AA": safe_float(ws[cells["AA"]].value, None)
                }

            wb.close()

            self.recon_data = recon
            self.excel_cm_rates = cm_rates
            self.swedbank_contribution = swedbank_contrib
            self.last_loaded_ts = datetime.now()

            self.load_weights_file()

            return True, f"{self.current_year_loaded} / {self.current_filename}"
        except Exception as e:
            return False, str(e)

    def get_days_for_date(self, date_str):
        if self.day_data.empty or "date" not in self.day_data.columns:
            return None
        try:
            target_date = pd.to_datetime(date_str)
            target_date = target_date.normalize()

            row = self.day_data[self.day_data["date"] == target_date]
            if not row.empty:
                r = row.iloc[0]
                return {
                    "1w": r.get("1w_Days", "-"),
                    "1m": r.get("1m_Days", "-"),
                    "2m": r.get("2m_Days", "-"),
                    "3m": r.get("3m_Days", "-"),
                    "6m": r.get("6m_Days", "-"),
                }
        except Exception:
            return None
        return None

    def get_future_days_data(self, limit_rows=300):
        if self.day_data.empty or "date" not in self.day_data.columns:
            return pd.DataFrame()
        today = pd.Timestamp(datetime.now().date()).normalize()
        future_df = self.day_data[self.day_data["date"] >= today].copy()
        for c in ["date", "settlement"]:
            if c in future_df.columns:
                future_df[c] = pd.to_datetime(future_df[c], errors="coerce").dt.strftime("%Y-%m-%d")
        future_df = future_df.reset_index(drop=True)
        if len(future_df) > limit_rows:
            future_df = future_df.iloc[:limit_rows].copy()
        return future_df

    def get_recon_value(self, cell_ref):
        try:
            row, col = coordinate_to_tuple(cell_ref)
            return self.recon_data.get((row, col), None)
        except Exception:
            return None


class HistoricalDataManager:
    """
    Manages historical snapshot comparison and sheet identification.
    Handles multi-sheet Excel workbook parsing.
    """

    def __init__(self, excel_engine: ExcelEngine, snapshot_engine):
        self.excel_engine = excel_engine
        self.snapshot_engine = snapshot_engine

    def identify_sheet_date(self, sheet_name: str) -> str | None:
        """
        Extract date from sheet name.
        Patterns: "2025-01-13", "13-01-2025", "13.01.2025", etc.

        Returns: Date string in YYYY-MM-DD format or None
        """
        import re

        patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',  # 2025-01-13
            r'(\d{2})-(\d{2})-(\d{4})',  # 13-01-2025
            r'(\d{2})\.(\d{2})\.(\d{4})',  # 13.01.2025
        ]

        for pattern in patterns:
            match = re.search(pattern, sheet_name)
            if match:
                groups = match.groups()
                # Determine format and convert to YYYY-MM-DD
                if len(groups[0]) == 4:  # YYYY-MM-DD
                    return f"{groups[0]}-{groups[1]}-{groups[2]}"
                else:  # DD-MM-YYYY or DD.MM.YYYY
                    return f"{groups[2]}-{groups[1]}-{groups[0]}"

        return None

    def get_all_workbook_sheets(self, workbook_path: Path) -> list[tuple[str, str]]:
        """
        Get all sheets from workbook with their dates.

        Returns: List of (sheet_name, date_str) tuples
        """
        from openpyxl import load_workbook

        try:
            wb = load_workbook(workbook_path, data_only=True, read_only=True)
            sheets_with_dates = []

            for sheet_name in wb.sheetnames:
                date_str = self.identify_sheet_date(sheet_name)
                if date_str:
                    sheets_with_dates.append((sheet_name, date_str))

            wb.close()
            return sheets_with_dates

        except Exception:
            return []

    def load_sheet_by_date(self, workbook_path: Path, target_date: str) -> dict | None:
        """
        Load specific sheet by date and extract contribution data.

        Returns: Dict with cell data or None
        """
        from openpyxl import load_workbook

        try:
            wb = load_workbook(workbook_path, data_only=True, read_only=True)

            # Find sheet matching target_date
            target_sheet = None
            for sheet_name in wb.sheetnames:
                if self.identify_sheet_date(sheet_name) == target_date:
                    target_sheet = sheet_name
                    break

            if not target_sheet:
                wb.close()
                return None

            ws = wb[target_sheet]

            # Extract contribution cells (Z7-Z10, AA7-AA10)
            contribution_cells = {
                "Z7": ws["Z7"].value,
                "AA7": ws["AA7"].value,
                "Z8": ws["Z8"].value,
                "AA8": ws["AA8"].value,
                "Z9": ws["Z9"].value,
                "AA9": ws["AA9"].value,
                "Z10": ws["Z10"].value,
                "AA10": ws["AA10"].value,
            }

            wb.close()
            return contribution_cells

        except Exception:
            return None

    def compare_contributions(self, today_date: str, yesterday_date: str) -> dict:
        """
        Compare Swedbank contributions between two dates.

        Returns: Dict with changes per tenor
        """
        today_snapshot = self.snapshot_engine.load_snapshot(today_date)
        yesterday_snapshot = self.snapshot_engine.load_snapshot(yesterday_date)

        if not today_snapshot or not yesterday_snapshot:
            return {"error": "Missing snapshot data"}

        today_contrib = today_snapshot.get("swedbank_contribution", {})
        yesterday_contrib = yesterday_snapshot.get("swedbank_contribution", {})

        changes = {}
        for tenor in ["1M", "2M", "3M", "6M"]:
            # Get Z cell values
            z_cell_key = f"Z{7 + ['1M','2M','3M','6M'].index(tenor)}"
            today_val = today_contrib.get(tenor, {}).get(z_cell_key)
            yesterday_val = yesterday_contrib.get(tenor, {}).get(z_cell_key)

            if today_val is not None and yesterday_val is not None:
                changes[tenor] = {
                    "today": today_val,
                    "yesterday": yesterday_val,
                    "change": today_val - yesterday_val
                }

        return changes


def _load_mock_defaults_from_excel() -> dict:
    """
    Load mock Bloomberg data from Implied_NOK_Defaults.xlsx.
    Returns dict mapping ticker -> price.

    Includes:
    - Spot rates (F033 Curncy)
    - Forward prices (F033 Curncy)
    - CM rates (SWET Curncy)
    - Days to maturity (TPSF Curncy) - for DAYS_TO_MTY field
    """
    from config import DATA_DIR

    defaults_file = DATA_DIR / "Implied_NOK_Defaults.xlsx"

    # Fallback values if file doesn't exist
    fallback = {
        # Spots
        "NOK F033 Curncy": 10.20, "NKEU F033 Curncy": 11.95,
        # USDNOK forwards
        "NK1W F033 Curncy": 10.20, "NK1M F033 Curncy": 10.20,
        "NK2M F033 Curncy": 10.21, "NK3M F033 Curncy": 10.21,
        "NK6M F033 Curncy": 10.22,
        # EURNOK forwards
        "NKEU1W F033 Curncy": 11.96, "NKEU1M F033 Curncy": 11.98,
        "NKEU2M F033 Curncy": 11.99, "NKEU3M F033 Curncy": 12.01,
        "NKEU6M F033 Curncy": 12.07,
        # EUR CM rates
        "EUCM1M SWET Curncy": 1.8, "EUCM2M SWET Curncy": 1.9,
        "EUCM3M SWET Curncy": 2.02, "EUCM6M SWET Curncy": 2.11,
        # USD CM rates
        "USCM1M SWET Curncy": 3.65, "USCM2M SWET Curncy": 3.7,
        "USCM3M SWET Curncy": 3.73, "USCM6M SWET Curncy": 3.73,
        # NOK CM rates (NIBOR)
        "NKCM1M SWET Curncy": 4.6, "NKCM2M SWET Curncy": 4.55,
        "NKCM3M SWET Curncy": 4.5, "NKCM6M SWET Curncy": 4.4,
        # DAYS_TO_MTY - EURNOK (TPSF Curncy)
        "EURNOK1W TPSF Curncy": 7, "EURNOK1M TPSF Curncy": 30,
        "EURNOK2M TPSF Curncy": 60, "EURNOK3M TPSF Curncy": 90,
        "EURNOK6M TPSF Curncy": 180,
        # DAYS_TO_MTY - USDNOK (TPSF Curncy)
        "NK1W TPSF Curncy": 7, "NK1M TPSF Curncy": 30,
        "NK2M TPSF Curncy": 60, "NK3M TPSF Curncy": 90,
        "NK6M TPSF Curncy": 180,
    }

    if not defaults_file.exists():
        return fallback

    try:
        df = pd.read_excel(defaults_file, header=1)
        df.columns = ["TENOR", "EURNOK_SPOT", "EURNOK_PIPS", "USDNOK_SPOT",
                      "USDNOK_PIPS", "DAYS", "EUR_CM", "USD_CM", "NOK_CM"]

        prices = {}
        tenor_map = {"1W": "1W", "1M": "1M", "2M": "2M", "3M": "3M", "6M": "6M"}

        for _, row in df.iterrows():
            tenor = str(row["TENOR"]).strip().upper()
            if tenor not in tenor_map:
                continue

            t = tenor_map[tenor]

            # Spots (same for all tenors, use first row values)
            eur_spot = float(row["EURNOK_SPOT"])
            usd_spot = float(row["USDNOK_SPOT"])
            prices["NKEU F033 Curncy"] = eur_spot
            prices["NOK F033 Curncy"] = usd_spot

            # Forward prices = spot + pips/10000
            eur_pips = float(row["EURNOK_PIPS"])
            usd_pips = float(row["USDNOK_PIPS"])
            prices[f"NKEU{t} F033 Curncy"] = eur_spot + (eur_pips / 10000.0)
            prices[f"NK{t} F033 Curncy"] = usd_spot + (usd_pips / 10000.0)

            # CM rates
            prices[f"EUCM{t} SWET Curncy"] = float(row["EUR_CM"])
            prices[f"USCM{t} SWET Curncy"] = float(row["USD_CM"])
            prices[f"NKCM{t} SWET Curncy"] = float(row["NOK_CM"])

            # Days to maturity (DAYS_TO_MTY field from Bloomberg)
            days_val = int(row["DAYS"])
            prices[f"EURNOK{t} TPSF Curncy"] = days_val
            prices[f"NK{t} TPSF Curncy"] = days_val

        # Add 1W if not in file (estimate)
        if "NKEU1W F033 Curncy" not in prices:
            prices["NKEU1W F033 Curncy"] = prices.get("NKEU F033 Curncy", 11.95) + 0.005
        if "NK1W F033 Curncy" not in prices:
            prices["NK1W F033 Curncy"] = prices.get("NOK F033 Curncy", 10.20) + 0.0001
        if "EURNOK1W TPSF Curncy" not in prices:
            prices["EURNOK1W TPSF Curncy"] = 7
        if "NK1W TPSF Curncy" not in prices:
            prices["NK1W TPSF Curncy"] = 7

        return prices

    except Exception as e:
        print(f"Warning: Could not load mock defaults from Excel: {e}")
        return fallback


class BloombergEngine:
    """
    Bloomberg ingestion engine with caching.
    Automatically falls back to mock data if:
    - blpapi is not installed (Linux/cloud environment)
    - USE_MOCK_DATA is True in config
    """

    def __init__(self, cache_ttl_sec: float = 3.0):
        self._lock = threading.Lock()
        self._session = None
        self._service = None
        self._is_ready = False
        self._last_error = None

        self._cache_ttl_sec = float(cache_ttl_sec)
        self._cache_data: dict = {}
        self._cache_ts: float | None = None
        self._cache_tickers: tuple[str, ...] | None = None
        self._last_meta: dict = {}

        # Determine if we should use mock mode
        self._use_mock = (blpapi is None) or USE_MOCK_DATA or DEVELOPMENT_MODE

        # Load mock prices from Excel file (used in mock mode)
        self._mock_prices = _load_mock_defaults_from_excel() if self._use_mock else {}

        # Only start Bloomberg session if not in mock mode
        if blpapi and not self._use_mock:
            self._start_session_async()

    def _start_session_async(self):
        def _starter():
            try:
                session_options = blpapi.SessionOptions()
                session_options.setServerHost("localhost")
                session_options.setServerPort(8194)
                session = blpapi.Session(session_options)
                if not session.start():
                    self._last_error = "Session Start Failed"
                    return
                if not session.openService("//blp/refdata"):
                    session.stop()
                    self._last_error = "Service Open Failed"
                    return
                service = session.getService("//blp/refdata")
                self._session = session
                self._service = service
                self._is_ready = True
                self._last_error = None
            except Exception as e:
                self._last_error = str(e)
        threading.Thread(target=_starter, daemon=True).start()

    def last_meta(self) -> dict:
        return dict(self._last_meta or {})

    def _generate_mock_price(self, ticker: str) -> dict:
        """Generate mock price data for a ticker from Excel defaults."""
        # Use exact price from Excel file (no randomization for verification)
        price = self._mock_prices.get(ticker, 1.0)

        # Generate realistic time string
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")

        return {"price": float(price), "change": 0.0, "time": time_str}

    def _fetch_mock_snapshot(self, tickers: list[str], callback_func, error_callback):
        """Fetch mock market data snapshot (used when blpapi is unavailable or USE_MOCK_DATA=True)."""
        tickers = [t for t in tickers if isinstance(t, str) and t.strip()]
        tickers_key = tuple(sorted(set(tickers)))

        now = time.time()
        # Check cache
        if self._cache_ts is not None and self._cache_tickers == tickers_key:
            age = now - float(self._cache_ts)
            if age <= self._cache_ttl_sec:
                meta = {
                    "request_id": uuid.uuid4().hex[:10],
                    "requested_at": datetime.fromtimestamp(now),
                    "received_at": datetime.fromtimestamp(now),
                    "duration_ms": 0,
                    "from_cache": True,
                    "requested_count": len(tickers_key),
                    "responded_count": len(self._cache_data),
                    "missing": [],
                    "mock": True,
                }
                self._last_meta = dict(meta)
                callback_func(dict(self._cache_data), dict(meta))
                return

        def _worker():
            with self._lock:
                req_id = uuid.uuid4().hex[:10]
                t0 = time.time()
                requested_at = datetime.fromtimestamp(t0)

                # Generate mock data for all tickers
                res = {}
                for ticker in tickers_key:
                    res[ticker] = self._generate_mock_price(ticker)

                # Simulate small network delay
                time.sleep(0.05)

                t1 = time.time()
                received_at = datetime.fromtimestamp(t1)
                duration_ms = int(round((t1 - t0) * 1000))

                meta = {
                    "request_id": req_id,
                    "requested_at": requested_at,
                    "received_at": received_at,
                    "duration_ms": duration_ms,
                    "from_cache": False,
                    "requested_count": len(tickers_key),
                    "responded_count": len(res),
                    "missing": [],
                    "mock": True,
                }
                self._last_meta = dict(meta)

                self._cache_data = dict(res)
                self._cache_ts = time.time()
                self._cache_tickers = tickers_key

                callback_func(res, meta)

        threading.Thread(target=_worker, daemon=True).start()

    def _ensure_ready_sync(self) -> tuple[bool, str | None]:
        if not blpapi:
            return False, "BLPAPI not installed"
        if self._is_ready and self._session and self._service:
            return True, None
        try:
            session_options = blpapi.SessionOptions()
            session_options.setServerHost("localhost")
            session_options.setServerPort(8194)
            session = blpapi.Session(session_options)
            if not session.start():
                return False, "Session Start Failed"
            if not session.openService("//blp/refdata"):
                session.stop()
                return False, "Service Open Failed"
            self._session = session
            self._service = session.getService("//blp/refdata")
            self._is_ready = True
            self._last_error = None
            return True, None
        except Exception as e:
            return False, str(e)

    def fetch_snapshot(self, tickers: list[str], callback_func, error_callback, fields: list[str] | None = None):
        # Use mock data if blpapi is unavailable OR USE_MOCK_DATA is True
        if self._use_mock:
            self._fetch_mock_snapshot(tickers, callback_func, error_callback)
            return

        fields = fields or ["PX_LAST", "CHG_NET_1D", "LAST_UPDATE"]
        tickers = [t for t in tickers if isinstance(t, str) and t.strip()]
        tickers_key = tuple(sorted(set(tickers)))

        now = time.time()
        if self._cache_ts is not None and self._cache_tickers == tickers_key:
            age = now - float(self._cache_ts)
            if age <= self._cache_ttl_sec:
                meta = {
                    "request_id": uuid.uuid4().hex[:10],
                    "requested_at": datetime.fromtimestamp(now),
                    "received_at": datetime.fromtimestamp(now),
                    "duration_ms": 0,
                    "from_cache": True,
                    "requested_count": len(tickers_key),
                    "responded_count": len(self._cache_data),
                    "missing": sorted(list(set(tickers_key) - set(self._cache_data.keys()))),
                }
                self._last_meta = dict(meta)
                callback_func(dict(self._cache_data), dict(meta))
                return

        def _worker():
            with self._lock:
                ok, err = self._ensure_ready_sync()
                if not ok:
                    self._last_error = err
                    error_callback(err or "Unknown Bloomberg error")
                    return

                req_id = uuid.uuid4().hex[:10]
                t0 = time.time()
                requested_at = datetime.fromtimestamp(t0)

                try:
                    req = self._service.createRequest("ReferenceDataRequest")
                    for t in tickers_key:
                        req.getElement("securities").appendValue(t)
                    for f in fields:
                        req.getElement("fields").appendValue(f)

                    self._session.sendRequest(req)

                    res = {}
                    responded = set()

                    while True:
                        ev = self._session.nextEvent(500)
                        if ev.eventType() in (blpapi.Event.RESPONSE, blpapi.Event.PARTIAL_RESPONSE):
                            for msg in ev:
                                if not msg.hasElement("securityData"):
                                    continue
                                arr = msg.getElement("securityData")
                                for i in range(arr.numValues()):
                                    sec = arr.getValueAsElement(i)
                                    t = sec.getElementAsString("security")
                                    if sec.hasElement("securityError"):
                                        continue
                                    if not sec.hasElement("fieldData"):
                                        continue
                                    flds = sec.getElement("fieldData")

                                    price = flds.getElementAsFloat("PX_LAST") if flds.hasElement("PX_LAST") else 0.0
                                    change = flds.getElementAsFloat("CHG_NET_1D") if flds.hasElement("CHG_NET_1D") else 0.0
                                    time_str = flds.getElementAsString("LAST_UPDATE") if flds.hasElement("LAST_UPDATE") else ""

                                    res[t] = {"price": float(price), "change": float(change), "time": str(time_str)}
                                    responded.add(t)

                            if ev.eventType() == blpapi.Event.RESPONSE:
                                break
                        elif ev.eventType() == blpapi.Event.TIMEOUT:
                            continue

                    t1 = time.time()
                    received_at = datetime.fromtimestamp(t1)
                    duration_ms = int(round((t1 - t0) * 1000))

                    missing = sorted(list(set(tickers_key) - responded))

                    meta = {
                        "request_id": req_id,
                        "requested_at": requested_at,
                        "received_at": received_at,
                        "duration_ms": duration_ms,
                        "from_cache": False,
                        "requested_count": len(tickers_key),
                        "responded_count": len(responded),
                        "missing": missing,
                    }
                    self._last_meta = dict(meta)

                    self._cache_data = dict(res)
                    self._cache_ts = time.time()
                    self._cache_tickers = tickers_key

                    callback_func(res, meta)
                except Exception as e:
                    self._last_error = str(e)
                    error_callback(str(e))

        threading.Thread(target=_worker, daemon=True).start()


class MockBloombergEngine:
    """
    Mock Bloomberg engine for testing without a real Bloomberg connection.
    Returns realistic random data for all tickers in MARKET_STRUCTURE.
    """

    def __init__(self, cache_ttl_sec: float = 3.0):
        self._lock = threading.Lock()
        self._is_ready = True
        self._last_error = None
        self._cache_ttl_sec = float(cache_ttl_sec)
        self._cache_data: dict = {}
        self._cache_ts: float | None = None
        self._cache_tickers: tuple[str, ...] | None = None
        self._last_meta: dict = {}

        # Realistic base prices for different ticker types
        self._base_prices = {
            # Spot rates
            "NOK F033 Curncy": 10.85,      # USDNOK around 10.85
            "NKEU F033 Curncy": 11.75,     # EURNOK around 11.75

            # USDNOK forwards (slightly higher than spot due to forward points)
            "NK1W F033 Curncy": 10.852,
            "NK1M F033 Curncy": 10.858,
            "NK2M F033 Curncy": 10.865,
            "NK3M F033 Curncy": 10.875,
            "NK6M F033 Curncy": 10.905,

            # EURNOK forwards
            "NKEU1W F033 Curncy": 11.752,
            "NKEU1M F033 Curncy": 11.758,
            "NKEU2M F033 Curncy": 11.765,
            "NKEU3M F033 Curncy": 11.775,
            "NKEU6M F033 Curncy": 11.805,

            # EUR CM curves (interest rates around 3-4%)
            "EUCM1M SWET Curncy": 3.85,
            "EUCM2M SWET Curncy": 3.78,
            "EUCM3M SWET Curncy": 3.72,
            "EUCM6M SWET Curncy": 3.55,

            # USD CM curves (interest rates around 4-5%)
            "USCM1M SWET Curncy": 4.85,
            "USCM2M SWET Curncy": 4.78,
            "USCM3M SWET Curncy": 4.72,
            "USCM6M SWET Curncy": 4.55,

            # NOK CM curves (NIBOR around 4-5%)
            "NKCM1M SWET Curncy": 4.65,
            "NKCM2M SWET Curncy": 4.58,
            "NKCM3M SWET Curncy": 4.52,
            "NKCM6M SWET Curncy": 4.35,
        }

    def last_meta(self) -> dict:
        """Return metadata from the last fetch operation."""
        return dict(self._last_meta or {})

    def _generate_mock_price(self, ticker: str) -> dict:
        """Generate realistic mock price data for a ticker."""
        import random

        base = self._base_prices.get(ticker, 1.0)
        # Add small random variation (±0.5%)
        variation = base * random.uniform(-0.005, 0.005)
        price = round(base + variation, 4)

        # Random daily change (±0.3%)
        change = round(price * random.uniform(-0.003, 0.003), 4)

        # Generate realistic time string
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")

        return {"price": price, "change": change, "time": time_str}

    def fetch_snapshot(self, tickers: list[str], callback_func, error_callback, fields: list[str] | None = None):
        """
        Fetch mock market data snapshot for given tickers.

        Args:
            tickers: List of Bloomberg ticker strings
            callback_func: Function to call with (data_dict, meta_dict) on success
            error_callback: Function to call with error message on failure
            fields: Optional list of fields (ignored in mock, always returns price/change/time)
        """
        tickers = [t for t in tickers if isinstance(t, str) and t.strip()]
        tickers_key = tuple(sorted(set(tickers)))

        now = time.time()
        # Check cache
        if self._cache_ts is not None and self._cache_tickers == tickers_key:
            age = now - float(self._cache_ts)
            if age <= self._cache_ttl_sec:
                meta = {
                    "request_id": uuid.uuid4().hex[:10],
                    "requested_at": datetime.fromtimestamp(now),
                    "received_at": datetime.fromtimestamp(now),
                    "duration_ms": 0,
                    "from_cache": True,
                    "requested_count": len(tickers_key),
                    "responded_count": len(self._cache_data),
                    "missing": [],
                    "mock": True,
                }
                self._last_meta = dict(meta)
                callback_func(dict(self._cache_data), dict(meta))
                return

        def _worker():
            with self._lock:
                req_id = uuid.uuid4().hex[:10]
                t0 = time.time()
                requested_at = datetime.fromtimestamp(t0)

                # Generate mock data for all tickers
                res = {}
                for ticker in tickers_key:
                    res[ticker] = self._generate_mock_price(ticker)

                # Simulate small network delay
                time.sleep(0.05)

                t1 = time.time()
                received_at = datetime.fromtimestamp(t1)
                duration_ms = int(round((t1 - t0) * 1000))

                meta = {
                    "request_id": req_id,
                    "requested_at": requested_at,
                    "received_at": received_at,
                    "duration_ms": duration_ms,
                    "from_cache": False,
                    "requested_count": len(tickers_key),
                    "responded_count": len(res),
                    "missing": [],
                    "mock": True,
                }
                self._last_meta = dict(meta)

                self._cache_data = dict(res)
                self._cache_ts = time.time()
                self._cache_tickers = tickers_key

                callback_func(res, meta)

        threading.Thread(target=_worker, daemon=True).start()
