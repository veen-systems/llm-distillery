---
name: feedback-probe-training-data
description: Stage-1 e5 probes trained on positives alone (or seeded from positives) miss low-scoring true positives — train on the FULL labeled set and pick the threshold recall-first
metadata:
  type: feedback
---

The Stage-1 screening probe decides which articles reach the expensive student, so a
false negative there is unrecoverable — the article is dropped and can never surface.
Two ways to build the probe, with different coverage properties:

- **Seed-from-positives / positives-only** (ADR-011 corpus screening): fast, but has a
  LOW-coverage failure — a probe that only knows what positives look like has no model of
  the negative space and mis-screens low-scoring true positives (recovery stories written
  in unusual language, non-English, or via an unfamiliar mechanism). Good for *selecting a
  corpus to oracle-score*; risky as the deployed inference screen.
- **Trained recall-first classifier on the FULL labeled set** (nature_recovery v4, 2026-07-09):
  train the probe on positives *and* negatives, fit its weighted-average as a binary
  MEDIUM+ classifier (class-weighted BCE), and choose the screen threshold off the
  **validation recall curve** at a target false-negative rate — never by minimizing error.
  Keeps 98.2% of true medium-plus while skipping ~64% of the haystack.

**Why:** on a floor-dominated corpus, an error-minimizing probe collapses to "reject
everything" (great MAE, zero recall — the H3 defect). And a positives-only probe can't
place the boundary because it never saw the near-boundary negatives. Full data + a
recall-first threshold fixes both.

**How to apply:** for a deployed needle-filter cascade, train the probe on the full
split with `scripts/train_probe.py --objective recall`, validate false-negative rate on
a held-out positive cohort, and set `hybrid_inference.stage1.threshold` from the curve.
Report recall / FN@MEDIUM+, not probe MAE. See [[gemma3-model]] only for loading; the
probe itself is e5-small + a small MLP. Related: [[feedback-oracle-not-ground-truth]]
(MAE is the wrong yardstick for needles at every stage).
