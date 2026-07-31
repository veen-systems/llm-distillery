---
name: obituary-v4-hypotheses
description: Hypotheses confirmed and learned from the obituary detector v4 corrective retrain
metadata:
  type: project
---

# Obituary Detector v4 — Hypotheses from Corrective Retrain

**Date:** 2026-07-28 (v5 production-FN addendum 2026-07-31)

## Confirmed

1. **Small-N hard negatives shift MLP boundaries effectively.** 12 hard negatives against 11,295 rows (0.1%) was enough to fix all 12 known FPs. The frozen embedder means the MLP only needs to learn a better separating hyperplane, not a new representation — so small targeted corrections work.

2. **Panel ground truth beats oracle labels for FP measurement.** The heldout showed 7 "FPs" at 0.95 against oracle labels, but the 4-model panel found only 4 actual FPs among the top scorers. Measuring FP fixes against oracle labels alone overstates the regression and understates the improvement.

3. ~~**Precision/recall tradeoff is real but acceptable for prefilter classifiers.**~~ **FALSIFIED 2026-07-30.** The original claim ("FNs just waste 5ms of lens scoring") confused a *blocking* prefilter with a *routing* one: once enforcement flips, an FN is an obituary on the site — the exact failure the owner keeps flagging (Farouq Hilal tribute, 2026-07-29: v3 0.977, v4 0.937 → v4@0.95 would miss it). Resolution: op-point moved to 0.90, where v4's heldout FP set is identical to 0.95 (zero precision cost) and recall recovers to 0.683. For blocking classifiers, sweep the op-point on both error directions against the product metric; never accept a recall drop on "FNs are cheap" grounds. See LD#83.

## Learned

4. **FP class matters for correction difficulty.** Legacy/tribute pieces (Greek/Spanish/Chinese historical profiles) dropped from >0.97 to <0.15 — easy to fix. Crime/accident reports dropped from >0.92 to <0.15 — also easy, once explicitly added. But one Spanish photographer profile (Belita Gracia) only dropped from 0.87 to 0.65 — the model still sees obituary-like structure in it. Some FP classes need more examples than others.

5. **OOF metrics overstate the tradeoff.** OOF recall dropped from 0.681 to 0.703 (actually improved), while heldout recall dropped from 0.744 to 0.608. The OOF numbers are on a clean train/test split of 11K rows; the heldout is 1,562 rows with different label noise characteristics. The heldout gap suggests the hard negatives shifted the boundary into a region where oracle labels were already noisy.

6. **Belita Gracia at 0.65 is the residual uncertainty.** The model isn't confident enough to call it an obituary (below 0.95) but isn't confident it's clean either (above 0.10). This is a legitimate ambiguous case — a profile of a deceased photographer published posthumously. The labeling rule says KEEP (legacy tribute), but the text has genuine obituary-like structure. Worth watching in production shadow.

## v5 production-FN addendum (2026-07-31, owner obit sighting on ovr.news)

7. **Open question 1 ANSWERED: yes, the recall loss appears in production, and it is structured, not noise.** Two live obituaries on ovr.news are true v5 FNs (rescored on gpu-server with the exact production text format `title + " " + content`; the rescore reproduces the production v4 stamp to 4 decimals — 0.4376 vs stamped 0.4375612):
   - **Community-mourning class — MONOTONE REGRESSION across versions.** "Namur mourns Yves Devos, captain of stilt walkers": v3 **0.682** → v4 **0.438** → v5 **0.122**. Each round of hard negatives (v4's legacy tributes, then v5's mix) pulled the community/festival-mourning style further from the obituary region. The correction mechanism from hypothesis 1 cuts both ways: small-N hard negatives shift the boundary effectively — including *over* genuine positives that share surface structure with the negatives. Under the owner's grief-vs-news rule this class is unambiguously BLOCK.
   - **Biography-rich obit class — STABLE BLIND SPOT, not a regression.** "Muere Teresa Alonso, la 'niña de Rusia'… dies at 101": v3 0.284 / v4 0.195 / v5 **0.277** — every version misses it. The article is dominated by decades of biography (Civil War evacuation, Leningrad siege), so it embeds as a history piece; the death-announcement frame is a small fraction of the text. Threshold changes cannot reach it (all versions <0.30); this class needs training examples (or title-weighted features — the title alone says "Muere…").
   Evidence for LD#85 when reactivated; both articles left on site per owner washout decision ("it is what it is").

## Open questions for v5+

- ~~Does the recall loss on the heldout appear in production, or was it concentrated in noisily-labeled regions?~~ **Answered 2026-07-31 — see addendum 7.**
- Is Belita Gracia a one-off or a whole class of Spanish-language legacy profiles that need dedicated hard negatives?
- Would the same fix work for a different architecture (e.g., fine-tuning the embedder instead of a frozen MLP)?
- **NEW: does the hard-negative↔positive interference (addendum 7) mean v6 needs paired examples** — for every hard-negative class added, a matched hard-positive set from the same surface style (memorial-events-blocked vs festivals-kept now inverts under the grief-vs-news rule anyway)?
