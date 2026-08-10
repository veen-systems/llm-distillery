# #102 step 2 — `uplifting v7` operating point, through the ADR-021 gate

**Measured 2026-08-10. Machine-readable: `filters/uplifting/v7/threshold_sweep.json`.**

## One-line answer

**Moving `uplifting v7` from 4.0 to 4.5 is a real specificity gain, not noise** —
FPR 8.11% → 2.70%, and the two specificity bands are **disjoint**. It costs a
real amount of recall (0.736 → 0.611, also disjoint). Under ADR-023 that trade is
the right direction. **Nothing was changed; this is the evidence, not the flip.**

## What was run, and why it is cheap now

`scripts/gate/ground_truth_gate.py` against the 660-row held-out oracle test
split, on **production's own predictions** — the committed
`datasets/parity/uplifting_v7_test660_gpuserver-serving-venv_2026-08-09.jsonl`,
calibrated with the deployed `calibration.json`. No re-scoring: the serving box
is only free between pipeline cycles and a 660-row run costs ~30 min of CPU there.
The conversion is `scripts/verification/parity_dump_to_gate_input.py` (new).

**Control, passed:** at threshold 4.0 this pipeline reproduces the committed
`ground_truth_gate.json` **exactly** — tp=159 fn=57 fp=36 tn=408, indeterminate
37/660. The sweep's 4.0 row is a known-answer test, which is the only reason the
other rows are worth reading.

## Three gaps in the gate, closed to make this measurable

The gate could not answer #102's question as it stood.

1. **Specificity had no band.** Every other metric carried a #95 uncertainty
   range; the one ADR-023 makes the objective was a bare point estimate. Added,
   and the overlap check now runs on **specificity first**, separately from F1 —
   two models can be indistinguishable on one and distinguishable on the other,
   and reporting only F1 hides both cases.
2. **The truth cut moved with the threshold.** Sweeping `--threshold` also moved
   what "on-lens" *means*, so the positive set changed underneath the sweep (216
   → 193 positives between 4.0 and 4.5) and recall at one threshold was not
   comparable to recall at another. New `--truth-threshold` pins the oracle cut.
   Default is unchanged, so every prior run and all 270 unit tests reproduce.
3. **The overlap check only ever said "OVERLAP".** It now also prints DISJOINT
   with the two bands, so "we checked and the difference is real" is a visible
   result rather than the absence of a warning.

## The sweep

On-lens pinned at oracle ≥ 4.0 (216 positives of 660, 32.7%) at every row; only
the student's bar moves.

| student thr | tp | fn | fp | tn | recall | **specificity** | FPR | spec band (#95) | recall band | indet. |
|---|---|---|---|---|---|---|---|---|---|---|
| **4.00** (deployed) | 159 | 57 | 36 | 408 | 0.7361 | **0.9189** | **8.11%** | [0.901, 0.941] | [0.685, 0.773] | 37 |
| 4.25 | 144 | 72 | 24 | 420 | 0.6667 | 0.9459 | 5.41% | [0.932, 0.962] | [0.630, 0.713] | 31 |
| **4.50** | 132 | 84 | 12 | 432 | 0.6111 | **0.9730** | **2.70%** | [0.957, 0.982] | [0.583, 0.644] | 24 |
| 4.75 | 121 | 95 | 7 | 437 | 0.5602 | 0.9842 | 1.58% | [0.977, 0.989] | [0.519, 0.593] | 21 |
| 5.00 | 103 | 113 | 5 | 439 | 0.4769 | 0.9887 | 1.13% | [0.986, 0.993] | [0.417, 0.542] | 30 |

The point estimates match yesterday's hand-rolled sweep exactly. What is new is
that they now come out of the ADR-021 gate with bands attached, which is what
step 2 asked for.

## 4.0 vs 4.5 under the #95 band rule

| metric | band at 4.0 | band at 4.5 | verdict |
|---|---|---|---|
| **specificity** | [0.9009, 0.9414] | [0.9572, 0.9820] | **DISJOINT — real** |
| **recall** | [0.6852, 0.7731] | [0.5833, 0.6435] | **DISJOINT — real** |
| F1 | [0.7255, 0.8166] | [0.6981, 0.7658] | OVERLAP — not distinguishable |

**The F1 overlap is the expected result, not a contradiction.** F1 is symmetric
and this is an asymmetric problem: it nets a real specificity gain against a real
recall loss and reports nothing. That is precisely what ADR-023 says not to
optimise. Read specificity and recall; do not read F1 here.

**The trade: 24 fewer false positives for 27 more false negatives.** Under
ADR-023 — *"letting junk through is way worse than not catching positives"* —
those are not equal-weight units, and 4.5 puts uplifting's FPR (2.70%) between
`solutions v6` (2.8%) and `nature_recovery v4` (2.1%) instead of 3–4× above both.

**Both numbers transfer to production, and this is the reason to trust them at
all**: recall and specificity are conditional on the true class, so the split's
32.7% enrichment does not distort them. Precision, MAE and F1 on this split do
not transfer, which is why they are excluded from the argument.

## Correction: "b650 is not cleared at 4.5" does not survive the band

Yesterday's `2026-08-09-cross-box-parity-uplifting-v7.md` concluded that b650 was
cleared at the 4.0 op-point and **not** at 4.5, on 3 verdict flips and
specificity 0.9730 (production) vs 0.9662 (b650). Running both boxes through the
gate:

| student thr | prod spec | b650 spec | gap | prod band width | bands |
|---|---|---|---|---|---|
| 4.00 | 0.9189 | 0.9189 | 0.0000 | 0.0405 | OVERLAP |
| 4.25 | 0.9459 | 0.9459 | 0.0000 | 0.0293 | OVERLAP |
| **4.50** | 0.9730 | 0.9662 | **0.0068** | **0.0248** | **OVERLAP** |
| 4.75 | 0.9842 | 0.9865 | 0.0023 | 0.0113 | OVERLAP |
| 5.00 | 0.9887 | 0.9910 | 0.0023 | 0.0068 | OVERLAP |

At 4.5 the between-box gap is **3.7× narrower than the within-box batch-noise
band**. Under the owner's 2026-08-06 rule — *two models whose bands overlap are
NOT DISTINGUISHABLE, whatever their point estimates say* — the specificity
difference is below this instrument's resolution. And at 4.75 and 5.0 the **sign
reverses** (b650 scores higher), which is what noise looks like and what a
systematic box bias does not.

**What stands and what does not.** The 3 row-level verdict flips at 4.5 are real
facts about 3 rows, as is max calibrated |Δ| 0.2008 and the 2.3% bit-identical
rate. What does not stand is the inference from those to *"b650 measures a
different specificity at 4.5"*. The general principle survives intact and was
the more important half anyway: **a box is cleared at a threshold, never in
general** — and absence of a measurable difference is not proof of none, so
threshold work should still be done on the serving box when it is free.

*(I made the original claim yesterday. The band was available then and I did not
apply it — the gate had no specificity band, which is the gap closed above.)*

## The constraint that decides the option set

**`MAX_NORMALIZATION_RAW_MIN = 4.5` bounds the op-point from above.**

`tests/unit/test_normalization_invariant.py` requires `normalization.json`'s
`stats.raw_min` to equal the filter's tier threshold, and
`NexusMind/src/scoring/production_scorer.py:513` **rejects** a fit with
`raw_min > 4.5`, falling through to `score_scale_factor` with a log warning and
no other symptom. The boundary is strict-greater-than and documented as such
("a fit with raw_min exactly equal to 4.5 is accepted", NM#205).

`uplifting v7`'s committed fit is `raw_min: 4.0`, n=18,130, fitted 2026-07-31.

Therefore:

- **4.5 is reachable, and sits exactly ON the bound with zero margin.**
- **4.75 and 5.0 are NOT reachable** without raising the constant in *both*
  repos — attempting either silently disables normalization.
- **Any op-point move must refit `normalization.json` at the new anchor in the
  same change**, or the invariant test fails and production quietly loses
  percentile normalization.

That was not visible before this run and it removes two of the five sweep rows
from consideration.

## Not done / what step 3 needs

- **Nothing was deployed or changed.** No config edit, no refit.
- **Production-population confirmation is missing.** These are held-out
  *training-split* rates. The corresponding production number — how many articles
  per cycle stop surfacing at 4.5 — has not been measured, and 4.5 would remove
  roughly two-thirds of uplifting's current surfacing volume if the split's
  ratios hold, which is a product decision, not a metrics one.
- **The recall loss is concentrated somewhere.** 27 articles move from TP to FN;
  which *kind* they are has not been looked at. If they are the genuine
  community-scale stories the lens exists for, that changes the answer.
- The 2026-08-09 adverse batch measured ~25% off-lens articles reaching readers
  at 4.0. Re-running that estimate at 4.5 would give the reader-facing number
  this whole line of work is actually about.

## Reproduce

```bash
PYTHONPATH=. python scripts/verification/parity_dump_to_gate_input.py \
    --dump datasets/parity/uplifting_v7_test660_gpuserver-serving-venv_2026-08-09.jsonl \
    --calibration filters/uplifting/v7/calibration.json --out /tmp/upl_prod.jsonl

# control first -- must print tp=159 fn=57 fp=36 tn=408
PYTHONPATH=. python scripts/gate/ground_truth_gate.py \
    --labels datasets/training/uplifting_v7/test.jsonl \
    --config filters/uplifting/v7/config.yaml --recompute-model-wa \
    --model v7=/tmp/upl_prod.jsonl --report /tmp/control.json

# then the sweep, with on-lens PINNED
for T in 4.0 4.25 4.5 4.75 5.0; do
  PYTHONPATH=. python scripts/gate/ground_truth_gate.py \
      --labels datasets/training/uplifting_v7/test.jsonl \
      --config filters/uplifting/v7/config.yaml --recompute-model-wa \
      --threshold $T --truth-threshold 4.0 \
      --model prod=/tmp/upl_prod.jsonl --report /tmp/sweep_$T.json
done
```

`datasets/training/uplifting_v7/test.jsonl` is gitignored and lives on b650 and
gpu-server (md5 `904ad059fe27157a297ac74c960adad3`); copy it from
`b650-gpu:~/llm-distillery/datasets/training/uplifting_v7/`.
