# ADR-017: Inter-Oracle MAE as Distillation Quality Floor

**Date:** 2026-04-07
**Status:** Accepted

## Decision

The inter-oracle MAE (mean absolute error between different frontier LLMs scoring the same articles with the same prompt) sets a hard floor on distilled model quality. We will not invest optimization effort to push distilled filter MAE below the inter-oracle disagreement range of **0.6-1.0** per dimension.

## Context

### The experiment

We scored the same articles across three filters (uplifting v5, foresight v1, cultural-discovery v1) using three independent oracle models from different model families:

- **Gemini Flash 2.5** (Google) — our production oracle
- **GPT-4o** (OpenAI, via GitHub Models)
- **Llama-3.1-405B-Instruct** (Meta, via GitHub Models)

Each model received the identical prompt and article text. Five articles per filter were selected with score spread across quintiles (5th, 25th, 50th, 75th, 95th percentile of weighted average).

### Results: inter-oracle MAE

| Filter | GPT-4o vs Gemini | Llama vs Gemini | GPT-4o vs Llama |
|--------|:---:|:---:|:---:|
| uplifting_v5 | 2.53 | 1.00 | 1.87 |
| foresight_v1 | 0.60 | 1.92 | 1.92 |
| cultural_discovery_v1 | 0.86 | 1.00 | 0.66 |

The best-agreeing oracle pairs per filter:

- **Uplifting:** Gemini-Llama at 1.00 (GPT-4o is an outlier — scores near zero on mid-range articles)
- **Foresight:** Gemini-GPT-4o at 0.60 (Llama hallucinated high scores on clearly off-topic articles)
- **Cultural discovery:** GPT-4o-Llama at 0.66 (all three models reasonably aligned)

### What this means for distillation

Our production distilled filters achieve:

| Filter | Distilled MAE | Best oracle-pair MAE |
|--------|:---:|:---:|
| uplifting v6 | 0.673 | 1.00 |
| belonging v1 | 0.534 | ~0.7-1.0 (estimated) |
| investment-risk v6 | 0.497 | ~0.7-1.0 (estimated) |
| foresight v1 | 0.744 | 0.60 |

The distilled models are already at or below the noise floor of oracle agreement. A distilled model with MAE 0.7 against Gemini Flash is not "wrong by 0.7" — it is performing within the range where different frontier models disagree with each other.

### Additional observations

1. **GPT-4o applies "out of scope" rules too aggressively on uplifting** — scores near zero on articles Gemini and Llama both score 2-4. This is a model-specific interpretation bias, not a prompt deficiency.
2. **Llama-405B struggles with scope judgment on foresight** — hallucinated high scores (6-8) on a clearly off-topic article where Gemini and GPT-4o both scored 1.0.
3. **Cultural discovery has the best cross-model robustness** — all three pairs within 0.66-1.00 MAE.

### Gemini Flash remains the best oracle choice

Across all three filters, Gemini Flash is the most balanced scorer:

- **Never hallucinated** — unlike Llama-405B which scored 6-8 on a clearly off-topic foresight article.
- **Never over-applied scope rules** — unlike GPT-4o which zeroed out mid-range uplifting articles that both Gemini and Llama scored 2-4.
- **Fastest and cheapest** — ~$0.00015/article vs ~$0.001+ for GPT-4o.
- **Best overall agreement** — Gemini appears on the best-agreeing pair for 2 out of 3 filters (uplifting: Gemini-Llama 1.00, foresight: Gemini-GPT-4o 0.60).

The experiment validates the original oracle choice (see ADR-010). No reason to switch.

## Consequences

- **Stop chasing MAE below ~0.6.** If a distilled filter has MAE < 1.0 against its oracle, it is performing at inter-oracle quality. Further training data, model size, or hyperparameter tuning will yield diminishing returns.
- **Invest in prompt robustness instead.** The uplifting MAE of 2.53 (GPT-4o vs Gemini) suggests the prompt's scope rules leave room for interpretation. Tightening those rules will reduce oracle disagreement and indirectly improve distillation.
- **Use multi-oracle agreement as a calibration signal.** Articles where all three oracles agree are high-confidence ground truth. Articles where they disagree may need prompt clarification or should be down-weighted in training.
- **Foresight v1 is already at its ceiling** (distilled MAE 0.744 vs oracle floor 0.60). Improving it requires a better prompt, not more data.

## References

- Raw comparison data: `scripts/three_way_comparison.json` <!-- placeholder -->
- Comparison script: `scripts/compare_github_models.py` <!-- placeholder -->
- ADR-010: Oracle consistency > data volume
