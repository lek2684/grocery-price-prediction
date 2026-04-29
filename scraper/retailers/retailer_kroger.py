"""
retailer_kroger.py — Real Kroger data via the official Kroger Developer API.

Setup (one-time, takes 5 minutes):
1. Go to developer.kroger.com
2. Click "Sign In" → create a free account
3. Go to "My Apps" → "Create App"
4. App name: grocery-price-research (or anything)
5. Redirect URI: http://localhost (required but unused for public data)
6. Copy your Client ID and Client Secret
7. Set environment variables on your laptop:
      Windows PowerShell:
        $env:KROGER_CLIENT_ID="your_client_id_here"
        $env:KROGER_CLIENT_SECRET="your_client_secret_here"
      Mac/Linux:
        export KROGER_CLIENT_ID="your_client_id_here"
        export KROGER_CLIENT_SECRET="your_client_secret_here"

Then run:
    python scraper/retailer_kroger.py

This uses client_credentials OAuth (no user login needed) with scope=product.compact.
Rate limit: 10,000 requests/day on free tier — more than enough for weekly scraping.
"""

import os
import base64
import time
import csv
import json
import requests
from datetime import date
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

BASE_URL    = "https://api.kroger.com/v1"
TOKEN_URL   = f"{BASE_URL}/connect/oauth2/token"
PRODUCT_URL = f"{BASE_URL}/products"

RAW_DIR     = Path("data/raw/scraped")
RAW_DIR.mkdir(parents=True, exist_ok=True)

RETAILER_NAME = "kroger"

# Your nearest Kroger location ID — find yours at:
# https://api.kroger.com/v1/locations?filter.zipCode.near=YOUR_ZIP
# Default below is a Chicago-area store. Replace with one near you.
LOCATION_ID = "01400376"   # Kroger, Chicago area — change this!

# The 10 staple products to search for
PRODUCTS = [
    ("milk",              "dairy",       "gallon milk whole"),
    ("eggs",              "dairy",       "eggs large grade a dozen"),
    ("bread",             "bakery",      "white sandwich bread loaf"),
    ("bananas",           "produce",     "bananas"),
    ("chicken breast",    "meat",        "boneless skinless chicken breast"),
    ("ground beef",       "meat",        "ground beef 80/20"),
    ("cereal",            "dry_goods",   "cheerios cereal"),
    ("pasta",             "dry_goods",   "spaghetti pasta 16oz"),
    ("rice",              "dry_goods",   "long grain white rice"),
    ("canned vegetables", "canned_goods","canned green beans"),
]

FIELDNAMES = [
    "product_name", "brand", "package_size",
    "price", "unit_price", "retailer", "scrape_date", "category",
]

# ── Auth ──────────────────────────────────────────────────────────────────────

def get_token() -> str:
    """Get OAuth2 client credentials token. Valid for 30 minutes."""
    client_id     = os.environ.get("KROGER_CLIENT_ID")
    client_secret = os.environ.get("KROGER_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise EnvironmentError(
            "KROGER_CLIENT_ID and KROGER_CLIENT_SECRET environment variables not set.\n"
            "See setup instructions at the top of this file."
        )

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    resp = requests.post(
        TOKEN_URL,
        headers={
            "Content-Type":  "application/x-www-form-urlencoded",
            "Authorization": f"Basic {credentials}",
        },
        data="grant_type=client_credentials&scope=product.compact",
        timeout=15,
    )
    resp.raise_for_status()
    token = resp.json()["access_token"]
    print("Kroger token obtained successfully.")
    return token


# ── Product search ─────────────────────────────────────────────────────────────

def search_product(token: str, query: str, location_id: str) -> list[dict]:
    """Search Kroger API for a product and return raw results."""
    resp = requests.get(
        PRODUCT_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept":        "application/json",
        },
        params={
            "filter.term":       query,
            "filter.locationId": location_id,
            "filter.limit":      5,          # top 5 results per query
        },
        timeout=15,
    )
    if resp.status_code == 401:
        raise RuntimeError("Token expired — call get_token() again.")
    resp.raise_for_status()
    return resp.json().get("data", [])


def parse_product(item: dict, canonical_name: str, category: str) -> dict | None:
    """Extract price and metadata from a Kroger API product response."""
    try:
        # Price: Kroger returns 'items' list with price details
        items = item.get("items", [])
        if not items:
            return None

        price_info = items[0].get("price", {})
        regular    = price_info.get("regular")   # shelf price
        promo      = price_info.get("promo")     # sale price if active

        # Use promo price if available, else regular
        price = promo if promo else regular
        if price is None:
            return None

        # Size info
        size = item.get("size", "")
        brand = item.get("brand", "")
        description = item.get("description", "")

        # Unit price (price per unit of measure)
        unit_price = None
        if size and price:
            try:
                # Very rough unit price — real unit price needs size parsing
                unit_price = round(price / 1, 2)
            except Exception:
                unit_price = None

        return {
            "product_name": canonical_name,
            "brand":        brand,
            "package_size": size,
            "price":        round(float(price), 2),
            "unit_price":   unit_price,
            "retailer":     RETAILER_NAME,
            "scrape_date":  date.today().isoformat(),
            "category":     category,
        }
    except Exception as e:
        print(f"  Parse error: {e}")
        return None


# ── Main scrape loop ──────────────────────────────────────────────────────────

def scrape_kroger(location_id: str = LOCATION_ID) -> list[dict]:
    """Scrape all 10 staple products from Kroger API."""
    token = get_token()
    rows  = []
    today = date.today().isoformat()

    for canonical_name, category, query in PRODUCTS:
        print(f"  Searching: {query}...")
        try:
            results = search_product(token, query, location_id)
            if not results:
                print(f"    No results for '{query}'")
                continue

            # Take the first result with a price
            for item in results:
                row = parse_product(item, canonical_name, category)
                if row:
                    rows.append(row)
                    print(f"    Found: {row['brand']} {row['package_size']} → ${row['price']}")
                    break
            else:
                print(f"    No priced results for '{query}'")

        except Exception as e:
            print(f"    Error searching '{query}': {e}")

        time.sleep(0.5)  # polite delay — 0.5s is fine for official API

    return rows


def save(rows: list[dict]):
    """Save scraped rows to data/raw/scraped/kroger_YYYY-MM-DD.csv"""
    out = RAW_DIR / f"kroger_{date.today().isoformat()}.csv"
    with open(out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved {len(rows)} rows → {out}")
    return out


def main():
    print("=" * 50)
    print("Kroger API Scraper")
    print(f"Location ID: {LOCATION_ID}")
    print(f"Date: {date.today().isoformat()}")
    print("=" * 50)

    rows = scrape_kroger()

    if rows:
        save(rows)
        print("\nSample results:")
        for r in rows:
            print(f"  {r['product_name']:20} ${r['price']:.2f}  ({r['brand']})")
    else:
        print("\nNo rows collected. Check your API credentials and location ID.")


if __name__ == "__main__":
    main()
