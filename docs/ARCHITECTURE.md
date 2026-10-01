# LLM Distillery - Architecture

**Last Updated**: 2026-02-22
**Status**: Production system with 4 deployed filters, hybrid inference pipeline

---

## Table of Contents

1. [Core Principles](#core-principles)
2. [Knowledge Distillation Pipeline](#knowledge-distillation-pipeline)
3. [Filter Package Architecture](#filter-package-architecture)
4. [Shared Infrastructure](#shared-infrastructure)
5. [Training Pipeline](#training-pipeline)
6. [Hybrid Inference Pipeline](#hybrid-inference-pipeline)
7. [Score Calibration](#score-calibration)
8. [Deployment](#deployment)
9. [Key Documents](#key-documents)

---

## Core Principles

### 1. Oracle Output Discipline

**Rule**: Oracles output **dimensional scores ONLY** (0-10), never tier/stage classifications.

**Why**: Enables changing tier thresholds without re-labeling training data. Separates concerns: oracle scores dimensions, postfilter classifies tiers.

### 2. Three-Stage Processing Pipeline

```
Article (title + text)
    |
    v
Prefilter          Fast rule-based (Python regex/keywords)
    |              Blocks obvious noise, <10% false negatives
    v
Oracle (LLM)       Scores dimensions (0-10) + reasoning
    |              Models: Gemini Flash ($0.00015/article)
    v
Postfilter         Computes tiers from dimensional scores
    |              Applies gatekeeper rules, configurable thresholds
    v
Final Output       Tier + dimensional scores + metadata
```

### 3. Knowledge Distillation

| | Teacher (Oracle) | Student |
|---|---|---|
| **Model** | Gemini Flash | Gemma-3-1B + LoRA |
| **Cost** | $0.00015/article | $0 (local) |
| **Latency** | 2-5 seconds | 30-40ms |
| **Purpose** | Label training data | Production inference |

**Workflow**:
1. Oracle scores 8-10K articles per filter
2. Student model fine-tuned on oracle scores (Gemma-3-1B + LoRA)
3. Isotonic calibration corrects score compression
4. Hybrid inference adds fast embedding probe for speedup
5. Deploy to HuggingFace Hub (private repos)

---

## Knowledge Distillation Pipeline

### Phase 1: Ground Truth Generation

```bash
# Score training data with oracle (Gemini Flash)
python -m ground_truth.batch_scorer \
  --filter filters/uplifting/v6 \
  --source datasets/raw/master_dataset.jsonl \
  --target-count 10000

# For needle-in-haystack filters: screen + merge (ADR-003)
# Random data provides negatives, screened data enriches positives
```

**Cost**: ~$1.50 per 10K articles (Gemini Flash)

### Phase 2: Data Preparation & Training

```bash
# Prepare stratified train/val/test splits (80/10/10)
python training/prepare_data.py \
  --filter filters/uplifting/v6 \
  --data-source datasets/scored/uplifting_v6/

# Train Gemma-3-1B + LoRA on oracle scores
python training/train.py \
  --filter filters/uplifting/v6 \
  --data-dir datasets/training/uplifting_v6
```

**Requirements**: 16GB+ GPU, ~2-4 hours per filter

### Phase 3: Calibration & Deployment

```bash
# Fit isotonic calibration on validation set
PYTHONPATH=. python scripts/calibration/fit_calibration.py \
  --filter filters/uplifting/v6 \
  --data-dir datasets/training/uplifting_v6 \
  --test-data datasets/training/uplifting_v6/test.jsonl

# Upload adapter to HuggingFace Hub
python scripts/deployment/upload_to_hub.py \
  --filter filters/uplifting/v6 \
  --repo-id jeergrvgreg/uplifting-filter-v6
```

---

## Filter Package Architecture

Each filter is a self-contained package:

```
filters/<filter-name>/v<version>/
├── config.yaml              # Dimensions, weights, tier definitions
├── prompt-compressed.md     # Oracle prompt (used for scoring)
├── base_scorer.py           # Subclass of FilterBaseScorer (shared logic)
├── inference.py             # Local inference (loads adapter from model/)
├── inference_hub.py         # HuggingFace Hub inference (loads from Hub)
├── inference_hybrid.py      # Two-stage hybrid inference (probe + model)
├── calibration.json         # Per-dimension isotonic calibration maps
├── model/                   # LoRA adapter files
│   ├── adapter_config.json
│   ├── adapter_model.safetensors
│   ├── tokenizer.json
│   └── tokenizer_config.json
├── probe/                   # Embedding probe for hybrid inference
│   └── embedding_probe_e5small.pkl
├── README.md                # Filter documentation
├── README_MODEL.md          # HuggingFace model card
├── training_metadata.json   # Training hyperparams and metrics
└── training_history.json    # Per-epoch training logs
```

### config.yaml Structure

```yaml
filter:
  name: "uplifting"
  version: "6.0"
  base_model: "google/gemma-3-1b-pt"

dimensions:
  - name: "agency"
    weight: 1.0
  - name: "progress"
    weight: 1.0
  # ... more dimensions

tiers:
  impact:
    min_score: 7.0
    description: "High impact uplifting content"
  connection:
    min_score: 4.0
  not_uplifting:
    max_score: 3.9

gatekeeper_rules:
  - dimension: "collective_benefit"
    threshold: 5.0
    action: "IF collective_benefit < 5.0 THEN max_overall = 3.0"
```

---

## Shared Infrastructure

All shared code lives in `filters/common/`:

```
filters/common/
├── filter_base_scorer.py    # FilterBaseScorer — shared base class for all filters
├── model_loading.py         # load_base_model_for_seq_cls(), load_lora_model()
├── score_calibration.py     # Isotonic calibration: fit, apply, save, load
├── embedding_stage.py       # e5-small embedding + MLP probe for hybrid Stage 1
├── hybrid_scorer.py         # Two-stage hybrid inference orchestrator
├── base_prefilter.py        # Base prefilter with commerce detector integration
├── text_cleaning.py         # Text normalization utilities
├── text_preprocessing.py    # Tokenization and truncation
└── commerce_prefilter/      # ML commerce/promotional content detector
```

### FilterBaseScorer (`filter_base_scorer.py`)

Base class that all filter `base_scorer.py` files inherit from. Provides:
- Model loading with Gemma-3 compatibility workaround
- Tokenization and batched inference
- Score extraction from model output
- Automatic calibration loading and application
- Tier classification from dimensional scores

### Model Loading (`model_loading.py`)

Handles the Gemma-3-1B compatibility issue: `google/gemma-3-1b-pt` uses `Gemma3TextConfig` (model_type `gemma3_text`), but `AutoModelForSequenceClassification` only maps `gemma3` (multimodal config). The loader tries Auto first, falls back to building a custom classification head on `Gemma3TextModel`.

Also provides `load_lora_model()` for consistent LoRA adapter loading with key format remapping between local format (`.lora_A.default.weight`) and Hub format (`.lora_A.weight`).

### Hybrid Scorer (`hybrid_scorer.py`)

Orchestrates two-stage inference:
1. **Stage 1**: e5-small embedding + MLP probe (1-2ms) — fast approximate score
2. **Stage 2**: Full Gemma-3-1B model (30-40ms) — only for articles above probe threshold

See [ADR-006](adr/006-hybrid-inference-pipeline.md) for design rationale.

---

## Training Pipeline

### Model Architecture

**Base Model**: `google/gemma-3-1b-pt` (Gemma-3-1B)
- ~1B parameters
- Fine-tuned with LoRA (rank 16, ~2M trainable parameters)
- Regression head: 8 outputs (one per dimension, 0-10 scale)
- Loss: MSE on dimensional scores

### Training Hyperparameters

```yaml
base_model: google/gemma-3-1b-pt
epochs: 3
batch_size: 4
learning_rate: 2e-5
lora_rank: 16
lora_alpha: 32
max_length: 512  # tokens (head+tail truncation)
```

### Training Data

- **Size**: 8-10K articles per filter
- **Splits**: 80% train / 10% validation / 10% test
- **Enrichment**: Screen+merge for needle-in-haystack filters (ADR-003), active learning for rare tiers (ADR-005)
- **Format**: JSONL with `text`, `dimension_scores`, `overall_score`, `tier`

### Validation Metrics

- **Per-dimension MAE**: Target < 1.0 (production filters achieve 0.47-0.74)
- **Tier classification accuracy**: Target > 85%
- **Calibrated MAE**: Post-calibration improvement typically 3-7%

---

## Hybrid Inference Pipeline

Two-stage pipeline for faster inference (ADR-006):

```
Article
    |
    v
Stage 1: e5-small Probe (1-2ms)
    |
    |--- score < threshold ---> Return probe estimate (skip Stage 2)
    |
    |--- score >= threshold --->
    v
Stage 2: Gemma-3-1B Model (30-40ms)
    |
    v
Calibrated scores + tier
```

### Performance by Filter

| Filter | Probe MAE | Threshold | FN Rate | Speedup |
|--------|-----------|-----------|---------|---------|
| uplifting v6 | 0.49 | 4.5 | 1.7% | ~2x |
| sustainability_technology v3 | 0.91 | 1.25 | ~1% | ~1.3x |
| investment-risk v6 | 0.557 | 1.50 | 0.8% | ~1.1x |
| cultural-discovery v4 | 0.87 | 1.25 | 3% | ~1.5x |

### Probe Architecture

- Embedding: `intfloat/e5-small-v2` (33M params, 384-dim)
- Classifier: MLP (384 -> 128 -> 1), trained on same training data
- Stored in `probe/embedding_probe_e5small.pkl`

---

## Score Calibration

Post-hoc isotonic regression corrects MSE-trained score compression (ADR-008):

- **Problem**: MSE loss causes predictions to regress toward the mean, compressing the score range
- **Solution**: Per-dimension isotonic regression fitted on validation set
- **Format**: `calibration.json` — maps raw model scores to calibrated scores via `numpy.interp`
- **Integration**: `FilterBaseScorer._process_raw_scores()` applies calibration automatically if `calibration.json` exists

```bash
# Fit calibration for a filter
PYTHONPATH=. python scripts/calibration/fit_calibration.py \
  --filter filters/uplifting/v6 \
  --data-dir datasets/training/uplifting_v6 \
  --test-data datasets/training/uplifting_v6/test.jsonl
```

Typical improvement: 3-7% MAE reduction.

---

## Deployment

### HuggingFace Hub (Production)

All 4 production filters are deployed as private repos on HuggingFace Hub:

| Filter | Hub Repo | MAE |
|--------|----------|-----|
| uplifting v6 | `jeergrvgreg/uplifting-filter-v6` | 0.673 |
| sustainability_technology v3 | `jeergrvgreg/sustainability-technology-filter-v3` | 0.724 |
| investment-risk v6 | `jeergrvgreg/investment-risk-filter-v6` | 0.497 |
| cultural-discovery v4 | `jeergrvgreg/cultural-discovery-filter-v4` | 0.740 |

### Three Inference Paths

1. **Local** (`inference.py`): Loads adapter from `model/` directory. Used for development and batch processing.
2. **Hub** (`inference_hub.py`): Loads adapter from HuggingFace Hub via `PeftModel.from_pretrained()`. Used by NexusMind production.
3. **Hybrid** (`inference_hybrid.py`): Stage 1 probe + Stage 2 Hub/local model. Used when throughput matters.

### Adapter Format (ADR-007)

Adapter files must be kept in OLD PEFT format (`.lora_A.weight`, `score.weight`) for Hub compatibility. Local inference remaps keys at load time. Do NOT run `resave_adapter.py` before upload.

### Performance

| Component | Latency | Cost |
|-----------|---------|------|
| Prefilter | <5ms | $0 |
| Embedding probe (Stage 1) | 1-2ms | $0 |
| Gemma-3-1B model (Stage 2) | 30-40ms | $0 |
| **Full pipeline** | **35-50ms** | **$0** |

vs. Oracle: 2-5 seconds, $0.00015/article

---

## Key Documents

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](../CLAUDE.md) | AI context and project overview |
| [TODO.md](TODO.md) | Active tasks and filter status |
| [ROADMAP.md](ROADMAP.md) | Now/Next/Later priorities |
| [ADR index](adr/README.md) | Architecture decision records (001-008) |
| [Filter creation workflow](guides/filter-creation-workflow.md) | Step-by-step for new filters |
| [Deployment gotchas](adr/007-adapter-format-and-deployment.md) | Adapter format and Hub upload |

---

*Last Updated: 2026-02-22*
