"""One sentence: what this experiment tries and why you expect it to help.

Copy this file to experiments/<you>/NNN_short_name.py, then:

    uv run comp run experiments/<you>/NNN_short_name.py

Write what you learned in experiments.md when the run finishes.
"""

import pandas as pd

from comp import config, seed

# Everything you might tune goes here. It is logged to MLflow with the run.
PARAMS = {}


def solve(task) -> pd.Series:
    """Return a prediction for every row of task.test, indexed by its id.

    task.train  features and the target
    task.test   features only

    This function runs once per CV fold, once for the shadow test and once on
    the real test set. It must learn from task.train every time and never
    read files from data/ itself. Use `seed()` for any random state, so
    `comp noise` can measure how much the score moves by chance.
    """
    cfg = config.load()
    _ = seed()  # pass this to every model's random_state
    # Baseline: predict the training mean for every row.
    value = task.train[cfg.target_column].mean()
    return pd.Series(value, index=task.test[cfg.id_column].to_numpy())
