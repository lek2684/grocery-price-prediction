# Week 4 Failure Analysis Memo
## Grocery Price Prediction — AutoResearch Capstone
**Date:** May 2026 | **GitHub:** https://github.com/lek2684/grocery-price-prediction

---

## Dominant Failure Mode: Signal Failure

Out of 8 controlled experiments this week, 7 were classified as **Signal Failure** —
the loop ran cleanly but produced no meaningful improvement. Only 1 experiment (n_estimators: 800→600)
produced a genuine improvement.

---

## What Is Signal Failure?

Signal failure means the loop is working correctly as an instrument — experiments
run, results are logged, keep/discard decisions are made automatically — but the
agent is not finding meaningful improvements. The model has largely converged.

This is different from a broken loop. The pipeline is healthy. The issue is that
we are near the optimum for this model family on this dataset.

---

## Evidence

**Controlled experiment results — Week 4:**

| Axis | Change | RMSE | vs Best | Decision |
|------|--------|------|---------|----------|
| n_estimators | 800→600 | 0.063802 | -0.000569 | ✅ keep |
| n_estimators | 800→1000 | 0.064834 | +0.001032 | ❌ discard |
| n_estimators | 800→1500 | 0.065546 | +0.001744 | ❌ discard |
| learning_rate | 0.01→0.005 | 0.070146 | +0.006344 | ❌ discard |
| learning_rate | 0.01→0.02 | 0.065478 | +0.001676 | ❌ discard |
| subsample | 0.6→0.5 | 0.064167 | +0.000365 | ❌ discard |
| subsample | 0.6→0.8 | 0.064167 | +0.000365 | ❌ discard |
| min_samples_leaf | 5→2 | 0.066423 | +0.002621 | ❌ discard |

**Key observation:** All four hyperparameter axes have been explored. The
current best (n=600, depth=3, lr=0.01, sub=0.6) is near the local optimum
for GradientBoosting on this feature set.

---

## Why Is This Happening?

Three compounding reasons:

**1. Synthetic data ceiling**
The training data was generated with controlled noise (σ ≈ 0.04 per week).
All models cluster near R²=0.9989 because the underlying signal is too clean.
RMSE differences of 0.001 may not be meaningful — they could be noise.

**2. Feature set is too small**
With only 4 features (week_idx, category_code, retailer_code, price_roll4),
GradientBoosting has limited structure to exploit. Hyperparameter tuning
helps marginally but cannot overcome limited input signal.

**3. Model family is saturated**
We have exhausted GradientBoosting's main hyperparameter axes. Further
tuning within this model family is unlikely to produce meaningful gains.

---

## Most Trusted Result

**n_estimators=600 (RMSE=0.063802)** is the most trusted result.

It was produced by a fully controlled experiment with one variable changed
(n_estimators: 800→600) and all others held fixed. The improvement was
consistent with a credible mechanism: fewer trees with this learning rate
may be better calibrated to the dataset size (580 training rows). The result
was not a one-off — it outperformed both n=1000 and n=1500 on the same axis.

---

## Most Distrusted Result

**HistGradientBoosting (RMSE=0.146, Week 3)** — nearly double the baseline.

This was not a controlled experiment. Multiple configuration changes were made
simultaneously, the model type changed, and the result was not reproducible.
It should be treated as a crash, not a data point.

---

## Error Taxonomy Summary

| Type | Count | Explanation |
|------|-------|-------------|
| Signal Failure | 7 | Loop runs but no improvement — model near optimum |
| Code Instability | 0 | No crashes this week |
| Evaluation Leakage | 0 | Evaluator remains frozen |
| Agent Misbehavior | 0 | Agent respected all boundaries |
| None (genuine improvement) | 1 | n_estimators=600 |

**Dominant error type: Signal Failure**

---

## Proposed Next Steps

**1. Add real features (highest priority)**
Switch from synthetic to real Kroger data and add BLS CPI features as inputs.
More signal in the features = more for the model to learn from = larger RMSE
differences between experiments.

**2. Target price changes instead of price levels**
Currently predicting absolute price. Predicting week-over-week price change
(Δprice) instead would make the residuals more interpretable for gap analysis
and give the model a harder, more meaningful task.

**3. Try a different model family**
GradientBoosting is saturated on this feature set. XGBoost or a simple
time-series model (ARIMA-based) may perform differently and reveal new signal.

**4. Lock the final model and begin gap analysis**
The current best (n=600, depth=3, lr=0.01, sub=0.6, RMSE=0.063802) is likely
the best achievable on synthetic data. Lock it and shift focus to the residual
analysis — which is the actual research question.
