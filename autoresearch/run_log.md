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
