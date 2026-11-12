# Research brief (fill every <...>)

You are a research agent for the competition repo at <repo path>. Find out whether <direction> improves the score, by testing as many sensible variants and combinations as you can. Report back; don't change the main repo.

## Read first

- `comp.toml`, `README.md`, `AGENTS.md`, `experiments.md`
- the baseline: `<experiments/name/NNN_baseline.py>`
- the idea cards to test from `ideas.md`: <I-NNN, I-NNN, ...>
- <any playbook, paper or notes file the person gave>

## Where things stand

- Baseline scores: CV <x ± std>, shadow <y>, parts <...>
- Noise: the score moves by about <noise> from the random seed alone.
- Already tried and failed: <list from experiments.md, with numbers>

## How to measure

- `uv run comp run <file>` gives CV and shadow; `uv run comp compare <baseline> <file>` gives the verdict.
- For fast loops, you may write scratch scripts that call `comp.cv.folds` and `comp.shadow.evaluate` directly and swap one part of the baseline at a time.
- Your first row must reproduce the baseline's scores exactly with your harness.
- Change one thing at a time. Average random seeds where the model is random. Record mean ± std over folds.

## Rules

- You work in your own git worktree. Write experiments only under `scratch/` in that worktree. Don't commit and don't push.
- Never upload or run `comp submit`, and never call the platform's CLI to submit.
- `solve(task)` may use only `task`. No feature may use information the test would not have (no future values, no test labels).
- Format only the files you wrote.
- Data: the data files are not in git. Link the main repo's data folder into your worktree: `rmdir data && ln -s <main repo>/data data`.
- Baseline branch: <main, or the branch to check out first>.

## Report

End with the table and sections in the report format the skill gives you (`report.md`), and nothing after them.
