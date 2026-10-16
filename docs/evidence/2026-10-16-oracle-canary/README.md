# Oracle canary for human_thriving (#177) — result

**Answer: the canary works as pre-registered, and it is LIVE.** A simulated calibration drift (the prompt told to
score one point lower) FAILS every single-run canary (16–20 flips against a bar of 6). Three clean runs PASS. By the
pre-registered rule, **k = 1 ships**, at about $0.03 per canary on the scorer's own estimate. Both oracle scorers
now REFUSE to label with human_thriving's prompt (`c4705408c477…`, or its stripped form `62c947319d87…` that
`batch_scorer` hashes) unless the latest canary record is an UNUSED PASS under 6 hours old for the SAME oracle (endpoint
+ requested model). A PASS admits ONE labelling run ("every labelling run", owner 2026-10-16); `--skip-canary
"<reason>"` overrides and is stamped on every label. Live proof, every step's output in `proof.txt`: a run uses a PASS
→ a second run is refused (single-use) → `batch_scorer` on Gemini with the same prompt file is refused (another oracle)
→ `canary.py run` PASS → the next run is admitted and stamped with that record.

Pre-registration: `PREREGISTRATION.md` (commit `91895f1`, before any oracle call on the set). Design and owner
rulings: `docs/proposals/oracle-canary-177.md`. Data: lab `experiments/2026-10-16-oracle-canary/` (`MANIFEST.json`).
Every figure below is in `result.txt`, re-derived from the lab copies by `analyse.py`.

## Result (`result.txt`)

| arm | runs | k = 1 | k = 3 | predicted |
|---|---|---|---|---|
| noise (B1–B6) | 6 | F1 = 5, S1 = 0.0693 | F3 = 6, S3 = 0.0449 | F1 in 2–8 ✓; F3 in 1–4 ✗ (6: triple-vs-triple sets two noisy means against each other, as the pre-registration said it would overstate) |
| P: "one point lower" | 3 | **FAIL ×3**: 16 / 20 / 19 flips, shift −0.44 / −0.51 / −0.48 | FAIL: 18 flips, −0.48 | flips 10–30 ✓; shift −0.8 to −1.0 ✗ (the model obeyed about halfway) |
| C: clean | 3 | PASS ×3: 5 / 4 / 5 flips | PASS: 4 | PASS ✓ |
| V: v8-5 (a real small edit) | 3 | 2 PASS, 1 FAIL (8 flips) | PASS: 6 | ≤ F3 + 1 at k = 3 ✓; no required outcome |

Bar: FAIL iff flips > F + 1 or |shift| > S + 0.15. Baseline: 30 of 100 items at ≥ 4.5 (the student's 30/30/40
strata did not survive into the oracle's scores one for one — that is fine, the set needs items near 4.5, and has
them). Served model on every row: `deepseek-flash`.

## What it does NOT show — caveats

- **False-alarm rate at k = 1 is barely measured.** The only OUT-OF-SAMPLE clean runs are C1–C3 (5 / 4 / 5 flips; the
  bar fails at 7) plus two live canaries (5, 5 — `proof.txt`). The six leave-one-out B values SET the bar, so they
  cannot exceed it and are not evidence of a low false-alarm rate (review 2026-10-16). A refusal on a clean oracle will happen at some rate
  this cannot pin down; re-running the canary after a FAIL is not pre-registered and would erode the bar if made a
  habit.
- **The detection test is a SIMULATED drift.** No real model swap was available; the V4 → V4.1 swap moved 3 of 12
  hand-picked rows (EXP-042), a different population. Power against a real swap is inferred, not measured.
- **The P runs' shift was half the instructed one**, so the canary's margin over the bar (16 vs 6 flips) is for a
  ~0.5-point drift. A smaller real drift (v8-5 is an example) can pass at k = 3 and fail one k = 1 run in three.
- **Parse errors:** 20 of 1,520 calls returned malformed JSON (16 on the first passes, 4 more on resumes), one
  article accounting for 8. `canary.py run` resumes them (up to 4 passes); a canary that still cannot complete records
  NO-VERDICT, which refuses labelling like a FAIL. The resume was not in the pre-registration; it was implied by
  `cmd_baseline`'s "resume them first" (committed `5fbdd54`, before the runs).
- **Cost:** the scorer's own off-peak estimates sum to $0.53 over 29 passes (15 runs + resumes), against a
  pre-registered ≈ $2.30. The pre-registration used `oracle_cost.py`'s per-article figure; prefix-cache hits on 100
  same-prompt calls are the likely difference. An estimate, not a billing figure, and it EXCLUDES the two live
  canaries and three single-article proof runs (about $0.06 more by the same estimate).
- **#177's proposal said the v8-5 edit must FAIL** (design step 5). The pre-registration dropped that requirement
  before any data — v8-5 is a power reading — so "works as pre-registered" holds and the proposal's done-when is NOT met
  for a small real prompt edit: at k = 1 one of three v8-5 runs fails, at k = 3 none.
- Only human_thriving is guarded. Every other prompt is stamped `canary: no-set` and labels with a banner.
- Pass records live in `datasets/canary/human_thriving/passes/` on situla (gitignored): a labelling run on another
  machine finds none and is refused. A canary served by a different model than the baseline's is recorded FAIL
  whatever its flips.
