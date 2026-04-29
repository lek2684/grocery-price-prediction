# AutoResearch Run Log

Human-readable history of all agent experiment iterations.
Each entry records what was tried, the RMSE outcome, and whether the change was kept.

---

## Baseline — Week 2

- Model: OLS regression
- Features (no lag): week_idx, category_code, retailer_code, price_roll4
- Features (with lag): + price_lag1
- Status: Not yet run — awaiting first data batch and panel build
- Target RMSE (no lag): TBD after baseline run

---

_Agent iterations will be logged here automatically by agent_loop.py_

## baseline_ols — Week 2

- Model: OLS regression
- Features with lag: week_idx, category_code, retailer_code, price_lag1, price_roll4
- Features without lag: week_idx, category_code, retailer_code, price_roll4
- Train: 820 rows (2024-01-01 → 2024-10-07)
- Test:  220 rows (2024-10-14 → 2024-12-23) — time-based forward-chaining split
- Data: synthetic panel (10 products × 2 retailers × 52 weeks)
- Runtime: ~12 seconds per full pipeline run

| Metric | With lag | Without lag |
|--------|----------|-------------|
| MAE    | 0.0539   | 0.0540      |
| RMSE   | 0.0811   | 0.0812      |
| R²     | 0.9983   | 0.9983      |

Note: R² is high because synthetic data has low noise by design.
Primary target metric going forward: rmse_no_lag (currently 0.0812).
Next step: implement real scraper and re-establish baseline on real data.
