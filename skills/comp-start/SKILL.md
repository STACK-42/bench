---
name: comp-start
description: Start a new machine learning competition (Kaggle or Zindi) from the bench template - create the repo, fill comp.toml, and build and prove the validation before any model. Use when the person wants to begin or set up a competition or ML project.
---

# Start a competition

The goal of every competition is the best final score. Most lost competitions are lost here, in validation, not later in modelling. So this skill ends with a validation you can trust and one baseline, and nothing more.

Work through the steps in order. Tell the person what you found after steps 2, 4 and 6.

## 1. Gather the facts

Ask only for what you can't find yourself: the competition URL, and solo or team (and the teammates' GitHub logins for a team). Then read, from the competition page and data page:

- the task, the target, the metric (exact formula, and whether lower is better)
- the files and their columns, the id column, the sample submission
- the public/private leaderboard split, if stated
- daily upload limit, final pick count, deadline (with time zone)
- rules on external data and pretrained models

Save the page text in `docs/competition.md`. Read the shared lessons, `~/.bench/lessons.md` (create it from `${CLAUDE_PLUGIN_ROOT}/lessons/seed.md` if it is missing), and note which ones apply.

## 2. Create the repo

```bash
cp -R "${CLAUDE_PLUGIN_ROOT}/template" <new-folder>
cd <new-folder> && git init -b main
```

- Fill `comp.toml`, the `description` in `pyproject.toml`, and the top of `README.md`.
- Create `experiments/<name>/` for each person in `[team] people` and remove `experiments/me/` if unused.
- If `[notes] enabled`, create `notes/index.html` and `notes/glossary.html` (see the `explain` skill for the style).
- `uv sync`, `make data` (Kaggle) or download by hand (Zindi), then `make test`.
- Make the first commit on `main`, create a private GitHub repo with `gh repo create --private --source . --push`, and check that CI passes.

## 3. Make the metric exact

If the metric is not one of the built-in names in `src/comp/metric.py`, write it there, with a test using numbers you compute by hand. If the score averages several parts (several targets, several kinds of rows), return each part too.

Prove it: reproduce any score the organisers published (a baseline, the sample submission's score) to several decimals. Write in `README.md` what you reproduced.

## 4. Answer: how does the test differ from the training data?

This is the most important question in the whole competition. Look at the data, not just the description:

- Run `uv run comp check`. An adversarial AUC near 0.5 means train and test look alike; above about 0.75 means they differ.
- Time: does the test come after the training data? Then `[cv] scheme = "time"` and set `time_column`.
- Groups: does the test contain new users, patients, places or days? Then `scheme = "group"` and set `group_column`.
- Distance: how far is the test from the nearest training row (in days, in groups)? CV must not be closer than that.
- New categories in the test that never appear in training.

Write the answer in `README.md` under "How we validate". If the data has a shape the default `data.py` and `cv.py` don't fit (time series with holes, images, several tables), rewrite those two files now, keeping `Task`, `folds` and `cross_validate` with the same meaning.

## 5. Build the shadow test

`src/comp/shadow.py` holds out the most test-like training rows, or the latest rows by time. Replace `holdout` if you know something better, for example rows the organisers released from the test period. The rule: the shadow test must copy the difference you found in step 4 more closely than CV does.

## 6. Baseline and noise

- Copy `experiments/_template.py` to `experiments/<name>/001_baseline.py` and make it a simple, honest model.
- `uv run comp run experiments/<name>/001_baseline.py`
- `uv run comp noise experiments/<name>/001_baseline.py`
- Submit the baseline once (with the person's approval, see the `submit` skill). Check that the leaderboard score is close to CV and shadow. If not, the validation is wrong: go back to step 4 before any modelling.

## Done when

- the metric is reproduced, CV and shadow are built, and the reason for each is written down
- the baseline's leaderboard score agrees with CV and shadow
- the noise is measured
- CI is green

Then continue with the `experiment` and `research` skills.
