"""
autoresearch_agent.py — Upgraded AutoResearch agent with reasoning output.

This agent thinks out loud before each experiment, explains why it chose
a change, predicts what will happen, then evaluates whether it was right.
It also classifies every result into the 4-category error taxonomy.

Usage:
    python autoresearch_agent.py          # runs 6 iterations
    python autoresearch_agent.py 10       # runs 10 iterations

Error taxonomy (from Week 4):
    SIGNAL FAILURE    — loop runs but no improvement appears
    CODE INSTABILITY  — crash or broken pipeline
    EVAL LEAKAGE      — metric improves but setup shifted
    AGENT MISBEHAVIOR — agent breaks rules or scope
"""

import sys
import csv
import shutil
import importlib
import time
from pathlib import Path
from prepare import load_data, evaluate, log_result, plot_results

RESULTS_FILE = "results.tsv"
MODEL_FILE   = Path("model.py")
BACKUP_FILE  = Path("model_backup.py")

# ── Week 4 controlled experiment plan ─────────────────────────────────────────
# Axis 1: n_estimators (holding depth=3, lr=0.01, sub=0.6 fixed — current best config)
# Axis 2: learning_rate (holding n=800, depth=3, sub=0.6 fixed)
# Axis 3: max_depth    (holding n=800, lr=0.01, sub=0.6 fixed)
# Axis 4: subsample    (holding n=800, depth=3, lr=0.01 fixed)
# One variable changes per iteration. All others stay fixed.

EXPERIMENTS = [
    # ── Axis 1: n_estimators sweep (depth=3, lr=0.01, sub=0.6 fixed) ──
    {
        "description": "GBT n=600 depth=3 lr=0.01 sub=0.6 [axis:n_estimators]",
        "axis":        "n_estimators",
        "changed":     "n_estimators: 800 → 600",
        "fixed":       "depth=3, lr=0.01, sub=0.6, leaf=5",
        "hypothesis":  "Fewer trees may underfit — expecting worse RMSE than current best",
        "code": """from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline

def build_model():
    \"\"\"Axis: n_estimators. Changed: 800→600. Fixed: depth=3, lr=0.01, sub=0.6\"\"\"
    return Pipeline([("model", GradientBoostingRegressor(
        n_estimators=600, max_depth=3, learning_rate=0.01,
        subsample=0.6, min_samples_leaf=5, random_state=42
    ))])
"""
    },
    {
        "description": "GBT n=1000 depth=3 lr=0.01 sub=0.6 [axis:n_estimators]",
        "axis":        "n_estimators",
        "changed":     "n_estimators: 800 → 1000",
        "fixed":       "depth=3, lr=0.01, sub=0.6, leaf=5",
        "hypothesis":  "More trees with same lr may further reduce RMSE — expecting small improvement",
        "code": """from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline

def build_model():
    \"\"\"Axis: n_estimators. Changed: 800→1000. Fixed: depth=3, lr=0.01, sub=0.6\"\"\"
    return Pipeline([("model", GradientBoostingRegressor(
        n_estimators=1000, max_depth=3, learning_rate=0.01,
        subsample=0.6, min_samples_leaf=5, random_state=42
    ))])
"""
    },
    {
        "description": "GBT n=1500 depth=3 lr=0.01 sub=0.6 [axis:n_estimators]",
        "axis":        "n_estimators",
        "changed":     "n_estimators: 800 → 1500",
        "fixed":       "depth=3, lr=0.01, sub=0.6, leaf=5",
        "hypothesis":  "Pushing trees further — may hit diminishing returns or overfit",
        "code": """from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline

def build_model():
    \"\"\"Axis: n_estimators. Changed: 800→1500. Fixed: depth=3, lr=0.01, sub=0.6\"\"\"
    return Pipeline([("model", GradientBoostingRegressor(
        n_estimators=1500, max_depth=3, learning_rate=0.01,
        subsample=0.6, min_samples_leaf=5, random_state=42
    ))])
"""
    },
    # ── Axis 2: learning_rate sweep (n=800, depth=3, sub=0.6 fixed) ──
    {
        "description": "GBT n=800 depth=3 lr=0.005 sub=0.6 [axis:learning_rate]",
        "axis":        "learning_rate",
        "changed":     "learning_rate: 0.01 → 0.005",
        "fixed":       "n=800, depth=3, sub=0.6, leaf=5",
        "hypothesis":  "Lower lr means smaller steps — may need more trees to converge, likely worse with fixed n=800",
        "code": """from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline

def build_model():
    \"\"\"Axis: learning_rate. Changed: 0.01→0.005. Fixed: n=800, depth=3, sub=0.6\"\"\"
    return Pipeline([("model", GradientBoostingRegressor(
        n_estimators=800, max_depth=3, learning_rate=0.005,
        subsample=0.6, min_samples_leaf=5, random_state=42
    ))])
"""
    },
    {
        "description": "GBT n=800 depth=3 lr=0.02 sub=0.6 [axis:learning_rate]",
        "axis":        "learning_rate",
        "changed":     "learning_rate: 0.01 → 0.02",
        "fixed":       "n=800, depth=3, sub=0.6, leaf=5",
        "hypothesis":  "Higher lr means larger steps — may converge faster but overshoot minimum",
        "code": """from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline

def build_model():
    \"\"\"Axis: learning_rate. Changed: 0.01→0.02. Fixed: n=800, depth=3, sub=0.6\"\"\"
    return Pipeline([("model", GradientBoostingRegressor(
        n_estimators=800, max_depth=3, learning_rate=0.02,
        subsample=0.6, min_samples_leaf=5, random_state=42
    ))])
"""
    },
    # ── Axis 3: subsample sweep (n=800, depth=3, lr=0.01 fixed) ──
    {
        "description": "GBT n=800 depth=3 lr=0.01 sub=0.5 [axis:subsample]",
        "axis":        "subsample",
        "changed":     "subsample: 0.6 → 0.5",
        "fixed":       "n=800, depth=3, lr=0.01, leaf=5",
        "hypothesis":  "More aggressive subsampling adds regularization — may reduce overfitting on smooth data",
        "code": """from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline

def build_model():
    \"\"\"Axis: subsample. Changed: 0.6→0.5. Fixed: n=800, depth=3, lr=0.01\"\"\"
    return Pipeline([("model", GradientBoostingRegressor(
        n_estimators=800, max_depth=3, learning_rate=0.01,
        subsample=0.5, min_samples_leaf=5, random_state=42
    ))])
"""
    },
    {
        "description": "GBT n=800 depth=3 lr=0.01 sub=0.8 [axis:subsample]",
        "axis":        "subsample",
        "changed":     "subsample: 0.6 → 0.8",
        "fixed":       "n=800, depth=3, lr=0.01, leaf=5",
        "hypothesis":  "Less subsampling uses more data per tree — may help on small dataset but reduces regularization",
        "code": """from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline

def build_model():
    \"\"\"Axis: subsample. Changed: 0.6→0.8. Fixed: n=800, depth=3, lr=0.01\"\"\"
    return Pipeline([("model", GradientBoostingRegressor(
        n_estimators=800, max_depth=3, learning_rate=0.01,
        subsample=0.8, min_samples_leaf=5, random_state=42
    ))])
"""
    },
    # ── Axis 4: min_samples_leaf sweep (n=800, depth=3, lr=0.01, sub=0.6 fixed) ──
    {
        "description": "GBT n=800 depth=3 lr=0.01 sub=0.6 leaf=2 [axis:min_samples_leaf]",
        "axis":        "min_samples_leaf",
        "changed":     "min_samples_leaf: 5 → 2",
        "fixed":       "n=800, depth=3, lr=0.01, sub=0.6",
        "hypothesis":  "Smaller leaf size allows finer splits — may capture more detail or overfit",
        "code": """from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline

def build_model():
    \"\"\"Axis: min_samples_leaf. Changed: 5→2. Fixed: n=800, depth=3, lr=0.01, sub=0.6\"\"\"
    return Pipeline([("model", GradientBoostingRegressor(
        n_estimators=800, max_depth=3, learning_rate=0.01,
        subsample=0.6, min_samples_leaf=2, random_state=42
    ))])
"""
    },
]


# ── Error taxonomy classifier ─────────────────────────────────────────────────

def classify_error(rmse: float, best_before: float, status: str, crashed: bool) -> tuple[str, str]:
    """Classify result into Week 4 error taxonomy."""
    if crashed:
        return "CODE INSTABILITY", "Pipeline crashed — model could not be trained or evaluated"
    if status == "keep" and rmse < best_before:
        return "NONE", "Genuine improvement — result is valid and interpretable"
    if abs(rmse - best_before) < 0.0001:
        return "SIGNAL FAILURE", "Result identical to best — model change had no measurable effect"
    if rmse > best_before * 1.5:
        return "CODE INSTABILITY", "RMSE jumped dramatically — likely a model configuration error"
    if status == "discard":
        return "SIGNAL FAILURE", "Model change did not improve RMSE — hypothesis was wrong"
    return "SIGNAL FAILURE", "No meaningful improvement detected"


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


def run_experiment() -> tuple[float, float]:
    import model as m
    importlib.reload(m)
    X_train, y_train, X_val, y_val, _ = load_data()
    clf = m.build_model()
    t0  = time.time()
    clf.fit(X_train, y_train)
    train_time = time.time() - t0
    rmse, r2   = evaluate(clf, X_val, y_val)
    return rmse, r2, train_time


# ── Main agent loop ───────────────────────────────────────────────────────────

def main():
    n_iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    experiments  = EXPERIMENTS[:n_iterations]

    print("\n" + "=" * 65)
    print("  AutoResearch Agent — Week 4: Controlled Experiments")
    print("=" * 65)
    print(f"  Running {len(experiments)} controlled iterations")
    print(f"  Strategy: one variable changes per run, all others fixed")
    print(f"  Starting best RMSE: {get_best_rmse():.6f}")
    print(f"  Primary metric: val_rmse without lagged price")
    print("=" * 65)

    results  = []
    taxonomy = []
    best     = get_best_rmse()

    for i, exp in enumerate(experiments):
        print(f"\n{'─'*65}")
        print(f"  Iteration {i+1}/{len(experiments)}")
        print(f"{'─'*65}")
        print(f"\n  📋 EXPERIMENT PLAN")
        print(f"  Description: {exp['description']}")
        print(f"  Axis varied: {exp['axis']}")
        print(f"  What changed: {exp['changed']}")
        print(f"  What stayed fixed: {exp['fixed']}")
        print(f"\n  🧠 AGENT REASONING")
        print(f"  Hypothesis: {exp['hypothesis']}")
        print(f"  Current best RMSE: {best:.6f}")
        print(f"  Prediction: {'improvement likely' if 'improvement' in exp['hypothesis'] else 'may not improve — testing to confirm'}")
        print(f"\n  ⚙️  RUNNING EXPERIMENT...")

        backup_model()
        write_model(exp["code"])
        crashed = False

        try:
            rmse, r2, train_time = run_experiment()
            improved = rmse < best

            if improved:
                status = "keep"
                print(f"\n  ✅ RESULT: IMPROVED")
                print(f"  RMSE: {best:.6f} → {rmse:.6f} (Δ = {best-rmse:.6f})")
                best = rmse
            else:
                status = "discard"
                print(f"\n  ❌ RESULT: NO IMPROVEMENT")
                print(f"  RMSE: {rmse:.6f} vs best {best:.6f} (Δ = {rmse-best:.6f})")
                restore_model()

            print(f"  R²: {r2:.6f}")
            print(f"  Training time: {train_time:.2f}s")

            log_result("w4", rmse, r2, status, exp["description"])

        except Exception as e:
            print(f"\n  💥 CRASH: {e}")
            restore_model()
            rmse, r2, status, crashed = float("inf"), 0.0, "crash", True
            log_result("w4", 9999.0, 0.0, "crash", exp["description"])

        # Error taxonomy classification
        error_type, error_detail = classify_error(rmse, best if not improved else best + 1, status, crashed)

        print(f"\n  🔬 ERROR TAXONOMY")
        print(f"  Type: {error_type}")
        print(f"  Detail: {error_detail}")

        # Post-experiment reasoning
        print(f"\n  💭 AGENT REFLECTION")
        if status == "keep":
            print(f"  Hypothesis was CORRECT — {exp['axis']} change produced real improvement.")
            print(f"  This confirms {exp['axis']} is a productive search axis.")
        elif status == "discard":
            print(f"  Hypothesis was WRONG — {exp['axis']} change did not help.")
            print(f"  Evidence: current best config is more optimal on this axis.")
        else:
            print(f"  Experiment crashed — configuration error, not a valid result.")

        results.append({
            "iteration":   i + 1,
            "axis":        exp["axis"],
            "changed":     exp["changed"],
            "fixed":       exp["fixed"],
            "hypothesis":  exp["hypothesis"],
            "rmse":        rmse if not crashed else None,
            "r2":          r2 if not crashed else None,
            "status":      status,
            "error_type":  error_type,
            "train_time":  train_time if not crashed else None,
        })
        taxonomy.append(error_type)

    # ── Final summary ─────────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  WEEK 4 SUMMARY — CONTROLLED EXPERIMENT RESULTS")
    print(f"{'='*65}")
    print(f"\n  {'#':<4} {'Axis':<20} {'RMSE':<12} {'Status':<10} {'Error Type'}")
    print(f"  {'-'*4} {'-'*20} {'-'*12} {'-'*10} {'-'*20}")

    for r in results:
        rmse_str   = f"{r['rmse']:.6f}" if r["rmse"] else "CRASH"
        icon       = "✅" if r["status"] == "keep" else ("❌" if r["status"] == "discard" else "💥")
        error_abbr = r["error_type"].split()[0] if r["error_type"] != "NONE" else "—"
        print(f"  {r['iteration']:<4} {r['axis']:<20} {rmse_str:<12} {icon} {r['status']:<8} {error_abbr}")

    print(f"\n  Final best RMSE: {get_best_rmse():.6f}")

    # Error taxonomy summary
    from collections import Counter
    counts = Counter(taxonomy)
    print(f"\n  ERROR TAXONOMY BREAKDOWN")
    for etype, count in counts.most_common():
        print(f"  {etype:<25} {count} occurrence{'s' if count > 1 else ''}")

    # Axis analysis
    kept_axes = [r["axis"] for r in results if r["status"] == "keep"]
    dead_axes = [r["axis"] for r in results if r["status"] == "discard"]
    if kept_axes:
        print(f"\n  PRODUCTIVE AXES:  {', '.join(set(kept_axes))}")
    if dead_axes:
        print(f"  EXHAUSTED AXES:   {', '.join(set(dead_axes))}")

    print(f"\n  Regenerating performance.png...")
    plot_results()
    print(f"  Done.")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()
