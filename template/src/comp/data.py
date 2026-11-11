"""Load the competition files and describe one problem to solve.

This default fits the common tabular shape: a train file with an id and a
target column, a test file without the target, and a sample submission.
For a different shape (time series with holes, images, several tables),
rewrite this file and cv.py together, and keep the `Task` idea: everything
a solver may use is inside the task, nothing else.
"""

from dataclasses import dataclass
from functools import cache

import pandas as pd

from comp import config, paths


@dataclass
class Task:
    """One problem to solve: learn from `train`, predict every row of `test`.

    train  features and the target
    test   features only; its id column says which rows to predict
    """

    train: pd.DataFrame
    test: pd.DataFrame


@cache
def load_raw() -> dict[str, pd.DataFrame]:
    """The competition files from data/, by role: train, test, sample_submission."""
    cfg = config.load()
    files = {
        "train": cfg.get("data", "train", "train.csv"),
        "test": cfg.get("data", "test", "test.csv"),
        "sample_submission": cfg.get("data", "sample_submission", "sample_submission.csv"),
    }
    missing = [name for name in files.values() if not (paths.DATA / name).exists()]
    if missing:
        raise SystemExit(f"missing in data/: {missing}. Run `make data` first.")
    return {role: pd.read_csv(paths.DATA / name) for role, name in files.items()}


def real_task() -> Task:
    """The real problem: all training rows, the real test rows."""
    raw = load_raw()
    return Task(train=raw["train"], test=raw["test"])


def features(frame: pd.DataFrame) -> pd.DataFrame:
    """Every column except the id and the target. A starting point for experiments."""
    cfg = config.load()
    return frame.drop(columns=[cfg.id_column, cfg.target_column], errors="ignore")
