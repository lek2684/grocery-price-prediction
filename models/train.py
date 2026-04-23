"""
train.py — Unified training script called by the AutoResearch agent.

The agent may call this script with different configs from experiments/configs/.
The agent may NOT modify this script directly — changes go to experiments/ only.

Usage:
    python models/train.py baseline
    python models/train.py --config experiments/configs/ridge_v1.yaml
"""

import argparse
import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

TRAIN_PATH  = Path("data/processed/train.csv")
MODEL_DIR   = Path("models/best_model")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

TARGET       = "price"
FEATURES_WITH_LAG    = ["week_idx", "category_code", "retailer_code", "price_lag1", "price_roll4"]
FEATURES_WITHOUT_LAG = ["week_idx", "category_code", "retailer_code", "price_roll4"]


BASELINE_CONFIG = {
    "model":    "ols",
    "features": "with_lag",  # also trains without_lag automatically
    "params":   {},
}

MODEL_REGISTRY = {
    "ols":              lambda p: LinearRegression(**p),
    "ridge":            lambda p: Ridge(**p),
    "lasso":            lambda p: Lasso(**p),
    "random_forest":    lambda p: RandomForestRegressor(random_state=42, **p),
    "gradient_boosting":lambda p: GradientBoostingRegressor(random_state=42, **p),
}


def load_train() -> pd.DataFrame:
    if not TRAIN_PATH.exists():
        raise FileNotFoundError(f"Training set not found: {TRAIN_PATH}. Run etl/build_panel.py first.")
    df = pd.read_csv(TRAIN_PATH, parse_dates=["week_start"])
    return df.dropna(subset=[TARGET])


def get_feature_cols(config: dict) -> list:
    return FEATURES_WITH_LAG if config.get("features") == "with_lag" else FEATURES_WITHOUT_LAG


def train(config: dict, df: pd.DataFrame):
    model_key = config.get("model", "ols")
    params    = config.get("params", {})

    if model_key not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model: {model_key}. Choose from {list(MODEL_REGISTRY)}")

    feat_cols = get_feature_cols(config)
    available = [c for c in feat_cols if c in df.columns]
    sub = df.dropna(subset=available + [TARGET])

    X = sub[available].values
    y = sub[TARGET].values

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("model",  MODEL_REGISTRY[model_key](params)),
    ])
    pipe.fit(X, y)
    print(f"Trained {model_key} on {len(sub)} rows using features: {available}")
    return pipe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", default="baseline",
                        help="'baseline' or path to a YAML config in experiments/configs/")
    args = parser.parse_args()

    if args.mode == "baseline":
        config = BASELINE_CONFIG
        run_id = "baseline"
    else:
        config_path = Path(args.mode)
        if not config_path.exists():
            config_path = Path("experiments/configs") / args.mode
        with open(config_path) as f:
            config = yaml.safe_load(f)
        run_id = config_path.stem

    print(f"Loading training data...")
    df = load_train()
    print(f"Training set: {len(df)} rows")

    print(f"Training model: {config.get('model', 'ols')}...")
    model = train(config, df)

    out = MODEL_DIR / "model.pkl"
    joblib.dump(model, out)
    print(f"Model saved to {out}")

    # Save config alongside model
    meta = {"run_id": run_id, "config": config}
    with open(MODEL_DIR / "model_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Metadata saved to {MODEL_DIR}/model_meta.json")
    print(f"\nNext: run  python models/evaluate.py --run-id {run_id}")


if __name__ == "__main__":
    main()
