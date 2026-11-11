"""Command line: `comp run`, `noise`, `compare`, `check`, `submit` and `scores`.

An experiment is a Python file that defines

    def solve(task: Task) -> pd.Series   # a prediction per test id
    PARAMS = {...}                       # optional, logged to MLflow

`run` scores it twice: cross-validation and the shadow test (see shadow.py).
With --submit it also solves the real test set and writes
submissions/submission<cv>.csv with a row in submissions.md.
"""

import argparse
import importlib.util
import json
import os
import subprocess
import sys

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")  # MLflow prints a hint on import
from pathlib import Path

import pandas as pd

from comp import config, paths
from comp.data import load_raw, real_task


def load_experiment(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    if not callable(getattr(module, "solve", None)):
        raise SystemExit(f"{path} must define solve(task)")
    return module


def run(args: argparse.Namespace) -> None:
    import mlflow

    from comp import ledger, shadow, tracking
    from comp.cv import cross_validate

    path = Path(args.experiment).resolve()
    script = str(path.relative_to(paths.ROOT))
    owner = path.parent.name
    module = load_experiment(path)
    state = tracking.git_state()
    untracked = not tracking.git("ls-files", script)
    if args.submit and (state["dirty"] or untracked):
        raise SystemExit(
            "Commit your changes first. A submission must come from a clean commit, "
            "otherwise its row in submissions.md points at code that never existed."
        )
    seeds = args.seeds or config.load().get("cv", "seeds", 1)
    params = getattr(module, "PARAMS", {})
    with tracking.run(path.stem, owner, script, params, seeds) as active:
        task = real_task()
        result = cross_validate(module.solve, task.train, seeds=seeds)
        tracking.log_cv(result)
        print(result.folds.round(5).to_string(index=False))
        parts = "  ".join(f"{k} {v:.5f}" for k, v in result.parts.items())
        print(f"\nCV score: {result.score:.5f} ± {result.std:.5f} (std over folds)  {parts}")

        shadow_score = ""
        if not args.no_shadow:
            scores, how = shadow.evaluate(module.solve, task)
            tracking.log_shadow(scores, how)
            shadow_score = f"{scores['score']:.5f}"
            print(f"shadow:   {shadow_score}  ({how})")

        direction = "lower" if config.load().lower_is_better else "higher"
        print(f"({config.load().metric}: {direction} is better)")

        if args.submit:
            frame = ledger.build(module.solve(task), load_raw()["sample_submission"])
            row = {
                "CV": f"{result.score:.5f}",
                "CV std": f"{result.std:.5f}",
                "shadow": shadow_score,
                "experiment": f"`{script}`",
                "owner": owner,
                "commit": f"`{state['commit'][:10]}`",
                "MLflow run": f"`{active.info.run_id}`",
            }
            name = ledger.write(frame, row)
            mlflow.set_tag("submission", name)
            print(f"\nwrote submissions/{name} and its row in submissions.md. Commit both.")


def noise(args: argparse.Namespace) -> None:
    """Run the same experiment with several random seeds and save how much the score moves."""
    scores = []
    for seed in range(args.repeats):
        env = {**os.environ, "COMP_SEED": str(seed), "COMP_NOISE_RUN": "1"}
        command = [sys.executable, "-m", "comp.cli", "run", args.experiment, "--no-shadow"]
        out = subprocess.run(command, env=env, capture_output=True, text=True, cwd=paths.ROOT)
        line = next((x for x in out.stdout.splitlines() if x.startswith("CV score:")), None)
        if line is None:
            raise SystemExit(out.stdout + out.stderr)
        scores.append(float(line.split()[2]))
        print(f"seed {seed}: CV {scores[-1]:.5f}")
    spread = float(pd.Series(scores).std(ddof=0))
    paths.NOISE.write_text(
        json.dumps({"experiment": args.experiment, "scores": scores, "std": spread}, indent=2)
    )
    print(f"\nnoise: CV moves by ±{spread:.5f} from the random seed alone. Saved to noise.json.")
    print("A change must beat the baseline by more than twice this to count.")


def compare(args: argparse.Namespace) -> None:
    """Compare the latest runs of two experiments on every logged score, against the noise."""
    from comp import tracking

    runs = tracking.latest_runs()
    if runs.empty:
        raise SystemExit("No runs yet.")
    if "tags.noise_run" in runs:
        runs = runs[runs["tags.noise_run"] != "true"]  # noise runs skip the shadow test
    picked = {}
    for name in (args.baseline, args.candidate):
        stem = Path(name).stem
        match = runs[runs["tags.mlflow.runName"] == stem]
        if match.empty:
            raise SystemExit(f"no run named {stem}. Run it first with `comp run`.")
        picked[stem] = match.iloc[0]
    (base_name, base), (cand_name, cand) = picked.items()
    metrics = [c for c in runs.columns if c.startswith("metrics.") and c != "metrics.cv_std"]
    noise_std = json.loads(paths.NOISE.read_text())["std"] if paths.NOISE.exists() else None
    lower = config.load().lower_is_better
    rows, verdicts = [], []
    for column in metrics:
        a, b = base[column], cand[column]
        if pd.isna(a) or pd.isna(b):
            continue
        gain = (a - b) if lower else (b - a)  # positive = candidate is better
        rows.append({"score": column.removeprefix("metrics."), base_name: a, cand_name: b,
                     "gain": gain})  # fmt: skip
        if column in ("metrics.cv_score", "metrics.shadow_score"):
            verdicts.append(gain > 2 * noise_std if noise_std is not None else gain > 0)
    if len(verdicts) < 2:
        print("Both runs need a CV and a shadow score. Rerun them without --no-shadow.")
        verdicts.append(False)
    print(pd.DataFrame(rows).round(5).to_string(index=False))
    measured = f"±{noise_std:.5f}" if noise_std is not None else "not measured"
    print(f"\nnoise (from noise.json): {measured}")
    if noise_std is None:
        print("Run `comp noise <baseline>` once, so small gains are not mistaken for real ones.")
    keep = bool(verdicts) and all(verdicts)
    print("verdict:", "KEEP: better on every check" if keep else "DROP: not better on every check")


def check(_: argparse.Namespace) -> None:
    """Check the data, the sample submission, and how different train and test look."""
    from comp import ledger, shadow

    raw, cfg = load_raw(), config.load()
    sample = raw["sample_submission"]
    print(f"train {raw['train'].shape}, test {raw['test'].shape}, sample {sample.shape}")
    for role in ("train", "test"):
        if cfg.id_column not in raw[role]:
            raise SystemExit(f"{role} has no id column {cfg.id_column!r}: fix comp.toml")
    if cfg.target_column not in raw["train"]:
        raise SystemExit(f"train has no target column {cfg.target_column!r}: fix comp.toml")
    if set(sample.iloc[:, 0]) != set(raw["test"][cfg.id_column]):
        raise SystemExit("the sample submission's ids are not the test ids")
    targets = list(sample.columns[1:])
    baseline = sample.set_index(sample.columns[0])[targets]
    ledger.build(baseline if len(targets) > 1 else baseline[targets[0]], sample)
    print("the sample submission builds into a valid file")
    _, auc = shadow.test_likeness(raw["train"], raw["test"])
    verdict = "they look alike" if auc < 0.6 else "they differ: trust the shadow test"
    print(f"adversarial AUC, train vs test: {auc:.3f} ({verdict})")


def submit(args: argparse.Namespace) -> None:
    from comp import ledger, platforms

    name = Path(args.file).name
    rows = {r["file"]: r for r in ledger.read_map()}
    if name not in rows:
        raise SystemExit(f"{name} has no row in submissions.md. Make it with `comp run --submit`.")
    row = rows[name]
    if row["public LB"] and not args.again:
        raise SystemExit(f"{name} was already uploaded ({row['public LB']}). Pass --again.")
    problem = _git_problem(name, row["commit"])
    if problem:
        raise SystemExit(f"Not submitting {name}: {problem}")
    ledger.build(
        pd.read_csv(paths.SUBMISSIONS / name).set_index(load_raw()["sample_submission"].columns[0]),
        load_raw()["sample_submission"],
    )  # same checks as when it was written, in case the file was edited
    message = f"{name} | {row['experiment']} | {row['commit']} | CV {row['CV']}"
    message += f" | {args.message}" if args.message else ""
    print(f"file     {name}\nmessage  {message}\n{platforms.limits()}")
    if not args.yes:
        if not sys.stdin.isatty():
            raise SystemExit("No terminal to confirm on. Pass --yes once the person has agreed.")
        if input("Upload it and use one of today's submissions? [y/N] ").strip().lower() != "y":
            raise SystemExit("Cancelled. Nothing was uploaded.")
    if not platforms.upload(paths.SUBMISSIONS / name, message, wait=not args.no_wait):
        raise SystemExit("The upload failed (see above). `comp scores` picks it up if it went.")
    platforms.sync_scores()
    value = {r["file"]: r["public LB"] for r in ledger.read_map()}[name]
    print(f"\npublic LB for {name}: {value or 'not recorded yet'}. Commit submissions.md.")


def _git_problem(name: str, commit: str) -> str | None:
    """Why the file can't be traced to a commit, or None if it can."""
    rel = f"submissions/{name}"

    def git(*a: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *a], cwd=paths.ROOT, capture_output=True, text=True)

    if git("ls-files", "--error-unmatch", rel).returncode != 0:
        return f"{rel} is not committed. Commit it with its row in submissions.md first."
    if git("status", "--porcelain", "--", rel).stdout.strip():
        return f"{rel} has uncommitted changes, so it no longer matches its row."
    if git("rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}").returncode != 0:
        return f"commit {commit} from submissions.md is not in this repository's history."
    return None


def scores(args: argparse.Namespace) -> None:
    from comp import ledger, platforms

    if args.set:
        name, value = args.set
        ledger.set_cell(Path(name).name, "public LB", value)
        print(f"recorded {name}: public LB {value}")
    for name, value in platforms.sync_scores():
        print(f"updated {name}: public LB {value}")
    rows = []
    for row in ledger.read_map():
        try:
            rows.append({"file": row["file"], "CV": float(row["CV"]),
                         "public LB": float(row["public LB"])})  # fmt: skip
        except ValueError:
            continue  # not uploaded yet, pending, or error
    if not rows:
        print("No scored submissions yet.")
        return
    frame = pd.DataFrame(rows).sort_values("CV", ignore_index=True)
    print(frame.to_string(index=False))
    if len(frame) >= 3:
        rho = frame["CV"].rank().corr(frame["public LB"].rank())
        print(f"\nrank correlation, CV vs public LB: {rho:+.2f} (+1 = same order)")
    print("Commit submissions.md if it changed.")


def main() -> None:
    pd.set_option("display.width", 200)
    parser = argparse.ArgumentParser(prog="comp", description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(required=True)

    p = commands.add_parser("run", help="cross-validate and shadow-test an experiment")
    p.add_argument("experiment")
    p.add_argument("--seeds", type=int, help="fold layouts (default: comp.toml)")
    p.add_argument("--no-shadow", action="store_true", help="skip the shadow test")
    p.add_argument("--submit", action="store_true", help="also write a submission file")
    p.set_defaults(func=run)

    p = commands.add_parser("noise", help="measure how much the score moves by seed alone")
    p.add_argument("experiment")
    p.add_argument("--repeats", type=int, default=3)
    p.set_defaults(func=noise)

    p = commands.add_parser("compare", help="keep or drop: candidate vs baseline")
    p.add_argument("baseline")
    p.add_argument("candidate")
    p.set_defaults(func=compare)

    p = commands.add_parser("check", help="check the data, the sample and train/test shift")
    p.set_defaults(func=check)

    p = commands.add_parser("submit", help="upload a mapped submission file")
    p.add_argument("file")
    p.add_argument("-m", "--message", help="a note added to the upload message")
    p.add_argument("--yes", action="store_true", help="skip the question (the person agreed)")
    p.add_argument("--again", action="store_true", help="allow a second upload of a file")
    p.add_argument("--no-wait", action="store_true", help="don't wait for the score")
    p.set_defaults(func=submit)

    p = commands.add_parser("scores", help="pull leaderboard scores into submissions.md")
    p.add_argument("--set", nargs=2, metavar=("FILE", "SCORE"), help="record a score by hand")
    p.set_defaults(func=scores)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
