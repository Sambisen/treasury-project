#!/usr/bin/env python3
"""
Development Runner - Kör och testa applikationslogik utan CustomTkinter/UI.

Användning på laptop (utan pip-bibliotek):
    python dev_runner.py              # Kör alla tester
    python dev_runner.py --calc       # Testa beräkningar
    python dev_runner.py --mock       # Visa mock-data
    python dev_runner.py --excel      # Testa Excel-läsning (kräver openpyxl)
    python dev_runner.py --weights    # Visa vikter

Detta låter dig utveckla och validera logik på laptopen innan
du kör den riktiga applikationen på stationära datorn.
"""
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Lägg till projektmappen i path
sys.path.insert(0, str(Path(__file__).parent))


def check_dependencies():
    """Kontrollera vilka bibliotek som finns tillgängliga."""
    deps = {}

    # Kärn-dependencies (bör finnas)
    try:
        import pandas
        deps["pandas"] = f"OK (v{pandas.__version__})"
    except ImportError:
        deps["pandas"] = "SAKNAS - kör: pip install pandas"

    try:
        import openpyxl
        deps["openpyxl"] = f"OK (v{openpyxl.__version__})"
    except ImportError:
        deps["openpyxl"] = "SAKNAS - kör: pip install openpyxl"

    # Valfria dependencies
    try:
        import customtkinter
        deps["customtkinter"] = f"OK (v{customtkinter.__version__})"
    except ImportError:
        deps["customtkinter"] = "SAKNAS (behövs endast för UI)"

    try:
        import blpapi
        deps["blpapi"] = "OK"
    except ImportError:
        deps["blpapi"] = "SAKNAS (använder mock-data istället)"

    try:
        import xlwings
        deps["xlwings"] = f"OK (v{xlwings.__version__})"
    except ImportError:
        deps["xlwings"] = "SAKNAS (endast Windows, skrivning till öppna Excel-filer)"

    try:
        import matplotlib
        deps["matplotlib"] = f"OK (v{matplotlib.__version__})"
    except ImportError:
        deps["matplotlib"] = "SAKNAS (behövs endast för charts)"

    return deps


def print_header(title):
    """Skriv ut en snygg rubrik."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def show_mock_data():
    """Visa tillgänglig mock-data."""
    print_header("MOCK MARKET DATA")

    from mock_data import MOCK_MARKET_DATA, MOCK_WEIGHTS

    print("\n[SPOT RATES]")
    for ticker, value in MOCK_MARKET_DATA.items():
        if "F043 Curncy" in ticker and "1" not in ticker and "2" not in ticker and "3" not in ticker and "6" not in ticker:
            print(f"  {ticker}: {value}")

    print("\n[FORWARD POINTS - USDNOK]")
    for tenor in ["1W", "1M", "2M", "3M", "6M"]:
        ticker = f"NK{tenor} F043 Curncy"
        if ticker in MOCK_MARKET_DATA:
            print(f"  {ticker}: {MOCK_MARKET_DATA[ticker]}")

    print("\n[FORWARD POINTS - EURNOK]")
    for tenor in ["1M", "2M", "3M", "6M"]:
        ticker = f"NKEU{tenor} F043 Curncy"
        if ticker in MOCK_MARKET_DATA:
            print(f"  {ticker}: {MOCK_MARKET_DATA[ticker]}")

    print("\n[CM RATES]")
    for ccy in ["EUR", "USD", "NOK"]:
        prefix = f"{ccy[:2].upper()}CM" if ccy != "NOK" else "NKCM"
        for tenor in ["1M", "2M", "3M", "6M"]:
            ticker = f"{prefix}{tenor} SWET Curncy"
            if ticker in MOCK_MARKET_DATA:
                print(f"  {ticker}: {MOCK_MARKET_DATA[ticker]}")

    print("\n[WEIGHTS]")
    for ccy, weight in MOCK_WEIGHTS.items():
        print(f"  {ccy}: {weight:.1%}")


def test_calculations():
    """Testa beräkningslogik med mock-data."""
    print_header("CALCULATION TEST")

    from mock_data import MOCK_MARKET_DATA, MOCK_WEIGHTS
    from calculations import calc_implied_yield

    print("\nTestar NOK implied yield-beräkningar...")
    print("-" * 50)

    tenors = ["1m", "2m", "3m", "6m"]

    for tenor in tenors:
        tenor_upper = tenor.upper()

        # Hämta mock-data
        eur_spot = MOCK_MARKET_DATA.get(f"NKEU F043 Curncy", 11.77)
        usd_spot = MOCK_MARKET_DATA.get(f"NOK F043 Curncy", 10.08)
        eur_fwd = MOCK_MARKET_DATA.get(f"NKEU{tenor_upper} F043 Curncy", eur_spot + 0.01)
        usd_fwd = MOCK_MARKET_DATA.get(f"NK{tenor_upper} F043 Curncy", usd_spot + 0.01)
        eur_cm = MOCK_MARKET_DATA.get(f"EUCM{tenor_upper} SWET Curncy", 2.0)
        usd_cm = MOCK_MARKET_DATA.get(f"USCM{tenor_upper} SWET Curncy", 3.7)

        # Beräkna days (mock)
        days_map = {"1m": 30, "2m": 58, "3m": 90, "6m": 181}
        days = days_map.get(tenor, 30)

        # Beräkna implied yields
        eur_implied = calc_implied_yield(eur_spot, eur_fwd, eur_cm, days)
        usd_implied = calc_implied_yield(usd_spot, usd_fwd, usd_cm, days)

        # Weighted average
        w_eur = MOCK_WEIGHTS.get("EUR", 0.055)
        w_usd = MOCK_WEIGHTS.get("USD", 0.445)
        w_nok = MOCK_WEIGHTS.get("NOK", 0.500)

        # NOK CM rate (proxy for NOK implied)
        nok_cm = MOCK_MARKET_DATA.get(f"NKCM{tenor_upper} SWET Curncy", 4.0)

        weighted_avg = (eur_implied * w_eur) + (usd_implied * w_usd) + (nok_cm * w_nok)

        print(f"\n{tenor.upper()}:")
        print(f"  EUR Implied: {eur_implied:.4f}%  (weight: {w_eur:.1%})")
        print(f"  USD Implied: {usd_implied:.4f}%  (weight: {w_usd:.1%})")
        print(f"  NOK CM:      {nok_cm:.4f}%  (weight: {w_nok:.1%})")
        print(f"  ─────────────────────────────")
        print(f"  Weighted Avg: {weighted_avg:.4f}%")


def test_excel_engine():
    """Testa Excel-läsning (kräver openpyxl)."""
    print_header("EXCEL ENGINE TEST")

    try:
        from engines import ExcelEngine
    except ImportError as e:
        print(f"\n[ERROR] Kan inte importera ExcelEngine: {e}")
        print("Kontrollera att openpyxl är installerat: pip install openpyxl")
        return

    print("\nInitierar ExcelEngine...")
    engine = ExcelEngine()

    # Vänta på bakgrundsladding
    import time
    time.sleep(1)

    print(f"\nDay data ready: {engine._day_data_ready}")
    print(f"Day data error: {engine._day_data_err}")
    print(f"Day data rows: {len(engine.day_data) if not engine.day_data.empty else 0}")

    # Försök ladda recon-data
    print("\nFörsöker ladda NIBOR fixing workbook...")
    success, msg = engine.load_recon_direct()
    print(f"  Status: {'OK' if success else 'FAILED'}")
    print(f"  Message: {msg}")

    if success:
        print(f"\n  Loaded file: {engine.current_filename}")
        print(f"  Year: {engine.current_year_loaded}")
        print(f"  Cells loaded: {len(engine.recon_data)}")


def test_weights():
    """Visa vikter från fil eller mock."""
    print_header("WEIGHTS TEST")

    from mock_data import MOCK_WEIGHTS

    print("\n[MOCK WEIGHTS]")
    total = sum(MOCK_WEIGHTS.values())
    for ccy, weight in MOCK_WEIGHTS.items():
        print(f"  {ccy}: {weight:.1%}")
    print(f"  ─────────────────")
    print(f"  Total: {total:.1%}")

    # Försök ladda från Excel
    try:
        from engines import ExcelEngine
        from config import WEIGHTS_FILE

        print(f"\n[WEIGHTS FILE]")
        print(f"  Path: {WEIGHTS_FILE}")
        print(f"  Exists: {WEIGHTS_FILE.exists()}")

        if WEIGHTS_FILE.exists():
            engine = ExcelEngine()
            if engine.load_weights_file():
                print(f"\n  Parsed weights:")
                for k, v in engine.weights_cells_parsed.items():
                    print(f"    {k}: {v}")
    except Exception as e:
        print(f"\n[WARN] Kunde inte ladda weights-fil: {e}")


def run_all_tests():
    """Kör alla tester."""
    print_header("NIBOR TERMINAL - DEVELOPMENT MODE")
    print(f"\nDatum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Platform: Laptop (utan CustomTkinter)")

    # Visa dependencies
    print_header("DEPENDENCY CHECK")
    deps = check_dependencies()
    for name, status in deps.items():
        symbol = "✓" if "OK" in status else "✗"
        print(f"  {symbol} {name}: {status}")

    # Kör tester
    show_mock_data()
    test_calculations()
    test_weights()


def main():
    parser = argparse.ArgumentParser(description="Nibor Terminal Development Runner")
    parser.add_argument("--calc", action="store_true", help="Testa beräkningar")
    parser.add_argument("--mock", action="store_true", help="Visa mock-data")
    parser.add_argument("--excel", action="store_true", help="Testa Excel-läsning")
    parser.add_argument("--weights", action="store_true", help="Visa vikter")
    parser.add_argument("--deps", action="store_true", help="Kontrollera dependencies")

    args = parser.parse_args()

    # Om inget argument, kör allt
    if not any([args.calc, args.mock, args.excel, args.weights, args.deps]):
        run_all_tests()
    else:
        if args.deps:
            print_header("DEPENDENCY CHECK")
            deps = check_dependencies()
            for name, status in deps.items():
                symbol = "✓" if "OK" in status else "✗"
                print(f"  {symbol} {name}: {status}")
        if args.mock:
            show_mock_data()
        if args.calc:
            test_calculations()
        if args.weights:
            test_weights()
        if args.excel:
            test_excel_engine()


if __name__ == "__main__":
    main()
