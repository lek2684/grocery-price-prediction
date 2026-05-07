# STAT 390 Capstone — Week 3 Assignment
**Grocery Price Prediction**
**GitHub:** https://github.com/lek2684/grocery-price-prediction

---

## Deliverable 1: program.md (Agent Instruction File)

The full `program.md` is in the repo. Summary of key rules:

- Agent may ONLY modify `model.py`
- Frozen files: `prepare.py`, `run.py`, `results.tsv`, `train.csv`, `test.csv`
- Primary metric: `val_rmse` without lagged price — lower is better
- One change per iteration, minimum 6 iterations
- If RMSE improves → keep. If not → revert `model.py` and log as discard
- Search order: linear → regularized → tree models → hyperparameter tuning

---

## Deliverable 2: Dry-Run Experiments (14 completed)

| # | Model | val_rmse | val_r2 | Decision |
|---|-------|----------|--------|----------|
| 0 | LinearRegression (baseline) | 0.070276 | 0.9987 | baseline |
| 1 | Ridge α=1.0 | 0.070124 | 0.9987 | keep |
| 2 | RandomForest n=100 | 0.077503 | 0.9984 | keep |
| 3 | GBT n=200 depth=4 lr=0.05 | 0.067889 | 0.9988 | keep |
| 4 | Lasso α=0.01 | 0.067255 | 0.9988 | discard |
| 5 | GBT n=400 depth=3 lr=0.03 sub=0.8 | 0.069107 | 0.9988 | keep |
| 6 | HistGradientBoosting iter=300 | 0.146272 | 0.9944 | keep |
| 7 | PolyFeatures degree=2 + Ridge | 0.071350 | 0.9987 | keep |
| 8 | ExtraTrees n=200 | 0.082224 | 0.9982 | keep |
| 9 | Ridge α=0.01 | 0.070274 | 0.9987 | keep |
| 10 | GBT n=300 depth=4 lr=0.04 sub=0.7 | 0.066561 | 0.9988 | keep |
| 11 | GBT n=500 depth=4 lr=0.02 sub=0.7 | 0.066292 | 0.9989 | keep |
| 12 | ElasticNet α=0.001 l1=0.5 | 0.069842 | 0.9987 | discard |
| 13 | RandomForest n=300 depth=10 leaf=3 | 0.070389 | 0.9987 | keep |
| 14 | GBT n=800 depth=4 lr=0.01 sub=0.7 | 0.066148 | 0.9989 | keep ✓ BEST |

**Baseline RMSE:** 0.070276
**Best RMSE:** 0.066148 (GBT n=800, depth=4, lr=0.01, sub=0.7)
**Total improvement:** 5.9% reduction over baseline

See `performance.png` for the full RMSE trajectory chart.

---

## Deliverable 3: Reflection — What the Agent Did Well and Badly

### What went well

**The one-change-at-a-time discipline made results interpretable.**
Every run produced a number that was directly comparable to the previous best.
When GradientBoosting beat Ridge it was obvious why — tree models capture
non-linear interactions between category, retailer, and time trend that linear
models cannot. The frozen evaluator made this comparison trustworthy because
every experiment was measured identically.

**GradientBoosting consistently improved with tuning.**
The best model (GBT n=800, lr=0.01, sub=0.7) emerged through a clear
progression: n=200 → n=300 → n=500 → n=800, each time nudging RMSE lower.
This is exactly how a real AutoResearch loop should behave — systematic
exploration of one axis at a time.

**The frozen evaluator prevented cheating.**
Because `prepare.py` cannot be touched, every experiment was measured on the
same validation split with the same metric. There was no way to accidentally
or deliberately evaluate on different data to make a model look better.

### What went badly

**RandomForest underperformed linear models.**
RMSE went from 0.0701 (Ridge) to 0.0775 (RandomForest n=100) — a step
backward. With only 4 features and smooth synthetic data, the tree model
had too little structure to work with. On real scraped data with genuine
price variation and retailer-specific patterns, RandomForest may perform better.

**HistGradientBoosting crashed badly (RMSE = 0.146).**
This was the worst result of all experiments — nearly double the baseline.
The likely cause: HistGradientBoosting uses a different internal binning
strategy that doesn't work well with the current small feature set and
smooth data. This should have been immediately discarded but was logged
as keep due to manual status setting.

**Lasso was discarded despite having a competitive RMSE (0.0673).**
Lasso was run out of order after GradientBoosting had already established
a better baseline. In a true autonomous loop, the agent would re-read
results.tsv before each run and compare against the global best, not
just the previous experiment. This was a process failure.

**The agent has no memory between runs.**
Each experiment is stateless. The agent doesn't remember what it tried
before unless it explicitly reads results.tsv. A more robust loop would
summarize past experiments at the start of each iteration and use that
to guide the next proposal.

---

## Deliverable 4: Common Failure Modes

**1. Comparing to previous run instead of global best**
The biggest process failure. The loop compared each new result to the
immediately prior run, not the best result ever recorded. Fix: always
read `min(val_rmse)` from results.tsv before deciding keep or discard.

**2. Manual status assignment**
`--baseline`, `--keep`, `--discard` were set manually before seeing results.
A better design runs the experiment first, compares automatically, and
writes status post-hoc. The `autoresearch_loop.py` script now does this.

**3. Tree models underperform on smooth synthetic data**
RandomForest and ExtraTrees both performed worse than Ridge on this dataset.
Synthetic data has low noise by design. On real scraped Kroger prices with
genuine week-to-week variation, tree models should perform better.

**4. No automatic revert logic**
When an experiment was discarded, model.py was not automatically restored.
Fixed in `autoresearch_loop.py` — it now backs up model.py before each
experiment and restores it automatically on discard or crash.

**5. Synthetic data ceiling**
All experiments cluster around R² = 0.9987-0.9989. Differences between
models are real but small (0.066 vs 0.077). On real Kroger + BLS data
the model differences will be larger and more meaningful.

**Note:** First real data collection completed this week —
10 Kroger products + 8 BLS national average prices collected
2026-04-29 and committed to GitHub.

---

## How to Run the AutoResearch Loop in VS Code

```bash
# Set Kroger credentials (every new terminal session)
$env:KROGER_CLIENT_ID="grocerypriceresearch-bbcdy6df"
$env:KROGER_CLIENT_SECRET="xxQO-ScQaW3VHkXlOyJml89JS-cdQtzRpd0agGvz"

# Run the interactive AutoResearch loop
cd week3
python autoresearch_loop.py
```

The loop will:
1. Show current best RMSE
2. Let you edit model.py with a new experiment
3. Run and evaluate automatically
4. Keep if improved, revert if not
5. Update performance.png after every run

## GitHub URL
https://github.com/lek2684/grocery-price-prediction
