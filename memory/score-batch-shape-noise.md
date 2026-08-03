---
name: score-batch-shape-noise
description: A student score is not a function of the article alone — batch composition moves it up to 0.17, flipping 7-9% of near-boundary surfacing decisions (#95)
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
<!-- verify: scratchpad measure_95.py on gpu-server; flips must recur at a similar rate -->

## What follows, and what does not

- **Aggregates are safe.** Mean 0.004 washes out at n=60. #92's DiD, MAE
  figures and calibration fits are unaffected.
- **Threshold tests are not.** Under ADR-022 visibility is `raw >= op-point`,
  so a flip is a *surfacing* flip. Tier, op-point and any per-article
  before/after comparison inherit a noise floor of ~0.17 worst case.
- **The #92 second-op-point re-run is directly exposed** — it selects on
  "clears the op-point" and re-selects at another op-point, which is exactly
  the movement measured here. Pin `batch_size` for that test, or treat the
  boundary as fuzzy to ±0.08.

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

## Related

- [[project_session_2026_08_03]]
- #95 — the issue, with the fix options (pin batch_size first)
