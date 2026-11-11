"""The competition harness. Commands live in cli.py; start with `uv run comp --help`."""

import os


def seed() -> int:
    """The random seed experiments should use. `comp noise` changes it to measure noise."""
    return int(os.environ.get("COMP_SEED", "0"))
