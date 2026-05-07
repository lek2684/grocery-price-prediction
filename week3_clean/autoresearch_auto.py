"""
autoresearch_auto.py — Runs the AutoResearch loop automatically for N iterations
and prints a clean summary at the end.

Usage:
    python autoresearch_auto.py          # runs 6 iterations (default)
    python autoresearch_auto.py 10       # runs 10 iterations

The agent tries a different model each iteration, automatically keeps
improvements and reverts bad ones, then prints a full summary.
"""

import sys
import csv
import shutil
import importlib
from pathlib import Path
from prepare import load_data, evaluate, log_result, plot_results

RESULTS_FILE = "results.tsv"
MODEL_FILE   = Path("model.py")
BACKUP_FILE  = Path("model_backup.py")

# ── Experiment configurations to try in order ─────────────────────────────────
# Each is (description, model_code)
# The loop tries these one at a time, keeps if better, discards if not

EXPERIMENTS = [
    (
        "Ridge alpha=0.1",
        """from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

def build_model():
    return Pipeline([
        ("scaler", StandardScaler()),
        ("model",  Ridge(alpha=0.1)),
    ])
"""
    ),
    (
        "Ridge alpha=5.0",
        """from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

def build_model():
    return Pipeline([
        ("scaler", StandardScaler()),
        ("model",  Ridge(alpha=5.0)),
    ])
"""
    ),
    (
        "GBT n=1000 depth=4 lr=0.008 sub=0.7",
        """from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline

def build_model():
    return Pipeline([
        ("model", GradientBoostingRegressor(
            n_estimators=1000, max_depth=4, learning_rate=0.008,
            subsample=0.7, min_samples_leaf=5, random_state=42
        )),
    ])
"""
    ),
    (
        "GBT n=800 depth=3 lr=0.01 sub=0.6",
        """from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline

def build_model():
    return Pipeline([
        ("model", GradientBoostingRegressor(
            n_estimators=800, max_depth=3, learning_rate=0.01,
            subsample=0.6, min_samples_leaf=5, random_state=42
        )),
    ])
"""
    ),
    (
        "GBT n=800 depth=5 lr=0.01 sub=0.7",
        """from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline

def build_model():
    return Pipeline([
        ("model", GradientBoostingRegressor(
            n_estimators=800, max_depth=5, learning_rate=0.01,
            subsample=0.7, min_samples_leaf=3, random_state=42
        )),
    ])
"""
    ),
    (
        "RandomForest n=500 depth=15 leaf=2",
        """from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline

def build_model():
    return Pipeline([
        ("model", RandomForestRegressor(
            n_estimators=500, max_depth=15, min_samples_leaf=2,
            random_state=42, n_jobs=-1
        )),
    ])
"""
    ),
    (
        "GBT n=1200 depth=4 lr=0.006 sub=0.7",
        """from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline

def build_model():
    return Pipeline([
        ("model", GradientBoostingRegressor(
            n_estimators=1200, max_depth=4, learning_rate=0.006,
            subsample=0.7, min_samples_leaf=5, random_state=42
        )),
    ])
"""
    ),
    (
        "GBT n=800 depth=4 lr=0.01 sub=0.8 leaf=3",
        """from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline

def build_model():
    return Pipeline([
        ("model", GradientBoostingRegressor(
            n_estimators=800, max_depth=4, learning_rate=0.01,
            subsample=0.8, min_samples_leaf=3, random_state=42
        )),
    ])
"""
    ),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_best_rmse() -> float:
    if not Path(RESULTS_FILE).exists():
        return float("inf")
    with open(RESULTS_FILE) as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    values = [float(r["val_rmse"]) for r in rows if r.get("val_rmse")]
    return min(values) if values else float("inf")


def backup_model():
    shutil.copy(MODEL_FILE, BACKUP_FILE)


def restore_model():
    if BACKUP_FILE.exists():
        shutil.copy(BACKUP_FILE, MODEL_FILE)


def write_model(code: str):
    MODEL_FILE.write_text(code)


def run_experiment(description: str) -> tuple[float, float]:
    import model as m
    importlib.reload(m)
    X_train, y_train, X_val, y_val, _ = load_data()
    clf = m.build_model()
    clf.fit(X_train, y_train)
    rmse, r2 = evaluate(clf, X_val, y_val)
    return rmse, r2


# ── Main auto loop ────────────────────────────────────────────────────────────

def main():
    n_iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    experiments  = EXPERIMENTS[:n_iterations]

    print("\n" + "=" * 60)
    print("  AutoResearch Auto Loop — Grocery Price Prediction")
    print("=" * 60)
    print(f"  Running {len(experiments)} iterations automatically")
    print(f"  Starting best RMSE: {get_best_rmse():.6f}")
    print(f"  Metric: val_rmse without lagged price (lower = better)")
    print("=" * 60 + "\n")

    results = []
    overall_best = get_best_rmse()

    for i, (description, model_code) in enumerate(experiments):
        print(f"Iteration {i+1}/{len(experiments)}: {description}")
        print(f"  Best so far: {overall_best:.6f}")

        backup_model()
        write_model(model_code)

        try:
            rmse, r2 = run_experiment(description)
            improved  = rmse < overall_best

            if improved:
                status = "keep"
                print(f"  ✅ IMPROVED: {overall_best:.6f} → {rmse:.6f}")
                overall_best = rmse
                log_result("auto", rmse, r2, "keep", description)
            else:
                status = "discard"
                print(f"  ❌ No improvement: {rmse:.6f} ≥ {overall_best:.6f} — reverting")
                restore_model()
                log_result("auto", rmse, r2, "discard", description)

            results.append({
                "iteration":   i + 1,
                "description": description,
                "rmse":        rmse,
                "r2":          r2,
                "status":      status,
            })

        except Exception as e:
            print(f"  💥 ERROR: {e} — reverting")
            restore_model()
            results.append({
                "iteration":   i + 1,
                "description": description,
                "rmse":        None,
                "r2":          None,
                "status":      "crash",
            })

        print()

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  {'#':<4} {'Status':<10} {'RMSE':<12} {'Description'}")
    print(f"  {'-'*4} {'-'*10} {'-'*12} {'-'*30}")
    for r in results:
        rmse_str = f"{r['rmse']:.6f}" if r['rmse'] else "ERROR"
        icon = "✅" if r["status"] == "keep" else ("❌" if r["status"] == "discard" else "💥")
        print(f"  {r['iteration']:<4} {icon} {r['status']:<8} {rmse_str:<12} {r['description']}")

    kept    = [r for r in results if r["status"] == "keep"]
    discard = [r for r in results if r["status"] == "discard"]
    crashes = [r for r in results if r["status"] == "crash"]

    print(f"\n  Kept:     {len(kept)}")
    print(f"  Discarded:{len(discard)}")
    print(f"  Crashes:  {len(crashes)}")
    print(f"\n  Final best RMSE: {overall_best:.6f}")

    if kept:
        best = min(kept, key=lambda r: r["rmse"])
        print(f"  Best new model:  {best['description']}")

    print("\n  Regenerating performance.png...")
    plot_results()
    print("  Done. See performance.png for full experiment history.")
    print("=" * 60)


if __name__ == "__main__":
    main()
