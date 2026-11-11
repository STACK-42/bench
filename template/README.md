# CHANGE-ME competition

CHANGE-ME: what the competition asks for, in one or two sentences, and its deadline.

Made from the bench template. `comp.toml` describes the competition; `AGENTS.md` has the rules for coding agents.

## Setup

You need [uv](https://docs.astral.sh/uv/).

```bash
make setup    # uv sync
make data     # download the data into data/ (Kaggle); for Zindi, download by hand
make check    # the data, the sample submission, and how different train and test look
make test
```

## Run an experiment

```bash
cp experiments/_template.py experiments/me/001_baseline.py
uv run comp run experiments/me/001_baseline.py
```

This prints the CV score per fold, the shadow score, and logs everything to MLflow (`make ui` to browse). Then:

```bash
uv run comp noise experiments/me/001_baseline.py            # once per baseline
uv run comp compare experiments/me/001_baseline.py experiments/me/002_idea.py
```

`compare` says keep only if the candidate is better on CV and on the shadow test, each by more than twice the noise.

## Make a submission

```bash
git commit -am "..."     # a submission must come from a clean commit
uv run comp run experiments/me/002_idea.py --submit
git add submissions.md submissions/ && git commit -m "Add submission0.12345.csv from 002_idea"
uv run comp submit submissions/submission0.12345.csv -m "optional note"
uv run comp scores       # later: pull the leaderboard scores into submissions.md
```

## How we validate

- CV copies how the test differs from the training rows: plain k-fold, groups kept together, or later periods predicted from earlier ones (`[cv] scheme` in `comp.toml`).
- The shadow test holds out the training rows that look most like the test, or the latest rows when there is a time column. `comp check` prints the adversarial AUC: near 0.5 means train and test look alike, and above about 0.75 means they differ.
- The public leaderboard is a sample of the test. It decides nothing on its own.
