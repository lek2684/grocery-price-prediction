"""
utils.py — Shared scraper helpers: rate limiting, user-agent rotation, parsing.
"""

import time
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]


def get_headers() -> dict:
    """Return a randomized browser-like header set."""
    return {
        "User-Agent":      random.choice(USER_AGENTS),
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT":             "1",
        "Connection":      "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def rate_limit(min_sec: float = 2.0, max_sec: float = 5.0):
    """Polite crawl delay between requests."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def parse_price(raw: str) -> float | None:
    """Extract a float price from a messy string like '$3.49' or '3.49/lb'."""
    import re
    match = re.search(r"[\d]+\.[\d]{2}", raw.replace(",", ""))
    if match:
        return float(match.group())
    return None


def parse_unit_price(raw: str) -> float | None:
    """Extract unit price from strings like '$0.25/oz'."""
    import re
    match = re.search(r"[\d]+\.[\d]+", raw.replace(",", ""))
    if match:
        return float(match.group())
    return None
