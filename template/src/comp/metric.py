"""The competition score.

`score` returns a dict with "score" (the number the leaderboard shows) and,
optionally, parts of it. A competition whose score averages several parts
(per target, per kind of row) should report each part too: a change often
helps one part and hurts another.

If the competition uses its own metric, replace `headline` and set
[task] metric and lower_is_better in comp.toml.
"""

import numpy as np
import pandas as pd
from sklearn import metrics

from comp import config


def headline(truth: np.ndarray, prediction: np.ndarray, name: str) -> float:
    """The competition metric by name. Probabilities for auc and logloss."""
    if name == "rmse":
        return float(np.sqrt(metrics.mean_squared_error(truth, prediction)))
    if name == "mae":
        return float(metrics.mean_absolute_error(truth, prediction))
    if name == "rmsle":
        return float(np.sqrt(metrics.mean_squared_log_error(truth, np.maximum(prediction, 0))))
    if name == "mape":
        return float(metrics.mean_absolute_percentage_error(truth, prediction))
    if name == "r2":
        return float(metrics.r2_score(truth, prediction))
    if name == "auc":
        return float(metrics.roc_auc_score(truth, prediction))
    if name == "logloss":
        return float(metrics.log_loss(truth, prediction))
    if name == "accuracy":
        return float(metrics.accuracy_score(truth, prediction))
    if name == "f1":
        return float(metrics.f1_score(truth, prediction, average="macro"))
    raise ValueError(f"unknown metric {name!r}: write it in metric.py")


def score(truth: pd.Series, prediction: pd.Series) -> dict[str, float]:
    """Score `prediction` against `truth`, both indexed by id. Returns {"score": ...}."""
    prediction = prediction.reindex(truth.index)
    if prediction.isna().any():
        bad = prediction.index[prediction.isna()][:5].tolist()
        raise ValueError(f"prediction is missing for ids such as {bad}")
    value = headline(truth.to_numpy(), prediction.to_numpy(), config.load().metric)
    return {"score": value}
