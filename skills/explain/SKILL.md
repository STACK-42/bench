---
name: explain
description: Write learning notes in a comp-lab competition repo - explain a finding, technique or metric detail in three layers (plain idea, worked example, formula or code) in simple English, and keep a glossary. Use when notes are enabled in comp.toml and a finding changes the plan, a new technique is introduced, or the person asks why something happened.
---

# Explain a finding

Use this only when `[notes] enabled = true` in `comp.toml`. The notes are for the people on the team to learn from, so they must make sense to someone who knows classical machine learning and is new to the technique.

## Where

- `notes/index.html` lists every page.
- One page per topic: `notes/NN-short-topic.html`. Keep a status page (`notes/NN-where-we-stand.html`) with a status box at the top, a section per finding, and a log table at the bottom; update it after every upload, leaderboard score and finding that changes the plan.
- `notes/glossary.html`: every special word, the first time it appears anywhere.

Plain HTML with one small inline stylesheet, readable offline. Diagrams as inline SVG when a picture says it faster.

## Three layers, always in this order

1. The idea in plain words, and its closest cousin in classical ML ("this is like stacking, but ...").
2. A worked example with real numbers from the competition, or small made-up ones.
3. The formula or the code, short, with each symbol explained.

## Language

Follow `[notes] style` in `comp.toml`. By default:

- Simple English for readers who use English as a second language: short sentences, common words, no idioms.
- Explain each special word the first time it appears, and add it to the glossary.
- State the finding and the number. No filler.

The same rules apply to chat replies about the work: keep them short, give the number, and point to the notes page.
