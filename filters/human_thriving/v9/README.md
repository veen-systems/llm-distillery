# human_thriving v9

**What it is:** `human_thriving v8`'s package with a **retrained student** (`adj3`). The oracle prompt,
the six dimensions and their weights, the Stage-1 e5 probe (byte-identical to v8's), the hybrid block
and the operating point (**4.5**, calibrated) are v8's, unchanged. For those, and for the lens itself,
read `../v8/README.md`. This file covers only what differs.

## What changed: the training data
1. **Every v8 label ≥ 3.5 re-judged** by blind Claude adjudication under the owner's rubric and
   rulings: 878 judged, **553 moved OUT** (none moved in); moved-out rows capped at 2.0 on all six
   dimensions. `docs/evidence/2026-09-24-thriving-adjudication-full/`.
2. **186 new production positives** (adjudicated in scope, then oracle-scored at k=3, DeepSeek V4.1)
   and **439 production hard negatives** (capped at 2.0). `docs/evidence/2026-09-24-thriving-more-positives/`.
3. Trained with v8's settings (6 epochs, batch 8, seed 42, `--select-metric recall_medium`) on b650
   (RTX 5090) at commit `bbf99b5`; epoch 5 selected. Own `calibration.json` (720 val rows).

## Label provenance: two oracle prompts are mixed (#179, owner ruling 2026-10-19)
⚠️ **The split (`datasets/training/human_thriving_v8_adj3`, 7,211 rows) carries no per-row provenance**, and its
labels come from TWO DeepSeek prompts. Joined on id to every upstream row stamping a `prompt_hash`
(`scripts/analysis/split_prompt_lineage.py <split> --roots datasets/scored ~/lab/llm-distillery`, 2026-10-19):

| upstream prompt | rows | labels equal that oracle output | labels changed after the oracle |
|---|---|---|---|
| `003cd35a5122` only (`../v8/prompt-candidate-tail.md`) | 6,130 | 5,755 | 375 (all capped ≤ 2.0) |
| `c4705408c477` only (`../v8/prompt-v8-4.md`, the live prompt) | 623 | 105 | 518 (168 capped ≤ 2.0; **350 other, not explained**) |
| both (the 456-row v8-4 relabel) | 456 | 278 v8-4, 4 either | 174 (all capped ≤ 2.0) |
| none found under those roots | 2 | — | — |

So 6,130 rows trace to the tail prompt and 1,079 to v8-4; by the label actually trained on, 5,755 are tail-prompt
output, 383 are v8-4 output, and 1,067 were changed after the oracle (the adjudication caps at 2.0 account for 717;
the 350 "other" are presumably the k=3 means of the new positives, but 350 ≠ 186, so that is NOT verified).
All are the `deepseek-chat` alias, which covered both V4 and V4.1 (EXP-042: −0.27 median shift between them).

**What differs between the prompts** (`diff` of the two files; three owner rulings of 2026-09-03, `../v8/PROMPTS.md`):
- **B (§2):** a policy change or pledge after the fact is a response, *however much of the article it occupies*;
  the *"especially as a trailing sentence"* qualifier is retired; a policy not yet in effect is an announcement.
- **C (§3):** a delisting, sanctions move or grey-list exit reaches a jurisdiction, not a person (0–2).
- **A3 (§5):** nothing has taken effect yet (proposal, draft law, plan, preparations) is excluded.

The tail-prompt rows were labelled WITHOUT these three rules. How many of them are the shape the rules decide
(policy responses, announcements, delistings) is NOT measured, so the effect on v9 is unknown. No relabelling (owner ruling): future splits carry provenance per row, legacy rows an explicit `unknown`.

## Evidence
| | v8 | v9 | source |
|---|---|---|---|
| gate, v8's 660 test ids, adjudicated labels: FP / TP of 23 | 11 / 9 | **1 / 8** | `docs/evidence/2026-09-25-v8-adj-retrain-gate/` |
| same rows, ORACLE labels: FP / TP of 35 | 9 / 11 | **1 / 8** | same |
| live week, junk share of what each publishes | 33.8% | **14.9%** | `docs/evidence/2026-09-25-v8-adj3-live-audit/` |
| live week, articles passing 4.5 per 4-hour cycle | ~32 | **~20** | same |

⚠️ **Read before quoting:** the gate's recall clause passed with zero margin; one seed; the judge
is Claude under the same rubric that produced the training labels (the owner's blind checks and
rulings are the independent part); every rate is a sample quantity. Details in each README.

## Operating point and normalization
- **4.5, ruled by the owner 2026-09-25.** Two attempts to measure junk below 4.5 failed their drift
  checks (the band is ambiguous, not measurable at that bar): `docs/evidence/2026-09-25-adj3-band-audit-2/`.
- `normalization.json` is **v9's own**, fitted at packaging time from v9's scores on a production week
  (826 articles ≥ 4.5): `docs/evidence/2026-09-25-v9-normalization/`.

## Status
`STATUS.md`.
