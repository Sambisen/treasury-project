"""
Calculation functions for Onyx Terminal.
Separates mathematical logic from GUI code for portability.
"""
from config import get_logger

log = get_logger("calculations")


def calc_implied_yield(spot: float, pips: float, base_rate: float, days: int) -> float | None:
    """
    Calculate implied NOK yield from FX forward points.
    
    EXACT Excel formula from user:
    =((($P$3+(R7/10000))*(1+(Q7*P7/36000)))-($P$3))/(($P$3*Q7)/36000)
    
    Where:
    - P3 = Spot (e.g., 9.225)
    - R7 = Pips (e.g., -437)
    - Q7 = Days (e.g., 90)
    - P7 = CM rate (e.g., 3.70)
    
    Example verification:
    Spot=9.225, Pips=-437, Days=90, CM_Rate=3.70 → Result=1.787622%

    Args:
        spot: Spot FX rate (e.g., USDNOK or EURNOK)
        pips: Forward points in pips
        base_rate: Base currency rate (USD or EUR CM rate) IN PERCENTAGE FORM (e.g., 3.70 for 3.70%)
        days: Number of days to maturity

    Returns:
        Implied yield as percentage, or None if calculation fails
    """
    log.debug(f"\n[calc_implied_yield] ========== CALCULATION STARTED ==========")
    log.debug(f"[calc_implied_yield] INPUT:")
    log.debug(f"  spot={spot}")
    log.debug(f"  pips={pips}")
    log.debug(f"  base_rate={base_rate}")
    log.debug(f"  days={days}")
    
    if not days or days <= 0:
        log.debug(f"[calc_implied_yield] [ERROR] Invalid days={days}")
        return None
    if spot is None or pips is None or base_rate is None:
        log.debug(f"[calc_implied_yield] [ERROR] None value in inputs")
        return None
    if spot <= 0:
        log.debug(f"[calc_implied_yield] [ERROR] Invalid spot={spot} (must be > 0)")
        return None

    try:
        # EXACT EXCEL FORMULA:
        # =((($P$3+(R7/10000))*(1+(Q7*P7/36000)))-($P$3))/(($P$3*Q7)/36000)
        
        # Step 1: Forward price = Spot + (Pips/10000)
        fwd = spot + (pips / 10000.0)
        log.debug(f"[calc_implied_yield] STEP 1: fwd = {spot} + ({pips}/10000) = {fwd}")
        
        # Step 2: Base factor = 1 + (Days * CM_Rate / 36000)
        base_factor = 1 + (days * base_rate / 36000.0)
        log.debug(f"[calc_implied_yield] STEP 2: base_factor = 1 + ({days}*{base_rate}/36000) = {base_factor}")
        
        # Step 3: Numerator = (Fwd * Base_factor) - Spot
        numerator = (fwd * base_factor) - spot
        log.debug(f"[calc_implied_yield] STEP 3: numerator = ({fwd}*{base_factor}) - {spot} = {numerator}")
        
        # Step 4: Denominator = (Spot * Days) / 36000
        denominator = (spot * days) / 36000.0
        log.debug(f"[calc_implied_yield] STEP 4: denominator = ({spot}*{days})/36000 = {denominator}")
        
        # Step 5: Implied rate = Numerator / Denominator
        r_nok = numerator / denominator
        log.debug(f"[calc_implied_yield] STEP 5: r_nok = {numerator}/{denominator} = {r_nok}%")
        
        # Sanity check
        if abs(r_nok) > 20.0:
            log.debug(f"[calc_implied_yield] [WARNING] Result {r_nok}% is outside normal range! Check input data.")
        
        log.debug(f"[calc_implied_yield] ========== RESULT: {r_nok}% ==========\n")
        return r_nok  # Already in percent form (e.g., 1.787622 for 1.787622%)
    except ZeroDivisionError:
        log.debug(f"[calc_implied_yield] [ERROR] Division by zero")
        return None
    except Exception as e:
        log.debug(f"[calc_implied_yield] [ERROR] Exception: {e}")
        return None


def calc_funding_rate(eur_implied: float, usd_implied: float, nok_cm: float, 
                     weights: dict) -> float | None:
    """
    Calculate weighted funding rate.
    
    Formula: (EUR_IMPLIED × EUR_WEIGHT) + (USD_IMPLIED × USD_WEIGHT) + (NOK_CM × NOK_WEIGHT)
    
    Args:
        eur_implied: EUR implied NOK rate in percentage form
        usd_implied: USD implied NOK rate in percentage form
        nok_cm: NOK CM rate in percentage form
        weights: Dictionary with keys 'EUR', 'USD', 'NOK' containing weight values (0-1)
    
    Returns:
        Weighted funding rate as percentage, or None if calculation fails
    """
    log.debug(f"\n[calc_funding_rate] CALCULATION:")
    log.debug(f"  eur={eur_implied}, usd={usd_implied}, nok={nok_cm}")
    
    if None in [eur_implied, usd_implied, nok_cm]:
        log.debug(f"[calc_funding_rate] ERROR: None value")
        return None
    
    if not all(k in weights for k in ['EUR', 'USD', 'NOK']):
        log.debug(f"[calc_funding_rate] ERROR: Missing weights")
        return None
    
    try:
        funding_rate = (
            eur_implied * weights['EUR'] +
            usd_implied * weights['USD'] +
            nok_cm * weights['NOK']
        )
        log.debug(f"  Result: {funding_rate:.4f}%")
        return funding_rate
    except Exception as e:
        log.debug(f"[calc_funding_rate] ERROR: {e}")
        return None
