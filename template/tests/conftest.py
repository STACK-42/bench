"""A small fake competition in a temp folder, so tests need no real data or network."""

import subprocess

import numpy as np
import pandas as pd
import pytest

from comp import config, data, paths

CONFIG = """
[competition]
platform = "zindi"
slug = "fake"
[data]
id_column = "id"
target_column = "target"
[task]
type = "regression"
metric = "rmse"
[cv]
scheme = "kfold"
folds = 3
"""


def fake_frames(seed: int = 0) -> dict[str, pd.DataFrame]:
    """A linear target with noise, a text column, and a test set shifted on x."""
    rng = np.random.default_rng(seed)
    n, m = 300, 100
    x = rng.normal(size=n)
    train = pd.DataFrame(
        {
            "id": [f"tr{i}" for i in range(n)],
            "x": x,
            "colour": rng.choice(["red", "blue"], n),
            "target": 3 * x + rng.normal(0, 0.5, n),
        }
    )
    test = pd.DataFrame(
        {"id": [f"te{i}" for i in range(m)], "x": rng.normal(1, 1, m), "colour": "red"}
    )
    sample = pd.DataFrame({"id": test["id"], "target": 0.0})
    return {"train": train, "test": test, "sample_submission": sample}


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A temp project folder with comp.toml, data/ and a git repo; paths point at it."""
    for name, value in {
        "ROOT": tmp_path,
        "CONFIG": tmp_path / "comp.toml",
        "DATA": tmp_path / "data",
        "SUBMISSIONS": tmp_path / "submissions",
        "SUBMISSIONS_MAP": tmp_path / "submissions.md",
        "NOISE": tmp_path / "noise.json",
    }.items():
        monkeypatch.setattr(paths, name, value)
    (tmp_path / "comp.toml").write_text(CONFIG)
    (tmp_path / "data").mkdir()
    files = {"train": "train.csv", "test": "test.csv", "sample_submission": "sample_submission.csv"}
    for role, frame in fake_frames().items():
        frame.to_csv(tmp_path / "data" / files[role], index=False)
    config.load.cache_clear()
    data.load_raw.cache_clear()
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    yield tmp_path
    config.load.cache_clear()
    data.load_raw.cache_clear()
