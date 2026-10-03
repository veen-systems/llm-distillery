# Belonging v1 label adjudication (plan phase 3): rules fixed BEFORE judging (2026-10-03)

> ⛔ **The label rule below is SUPERSEDED** by the owner's ruling after the owner checks (`README.md` § *Ruling*):
> demote only rows where both judges said `out_one_moment` (238), drop the other moved-out rows (566), keep 55.
> The build reads `treatment.jsonl` from `adjudicate.py ruling`, never `verdicts.jsonl`'s `outcome`.

**Owner ruling (2026-10-03):** clean v1's data before harvesting more.

## The pool

Every row of v1's train/val/test splits (b650 `~/llm-distillery/datasets/training/belonging_v1/`, copied to the
gitignored `datasets/belonging_v1_adj/`) whose label weighted average is **≥ 3.5**. The weighted average uses v1's
weights and gatekeeper from `filters/belonging/v1/base_scorer.py`.

| split | rows ≥ 3.5 |
|---|---|
| train | 684 |
| val | 87 |
| test | 88 |
| total | 859 |

253 of the 859 have under 500 characters of content.

## The judging

The frozen rubric v2.2 (sha `d450b79510418cf7`) and `judge_instructions_v2.md` verbatim. Two blind passes of
Claude Opus 5.5 subagents on different shuffles, with opaque ids. The judges see the row's stored title, url and
content, with no label, score or split. Earlier pilot verdicts are NOT reused: they were made under rubric v1/v2.0.

## The label rules (fixed now)

| judges | label |
|---|---|
| both `in_scope` | v1's labels unchanged |
| both out (any `out_*`) | **moved out**: every dimension → `min(label, 2.0)` |
| split, or any `cannot_judge` | v1's labels unchanged (no evidence to move it); counted and reported |

Rows below 3.5 are not judged and keep v1's labels. Test rows are adjudicated too: phase 6 gates on v1's test ids
with the adjudicated labels.

## Reported

- the counts per split per outcome
- A/B agreement
- the share moved out
- 10 rows for the owner: 5 moved-out, 5 kept-in, seed 20261007
