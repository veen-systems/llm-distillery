# PLAN — event-identity encoder for NexusMind story dedup

**Status:** PROPOSED, not started. Filed 2026-08-06.
**Owner decision required before any work begins** — this is a new training
capability in this repo, not a run of the existing pipeline.

## Problem

NexusMind's story dedup embeds article titles with stock
`intfloat/multilingual-e5-large` and merges on a global cosine threshold
(0.92 same-outlet / 0.88 cross-outlet). It is not accurate enough to carry the
decisions built on top of it.

Measured, in NexusMind (`docs/vv/corroboration-dedup-registry.md`):

| finding | value |
|---|---|
| merged-pair precision, production cap DISABLED | **0.283** |
| merged-pair precision, `pair` stratum (2-article clusters) | **0.560** |
| same-language recall | 68.5% |
| cross-language recall | 38.7% |
| F1 of production title-only@0.88 | 0.608 |
| F1 of the merge-everything **degenerate baseline** | **0.690** |

The last row is the one that should decide this: production is beaten on F1 by
merging everything. And four *same-language* combinations sit below the 0.88
bar (tr-tr 0.868, ar-ar 0.875, de-de 0.877, pl-pl 0.877), so this is a scale
problem across all 17 language pairs, not a cross-lingual one.

Downstream consequence: dedup deletes ~2,000 articles/cycle, and the surviving
representative carries `_corroboration.other_sources`, which ovr.news renders
to readers as "N sources reported this" with clickable outlet links. At 0.560
those links are wrong a large fraction of the time — a live violation of
NexusMind `docs/INTEGRITY.md`.

## Diagnosis

e5 is not malfunctioning. It is trained for **topical similarity**, and the
task needs **event identity**. Two different earthquakes are topically near-
identical; the space has no axis that separates them. "Topic attractor"
clusters — the #188/#195 pathology — are the predictable consequence of using a
topical space for an identity decision, not a threshold miscalibration.

Two sessions of threshold and linkage tuning in NexusMind shipped nothing, and
its own memory records the conclusion: *corroboration is not a threshold
problem*.

## Proposal

Contrastive fine-tune `multilingual-e5-large` for event identity.

- **Data:** SemEval-2022 Task 8 (Multilingual News Article Similarity), already
  on disk at NexusMind `data/research/semeval/final_eval_data.csv` — 4,902
  pairs, 18 language combinations, ~2,422 gold positives. External, no
  adjudication cost. For scale: NexusMind's own V1 labelling campaign yielded
  23 positives and failed on that basis.
- **Loss:** `MultipleNegativesRankingLoss` or triplet, via
  `sentence-transformers`.
- **The part with actual craft in it: hard negative mining.** Random negatives
  teach nothing — the space already separates them. The training signal lives
  in same-topic/different-event near-misses. NexusMind's `near_miss_control`
  rows are the seed population.
- **Artifact:** a full `SentenceTransformer`, 1024-dim, drop-in replacement for
  the stock model. Not a LoRA adapter, not a probe head.

## Why this is new machinery here

This repo trains LoRA adapters (`train_qwen_lora.py`, peft) and MLP probes on
**frozen** e5 embeddings. Nothing in it does contrastive bi-encoder training —
no `MultipleNegativesRankingLoss`, no triplet loss, no
`SentenceTransformerTrainer` (verified 2026-08-06).

| | today | this |
|---|---|---|
| what moves | adapter / probe head | the encoder's own weights |
| embeddings | frozen | the object being changed |
| data shape | labelled articles | labelled **pairs** + hard negatives |
| artifact | LoRA adapter / probe | full SentenceTransformer |

Not enormous — sentence-transformers makes the training loop turnkey — but it
is a new data pipeline and a new artifact type, and it should be scoped as
such.

## Scope boundary — the ship gate does NOT live in this repo

This repo can report pairwise accuracy on SemEval. **That number does not
predict what breaks in NexusMind.** Cluster size is an emergent property of
greedy linkage over a whole corpus (chaining, percolation, topic attractors);
no pair-level score sees it. OBS-20 above is the proof: a pairwise metric can
look respectable while the clustering is beaten by merging everything.

The precedent is NM#295 — a representation change that passed its author's own
validation and doubled over-merge in production (clusters ≥20 went 12-16 →
34-38, largest 76 → 239). It was reverted.

So: **train here, gate there.** Acceptance is measured in NexusMind by the
cluster-size replay plus the cap-disposition telemetry
(`scripts/research/replay_cap_disposition.py`), before anything reaches a
cycle. Per NexusMind CLAUDE.md, an instrument is not certified by its own
author.

## Integration constraints (NexusMind side, verified 2026-08-06)

1. **`e5-large` has exactly one consumer: `src/preprocessing/story_dedup.py`.**
   All 14 `filters/*/v*/inference_hybrid.py` pass `e5-small` explicitly, so
   `EmbeddingStage`'s e5-large default is never reached. A swap therefore has
   **zero filter impact** and adds **no VRAM** — it replaces a slot of the same
   size. That last point matters: gpu-server is an RTX 4080 with three tenants,
   an OOM cascade history and `MAX_LOADED_FILTERS=2` as a live stopgap
   (NM#221). Adding a *third* resident model would not be safe; replacing one
   is free.

2. **`EMBEDDING_VERSION` must be bumped in the same change.** This is the trap.
   A fine-tuned e5-large is still 1024-dim, so `checked_dim` and the
   dim-mismatch drop path **stay silent** while every saved centroid sits in a
   different vector space. Nothing raises. The version bump is the only guard,
   and it is manual — `story_dedup.py` re-embeds stored `embedding_text` for
   clusters with `embedding_version < EMBEDDING_VERSION`, which migrates the
   14-day cluster state rather than cold-starting it.

3. **Thresholds must be refit in the same commit.** MECH-1: changing the
   embedded text silently retunes every threshold read against it. NM#295
   shipped a representation change without one and that is exactly what went
   wrong.

## Risks / open questions

- SemEval is **general news**; NexusMind's corpus skews tech/sustainability.
  Domain gap is real and unquantified.
- SemEval rates similarity on a **graded scale**, not binary same-story. The
  positive/negative cut is a modelling choice that needs recording.
- Fine-tuning may degrade generic retrieval quality. Acceptable here *only*
  because e5-large has no other consumer — re-verify that before shipping.
- Pairwise quality does not fix **linkage**. Even a perfect pairwise model
  chained greedily still produces A~B, B~C, A≁C clusters. Complete-linkage
  (policy D) cut largest cluster 592→157 for 0.7pp of recall; that axis is
  independent of this one and may still be needed.

## Sequencing

This is the highest-ceiling lever available, and the SemEval labels make it
affordable for the first time. It is **not** the next thing to do. Ahead of it
in NexusMind:

1. Measure how many of the ~2,000 deletions/cycle are wrong — never measured.
2. Phase 4a: stop asserting a corroboration count precision cannot support
   (live integrity violation, depends on no research result).

A better encoder changes the deletion number without ever telling you what it
was.
