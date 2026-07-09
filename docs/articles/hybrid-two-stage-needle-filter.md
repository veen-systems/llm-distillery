# Hybrid two-stage inference for needle-in-haystack content filtering

**Claim.** For low-prevalence content categories (≪10% of corpus), a frozen e5-small embedding probe seeded from Phase-3 positives, followed by a fine-tuned Gemma-3-1B scorer on the survivors, beats running the full scorer alone at fixed compute. ADR-006 + ADR-011.

**Evidence we already have.**
- Hybrid scorer shipped (`filters/common/hybrid_scorer.py`).
- Uplifting v7 uses it in production.
- Phase-3-positive seeding replaced keyword screening (ADR-011) — we have before/after on screening quality.

**What's novel.** Two-stage cascades are standard. Specifics here:
- Two viable probe recipes, and we now have data on both. (a) *Seeded from oracle-positive examples* (ADR-011) — used to screen a corpus for training-data selection. (b) **Trained recall-first classifier** (nature_recovery v4, 2026-07-09) — a small MLP on frozen e5 embeddings trained on the *full* labeled set (positives + negatives), where the probe's weighted-average is fit as a binary MEDIUM+ classifier and the screen threshold is chosen off the **validation recall curve** at a target false-negative rate, not by minimizing error. This directly answers the "LOW-coverage / positives-only" worry below: training on full data + a recall-first threshold kept **98.2% of true medium-plus articles while skipping ~64% of the haystack**. The two recipes are complementary — seed-similarity for corpus screening, trained recall-first for the deployed inference cascade.
- A screen must be measured by what it *doesn't* wrongly discard (recall / false-negative rate), never by average accuracy — an error-minimizing probe on a floor-dominated corpus collapses to "reject everything" (the H3 defect that motivated the recall-first rewrite).
- The cascade is justified by needle filter economics — not "make it faster" but "the full scorer's FP rate is the bottleneck at our prevalence."
- Composes cleanly with the calibration/normalization recipe above.

**Risk / what's needed before writing.**
- We need the ablation: probe-only vs. full-model-only vs. hybrid, at matched compute budget, on a needle filter. Precision/recall + cost-per-1K-articles. Probably ~1 week to run cleanly.
- The "seed-from-positives" choice has known limitations — production probes trained on positives alone miss low-scoring true positives. We should be honest about when the cascade helps and when it doesn't.

**Venue.** arXiv tech report. Could be the most concrete/short of the three if the ablation is clean. ~4-6 pages.
