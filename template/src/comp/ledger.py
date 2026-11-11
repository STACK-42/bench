"""Submission files and the map of what produced each one.

A submission is named after its CV score: CV 0.81234 gives
submissions/submission0.81234.csv. Each file gets one row in submissions.md
with the commit and MLflow run that produced it, so any leaderboard score
can be traced back to its code.
"""

from datetime import date

import numpy as np
import pandas as pd

from comp import paths

COLUMNS = [
    "file",
    "CV",
    "CV std",
    "shadow",
    "public LB",
    "private LB",
    "experiment",
    "owner",
    "commit",
    "MLflow run",
    "date",
]
MAP_HEADER = "| " + " | ".join(COLUMNS) + " |\n|" + " --- |" * len(COLUMNS) + "\n"


def build(prediction: pd.Series | pd.DataFrame, sample: pd.DataFrame) -> pd.DataFrame:
    """Put a prediction in the sample submission's shape and row order, or explain why not.

    `prediction` is a Series indexed by id (one target column) or a DataFrame
    indexed by id with the sample's target columns.
    """
    id_column, targets = sample.columns[0], list(sample.columns[1:])
    if isinstance(prediction, pd.Series):
        if len(targets) != 1:
            raise ValueError(f"the sample has {len(targets)} target columns: return a DataFrame")
        prediction = prediction.to_frame(targets[0])
    if set(prediction.columns) != set(targets):
        raise ValueError(f"columns are {list(prediction.columns)}, expected {targets}")
    if prediction.index.duplicated().any():
        raise ValueError("some ids appear twice in the prediction")
    frame = prediction.reindex(sample[id_column])[targets]
    if frame.isna().any().any():
        raise ValueError(f"{int(frame.isna().any(axis=1).sum())} ids have no prediction")
    numeric = frame.select_dtypes("number")
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError("some predictions are not finite")
    return frame.reset_index().rename(columns={"index": id_column})


def write(frame: pd.DataFrame, row: dict[str, str]) -> str:
    """Save the file and append its row to submissions.md. Returns the file name.

    `row` holds the COLUMNS values except file and date.
    """
    paths.SUBMISSIONS.mkdir(exist_ok=True)
    name = f"submission{float(row['CV']):.5f}.csv"
    target = paths.SUBMISSIONS / name
    if target.exists():
        if pd.read_csv(target).equals(pd.read_csv(_round_trip(frame))):
            return name  # the same file is already mapped
        raise FileExistsError(
            f"{name} exists with different predictions. Two models share a CV to five "
            "decimals: rename the old file and its row in submissions.md by hand."
        )
    frame.to_csv(target, index=False)
    if not paths.SUBMISSIONS_MAP.exists():
        paths.SUBMISSIONS_MAP.write_text("# Submissions\n\n" + MAP_HEADER)
    values = {**row, "file": f"`{name}`", "date": date.today().isoformat()}
    line = "| " + " | ".join(str(values.get(c, "")) for c in COLUMNS) + " |\n"
    with paths.SUBMISSIONS_MAP.open("a") as handle:
        handle.write(line)
    return name


def _round_trip(frame: pd.DataFrame):
    """The frame as it would read back from CSV, to compare with a file on disk."""
    import io

    buffer = io.StringIO()
    frame.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer


def read_map() -> list[dict[str, str]]:
    """The rows of submissions.md as dicts keyed by COLUMNS, without backticks."""
    if not paths.SUBMISSIONS_MAP.exists():
        return []
    rows = []
    for line in paths.SUBMISSIONS_MAP.read_text().splitlines():
        if line.startswith("| `"):  # data rows start with the backticked file name
            cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
            rows.append(dict(zip(COLUMNS, cells, strict=False)))
    return rows


def set_cell(name: str, column: str, value: str) -> None:
    """Replace one cell in the row of file `name`, leaving the rest of the file alone."""
    lines = paths.SUBMISSIONS_MAP.read_text().splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith(f"| `{name}` |"):
            cells = line.rstrip("\n").strip().strip("|").split("|")
            cells[COLUMNS.index(column)] = f" {value} "
            lines[i] = "|" + "|".join(cells) + "|\n"
            paths.SUBMISSIONS_MAP.write_text("".join(lines))
            return
    raise KeyError(f"{name} has no row in {paths.SUBMISSIONS_MAP.name}")
