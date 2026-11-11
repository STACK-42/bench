"""Cross-validation: the home test that stands in for the leaderboard.

A fold hides part of the training rows, lets the solver learn from the rest,
and scores its predictions on the hidden rows. The scheme must copy how the
test set differs from the training set:

    kfold  rows are independent and the test looks like the training rows
    group  rows come in groups (a user, a patient, a day); a group never
           appears on both sides, because the test has new groups
    time   the test comes after the training data; every fold predicts a
           later period from earlier ones

If you change how folds are made or scored, raise CV_VERSION. Scores from
different versions cannot be compared.
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, KFold, TimeSeriesSplit

from comp import config
from comp import seed as comp_seed
from comp.data import Task
from comp.metric import score

CV_VERSION = 1

Solver = Callable[[Task], pd.Series]


@dataclass
class CVResult:
    score: float  # mean over folds: the number that names a submission
    parts: dict[str, float]  # mean of each part of the score, if the metric has parts
    folds: pd.DataFrame  # one row per fold

    @property
    def std(self) -> float:
        return float(self.folds["score"].std(ddof=0))


def splits(train: pd.DataFrame, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """(train rows, validation rows) for each fold, as positions in `train`."""
    cfg = config.load()
    scheme, k = cfg.get("cv", "scheme", "kfold"), cfg.get("cv", "folds", 5)
    if scheme == "group":
        groups = train[cfg.get("data", "group_column")]
        return list(GroupKFold(n_splits=k).split(train, groups=groups))
    if scheme == "time":
        order = np.argsort(train[cfg.get("data", "time_column")].to_numpy(), kind="stable")
        return [(order[a], order[b]) for a, b in TimeSeriesSplit(n_splits=k).split(order)]
    # COMP_SEED changes the shuffle too, so `comp noise` sees how much the fold layout matters.
    shuffle = seed + 1000 * comp_seed()
    return list(KFold(n_splits=k, shuffle=True, random_state=shuffle).split(train))


def folds(train: pd.DataFrame, seeds: int = 1):
    """Yield (label, Task, truth) for every fold. `truth` is indexed by id."""
    cfg = config.load()
    for seed in range(seeds):
        for number, (fit, held) in enumerate(splits(train, seed)):
            held_rows = train.iloc[held]
            task = Task(
                train=train.iloc[fit].reset_index(drop=True),
                test=held_rows.drop(columns=[cfg.target_column]).reset_index(drop=True),
            )
            truth = held_rows.set_index(cfg.id_column)[cfg.target_column]
            yield {"seed": seed, "fold": number}, task, truth


def cross_validate(solver: Solver, train: pd.DataFrame, seeds: int = 1) -> CVResult:
    rows = []
    for label, task, truth in folds(train, seeds):
        rows.append({**label, "rows": len(truth), **score(truth, solver(task))})
    frame = pd.DataFrame(rows)
    parts = [c for c in frame.columns if c not in ("seed", "fold", "rows", "score")]
    return CVResult(
        score=float(frame["score"].mean()),
        parts=frame[parts].mean().to_dict(),
        folds=frame,
    )
