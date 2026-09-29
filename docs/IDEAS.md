# LLM Distillery - Ideas

A parking lot for project ideas worth exploring later.

---

## Architecture & Infrastructure

### Multi-Model Ensemble
**Status:** Idea
**Origin:** Potential accuracy improvement

Could train multiple smaller models and ensemble their predictions. Trade-off: complexity vs marginal accuracy gain.

### Active Learning Loop
**Status:** Implemented (ADR-005)
**Origin:** Training efficiency

Use production model predictions to guide oracle labeling. Implemented for uplifting v6 and sustainability_technology:
- Screen production output by prediction threshold (≥5.0)
- Oracle score candidates
- Merge with training data, retrain

See `docs/adr/005-active-learning-for-filter-improvement.md` for full methodology.

**Results:** MEDIUM-tier enrichment works (31.5% → 34.6%). HIGH-tier needle search ongoing.

### Confidence Calibration
**Status:** Idea
**Origin:** Production reliability

Output calibrated confidence scores alongside dimensional predictions. Useful for flagging uncertain results for human review.

### Separate Filters Repository
**Status:** Backlog
**Origin:** Deployment architecture (Jan 2025)

Extract `filters/` into its own git repository that both llm-distillery and NexusMind depend on.

**Current state:** Manual copy via `scripts/deploy_to_nexusmind.sh`

**Options to explore:**
1. **Git submodule** - NexusMind includes filters repo as submodule
2. **Separate filters repo** - Both projects clone/pull from shared filters repo
3. **Python package** - Publish filters as pip installable packages

**Benefits:**
- Single source of truth for filter code
- No manual copy steps
- Version pinning in NexusMind
- Cleaner separation of concerns (llm-distillery = training, filters = artifacts, NexusMind = deployment)

**Trade-offs:**
- Submodules add complexity
- Separate repo means more repos to manage
- Python packages require packaging infrastructure

**Decision trigger:** When manual deploy script becomes painful or error-prone.

---

## Filter Ideas

See `docs/FUTURE_FILTER_IDEAS.md` for filter-specific ideas (equanimity, etc.)

---

## Tooling & Developer Experience

### Filter Development CLI
**Status:** Idea
**Origin:** DX improvement

```bash
distillery new-filter --name belonging --dimensions 6
distillery score --filter belonging/v1 --articles 1000
distillery train --filter belonging/v1
distillery evaluate --filter belonging/v1
```

### Dashboard for Filter Performance
**Status:** Idea
**Origin:** Monitoring need

Web dashboard showing:
- Per-filter accuracy metrics over time
- Score distributions
- Prefilter false positive/negative rates
- API cost tracking

---

## Research Experiments

### Smaller Base Models
**Status:** Idea
**Origin:** Cost/speed optimization

Test Qwen2.5-0.5B or Phi-2 as base model. Potential for even faster inference on weaker hardware.

### Cross-Filter Transfer Learning
**Status:** Idea
**Origin:** Training efficiency

Train shared encoder across filters, with filter-specific heads. Could reduce training time for new filters.

### Synthetic Training Data
**Status:** Idea
**Origin:** Data augmentation

Use LLM to generate synthetic articles with known scores. Could help with rare edge cases.

### Context Length Extension
**Status:** Completed (Jan 2025)
**Origin:** Discovery that Qwen2.5-1.5B supports 128K tokens but training used only 512

#### Experiment Results

| Context Length | Batch Size | Best Val MAE | vs Baseline | Training Time |
|----------------|------------|--------------|-------------|---------------|
| 512 tokens | 8 | 0.6800 | baseline | ~45 min |
| 1024 tokens | 4 | 0.6520 | **-4.1%** | ~1.5 hrs |
| 2048 tokens | 1 | 0.6267 | **-7.8%** | ~7.5 hrs |

#### Key Findings

1. **Longer context consistently improves MAE** - each doubling of context reduces error
2. **Diminishing returns** - 512→1024 gave 4.1%, 1024→2048 gave only 3.7% more
3. **Training cost scales linearly** - 2048 tokens requires batch_size=1 on 16GB GPU
4. **Inference cost scales quadratically** - attention is O(n²)

#### Article Length Analysis

| Length Category | % of Articles | % of High-Scorers (>=6) |
|-----------------|---------------|-------------------------|
| <= 512 tokens | 77.7% | 43% |
| 512-1024 tokens | 12.0% | 49% |
| 1024-2048 tokens | 8.6% | 7.5% |
| > 2048 tokens | 1.7% | 0% |

**Critical insight:** High-scoring articles tend to be longer. At 512 tokens, 56.9% of high-scorers are truncated.

#### Truncation Impact on High-Scorers

| Context Limit | High-Scorers Truncated |
|---------------|------------------------|
| 512 tokens | 56.9% |
| 1024 tokens | 31.6% |
| 2048 tokens | 7.5% |
| 4096 tokens | 0.0% |

#### CPU Inference Cost (Quantized INT8)

| Context | Time per Article | 10K Articles |
|---------|------------------|--------------|
| 512 | 1.6s | 4.4 hours |
| 1024 | 3.5s | 9.7 hours |
| 2048 | ~7s | ~19 hours |
| 4096 | ~15s | ~42 hours |

#### Conclusion

**Longer context helps quality but is impractical for production.**

- 2048 tokens gives best MAE (0.6267) but 4x slower inference
- For cost-effective deployment, need alternative approaches:
  - **Head+tail extraction** (train with first N + last M tokens)
  - **Chunk-based training** (train on chunks, aggregate at inference)
- Recommended: Train with head+tail extraction at 512 total tokens

#### Models Produced

- `research/embedding_vs_finetuning/models/uplifting_v5_1024tok/` - 1024 token model (MAE 0.652)
- `research/embedding_vs_finetuning/models/uplifting_v5_2048tok/` - 2048 token model (MAE 0.627)
- `research/embedding_vs_finetuning/models/uplifting_v5_head_tail/` - head+tail model (MAE 0.655)

### Head+Tail Extraction Experiment
**Status:** Completed (Jan 2025)
**Origin:** Alternative to full long-context for handling article length

#### Concept
Extract first 256 tokens (intro/summary) + last 256 tokens (conclusion/outcome) = 512 total tokens.
Hypothesis: Most signal is at beginning and end of articles, middle can be skipped.

#### Implementation
See `research/embedding_vs_finetuning/prepare_head_tail_data.py` <!-- placeholder -->

```python
# Extract head + tail with separator
head_text = tokenizer.decode(tokens[:256])
tail_text = tokenizer.decode(tokens[-256:])
return head_text + " [...] " + tail_text
```

#### Results

| Model | Max Length | Best Val MAE | vs Baseline | Inference Speed |
|-------|------------|--------------|-------------|-----------------|
| baseline | 512 | 0.680 | - | 1x |
| 1024tok | 1024 | 0.652 | -4.1% | 2x slower |
| **head_tail** | **512 (256+256)** | **0.655** | **-3.7%** | **1x** |
| 2048tok | 2048 | 0.627 | -7.8% | 4x slower |

#### Key Finding

**Head+tail nearly matches 1024tok performance while keeping baseline inference speed.**

- Head+tail (0.655) vs 1024tok (0.652) = only 0.003 MAE difference
- Head+tail uses same 512 tokens as baseline = same fast inference
- Captures intro (context) + conclusion (outcomes) which contain most signal
- Middle content (detailed explanation) contributes less to scoring

#### Recommendation

**Use head+tail for production.** Best quality-speed tradeoff:
- 3.7% better than baseline (0.655 vs 0.680)
- Same inference speed as baseline
- 4x faster than 2048tok with only 4.3% worse MAE

---

### Ranking Loss for Training (Contrastive Training)
**Status:** Idea
**Origin:** Suggestion that contrastive training improves Qwen performance (Jan 2025)

#### Concept
Add a ranking/contrastive loss component to training alongside MSE loss. Currently we only optimize for absolute accuracy (MSE), but relative ordering may matter more for filtering tasks.

#### Current Training
```python
# MSE only - optimizes absolute accuracy
loss = MSE(predicted_scores, ground_truth_scores)
```

#### Proposed Hybrid Loss
```python
def hybrid_loss(predictions, targets):
    # Absolute accuracy
    mse = F.mse_loss(predictions, targets)

    # Relative ordering - ensure higher targets → higher predictions
    # Sample pairs within batch, apply margin ranking loss
    ranking = margin_ranking_loss(predictions, targets, margin=0.5)

    return mse + lambda * ranking  # lambda ~0.1-0.3
```

#### Why This Might Help
- MSE treats all errors equally (2→3 same as 6→7)
- For filtering, **relative ranking often matters more** than absolute scores
- Could reduce regression-to-mean effect (predictions clustering toward middle)
- Enforces that model learns "A is better than B" not just "A ≈ 5.2"

#### Implementation Options
| Approach | Description | Complexity |
|----------|-------------|------------|
| Pairwise margin | Compare pairs within batch | Low |
| Triplet loss | Anchor + positive + negative | Medium |
| ListMLE | Full listwise ranking | High |

#### When to Try
- After context length experiments (512 → 1024 → 2048) complete
- If longer context doesn't improve MAE
- If regression-to-mean is identified as key weakness

#### Files to Modify
- `training/train.py` - Add ranking loss component
- Need to sample pairs/triplets during training
- May need to adjust batch size for pair sampling

### Hybrid Embedding + Fine-tuned Pipeline
**Status:** Implemented (Feb 2025)
**Origin:** Embedding vs fine-tuning research (Jan 2025)

Implemented as two-stage hybrid inference pipeline. See `docs/adr/006-hybrid-inference-pipeline.md`.

- `filters/common/embedding_stage.py` - Stage 1: embedding + MLP probe
- `filters/common/hybrid_scorer.py` - Two-stage orchestrator
- `filters/uplifting/v5/inference_hybrid.py` <!-- placeholder --> - First filter integration
- `evaluation/calibrate_hybrid_threshold.py` - Threshold calibration

Threshold set at 3.0 (not 2.5 as originally proposed) — gives ~1.0 safety margin below MEDIUM tier (4.0), targeting <2% FN rate. ~68% of articles skip Stage 2.

---

## Template

**Status:** Idea | Exploring | Parked | Rejected
**Origin:** Context of how this idea emerged

### Concept
Brief description.

### Benefits
- Benefit 1
- Benefit 2

### Challenges
- Challenge 1
- Challenge 2

### Notes
Any other context.

---

*Last updated: 2026-02-14*
