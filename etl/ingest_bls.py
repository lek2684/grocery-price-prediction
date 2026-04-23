"""
ingest_bls.py — Pull and clean BLS CPI, PPI, and average price data.

BLS public API v2 (no key required for low-volume pulls).
Saves raw JSON + cleaned CSVs to data/raw/bls/.
"""

import requests
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

BLS_API = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
RAW_DIR = Path("data/raw/bls")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Series IDs — food-at-home CPI subcategories + selected avg prices
SERIES = {
    # CPI food-at-home
    "cpi_food_at_home":      "CUUR0000SAF11",
    "cpi_cereals_bakery":    "CUUR0000SAF111",
    "cpi_meats_poultry":     "CUUR0000SAF112",
    "cpi_dairy":             "CUUR0000SAF113",
    "cpi_fruits_veg":        "CUUR0000SAF114",
    "cpi_other_food_home":   "CUUR0000SAF116",
    # PPI — food manufacturing
    "ppi_food_mfg":          "PCU311311",
    # Avg prices (selected items)
    "avg_eggs_dozen":        "APU0000708111",
    "avg_milk_gallon":       "APU0000709112",
    "avg_bread_loaf":        "APU0000702111",
    "avg_ground_beef_lb":    "APU0000703112",
    "avg_chicken_breast_lb": "APU0000706111",
    "avg_bananas_lb":        "APU0000711211",
    "avg_rice_lb":           "APU0000712311",
}

START_YEAR = "2022"
END_YEAR   = str(datetime.now().year)


def fetch_series(series_ids: list[str], start_year: str, end_year: str) -> dict:
    payload = {
        "seriesid": series_ids,
        "startyear": start_year,
        "endyear":   end_year,
    }
    resp = requests.post(BLS_API, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def parse_series(data: dict, label_map: dict) -> pd.DataFrame:
    rows = []
    for series in data.get("Results", {}).get("series", []):
        sid = series["seriesID"]
        label = label_map.get(sid, sid)
        for obs in series.get("data", []):
            rows.append({
                "series_id": sid,
                "label":     label,
                "year":      int(obs["year"]),
                "period":    obs["period"],
                "value":     float(obs["value"]) if obs["value"] != "-" else None,
                "footnotes": "; ".join(f["text"] for f in obs.get("footnotes", []) if f),
            })
    df = pd.DataFrame(rows)
    # Convert period (M01–M12) to date
    df = df[df["period"].str.startswith("M")]
    df["month"] = df["period"].str[1:].astype(int)
    df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
    return df.drop(columns=["period", "month"]).sort_values(["label", "date"])


def main():
    id_to_label = {v: k for k, v in SERIES.items()}
    series_ids  = list(SERIES.values())

    # BLS API allows max 50 series per request
    chunks = [series_ids[i:i+50] for i in range(0, len(series_ids), 50)]
    all_dfs = []
    for chunk in chunks:
        raw = fetch_series(chunk, START_YEAR, END_YEAR)
        # Save raw JSON
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(RAW_DIR / f"bls_raw_{ts}.json", "w") as f:
            json.dump(raw, f, indent=2)
        all_dfs.append(parse_series(raw, id_to_label))

    df = pd.concat(all_dfs, ignore_index=True)
    out = RAW_DIR / "bls_clean.csv"
    df.to_csv(out, index=False)
    print(f"Saved {len(df)} rows to {out}")
    print(df.groupby("label")["date"].agg(["min", "max"]))


if __name__ == "__main__":
    main()
