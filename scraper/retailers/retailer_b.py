"""
retailer_b.py — Walmart scraper via Open Food Facts + Walmart Open API.

Walmart's product search API is available through RapidAPI (free tier):
  https://rapidapi.com/apidojo/api/walmart

Sign up for a free RapidAPI key, subscribe to the Walmart API (free tier),
then set:
    RAPIDAPI_KEY=your_rapidapi_key

Free tier: 500 requests/month — enough for weekly scraping of 10 products.
"""

import os
import requests
from scraper.utils import parse_price

RETAILER_NAME = "walmart"
SEARCH_URL    = "https://walmart.p.rapidapi.com/v1/search"

CATEGORY_MAP = {
    "milk": "dairy", "eggs": "dairy", "bread": "bakery",
    "bananas": "produce", "chicken breast": "meat", "ground beef": "meat",
    "cereal": "dry_goods", "pasta": "dry_goods", "rice": "dry_goods",
    "canned vegetables": "canned_goods",
}


def search(product: str, headers: dict) -> list[dict]:
    results = []
    api_key = os.environ.get("RAPIDAPI_KEY")
    if not api_key:
        print("  [walmart] Set RAPIDAPI_KEY environment variable.")
        print("  Get a free key at: https://rapidapi.com/apidojo/api/walmart")
        return results

    try:
        resp = requests.get(
            SEARCH_URL,
            headers={
                "X-RapidAPI-Key":  api_key,
                "X-RapidAPI-Host": "walmart.p.rapidapi.com",
            },
            params={"query": product, "page": "1"},
            timeout=15,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])

        for item in items[:5]:
            price = item.get("price") or item.get("salePrice")
            if price:
                results.append({
                    "product_name": product,
                    "brand":        item.get("brand", ""),
                    "package_size": item.get("size", ""),
                    "price":        float(price),
                    "unit_price":   None,
                    "category":     CATEGORY_MAP.get(product, "other"),
                })

    except Exception as e:
        print(f"  [walmart] Error on '{product}': {e}")

    return results
