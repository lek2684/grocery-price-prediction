"""
FROZEN -- Do not modify this file.
Data loading, train/val split, evaluation metric, and plotting.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import csv
import os

RANDOM_SEED   = 42
VAL_FRACTION  = 0.2
RESULTS_FILE  = "results.tsv"

# Features WITHOUT lagged price — this is the meaningful metric
# (lagged price makes R² trivially high; without it residuals show real gaps)
FEATURES = ["week_idx", "category_code", "retailer_code", "price_roll4"]
TARGET   = "price"


def load_data():
    """
    Load grocery price panel from train.csv / test.csv.
    Uses a secondary val split from train for model search.
    Test set is never touched during the search phase.
    """
    train_df = pd.read_csv("train.csv")
    train_df = train_df.dropna(subset=FEATURES + [TARGET])

    # Val split: last 20% of training weeks (time-ordered, not random)
    weeks     = sorted(train_df["week_start"].unique())
    cutoff    = weeks[int(len(weeks) * (1 - VAL_FRACTION))]
    val_mask  = train_df["week_start"] >= cutoff

    X_train = train_df[~val_mask][FEATURES].values
    y_train = train_df[~val_mask][TARGET].values
    X_val   = train_df[val_mask][FEATURES].values
    y_val   = train_df[val_mask][TARGET].values

    print(f"Data: {len(X_train)} train, {len(X_val)} val, {len(FEATURES)} features")
    return X_train, y_train, X_val, y_val, FEATURES


def evaluate(model, X_val, y_val):
    """Frozen evaluation metric: validation RMSE (lower is better)."""
    y_pred = model.predict(X_val)
    rmse   = float(np.sqrt(mean_squared_error(y_val, y_pred)))
    r2     = float(r2_score(y_val, y_pred))
    return rmse, r2


def log_result(experiment_id, val_rmse, val_r2, status, description):
    """Append one row to results.tsv."""
    file_exists = os.path.exists(RESULTS_FILE)
    with open(RESULTS_FILE, "a", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        if not file_exists:
            writer.writerow(["experiment", "val_rmse", "val_r2", "status", "description"])
        writer.writerow([experiment_id, f"{val_rmse:.6f}", f"{val_r2:.6f}", status, description])


def plot_results(save_path="performance.png"):
    """Plot val RMSE and R² over experiments from results.tsv."""
    if not os.path.exists(RESULTS_FILE):
        print("No results.tsv found. Run some experiments first.")
        return

    experiments, rmses, r2s, statuses, descriptions = [], [], [], [], []
    with open(RESULTS_FILE) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            experiments.append(row["experiment"])
            rmses.append(float(row["val_rmse"]))
            r2s.append(float(row["val_r2"]))
            statuses.append(row["status"])
            descriptions.append(row["description"])

    color_map = {"keep": "#2ecc71", "discard": "#e74c3c", "baseline": "#3498db"}
    colors    = [color_map.get(s, "#95a5a6") for s in statuses]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Outlier clipping
    q75 = np.percentile(rmses, 75)
    iqr = np.percentile(rmses, 75) - np.percentile(rmses, 25)
    rmse_upper = q75 + 2.5 * max(iqr, 0.01)

    # Top: RMSE
    ax1.scatter(range(len(rmses)), rmses, c=colors, s=80, zorder=3,
                edgecolors="white", linewidth=0.5)
    ax1.plot(range(len(rmses)), rmses, "k--", alpha=0.2, zorder=2)

    best_so_far, current_best = [], float("inf")
    for r in rmses:
        current_best = min(current_best, r)
        best_so_far.append(current_best)
    ax1.plot(range(len(rmses)), best_so_far, color="#2ecc71",
             linewidth=2.5, label="Best so far")

    reasonable_max = min(max(rmses), rmse_upper)
    ax1.set_ylim(min(rmses) * 0.9, reasonable_max * 1.15)
    for i, r in enumerate(rmses):
        if r > reasonable_max:
            ax1.annotate(f"{r:.3f}", xy=(i, reasonable_max * 1.05),
                         fontsize=8, ha="center", color="#e74c3c", fontweight="bold")

    ax1.set_ylabel("Validation RMSE — no lag (lower = better)", fontsize=11)
    ax1.set_title("AutoResearch: Grocery Price Prediction", fontsize=13, fontweight="bold")
    ax1.grid(True, alpha=0.3)

    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#3498db",
               markersize=10, label="baseline"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#2ecc71",
               markersize=10, label="keep (improved)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#e74c3c",
               markersize=10, label="discard (regressed)"),
        Line2D([0], [0], color="#2ecc71", linewidth=2.5, label="Best so far"),
    ]
    ax1.legend(handles=legend_elements, loc="upper right", fontsize=9)

    # Bottom: R²
    ax2.scatter(range(len(r2s)), r2s, c=colors, s=80, zorder=3,
                edgecolors="white", linewidth=0.5)
    ax2.plot(range(len(r2s)), r2s, "k--", alpha=0.2, zorder=2)

    best_r2, current_best_r2 = [], -float("inf")
    for r in r2s:
        current_best_r2 = max(current_best_r2, r)
        best_r2.append(current_best_r2)
    ax2.plot(range(len(r2s)), best_r2, color="#2ecc71", linewidth=2.5)
    ax2.set_ylim(max(min(r2s) * 1.05, -0.1), max(r2s) * 1.05)
    ax2.set_ylabel("Validation R² (higher = better)", fontsize=11)
    ax2.set_xlabel("Experiment #", fontsize=11)
    ax2.grid(True, alpha=0.3)

    short_labels = [d[:22] + ".." if len(d) > 24 else d for d in descriptions]
    ax2.set_xticks(range(len(rmses)))
    ax2.set_xticklabels(short_labels, rotation=45, ha="right", fontsize=8)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"Saved {save_path}")


if __name__ == "__main__":
    plot_results()
