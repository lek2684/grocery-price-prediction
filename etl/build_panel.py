"""
build_panel.py — Merge scraped retail prices with BLS/USDA public data
into a single item–retailer–date panel (data/processed/panel.csv).

IMPORTANT: This script uses a TIME-BASED forward-chaining split.
Random splits are NOT used — prices are autocorrelated and random
splits leak future data into training, inflating R².
"""

import pandas as pd
import numpy as np
from pathlib import Path

RAW_SCRAPED = Path("data/raw/scraped")
BLS_CLEAN   = Path("data/raw/bls/bls_clean.csv")
USDA_CLEAN  = Path("data/raw/usda/usda_clean.csv")
PROCESSED   = Path("data/processed")
PROCESSED.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Load scraped retail prices
# ---------------------------------------------------------------------------

def load_scraped() -> pd.DataFrame:
    csvs = list(RAW_SCRAPED.glob("*.csv"))
    if not csvs:
        print("No scraped CSVs found in data/raw/scraped/ — returning empty frame.")
        return pd.DataFrame(columns=[
            "product_name", "brand", "package_size", "price",
            "unit_price", "retailer", "scrape_date", "category",
        ])
    df = pd.concat([pd.read_csv(f) for f in csvs], ignore_index=True)
    df["scrape_date"] = pd.to_datetime(df["scrape_date"])
    df["week_start"]  = df["scrape_date"] - pd.to_timedelta(
        df["scrape_date"].dt.dayofweek, unit="d"
    )
    return df


# ---------------------------------------------------------------------------
# 2. Load BLS data and pivot to wide format (one column per series)
# ---------------------------------------------------------------------------

def load_bls() -> pd.DataFrame:
    if not BLS_CLEAN.exists():
        print("BLS clean CSV not found — run ingest_bls.py first.")
        return pd.DataFrame()
    df = pd.read_csv(BLS_CLEAN, parse_dates=["date"])
    wide = df.pivot_table(index="date", columns="label", values="value", aggfunc="mean")
    wide.columns = [f"bls_{c}" for c in wide.columns]
    wide = wide.reset_index().rename(columns={"date": "month_start"})
    return wide


# ---------------------------------------------------------------------------
# 3. Build panel: merge scraped + BLS on approximate month
# ---------------------------------------------------------------------------

def build_panel(scraped: pd.DataFrame, bls: pd.DataFrame) -> pd.DataFrame:
    if scraped.empty:
        print("Scraped data is empty — panel will contain only BLS data.")
        return bls

    # Align scraped weekly data to BLS monthly data via month floor
    scraped["month_start"] = scraped["week_start"].dt.to_period("M").dt.to_timestamp()

    if bls.empty:
        panel = scraped.copy()
    else:
        panel = scraped.merge(bls, on="month_start", how="left")

    return panel


# ---------------------------------------------------------------------------
# 4. Feature engineering
# ---------------------------------------------------------------------------

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["product_name", "retailer", "week_start"]).copy()

    # Lagged price (1 week) — NOTE: report metrics BOTH with and without this
    df["price_lag1"] = df.groupby(["product_name", "retailer"])["price"].shift(1)

    # Price change (week-over-week) — preferred target for gap analysis
    df["price_delta"] = df["price"] - df["price_lag1"]

    # Rolling 4-week average price
    df["price_roll4"] = (
        df.groupby(["product_name", "retailer"])["price"]
        .transform(lambda x: x.shift(1).rolling(4).mean())
    )

    # Categorical encodings
    df["category_code"] = df["category"].astype("category").cat.codes
    df["retailer_code"]  = df["retailer"].astype("category").cat.codes

    # Week index (for time trend)
    if "week_start" in df.columns:
        min_week = df["week_start"].min()
        df["week_idx"] = ((df["week_start"] - min_week).dt.days / 7).astype(int)

    return df


# ---------------------------------------------------------------------------
# 5. Time-based train/test split
# ---------------------------------------------------------------------------

def time_split(df: pd.DataFrame, test_frac: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Forward-chaining split: train on the earliest (1 - test_frac) of weeks,
    test on the latest test_frac of weeks.

    This is mandatory — random splits inflate R² due to autocorrelation.
    """
    if "week_start" not in df.columns:
        raise ValueError("week_start column required for time-based split.")

    weeks = sorted(df["week_start"].unique())
    cutoff_idx = int(len(weeks) * (1 - test_frac))
    cutoff     = weeks[cutoff_idx]

    train = df[df["week_start"] <  cutoff].copy()
    test  = df[df["week_start"] >= cutoff].copy()

    print(f"Split: train {len(train)} rows ({train['week_start'].min()} → {train['week_start'].max()})")
    print(f"       test  {len(test)}  rows ({test['week_start'].min()} → {test['week_start'].max()})")
    return train, test


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading scraped data...")
    scraped = load_scraped()

    print("Loading BLS data...")
    bls = load_bls()

    print("Building panel...")
    panel = build_panel(scraped, bls)

    print("Engineering features...")
    panel = engineer_features(panel)

    # Save full panel
    panel_out = PROCESSED / "panel.csv"
    panel.to_csv(panel_out, index=False)
    print(f"Panel saved: {panel_out} ({len(panel)} rows)")

    # Save feature matrix (drop raw text columns)
    drop_cols = ["brand", "package_size", "scrape_date"]
    features = panel.drop(columns=[c for c in drop_cols if c in panel.columns])
    feat_out = PROCESSED / "features.csv"
    features.to_csv(feat_out, index=False)
    print(f"Features saved: {feat_out}")

    # Time split (deterministic)
    if "week_start" in panel.columns and not panel.empty:
        train, test = time_split(panel)
        train.to_csv(PROCESSED / "train.csv", index=False)
        test.to_csv(PROCESSED / "test.csv",   index=False)
        print("Train/test CSVs saved.")


if __name__ == "__main__":
    main()
