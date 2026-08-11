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

## CONFIRMED

**H1 — the dimension is real, it is just rare.** When the oracle scores it, it
spreads properly: n=397 across all splits, mean 5.09, median 5.0, range 1.0–8.5,
with coherent exemplars (Amul Dairy Cooperative 8.5, community forestry in Nepal
8.0, a Rajasthan "River Parliament" allocating water across 70 villages 8.0).
Verify: `PYTHONPATH=. python3 scripts/research/solutions_v6_reweight_ablation.py`.

**H2 — the student learns it BETTER than it learns the other six.** 1,032 test
rows, b650, GPU. Conditional correlation on oracle-positive rows **r=0.622, the
highest of all seven** (others 0.373–0.573); false-fire rate on true-zero rows
**4.0%, the lowest**. It is the most precise dimension the filter has, which
under ADR-023 is the property worth having. Verify:
`PYTHONPATH=. python3 scripts/research/solutions_v6_dim_fidelity_report.py`.

**H3 — the score ceiling really does differ by solution type.** Weights sum to
1.00 and Step 2 of the oracle prompt mandates zeros, so maximum achievable
weighted score is **7.50 for pure tech, 9.00 for governance, 10.00 for
community/hybrid**. This is arithmetic. It is also inert — see R2.

**H4 — the concreteness gatekeeper is inert on the training corpus too (#94).**
8,451 of 10,297 rows have concreteness < 3.0; **0** of them exceed the 3.0 cap,
max weighted average 2.600, margin 0.400. Second population agreeing with the
issue's 191,616 production articles. **The inertness is EMPIRICAL, not
structural** — a row at concreteness 2.99 could reach 8.60; it does not because
low concreteness correlates with low everything. #84's router rework could
decouple that.

## REFUTED

**R1 — "the dimension is dead."** Refuted three ways: labels (H1), student (H2),
and the miss hunt. Screening all 1,953 on-topic zeros twice — keyword pass (201
hits), actor-centred pass requiring the community to be the *doer* (112 hits, 42
at/above weighted 4.0) — and hand-reading the strongest yielded **2 genuine
misses, not 20**. The 83% is base rate.

**R2 — "re-weighting would recover the ceiling."** At matched surfacing volume,
renormalising over permitted dimensions swaps **11 of 1,628 articles (0.7%)**;
dropping comm+gov entirely swaps 17 (1.0%). It is a near-monotone rescale: it
moves the scale, it does not reorder. No weighting change is worth making.

**R3 — "re-weighting would fix NexusMind's enrichment starvation (NM#319)."**
⚠️ **The most dangerous refuted item here, because the measurement was clean.**
Re-weighting moves ≥4.0 from 31.1% to 50.6% (tech alone 15.6% → 56.8%), which
looks decisive. It is an artifact. NexusMind's gate reads
`result["weighted_average"]` (`article_fetcher.py:1355`), and
`production_scorer.py:16-17` overwrites that field with the **NORMALIZED** score.
Normalization is a percentile CDF, so a monotone rescale maps back to the same
percentiles and the effect vanishes at the next refit. **This was one code read
away from being recommended.** The ablation script now prints the interception in
section 3 so it cannot be re-derived as a win.

**R4 — a decomposition of the 83.1% into "40.0% tech-shaped + 43.1%
governance-shaped".** Circular: both categories are defined *using* `comm == 0`,
so they sum to the zero rate by construction. `content_type` is **not stored in
the training splits**, so the prompt's forcing rule cannot be verified from this
data at all. Retracted the same session it was written.

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
  surfacing training rows clear it — so the weighting scale is not the cause.
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
- **Cross-box:** the Gemma-3-1B student is not probe-clean across boxes (b650 vs
  gpu-server ran to |0.2008| on uplifting v7, above the #95 floor). Fine for "does
  this dimension carry signal"; **no number here is production's** without
  re-running `scripts/verification/box_parity.py` at the relevant threshold.
- **`content_type` is not in the splits.** Shape is a proxy throughout and cannot
  distinguish a mandated zero from an honest one.
