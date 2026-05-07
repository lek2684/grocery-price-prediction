# Grocery Price Prediction

**Research question:** Do retail grocery prices track observable cost fundamentals, or did prices rise beyond what public CPI/PPI data would predict?

**Data:** Kroger (official API) + BLS national average prices + BLS CPI/PPI
**Method:** OLS baseline -> Ridge/Lasso -> Random Forest -> GradientBoosting; gap analysis on residuals
**Metric:** RMSE without lagged price (time-based forward-chaining split)
**Current best result:** RMSE = 0.063802 -- GradientBoosting (n=600, depth=3, lr=0.01, sub=0.6) after 29 experiments

## Run the AutoResearch agent
cd week3_clean
python autoresearch_agent.py 8

## Weekly scrape
python scraper/scraper.py

## GitHub
https://github.com/lek2684/grocery-price-prediction
