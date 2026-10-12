---
name: solutions-v6-dimension-hypotheses
description: solutions v6 — which hypotheses about community_practice_strength being a "dead dimension" survived measurement. Read before proposing a weight change, a recalibration, or a length gate on this filter.
type: project
---

# solutions v6 dimensions — hypotheses (2026-08-11 evening)

Prompted by the owner's framing: *"`community_practice_strength` is dead — zero
on 83% of on-topic articles while carrying 10% of the score. Find 20 articles
that should score high on it. Easy to find = data gap worth fixing. Hard to find
= the dimension isn't real."*

**Neither branch held.** The dimension is real, the misses are hard to find, and
the only defect that survived measurement is small and belongs to calibration.

Full record: `docs/evidence/2026-08-11-solutions-v6-community-practice-dimension.md`
(commit `3ea78a5`). Reproduce with `scripts/research/solutions_v6_*.py`.
Companions: `score-batch-shape-noise.md` (#95, the floor every effect here is
sized against), `google-news-corpus-hypotheses.md` (the 25.7% stub population),
`prefilter-length-floor-hypotheses.md` (why the answer is never a length gate).

## CONFIRMED H1–H4 · REFUTED R1–R4 — MOVED to [`archive/solutions-v6-dimension-hypotheses-archive.md`](archive/solutions-v6-dimension-hypotheses-archive.md) (2026-10-12)

- `community_practice_strength` is REAL, just rare (oracle n=397, mean 5.09); the student learns it better than the other
  six. ⛔ **The 83% zero rate is BASE RATE, not breakage** — R1 "the dimension is dead" is refuted three ways.
- Re-weighting does not recover the ceiling (R2) and cannot fix NM#319 (R3): NexusMind's gate reads `weighted_average`,
  which `production_scorer.py` overwrites with the NORMALIZED score, so a monotone reweight vanishes at the next refit.
- The concreteness gatekeeper is inert on the training corpus too (#94); R4's 40.0/43.1 decomposition is circular.

## THE ONE REAL DEFECT — small, and it is calibration

On oracle-positive rows the student averages **2.69 against the oracle's 4.63**;
the dimension does ~58% of its designed work. It emits only **16 distinct values**
(fewest of the seven), with **13 of 41 positives pinned to exactly 1.90**, because
the isotonic fit had 21 breakpoints to work with.

Sized: **0.194 on the weighted score at weight 0.10, on 4.0% of rows** — barely
above the #95 noise floor of 0.16. **Fold into the next calibration refit; not
worth its own change.**

## UNTESTED

- **Whether NM#319's enrichment starvation has any cause visible from here.**
  Side result: normalized 4.0 corresponds to **raw 3.261**, and **75.6%** of
  surfacing training rows clear it (out-of-sample: the CDF is fitted on production rows) — so the weighting scale is not the cause.
  That is a prediction about production data and was **not** tested against it.
- **Whether the 2 genuine misses generalise.** Both are hybrid articles tagged
  single-type, where Step 2's hard `content_type` gate deletes the dimension
  rather than shading it. n=2. Not a rate.
- **Whether more community-practice training data is obtainable.** §6 of the
  evidence doc argues this is a *sourcing* question, not a modelling one, since
  the positives are not hiding in the corpus. No outlet survey has been done.

## TRAPS

- **MAE is the wrong instrument here, twice.** `community_practice_strength` has
  the **lowest MAE of the seven (0.179)** and that fact carries no quality
  information — it is zero on 96% of the split. ADR-023 in miniature. The report
  script prints MAE last and labels it as scale.
- **Never answer this with a prefilter length check.** #93 deliberately removed
  exactly that; adding `check_content_length` re-creates what #93 removed.
- **Stack/device, NOT "cross-box" (corrected 2026-08-29):** the |0.2008| measured on
  uplifting v7 is the **library stack**, not the machine — the host term is 0.0000,
  660/660 bit-identical. The other live term is the **device**, CPU→CUDA |0.1956|,
  and production serves on GPU. Fine for "does this dimension carry signal"; **no
  number here is production's** without re-running `scripts/verification/box_parity.py`
  and comparing with **`diff_box_parity.py --threshold`** (the threshold is on the diff,
  not the dump) at production's device.
- **`content_type` is not in the splits.** Shape is a proxy throughout and cannot
  distinguish a mandated zero from an honest one.
