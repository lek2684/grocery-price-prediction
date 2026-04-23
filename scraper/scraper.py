"""
scraper.py — Main scraping orchestrator.

Calls retailer-specific modules and saves output CSVs to data/raw/scraped/.
Uses polite crawl delays and user-agent rotation to reduce blocking risk.
"""

import time
import random
import csv
from datetime import date
from pathlib import Path

from scraper.retailers import retailer_a, retailer_b
from scraper.utils import get_headers, rate_limit

RAW_DIR = Path("data/raw/scraped")
RAW_DIR.mkdir(parents=True, exist_ok=True)

TARGET_PRODUCTS = [
    "milk",
    "eggs",
    "bread",
    "bananas",
    "chicken breast",
    "ground beef",
    "cereal",
    "pasta",
    "rice",
    "canned vegetables",
]

RETAILERS = {
    "retailer_a": retailer_a,
    "retailer_b": retailer_b,
}

FIELDNAMES = [
    "product_name", "brand", "package_size",
    "price", "unit_price", "retailer", "scrape_date", "category",
]


def scrape_all() -> list[dict]:
    rows = []
    today = date.today().isoformat()

    for retailer_name, module in RETAILERS.items():
        print(f"\nScraping {retailer_name}...")
        for product in TARGET_PRODUCTS:
            try:
                results = module.search(product, headers=get_headers())
                for r in results:
                    r["retailer"]    = retailer_name
                    r["scrape_date"] = today
                    rows.append(r)
                rate_limit()
            except Exception as e:
                print(f"  Error scraping {product} from {retailer_name}: {e}")

    return rows


def save(rows: list[dict]):
    out = RAW_DIR / f"scrape_{date.today().isoformat()}.csv"
    with open(out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved {len(rows)} rows to {out}")


def main():
    rows = scrape_all()
    if rows:
        save(rows)
    else:
        print("No rows collected — check scraper modules and network access.")


if __name__ == "__main__":
    main()
