# Week 3 Reflection: First AutoResearch Loop

## Dry-run experiment results

| Run | Model | RMSE (no lag) | R² (no lag) | MAE (no lag) |
|-----|-------|--------------|-------------|--------------|
| baseline_ols | OLS | 0.0812 | 0.9983 | 0.0540 |
| exp1_ridge_a1 | Ridge α=1.0 | 0.0812 | 0.9983 | 0.0540 |
| exp2_ridge_a10 | Ridge α=10.0 | 0.0812 | 0.9983 | 0.0540 |
| exp3_lasso_a001 | Lasso α=0.01 | 0.0812 | 0.9983 | 0.0540 |
| exp4_rf | Random Forest | 0.0812 | 0.9983 | 0.0540 |
| exp5_ols_with_lag | OLS + lag | 0.0812 | 0.9983 | 0.0540 |

## What the agent did well

- The loop ran cleanly end-to-end for all 5 experiments without crashes
- Each run was logged automatically to metrics_log.csv
- The keep/discard logic worked correctly — no experiment improved on baseline
- evaluate.py correctly reported both with-lag and without-lag metrics every time

## What the agent did badly / failure modes observed

1. **No differentiation on synthetic data** — all experiments returned identical RMSE
   because the synthetic data has uniform noise structure. The agent cannot learn
   anything meaningful until real scraped data is available.

2. **No feature variance** — with only 4 features (week_idx, category_code,
   retailer_code, price_roll4), regularization (Ridge/Lasso) has nothing meaningful
   to penalize. All models collapse to the same solution.

3. **Agent cannot yet distinguish signal from noise** — on synthetic data every
   model looks equally good, which means the loop produces no useful search signal.

## Most common failure modes so far

- **Data quality bottleneck**: the loop is ready but the data is synthetic.
  Real scraped prices will introduce genuine variance across retailers and products,
  which will make model selection and feature engineering meaningful.
- **Feature space too small**: need to add BLS CPI/PPI features as covariates
  before the agent can find meaningful improvements.

## What needs to happen before the loop becomes meaningful

1. Real scraped data from Kroger and Walmart APIs
2. BLS CPI/PPI joined to panel as numeric features
3. At least 4–8 weeks of real price observations
4. Then rerun all 5 experiments — RMSE will diverge and agent search becomes real

## Agent boundary confirmed

- Agent writes only to: experiments/configs/, experiments/results/
- Agent does NOT touch: evaluate.py, build_panel.py, data splits, train.py
- This boundary held correctly across all 5 dry runs
