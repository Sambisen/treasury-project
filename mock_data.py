"""Mock data for development without Bloomberg/Excel."""

_BASE_MOCK_MARKET_DATA = {
    "NOK F033 Curncy": 10.0834,
    "NKEU F033 Curncy": 11.7724,
    "NK1M F033 Curncy": 8.93,
    "NK2M F033 Curncy": 27.41,
    "NK3M F033 Curncy": 54.05,
    "NK6M F033 Curncy": 151.07,
    "NKEU1M F033 Curncy": 184.78,
    "NKEU2M F033 Curncy": 360.51,
    "NKEU3M F033 Curncy": 557.15,
    "NKEU6M F033 Curncy": 1131.19,
    "USCM1M SWET Curncy": 3.65,
    "USCM2M SWET Curncy": 3.68,
    "USCM3M SWET Curncy": 3.70,
    "USCM6M SWET Curncy": 3.76,
    "EUCM1M SWET Curncy": 1.93,
    "EUCM2M SWET Curncy": 1.97,
    "EUCM3M SWET Curncy": 2.01,
    "EUCM6M SWET Curncy": 2.13,
    "NKCM1M SWET Curncy": 3.76,
    "NKCM2M SWET Curncy": 3.86,
    "NKCM3M SWET Curncy": 3.93,
    "NKCM6M SWET Curncy": 4.08,
    "NK1W TPSF Curncy": 7,
    "NK1M TPSF Curncy": 30,
    "NK2M TPSF Curncy": 58,
    "NK3M TPSF Curncy": 90,
    "NK6M TPSF Curncy": 181,
    "EURNOK1W TPSF Curncy": 7,
    "EURNOK1M TPSF Curncy": 30,
    "EURNOK2M TPSF Curncy": 58,
    "EURNOK3M TPSF Curncy": 90,
    "EURNOK6M TPSF Curncy": 181,
}

# Add F043 versions for Dev mode compatibility
MOCK_MARKET_DATA = dict(_BASE_MOCK_MARKET_DATA)
for ticker, value in list(_BASE_MOCK_MARKET_DATA.items()):
    if "F033" in ticker:
        MOCK_MARKET_DATA[ticker.replace("F033", "F043")] = value

MOCK_WEIGHTS = {"USD": 0.445, "EUR": 0.055, "NOK": 0.500}
