---
name: blend
description: Combine the predictions of two or more experiments in a bench competition repo into one experiment, with mix weights chosen on out-of-fold predictions and confirmed on CV and the shadow test. Use near the end of a competition, or when two good experiments differ in method.
---

# Blend experiments

A blend averages the predictions of several models. It helps when the models make different mistakes, so blend experiments that differ in method, not near copies of one another. It is the classical-ML idea of an ensemble.

Commands: this skill shows the template's defaults (`uv run comp run`, `uv run comp compare`, and so on). If `comp.toml` has a `[commands]` table, use the commands named there instead, and do any step without a command by hand.

## 1. Pick the members

Two to four experiments that are each good on CV and shadow, and that differ in method. Check how different they are first: load their out-of-fold predictions and compute the correlation of their errors.

```python
from comp import tracking
runs = tracking.latest_runs()
run_id = runs[runs["tags.mlflow.runName"] == "<experiment stem>"].iloc[0]["run_id"]
oof = tracking.load_oof(run_id)   # seed, fold, id, truth, prediction
```

Errors correlated above about 0.95 mean the blend will barely help. If a repo has no `oof.csv` (an older harness), rerun the members' CV and save their held-out predictions yourself.

## 2. Choose the weights on the out-of-fold predictions

Join the members' out-of-fold predictions on `seed`, `fold` and `id`, and score a few weightings with the competition metric: equal weights first, then a small grid (steps of 0.1). Prefer equal weights unless another weighting is better by more than twice the noise: weights fitted on the same rows overfit them.

If the score has parts (kinds of rows, targets), a weight per part is allowed, but each extra weight is another chance to overfit. Write down why each one is needed.

## 3. Make it an experiment

Write the blend as the next experiment number: its `solve(task)` calls each member's `solve(task)` and mixes the predictions with the fixed weights. Load the members with `importlib`, the way `comp run` does, so the blend runs the exact committed code. Put the weights and the member names in `PARAMS`.

Run it like any experiment. Keep it only if CV and shadow both beat the best member by more than twice the noise, and log it in `experiments.md` either way.

## 4. Check for leaks

A blend can't fix a leak in a member, and it can hide one. Ask the `bench:leak-auditor` agent to read every member before the blend is submitted.
