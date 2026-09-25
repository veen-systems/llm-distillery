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
