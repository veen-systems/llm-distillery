# human_thriving v10 candidate (adj4) vs v9 — gate RESULT (2026-09-26)

**NOT DISTINGUISHABLE under the owner-ruled bar** (`PREREGISTRATION.md`, ruled before training). **v9 stays
live.** Nothing is deployed. The pre-registration said this outcome was likely.

## What ran (b650, RTX 5090, CUDA; `logs/v10_20260926.sh` then `logs/v10_post_20260926.sh` on b650)
- adj4 trained 20:42–21:33 (commit `bbbc145` checked out on b650), v9 settings; best epoch 5 (recall_medium 0.480).
- ⚠️ The first post-step staged under `staging/` and `fit_calibration.py` refused it ("Expected 'filters' in
  path"), the same failure the 09-25 run hit before its `adj_post2` fix. Re-run staged at
  `filters/human_thriving/v8_adj4` (b650 only, untracked). Own `calibration.json` on adj4's val split.
- v9 re-dumped in the same session. **Control:** it reproduces the 09-25 gate exactly (adjudicated recall 0.348,
  spec 0.998, 2 indeterminate).
- Dumps: `datasets/gate/ht_v10_2026-09-26/` (gitignored, local). Reports: `gate_*.txt/json` here.

## Primary — adjudicated labels, v8's 660 test ids (`gate_adjudicated.txt`)
| arm | recall [band] | spec [band] | indet |
|---|---|---|---|
| v9 | 0.348 [0.261, 0.348] | 0.998 [0.998, 0.998] | 2 |
| adj4 | 0.348 [0.348, 0.348] | 0.998 [0.998, 1.000] | 1 |

Clause 1 (adj4 recall `lo` > v9 recall `hi`): 0.348 > 0.348 **fails**. Clause 2 (adj4 spec `hi` ≥ v9 spec `lo`):
1.000 ≥ 0.998 holds. No LOSE condition holds. → **NOT DISTINGUISHABLE.**

## Secondary (not gating)
- **Oracle labels, same 660:** identical point figures (recall 0.229, spec 0.998); bands overlap.
- **The pool's own held-out rows** (65: the adj4 test additions, 15 labels ≥ 4.5, 50 below; design-weighted
  toward production ≥ 7 articles): v9 recall 0.867 [0.667, 0.867], spec 0.940; **adj4 recall 0.600
  [0.600, 0.667], spec 0.980**. Spec bands do not overlap; recall bands overlap. **adj4 is STRICTER, not more
  generous:** the ≥ 7 pool did not buy volume. *Gloss (not measured):* 471 capped negatives vs 177 positives
  moved it toward caution.
- **Owner-flagged articles (must-reject):** both arms reject all 3 (v9 3.171 / 1.172 / 1.074; adj4 3.146 /
  1.169 / 1.112). ✅

## What next (owner)
Per the pre-registration: report; v9 stays live. Options, not ruled: (a) stop here: v9 is the model;
(b) an adj2-style diagnostic (positives only, no pool negatives) to test the gloss above; (c) a seed band
before reading any more single-seed comparisons (EXP-015).
