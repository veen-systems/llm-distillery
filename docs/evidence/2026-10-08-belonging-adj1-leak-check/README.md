# belonging adj1: pre-gate leak check: RESULT (2026-10-08)

Rule and population: `PREREGISTRATION.md` (committed in `20637ec`, before any score existed). Candidate:
`filters/belonging/v1_adj1` trained at `20637ec`, `--select-metric last` (epoch 6; run 1 at `baf7d06` kept an
undertrained epoch 1 and was discarded), calibration fitted on val. Both packages load their own model and calibration
(checked by path). Draw: 5,000 rows, window `filtered_20260910_051711 .. filtered_20261008_051442` (156 files, pool 433,274).
Full output: `result.json`.

## Verdict: NOT LEAKED (exit 0). The candidate flags FEWER rows than v1 in every group

| group | n | v1 flags | candidate flags | ratio | 95% CI of (cand − v1) |
|---|---|---|---|---|---|
| LONG (>4,000 chars) | 1,260 | 35 (2.8%) | 9 (0.7%) | 0.26 | [−0.030, −0.012] |
| FRENCH | 285 | 15 (5.3%) | 7 (2.5%) | 0.47 | [−0.053, −0.007] |
| ALL (context) | 5,000 | 109 (2.2%) | 29 (0.6%) | 0.27 | [−0.020, −0.012] |

Stage-1 split identical (0 disagreements; 3,971 stage2 / 1,029 stage1_low). One batch order (#95, the batch-composition
noise floor, not covered by the bootstrap); the gaps are 80 rows overall, far beyond a near-threshold flip count.
Only Korean moved up (0 → 2 of 117), inside noise.

## Follow-up the result raised: is the lower flag rate lost recall? (not pre-registered, run after the verdict)

The gate needs k ≥ 31 of 44 held-out positives. Proxy that does NOT touch the held-out set: the 23 harvest-r1 positives
in the candidate's TEST split (same Gemini + judge chain as the held-out positives; never trained on; calibration was fitted on val).
**v1 finds 23/23, the candidate 22/23** (the miss scores 2.36; the next two are 4.39 and 4.41, just above the 4.0 op-point).
⚠️ Optimistic as a gate predictor: these 23 come from the SAME harvest draw as the 190 training positives, while the
held-out positives were drawn separately. Measured: the candidate flags ~¼ as many production rows as v1. Guessed, not measured:
that the dropped flags are mostly v1 false positives. Only the gate's specificity arm can say.
