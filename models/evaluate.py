"""
evaluate.py — LOCKED evaluation script.

DO NOT MODIFY. This file is version-locked.
The agent may NOT edit this file — it writes only to experiments/.

Computes MAE, RMSE, and R² on the held-out test set.
Results are appended to experiments/results/metrics_log.csv.

Usage:
    python models/evaluate.py --run-id <desc>
    python models/evaluate.py --run-id baseline_ols_no_lag
"""

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

TEST_PATH    = Path("data/processed/test.csv")
MODEL_PATH   = Path("models/best_model/model.pkl")
RESULTS_LOG  = Path("experiments/results/metrics_log.csv")
RESULTS_LOG.parent.mkdir(parents=True, exist_ok=True)

TARGET       = "price"
TARGET_DELTA = "price_delta"

# Features used by the model (must match train.py)
FEATURES_WITH_LAG    = ["week_idx", "category_code", "retailer_code", "price_lag1", "price_roll4"]
FEATURES_WITHOUT_LAG = ["week_idx", "category_code", "retailer_code", "price_roll4"]


def load_test() -> pd.DataFrame:
    if not TEST_PATH.exists():
        raise FileNotFoundError(f"Test set not found: {TEST_PATH}. Run etl/build_panel.py first.")
    df = pd.read_csv(TEST_PATH, parse_dates=["week_start"])
    return df.dropna(subset=[TARGET])


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {
        "mae":  round(float(mean_absolute_error(y_true, y_pred)), 6),
        "rmse": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 6),
        "r2":   round(float(r2_score(y_true, y_pred)), 6),
        "n":    int(len(y_true)),
    }


def evaluate_model(model, df: pd.DataFrame, feature_cols: list, target: str) -> dict:
    available = [c for c in feature_cols if c in df.columns]
    missing   = [c for c in feature_cols if c not in df.columns]
    if missing:
        print(f"  Warning: missing features {missing} — dropping from eval")
    sub = df.dropna(subset=available + [target])
    y_true = sub[target].values
    y_pred = model.predict(sub[available])
    return compute_metrics(y_true, y_pred)


def log_result(run_id: str, metrics_with: dict, metrics_without: dict, notes: str = ""):
    row = {
        "timestamp":       datetime.now().isoformat(),
        "run_id":          run_id,
        "mae_with_lag":    metrics_with.get("mae"),
        "rmse_with_lag":   metrics_with.get("rmse"),
        "r2_with_lag":     metrics_with.get("r2"),
        "mae_no_lag":      metrics_without.get("mae"),
        "rmse_no_lag":     metrics_without.get("rmse"),
        "r2_no_lag":       metrics_without.get("r2"),
        "n_test":          metrics_with.get("n"),
        "notes":           notes,
    }
    write_header = not RESULTS_LOG.exists()
    with open(RESULTS_LOG, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(row)
    print(f"\nLogged to {RESULTS_LOG}")
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default="unnamed_run", help="Short description of this run")
    parser.add_argument("--notes", default="", help="Optional notes")
    args = parser.parse_args()

    print(f"Loading test set from {TEST_PATH}...")
    df = load_test()
    print(f"Test set: {len(df)} rows")

    print(f"Loading model from {MODEL_PATH}...")
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}. Run models/train.py first.")
    model = joblib.load(MODEL_PATH)

    print("\n--- Evaluation WITH lagged price ---")
    m_with = evaluate_model(model, df, FEATURES_WITH_LAG, TARGET)
    print(json.dumps(m_with, indent=2))

    print("\n--- Evaluation WITHOUT lagged price ---")
    m_without = evaluate_model(model, df, FEATURES_WITHOUT_LAG, TARGET)
    print(json.dumps(m_without, indent=2))

    print("\n--- Summary ---")
    print(f"R² with lag:    {m_with['r2']:.4f}  (high expected — prices are sticky)")
    print(f"R² without lag: {m_without['r2']:.4f}  (this is the meaningful number)")

    log_result(args.run_id, m_with, m_without, args.notes)


if __name__ == "__main__":
    main()
