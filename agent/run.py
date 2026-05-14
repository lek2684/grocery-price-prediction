"""
FROZEN -- Do not modify this file.
Run a single experiment and log result.

Status (keep/discard/baseline) is determined AUTOMATICALLY by comparing
val_rmse to the current best in results.tsv. Never set manually.

Usage:
    python run.py "description"            # auto keep/discard
    python run.py "description" --baseline # marks as baseline
"""

import sys
import csv
import time
import subprocess
from pathlib import Path
from prepare import load_data, evaluate, log_result

RESULTS_FILE = "results.tsv"


def get_best_rmse() -> float:
    """Read current best RMSE from results.tsv."""
    if not Path(RESULTS_FILE).exists():
        return float("inf")
    with open(RESULTS_FILE) as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    values = [float(r["val_rmse"]) for r in rows if r.get("val_rmse")]
    return min(values) if values else float("inf")


def get_git_hash():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return "no-git"


def main():
    args = sys.argv[1:]
    is_baseline = "--baseline" in args
    description_parts = [a for a in args if a != "--baseline"]
    description = " ".join(description_parts) if description_parts else "experiment"

    # Load data
    X_train, y_train, X_val, y_val, _ = load_data()

    # Build and train model
    from model import build_model
    model = build_model()
    print(f"Model: {model}")

    t0 = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - t0
    print(f"Training time: {train_time:.2f}s")

    # Evaluate
    val_rmse, val_r2 = evaluate(model, X_val, y_val)
    print(f"val_rmse: {val_rmse:.6f}")
    print(f"val_r2:   {val_r2:.6f}")

    # Auto-determine status — never manual
    if is_baseline:
        status = "baseline"
    else:
        best_before = get_best_rmse()
        status = "keep" if val_rmse < best_before else "discard"
        print(f"Previous best: {best_before:.6f} → status: {status}")

    # Log result
    commit = get_git_hash()
    log_result(commit, val_rmse, val_r2, status, description)
    print(f"Result logged to {RESULTS_FILE} (status={status})")


if __name__ == "__main__":
    main()
