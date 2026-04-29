"""
retailer_bls.py — BLS Average Prices as second "retailer" data source.

The instructor approved BLS average prices as a substitute for scraped
prices with a clear asterisk — recorded as a distinct data source, not
mixed into the scraped panel.

BLS publishes monthly average retail prices for ~70 food items, collected
from actual stores nationwide. This is real price data, just aggregated.

Series used (national average prices):
    APU0000708111 — eggs, grade A large, per dozen
    APU0000709112 — milk, fresh, whole, fortified, per gallon
    APU0000702111 — bread, white pan, per lb
    APU0000711211 — bananas, per lb
    APU0000706111 — chicken breast, boneless, per lb
    APU0000703112 — ground beef, 100% beef, per lb
    APU0000712311 — rice, white, long grain, per lb
    APU0000701312 — flour, white, all purpose, per lb (proxy for pasta/cereal)

Docs: https://www.bls.gov/charts/cpi/avg-price-data.htm
"""

import requests
import pandas as pd
import csv
from datetime import date, datetime
from pathlib import Path

RAW_DIR       = Path("data/raw/scraped")
RAW_DIR.mkdir(parents=True, exist_ok=True)
RETAILER_NAME = "bls_national_avg"

BLS_API = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# Map BLS series → canonical product name + category
BLS_SERIES = {
    "APU0000708111": ("eggs",              "dairy",       "per dozen"),
    "APU0000709112": ("milk",              "dairy",       "per gallon"),
    "APU0000702111": ("bread",             "bakery",      "per lb"),
    "APU0000711211": ("bananas",           "produce",     "per lb"),
    "APU0000706111": ("chicken breast",    "meat",        "per lb"),
    "APU0000703112": ("ground beef",       "meat",        "per lb"),
    "APU0000712311": ("rice",              "dry_goods",   "per lb"),
    "APU0000701312": ("pasta",             "dry_goods",   "per lb"),
}

FIELDNAMES = [
    "product_name", "brand", "package_size",
    "price", "unit_price", "retailer", "scrape_date", "category",
]


def fetch_bls_prices(year: int = None) -> list[dict]:
    """Fetch latest BLS average prices and format as retailer rows."""
    if year is None:
        year = datetime.now().year

    payload = {
        "seriesid":  list(BLS_SERIES.keys()),
        "startyear": str(year - 1),
        "endyear":   str(year),
    }

    resp = requests.post(BLS_API, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "REQUEST_SUCCEEDED":
        print(f"BLS API warning: {data.get('message', 'unknown error')}")

    today = date.today().isoformat()
    rows  = []

    for series in data.get("Results", {}).get("series", []):
        sid = series["seriesID"]
        if sid not in BLS_SERIES:
            continue

        canonical_name, category, unit = BLS_SERIES[sid]
        obs_list = series.get("data", [])
        if not obs_list:
            continue

        # BLS returns newest first — take the most recent monthly value
        latest = obs_list[0]
        try:
            price = float(latest["value"])
        except (ValueError, KeyError):
            continue

        period = latest.get("period", "M??")
        period_label = f"{latest.get('year','?')}-{period[1:]}"

        rows.append({
            "product_name": canonical_name,
            "brand":        "BLS National Average",
            "package_size": f"{unit} ({period_label})",
            "price":        round(price, 4),
            "unit_price":   round(price, 4),
            "retailer":     RETAILER_NAME,
            "scrape_date":  today,
            "category":     category,
        })

    return rows


def save(rows: list[dict]) -> Path:
    out = RAW_DIR / f"bls_avg_{date.today().isoformat()}.csv"
    with open(out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} BLS average price rows → {out}")
    return out


def main():
    print("Fetching BLS national average prices...")
    rows = fetch_bls_prices()
    if rows:
        save(rows)
        print("\nBLS prices:")
        for r in rows:
            print(f"  {r['product_name']:20} ${r['price']:.4f}  ({r['package_size']})")
    else:
        print("No rows returned. Check network connection.")


if __name__ == "__main__":
    main()
