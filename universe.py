"""Scan universe: DJI30 / NDX100 / SP500 indices and constituent stocks."""

from __future__ import annotations

from sp500_constituents import SP500_STOCKS

INDICES: list[tuple[str, str, str, str]] = [
    ("index", "^DJI", "DJI30", "道瓊 30"),
    ("index", "^NDX", "NDX100", "納指 100"),
    ("index", "^GSPC", "SP500", "標普 500"),
]

# Current DJIA constituents (Yahoo tickers)
DJI30_STOCKS: list[tuple[str, str]] = [
    ("AAPL", "Apple"),
    ("AMGN", "Amgen"),
    ("AMZN", "Amazon"),
    ("AXP", "American Express"),
    ("BA", "Boeing"),
    ("CAT", "Caterpillar"),
    ("CRM", "Salesforce"),
    ("CSCO", "Cisco"),
    ("CVX", "Chevron"),
    ("DIS", "Disney"),
    ("GS", "Goldman Sachs"),
    ("HD", "Home Depot"),
    ("HON", "Honeywell"),
    ("IBM", "IBM"),
    ("JNJ", "Johnson & Johnson"),
    ("JPM", "JPMorgan"),
    ("KO", "Coca-Cola"),
    ("MCD", "McDonald's"),
    ("MMM", "3M"),
    ("MRK", "Merck"),
    ("MSFT", "Microsoft"),
    ("NKE", "Nike"),
    ("NVDA", "NVIDIA"),
    ("PG", "Procter & Gamble"),
    ("SHW", "Sherwin-Williams"),
    ("TRV", "Travelers"),
    ("UNH", "UnitedHealth"),
    ("V", "Visa"),
    ("VZ", "Verizon"),
    ("WMT", "Walmart"),
]

# NASDAQ-100 constituents (source: slickcharts.com/nasdaq100, 102 tickers)
NDX100_STOCKS: list[tuple[str, str]] = [
    ("NVDA", "NVIDIA"),
    ("AAPL", "Apple"),
    ("MSFT", "Microsoft"),
    ("AMZN", "Amazon"),
    ("GOOGL", "Alphabet A"),
    ("GOOG", "Alphabet C"),
    ("AVGO", "Broadcom"),
    ("SPCX", "SpaceX (SPCX)"),
    ("META", "Meta"),
    ("TSLA", "Tesla"),
    ("MU", "Micron"),
    ("WMT", "Walmart"),
    ("AMD", "AMD"),
    ("ASML", "ASML"),
    ("INTC", "Intel"),
    ("CSCO", "Cisco"),
    ("AMAT", "Applied Materials"),
    ("COST", "Costco"),
    ("LRCX", "Lam Research"),
    ("PLTR", "Palantir"),
    ("PANW", "Palo Alto Networks"),
    ("NFLX", "Netflix"),
    ("ARM", "Arm Holdings"),
    ("KLAC", "KLA"),
    ("TXN", "Texas Instruments"),
    ("CRWD", "CrowdStrike"),
    ("AMGN", "Amgen"),
    ("LIN", "Linde"),
    ("SNDK", "Sandisk"),
    ("STX", "Seagate"),
    ("MRVL", "Marvell"),
    ("SHOP", "Shopify"),
    ("TMUS", "T-Mobile"),
    ("ADI", "Analog Devices"),
    ("PEP", "PepsiCo"),
    ("QCOM", "Qualcomm"),
    ("GILD", "Gilead"),
    ("WDC", "Western Digital"),
    ("BKNG", "Booking"),
    ("ISRG", "Intuitive Surgical"),
    ("VRTX", "Vertex"),
    ("PDD", "PDD Holdings"),
    ("SBUX", "Starbucks"),
    ("FTNT", "Fortinet"),
    ("ABNB", "Airbnb"),
    ("ADP", "ADP"),
    ("APP", "AppLovin"),
    ("ADBE", "Adobe"),
    ("CEG", "Constellation Energy"),
    ("MELI", "MercadoLibre"),
    ("DASH", "DoorDash"),
    ("CSX", "CSX"),
    ("MAR", "Marriott"),
    ("INTU", "Intuit"),
    ("CDNS", "Cadence"),
    ("CMCSA", "Comcast"),
    ("DDOG", "Datadog"),
    ("MNST", "Monster Beverage"),
    ("REGN", "Regeneron"),
    ("CTAS", "Cintas"),
    ("ROST", "Ross Stores"),
    ("SNPS", "Synopsys"),
    ("MDLZ", "Mondelez"),
    ("ORLY", "O'Reilly Auto"),
    ("HON", "Honeywell"),
    ("LITE", "Lumentum"),
    ("MPWR", "Monolithic Power"),
    ("WBD", "Warner Bros Discovery"),
    ("PCAR", "Paccar"),
    ("AEP", "American Electric Power"),
    ("BKR", "Baker Hughes"),
    ("TER", "Teradyne"),
    ("FAST", "Fastenal"),
    ("NXPI", "NXP Semiconductors"),
    ("NBIS", "Nebius Group"),
    ("CRWV", "CoreWeave"),
    ("ALAB", "Astera Labs"),
    ("FANG", "Diamondback Energy"),
    ("HONA", "Honeywell Aerospace"),
    ("ADSK", "Autodesk"),
    ("AXON", "Axon Enterprise"),
    ("RKLB", "Rocket Lab"),
    ("PYPL", "PayPal"),
    ("XEL", "Xcel Energy"),
    ("FER", "Ferrovial"),
    ("CCEP", "Coca-Cola Europacific"),
    ("EXC", "Exelon"),
    ("TTWO", "Take-Two"),
    ("IDXX", "Idexx Labs"),
    ("ODFL", "Old Dominion Freight"),
    ("TRI", "Thomson Reuters"),
    ("MCHP", "Microchip"),
    ("WDAY", "Workday"),
    ("PAYX", "Paychex"),
    ("KDP", "Keurig Dr Pepper"),
    ("ROP", "Roper Technologies"),
    ("MSTR", "Strategy (MSTR)"),
    ("DXCM", "DexCom"),
    ("GEHC", "GE HealthCare"),
    ("ALNY", "Alnylam"),
    ("KHC", "Kraft Heinz"),
    ("CPRT", "Copart"),
]

GROUP_ORDER = {"index": 0, "dji": 1, "ndx": 2, "sp500": 3}


def build_scan_jobs() -> list[dict[str, str]]:
    """Return deduplicated scan jobs; DJI > NDX > SP500 when a ticker is in multiple lists."""
    jobs: list[dict[str, str]] = []
    seen: set[str] = set()

    for group, yahoo, display, name in INDICES:
        jobs.append(
            {
                "group": group,
                "yahoo": yahoo,
                "symbol": display,
                "name": name,
            }
        )

    dji_set = {t for t, _ in DJI30_STOCKS}
    ndx_names = dict(NDX100_STOCKS)
    dji_names = dict(DJI30_STOCKS)
    sp500_names = dict(SP500_STOCKS)

    for ticker, name in DJI30_STOCKS:
        if ticker in seen:
            continue
        seen.add(ticker)
        jobs.append(
            {
                "group": "dji",
                "yahoo": ticker,
                "symbol": ticker,
                "name": name,
            }
        )

    for ticker, name in NDX100_STOCKS:
        if ticker in seen:
            continue
        seen.add(ticker)
        jobs.append(
            {
                "group": "ndx",
                "yahoo": ticker,
                "symbol": ticker,
                "name": ndx_names.get(ticker, name),
            }
        )

    for ticker, name in SP500_STOCKS:
        if ticker in seen:
            continue
        seen.add(ticker)
        jobs.append(
            {
                "group": "sp500",
                "yahoo": ticker,
                "symbol": ticker,
                "name": sp500_names.get(ticker, name),
            }
        )

    for job in jobs:
        y = job.get("yahoo", "")
        if job["group"] == "dji" and y in ndx_names:
            job["also_ndx"] = "1"
        elif job["group"] == "ndx" and y in dji_set:
            job["also_dji"] = "1"
        if job["group"] in ("dji", "ndx") and y in sp500_names:
            job["also_sp500"] = "1"
        elif job["group"] == "sp500" and (y in dji_set or y in ndx_names):
            if y in dji_set:
                job["also_dji"] = "1"
            if y in ndx_names:
                job["also_ndx"] = "1"

    return jobs


def group_label(group: str) -> str:
    return {
        "index": "指數",
        "dji": "DJI30",
        "ndx": "NDX100",
        "sp500": "SP500",
    }.get(group, group)
