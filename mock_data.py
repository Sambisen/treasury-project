"""
Mock data for development/testing without Bloomberg or Excel files.
Used when DEVELOPMENT_MODE = True in config.py
"""

MOCK_MARKET_DATA = {
    # Spot rates
    "NOK F033 Curncy": 10.0834,
    "NKEU F033 Curncy": 11.7724,

    # USDNOK forwards (pips)
    "NK1M F033 Curncy": 8.93,
    "NK2M F033 Curncy": 27.41,
    "NK3M F033 Curncy": 54.05,
    "NK6M F033 Curncy": 151.07,

    # EURNOK forwards (pips)
    "NKEU1M F033 Curncy": 184.78,
    "NKEU2M F033 Curncy": 360.51,
    "NKEU3M F033 Curncy": 557.15,
    "NKEU6M F033 Curncy": 1131.19,

    # USD CM rates
    "USCM1M SWET Curncy": 3.65,
    "USCM2M SWET Curncy": 3.68,
    "USCM3M SWET Curncy": 3.70,
    "USCM6M SWET Curncy": 3.76,

    # EUR CM rates
    "EUCM1M SWET Curncy": 1.93,
    "EUCM2M SWET Curncy": 1.97,
    "EUCM3M SWET Curncy": 2.01,
    "EUCM6M SWET Curncy": 2.13,

    # NOK CM rates
    "NKCM1M SWET Curncy": 3.76,
    "NKCM2M SWET Curncy": 3.86,
    "NKCM3M SWET Curncy": 3.93,
    "NKCM6M SWET Curncy": 4.08,

    # Days to maturity (TPSF Curncy)
    "NK1M TPSF Curncy": 30,
    "NK2M TPSF Curncy": 58,
    "NK3M TPSF Curncy": 90,
    "NK6M TPSF Curncy": 181,
    "EURNOK1M TPSF Curncy": 30,
    "EURNOK2M TPSF Curncy": 58,
    "EURNOK3M TPSF Curncy": 90,
    "EURNOK6M TPSF Curncy": 181,
}

# Default weights for funding rate calculation
MOCK_WEIGHTS = {"USD": 0.45, "EUR": 0.05, "NOK": 0.50}
