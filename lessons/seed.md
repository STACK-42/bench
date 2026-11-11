# Lessons across competitions

Lessons about the method, grouped by problem type. Each one says where it was
learned. `/bench:comp-start` reads this file before planning a new
competition, and `/bench:review` adds to it.

## Any competition

- Build and prove the validation before any model. Reproduce something the organisers published (the sample submission, a baseline score) with your own code first. (Madinah 2026)
- One check is not enough. Ask "what does the test have that my CV does not?" and build a second check for that difference. In Madinah, CV trained on the day next to the held-out day, while the test days were a week away. A model scored 0.821 in CV and 1.022 on the leaderboard. A test-day check built from the released test rows caught it. (Madinah 2026)
- Measure the noise before you believe a gain. Changing only the random seed of a LightGBM model moved the score by about 0.01, which was as large as most tuning gains. Average a few seeds, and keep a change only if it beats about twice the noise on every check. (Madinah 2026)
- A main agent plus research agents works. Researchers try many variants in scratch or a worktree and report a table; the main agent moves only the winners into the repo. About 30 variants in one evening, with no conflicts. (Madinah 2026)
- Never run a formatter over the whole folder. It rewrote code blocks inside a Markdown document that was not ours. (Madinah 2026)

## Time series and forecasting

- A gradient boosting model that predicts the whole value did worse than simple rules. The same model trained to predict the rules' error (a residual), and mixed half and half with them, improved CV by 0.04 and both test-day checks. Start from strong hand-made rules, then let a model correct them. (Madinah 2026)
- Calendar features matter, and their strength must be checked on data far from the training days. Lining up daily crowd curves on prayer times helped only at the mild setting; the strong setting overfit the CV. (Madinah 2026)
- Pseudo-labels made from the test's own released rows did not help here. (Madinah 2026)
