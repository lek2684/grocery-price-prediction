# Grocery Price Prediction

**Research question:** Do retail grocery prices track observable cost fundamentals, or did prices rise beyond what public CPI/PPI data would predict?

**Data:** Scraped retail prices (~10 staple items, 2–4 U.S. retailers) + BLS CPI/PPI + USDA Food Price Outlook  
**Method:** OLS baseline → Ridge/Lasso → Random Forest → XGBoost; gap analysis on residuals  
**Metric:** RMSE, MAE, R² on held-out test set (time-based forward-chaining split)  
**Success criterion:** R² ≥ 0.70 on test data; at least one statistically interpretable residual pattern

**Current best result:** _Baseline not yet established (Week 2 in progress)_

---

## Setup

```bash
pip install -r requirements.txt
```

## Running the pipeline

```bash
# 1. Pull BLS and USDA data
python etl/ingest_bls.py
python etl/ingest_usda.py

# 2. Build the merged panel
python etl/build_panel.py

# 3. Run baseline model
python models/train.py baseline

# 4. Evaluate
python models/evaluate.py
```

## Repository structure

```
grocery-price-prediction/
├── data/
│   ├── raw/scraped/        # Raw scrape output CSVs
│   ├── raw/bls/            # BLS CPI, PPI, avg-price files
│   ├── raw/usda/           # USDA Food Price Outlook CSVs
│   ├── processed/
│   │   ├── panel.csv       # Merged item–retailer–date panel
│   │   └── features.csv    # Engineered feature matrix
│   └── canonical_products.csv
├── scraper/                # Scraping scripts
├── etl/                    # Data ingestion and merging
├── notebooks/              # EDA and model notebooks
├── models/                 # Training and evaluation scripts
├── experiments/            # Agent-writable zone only
├── autoresearch/           # AutoResearch loop
└── reports/                # Charter, gap analysis, final report
```

## Key design decisions (per Week 1 feedback)

- **Time-based split only:** Forward-chaining train/test split. Prices are autocorrelated — random splits leak future info and inflate R². Train on earlier weeks, test on later weeks.
- **Dual reporting on lagged price:** Results reported both with and without lagged price as a feature. With lagged price, R² ≥ 0.70 is trivial (prices are sticky). Without it, residuals reflect genuine cost-fundamentals gaps — the actual research question.
