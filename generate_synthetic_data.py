"""
generate_synthetic_data.py — Generate synthetic grocery price panel data
that mimics the real scraped + BLS structure.

Run this ONCE to bootstrap the pipeline before real scraped data is available.
Replace with real data in Week 3.

Usage:
    python generate_synthetic_data.py
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date, timedelta

np.random.seed(42)

RAW_SCRAPED = Path("data/raw/scraped")
RAW_BLS     = Path("data/raw/bls")
RAW_SCRAPED.mkdir(parents=True, exist_ok=True)
RAW_BLS.mkdir(parents=True, exist_ok=True)

# --- Config ---
PRODUCTS = [
    ("milk",              "dairy",      3.89),
    ("eggs",              "dairy",      2.49),
    ("bread",             "bakery",     3.29),
    ("bananas",           "produce",    0.59),
    ("chicken breast",    "meat",       5.49),
    ("ground beef",       "meat",       6.99),
    ("cereal",            "dry_goods",  4.79),
    ("pasta",             "dry_goods",  1.49),
    ("rice",              "dry_goods",  2.29),
    ("canned vegetables", "canned_goods", 0.99),
]

RETAILERS   = ["retailer_a", "retailer_b"]
START_DATE  = date(2024, 1, 7)   # first Sunday
N_WEEKS     = 52                  # one full year of weekly data


def generate_scraped() -> pd.DataFrame:
    rows = []
    week_starts = [START_DATE + timedelta(weeks=w) for w in range(N_WEEKS)]

    for product, category, base_price in PRODUCTS:
        for retailer in RETAILERS:
            # Retailer B is slightly cheaper on average
            retailer_offset = -0.15 if retailer == "retailer_b" else 0.0
            price = base_price + retailer_offset

            for week_start in week_starts:
                # Gradual upward trend + weekly noise + occasional spike
                week_idx = week_starts.index(week_start)
                trend    = 0.003 * week_idx
                seasonal = 0.05 * np.sin(2 * np.pi * week_idx / 52)
                noise    = np.random.normal(0, 0.04)
                spike    = np.random.choice([0, 0.25], p=[0.95, 0.05])

                observed_price = round(max(0.10, price + trend + seasonal + noise + spike), 2)
                unit_price     = round(observed_price / np.random.uniform(0.8, 1.5), 2)

                rows.append({
                    "product_name": product,
                    "brand":        "Store Brand",
                    "package_size": "standard",
                    "price":        observed_price,
                    "unit_price":   unit_price,
                    "retailer":     retailer,
                    "scrape_date":  week_start.isoformat(),
                    "category":     category,
                })

    return pd.DataFrame(rows)


def generate_bls() -> pd.DataFrame:
    """Generate synthetic BLS CPI series aligned to monthly dates."""
    months = pd.date_range("2024-01-01", periods=14, freq="MS")
    rows = []
    base_values = {
        "bls_cpi_food_at_home":   312.0,
        "bls_cpi_meats_poultry":  285.0,
        "bls_cpi_dairy":          290.0,
        "bls_cpi_cereals_bakery": 320.0,
        "bls_cpi_fruits_veg":     295.0,
        "bls_ppi_food_mfg":       275.0,
        "bls_avg_eggs_dozen":     2.45,
        "bls_avg_milk_gallon":    3.85,
        "bls_avg_bread_loaf":     3.25,
    }
    for i, month in enumerate(months):
        row = {"date": month.date().isoformat(), "month_start": month.date().isoformat()}
        for series, base in base_values.items():
            trend = 0.002 * i
            noise = np.random.normal(0, 0.005)
            row[series] = round(base * (1 + trend + noise), 4)
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    print("Generating synthetic scraped price data...")
    scraped = generate_scraped()
    out = RAW_SCRAPED / "synthetic_scrape_2024.csv"
    scraped.to_csv(out, index=False)
    print(f"  Saved {len(scraped)} rows to {out}")

    print("Generating synthetic BLS data...")
    bls = generate_bls()
    # Save in the wide format build_panel.py expects
    bls_out = RAW_BLS / "bls_clean.csv"
    # Also save long format
    bls_long_rows = []
    for _, row in bls.iterrows():
        for col in bls.columns:
            if col not in ("date", "month_start"):
                bls_long_rows.append({
                    "date":     row["date"],
                    "label":    col.replace("bls_", ""),
                    "value":    row[col],
                    "series_id": col,
                })
    bls_long = pd.DataFrame(bls_long_rows)
    bls_long.to_csv(bls_out, index=False)
    print(f"  Saved BLS data to {bls_out}")

    print("\nDone. Now run:")
    print("  python etl/build_panel.py")
    print("  python models/train.py baseline")
    print("  python models/evaluate.py --run-id baseline_ols")


if __name__ == "__main__":
    main()
