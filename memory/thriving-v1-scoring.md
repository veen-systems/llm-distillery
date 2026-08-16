---
name: thriving-v1-scoring
description: Thriving v1 — PARKED indefinitely (ADR-015). Bimodal distribution from orthogonal lens design. Uplifting v7 serves the Thriving tab.
type: project
---

# Thriving v1 Status

## Current State (updated 2026-04-19)

**PARKED indefinitely** per ADR-015 (lenses as perspectives, not partitions). Two training attempts produced val MAE 1.09 and 0.97 (calibrated 0.94). Root cause turned out to be the orthogonal-lens prompt design (bimodal scores), not the training pipeline. Uplifting v7 remains on the Thriving tab — v7 is deployed on Hub with hybrid inference. <!-- verify: grep -qE "\*\*thriving\*\*.*PARKED indefinitely" CLAUDE.md && echo PASS || echo FAIL -->

## What We Tried

### Training Attempt 1 — Hybrid dataset, no head+tail, 3 epochs
- **Data**: 5,568 articles (1,048 triple-averaged + 4,520 single-run)
- **Result**: Val MAE 1.09
- **Problem**: Selection bias — averaged articles were enriched positives (mean score 5.27), single-run were random negatives (mean 2.04). Two contradictory populations.

### Training Attempt 2 — Full 2-run averaged, head+tail, 6 epochs
- **Data**: 5,568 articles, all 2-run averaged (no bias), 34-37 unique values per dimension
- **Config**: `--use-head-tail --head-tokens 256 --tail-tokens 256 --epochs 6`
- **Result**: Val MAE 0.97 (best at epoch 5), calibrated test MAE **0.94**
- **Overfitting**: Train MAE 0.63 vs val 0.97 by epoch 6 — model memorizes but doesn't generalize

### Per-dimension MAE (best model, calibrated)
| Dimension | MAE |
|-----------|-----|
| human_wellbeing_impact | 0.92 |
| justice_rights_impact | 0.90 |
| change_durability | 0.90 |
| benefit_distribution | 0.95 |
| evidence_level | 1.02 |

## Root Cause: Bimodal Score Distribution

The thriving prompt produces a bimodal distribution that is fundamentally harder to learn:

| Oracle WA bucket | % of data | Description |
|------------------|-----------|-------------|
| 0-1 | 35.8% | Clear noise (articles not about thriving) |
| 1-3 | 20.9% | Low relevance |
| 3-5 | 17.7% | **Sparse middle — model struggles here** |
| 5-7 | 23.1% | Genuine thriving content |
| 7+ | 2.5% | Exceptional (model assigns 0 to this tier) |

Compare: belonging v1 (MAE 0.49) and investment-risk v6 (MAE 0.47) likely have smoother distributions. The thriving prompt's scope check creates a hard boundary — articles are either clearly in-scope (scored 4-7) or clearly out (scored 0-1), with very few in between. The model can't learn the transition.

Additionally, the model's predicted range is compressed (max ~8.2 vs oracle max 9.0), meaning it never assigns HIGH tier.

## Open Questions for Future Work

1. **Is the prompt the problem?** The scope check may be too binary. A softer gradation might produce a smoother distribution that's easier to learn.
2. **Would more data help?** 5,568 articles may not be enough for a bimodal distribution. 10K+ with enriched middle-range articles (active learning targeting WA 2-5) could help.
3. **Would a different loss function help?** MSE penalizes large errors quadratically. A Huber loss or asymmetric loss might handle the bimodal case better.
4. **Should thriving just be uplifting v7?** The v7 prompt (before thriving rename) achieved MAE 0.787. The dimension reduction (6→5, removing social_cohesion_impact) and the prompt changes may have made the task harder, not easier.

## Assets (all preserved for future work)

| Asset | Location |
|-------|----------|
| Oracle data (run 1) | `datasets/scored/thriving_v1_run1/thriving/` (5,568 articles) |
| Oracle data (run 2) | `datasets/scored/thriving_v1_run2/thriving/` (5,568 articles) |
| Oracle data (run 3, partial) | `datasets/scored/thriving_v1_run3/thriving/` (1,051 articles) |
| 2-run averaged scores | `datasets/scored/thriving_v1_averaged_full/thriving_v1_averaged.jsonl` |
| Training splits | `datasets/training/thriving_v1/` (4,453/556/559) |
| Trained model (attempt 2) | `filters/thriving/v1/model/` |
| Calibration | `filters/thriving/v1/calibration.json` |
| Filter package | `filters/thriving/v1/` (config, prompt, prefilter, scorers) |
| Source corpus | `datasets/raw/thriving_v1/oracle_input.jsonl` (6,590 articles) |

## Cost

- Run 1: ~€9.25
- Runs 2+3 (partial): ~€12
- Run 2 completion: ~€20-25
- **Total oracle cost: ~€41-46**
