---
name: violence-promotion-v1-hypotheses
description: Hypotheses confirmed and open questions from violence_promotion v1 build and shadow deploy
metadata:
  type: project
---

# Violence Promotion v1 — Hypotheses

**Date:** 2026-07-28

## Confirmed

1. **The binary-preinfilter recipe transfers cleanly.** Same frozen-embedder + MLP architecture (mpnet-base-v2 → StandardScaler → MLP(256,128)) that worked for commerce_prefilter and obituary_detector works for violence_promotion too. Inference code, oracle.py, calibration_report, CHANGE_REQUEST — the template is mature and reproducible.

2. **The prompt boundary holds on smoke tests.** The oracle prompt's core discriminator — "does this article make violence seem normal, acceptable, desirable, or a source of progress?" — produces correct classifications on the 5 canonical test cases (combat=0.997, recovery=0.035, weapons-as-progress=0.989, peace=0.000, borderline-economic-framing=0.721).

3. **DeepSeek is cost-effective for binary labeling.** 2,000 articles ≈ $0.45 total. The JSON response format with temp=0 produces clean parseable scores. Same pattern validated on obituary_detector.

4. **Shadow-deploy is the correct first step for prefilter classifiers.** The model has known gaps (recall 0.55, only 1,957 training samples) but shadow mode costs nothing in content loss. Production data will reveal which error classes actually matter.

## Open questions

5. **How low can recall go before it matters?** At 0.55 recall, ~45% of violence-promoting content leaks through. For a stamp-only prefilter, this is invisible to users (no content dropped). But when ovr.news starts excluding stamped articles, the false-negative rate determines how much off-brand content reaches the lens. The calibration scan found 8.7% of pipeline articles are violence-promoting — at 55% recall, ~3.9% would still reach ovr.news. Acceptable?

6. **Is the single calibration FP (Korean Su-57 crash) a class or an outlier?** The independent calibration found 1 FP at 0.95 — a Korean article about an Su-57 fighter jet crash. Is this "weapons system in headline but framed as news reporting" a recurring pattern? Shadow data will tell us.

7. **Does the small training set (1,957) cover the violence-promotion spectrum?** With only 211 positive examples, the model has seen a limited range of violence-promoting language. Production shadow will reveal whether the recall gap is concentrated in specific domains (defense industry, state violence, armed groups) or evenly distributed.

8. **Does the weapons-manufacturing-as-progress framing generalize across languages?** The prompt explicitly targets domestic arms production framed as achievement/growth/innovation — a framing common in state media. The multilingual embedder should handle this, but we haven't validated on non-English weapons-industry content.

## Design decisions (not yet tested)

9. **ADR-004 stamp-only approach pushes the enforcement decision to consumers.** ovr.news excludes stamped articles at selection; investment_risk and resilience keep them. This is correct in theory, but means the "did we get it right?" feedback loop requires cross-repo coordination. A violence-promoting article flagged by the prefilter that investment_risk would have scored highly is invisible unless someone explicitly checks.

10. **The 0.95 threshold was chosen for precision, not recall.** At 0.90: precision 0.896, recall 0.611 (OOF). At 0.80: precision 0.890, recall 0.687. If shadow data shows the model is too conservative, lowering the threshold is cheaper than retraining — but precision degrades quickly below 0.95.
