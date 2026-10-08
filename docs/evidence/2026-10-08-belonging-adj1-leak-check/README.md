# belonging adj1: pre-gate leak check: RESULT (2026-10-08)

⚠️ **The tables below are RUN 2** (`20637ec`), which the gate refused before scoring (2 footer "twins"). **Run 3** (`875cb9f`,
2 rows fewer) is at the end, together with the GATE RESULT.

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

## Run 3 (`875cb9f`): leak check, GATE, and the ovr.news panel check

**Leak check: NOT LEAKED** (`result_run3.json`). Flags v1 → candidate: LONG 35 → 12, FRENCH 15 → 11 (CI [−0.035, +0.004]),
ALL 109 → 42 of 5,000. Run 3's val recall_medium is 0.759 vs run 2's 0.862 on the same 29 positives: dropping 2
negative rows moved the training trajectory that much. That is a seed-like band, not an effect.

**GATE: FAIL** (exit 1; full output `docs/evidence/2026-10-03-belonging-heldout/result_v1_adj1.txt`). **The held-out set is SPENT.**
- k = 40/44 at op 4.0 (rule ≥ 31: passes). v1 matched at t* = 5.3504.
- Weighted spec on the 163 deciding negatives: candidate 0.838 vs v1@t* 0.792; Δ +0.047, **95% CI [−0.015, +0.105]**. The rule
  needs the lower bound > 0, so it FAILS. Identical in both orders; 0/295 order flips.
- Not deciding: unweighted spec 0.804 vs 0.583; hi+mid unweighted 0.746 vs 0.404; DISPUTED stratum (n=75) candidate WORSE,
  0.472 vs 0.610 weighted.

**ovr.news EXP-028 check** (their 40 published Belonging stories, panel-rated on og:title + description; a check, not labels):
v1 passes 40/40 (by construction, being the published set). The candidate passes 13/27 weak and 7/13 non-weak (excluding
the 2 training URLs, both non-weak: 13/27 and 5/11). **It drops weak and non-weak at about the same rate**, so on ovr's reader
measure the candidate cuts volume without selecting better. It KEEPS state commemoration / political messaging (both
Alban-Udi copies, 7 October remembrance, Odinga ceasefire, Orange Shirt Day) and harm-led stories (GP-less town, Colombia
rivers, marchers). It DROPS single-person stories the panel liked (rubric v2.1 `out_one_moment`, which is where all 121 hard
negatives came from). My reading, not measured: the data reshape taught `out_one_moment` and nothing about
`out_gift_official` or `out_harm_is_story`.

**Where the dropped good stories would land (b650 GPU, not production's device; near-threshold scores can flip).** Of the 6
non-weak stories the candidate drops: human_thriving v9 (op 4.5) passes 1 (softball sisters 5.72; card game 4.24),
cultural_discovery v5 (op 4.0) passes 1 (Freedom's Daughters 4.60, though production published it under Belonging, so
production did not pass it there), uplifting v7 (op 4.5) passes 5. On all 40: v9 passes 0/27 weak and 3/13 non-weak; cd v5 3/27
and 5/13; uplifting v7 **16/27** and 10/13. A broad "inspirational" construct catches the single-person gems AND most of the weak picks.

**Owner ruling 2026-10-08 (after the FAIL):** keep v1; build candidate 2 with hard negatives only from `out_gift_official` and
`out_harm_is_story`; no new `out_one_moment` negatives; revisit single-person stories with ovr's post-switch panel.
