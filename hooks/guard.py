"""PreToolUse guard for Bash commands in competition repos.

Claude Code sends the tool call as JSON on stdin. This script answers with a
permission decision on stdout, or prints nothing to leave the call alone.
It acts only inside a competition repo: a folder with comp.toml in it or
above it.

    direct platform upload (kaggle competitions submit ...)   deny
    the repo's submit command, from a subagent                deny
    the repo's submit command, from the main agent            ask the person
    a formatter run over the whole folder (ruff format .)     deny

The submit command is `comp submit` unless comp.toml names another one in
[commands] submit, for a repo that had its own harness before bench.

Uploads use a few daily submissions and can't be taken back, so the person
approves each one in Claude Code's own permission prompt. That approval is
real in a way that an agent passing --yes is not.
"""

from __future__ import annotations  # `str | None` must also work on Python 3.9

import json
import re
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:  # older Pythons: read the one line we need by hand
    tomllib = None

DIRECT_UPLOAD = re.compile(r"\bkaggle\s+(competitions|c)\s+submit\b")
DEFAULT_SUBMIT = "comp submit"
# `ruff format` or `black` with no path, or with `.` as the path.
WHOLE_FOLDER_FORMAT = re.compile(r"\b(ruff\s+format|black)(\s+-{1,2}[\w-]+)*\s*(\.\s*)?($|[;&|])")


def find_config(cwd: str) -> Path | None:
    """The comp.toml in `cwd` or the nearest folder above it, or None outside a competition repo."""
    folder = Path(cwd or ".").resolve()
    for place in (folder, *folder.parents):
        if (place / "comp.toml").exists():
            return place / "comp.toml"
    return None


def submit_command(config: Path) -> str:
    """The repo's upload command without its runner, e.g. "comp submit" or "madinah submit"."""
    text = config.read_text()
    if tomllib is not None:
        try:
            command = tomllib.loads(text).get("commands", {}).get("submit", DEFAULT_SUBMIT)
        except tomllib.TOMLDecodeError:
            command = DEFAULT_SUBMIT
    else:
        found = re.search(r'^\s*submit\s*=\s*"([^"]+)"', text, re.MULTILINE)
        command = found.group(1) if found else DEFAULT_SUBMIT
    words = command.split()
    return " ".join(words[-2:]) if len(words) >= 2 else DEFAULT_SUBMIT  # drop `uv run`


def matches(command: str, words: str) -> bool:
    """True if `command` contains the words of `words` in order, as whole words."""
    pattern = r"\b" + r"\s+".join(re.escape(w) for w in words.split()) + r"\b"
    return re.search(pattern, command) is not None


def decide(event: dict) -> tuple[str, str] | None:
    """(decision, reason) for this tool call, or None to leave it alone."""
    config = find_config(event.get("cwd", ""))
    if event.get("tool_name") != "Bash" or config is None:
        return None
    command = event.get("tool_input", {}).get("command", "")
    submit = submit_command(config)
    if DIRECT_UPLOAD.search(command):
        return "deny", (
            f"Upload through `uv run {submit} <file>`, not the platform CLI: it checks the "
            "file, ties it to a commit, and writes the score into submissions.md."
        )
    if matches(command, submit):
        if event.get("agent_id"):
            return "deny", "Only the main agent uploads. Report the file to it instead."
        return "ask", (
            "This uploads a submission and uses one of today's few tries. "
            "Approve only if you asked for this specific file."
        )
    match = WHOLE_FOLDER_FORMAT.search(command)
    if match and not re.search(r"--(check|diff)\b", match.group(0)):  # read-only runs are fine
        return "deny", (
            "Don't format the whole folder: it rewrites notes and other people's files. "
            "Use `make format` (tracked Python files only) or name the files you changed."
        )
    return None


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return  # not our business: never block on a bad payload
    decision = decide(event)
    if decision is None:
        return
    verdict, reason = decision
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": verdict,
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
