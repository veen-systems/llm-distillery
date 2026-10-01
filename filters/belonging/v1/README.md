# Belonging Filter v1

**Date:** 2026-03-04
**Status:** Deployed (HuggingFace Hub + gpu-server)
**Base model:** Gemma-3-1B + LoRA

## Purpose

Scores articles for evidence of genuine belonging: social fabric, rootedness, and intergenerational continuity that cannot be purchased or optimized. Inspired by Blue Zones research but deliberately excludes commercially-capturable dimensions (diet, exercise, longevity hacks).

**ovr.news tab:** Belonging (pending frontend integration)

See `DEEP_ROOTS.md` for philosophical grounding (Simone Weil, Tönnies, Blue Zones).

## Results

| Metric | Value |
|--------|-------|
| Val MAE (raw) | 0.534 |
| Val MAE (calibrated) | **0.489** |
| Calibration improvement | +8.3% |
| Training articles | 7,370 |
| Val articles | 738 |
| Test articles | 738 |
| Probe MAE | 0.54 |

### Per-Dimension MAE (calibrated, val set)

| Dimension | Weight | Raw MAE | Calibrated MAE |
|-----------|--------|---------|----------------|
| intergenerational_bonds | 0.25 | 0.522 | 0.468 |
| community_fabric | 0.25 | 0.590 | 0.557 |
| reciprocal_care | 0.10 | 0.508 | 0.458 |
| rootedness | 0.15 | 0.531 | 0.485 |
| purpose_beyond_self | 0.15 | 0.596 | 0.555 |
| slow_presence | 0.10 | 0.454 | 0.412 |

### Tier Thresholds

| Tier | Threshold | Description |
|------|-----------|-------------|
| HIGH | >= 7.0 | Strong evidence of genuine belonging |
| MEDIUM | >= 4.0 | Some belonging elements present |
| LOW | < 4.0 | Minimal belonging evidence |

**Gatekeeper:** `community_fabric` < 3.0 caps overall score at 3.42.

### Training Data Distribution

| Source | Articles | HIGH | MEDIUM | LOW |
|--------|----------|------|--------|-----|
| Scope candidates (probe-screened) | 4,999 | 72 (1.4%) | 722 (14.4%) | 4,205 (84.1%) |
| Random negatives | 2,500 | 1 (0.0%) | 36 (1.4%) | 2,463 (98.5%) |
| **Merged (deduplicated)** | **7,370** | **72 (1.0%)** | **730 (9.9%)** | **6,568 (89.1%)** |

## Training Configuration

| Parameter | Value |
|-----------|-------|
| Base model | `google/gemma-3-1b-pt` |
| LoRA rank | 16 |
| LoRA alpha | 32 |
| Epochs | 3 |
| Batch size | 8 |
| Learning rate | 2e-5 |
| Max length | 512 |
| Head+tail | 256 + 256 tokens |
| Trainable params | 13.05M / 1.01B (1.29%) |

### Training Progression

| Epoch | Train MAE | Val MAE |
|-------|-----------|---------|
| 1 | — | 0.784 |
| 2 | — | 0.698 |
| 3 | — | **0.534** |

## Usage

### Local Inference

```python
from filters.belonging.v1.inference import BelongingScorer

scorer = BelongingScorer()
result = scorer.score_article({"title": "...", "content": "..."})
# result["tier"] -> "high", "medium", or "low"
# result["weighted_average"] -> 0.0-10.0
# result["scores"] -> per-dimension scores
```

### HuggingFace Hub Inference

```python
from filters.belonging.v1.inference_hub import BelongingScorerHub

scorer = BelongingScorerHub(
    repo_id="jeergrvgreg/belonging-filter-v1",
    token="hf_...",
)
```

### Hybrid Inference

```python
from filters.belonging.v1.inference_hybrid import BelongingHybridScorer

scorer = BelongingHybridScorer()
result = scorer.score_article(article)
# result["stage_used"] -> "stage1_low" or "stage2"
```

## Data Strategy

Belonging is a needle-in-haystack filter (~1% HIGH, ~10% MEDIUM in news). Training data was built using screen+merge (ADR-003):

1. **Phase 3:** Oracle validated 152 articles (3 HIGH, 16 MEDIUM, 133 LOW)
2. **Scope probe:** Logistic regression on e5-small embeddings (73.7% recall on MEDIUM+) ranked 178K articles
3. **Scope candidates:** Top 5,000 probe-ranked articles scored by oracle
4. **Random negatives:** 2,500 random articles scored by oracle
5. **Merge:** 7,370 unique articles after deduplication (129 cross-source duplicates removed)

## Dimension Independence

Phase 3 flagged community_fabric-rootedness at r=0.845 (n=19). Re-evaluated with full batch data (n=801 MEDIUM+): r=0.470 — not redundant. The high initial correlation was a small-sample artifact.

## Cross-Filter Orthogonality

| Filter pair | r | Status |
|-------------|---|--------|
| belonging-uplifting | 0.508 | Moderate overlap |
| belonging-cultural_discovery | 0.547 | Moderate overlap |
| belonging-sustainability_tech | 0.119 | Orthogonal |

498 belonging MEDIUM+ articles are truly exclusive (LOW on all other filters). Belonging captures distinct content: intergenerational bonds, rootedness, mutual care in ordinary life. Deployed as separate tab per ADR-009.

## Known Limitations

- **slow_presence caps at ~6.0 in news** — Unhurried rituals need literary/longform content to score higher. Not a prompt issue; news is inherently fast-paced.
- **Crime fix not applied** — Unlike uplifting v6, no crime article label correction was done. Monitor for over-scored justice articles.

## Files

```
filters/belonging/v1/
├── README.md                    # This file
├── STATUS.md                    # Development status tracker
├── DEEP_ROOTS.md                # Philosophical grounding
├── config.yaml                  # Dimensions, weights, gatekeeper
├── prompt-compressed.md         # Oracle prompt
├── base_scorer.py               # Scoring logic
├── inference.py                 # Local inference
├── inference_hub.py             # Hub inference
├── inference_hybrid.py          # Two-stage hybrid
├── calibration.json             # Isotonic regression (738 val articles)
├── training_history.json        # Per-epoch metrics
├── training_metadata.json       # Hyperparameters
├── model/                       # LoRA adapter + tokenizer
└── probe/                       # e5-small MLP probe
```

---

*Created: 2026-03-04*
