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

## Diagnostic (b) — adj4p RESULT (2026-09-27; rule fixed in `PREREGISTRATION.md` before training)
**Gloss SUPPORTED: the 471 capped negatives, not the positives, made adj4 stricter.** adj4p (adj3 + 177 positives,
no pool negatives) trained 09:59–10:51 on b650 (`logs/adj4p_20260927.sh`), best epoch 3, own calibration; staged at
`filters/human_thriving/v8_adj4p` (b650 only, untracked). Reports: `adjp_{gate,oracle,pool}.{txt,json}`.

| population | arm | recall [band] | spec [band] |
|---|---|---|---|
| pool held-out (65; 15 pos) | v9 | 0.867 [0.667, 0.867] | 0.940 [0.940, 0.940] |
| | adj4 | 0.600 [0.600, 0.667] | 0.980 [0.980, 0.980] |
| | **adj4p** | **0.933 [0.933, 0.933]** | **0.860 [0.860, 0.900]** |
| 660, adjudicated labels | v9 | 0.348 [0.261, 0.348] | 0.998 [0.998, 0.998] |
| | adj4 | 0.348 [0.348, 0.348] | 0.998 [0.998, 1.000] |
| | **adj4p** | **0.522 [0.478, 0.522]** | **0.994 [0.992, 0.997]** |
| 660, oracle labels | v9 | 0.229 [0.171, 0.229] | 0.998 [0.998, 0.998] |
| | adj4 | 0.229 [0.229, 0.229] | 0.998 [0.998, 1.000] |
| | **adj4p** | **0.371 [0.314, 0.371]** | **0.995 [0.994, 0.997]** |

- **Rule clause 1:** adj4p pool recall `lo` 0.933 > adj4 `hi` 0.667 → **the negatives caused the strictness.**
- **Rule clause 2** (adj4p `hi` < v9 `lo`) does **not** hold. The rule named no conclusion for the other direction;
  *observed, not ruled:* adj4p's recall band sits above v9's on all three populations, and its **specificity
  band sits below v9's on all three**. *Gloss, not ruled:* consistent with positives adding volume at a specificity cost (one seed).
- **Owner flags (must-reject): all 3 rejected** (3 of 3) — adj4p 2.853 / 1.911 / 1.360 (v9 and adj4 reproduce
  yesterday's 3.171 / 1.172 / 1.074 and 3.146 / 1.169 / 1.112 exactly: the control). File: `flagged3_weighted.json`.
- *Gloss:* under adj4's bar (adj4p has none of its own) it would meet the LOSES condition, spec `hi` 0.997 < v9
  `lo` 0.998 on the adjudicated 660, while clause 1 (recall `lo` 0.478 > 0.348) would have passed. It is
  diagnostic and nothing is deployed; v9 stays live.
- ⚠️ Every band here is the #95 batch-composition band only; single seed (EXP-015), and on the pool one article
  is 0.067 recall. Measured counts: pool positives caught v9 13, adj4 9, adj4p 14 of 15; pool false positives
  v9 3, adj4 1, adj4p 7 of 50. ⚠️ `PREREGISTRATION.md` describes the pool held-out as 18 positives / 47 negatives;
  the gate reports read 15 / 50 at on-lens := oracle ≥ 4.5. Unexplained here; the reports are what was measured.

## What next (owner)
Per the pre-registration: report; v9 stays live. Options, not ruled: (a) stop here: v9 is the model;
(b) an adj2-style diagnostic (positives only, no pool negatives) to test the gloss above; (c) a seed band
before reading any more single-seed comparisons (EXP-015).
