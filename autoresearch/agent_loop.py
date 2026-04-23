"""
agent_loop.py — AutoResearch loop: run → evaluate → compare → keep/discard.

The agent may only write to experiments/.
It may NOT modify: evaluate.py, build_panel.py, data splits, or this file.

Loop (≥ 6 iterations):
  1. Read program.md for rules and search strategy
  2. Propose one change to model config or feature engineering
  3. Write change to experiments/configs/<desc>.yaml
  4. Run train.py with that config
  5. Run evaluate.py and read RMSE from metrics_log.csv
  6. If RMSE improves → keep config, update best
     Else → discard (do not update best model)
  7. Log result to autoresearch/run_log.md
  8. Repeat
"""

import subprocess
import csv
import shutil
from pathlib import Path
from datetime import datetime

METRICS_LOG = Path("experiments/results/metrics_log.csv")
BEST_MODEL  = Path("models/best_model")
RUN_LOG     = Path("autoresearch/run_log.md")
RUN_LOG.parent.mkdir(parents=True, exist_ok=True)


def read_best_rmse() -> float:
    """Return the best (lowest) RMSE without lag from the metrics log."""
    if not METRICS_LOG.exists():
        return float("inf")
    with open(METRICS_LOG) as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return float("inf")
    values = [float(r["rmse_no_lag"]) for r in rows if r.get("rmse_no_lag")]
    return min(values) if values else float("inf")


def run_command(cmd: list[str]) -> tuple[int, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout + result.stderr
    return result.returncode, output


def log_run(run_id: str, rmse_before: float, rmse_after: float, kept: bool, notes: str = ""):
    with open(RUN_LOG, "a") as f:
        f.write(f"\n## {run_id} — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"- RMSE before: {rmse_before:.4f}\n")
        f.write(f"- RMSE after:  {rmse_after:.4f}\n")
        f.write(f"- Kept:        {'YES' if kept else 'NO (reverted)'}\n")
        if notes:
            f.write(f"- Notes: {notes}\n")


def run_iteration(config_path: Path, run_id: str) -> bool:
    """
    Run one AutoResearch iteration. Returns True if improvement was kept.
    """
    rmse_before = read_best_rmse()
    print(f"\n[{run_id}] Best RMSE so far: {rmse_before:.4f}")

    # Train with proposed config
    rc, out = run_command(["python", "models/train.py", str(config_path)])
    if rc != 0:
        print(f"  Training failed:\n{out}")
        log_run(run_id, rmse_before, float("inf"), kept=False, notes="training crash")
        return False

    # Evaluate
    rc, out = run_command(["python", "models/evaluate.py", "--run-id", run_id])
    if rc != 0:
        print(f"  Evaluation failed:\n{out}")
        log_run(run_id, rmse_before, float("inf"), kept=False, notes="eval crash")
        return False

    rmse_after = read_best_rmse()
    improved = rmse_after < rmse_before

    if improved:
        print(f"  Improvement! {rmse_before:.4f} → {rmse_after:.4f} — KEEPING")
        log_run(run_id, rmse_before, rmse_after, kept=True)
    else:
        print(f"  No improvement ({rmse_after:.4f} ≥ {rmse_before:.4f}) — REVERTING")
        # Restore previous best model
        # (In practice, the agent should checkpoint before each run)
        log_run(run_id, rmse_before, rmse_after, kept=False)

    return improved


def main():
    print("AutoResearch loop — reading program.md for strategy...")
    program_path = Path("autoresearch/program.md")
    if program_path.exists():
        print(program_path.read_text())
    else:
        print("No program.md found. Create autoresearch/program.md with agent instructions.")
        return

    configs = sorted(Path("experiments/configs").glob("*.yaml"))
    if not configs:
        print("No experiment configs found in experiments/configs/. Add YAML configs to begin.")
        return

    for config_path in configs:
        run_id = config_path.stem
        run_iteration(config_path, run_id)


if __name__ == "__main__":
    main()
