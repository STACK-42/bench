---
name: research
description: Send research agents to try many ML ideas at once in a bench competition repo, each in its own worktree, and collect a standard report table. Use when the person wants to explore ideas, apply a playbook or paper, or try many combinations, or when single experiments stop improving.
---

# Research with agents

Machine learning is experimental: most ideas fail, and the ones that work often work only in combination. Research agents try many variants quickly, away from the main repo. You (the main agent) stay in charge of the repo, the decisions and the uploads.

## 1. Choose directions

List three to six directions. Good sources: the person's request, `~/.bench/lessons.md`, the `experiments.md` failures (to avoid repeating them), a playbook or paper the person names, and the parts of the score that are worst. Give each direction a clear question, for example "Does a LightGBM model of the current forecast's error help, and with which mix weight?"

## 2. Write the brief

Fill `${CLAUDE_SKILL_DIR}/brief.md` once per agent. Send at most three agents at a time. More than that is hard to review and they compete for the CPU. Each agent gets one direction, the baseline experiment, the current scores, the noise, and the known failures.

## 3. Launch

Use the `bench:researcher` agent with `run_in_background: true`. It runs in its own git worktree, so it can't change the main working tree. Keep working or waiting while it runs, and don't guess its results before it reports.

The worktree starts from the default branch, not from your current branch. Commit the baseline first, and if it is not on `main`, put the branch name in the brief so the agent checks it out before it starts. The data files are not in git: give the agent the absolute path of the main repo's `data/` folder and tell it to link it into its worktree (`rmdir data && ln -s <main repo>/data data`). Don't point `COMP_ROOT` at the main repo: the agent would then write into its MLflow database and submissions.

## 4. Review the report

Every report ends with the table from `${CLAUDE_SKILL_DIR}/report.md`. Before you believe it:

- Does the baseline row reproduce the known scores exactly? If not, its harness differs, and its numbers can't be compared.
- Is every KEEP better on CV and on shadow by more than twice the noise?
- Ask the `bench:leak-auditor` agent to read the candidate code: researchers make leakage mistakes too.

## 5. Move the winners into the repo

Build the winners yourself as the next experiment number, following the `experiment` skill: copy the baseline, apply the changes, run, compare, log, commit. Your own run must confirm the agent's numbers before anything is submitted. Log the dropped ideas in `experiments.md` too, with their numbers, so nobody tries them again.

When an agent finishes, stop any background work it left running.
