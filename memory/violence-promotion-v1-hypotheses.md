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

## Settled 2026-08-01 (NM#281)

9. **The enforcement path now exists, default-off, and is a config flip.**
   `pipeline.violence_promotion.enforce: false` → `_enforce_violence_promotion()`
   in NexusMind's `scripts/main.py`. Flipping it after LD#82 needs no new mechanism and no
   deploy. **Caveat carried in the config comment:** at recall 0.55, enforcing
   gates roughly half of true positives — precision-first by construction, so
   question 5 below becomes an owner decision, not a modelling one.

10. **Fail-open is now an explicit decision, not an accident.** If the detector
    errors, articles are unstamped and **admitted**. Correct for a
    precision-first gate — fail-closed would empty the corpus on any model
    failure — but it means a silent model failure admits everything, with only
    an ERROR line as signal. `_enforce_violence_promotion` keys on `is True`
    (not truthiness) so unstamped and non-bool values can never cause a drop.

11. **The first gate implementation could not fire** (found by adversarial
    review the same day, before any flip). It was placed in `_is_duplicate`,
    which runs *before* violence stamping — `enforce: true` would have dropped
    zero while logging `0 violence`. Fixed in `b85a467`. **Lesson for whoever
    flips it: verify from the `Violence promotion ENFORCED: dropped N` line,
    not from `filtered_*.jsonl`,** which only ever contains survivors.

12. **Three run modes silently skip stamping entirely** (NM#286): single-filter
    runs, `--no-dedup`, and a shared-dedup exception all leave `_article_cache`
    empty, so the detector never runs. Combined with fail-open, those modes
    admit everything. Fix before enforcing.

## Open questions

**Measured 2026-08-03 — shadow flag rate, four consecutive cycles.** 95/2,172
(4.4%), 61/2,082 (2.9%), 58/2,627 (2.2%), 53/2,626 (2.0%). Stamps present on
**100%** of live rows (`_violence_model: v1`), so the detector is running
everywhere it should in the scheduled path.

Worth noting against question 5: the calibration scan put prevalence at 8.7%,
and 8.7% × 0.55 recall ≈ **4.8% expected flag rate**. The observed rate sits at
or below that (4.4% falling to 2.0%), which is *consistent* with the recall
estimate rather than contradicting it. **Do not read the decline across cycles
as a trend** — corpus composition differs per cycle and n is 4. What this does
give #82 is a concrete prior: expect to audit ~50–95 articles per cycle, and
expect roughly as many true positives again to be sitting unflagged.

5. **How low can recall go before it matters?** At 0.55 recall, ~45% of violence-promoting content leaks through. For a stamp-only prefilter, this is invisible to users (no content dropped). But when ovr.news starts excluding stamped articles, the false-negative rate determines how much off-brand content reaches the lens. The calibration scan found 8.7% of pipeline articles are violence-promoting — at 55% recall, ~3.9% would still reach ovr.news. Acceptable?

6. **Is the single calibration FP (Korean Su-57 crash) a class or an outlier?** The independent calibration found 1 FP at 0.95 — a Korean article about an Su-57 fighter jet crash. Is this "weapons system in headline but framed as news reporting" a recurring pattern? Shadow data will tell us.

7. **Does the small training set (1,957) cover the violence-promotion spectrum?** With only 211 positive examples, the model has seen a limited range of violence-promoting language. Production shadow will reveal whether the recall gap is concentrated in specific domains (defense industry, state violence, armed groups) or evenly distributed.

8. **Does the weapons-manufacturing-as-progress framing generalize across languages?** The prompt explicitly targets domestic arms production framed as achievement/growth/innovation — a framing common in state media. The multilingual embedder should handle this, but we haven't validated on non-English weapons-industry content.

## Design decisions (not yet tested)

9. **ADR-004 stamp-only approach pushes the enforcement decision to consumers.** ovr.news excludes stamped articles at selection; investment_risk and resilience keep them. This is correct in theory, but means the "did we get it right?" feedback loop requires cross-repo coordination. A violence-promoting article flagged by the prefilter that investment_risk would have scored highly is invisible unless someone explicitly checks.

10. **The 0.95 threshold was chosen for precision, not recall.** At 0.90: precision 0.896, recall 0.611 (OOF). At 0.80: precision 0.890, recall 0.687. If shadow data shows the model is too conservative, lowering the threshold is cheaper than retraining — but precision degrades quickly below 0.95.
