---
name: feedback-oracle-not-ground-truth
description: The oracle is a consistent labeler, not ground truth — optimize student agreement with the oracle, don't treat oracle scores as objective truth
metadata:
  type: feedback
---

Treat the oracle (Gemini/DeepSeek) as a **consistent labeling function**, not as ground truth. The goal of distillation is for the student to *replicate the oracle*, so what matters is the oracle's internal consistency, not whether its scores are "objectively correct."

**Why:** Chasing "true" scores is a category error — there is no external gold label for a 0–10 dimension like `evidence_quality`. Student MAE is measured against oracle labels, so oracle *consistency* (low inter-run disagreement, low intra-prompt drift) sets the MAE floor. A noisy-but-unbiased oracle caps how good the student can get regardless of model size or data volume. This is the flip side of ADR-010 (oracle consistency over data volume): prompt precision predicts MAE better than dataset size.

**How to apply:** When a dimension has stubbornly high MAE (e.g. cd `evidence_quality`, #23), first suspect **label noise**, not the student — check oracle consistency across re-runs before adding data or capacity. Don't "fix" scores toward your own intuition of truth; fix the *prompt* so the oracle is more self-consistent. Related: [[feedback-oracle-selection-criteria]], [[feedback-conservative-oracle-better]].

<!-- Reconstructed 2026-07-05 from the 2026-05-31 session description; listed in that recap but never committed. Grounded in ADR-010 + MEMORY.md recap. -->
