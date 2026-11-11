# Rules for coding agents

This is a machine learning competition repo made from the comp-lab template. Its one goal is the best final score. `comp.toml` says which competition, which metric, solo or team, and whether to write learning notes. Read it, `README.md` and `experiments.md` before you change anything.

## How a score is trusted

Every experiment gets two scores from `uv run comp run <experiment>`:

- CV: cross-validation on the training data (see `src/comp/cv.py`).
- shadow: a holdout built to look like the real test (see `src/comp/shadow.py`).

A change is kept only if it is better on both, by more than the noise. Measure the noise once per baseline with `uv run comp noise <experiment>`, then decide with `uv run comp compare <baseline> <candidate>`. The public leaderboard is a third, noisy check. It never overrules the other two on its own.

## Hard rules

1. Never write a submission file by hand. Use `uv run comp run <experiment> --submit`. It names the file `submission<CV>.csv`, refuses to run on uncommitted code, and records the commit in `submissions.md`.
2. Commit a new submission file together with its row in `submissions.md`, and name the file in the commit message.
3. `solve(task)` may use only what is in `task`. It must learn from `task.train` each time it is called, and never read `data/` itself. Anything else leaks the held-out rows into training and makes the scores meaningless.
4. Features for a row may use only information the real test would have for that row. Think about time: no feature may look at the future of the row it describes.
5. If you change how folds, the shadow holdout or the metric work in a way that moves scores, raise `CV_VERSION` in `src/comp/cv.py`.
6. Don't edit an experiment that already has a row in `experiments.md` or `submissions.md`. Copy it to the next number.
7. In team mode, stay in the experiments folder of the person you are working for. Never edit another person's folder. Copy from it instead.
8. Never commit `data/`, `mlflow.db`, `mlruns/` or `noise.json`.
9. Uploads use the team's few daily submissions and can't be taken back. Run `uv run comp submit` only when the person asked you to upload that specific file. Never upload through the platform's CLI directly, because the score then never reaches `submissions.md`.
10. Format only the files you changed (`make format` formats tracked Python files only). Never run a formatter over the whole folder: it can rewrite other people's notes and documents.

## After every experiment

Add an entry to `experiments.md` using the format at the top of that file: CV ± std, shadow, the parts of the score, and one or two sentences on what the result tells us. Record failures too.

If `[notes] enabled = true` in `comp.toml`, explain each finding that changes the plan in `notes/`, in the style given there, and add new words to `notes/glossary.html`.

To read past runs, query MLflow:

```bash
uv run python -c "
import mlflow; mlflow.set_tracking_uri('sqlite:///mlflow.db')
r = mlflow.search_runs(experiment_names=['comp'])
print(r[['tags.mlflow.runName','tags.owner','metrics.cv_score','metrics.cv_std','metrics.shadow_score']])"
```

## Code

- Short functions with a docstring that says what goes in and what comes out.
- A comment where a line makes a modelling decision, saying why.
- No clever abstractions. A little repetition between experiments is fine.
- `make lint` and `make test` must pass before you commit.
