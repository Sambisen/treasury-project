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
    if not days or days <= 0:
        return None
    if spot is None or pips is None or base_rate is None:
        return None

    # Check if base_rate is in decimal form (< 1.0) and convert to percentage
    if base_rate < 1.0 and base_rate > 0:
        base_rate = base_rate * 100.0

    fwd_price = spot + (pips / 10000.0)
    base_factor = 1.0 + (base_rate * days) / 36000.0

    try:
        term_factor = (fwd_price / spot) * base_factor
        r_nok = (term_factor - 1.0) * (36000.0 / days)
        return r_nok  # Already in percent form (e.g., 6.36 for 6.36%)
    except ZeroDivisionError:
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
    print(f"\n[calc_funding_rate] CALCULATION:")
    print(f"  eur={eur_implied}, usd={usd_implied}, nok={nok_cm}")
    
    if None in [eur_implied, usd_implied, nok_cm]:
        print(f"[calc_funding_rate] ERROR: None value")
        return None
    
    if not all(k in weights for k in ['EUR', 'USD', 'NOK']):
        print(f"[calc_funding_rate] ERROR: Missing weights")
        return None
    
    try:
        funding_rate = (
            eur_implied * weights['EUR'] +
            usd_implied * weights['USD'] +
            nok_cm * weights['NOK']
        )
        print(f"  Result: {funding_rate:.4f}%")
        return funding_rate
    except Exception as e:
        print(f"[calc_funding_rate] ERROR: {e}")
        return None
