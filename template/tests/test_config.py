from comp import config, tracking


def test_metric_direction(project):
    cfg = config.load()
    assert cfg.metric == "rmse" and cfg.lower_is_better
    assert config.better(0.4, 0.5)


def test_params_are_flattened_for_mlflow():
    flat = tracking.flatten({"lr": 0.1, "sizes": (5, 15), "tree": {"depth": 3}})
    assert flat == {"lr": 0.1, "sizes": "(5, 15)", "tree.depth": 3}
