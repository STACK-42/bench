"""Where things live. Everything else imports paths from here."""

import os
from pathlib import Path

ROOT = Path(os.environ.get("COMP_ROOT", Path(__file__).resolve().parents[2]))
CONFIG = ROOT / "comp.toml"
DATA = ROOT / "data"
SUBMISSIONS = ROOT / "submissions"
SUBMISSIONS_MAP = ROOT / "submissions.md"
NOISE = ROOT / "noise.json"
MLFLOW_DB = ROOT / "mlflow.db"
MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", f"sqlite:///{MLFLOW_DB}")
