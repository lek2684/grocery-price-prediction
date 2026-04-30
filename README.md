# Grocery Price Prediction

**Research question:** Do retail grocery prices track observable cost fundamentals, or did prices rise beyond what public CPI/PPI data would predict?

**Data:** Kroger (official API) + BLS national average prices (~10 staple items) + BLS CPI/PPI + USDA Food Price Outlook  
**Method:** OLS baseline → Ridge/Lasso → Random Forest → GradientBoosting; gap analysis on residuals  
**Metric:** RMSE without lagged price on held-out test set (time-based forward-chaining split)  
**Success criterion:** R² ≥ 0.70 on test data; at least one statistically interpretable residual pattern

**Current best result:** RMSE = 0.064371 — GradientBoosting (n=800, depth=3, lr=0.01, sub=0.6) after 20 experiments

---

## Setup

```bash
pip install -r requirements.txt
```

## Running the pipeline

```bash
# 1. Collect real prices (run weekly)
$env:KROGER_CLIENT_ID="your_client_id"
$env:KROGER_CLIENT_SECRET="your_client_secret"
python scraper/scraper.py

# 2. Pull BLS and USDA public data
python etl/ingest_bls.py
python etl/ingest_usda.py

# 3. Build the merged panel and train/test split
python etl/build_panel.py

# 4. Train baseline model
python models/train.py baseline

# 5. Evaluate (locked script)
python models/evaluate.py --run-id baseline_ols

# 6. Run AutoResearch loop (6 iterations)
python autoresearch_auto.py 6
```

## AutoResearch Loop

The agent iterates automatically — trying one model change at a time, keeping improvements, reverting failures.

```
python autoresearch_auto.py 6
```

Output example:
```
Iteration 1/6: Ridge alpha=0.1       ❌ discard  RMSE: 0.070253
Iteration 2/6: Ridge alpha=5.0       ❌ discard  RMSE: 0.070253
Iteration 3/6: GBT n=1000 lr=0.008  ❌ discard  RMSE: 0.066256
Iteration 4/6: GBT n=800 depth=3    ✅ keep     RMSE: 0.064371  ← new best
Iteration 5/6: GBT n=800 depth=5    ❌ discard  RMSE: 0.069796
Iteration 6/6: RandomForest n=500   ❌ discard  RMSE: 0.071619
```

## Experiment history

| Week | Experiments | Best RMSE | Best model |
|------|-------------|-----------|------------|
| 2 | 1 (baseline) | 0.070276 | OLS LinearRegression |
| 3 | 20 total | **0.064371** | GBT n=800 depth=3 lr=0.01 sub=0.6 |

Total improvement over baseline: **8.4%**

## Key design decisions

**Time-based split:** Train on earlier weeks, test on later weeks. Random splits are banned — grocery prices are autocorrelated and random splits leak future data into training, inflating R².

**Dual RMSE reporting:** Results reported both with and without lagged price. With lag, R² is trivially high because prices are sticky week-to-week. Without lag, residuals show where prices diverged from cost fundamentals — the actual research question. We optimize on RMSE without lag.

**Locked evaluator:** evaluate.py cannot be modified by the agent. Every experiment is measured identically.

**Agent boundary:** Agent writes only to experiments/ and model.py. Cannot touch data, splits, evaluator, or scraper.

## Data sources

| Source | Type | Status |
|--------|------|--------|
| Kroger Developer API | Real retail prices | ✅ Live |
| BLS Average Prices | National avg prices | ✅ Live |
| BLS CPI/PPI | Cost fundamentals | ✅ Live |
| USDA Food Price Outlook | Forecasts | ⬜ Pending |

## Repository structure

```
grocery-price-prediction/
├── README.md
├── requirements.txt
├── autoresearch_auto.py          ← AutoResearch loop runner
├── performance.png               ← Experiment history chart
├── data/
│   ├── raw/scraped/              ← Kroger + BLS weekly price CSVs
│   ├── raw/bls/                  ← BLS CPI/PPI data
│   ├── processed/
│   │   ├── panel.csv             ← Merged panel
│   │   ├── train.csv             ← Training set (time-based)
│   │   └── test.csv              ← Held-out test set (locked)
│   └── canonical_products.csv
├── scraper/
│   ├── scraper.py
│   └── retailers/
│       ├── retailer_kroger.py    ← Kroger official API
│       └── retailer_bls.py      ← BLS national averages
├── etl/
│   ├── ingest_bls.py
│   ├── ingest_usda.py
│   └── build_panel.py
├── models/
│   ├── train.py
│   └── evaluate.py               ← LOCKED — do not modify
├── experiments/
│   └── results/metrics_log.csv
├── autoresearch/
│   ├── program.md                ← Agent instructions
│   └── run_log.md
└── reports/
    └── charter.md
```
