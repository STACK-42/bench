.PHONY: setup data check test lint format ui scores

SLUG = $(shell uv run python -c "from comp import config; print(config.load().get('competition', 'slug'))")

setup:  ## install everything into .venv
	uv sync

data:  ## download the competition files into data/ (Kaggle only; for Zindi, download by hand)
	uv run kaggle competitions download -c $(SLUG) -p data
	unzip -o data/*.zip -d data

check:  ## data, sample submission, and train/test shift
	uv run comp check

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

format:  ## only Python files that git knows about
	uv run ruff check --fix $(shell git ls-files '*.py')
	uv run ruff format $(shell git ls-files '*.py')

scores:  ## pull leaderboard scores into submissions.md
	uv run comp scores

ui:  ## browse every run at http://127.0.0.1:5000
	uv run mlflow ui --backend-store-uri sqlite:///mlflow.db
