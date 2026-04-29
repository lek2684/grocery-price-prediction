"""
scraper.py — Main scraping orchestrator.

Data sources:
  1. Kroger — official Kroger Developer API (requires free API key)
  2. BLS National Average — BLS average prices, approved as substitute (no key needed)

Weekly usage:
    python scraper/scraper.py

Setup for Kroger API (one-time):
    See scraper/retailers/retailer_kroger.py for setup instructions.
    Requires KROGER_CLIENT_ID and KROGER_CLIENT_SECRET env variables.
"""

import csv
import os
from datetime import date
from pathlib import Path
from collections import Counter

RAW_DIR = Path("data/raw/scraped")
RAW_DIR.mkdir(parents=True, exist_ok=True)

FIELDNAMES = [
    "product_name", "brand", "package_size",
    "price", "unit_price", "retailer", "scrape_date", "category",
]


def run_kroger() -> list:
    if not os.environ.get("KROGER_CLIENT_ID"):
        print("Kroger: KROGER_CLIENT_ID not set — skipping.")
        print("  See scraper/retailers/retailer_kroger.py for setup instructions.")
        return []
    try:
        from scraper.retailers.retailer_kroger import scrape_kroger
        print("\n--- Kroger API ---")
        return scrape_kroger()
    except Exception as e:
        print(f"Kroger scrape failed: {e}")
        return []


def run_bls() -> list:
    try:
        from scraper.retailers.retailer_bls import fetch_bls_prices
        print("\n--- BLS National Average Prices ---")
        return fetch_bls_prices()
    except Exception as e:
        print(f"BLS fetch failed: {e}")
        return []


def save(rows: list):
    today = date.today().isoformat()
    out   = RAW_DIR / f"scrape_{today}.csv"
    with open(out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nTotal: {len(rows)} rows saved to {out}")
    counts = Counter(r["retailer"] for r in rows)
    for retailer, count in counts.items():
        print(f"  {retailer}: {count} rows")


def main():
    print(f"Scrape run: {date.today().isoformat()}")
    print("=" * 50)
    all_rows = []
    all_rows.extend(run_kroger())
    all_rows.extend(run_bls())
    if all_rows:
        save(all_rows)
    else:
        print("\nNo rows collected. Set KROGER_CLIENT_ID to enable Kroger scraping.")


if __name__ == "__main__":
    main()
