---
name: corroboration-feature-hypotheses
description: What is confirmed, refuted and untested about features for corroboration/story matching — cosine, time delta, NER entity overlap. Read before proposing any NER or matching-feature work.
metadata:
  type: project
---


⏸ **DORMANT since 2026-08-27 (owner, 2026-10-09: keep, do not archive).** NexusMind owns the programme: parent
issues **NexusMind#188** (story-dedup feature augmentation) and **NexusMind#301** (merged-pair precision); NexusMind#213
is CLOSED. **THINNED 2026-10-12** (owner ruling 2026-10-10): this file is now the current summary only. Every dated
section, the measurements, tables, retractions and literature, is VERBATIM in
[`archive/corroboration-feature-hypotheses-archive.md`](archive/corroboration-feature-hypotheses-archive.md) —
**grep it before quoting any number not on this page, and before concluding something was never measured.**
⚠️ The NexusMind issue states and config values below are as last recorded (2026-08-27), not re-checked 2026-10-12.

## What to believe now — the three newest findings

1. **The lever is a GATE, not a similarity feature or the threshold (2026-08-09).** Primary scientific documents
   (a paper is not an event, so two outlets never independently corroborate it) were merged at 0–14% correctness at
   every threshold. ⛔ The panel figures (20.6–30.4% of merges, weighted precision 0.344 → 0.459) are **unusable as the
   gate's value**: the panel is stratified toward giant clusters and its academic cut is a 6-slug substring label, while
   production reads `metadata.primary_literature` (FluxusSource `33c7f41`); NexusMind measured PL at **8.05%** of
   everything merged (2026-08-16). **The academic gate is LIVE since 2026-08-17 09:50 CEST** (NexusMind#392 — not
   NexusMind#391): both-sides semantics, stamp read never re-derived, ADR-022 stamp-always. `pl_pl` **0 correct of 28**
   (rule-of-three upper bound ≈10.7%; never quote 0.0% bare), cost 322:1, measured on ONE batch chosen as the DENSEST
   (29.4% PL vs ~10% typical). Its review-by date (2026-08-23) was never confirmed done here.
2. **Production is 79.3% sub-threshold artefact (2026-08-16/17).** On a 3,835-article batch, 97,492 of 122,901 merge
   pairs (79.3%) sat below the 0.88 cosine bar: an article matches a cluster CENTROID and inherits co-membership with
   members it is nowhere near (attractors: one article in 6 of 30 sampled pairs). The gate cut this to 35.1% as a side
   effect; it is not the fix. On a separate batch with NO cross-run seeds (39.7% below bar — a different population,
   not a correction): **63.8% chained** (94.75% exactly 2 hops: one bridge article) and **36.2% drift** (unreachable by
   any path at the bar). The below-bar pairs are disproportionately cross-language (72.1% / 67.3% vs 38.9% above bar),
   so complete-linkage would delete cross-language corroboration; correlation clustering (PIVOT) is the preferred
   formulation. ⛔ **No instrument works at the level of the defect**: every one we own is pairwise, and a story split
   across eight confident clusters is invisible to all of them. A partition-level instrument (B³ / CEAF-e, INST-6, never
   built) is a PREREQUISITE for knowing whether any consolidation fix worked.
3. **Combining features beats the production threshold (2026-08-17).** Seven cheap pairwise features in an L2
   logistic regression, grouped 5-fold CV: AUC **0.7701 (cosine only) → 0.8827**, pooled n=1,196 over three panels,
   each panel replicating; 50-permutation null max 0.5271. Token overlap flips sign in the joint fit (templated-title
   collisions), which no per-feature AUC table can show. ⚠️ Binding caveats: the negative class is FALSE MERGES (it
   filters bad merges, it is not shown to find new ones); panels are giant-stratified (AUC is the portable half);
   labels are LLM-judge verdicts; **built and reported by one session — needs a non-author check before it drives
   anything.**

And one later trap (2026-08-26): **half of `other_sources` is bookkeeping.** Cross-run entries (`cross_run: true`)
carry a HARDCODED `source_tier: "unknown"` / `credibility_score: null`: 51.4% of entries over 14 days, 97.7% of all
`unknown`. ⛔ Never average, threshold or rank on credibility read from `other_sources` without grouping on `cross_run`.

## Standing cautions — each was a wrong number once

- **Operating points.** SemEval-2022 Task 8 (external gold) prefers title+body at 0.92 over title-only at 0.88; that
  ordering is robust, the op-point does NOT transfer. On production panel v3, `title_body@0.94/0.90` ties live by
  overlapping CIs; `0.96/0.92` is more precise only by going quiet. Production embeds `title_raw`.
- **Temporal feature.** NexusMind ships `sigma_hours: 72.0`, the refuted width (sweep prefers σ≈18); the AUC is
  σ-invariant BY CONSTRUCTION, so it cannot arbitrate σ. Any before/after delta runs at σ ∈ [12, 24].
- **NER.** V1's failure (precision/recall 0.000) was n=23 (21 from one case) plus spaCy's ~2 entities/article.
  XLM-R gives a median of 12 and 0 of 4,000 unrelated pairs ≥ 0.3 — the NEGATIVE side only; positives never measured.
  No NER script persists (it ran from `/tmp`). Literature: entity grounding buys little (+0.00075 Pearson).
- **Ratio-margin scoring** (hubness fix) is the top untested per-pair lever. Quote BUCC EN-DE as **77.0 → 94.8
  forward-to-forward** (82.8 is the intersection baseline); always name the retrieval variant.
- **Corpus.** Pre-depleted at collection (FluxusSource#133): cross-run loss is publisher-correlated and sticky for up
  to 30 days. `SavedCluster` persists no member ids, so no multilingual number comes from production. MinHash was
  deleted, measurement-backed (FluxusSource#134).
- **Data.** Judge verdicts are in the WORKSTATION NexusMind checkout, `data/research/precision_panel{,_v2,_v3}/judge_verdicts.jsonl`
  (gitignored; not on b650 or sadalsuud). Panel `item_id`s collide across panels; `sim` in v3's `answer_key.json`
  exists only on the discarded near-miss rows.
- **Mojibake** in titles: ~0.11–0.13%, both FLOORS. Generate signatures from codecs, never hand-write a class, and
  verify by inversion (`NexusMind/scripts/research/nm188_mojibake_invert.py`); the generator itself was never committed.

## Untested, in priority order (2026-08-17)

1. Cross-run seeded clustering — the population the 79.3% came from.
2. Ratio-margin `sim` over a production neighbour pool, in the same 1,196-pair harness.
3. XLM-R entity Jaccard on the 1,316 adjudicated pairs, scored against the judge verdicts.
4. Numeral normalisation before re-measuring numeric overlap.

## Where each dated section went (all in the archive, headings unchanged)

The 2026-08-07 summary (feature set, CONFIRMED / REFUTED / UNTESTED, the pre-depleted corpus, sequencing) ·
STEP 2 turn-over 2026-08-09 + the SemEval section 2026-08-08 · 2026-08-26 `other_sources` · data inventory
2026-08-08 · **2026-08-17** (chaining vs drift, the under-merge framing correction, ovr's moving figure, combined
features, the records FMEA, the traps, six-lens literature, untested list) · 2026-08-16/17 the 79.3% headline and the
three method findings · 2026-08-16 the academic stamp · 2026-08-09 the gate · 2026-08-09 the feature probe and the
77.0 retraction · the academic-gate deploy record.

Related: [[cd-v6-probe-hypotheses]], [[score-batch-shape-noise]], [[hypothesis-ledger]].
