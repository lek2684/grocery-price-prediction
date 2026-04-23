"""
ingest_usda.py — Pull USDA Food Price Outlook data.

Downloads the USDA ERS food price outlook spreadsheet and extracts
CPI forecast data for food-at-home categories.
Saves to data/raw/usda/.
"""

import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

RAW_DIR = Path("data/raw/usda")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# USDA ERS food price outlook — historical and forecast tables
# Check https://ers.usda.gov/data-products/food-price-outlook/ for current URL
USDA_URL = (
    "https://ers.usda.gov/webdocs/DataFiles/50673/"
    "CPIFoodAndExpenditures.xlsx?v=3491"
)


def download_usda(url: str, dest: Path) -> Path:
    resp = requests.get(url, timeout=60, stream=True)
    resp.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Downloaded USDA data to {dest}")
    return dest


def parse_usda(xlsx_path: Path) -> pd.DataFrame:
    """
    Parse the USDA CPI food price outlook Excel file.
    Sheet structure varies by release — this targets the 'Summary' sheet.
    Adjust sheet_name / skiprows if USDA changes the format.
    """
    xl = pd.ExcelFile(xlsx_path)
    print("Available sheets:", xl.sheet_names)

    dfs = []
    for sheet in xl.sheet_names:
        try:
            df = pd.read_excel(xlsx_path, sheet_name=sheet, header=None)
            # Look for year-indexed rows
            year_col = None
            for col in df.columns:
                if df[col].astype(str).str.match(r"^20\d{2}$").any():
                    year_col = col
                    break
            if year_col is not None:
                df.columns = df.iloc[0]
                df = df[1:].copy()
                df["sheet"] = sheet
                dfs.append(df)
        except Exception as e:
            print(f"  Skipping sheet {sheet}: {e}")

    if not dfs:
        print("Warning: no parseable sheets found. Inspect the file manually.")
        return pd.DataFrame()

    combined = pd.concat(dfs, ignore_index=True)
    return combined


def main():
    ts = datetime.now().strftime("%Y%m%d")
    dest_raw = RAW_DIR / f"usda_raw_{ts}.xlsx"

    try:
        download_usda(USDA_URL, dest_raw)
    except Exception as e:
        print(f"Download failed: {e}")
        print("Manual fallback: download from ers.usda.gov/data-products/food-price-outlook/")
        return

    df = parse_usda(dest_raw)
    out = RAW_DIR / "usda_clean.csv"
    df.to_csv(out, index=False)
    print(f"Saved {len(df)} rows to {out}")


if __name__ == "__main__":
    main()
