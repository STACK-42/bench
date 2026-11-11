"""PreToolUse guard for Bash commands in competition repos.

Claude Code sends the tool call as JSON on stdin. This script answers with a
permission decision on stdout, or prints nothing to leave the call alone.
It acts only inside a competition repo: a folder with comp.toml in it or
above it.

    direct platform upload (kaggle competitions submit ...)   deny
    comp submit, from a subagent                              deny
    comp submit, from the main agent                          ask the person
    a formatter run over the whole folder (ruff format .)     deny

Uploads use a few daily submissions and can't be taken back, so the person
approves each one in Claude Code's own permission prompt. That approval is
real in a way that an agent passing --yes is not.
"""

import json
import re
import sys
from pathlib import Path

DIRECT_UPLOAD = re.compile(r"\bkaggle\s+(competitions|c)\s+submit\b")
COMP_SUBMIT = re.compile(r"\bcomp\s+submit\b")
# `ruff format` or `black` with no path, or with `.` as the path.
WHOLE_FOLDER_FORMAT = re.compile(r"\b(ruff\s+format|black)(\s+-{1,2}[\w-]+)*\s*(\.\s*)?($|[;&|])")


def in_competition_repo(cwd: str) -> bool:
    folder = Path(cwd or ".").resolve()
    return any((p / "comp.toml").exists() for p in (folder, *folder.parents))


def decide(event: dict) -> tuple[str, str] | None:
    """(decision, reason) for this tool call, or None to leave it alone."""
    if event.get("tool_name") != "Bash" or not in_competition_repo(event.get("cwd", "")):
        return None
    command = event.get("tool_input", {}).get("command", "")
    if DIRECT_UPLOAD.search(command):
        return "deny", (
            "Upload through `uv run comp submit <file>`, not the platform CLI: it checks the "
            "file, ties it to a commit, and writes the score into submissions.md."
        )
    if COMP_SUBMIT.search(command):
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
