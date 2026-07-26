# Solutions v6 — Retrained with probe-split corpus + tightened oracle prompt

**Status (2026-07-26): trained, calibrated. Gate pending (scored test set, gate script needs format debug).**

## What changed from v5

v5 deployed the e5 probe (ADR-006) but used the v4-trained model. The v4 model learned concreteness inflation from the v4 oracle prompt, which had weaker Step-1 routing and higher caps (4.0-5.0 vs 3.0-3.5).

v6 retrains the model on a probe-split corpus:
- **Probe-negative (~46%)**: all dimensions = 0 (free, no oracle cost)
- **Probe-positive, low (<2.0, ~31%)**: kept v4 oracle scores (already correct)
- **Probe-positive, mid-range (2.0-6.0, ~23%)**: rescored with tightened v5 oracle prompt (DeepSeek, $2.96)
- **Probe-positive, high (>=6.0, <1%)**: kept v4 oracle scores (clear solutions)

The rescored mid-range data shows 702 false positives dropped and 28 real solutions promoted vs. v4 oracle scores.

## Training results (2026-07-26)

| Metric | v4 | v6 |
|--------|----|----|
| Val MAE | 0.564 | **0.476** |
| Train articles | 9,265 | 8,236 (80/10/10 split) |
| Oracle rescore cost | — | $2.96 (2,401 articles) |

Epoch progression: train MAE 1.08→0.51→0.40, val MAE 0.58→0.49→0.48.

## Production impact (projected)

On the 62-article medium+ sample from the v5 production run:
- v5 model: 62 surfacing, ~20 false positives
- v6 trained on cleaner data: estimated ~30-40% fewer false positives

The probe (unchanged from v5, calibrated for ≤2% FN rate) screens ~96% of production articles at Stage 1.

## Files

- `config.yaml` — v6.0 dimensions, weights, gatekeeper, tiers
- `prompt-compressed.md` — tightened oracle prompt (Step-1 routing, Flag-A for enforcement, science fix)
- `base_scorer.py` — BaseSolutionsScorer
- `inference.py` — SolutionsScorer (local LoRA load)
- `inference_hybrid.py` — SolutionsHybridScorer (e5 probe + model)
- `inference_hub.py` — SolutionsScorerHub (Hub load)
- `prefilter.py` — SolutionsPreFilterV6
- `probe/` — e5-small embedding probe (same as v5, threshold 1.225)
- `calibration.json` — per-dim isotonic (ADR-008)
- `model/` — LoRA adapter (gitignored)
- `prompt-compressed.md` — oracle prompt with tightened Step-1, science/product-review/enforcement blind-spot fixes
