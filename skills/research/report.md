# Research report format

## Summary

Two or three sentences: what helped, by how much, on which checks.

## Every idea tried

| # | card | idea | CV (change) | shadow (change) | parts that moved | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | | baseline, reproduced | 0.00000 (0) | 0.00000 (0) | | reference |
| 1 | I-NNN | ... | -0.00000 | -0.00000 | ... | keep / drop / superseded by N |

Changes are candidate minus baseline. Say whether lower or higher is better. Use `own` in the card column for an idea that has no card. Mark a verdict "keep" only if CV and shadow both improve by more than twice the noise.

## Noise

How much the scores moved from the random seed alone, and how you averaged it away.

## To build the winners

For each kept idea: the scratch file path, and the exact change needed in the baseline (settings, new functions, new dependencies).

## Doesn't apply here

One line each for the ideas you skipped and why.

## Not tested

Anything you could not measure, said plainly.
