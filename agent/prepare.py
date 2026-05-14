"""
FROZEN -- Do not modify this file.
Data loading, train/val split, evaluation metric, and plotting.
Colors on performance.png are based on actual RMSE improvement vs running best,
not the status column — green always means genuine improvement.
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

FEATURES = ["week_idx", "category_code", "retailer_code", "price_roll4"]
TARGET   = "price"


def load_data():
    train_df = pd.read_csv("train.csv")
    train_df = train_df.dropna(subset=FEATURES + [TARGET])
    weeks    = sorted(train_df["week_start"].unique())
    cutoff   = weeks[int(len(weeks) * (1 - VAL_FRACTION))]
    val_mask = train_df["week_start"] >= cutoff
    X_train = train_df[~val_mask][FEATURES].values
    y_train = train_df[~val_mask][TARGET].values
    X_val   = train_df[val_mask][FEATURES].values
    y_val   = train_df[val_mask][TARGET].values
    print(f"Data: {len(X_train)} train, {len(X_val)} val, {len(FEATURES)} features")
    return X_train, y_train, X_val, y_val, FEATURES


def evaluate(model, X_val, y_val):
    y_pred = model.predict(X_val)
    rmse   = float(np.sqrt(mean_squared_error(y_val, y_pred)))
    r2     = float(r2_score(y_val, y_pred))
    return rmse, r2


def log_result(experiment_id, val_rmse, val_r2, status, description):
    file_exists = os.path.exists(RESULTS_FILE)
    with open(RESULTS_FILE, "a", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        if not file_exists:
            writer.writerow(["experiment", "val_rmse", "val_r2", "status", "description"])
        writer.writerow([experiment_id, f"{val_rmse:.6f}", f"{val_r2:.6f}", status, description])


def plot_results(save_path="performance.png"):
    if not os.path.exists(RESULTS_FILE):
        print("No results.tsv found.")
        return

    rmses, r2s, statuses, descriptions = [], [], [], []
    with open(RESULTS_FILE) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            try:
                rmse = float(row["val_rmse"])
                r2   = float(row["val_r2"])
                if rmse <= 0 or rmse > 10 or r2 > 1.0:
                    continue
                rmses.append(rmse)
                r2s.append(r2)
                statuses.append(row["status"])
                descriptions.append(row["description"])
            except (ValueError, KeyError):
                continue

    if not rmses:
        print("No valid results to plot.")
        return

    n = len(rmses)

    # Color based on ACTUAL running best
    running_best = []
    colors = []
    best = float("inf")
    for i, r in enumerate(rmses):
        if statuses[i] == "baseline":
            colors.append("#3498db")
            best = min(best, r)
        elif r < best:
            colors.append("#2ecc71")
            best = r
        else:
            colors.append("#e74c3c")
        running_best.append(best)

    valid_rmse = [r for r in rmses if r < 0.2]
    clip_max   = 0.19
    clip       = [min(r, clip_max) for r in rmses]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(max(14, n * 0.15), 9), sharex=True)

    ax1.scatter(range(n), clip, c=colors, s=55, zorder=3, edgecolors="white", linewidth=0.4)
    ax1.plot(range(n), clip, "k-", alpha=0.08, zorder=2, linewidth=0.7)
    ax1.plot(range(n), [min(rb, clip_max) for rb in running_best],
             color="#2ecc71", linewidth=2.5, zorder=4)

    for i, r in enumerate(rmses):
        if r > clip_max:
            ax1.annotate(f"{r:.3f}", xy=(i, clip_max * 0.995),
                         fontsize=7, ha="center", color="#e74c3c", fontweight="bold")

    best_val = min(valid_rmse)
    best_idx = next(i for i, r in enumerate(rmses) if r == best_val)
    y_range  = (max(valid_rmse) - min(valid_rmse)) or 0.01
    ax1.annotate(f"Best: {best_val:.5f}",
                 xy=(best_idx, best_val),
                 xytext=(max(0, best_idx - 6), best_val + y_range * 0.5),
                 fontsize=9, color="#27ae60", fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="#27ae60", lw=1.5))

    ax1.set_ylim(min(valid_rmse) * 0.975, max(valid_rmse) * 1.08)
    ax1.set_ylabel("Validation RMSE — no lag (lower = better)", fontsize=11)
    ax1.set_title(f"AutoResearch: Grocery Price Prediction  ({n} experiments)", fontsize=13, fontweight="bold")
    ax1.grid(True, alpha=0.25)

    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#3498db", markersize=9, label="baseline"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#2ecc71", markersize=9, label="genuine improvement"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#e74c3c", markersize=9, label="did not improve"),
        Line2D([0], [0], color="#2ecc71", linewidth=2.5, label="Running best"),
    ]
    ax1.legend(handles=legend_elements, loc="upper right", fontsize=9)

    r2_clip = [max(0, min(r, 1.0)) for r in r2s]
    ax2.scatter(range(n), r2_clip, c=colors, s=55, zorder=3, edgecolors="white", linewidth=0.4)
    ax2.plot(range(n), r2_clip, "k-", alpha=0.08, zorder=2, linewidth=0.7)
    r2_best, cb = [], -float("inf")
    for r in r2_clip:
        cb = max(cb, r)
        r2_best.append(cb)
    ax2.plot(range(n), r2_best, color="#2ecc71", linewidth=2.5)
    valid_r2 = [r for r in r2s if 0 <= r <= 1.0]
    if valid_r2:
        ax2.set_ylim(max(0, min(valid_r2) * 0.9995), min(1.0, max(valid_r2) * 1.0002))
    ax2.set_ylabel("Validation R² (higher = better)", fontsize=11)
    ax2.set_xlabel("Experiment #", fontsize=11)
    ax2.grid(True, alpha=0.25)

    step = max(1, n // 40)
    ax2.set_xticks(range(0, n, step))
    short_labels = [descriptions[i][:18] + ".." if len(descriptions[i]) > 20 else descriptions[i]
                    for i in range(0, n, step)]
    ax2.set_xticklabels(short_labels, rotation=45, ha="right", fontsize=7)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"Saved {save_path}  ({n} experiments, best RMSE: {best_val:.6f})")


if __name__ == "__main__":
    plot_results()
