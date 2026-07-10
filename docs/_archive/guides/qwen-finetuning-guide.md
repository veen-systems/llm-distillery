> **DEPRECATED (Feb 2026):** Training now uses Gemma-3-1B with `filters/common/model_loading.py`. See `docs/guides/filter-creation-workflow.md` for the current workflow.

# Qwen 2.5 Fine-tuning Guide for Filter Training

**Version:** 2.0
**Last Updated:** 2025-11-10
**Hardware:** GPU with 16GB+ VRAM
**Use Case:** Training local 7B models to replicate oracle LLM behavior via knowledge distillation

---

## Table of Contents

1. [Overview](#overview)
2. [Training Approach](#training-approach)
3. [Hardware Requirements](#hardware-requirements)
4. [Environment Setup](#environment-setup)
5. [Training Process](#training-process)
6. [Model Evaluation](#model-evaluation)
7. [Troubleshooting](#troubleshooting)
8. [Performance Benchmarks](#performance-benchmarks)

---

## Overview

### Project Goals

This guide covers **knowledge distillation** - training a local 7B model (Qwen2.5-7B-Instruct) to replicate expensive cloud oracle behavior (Gemini Flash).

**Pipeline:**
1. Oracle labels articles with 8-dimensional scores ($0.001/article)
2. Prepare training data with stratified splits + oversampling
3. Train Qwen2.5-7B-Instruct on regression task (predict score arrays)
4. Achieve 90%+ accuracy at $0/article inference cost

**Key Principle:** This is **regression training**, not text generation. The model learns to predict 8-dimensional score arrays directly.

### Why Regression (Not Text Generation)?

**❌ Text Generation Approach (Deprecated):**
- Model generates JSON text: `{"agency": 8, "progress": 7, ...}`
- Requires parsing, error-prone
- Slower inference
- More complex training

**✅ Regression Approach (Current):**
- Model outputs 8 floating-point scores directly
- No parsing needed
- Faster inference
- Simpler training and evaluation
- See ADR: `docs/decisions/2025-11-09-model-output-format.md`

---

## Hardware Requirements

### Minimum Requirements

**For Training:**
- GPU: 16GB VRAM minimum (RTX 4080, RTX 4090, A100, etc.)
- RAM: 32GB system RAM
- Storage: 100GB free space for models + datasets
- Training time: 2-4 hours for 4K examples (3 epochs)

**For Inference:**
- GPU: 8GB VRAM (for local model)
- RAM: 16GB system RAM
- Inference speed: <50ms per article

### VRAM Usage During Training

| Configuration | VRAM Usage | Training Speed | Notes |
|---------------|------------|----------------|-------|
| Batch size 8 | 10-12GB | Fastest | Recommended |
| Batch size 4 | 6-8GB | Slower | If OOM errors |
| Batch size 2 | 4-6GB | Slowest | Minimal VRAM |

**Recommended:** Batch size 8 for best training speed on 16GB GPU

---

## Environment Setup

**Prerequisites:**
- Python 3.10+
- CUDA-compatible GPU with 16GB+ VRAM
- Git

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/llm-distillery.git
cd llm-distillery
```

### Step 2: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Verify CUDA is available
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
# Expected: CUDA available: True
```

**Key dependencies** (from requirements.txt):
- `torch` - PyTorch with CUDA support
- `transformers` - Hugging Face transformers
- `datasets` - Dataset loading and processing
- `peft` - Parameter-efficient fine-tuning (LoRA)
- `accelerate` - Distributed training utilities

### Step 3: Verify GPU Access

```bash
# Check GPU visibility
nvidia-smi

# Expected output should show your GPU
# Example: NVIDIA GeForce RTX 4080 16GB
```

**That's it!** The model will download automatically during first training run.

---

## Training Approach

### Data Preparation Overview

Before training, you need prepared training data:

1. **Oracle Labeling** - Generate ground truth with Gemini Flash (~$4 for 4K articles)
2. **Dataset Preparation** - Create stratified train/val/test splits with oversampling
3. **Training** - Fine-tune Qwen2.5-7B-Instruct on score prediction task

**See:** [`getting-started.md`](getting-started.md) for complete pipeline walkthrough

### Data Format

**Oracle labels** (from `batch_scorer`):
```json
{
  "id": "article-123",
  "title": "...",
  "content": "...",
  "analysis": {
    "deployment_maturity": 8,
    "technology_performance": 7,
    "cost_trajectory": 6,
    ...  // 8 dimensions total
  }
}
```

**Training data** (from `prepare_training_data_*.py`):
```json
{
  "id": "article-123",
  "text": "Full article text (~800 words)...",
  "dimension_scores": [8, 7, 6, 8, 5, 7, 6, 8],
  "overall_score": 6.9,
  "tier": "early_commercial"
}
```

**Key transformation:**
- Truncate content to ~800 words (oracle-student consistency)
- Extract 8-dimensional score array from analysis
- Calculate overall score using weighted sum
- Assign tier based on thresholds

### Data Preparation Scripts

**Generate oracle labels:**
```bash
python -m ground_truth.batch_scorer \
    --filter filters/sustainability_tech_deployment/v1 \
    --source "datasets/raw/*.jsonl" \
    --llm gemini-flash \
    --target-count 4000 \
    --random-sample \
    --output-dir ground_truth/labeled/tech_deployment
```

**Prepare training data:**
```bash
python scripts/prepare_training_data_tech_deployment.py \
    --input datasets/scored/sustainability_tech_deployment/all_labels.jsonl \
    --output-dir datasets/training/sustainability_tech_deployment \
    --train-ratio 0.8 \
    --val-ratio 0.1 \
    --test-ratio 0.1 \
    --oversample-ratio 0.2 \
    --seed 42
```

**Output:**
- `datasets/training/{filter}/train.jsonl` - Training set (with oversampling)
- `datasets/training/{filter}/val.jsonl` - Validation set (natural distribution)
- `datasets/training/{filter}/test.jsonl` - Test set (natural distribution)

---

## Training Process

### Using training/train.py

**Basic command:**
```bash
python -m training.train \
    --filter filters/sustainability_tech_deployment/v1 \
    --data-dir datasets/training/sustainability_tech_deployment \
    --epochs 3 \
    --batch-size 8 \
    --learning-rate 2e-5
```

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--filter` | Required | Path to filter package (config.yaml) |
| `--data-dir` | Required | Directory with train/val/test JSONL files |
| `--epochs` | 3 | Number of training epochs |
| `--batch-size` | 8 | Batch size (reduce if OOM) |
| `--learning-rate` | 2e-5 | Learning rate for optimizer |
| `--model-name` | Qwen/Qwen2.5-7B-Instruct | Base model |
| `--output-dir` | models/{filter_name} | Where to save checkpoints |

### Training on GPU Machine (with tmux)

**Recommended workflow:**
```bash
# Start tmux session
tmux new -s training

# Run training
python -m training.train \
    --filter filters/sustainability_tech_deployment/v1 \
    --data-dir datasets/training/sustainability_tech_deployment \
    --epochs 3 \
    --batch-size 8 \
    --learning-rate 2e-5

# Detach from tmux: Ctrl+B, then D
# Reattach later: tmux attach -t training
```

**See:** [`tmux-usage.md`](tmux-usage.md) for tmux commands

### Expected Training Output

```
Loading training data from datasets/training/sustainability_tech_deployment...
  Train: 4,328 examples
  Val: 413 examples
  Test: 417 examples

Loading model: Qwen/Qwen2.5-7B-Instruct...
Model loaded successfully!

Configuring LoRA adapters...
LoRA configured with rank 16

Starting training (3 epochs)...

Epoch 1/3:
  [████████████████████████████] 541/541 - loss: 1.234 - val_loss: 0.987
  Checkpoint saved: models/sustainability_tech_deployment/checkpoint-epoch-1

Epoch 2/3:
  [████████████████████████████] 541/541 - loss: 0.876 - val_loss: 0.765
  Checkpoint saved: models/sustainability_tech_deployment/checkpoint-epoch-2

Epoch 3/3:
  [████████████████████████████] 541/541 - loss: 0.654 - val_loss: 0.621
  Checkpoint saved: models/sustainability_tech_deployment/checkpoint-epoch-3

Training complete!
Best model saved: models/sustainability_tech_deployment/checkpoint-best
```

### Training Time Estimates

| Dataset Size | Batch Size | Epochs | GPU | Time |
|--------------|------------|--------|-----|------|
| 4,000 examples | 8 | 3 | RTX 4080 | 2-3 hours |
| 4,000 examples | 4 | 3 | RTX 4080 | 3-4 hours |
| 4,000 examples | 2 | 3 | RTX 4080 | 4-6 hours |
| 4,000 examples | 8 | 3 | RTX 4090 | 1.5-2 hours |

---

## Model Evaluation

### Using training/evaluate.py

**Run evaluation on validation set:**
```bash
python -m training.evaluate \
    --model-checkpoint models/sustainability_tech_deployment/checkpoint-best \
    --data-dir datasets/training/sustainability_tech_deployment \
    --output reports/model_evaluation.md
```

### Success Criteria (from ADRs)

**Per-dimension metrics:**
- MAE (Mean Absolute Error) < 1.5 per dimension
- Strong correlation with oracle labels

**Tier classification:**
- Accuracy ≥ 70% per tier
- Deployed tier recall ≥ 60% (critical minority class)

**Overall:**
- Model generalizes to validation set (natural distribution)
- No catastrophic overfitting

### Example Evaluation Output

```
Model Evaluation Report
=======================

Per-Dimension MAE:
  deployment_maturity:      0.87
  technology_performance:   0.92
  cost_trajectory:          1.12
  market_signals:           0.78
  scalability:              1.03
  integration_readiness:    0.95
  risk_factors:             0.88
  impact_potential:         0.81

Overall MAE: 0.92  ✅ (target: <1.5)

Tier Classification:
                   Precision  Recall  F1-Score
  Vaporware           0.91     0.94     0.93
  Pilot               0.78     0.72     0.75
  Early Commercial    0.82     0.79     0.80
  Deployed            0.76     0.68     0.72  ✅ (recall target: ≥60%)

Overall Accuracy: 85.2%  ✅

Conclusion: Model meets success criteria, ready for deployment.
```

### If Metrics Don't Meet Targets

**Options:**
1. **More epochs** - Try 5 epochs instead of 3
2. **Adjust oversampling** - Increase minority class ratio
3. **Class weighting** - Apply weights to loss function
4. **More training data** - Generate additional oracle labels
5. **Hyperparameter tuning** - Try different learning rates

---

## Post-Training: Creating Postfilter

Once model is trained and evaluated, create postfilter for production inference:

**Postfilter structure:**
```
filters/sustainability_tech_deployment/v1/
├── config.yaml
├── prompt-compressed.md
├── prefilter.py
└── postfilter.py  ← Create this
```

**Postfilter responsibilities:**
- Load trained model from checkpoint
- Run inference on new articles
- Predict 8-dimensional scores
- Calculate overall score using config weights
- Assign tier based on thresholds

**See:** [`docs/CURRENT_TASK.md`](../CURRENT_TASK.md) Phase 4 for postfilter implementation plan

---

## Troubleshooting

### Common Issues

#### CUDA Out of Memory

**Symptoms:**
```
RuntimeError: CUDA out of memory
```

**Solutions:**
```bash
# Reduce batch size
--batch-size 4  # Instead of 8

# Or batch size 2 for minimal VRAM
--batch-size 2
```

#### Model Not Learning (Loss Not Decreasing)

**Symptoms:**
- Validation loss stays high
- No improvement across epochs

**Solutions:**
```bash
# 1. Increase learning rate
--learning-rate 5e-5  # Instead of 2e-5

# 2. Train longer
--epochs 5  # Instead of 3

# 3. Check data quality
# - Verify labels are correct
# - Check for data format issues
```

#### Import Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'transformers'
```

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

#### Slow Training Speed

**Solutions:**
```bash
# Increase batch size (if VRAM allows)
--batch-size 16

# Reduce sequence length in data preparation
# (Edit prepare_training_data_*.py, reduce word limit)
```

---

## Performance Benchmarks

### Training Performance (RTX 4080 16GB)

| Dataset Size | Batch Size | Epochs | Time per Epoch | Total Time |
|--------------|------------|--------|----------------|------------|
| 4,000 examples | 8 | 3 | 40-50 min | 2-2.5 hours |
| 4,000 examples | 4 | 3 | 60-80 min | 3-4 hours |
| 4,000 examples | 2 | 3 | 100-120 min | 5-6 hours |

### Expected Model Quality

| Metric | Target | Good | Excellent |
|--------|--------|------|-----------|
| Per-dimension MAE | <1.5 | <1.0 | <0.5 |
| Tier accuracy | >70% | >80% | >90% |
| Deployed recall | >60% | >70% | >80% |

### VRAM Usage

| Configuration | Training VRAM | Inference VRAM |
|---------------|---------------|----------------|
| Batch size 8 | 10-12 GB | 8 GB |
| Batch size 4 | 6-8 GB | 8 GB |
| Batch size 2 | 4-6 GB | 8 GB |

---

## Next Steps

After training completes:

1. **Evaluate model** - Run evaluation script on validation set
2. **Analyze metrics** - Check if success criteria are met
3. **Create postfilter** - Implement production inference module
4. **Deploy on corpus** - Run inference on full 99K article corpus
5. **Apply to remaining filters** - Repeat process for 5 other filters

**See:**
- [`getting-started.md`](getting-started.md) - Complete pipeline walkthrough
- [`docs/CURRENT_TASK.md`](../CURRENT_TASK.md) - Current phase and next steps
- [`docs/decisions/`](../decisions/) - Architecture decision records

---

**Document Version:** 2.0
**Last Updated:** 2025-11-10
**Previous Version:** 1.0 (deprecated - Unsloth/text generation approach)
