# Thriving Filter v1

## Lineage

`uplifting v6` (deployed) → `uplifting v7` (prompt rewrite, not deployed) → **`thriving v1`** (lens alignment + dimension refinement)

## What Changed

### 1. Renamed from "uplifting" to "thriving" (ADR-012)

Aligns with ovr.news editorial lens naming. The filter now produces `thriving_analysis` instead of `uplifting_analysis`. See `docs/adr/012-lens-aligned-filter-naming.md`.

### 2. Removed `social_cohesion_impact` Dimension

**Problem:** `social_cohesion_impact` (20% weight) measured "communities strengthened, solidarity built" — this is what Belonging's `community_fabric` (25% weight) measures. Articles about community gardens, mutual aid networks, and neighborhood events scored high on both filters, weakening lens differentiation.

**Solution:** Removed `social_cohesion_impact` entirely. Redistributed weight:

| Dimension | uplifting v7 | thriving v1 | Change |
|-----------|-------------|-------------|--------|
| human_wellbeing_impact | 0.30 | **0.40** | +0.10 |
| ~~social_cohesion_impact~~ | ~~0.20~~ | **removed** | — |
| justice_rights_impact | 0.15 | **0.25** | +0.10 |
| evidence_level | 0.10 | 0.10 | — |
| benefit_distribution | 0.10 | 0.10 | — |
| change_durability | 0.15 | 0.15 | — |

- Impact domains: 0.40 + 0.25 = **0.65** (unchanged from v7)
- Assessment: 0.10 + 0.10 + 0.15 = **0.35** (unchanged from v7)
- 5 dimensions instead of 6

### 3. Oracle Multi-Run Averaging

uplifting v7's single oracle run produced 15-17 discrete values per dimension, leading to poor training signal and MAE regression (0.787 vs v6's 0.673). Thriving v1 uses 3-run averaging for ~45+ continuous values per dimension.

### 4. Prompt Includes Belonging Distinction

The oracle prompt explicitly calls out the Thriving vs Belonging boundary:
- Community togetherness/solidarity WITHOUT measurable wellbeing improvement → Belonging, score 0-2 on Thriving
- Includes a contrastive example (village festival: high Belonging, low Thriving)

## Files

| File | Purpose |
|------|---------|
| `config.yaml` | Filter configuration, dimensions, weights, tiers |
| `prompt-compressed.md` | Oracle scoring prompt (5 dimensions, Belonging distinction) |
| `base_scorer.py` | Base scorer class with filter constants |
| `inference.py` | Local model inference |
| `inference_hub.py` | HuggingFace Hub inference |
| `inference_hybrid.py` | Two-stage hybrid inference (after probe training) |

## Oracle Scoring

```bash
# Run 3x with thriving v1 prompt
python -m ground_truth.batch_scorer --filter filters/thriving/v1 --source datasets/raw/master_dataset.jsonl --output-dir datasets/scored/thriving_v1_run1
python -m ground_truth.batch_scorer --filter filters/thriving/v1 --source datasets/raw/master_dataset.jsonl --output-dir datasets/scored/thriving_v1_run2
python -m ground_truth.batch_scorer --filter filters/thriving/v1 --source datasets/raw/master_dataset.jsonl --output-dir datasets/scored/thriving_v1_run3

# Average the 3 runs
python scripts/oracle/average_oracle_runs.py \
    --runs datasets/scored/thriving_v1_run1 datasets/scored/thriving_v1_run2 datasets/scored/thriving_v1_run3 \
    --output datasets/scored/thriving_v1_averaged \
    --filter-name thriving
```

## Training

Standard pipeline on gpu-server:

```bash
python training/prepare_data.py --filter filters/thriving/v1 --data-source datasets/scored/thriving_v1_averaged/thriving_v1_averaged.jsonl
python training/train.py --filter filters/thriving/v1 --data-dir datasets/training/thriving_v1
PYTHONPATH=. python scripts/calibration/fit_calibration.py --filter filters/thriving/v1 --data-dir datasets/training/thriving_v1 --test-data datasets/training/thriving_v1/test.jsonl
```

## Target Metrics

- **MAE:** < 0.55 (belonging-level, achievable with ADR-010 precision + averaged targets)
- **Cross-lens correlation:** `r(thriving, belonging)` < 0.508 (old uplifting-belonging correlation)
