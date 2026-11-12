"""MLflow logging. Every run lands in mlflow.db at the repo root.

Read it in the browser with `make ui`, or query it from Python:

    import mlflow; mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.search_runs(experiment_names=["comp"])
"""

import hashlib
import importlib.metadata
import os
import subprocess
from contextlib import contextmanager

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")

import mlflow  # noqa: E402
import pandas as pd  # noqa: E402

from comp import config, paths  # noqa: E402
from comp.cv import CV_VERSION, CVResult  # noqa: E402

EXPERIMENT = "comp"


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=paths.ROOT, capture_output=True, text=True)
    return result.stdout.strip()


def git_state() -> dict[str, str | bool]:
    """Commit, branch and whether tracked files have uncommitted changes."""
    return {
        "commit": git("rev-parse", "HEAD"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(git("status", "--porcelain", "--untracked-files=no")),
    }


def flatten(params: dict, prefix: str = "") -> dict:
    """{"a": {"b": 1}} becomes {"a.b": 1}. Values MLflow can't store as is become strings."""
    flat = {}
    for key, value in params.items():
        if isinstance(value, dict):
            flat.update(flatten(value, f"{prefix}{key}."))
        elif isinstance(value, bool | int | float | str):
            flat[f"{prefix}{key}"] = value
        else:
            flat[f"{prefix}{key}"] = str(value)
    return flat


def data_fingerprint() -> dict[str, str]:
    """A short hash per data file, so a run says which data it saw."""
    return {
        f"{path.stem}_sha256": hashlib.sha256(path.read_bytes()).hexdigest()[:12]
        for path in sorted(paths.DATA.glob("*.csv"))
    }


@contextmanager
def run(name: str, owner: str, script: str, params: dict, seeds: int):
    """Open an MLflow run and log what is needed to reproduce it.

    params    the experiment's PARAMS, then `cv.*` (how validation was set up)
              and `data.*` (which files it ran on)
    tags      owner, script, commit, whether the tree was dirty, cv_version
    artifacts a copy of the experiment file, the package list and uv.lock
    """
    mlflow.set_tracking_uri(paths.MLFLOW_URI)
    mlflow.set_experiment(EXPERIMENT)
    state = git_state()
    cv = {**config.load().raw.get("cv", {}), "seeds": seeds, "version": CV_VERSION}
    with mlflow.start_run(run_name=name) as active:
        mlflow.set_tags(
            {
                "owner": owner,
                "script": script,
                "git_commit": state["commit"],
                "git_commit_dirty": str(state["dirty"]),
                "cv_version": str(CV_VERSION),
                "noise_run": str(os.environ.get("COMP_NOISE_RUN") == "1").lower(),
            }
        )
        mlflow.log_params(
            {**flatten(params), **flatten(cv, "cv."), **flatten(data_fingerprint(), "data.")}
        )
        packages = sorted(
            f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions()
        )
        mlflow.log_text("\n".join(packages) + "\n", "environment.txt")
        if (paths.ROOT / "uv.lock").exists():
            mlflow.log_artifact(str(paths.ROOT / "uv.lock"), artifact_path="code")
        mlflow.log_artifact(str(paths.ROOT / script), artifact_path="code")
        yield active


def log_cv(result: CVResult) -> None:
    mlflow.log_metric("cv_score", result.score)
    mlflow.log_metric("cv_std", result.std)
    for part, value in result.parts.items():
        mlflow.log_metric(f"cv_{part}", value)
    mlflow.log_text(result.folds.to_csv(index=False), "cv_folds.csv")
    # Kept for blending: the blend skill reads these to choose mix weights.
    mlflow.log_text(result.oof.to_csv(index=False), "oof.csv")


def load_oof(run_id: str) -> pd.DataFrame:
    """The out-of-fold predictions a run logged (columns seed, fold, id, truth, prediction)."""
    mlflow.set_tracking_uri(paths.MLFLOW_URI)
    return pd.read_csv(mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path="oof.csv"))


def log_shadow(scores: dict[str, float], how: str) -> None:
    for part, value in scores.items():
        mlflow.log_metric("shadow_score" if part == "score" else f"shadow_{part}", value)
    mlflow.set_tag("shadow_holdout", how)


def latest_runs():
    """Every run, newest first, as a DataFrame (empty if there are none yet)."""
    mlflow.set_tracking_uri(paths.MLFLOW_URI)
    return mlflow.search_runs(experiment_names=[EXPERIMENT], order_by=["start_time DESC"])
