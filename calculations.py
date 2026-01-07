"""
Calculation functions for Onyx Terminal.
Separates mathematical logic from GUI code for portability.
"""


def calc_implied_yield(spot: float, pips: float, base_rate: float, days: int) -> float | None:
    """
    Calculate implied NOK yield from FX forward points.

    Args:
        spot: Spot FX rate (e.g., USDNOK or EURNOK)
        pips: Forward points in pips (will be divided by 10000)
        base_rate: Base currency rate (e.g., USD or EUR rate) IN PERCENTAGE FORM (e.g., 3.65 for 3.65%)
        days: Number of days to maturity

    Returns:
        Implied yield as percentage, or None if calculation fails
    """
    print(f"\n[calc_implied_yield] ========== CALCULATION STARTED ==========")
    print(f"[calc_implied_yield] INPUT:")
    print(f"  spot={spot}")
    print(f"  pips={pips}")
    print(f"  base_rate={base_rate}")
    print(f"  days={days}")
    
    if not days or days <= 0:
        print(f"[calc_implied_yield] [ERROR] Invalid days={days}")
        return None
    if spot is None or pips is None or base_rate is None:
        print(f"[calc_implied_yield] [ERROR] None value in inputs")
        return None

    # Check if base_rate is in decimal form (< 1.0) and convert to percentage
    original_base_rate = base_rate
    if base_rate < 1.0 and base_rate > 0:
        base_rate = base_rate * 100.0
        print(f"[calc_implied_yield] [WARNING] Converted base_rate from decimal to percentage: {original_base_rate} -> {base_rate}%")

    fwd_price = spot + (pips / 10000.0)
    print(f"[calc_implied_yield] STEP 1: fwd_price = {spot} + ({pips}/10000) = {fwd_price}")
    
    base_factor = 1.0 + (base_rate * days) / 36000.0
    print(f"[calc_implied_yield] STEP 2: base_factor = 1.0 + ({base_rate}*{days})/36000 = {base_factor}")

    try:
        term_factor = (fwd_price / spot) * base_factor
        print(f"[calc_implied_yield] STEP 3: term_factor = ({fwd_price}/{spot}) * {base_factor} = {term_factor}")
        
        r_nok = (term_factor - 1.0) * (36000.0 / days)
        print(f"[calc_implied_yield] STEP 4: r_nok = ({term_factor}-1.0) * (36000/{days}) = {r_nok}%")
        
        # Sanity check
        if r_nok < -50.0 or r_nok > 100.0:
            print(f"[calc_implied_yield] [ERROR] Result {r_nok}% is out of reasonable range! Likely data format issue.")
        
        print(f"[calc_implied_yield] ========== RESULT: {r_nok}% ==========\n")
        return r_nok  # Already in percent form (e.g., 6.36 for 6.36%)
    except ZeroDivisionError:
        print(f"[calc_implied_yield] [ERROR] Division by zero")
        return None
