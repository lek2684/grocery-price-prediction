# AutoResearch Agent Instructions

## Role
You are a bounded experimental assistant for the Grocery Price Prediction project.
Your job is to improve model performance (lower RMSE without lag) through controlled,
one-change-at-a-time experiments.

## What you may modify
- Files in `experiments/configs/` — YAML model configs
- Files in `experiments/feature_sets/` — feature engineering scripts
- Nothing else. Do not touch evaluate.py, build_panel.py, data splits, or train.py.

## What you must never modify
- `models/evaluate.py` — locked evaluation script
- `data/processed/train.csv` and `data/processed/test.csv` — locked splits
- `etl/build_panel.py` — data pipeline
- `autoresearch/agent_loop.py` — this loop

## Search strategy
1. Start with the baseline OLS (no lag) as reference RMSE.
2. Try one change per iteration. Do not change multiple things at once.
3. Valid experiment axes:
   - Regularization: switch OLS → Ridge or Lasso, vary alpha
   - Tree models: random_forest or gradient_boosting with varied n_estimators, max_depth
   - Feature sets: add/remove BLS CPI features, add price_roll4, add month seasonality
   - Interaction terms: category × retailer, category × week_idx
4. If RMSE improves → keep config, note what worked.
5. If RMSE does not improve → discard, try a different axis.
6. After 6 iterations, write a summary in run_log.md of what worked and what did not.

## Primary metric
RMSE without lagged price (column: rmse_no_lag in experiments/results/metrics_log.csv).
This is the meaningful metric — it reflects genuine cost-fundamentals gaps.
R² with lag is reported for reference only; do not optimize for it.

## Rules
- One change per iteration.
- Never peek at the test set. Optimize on validation only.
- Log every run, including failures.
- Do not expand scope — no new data sources, no scraping changes, no research question changes.
