---
name: submit
description: Plan and make leaderboard uploads in a bench competition repo - choose which files to spend the day's few uploads on, upload with the person's approval, record the score, and pick the final submissions near the deadline. Use when the person wants to submit, upload, check the leaderboard, or choose final submissions.
---

# Submit

Uploads are scarce (a few per day) and can't be taken back. The public leaderboard is a sample of the test: useful as a third check, never as the only one.

## Make the file

1. The experiment must be committed. `uv run comp run <experiment> --submit` writes `submissions/submission<CV>.csv` and its row in `submissions.md`.
2. Commit the file and its row together, naming the file in the message.

## Plan the day

- `uv run comp submit` prints the remaining uploads. Kaggle limits reset at 00:00 UTC.
- Spend uploads on questions, not hope. Good uses: a candidate that is better on CV and shadow; a check of whether CV and leaderboard still agree (the first upload after a validation change). Bad uses: small tuning steps inside the noise.
- Upload the most promising file first, so later uploads can depend on what it shows.
- If the limit is used up, say so and wait. With `/loop`, schedule a wakeup shortly after the reset, and fill the wait with research.

## Upload

Upload only a file the person asked you to upload, or that falls under a standing instruction they gave in this conversation (for example "submit it when it's ready"). Then:

```bash
uv run comp submit submissions/submission<CV>.csv -m "<what changed, in a few words>" --yes
```

The bench hook shows the person a permission prompt for every `comp submit`; their approval there is the confirmation, which is why `--yes` is fine after it. Never upload through the platform's own CLI, and never from a research agent.

Zindi has no upload API here: `comp submit` checks the file and prints what to upload and the comment to use. After the person uploads it, record the score with `uv run comp scores --set <file> <score>`.

## Afterwards

- Commit `submissions.md` with the new score.
- Run the `review` skill: did the leaderboard move the way CV and shadow said?
- If `[notes] enabled`, update the notes' status page.
- If the file beats the best score so far, push and merge the work the way the repo's rules say.

## Final picks

Near the deadline, choose the files that count for the private leaderboard (`final_picks` in `comp.toml`):

1. The best file by CV and shadow together, even if another file has a better public score. The public board is only part of the test.
2. If there is a second pick: a file that is good on every check but differs in method (a hedge), not a near copy of the first.

Write down the choice and the reason in `submissions.md` and tell the person before the deadline. The person makes the final selection on the platform.
