"""The PreToolUse guard, fed the JSON Claude Code would send."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

GUARD = Path(__file__).resolve().parents[1] / "hooks" / "guard.py"
spec = importlib.util.spec_from_file_location("guard", GUARD)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "comp.toml").write_text("[competition]\n")
    (tmp_path / "src").mkdir()
    return tmp_path


def event(command: str, cwd: Path, agent_id: str | None = None) -> dict:
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd)}
    if agent_id:
        payload["agent_id"] = agent_id
    return payload


@pytest.mark.parametrize(
    "command",
    [
        "kaggle competitions submit my-comp -f s.csv -m x",
        "uv run kaggle c submit my-comp -f s.csv -m x",
    ],
)
def test_direct_uploads_are_denied(repo, command):
    assert guard.decide(event(command, repo))[0] == "deny"


def test_comp_submit_asks_the_person(repo):
    assert guard.decide(event("uv run comp submit submissions/x.csv --yes", repo))[0] == "ask"


def test_subagents_may_not_upload(repo):
    decision = guard.decide(event("uv run comp submit x.csv", repo / "src", agent_id="a1"))
    assert decision[0] == "deny"


@pytest.mark.parametrize("command", ["ruff format .", "uv run ruff format", "black . && ls"])
def test_whole_folder_formatting_is_denied(repo, command):
    assert guard.decide(event(command, repo))[0] == "deny"


@pytest.mark.parametrize(
    "command",
    [
        "uv run ruff format src/comp/cli.py",
        "make format",
        "uv run ruff format --check .",
        "uv run comp run experiments/me/001.py --submit",
        "git commit -m 'kaggle submission notes'",
    ],
)
def test_ordinary_commands_pass(repo, command):
    assert guard.decide(event(command, repo)) is None


def test_outside_a_competition_repo_nothing_is_checked(tmp_path):
    assert guard.decide(event("kaggle competitions submit x", tmp_path)) is None


def test_script_prints_a_permission_decision(repo):
    payload = json.dumps(event("kaggle competitions submit x -f a.csv", repo))
    out = subprocess.run(
        [sys.executable, str(GUARD)], input=payload, capture_output=True, text=True, check=True
    )
    decision = json.loads(out.stdout)["hookSpecificOutput"]
    assert decision["hookEventName"] == "PreToolUse"
    assert decision["permissionDecision"] == "deny"
