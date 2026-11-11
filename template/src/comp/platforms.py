"""Upload submissions and read scores back, for each competition platform.

Kaggle   uses the Kaggle CLI that is installed with the project. It finds the
         KAGGLE_API_TOKEN variable, ~/.kaggle/access_token, or the login from
         `kaggle auth login`.
Zindi    has no official upload API that this harness trusts yet, so uploads
         are manual: `comp submit` checks the file and prints what to do, and
         `comp scores --set FILE SCORE` records the score you read on the site.

Every Kaggle upload message starts with the file name, and Kaggle records the
file name too, so a score can always be matched back to its row.
"""

import csv
import io
import subprocess
import sys
from pathlib import Path

from comp import config, ledger, paths

WAIT_SECONDS = 900  # how long `submit` waits for Kaggle to score the file


def kaggle(*args: str) -> str:
    """Run the Kaggle CLI from this environment. Stops with its message on failure."""
    command = [str(Path(sys.executable).parent / "kaggle"), *args]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"kaggle {' '.join(args[:2])} failed:\n{result.stdout}{result.stderr}")
    return result.stdout


def limits() -> str:
    """Today's remaining uploads, as the platform words it."""
    cfg = config.load()
    if cfg.get("competition", "platform") == "kaggle":
        slug = cfg.get("competition", "slug")
        return kaggle("competitions", "submission-limits", slug).strip()
    return "Check today's remaining uploads on the competition page."


def upload(path: Path, message: str, wait: bool) -> bool:
    """Upload one file. Returns True if the platform took it (or the manual steps were shown)."""
    cfg = config.load()
    platform, slug = cfg.get("competition", "platform"), cfg.get("competition", "slug")
    if platform == "kaggle":
        command = ["competitions", "submit", slug, "-f", str(path), "-m", message]
        if wait:
            command += ["--wait", str(WAIT_SECONDS)]
        sys.stdout.flush()  # our lines first, then the Kaggle CLI writes to the terminal
        executable = str(Path(sys.executable).parent / "kaggle")
        return subprocess.run([executable, *command]).returncode == 0
    print(
        f"\n{platform} uploads are manual. Upload this file on the competition page:\n"
        f"  {path}\nwith this comment:\n  {message}\n"
        f"Then record the score: uv run comp scores --set {path.name} <public score>"
    )
    return True


def fetch_scores() -> dict[str, tuple[str, str]]:
    """{file name: (public score, private score)} from the platform, latest upload wins.

    Values are "pending" or "error" when there is no number yet. Empty for
    platforms without an API.
    """
    cfg = config.load()
    if cfg.get("competition", "platform") != "kaggle":
        return {}
    slug = cfg.get("competition", "slug")
    text = kaggle("competitions", "submissions", slug, "--csv", "--page-size", "200", "-q")
    out = {}
    for entry in sorted(csv.DictReader(io.StringIO(text)), key=lambda e: e.get("date", "")):
        status = entry.get("status", "").lower()
        public = entry.get("publicScore", "").strip()
        private = entry.get("privateScore", "").strip()
        if "error" in status or "fail" in status:
            public = "error"
        elif not public:
            public = "pending"
        out[entry.get("fileName", "")] = (public, private)
    return out


def sync_scores() -> list[tuple[str, str]]:
    """Copy the platform's scores into submissions.md. Returns [(file, new public score)]."""
    remote = fetch_scores()
    changes = []
    for row in ledger.read_map():
        if row["file"] not in remote:
            continue
        public, private = remote[row["file"]]
        if public != row["public LB"]:
            ledger.set_cell(row["file"], "public LB", public)
            changes.append((row["file"], public))
        if private and private != row.get("private LB", ""):
            ledger.set_cell(row["file"], "private LB", private)
    return changes


def submission_path(name: str) -> Path:
    return paths.SUBMISSIONS / name
