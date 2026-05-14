# AutoResearch Agent Instructions — Grocery Price Prediction

## Your Role

You are a bounded AutoResearch agent for the grocery price prediction project.

Your job is to minimize `val_rmse` by making controlled, interpretable changes to `model.py`.

This is not a leaderboard task. The goal is a trustworthy research trace: complete logs, comparable experiments, clear keep/discard decisions, and clear rollback logic.

## Primary Metric

The primary metric is `val_rmse` — validation RMSE without lagged price.

Lower is better.

Use validation RMSE only. Never optimize on `test.csv`.

## What You May Modify

You may modify only:

- `model.py`

`model.py` must define a valid `build_model()` function that returns a sklearn-compatible estimator or pipeline.

## What You Must Never Modify

Do not edit:

- `prepare.py` — frozen data loading, validation split, evaluation, and plotting
- `run.py` — frozen experiment runner
- `results.tsv` — append-only log, never edit manually
- `train.csv` — locked training data
- `test.csv` — locked test data

`results.tsv` should only change when `python run.py "<description>"` is executed.

## Autonomous Block Length

Run exactly 5 iterations unless the user explicitly gives a different number.

Do not continue beyond the requested number of iterations.

Do not ask the user what to try next.

Do not ask for approval between iterations.

If unsure, choose the most conservative interpretable experiment and continue.

## Required Loop

For each iteration:

1. Read `results.tsv` and identify the current best `val_rmse`.
2. Read the current `model.py`.
3. Choose one interpretable experiment idea.
4. Edit `model.py`.
5. Run:

   `python run.py "<short description>"`

6. Compare the new `val_rmse` to the previous best.
7. If improved, keep the new `model.py`.
8. If not improved, revert `model.py` to the previous best version.
9. Classify the run as `keep`, `discard`, or `crash`.
10. Continue until exactly 5 iterations are complete.

## Experiment Discipline

Change one interpretable idea per iteration.

Acceptable experiment ideas include:

- Change one hyperparameter
- Change one model family
- Change one loss function
- Add one preprocessing step
- Add one feature transformation inside the model pipeline

Avoid changing several unrelated things at once.

If multiple code details change, they must belong to one clear experiment idea.

## Search Strategy

Follow this general order unless results strongly suggest a better next step:

1. Confirm the current best model from `results.tsv`.
2. Try small controlled variations around the current best.
3. If tuning no longer helps, try a different model family.
4. If model-family changes fail, try one pipeline or feature-engineering change.
5. Stop after the requested block length and summarize the trace.

## Rollback Rules

Before editing `model.py`, preserve the current best version.

If the new run does not beat the current best `val_rmse`, restore the previous best `model.py`.

A discarded run should still remain in `results.tsv` through the normal `run.py` logging process.

## Crash Rules

If a run crashes:

1. Record it as a crash in the final summary.
2. Revert `model.py` to the previous best version.
3. Continue to the next iteration if the block is not complete.

Do not repeatedly try the same crashing idea.

## End-of-Block Summary

After the autonomous block, print a concise Week 5 summary with:

- Block length
- Baseline RMSE
- Starting best RMSE
- Final best RMSE
- Keep / discard / crash counts
- Most helpful modification type
- Most common failed modification type
- What actually worked
- Biggest uncertainty
- Whether the improvement appears real or possibly accidental

Then stop.