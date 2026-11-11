"""The second check: a holdout built to look like the real test, not like the training set.

Cross-validation can be fooled when the test differs from the training rows
in a way the folds do not copy (later dates, new groups, a different mix).
In the competition this harness came from, a model scored 0.821 in CV and
1.022 on the leaderboard for exactly this reason. The shadow test is the
guard: keep a change only if it helps in CV *and* here.

Default, chosen from comp.toml:

    time_column set   hold out the latest 20% of training rows
    otherwise         adversarial validation: train a classifier to tell
                      training rows from test rows, and hold out the 20% of
                      training rows that look most like the test

Rewrite `holdout` when you know something better about the test (for
example the real test's released rows, as in the Madinah competition).
"""

from collections.abc import Callable

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import cross_val_predict

from comp import config
from comp.data import Task, features
from comp.metric import score

HOLDOUT_SHARE = 0.2


def encoded(frame: pd.DataFrame) -> pd.DataFrame:
    """Features as numbers: text columns become category codes, so a tree can split them."""
    out = features(frame).copy()
    for column in out.columns:
        if not pd.api.types.is_numeric_dtype(out[column]):
            out[column] = out[column].astype("category").cat.codes
    return out


def test_likeness(train: pd.DataFrame, test: pd.DataFrame) -> tuple[np.ndarray, float]:
    """For each training row, how likely a classifier thinks it is a test row.

    Returns (probabilities, AUC). AUC near 0.5 means train and test look the
    same; above about 0.75 means they differ, and plain k-fold will mislead.
    """
    pooled = pd.concat([encoded(train), encoded(test)], ignore_index=True)
    is_test = np.r_[np.zeros(len(train)), np.ones(len(test))]
    model = HistGradientBoostingClassifier(max_iter=200, random_state=0)
    probability = cross_val_predict(model, pooled, is_test, cv=5, method="predict_proba")[:, 1]
    return probability[: len(train)], float(roc_auc_score(is_test, probability))


def holdout(train: pd.DataFrame, test: pd.DataFrame) -> tuple[np.ndarray, str]:
    """Positions of the training rows to hold out, and a sentence saying how they were chosen."""
    cfg = config.load()
    count = int(len(train) * HOLDOUT_SHARE)
    time_column = cfg.get("data", "time_column")
    if time_column:
        order = np.argsort(train[time_column].to_numpy(), kind="stable")
        return order[-count:], f"the latest {HOLDOUT_SHARE:.0%} of rows by {time_column}"
    likeness, auc = test_likeness(train, test)
    return np.argsort(-likeness)[:count], (
        f"the {HOLDOUT_SHARE:.0%} of rows most like the test (adversarial AUC {auc:.3f})"
    )


def evaluate(solver: Callable[[Task], pd.Series], real: Task) -> tuple[dict[str, float], str]:
    """Score `solver` on the shadow holdout. Returns (scores, how the holdout was chosen)."""
    cfg = config.load()
    held, how = holdout(real.train, real.test)
    mask = np.zeros(len(real.train), dtype=bool)
    mask[held] = True
    held_rows = real.train[mask]
    task = Task(
        train=real.train[~mask].reset_index(drop=True),
        test=held_rows.drop(columns=[cfg.target_column]).reset_index(drop=True),
    )
    truth = held_rows.set_index(cfg.id_column)[cfg.target_column]
    return score(truth, solver(task)), how
