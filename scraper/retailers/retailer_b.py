"""
retailer_b.py — Scraping logic for Retailer B.
Same interface as retailer_a.py — implement search() below.
"""

from scraper.utils import parse_price, parse_unit_price

RETAILER_NAME = "retailer_b"
BASE_URL = "https://www.example-retailer-b.com"  # Replace with actual URL

CATEGORY_MAP = {
    "milk":              "dairy",
    "eggs":              "dairy",
    "bread":             "bakery",
    "bananas":           "produce",
    "chicken breast":    "meat",
    "ground beef":       "meat",
    "cereal":            "dry_goods",
    "pasta":             "dry_goods",
    "rice":              "dry_goods",
    "canned vegetables": "canned_goods",
}


def search(product: str, headers: dict) -> list[dict]:
    """
    Search for a product and return a list of result dicts.
    Implement retailer-specific logic here.
    """
    results = []
    # TODO: implement
    return results
