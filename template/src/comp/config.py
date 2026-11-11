"""Read comp.toml, the one file that describes this competition."""

import tomllib
from dataclasses import dataclass, field
from functools import cache

from comp import paths

# For each metric: is a lower value better?
LOWER_IS_BETTER = {
    "rmse": True,
    "mae": True,
    "rmsle": True,
    "mape": True,
    "logloss": True,
    "auc": False,
    "accuracy": False,
    "f1": False,
    "r2": False,
}


@dataclass(frozen=True)
class Config:
    raw: dict = field(repr=False)

    def get(self, section: str, key: str, default=None):
        return self.raw.get(section, {}).get(key, default)

    @property
    def metric(self) -> str:
        return self.get("task", "metric", "rmse")

    @property
    def lower_is_better(self) -> bool:
        """Custom metrics can set [task] lower_is_better; the known ones look it up."""
        explicit = self.get("task", "lower_is_better")
        return explicit if explicit is not None else LOWER_IS_BETTER.get(self.metric, True)

    @property
    def id_column(self) -> str:
        return self.get("data", "id_column", "id")

    @property
    def target_column(self) -> str:
        return self.get("data", "target_column", "target")


@cache
def load() -> Config:
    """The project's comp.toml. An empty config if the file is missing (tests)."""
    if not paths.CONFIG.exists():
        return Config({})
    return Config(tomllib.loads(paths.CONFIG.read_text()))


def better(a: float, b: float) -> bool:
    """True if score `a` is better than score `b` under this competition's metric."""
    return a < b if load().lower_is_better else a > b
