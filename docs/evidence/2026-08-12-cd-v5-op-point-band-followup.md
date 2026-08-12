# `cultural_discovery v5` at the operating point — #109 arm A follow-up

**Date:** 2026-08-12
**Issue:** #109 (arm A follow-up; owner approved the ~$0.40 spend)
**Status:** **PRE-REGISTERED — sample drawn, rule fixed, oracle not yet run.**
**Parent:** `docs/evidence/2026-08-12-cd-v5-cross-oracle-arm-a.md`
**Reproduce (sampling):**
```
PYTHONPATH=. python3 scripts/research/cd_v5_arm_a_sample.py \
  --splits-dir <splits> --meta <merged-scored> --out-dir <scratch> \
  --n 66 --noise-pairs 20 --seed 20260813 --restrict-min 4.0 \
  --bands "4.0:5.0,5.0:6.0,6.0:7.0,7.0:10.01" --exclude-design <arm_a>/design.json
```

## Why this exists

Arm A returned a bounded null corpus-wide (`D` = −0.0045, CI [−0.216, +0.195],
ν = 0.436). Its band table did not:

| band | pairs | `D` |
|---|---|---|
| `[0,0.5)` | 28 | −0.102 |
| `[0.5,1.5)` | 62 | −0.164 |
| `[1.5,2.5)` | 33 | −0.072 |
| `[2.5,4.0)` | 18 | +0.294 |
| **`[4.0,10]`** | **9** | **+1.044** |

Two reasons that is worth $0.40 rather than a footnote. First, **ADR-023 says the
thin band at the operating point is the only place a decision lives**, and arm A's
registered primary is a corpus-wide mean in which that band is 9 of 150 pairs.
Second, the sign flips there: it is the one region pointing toward *less*
defensible refused labels.

**+1.044 on 9 pairs is a hypothesis and is not cited as a result anywhere.** This
run exists to kill it or keep it.

## Design differences from arm A

Same instrument, three changes:

1. **Restricted to stored ≥ 4.0**, the runtime op-point from
   `base_scorer.py TIER_THRESHOLDS`.
2. **Finer matching bands** — `[4,5) [5,6) [6,7) [7,10]` instead of one wide
   `[4,10]` band. The wide band spans 6 points of label, and matching inside it
   would have permitted exactly the imbalance #105 showed dominates an unmatched
   comparison. It costs capacity: 88 pairable pairs at one band, **66** at four.
   Matching bought with capacity is the right trade here, because the effect under
   test is larger than the resolution lost.
3. **The 9 pairs arm A already scored are excluded** (`--exclude-design`), so this
   sample is independent of already-observed data and can carry its own
   pre-registration. Pooling the two is reported as a **secondary**, never as the
   registered primary.

Matching achieved: mean stored label **4.652 refused vs 4.666 passed**; 33 cells;
median content length 1,700 vs 1,966 chars.

## This is a near-census, and that changes what the CI means

Pair capacity at four sub-bands is 66 and `n = 66`. The Horvitz-Thompson weight
is **1.0**: every pairable pair in the op-point band is in the sample.

So there is no selection uncertainty *between* cells. What remains is (a) which
refused row is taken inside a cell where `|refused| > |passed|`, and (b) oracle
sampling noise. The bootstrap CI is therefore reported in the super-population
sense — "what would this measurement give on another draw of comparable articles"
— and **the binding constraint on interpretation is ν, not the CI.** With a
census, a CI that excludes zero is close to guaranteed for any non-zero true
difference; the noise floor is what stops that from being over-read.

**Population:** 100 refused and 649 passed rows at stored ≥ 4.0 and ≥300 chars.
The refused side is 100 rows, so the op-point region of this corpus is *small* —
2.2% of the 4,458 refused rows. Whatever comes back, it is a statement about 100
articles, and no reading may inflate it into a corpus property.

## Decision rule — fixed before any score was seen

Identical in form to arm A's, with ν re-measured for this band:

**Primary:** `D₄ = MAD_refused − MAD_passed` over the 66 pairs, paired within
cell, bootstrapped 10,000×.

**MATERIAL iff** the 95% CI excludes 0 **AND** `|D₄| ≥ ν₄`.

**ν₄ is measured on this band, not inherited from arm A's 0.436.** Arm A's ν was
arm-asymmetric (0.238 off-lens vs 0.634 on-lens) because off-lens rows return
zeros from both runs and agree trivially. Every row here is high-scoring, so ν₄
should be expected *above* 0.436, and using arm A's figure would be the same
wrong-instrument error one level down. 20 pairs are re-scored a second time
(40 rows).

**Pre-registered outcomes:**

| result | reading |
|---|---|
| `D₄` within noise | The +1.044 was small-sample noise. Arm A's null then holds *including* at the op-point, and #105's cd half closes without residue. |
| `D₄` material, refused worse | The corpus-wide null is real but **does not extend to where decisions are made**: at the op-point, refused rows' labels are less defensible. `human_thriving` v8's corpus stopping condition must then be evaluated at the op-point, not corpus-wide — and arm A's headline must never be quoted without this. |
| `D₄` material, refused better | The lens gate is refusing the better-labelled rows in the only band that matters. Would need its own investigation before any retrain. |
| CI excludes 0 but `|D₄| < ν₄` | Not interpretable — the same rule that demoted arm A's signed bias. Report and stop. |

**Power, stated in advance.** Arm A's per-pair SD implies a 95% half-width near
0.30 at n=66, and ν₄ is expected in the 0.4–0.8 range. So this design can
separate "≈ +1.0" from "≈ 0", which is the question asked. It **cannot** resolve
a true effect below ~0.4, and a null here therefore means "no effect of the
claimed size", not "no effect".

## Results

*Not yet run.*
