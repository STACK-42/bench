---
name: postmortem
description: After a leaderboard score comes back in a bench repo, check whether CV, the shadow test and the leaderboard agree, find out why if they don't, and record lessons for this and future competitions. Use after every upload's score, and at the end of a competition.
---

# Postmortem

The leaderboard is the only check you can't build yourself. Use every score to test your own checks.

## After each scored upload

1. `uv run comp scores` pulls the scores and prints the rank correlation between CV and the public board once three files are scored.
2. Compare the new file with the previous best on all three checks: CV, shadow, public board.

| what happened | what it means | what to do |
| --- | --- | --- |
| all three agree | the checks work | carry on |
| CV and shadow better, board worse by more than its noise | something in the test is missing from both checks | find it (step 3) before more uploads |
| CV better, shadow and board worse | the change fits the training data's structure, not the test's | trust shadow, drop the change |
| board better, CV and shadow worse | likely luck on the public sample | don't follow it |

3. When the board disagrees, look for what the test has that the checks don't: different dates or groups, new categories, a different mix of rows, a part of the score that changed most. Look at the parts of the score, not only the total. Build a check for the difference if you can (in Madinah, a test-day check from the test's released rows found the cause in one evening).
4. Write the finding in `experiments.md` and, if notes are on, in the notes.

## Lessons

Add a lesson to `lessons.md` in the repo whenever the method itself worked or failed: a check that caught a problem, a check that missed one, an agent mistake, a workflow that saved time. Write the lesson, the evidence (numbers), and what to do next time.

At the end of a competition, or when a lesson is clearly general, copy it to the shared file `~/.bench/lessons.md` under its problem type (create the file from `${CLAUDE_PLUGIN_ROOT}/lessons/seed.md` if missing), with the competition's name and year. Tell the person, so they can also add it to the plugin's `lessons/seed.md` for everyone.
