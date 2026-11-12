---
name: experiment
description: Run one experiment in a bench competition repo - one idea, scored on CV and the shadow test against the noise, logged, kept or dropped. Use when trying an idea, a feature, a model or a setting to improve the score.
---

# One experiment

One idea per experiment. If you change two things and the score moves, you don't know which one did it.

Commands: this skill shows the template's defaults (`uv run comp run`, `uv run comp submit`, and so on). If `comp.toml` has a `[commands]` table, use the commands named there instead. If a command is empty or missing, do that step by hand: `compare` by reading both runs from MLflow and checking each score against the noise, `noise` by running the baseline with two or three other random seeds, and `shadow` with whatever second check the repo's README describes.

## Steps

1. Pick the baseline: the best experiment so far that is better on both CV and shadow (read `experiments.md` and MLflow). Check that `noise.json` belongs to it; if not, run `uv run comp noise <baseline>`.
2. Copy the baseline to the next number in the person's folder: `experiments/<name>/NNN_short_name.py`. Never edit a file that already has a row in `experiments.md` or `submissions.md`.
3. Make the one change. Put new settings in `PARAMS`. Use `seed()` for random state.
4. Before running, check rules 3 and 4 in `AGENTS.md`: `solve` uses only `task`, and no feature looks at information the test would not have. For anything with time in it, look at every rolling window, `shift`, `bfill`, `interpolate` and centred window: each can pull the future into the past.
5. `uv run comp run experiments/<name>/NNN_short_name.py`
6. `uv run comp compare <baseline> <candidate>`. It prints every score, the gain, the noise, and KEEP or DROP.
7. Add the entry to `experiments.md` (format at the top of that file), win or lose.
8. `make lint && make test`, then commit the experiment and the log entry together.
9. If `[notes] enabled` in `comp.toml` and the finding changes the plan, explain it with the `explain` skill.

## Reading the result

- KEEP needs CV and shadow both better, each by more than twice the noise. Better on one and worse on the other means the change fits something the test does not have: drop it, or find out why.
- If a part of the score improves and another gets worse, try the change on the improving part only.
- A small gain that holds up on every fold is worth more than a large gain from one fold. Look at the fold table.
- Record the number and the reason. "Dropped: helps CV by 0.004, hurts shadow by 0.010, the setting is tuned to the days near the training data" helps the next person. "Didn't work" does not.

## When to move on

After three or four small changes in a row that drop, stop tuning and change direction: a new kind of feature, a model of the error of the current one, a different validation question. The `research` skill runs many directions at once.
