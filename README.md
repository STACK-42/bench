<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/brand/bench-horizontal-dark.svg">
    <img src="assets/brand/bench-horizontal.svg" alt="bench" width="360">
  </picture>
</p>

<p align="center"><strong>Validation first. Every result measured twice.</strong></p>

<p align="center"><a href="https://github.com/A7med7x7/bench/actions/workflows/ci.yml"><img src="https://github.com/A7med7x7/bench/actions/workflows/ci.yml/badge.svg" alt="CI"></a></p>

bench is a Claude Code plugin for machine learning competitions on Kaggle and Zindi. It has one goal: the best final score. It does not try to get there by guessing faster. It makes the validation trustworthy first, then lets a main agent and research agents run many experiments that are all measured the same way.

It grew out of the Madinah crowd-count competition (Kaggle, 2026). There, one model scored 0.821 in cross-validation and 1.022 on the leaderboard. A second check built to look like the test caught the problem, and a research agent then found three improvements in one evening. This plugin packages that way of working.

![The bench loop: comp-start proves the validation, experiment tries one idea on two checks, research sends agents to try many, submit uploads only with your approval, postmortem checks whether the leaderboard agrees, and lessons feed the next experiment. A change is kept only if CV and the shadow test both beat twice the noise.](assets/brand/loop.svg)

## What is in it

| part | what it does |
| --- | --- |
| `template/` | the project harness each competition starts from: `comp.toml`, data loading, CV, a shadow test, the metric, MLflow tracking, a submissions log tied to commits, and Kaggle/Zindi upload |
| `skills/comp-start` | set up a new competition and build and prove the validation before any model |
| `skills/experiment` | one idea, scored on CV and the shadow test against the noise, logged, kept or dropped |
| `skills/research` | send research agents to try many ideas in their own worktrees, with a fixed brief and report |
| `skills/submit` | plan the day's few uploads, upload with your approval, pick the final submissions |
| `skills/postmortem` | after each leaderboard score: do the checks agree? Record lessons |
| `skills/explain` | optional learning notes in three layers, in simple English |
| `agents/researcher` | tests one direction in a git worktree and reports a table |
| `agents/leak-auditor` | reads an experiment and reports any information leak |
| `hooks/guard.py` | in competition repos: asks you before every upload, blocks uploads that skip the log, blocks whole-folder formatting |
| `lessons/seed.md` | lessons across competitions, read at the start of each new one |
| `assets/brand/` | the bench logo kit (symbol, wordmark, lockups, icons), the workflow diagram, `notes.css` for themed learning notes, and `GUIDELINES.md` |

## Install

The repo is private, so your git must be able to read it (`gh auth login` and `gh auth setup-git`, or an SSH key).

```text
/plugin marketplace add A7med7x7/bench
/plugin install bench@bench
```

> [!NOTE]
> If you have no SSH key for GitHub, set `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` before starting Claude Code, so the install uses HTTPS.

## Use

Start a competition by telling Claude, or run the skill directly:

```text
/bench:comp-start https://www.kaggle.com/competitions/<name>
```

Then work in that repo:

```text
/bench:experiment   try adding lag features to 003_baseline
/bench:research     test the ideas in this playbook against our best model
/bench:submit       upload the best file when the limit resets
/bench:postmortem   the score came back: 0.912
```

Every experiment is scored twice. `uv run comp run` gives the CV score and the shadow score, and `uv run comp compare` keeps a change only if it is better on both by more than twice the noise that `uv run comp noise` measured. The leaderboard is a third check and never decides alone.

`comp.toml` in each competition repo sets solo or team mode (team mode adds per-person experiment folders and reviewers) and whether learning notes are written.

## How it is built

- Claude is the orchestrator. The skills say what to do at each stage, the agents have fixed roles and limits, and the hook enforces the two rules that must never depend on memory: uploads need your approval, and nothing formats the whole folder.
- The template is copied into each competition and then belongs to it. Change `data.py`, `cv.py`, `metric.py` and `shadow.py` freely for a competition with a different shape; keep their meaning.
- Lessons live in `~/.bench/lessons.md` on your machine, seeded from `lessons/seed.md`. Add the general ones back to `lessons/seed.md` here so every new competition starts from them.

## Develop

```bash
cd template && uv sync && uv run pytest && cd ..
uv run --project template pytest tests     # the hook's tests
claude plugin validate .
```
