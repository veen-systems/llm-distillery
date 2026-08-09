---
name: score-batch-shape-noise
description: A student score is not a function of the article alone — batch composition moves it up to 0.16, flipping 7-9% of near-boundary surfacing decisions (#95); cycles are replayable since 2026-08-03 but scores are not stable
metadata:
  type: project
---

# Batch-Shape Score Noise (#95)

**Date:** 2026-08-03. Found while smoke-testing #93 on gpu-server; **not caused
by #93** — measured with every #93 code path inert.

## The finding

Same article, same model, same weights, same box, same process. Only
`batch_size` differs. Scores move.

| filter | op-point | corpus | in ±0.30 band | flipped tier/op-point | share of band | share of corpus |
|---|---|---|---|---|---|---|
| solutions v6 | 2.252 | 2,814 | 28 | 2 | **7.1%** | 0.07% |
| uplifting v7 | 4.0 | 950 | 33 | 3 | **9.1%** | 0.32% |

```
solutions [3]  bs1=2.1745(low)  bs4=2.3398(medium)  bs8=2.3080(medium)  bs16=2.1745(low)
uplifting [9]  bs1=4.0390(medium)  bs4=3.9193(low)  bs8=3.9012(low)  bs16=4.0390(medium)
```

Magnitude over 120 articles: **max |Δ| 0.162, mean |Δ| 0.004**, ~40% of articles
affected at all. Consistent with GPU kernel reduction order varying with the
batch dimension. `score_article` vs `score_batch` disagree the same way and by
the same amounts — the API difference is incidental, the batch *shape* is the
cause.
<!-- verify: test -f scripts/diagnostics/measure_batch_shape_flips.py && echo PASS || echo FAIL -->

## What follows, and what does not

- **Aggregates are safe.** Mean 0.004 washes out at n=60. #92's DiD, MAE
  figures and calibration fits are unaffected.
- **Threshold tests are not.** Under ADR-022 visibility is `raw >= op-point`,
  so a flip is a *surfacing* flip. Tier, op-point and any per-article
  before/after comparison inherit a noise floor of **0.16** worst case (the
  measured max is 0.162 — do not round it up to 0.17, as an earlier draft of
  this file and its description did).

## What shipped 2026-08-03 evening

- **Seeded per-run shuffle** (NexusMind `f7fef85`, deployed). The variable was
  never batch *size* — `DEFAULT_BATCH_SIZE = 16` is fixed and never varies in
  production. It was batch *composition*, from an unseeded
  `random.shuffle(articles)` in `scripts/main.py`. Now seeded per (run, filter),
  logged in the start banner, replayable via `NEXUSMIND_RUN_SEED`.
  **This is replay, not stability** — the next cycle reshuffles and the article
  moves again. Do not cite it as a fix for #95.
- **Noise floor recorded** (LD `efab69d`) in `docs/FILTER_PLAYBOOK.md` §7, the
  `ground_truth_gate.py` docstring, and CLAUDE.md's hard constraints.

## The owner decision, 2026-08-06 (#95 step 2)

**Budget for the floor; do not try to remove it.** Options put to the owner were
(a) declare a noise margin, (b) test the fixed-length-padding hypothesis first,
(c) both. Chosen: **(a), no experiment.** The padding test stays unrun.

Note the option that was *not* available: "pin a batch size in production."
`DEFAULT_BATCH_SIZE = 16` (`filters/common/filter_base_scorer.py:50`) is already
fixed and never varies in production — the variable is batch *composition*, which
is what the seeding addressed. #95's own "suggested next steps" text offered
pinning as a live option; it was not one.

**The rule, as shipped:** an article predicted within **0.16** of the surfacing
threshold is *indeterminate* — the batch decided it, not the model. Every metric
computed at that threshold carries a band, and **two models whose bands overlap
are NOT DISTINGUISHABLE**. Binds the ground-truth gate, FN-deltas, op-point
re-derivations (#87) and short-content cap measurements (#93 step 4).

`scripts/gate/ground_truth_gate.py` computes it (`--noise-floor`, default 0.16;
`0` reproduces pre-2026-08-06 runs). Worked example — `solutions v6` on its own
held-out test set, 19 of 1,032 indeterminate:

```
F1     0.739 [0.712, 0.771]
recall 0.671 [0.659, 0.707]
prec   0.824 [0.775, 0.849]
```

A candidate landing anywhere inside that band has not beaten v6.
<!-- verify: grep -q "NOT DISTINGUISHABLE" scripts/gate/ground_truth_gate.py && echo PASS || echo FAIL -->

**Still open:** whether scores can be made a function of the article alone.
Untested hypothesis — if batches pad to the longest article *in the batch*, an
article's computation depends on its batch-mates, and fixed-length padding
would remove the dependence. Falsifiable in a few hours on GPU; deferred until
something needs batch-invariant scores.
- **The #92 second-op-point re-run is directly exposed** — it selects on
  "clears the op-point" and re-selects at another op-point, which is exactly
  the movement measured here. Pin `batch_size` for that test, or treat the
  boundary as fuzzy to ±0.08.

## Does it change a decision? Yes — measured 2026-08-03

The first pass (120 articles) found 0 tier flips **and 0 articles within 0.05 of
the op-point**, so it could not have found one. Re-run against the band where a
flip is possible (`scripts/diagnostics/measure_batch_shape_flips.py`):

| filter | op-point | in ±0.30 band | flipped | share of band | share of corpus |
|---|---|---|---|---|---|
| solutions v6 | 2.252 | 28 | 2 | **7.1%** | 0.07% |
| uplifting v7 | 4.0 | 33 | 3 | **9.1%** | 0.32% |

```
solutions [3]  bs1=2.1745(low)  bs4=2.3398(medium)  bs8=2.3080(medium)  bs16=2.1745(low)
uplifting [9]  bs1=4.0390(medium)  bs4=3.9193(low)   bs8=3.9012(low)     bs16=4.0390(medium)
```

Flips occur within 0.077 (solutions) / 0.039 (uplifting) of the op-point.

## Not measured

Whether the *same* batch_size with different batch *membership* (which is what
production actually varies, cycle to cycle) produces the same effect. Almost
certainly yes — membership changes the shape the same way — but it is inferred,
not measured. The production-relevant number is therefore an estimate.

## Distinguish from its two cousins

- **Training-time CUDA nondeterminism** (gotcha 2026-07-09): same seed, fresh
  re-train, different *weights*. This one is fixed weights at inference.
- **Cross-box score skew** (gotcha 2026-07-30): |0.16| between gpu-server and
  b650 from a sentence-transformers version difference. Same magnitude,
  different cause — and note this one is *within* a single box.
  **NOW MEASURED FOR THE GEMMA STUDENT TOO (2026-08-09 night)**, and it is the
  same order as this floor rather than smaller: uplifting v7's 660 held-out rows,
  b650 vs gpu-server's serving venv, model weights + all filter/`common/` code +
  split md5-identical, CPU both sides — **max calibrated |Δ| 0.2008, i.e. ABOVE
  the 0.16 floor**, p99 0.1198, p90 0.0345, p50 0.0000, only 2.3% of rows
  bit-identical, signed mean +0.00018 (noise, not a shift). **Decision impact is
  threshold-dependent: 0 verdict flips at the 4.0 op-point (identical confusion
  matrix, so the gate report is production's number) and 3 flips at 4.5,
  splitting specificity 0.9730 vs 0.9662.** So the two noise sources *stack*, and
  **a box is cleared at a threshold, never in general**. The e5 probe's clean
  4.2e-6 result does NOT transfer to the student. Beware the p50 of exactly
  0.0000 — raw logits are bf16-quantised (~0.03 steps), so most disagreements are
  hidden, not absent. Harness: `scripts/verification/box_parity.py` +
  `diff_box_parity.py`; record:
  `docs/evidence/2026-08-09-cross-box-parity-uplifting-v7.md`.
  Still unmeasured for the student: **CPU vs CUDA**.

## Related

- [[project_session_2026_08_03]]
- #95 — the issue, with the fix options (pin batch_size first)
