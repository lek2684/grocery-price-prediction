"""
retailer_a.py — Kroger API scraper.

Uses the official Kroger Developer API (free tier).
Sign up at: https://developer.kroger.com
- Create an app to get a Client ID and Client Secret
- Set environment variables:
    KROGER_CLIENT_ID=your_client_id
    KROGER_CLIENT_SECRET=your_client_secret
"""

import os
import time
import requests
from scraper.utils import parse_price, parse_unit_price

RETAILER_NAME    = "kroger"
TOKEN_URL        = "https://api.kroger.com/v1/connect/oauth2/token"
PRODUCTS_URL     = "https://api.kroger.com/v1/products"
DEFAULT_LOCATION = "01400943"  # Chicago-area Kroger store

CATEGORY_MAP = {
    "milk": "dairy", "eggs": "dairy", "bread": "bakery",
    "bananas": "produce", "chicken breast": "meat", "ground beef": "meat",
    "cereal": "dry_goods", "pasta": "dry_goods", "rice": "dry_goods",
    "canned vegetables": "canned_goods",
}

_token_cache = {"token": None, "expires_at": 0}


def get_token() -> str:
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["token"]
    client_id     = os.environ.get("KROGER_CLIENT_ID")
    client_secret = os.environ.get("KROGER_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise EnvironmentError(
            "Set KROGER_CLIENT_ID and KROGER_CLIENT_SECRET.\n"
            "Free credentials at: https://developer.kroger.com"
        )
    resp = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials", "scope": "product.compact"},
        auth=(client_id, client_secret),
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"]      = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 1800)
    return _token_cache["token"]


def search(product: str, headers: dict) -> list[dict]:
    results = []
    try:
        token = get_token()
        resp  = requests.get(
            PRODUCTS_URL,
            headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
            params={"filter.term": product, "filter.locationId": DEFAULT_LOCATION, "filter.limit": 5},
            timeout=15,
        )
        resp.raise_for_status()
        for item in resp.json().get("data", []):
            for sku in item.get("items", []):
                price_info = sku.get("price", {})
                price = price_info.get("regular") or price_info.get("promo")
                unit  = price_info.get("regularPerUnitEstimate")
                if price:
                    results.append({
                        "product_name": product,
                        "brand":        item.get("brand", ""),
                        "package_size": sku.get("size", ""),
                        "price":        float(price),
                        "unit_price":   float(unit) if unit else None,
                        "category":     CATEGORY_MAP.get(product, "other"),
                    })
                break
    except EnvironmentError as e:
        print(f"  [kroger] Config error: {e}")
    except Exception as e:
        print(f"  [kroger] Error on '{product}': {e}")
    return results
