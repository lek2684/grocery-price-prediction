# STAT 390 Capstone — Week 2 Check-In

**Submitted:** [insert submission date]

---

## Project title
Grocery Price Prediction: Do retail grocery prices track observable cost fundamentals?

---

## This week's goal
Set up the GitHub repository, rebuild the development environment on a new machine,
pull the first BLS/USDA data batch, and establish a reproducible end-to-end baseline pipeline.

---

## What I completed

My laptop failed mid-week and I lost my local environment. I am starting fresh on a new machine.

Despite this, I have completed the following:

- Full repository structure created matching the Week 1 charter
- `README.md` with one-sentence problem, data, method, metric, and run instructions
- `etl/ingest_bls.py` — pulls CPI, PPI, and average price series from BLS public API
- `etl/ingest_usda.py` — downloads USDA Food Price Outlook data
- `etl/build_panel.py` — merges scraped + BLS data into item–retailer–date panel
- `models/train.py` — unified training script (OLS, Ridge, Lasso, RF, XGBoost)
- `models/evaluate.py` — **locked** evaluation script, reports MAE/RMSE/R² both with and without lagged price
- `scraper/scraper.py`, `utils.py`, `retailer_a.py`, `retailer_b.py` — scraper scaffold
- `autoresearch/program.md` — agent instruction file with search strategy and rules
- `autoresearch/agent_loop.py` — run → evaluate → compare → keep/discard loop
- `data/canonical_products.csv` — product name mapping table
- `experiments/results/metrics_log.csv` — initialized, ready to receive baseline run
- `reports/charter.md` — full project charter with incorporated Week 1 feedback

**Key design changes incorporated from Week 1 feedback:**

1. **Time-based forward-chaining split** (not random). `build_panel.py` trains on earlier
   weeks and tests on later weeks. Random splits are explicitly blocked in code comments.

2. **Dual metric reporting** — `evaluate.py` reports results both with and without lagged
   price as a feature. The primary optimization target is `rmse_no_lag`, which captures
   genuine cost-fundamentals gaps rather than week-to-week price stickiness.

---

## One key artifact

GitHub repository: **[INSERT GITHUB URL HERE]**

Repository contains the full structure above. The `evaluate.py` script is locked and
version-controlled separately from the agent-writable `experiments/` directory.

---

## Biggest blocker

Laptop failure wiped the local environment. The scraper modules (`retailer_a.py`,
`retailer_b.py`) are scaffolded but not yet implemented with real retailer URLs —
this is the primary remaining task before data collection can begin.

The baseline pipeline cannot produce a real RMSE until the first scraped data batch
is collected. I am targeting first data by [INSERT DATE].

---

## Plan for next week

1. Implement `retailer_a.py` and `retailer_b.py` with real scraping logic for 2 retailers
2. Run `ingest_bls.py` and `ingest_usda.py` to pull public data
3. Collect first scraped batch and run `build_panel.py` end-to-end
4. Run `train.py baseline` + `evaluate.py` to establish baseline RMSE (with and without lag)
5. Commit first entry to `experiments/results/metrics_log.csv`
6. Measure and record runtime per iteration
7. Submit GitHub URL with all of the above committed

---

## Help needed from instructor / TA

Given the laptop failure, I am behind on the Week 2 reproducibility gate. I have
built the full pipeline scaffold and incorporated all Week 1 feedback into the code.
The missing piece is real data, which requires the scraper to be live.

**Request:** Can I receive a Yellow status while I catch up on the first data batch
and baseline run? I will have a working end-to-end run with a real RMSE logged by
[INSERT TARGET DATE].

I would also appreciate TA guidance on: preferred format for the experiment log, and
whether BLS average price data (already in `ingest_bls.py`) counts as a substitute
for scraped prices during the first week of data collection.

---

## GitHub URL

[INSERT GITHUB URL — to be created and submitted this week]
