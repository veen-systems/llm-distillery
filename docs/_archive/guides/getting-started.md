> **DEPRECATED (Feb 2026):** This guide references Qwen2.5-7B and early-stage workflows that no longer apply. See `docs/guides/filter-creation-workflow.md` for the current workflow.

# Getting Started with LLM Distillery

**Last Updated:** 2025-11-10
**Purpose:** Train local 7B models to replicate expensive cloud LLM behavior

---

## 🎯 What You'll Build

Transform expensive cloud LLM evaluations into fast, cheap local models through **knowledge distillation**:

- **Oracle (Gemini Flash)**: $0.001/article, slow, requires API
- **Student (Qwen2.5-7B-Instruct)**: $0/article, fast (<50ms), runs locally
- **Process**: Oracle labels 4K articles → Train student model → 90%+ accuracy

**Example ROI:**
- Oracle labeling: 4,000 articles × $0.001 = **$4 one-time cost**
- Inference on 99K corpus: **$0** (vs $99 with oracle)
- Annual savings: ~$300-500 per filter

---

## 📋 Prerequisites

### Required
1. **Python 3.10+**
2. **GPU with 16GB+ VRAM** (for training)
   - NVIDIA RTX 4080/4090, A100, or similar
   - Training takes 2-4 hours for 4K examples
3. **API Keys**:
   - Google Gemini API key (for oracle labeling)
   - Optional: Groq API (alternative oracle)

### Recommended
- **Tmux** (for long-running GPU jobs)
- **Remote GPU server** (if training remotely)
- See: [`remote-sync-guide.md`](remote-sync-guide.md) and [`tmux-usage.md`](tmux-usage.md)

---

## 🚀 Complete Pipeline (5 Steps)

### Step 1: Set Up Environment

```bash
# Clone repository
cd /path/to/llm-distillery

# Install dependencies
pip install -r requirements.txt

# Configure API key
export GEMINI_API_KEY="your-api-key-here"
# Or add to config/credentials/secrets.ini
```

---

### Step 2: Calibrate Oracle (Optional but Recommended)

**Purpose**: Choose best oracle LLM and test prefilter

```bash
# Compare Gemini Flash vs Pro on sample
python -m ground_truth.calibrate_oracle \
    --filter filters/sustainability_tech_deployment/v1 \
    --source "datasets/raw/*.jsonl" \
    --sample-size 100 \
    --models gemini-flash,gemini-pro \
    --output reports/oracle_calibration.md
```

**Expected output**: Comparison report showing which model performs better

**Typical result**: Gemini Flash wins (better discrimination, 10x cheaper)

**Time**: 5-10 minutes
**Cost**: ~$0.10

See: [`ground-truth-generation.md`](ground-truth-generation.md) for details

---

### Step 3: Generate Oracle Labels

**Purpose**: Create ground truth training data

```bash
# Label 2,000-4,000 articles with oracle LLM
python -m ground_truth.batch_scorer \
    --filter filters/sustainability_tech_deployment/v1 \
    --source "datasets/raw/*.jsonl" \
    --llm gemini-flash \
    --target-count 4000 \
    --random-sample \
    --output-dir ground_truth/labeled/tech_deployment
```

**Expected output**:
- JSONL file with oracle-labeled articles
- Each article scored across filter dimensions
- Success rate: >96% (with retries)

**Time**: 2-4 hours (rate limited)
**Cost**: ~$4 (4,000 × $0.001)

**Tip**: Run in tmux session on server (job survives disconnection)

---

### Step 4: Prepare Training Data

**Purpose**: Convert oracle labels to training format with stratification + oversampling

```bash
# Create train/val/test splits (80/10/10)
# Applies minority class oversampling to training set
python scripts/prepare_training_data_tech_deployment.py \
    --input datasets/scored/sustainability_tech_deployment/all_labels.jsonl \
    --output-dir datasets/training/sustainability_tech_deployment \
    --train-ratio 0.8 \
    --val-ratio 0.1 \
    --test-ratio 0.1 \
    --oversample-ratio 0.2 \
    --seed 42
```

**Expected output**:
- `datasets/training/sustainability_tech_deployment/train.jsonl` (with oversampling)
- `datasets/training/sustainability_tech_deployment/val.jsonl` (natural distribution)
- `datasets/training/sustainability_tech_deployment/test.jsonl` (natural distribution)

**Time**: <1 minute

See: [`docs/decisions/2025-11-09-class-imbalance-strategy.md`](../decisions/2025-11-09-class-imbalance-strategy.md)

---

### Step 5: Train Model

**Purpose**: Fine-tune Qwen2.5-7B-Instruct on prepared data

**On GPU machine** (in tmux session):

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
```

**Expected output**:
- Model checkpoints saved during training
- Training metrics logged (loss, accuracy)
- Best checkpoint saved at end

**Time**: 2-4 hours (depends on GPU)
**VRAM**: ~8-12GB
**Cost**: $0 (local compute)

**Tip**: Monitor with `tmux attach -t training` to check progress

See: [`tmux-usage.md`](tmux-usage.md) for tmux commands

---

## 📊 After Training: Evaluation & Deployment

### Evaluate Model Performance

```bash
# Run evaluation on validation set
python -m training.evaluate \
    --model-checkpoint models/sustainability_tech_deployment/checkpoint-best \
    --data-dir datasets/training/sustainability_tech_deployment \
    --output reports/model_evaluation.md
```

**Success criteria** (from ADR):
- Per-dimension MAE < 1.5
- Tier classification accuracy ≥ 70% per tier
- Deployed tier recall ≥ 60%

See: [`docs/decisions/2025-11-09-model-output-format.md`](../decisions/2025-11-09-model-output-format.md)

### Create Postfilter for Inference

```bash
# Create postfilter module for production inference
# (Coming soon - see docs/CURRENT_TASK.md for roadmap)
```

---

## 🏗️ Project Structure

```
llm-distillery/
├── filters/                          # Filter definitions
│   └── sustainability_tech_deployment/v1/
│       ├── config.yaml              # Dimension weights, thresholds
│       ├── prompt-compressed.md     # Oracle prompt
│       └── README.md                # Filter documentation
│
├── ground_truth/                    # Oracle labeling tools
│   ├── batch_scorer.py            # Main labeling script
│   └── calibrate_oracle.py         # Oracle comparison tool
│
├── datasets/
│   ├── raw/                        # Unlabeled articles (JSONL)
│   ├── labeled/                    # Oracle-labeled data
│   └── training/                   # Train/val/test splits
│
├── training/
│   └── train.py                    # Model training script
│
└── docs/
    ├── guides/                     # How-to guides (you are here!)
    └── decisions/                  # Architecture Decision Records (ADRs)
```

---

## 🔄 Typical Workflow

### First Filter (Sustainability Tech Deployment)
1. ✅ Create filter package → `filters/sustainability_tech_deployment/v1/`
2. ✅ Calibrate oracle → Gemini Flash selected
3. ✅ Generate 4,146 oracle labels → `datasets/scored/`
4. ✅ Prepare training data → `datasets/training/` (4,328/413/417)
5. 🔄 **Train model** (in progress on GPU)
6. ⏭️ Evaluate model
7. ⏭️ Create postfilter for inference
8. ⏭️ Deploy on full corpus (99K articles)

### Subsequent Filters (5 remaining)
- Apply same workflow to:
  - Economic Viability
  - Policy Effectiveness
  - Nature Recovery
  - Movement Growth
  - AI-Augmented Practice

**Efficiency gains**:
- Reuse calibration methodology
- Reuse training scripts
- Parallel oracle labeling for multiple filters

---

## 💡 Key Concepts

### Oracle vs Student
- **Oracle**: Expensive cloud LLM (Gemini Flash) that provides ground truth labels
- **Student**: Local 7B model (Qwen2.5-7B-Instruct) trained to replicate oracle
- **Distillation**: Process of transferring oracle knowledge to student

### Filter Dimensions
Each filter scores articles across multiple dimensions (typically 8):
- Example (Tech Deployment): deployment_maturity, technology_performance, cost_trajectory, etc.
- Weighted combination → Overall score → Tier classification

### Training Approach
- **Regression** (not text generation)
- **Output**: 8-dimensional score array (not reasoning text)
- **Loss**: Mean Absolute Error (MAE)
- **Rationale**: Simpler, faster, less error-prone than text generation

See: [`docs/decisions/2025-11-09-model-output-format.md`](../decisions/2025-11-09-model-output-format.md)

### Class Imbalance Handling
- **Problem**: Natural corpus is 81.6% vaporware, only 1.4% deployed
- **Solution**: Stratified splitting + minority class oversampling (training only)
- **Result**: Balanced training set (12.4% deployed) while preserving natural validation set

See: [`docs/decisions/2025-11-09-class-imbalance-strategy.md`](../decisions/2025-11-09-class-imbalance-strategy.md)

---

## 🆘 Troubleshooting

### "ModuleNotFoundError: transformers"
**Solution**: `pip install -r requirements.txt`

### "CUDA out of memory" during training
**Solution**: Reduce `--batch-size` from 8 to 4 or 2

### Oracle labeling timeout errors
**Solution**: Retries are automatic (max 3 attempts). If persistent, check API key and rate limits.

### Low model accuracy (<70%)
**Possible causes**:
1. Not enough training data (need 3K+ examples)
2. Class imbalance too severe (check oversampling ratio)
3. Wrong model architecture (verify Qwen2.5-7B-Instruct)

**Solution**: Review validation metrics, adjust hyperparameters, or generate more labels

---

## 📚 Further Reading

### Essential Guides
- [Ground Truth Generation](ground-truth-generation.md) - Detailed oracle labeling workflow
- [Tmux Usage](tmux-usage.md) - Running long jobs on GPU server
- [Remote Sync](remote-sync-guide.md) - Syncing code/data between machines

### Architecture Decisions (ADRs)
- [Model Selection](../decisions/2025-11-08-local-model-selection.md) - Why Qwen2.5-7B-Instruct
- [Model Output Format](../decisions/2025-11-09-model-output-format.md) - Score arrays only
- [Class Imbalance](../decisions/2025-11-09-class-imbalance-strategy.md) - Stratification + oversampling
- [Content Truncation](../decisions/2025-11-09-content-truncation-strategy.md) - ~800 words

### Project Status
- [PROJECT_OVERVIEW](../PROJECT_OVERVIEW.md) - Current phase and metrics
- [CURRENT_TASK](../CURRENT_TASK.md) - What we're working on now
- [OPEN_QUESTIONS](../OPEN_QUESTIONS.md) - Unresolved decisions

---

## ✅ Next Steps

Once your first filter is trained and evaluated:

1. **Create postfilter** for production inference
2. **Run on full corpus** (99K articles)
3. **Analyze results** vs oracle on sample
4. **Iterate if needed** (more data, hyperparameter tuning)
5. **Apply to 5 remaining filters**

**Ready to start?** Begin with Step 1 (environment setup) above!
