---
name: obituary-v4-hypotheses
description: Hypotheses confirmed and learned from the obituary detector v4 corrective retrain
metadata:
  type: project
---

# Obituary Detector v4 — Hypotheses from Corrective Retrain

**Date:** 2026-07-28

## Confirmed

1. **Small-N hard negatives shift MLP boundaries effectively.** 12 hard negatives against 11,295 rows (0.1%) was enough to fix all 12 known FPs. The frozen embedder means the MLP only needs to learn a better separating hyperplane, not a new representation — so small targeted corrections work.

2. **Panel ground truth beats oracle labels for FP measurement.** The heldout showed 7 "FPs" at 0.95 against oracle labels, but the 4-model panel found only 4 actual FPs among the top scorers. Measuring FP fixes against oracle labels alone overstates the regression and understates the improvement.

3. **Precision/recall tradeoff is real but acceptable for prefilter classifiers.** v4 gained precision (0.977 vs 0.973) at the cost of recall (0.608 vs 0.744). For a prefilter where FPs block real content visible to users and FNs just waste 5ms of lens scoring, this is the correct direction.

## Learned

4. **FP class matters for correction difficulty.** Legacy/tribute pieces (Greek/Spanish/Chinese historical profiles) dropped from >0.97 to <0.15 — easy to fix. Crime/accident reports dropped from >0.92 to <0.15 — also easy, once explicitly added. But one Spanish photographer profile (Belita Gracia) only dropped from 0.87 to 0.65 — the model still sees obituary-like structure in it. Some FP classes need more examples than others.

5. **OOF metrics overstate the tradeoff.** OOF recall dropped from 0.681 to 0.703 (actually improved), while heldout recall dropped from 0.744 to 0.608. The OOF numbers are on a clean train/test split of 11K rows; the heldout is 1,562 rows with different label noise characteristics. The heldout gap suggests the hard negatives shifted the boundary into a region where oracle labels were already noisy.

6. **Belita Gracia at 0.65 is the residual uncertainty.** The model isn't confident enough to call it an obituary (below 0.95) but isn't confident it's clean either (above 0.10). This is a legitimate ambiguous case — a profile of a deceased photographer published posthumously. The labeling rule says KEEP (legacy tribute), but the text has genuine obituary-like structure. Worth watching in production shadow.

## Open questions for v5+

- Does the recall loss on the heldout appear in production, or was it concentrated in noisily-labeled regions?
- Is Belita Gracia a one-off or a whole class of Spanish-language legacy profiles that need dedicated hard negatives?
- Would the same fix work for a different architecture (e.g., fine-tuning the embedder instead of a frozen MLP)?
