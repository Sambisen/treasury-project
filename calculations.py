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
        base_rate: Base currency rate (e.g., USD or EUR rate)
        days: Number of days to maturity

    Returns:
        Implied yield as percentage, or None if calculation fails
    """
    if not days or days <= 0:
        return None
    if spot is None or pips is None or base_rate is None:
        return None

    fwd_price = spot + (pips / 10000.0)
    base_factor = 1.0 + (base_rate * days) / 36000.0

    try:
        term_factor = (fwd_price / spot) * base_factor
        r_nok = (term_factor - 1.0) * (36000.0 / days)
        return r_nok  # Already in percent form (e.g., 6.36 for 6.36%)
    except ZeroDivisionError:
        return None
