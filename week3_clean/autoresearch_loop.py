"""
autoresearch_loop.py — Run the AutoResearch loop interactively.

This is the main script you run in VS Code to execute the research loop.
It reads program.md, runs experiments by editing model.py, evaluates,
and logs results to results.tsv.

Usage:
    python autoresearch_loop.py

The loop will:
1. Show you the current best RMSE
2. Ask you to confirm before each experiment
3. Automatically log keep/discard decisions
4. Update performance.png after each run
"""

import csv
import sys
import shutil
from pathlib import Path
from prepare import load_data, evaluate, log_result, plot_results

RESULTS_FILE = "results.tsv"
MODEL_FILE   = Path("model.py")
BACKUP_FILE  = Path("model_backup.py")


def get_best_rmse() -> float:
    """Read current best RMSE from results.tsv."""
    if not Path(RESULTS_FILE).exists():
        return float("inf")
    with open(RESULTS_FILE) as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    values = [float(r["val_rmse"]) for r in rows if r.get("val_rmse")]
    return min(values) if values else float("inf")


def get_best_description() -> str:
    """Return description of the best run so far."""
    if not Path(RESULTS_FILE).exists():
        return "none yet"
    with open(RESULTS_FILE) as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if not rows:
        return "none yet"
    best = min(rows, key=lambda r: float(r["val_rmse"]))
    return best["description"]


def backup_model():
    """Save current model.py before experimenting."""
    shutil.copy(MODEL_FILE, BACKUP_FILE)


def restore_model():
    """Restore model.py from backup (on discard)."""
    if BACKUP_FILE.exists():
        shutil.copy(BACKUP_FILE, MODEL_FILE)
        print("  model.py reverted to previous version.")


def run_one_experiment(description: str, status: str = "keep") -> tuple[float, float]:
    """Train and evaluate current model.py. Returns (rmse, r2)."""
    # Reload model fresh each time
    import importlib
    import model as m
    importlib.reload(m)

    X_train, y_train, X_val, y_val, _ = load_data()
    clf = m.build_model()
    clf.fit(X_train, y_train)
    rmse, r2 = evaluate(clf, X_val, y_val)
    log_result("loop", rmse, r2, status, description)
    return rmse, r2


def print_header():
    print("\n" + "=" * 55)
    print("  AutoResearch Loop — Grocery Price Prediction")
    print("=" * 55)
    print(f"  Metric:      val_rmse (without lagged price)")
    print(f"  Best so far: {get_best_rmse():.6f}")
    print(f"  Best model:  {get_best_description()}")
    print("=" * 55)


def main():
    print_header()
    print("\nReading program.md for agent instructions...")
    if Path("program.md").exists():
        print(Path("program.md").read_text())
    else:
        print("WARNING: program.md not found.")

    iteration = 0
    while True:
        iteration += 1
        print(f"\n{'─'*55}")
        print(f"  Iteration {iteration}")
        print(f"  Current best RMSE: {get_best_rmse():.6f}")
        print(f"{'─'*55}")
        print("\nOptions:")
        print("  [r] Run experiment with current model.py")
        print("  [s] Show current model.py")
        print("  [p] Plot results and save performance.png")
        print("  [q] Quit loop")

        choice = input("\nChoice: ").strip().lower()

        if choice == "q":
            print("\nLoop ended. Final results:")
            plot_results()
            print(f"Best RMSE: {get_best_rmse():.6f}")
            break

        elif choice == "p":
            plot_results()
            print("performance.png updated.")

        elif choice == "s":
            print("\n--- model.py ---")
            print(MODEL_FILE.read_text())

        elif choice == "r":
            description = input("Describe this experiment (e.g. 'Ridge alpha=0.1'): ").strip()
            if not description:
                description = f"iteration_{iteration}"

            best_before = get_best_rmse()
            backup_model()

            print(f"\nRunning experiment: {description}...")
            try:
                rmse, r2 = run_one_experiment(description, status="keep")
                print(f"  val_rmse: {rmse:.6f}")
                print(f"  val_r2:   {r2:.6f}")
                print(f"  Previous best: {best_before:.6f}")

                if rmse < best_before:
                    print(f"\n  ✅ IMPROVEMENT! {best_before:.6f} → {rmse:.6f}")
                    print("  Keeping this model.")
                    # Update status to keep in log (already logged as keep)
                else:
                    print(f"\n  ❌ No improvement ({rmse:.6f} ≥ {best_before:.6f})")
                    print("  Reverting model.py...")
                    restore_model()
                    # Re-log as discard
                    with open(RESULTS_FILE) as f:
                        lines = f.readlines()
                    lines[-1] = lines[-1].replace("\tkeep\t", "\tdiscard\t")
                    with open(RESULTS_FILE, "w") as f:
                        f.writelines(lines)

                plot_results()
                print(f"  performance.png updated.")

            except Exception as e:
                print(f"  ERROR: {e}")
                restore_model()
                print("  model.py reverted due to error.")
        else:
            print("  Unknown option. Try r, s, p, or q.")


if __name__ == "__main__":
    main()
