# AutoResearch Agent Instructions — Grocery Price Prediction

## Your Role
You are a bounded experimental assistant. Your job is to minimize `val_rmse`
on the grocery price prediction task by making one change at a time to `model.py`.

## What You May Modify
- `model.py` — the ONLY file you are allowed to edit

## What You Must NEVER Modify
- `prepare.py` — frozen data loading, evaluation, and plotting
- `run.py` — frozen experiment runner
- `results.tsv` — append-only log, never edit manually
- `train.csv` / `test.csv` — locked data splits

## The Loop (repeat ≥ 6 times)
1. Read this file and `model.py`
2. Propose ONE change to `model.py` (one idea at a time)
3. Edit `model.py` with your change
4. Run: `python run.py "<short description>"`
5. Compare new `val_rmse` to current best
   - If improved → KEEP, note new best
   - If worse → REVERT `model.py` to previous version, log as discard
6. Repeat

## Primary Metric
`val_rmse` (validation RMSE without lagged price) — lower is better.
This is the meaningful metric — it shows whether prices deviate from cost fundamentals.

## Search Strategy (follow this order)
1. Baseline: LinearRegression (no lag features)
2. Regularized linear: Ridge, Lasso — try alpha values 0.1, 1.0, 10.0
3. Feature engineering: add BLS CPI interaction terms, month seasonality
4. Tree models: RandomForest (n_estimators=100, 200), GradientBoosting
5. Hyperparameter tuning: tune the best model found so far

## Rules
- ONE change per iteration — never change model type AND hyperparameters at the same time
- Never peek at test.csv — optimize on validation only
- Log every run including failures and discards
- Do not change the research question or data pipeline
- Each run must complete in under 60 seconds
