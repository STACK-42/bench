import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression

from comp import config, cv, ledger, shadow
from comp.data import real_task


def mean_solver(task):
    return pd.Series(task.train["target"].mean(), index=task.test["id"].to_numpy())


def linear_solver(task):
    model = LinearRegression().fit(task.train[["x"]], task.train["target"])
    return pd.Series(model.predict(task.test[["x"]]), index=task.test["id"].to_numpy())


def test_cv_ranks_a_real_model_above_the_mean(project):
    train = real_task().train
    baseline = cv.cross_validate(mean_solver, train)
    better = cv.cross_validate(linear_solver, train)
    assert len(baseline.folds) == 3
    assert config.better(better.score, baseline.score)
    assert better.std >= 0


def test_cv_keeps_one_prediction_per_held_out_row(project):
    train = real_task().train
    result = cv.cross_validate(linear_solver, train)
    assert list(result.oof.columns) == ["seed", "fold", "id", "truth", "prediction"]
    assert sorted(result.oof["id"]) == sorted(train["id"])  # kfold: every row held out once
    assert result.oof["prediction"].notna().all()


def test_folds_never_show_the_target_of_held_out_rows(project):
    train = real_task().train
    for _, task, truth in cv.folds(train):
        assert "target" not in task.test.columns
        assert not set(task.train["id"]) & set(truth.index)


def test_shadow_holds_out_test_like_rows(project):
    real = real_task()
    held, how = shadow.holdout(real.train, real.test)
    assert len(held) == int(len(real.train) * shadow.HOLDOUT_SHARE)
    assert "adversarial AUC" in how
    # The test is shifted to larger x, so the held-out rows should be too.
    assert real.train["x"].iloc[held].mean() > real.train["x"].mean()
    scores, _ = shadow.evaluate(linear_solver, real)
    assert scores["score"] < 1.0


def test_ledger_builds_writes_and_maps_a_submission(project):
    real = real_task()
    sample = pd.read_csv(project / "data" / "sample_submission.csv")
    frame = ledger.build(linear_solver(real), sample)
    assert list(frame.columns) == ["id", "target"]
    assert list(frame["id"]) == list(sample["id"])
    row = {"CV": "0.51234", "CV std": "0.01", "shadow": "0.6", "experiment": "`e.py`",
           "owner": "me", "commit": "`abc`", "MLflow run": "`r`"}  # fmt: skip
    name = ledger.write(frame, row)
    assert name == "submission0.51234.csv"
    assert ledger.write(frame, row) == name  # writing the same file again is a no-op
    (entry,) = ledger.read_map()
    assert entry["file"] == name and entry["experiment"] == "e.py"
    ledger.set_cell(name, "public LB", "0.55")
    assert ledger.read_map()[0]["public LB"] == "0.55"


def test_ledger_refuses_incomplete_predictions(project):
    sample = pd.read_csv(project / "data" / "sample_submission.csv")
    partial = pd.Series(np.zeros(5), index=sample["id"][:5])
    with pytest.raises(ValueError, match="no prediction"):
        ledger.build(partial, sample)
