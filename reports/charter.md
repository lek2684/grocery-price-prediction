# Project Charter: Grocery Price Prediction

## Research Question

Do retail grocery prices track observable cost fundamentals, or did prices rise beyond what public CPI/PPI data would predict?

## Scope

- **Basket:** ~10 staple items (milk, eggs, bread, bananas, chicken, ground beef, cereal, pasta, rice, canned vegetables)
- **Retailers:** 2–4 major U.S. retailers (subject to scraping feasibility)
- **Time horizon:** Rolling panel collected weekly during the project quarter
- **Geography:** U.S. national level

## Data Sources

| Source | Data | URL |
|--------|------|-----|
| Web scraping (self-built) | Retail prices by item, retailer, date | — |
| BLS CPI | Food-at-home inflation, grocery subcategories | bls.gov/cpi |
| BLS Avg Prices | Unit prices for ~70 food items | bls.gov/charts/cpi/avg-price-data |
| BLS PPI | Upstream producer cost pressure | bls.gov/ppi |
| USDA Food Price Outlook | Historical CPI/PPI-based forecasts | ers.usda.gov/data-products/food-price-outlook |

**Schema (scraped):** `product_name`, `brand`, `package_size`, `price`, `unit_price`, `retailer`, `scrape_date`, `category`  
**Format:** CSV, one row per item–retailer–date observation

## Analytical Approach

1. **EDA** — price trends over time, category and retailer comparisons, basket vs. CPI-food-at-home
2. **Baseline model** — OLS regression: time + category + retailer + lagged price + CPI/PPI indicators
3. **Advanced models** — regularized regression (Ridge/Lasso), random forest, gradient boosting / XGBoost
4. **Gap analysis** — use residuals to identify periods or categories with prices above model predictions

## Success Criterion

R² ≥ 0.70 on held-out test data **and** the residual gap analysis surfaces at least one statistically interpretable pattern (e.g., a product category or time window where retail prices appear systematically elevated beyond cost fundamentals).

**Evaluation metrics:** MAE, RMSE, R²

## Key Design Decisions (incorporating Week 1 feedback)

### Time-based train/test split
Random train/test splits must NOT be used. Price panels are strongly autocorrelated — random splits leak future information into training and inflate R². The pipeline uses a **forward-chaining split**: train on earlier weeks, test on later weeks.

### Dual lagged-price reporting
Lagged price dominates R² because prices are sticky week-to-week. A model including lagged price will trivially reach R² ≥ 0.70 but residuals only reflect short-term deviations, not the "priced beyond fundamentals" gap the research question cares about. Results are reported **both with and without lagged price** as a feature, or the model targets price changes (Δprice) instead of levels.

## AutoResearch Agent Role

The agent acts as a bounded experimental assistant:
- **Fixed inputs:** dataset, train/test split, evaluation script
- **Allowed modifications:** feature engineering, preprocessing, model selection, hyperparameters
- **Loop:** run → evaluate (MAE/RMSE/R²) → compare to current best → keep if improved → iterate
- **Not in scope for agent:** data collection, research question definition, scraping logic

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Retailer blocks scraping | Medium | Start with 2 retailers; rotate user-agent; use polite crawl delays |
| Inconsistent product naming across retailers | High | Canonical product map; fuzzy matching on brand + size |
| BLS/USDA data lags scraping by 1–4 weeks | Low | Align time series on release date, not observation date |
| Too few observations for robust modeling | Medium | Scrape weekly from day 1; maintain imputed history using BLS avg prices |
| Agent makes out-of-scope changes to codebase | Low | Version-lock data ingestion and eval scripts; agent writes only to experiments/ |

## Timeline

| Week | Milestone |
|------|-----------|
| 1 | Charter, repo structure, scraping prototype |
| 2 | Scraper live, first data batch, BLS/USDA pulls |
| 3 | EDA complete, baseline model trained |
| 4 | Advanced models, AutoResearch loop initialized |
| 5–6 | Iterative model improvement via agent |
| 7 | Gap analysis, residual interpretation |
| 8 | Final report, repo cleanup, presentation |
