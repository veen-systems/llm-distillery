# Model Evaluation Agent Template v1.0

**Purpose:** Systematically validate trained student model quality and determine production readiness.

**When to use:** After training completes, before deploying model to production.

**Expected duration:** 15-30 minutes (includes test set inference + analysis)

---

## Agent Task Description

You are evaluating a trained filter model to determine if it's ready for production deployment. Use the evaluation criteria below to generate a comprehensive assessment.

**Input artifacts:**
- Trained model: `filters/{filter_name}/v1/model/`
- Training metadata: `filters/{filter_name}/v1/training_metadata.json`
- Training history: `filters/{filter_name}/v1/training_history.json`
- Test dataset: `datasets/training/{filter_name}/test.jsonl`

**Your responsibilities:**
1. Run test set evaluation using `sandbox/analysis_scripts/evaluate_model.py` <!-- placeholder -->
2. Analyze training progression (epochs, convergence)
3. Check for overfitting (train vs val vs test gaps)
4. Identify problematic dimensions (high MAE)
5. Generate production readiness report
6. Recommend: DEPLOY / RETRAIN / INVESTIGATE

---

## Evaluation Criteria

### CRITICAL (Must Pass)

#### 1. Test Set Performance
**Metric:** Mean Absolute Error (MAE) on test set

**Target:** MAE < 1.0 (on 0-10 scale)

**Check:**
```bash
python sandbox/analysis_scripts/evaluate_model.py \
    --model-dir filters/{filter_name}/v1/model \
    --test-data datasets/training/{filter_name}/test.jsonl
```

**Pass criteria:**
- ✅ Overall test MAE < 1.0
- ✅ At least 5/8 dimensions have MAE < 1.1
- ❌ FAIL if test MAE > 1.2 or any dimension MAE > 2.0

**Reasoning:** MAE < 1.0 means model can reliably distinguish adjacent score levels (e.g., 6 vs 7). Errors >1.0 introduce too much noise for filtering.

#### 2. Generalization (No Overfitting)
**Metric:** Train/Validation/Test MAE gap

**Check training history:**
```python
# Read training_history.json
final_epoch = history[-1]
train_mae = final_epoch['train']['mae']
val_mae = final_epoch['val']['mae']
# Compare to test MAE from evaluation
```

**Pass criteria:**
- ✅ Val MAE ≈ Test MAE (within 0.05)
- ✅ Train MAE ≈ Val MAE (gap < 0.15)
- ⚠️ REVIEW if val/test gap > 0.1 (possible data leakage or distribution shift)
- ❌ FAIL if val MAE < test MAE by >0.2 (severe overfitting)

**Example:**
```
Train MAE: 0.92
Val MAE:   0.99
Test MAE:  0.98  ✅ Good generalization
```

#### 3. Training Convergence
**Metric:** MAE improvement trend across epochs

**Check:**
```python
# Extract val MAE per epoch
epoch_maes = [epoch['val']['mae'] for epoch in history]
# Check if improving or plateaued
```

**Pass criteria:**
- ✅ Val MAE decreased in at least 2/3 of epochs
- ✅ Final epoch shows improvement OR plateau (not degrading)
- ⚠️ REVIEW if oscillating wildly (±0.2 between epochs)
- ❌ FAIL if final epoch MAE > first epoch MAE (no learning)

**Example (Good):**
```
Epoch 1: 1.44
Epoch 2: 1.06 ✅ (26% improvement)
Epoch 3: 0.99 ✅ (6% improvement)
```

### QUALITY (Report but Don't Block)

#### 4. Per-Dimension Analysis
**Metric:** Identify dimensions with high error rates

**Check test evaluation output:**
```python
per_dim_mae = test_results['per_dimension_mae']
# Sort by MAE, identify worst performers
```

**Report:**
- List dimensions with MAE > 1.1 (challenging)
- List dimensions with MAE < 0.9 (excellent)
- Identify if certain dimension types struggle (e.g., subjective vs objective)

**Example findings:**
```
Excellent (MAE < 0.9):
  - cost_trajectory: 0.83
  - market_penetration: 0.85

Challenging (MAE > 1.1):
  - technology_readiness: 1.13
  - scale_of_deployment: 1.11
```

**Interpretation:**
- Objective/quantifiable dimensions (cost, market %) perform best
- Subjective/contextual dimensions (readiness, maturity) have higher error
- This is expected and acceptable if overall MAE < 1.0

#### 5. Model Efficiency
**Metric:** Model size and inference speed

**Check:**
```python
# From training_metadata.json
num_parameters = metadata['num_parameters']
num_trainable = metadata['num_trainable_parameters']
model_name = metadata['model_name']  # e.g., Qwen/Qwen2.5-1.5B

# Estimate inference time (if not measured)
# 1.5B model: ~200ms/article
# 7B model: ~1000ms/article
```

**Report:**
- Model size (1.5B, 7B, etc.)
- Trainable parameters (LoRA adapter size)
- Expected inference time
- Suitability for production scale

**Example:**
```
Model: Qwen 2.5-1.5B
Trainable params: 18M (LoRA)
Est. inference: 200ms/article
Scale test: 1000 articles/day × 15 filters = 6 min/day ✅
```

### INFORMATIONAL (Context Only)

#### 6. Training Configuration Review
**Check metadata for training parameters:**
```python
epochs = metadata['epochs']
batch_size = metadata['batch_size']
learning_rate = metadata['learning_rate']
train_examples = metadata['train_examples']
val_examples = metadata['val_examples']
```

**Report:**
- Total training examples
- Train/val split ratio
- Hyperparameters used
- Training duration estimate

#### 7. Comparison to Baseline
**If previous model exists** (in archive/), compare:

```python
# Old model (if available)
old_mae = 1.31  # from archive/models/{filter}/v1_old/training_metadata.json

# New model
new_mae = 0.98  # from current evaluation

improvement = (old_mae - new_mae) / old_mae * 100
# Report: "25% improvement over previous model"
```

---

## Decision Matrix

### ✅ DEPLOY (Production Ready)

**Criteria:**
- Test MAE < 1.0 ✅
- No overfitting (val ≈ test) ✅
- Converged training (improvement visible) ✅
- At least 5/8 dimensions MAE < 1.1 ✅

**Recommendation:**
```
DECISION: DEPLOY TO PRODUCTION

Test Performance: MAE 0.978 ✅
Generalization: Excellent (val 0.984, test 0.978)
Convergence: Good (improving each epoch)
Per-Dimension: 5/8 dimensions < 1.0

This model is ready for production deployment.

Next steps:
1. Archive model to production directory
2. Deploy to inference pipeline
3. Monitor real-world performance
4. Collect edge cases for future training iterations
```

### ⚠️ REVIEW (Borderline - Discuss Trade-offs)

**Criteria:**
- Test MAE 1.0-1.2 (acceptable but not ideal)
- OR 3+ dimensions have MAE > 1.2
- OR some overfitting detected (val-test gap 0.1-0.2)

**Recommendation:**
```
DECISION: REVIEW - Discuss Trade-offs

Test Performance: MAE 1.15 ⚠️
Issue: 3 dimensions have MAE > 1.2
- technology_readiness: 1.35
- deployment_maturity: 1.28
- scale_of_deployment: 1.22

Options:
1. Deploy as-is (acceptable for filtering, not for fine-grained ranking)
2. Retrain with more epochs (may improve to ~1.0)
3. Switch to 7B model (likely 15% improvement)
4. Collect more training data for challenging dimensions

Recommend: Deploy for filtering use case, consider retraining if precision critical.
```

### ❌ FAIL (Retrain Required)

**Criteria:**
- Test MAE > 1.2 (unacceptable error)
- OR severe overfitting (val-test gap > 0.2)
- OR training didn't converge (final MAE ≈ initial MAE)
- OR any dimension MAE > 2.0

**Recommendation:**
```
DECISION: RETRAIN REQUIRED

Test Performance: MAE 1.45 ❌
Issue: Model did not learn effectively

Root causes to investigate:
1. Data quality - Check for label noise or inconsistencies
2. Insufficient training - Try more epochs or larger model
3. Learning rate - May need adjustment (too high or too low)
4. Data quantity - May need more labeled examples

Recommended actions:
1. Audit training data quality (run dimensional regression QA agent)
2. Retrain with adjusted hyperparameters:
   - Increase epochs from 3 to 7
   - OR switch from 1.5B to 7B model
3. If still failing, collect more ground truth data
```

---

## Report Template

Use this structure for your evaluation report:

```markdown
# Model Evaluation Report: {filter_name}

**Date:** {date}
**Model:** {model_name} (e.g., Qwen 2.5-1.5B)
**Evaluator:** Model Evaluation Agent v1.0

---

## Executive Summary

**Decision:** ✅ DEPLOY / ⚠️ REVIEW / ❌ FAIL

**Test MAE:** {test_mae}
**Overall Assessment:** [One sentence summary]

---

## Detailed Results

### 1. Test Set Performance

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Overall MAE | {mae} | < 1.0 | ✅/⚠️/❌ |
| Overall RMSE | {rmse} | < 1.5 | ✅/⚠️/❌ |
| Test examples | {n} | N/A | ℹ️ |

### 2. Per-Dimension Performance

| Dimension | Test MAE | Status |
|-----------|----------|--------|
| dimension_1 | 0.85 | ✅ Excellent |
| dimension_2 | 1.02 | ✅ Good |
| dimension_3 | 1.15 | ⚠️ Acceptable |
| ... | ... | ... |

**Best performers:** [List dimensions with MAE < 0.9]
**Challenging dimensions:** [List dimensions with MAE > 1.1]

### 3. Generalization Check

| Dataset | MAE | RMSE |
|---------|-----|------|
| Training | {train_mae} | {train_rmse} |
| Validation | {val_mae} | {val_rmse} |
| Test | {test_mae} | {test_rmse} |

**Train-Val gap:** {gap} (✅ < 0.15 / ⚠️ 0.15-0.25 / ❌ > 0.25)
**Val-Test gap:** {gap} (✅ < 0.05 / ⚠️ 0.05-0.15 / ❌ > 0.15)

**Assessment:** [No overfitting / Minor overfitting / Severe overfitting]

### 4. Training Convergence

**Epoch progression:**
```
Epoch 1: MAE {e1_mae}
Epoch 2: MAE {e2_mae} ({improvement}% improvement)
Epoch 3: MAE {e3_mae} ({improvement}% improvement)
```

**Assessment:** [Converged / Still improving / Plateaued / Degrading]

### 5. Model Efficiency

- **Model size:** {model_name}
- **Parameters:** {num_params:,} total, {trainable_params:,} trainable
- **Est. inference time:** {inference_time}ms/article
- **Production scale:** {daily_volume} articles/day × {num_filters} filters = {total_time} minutes/day

---

## Comparison to Baseline

| Metric | Old Model | New Model | Improvement |
|--------|-----------|-----------|-------------|
| Test MAE | {old_mae} | {new_mae} | {improvement}% |
| Training data | {old_samples} | {new_samples} | +{diff} samples |
| Model size | {old_size} | {new_size} | {change} |

---

## Recommendations

### Immediate Actions

1. [✅ DEPLOY / ⚠️ REVIEW WITH TEAM / ❌ RETRAIN]
2. [Specific next steps]

### Future Improvements

- [Optional suggestions for next iteration]
- [Data collection priorities]
- [Hyperparameter tuning ideas]

---

## Appendix

**Files evaluated:**
- Model: `filters/{filter_name}/v1/model/`
- Metadata: `filters/{filter_name}/v1/training_metadata.json`
- History: `filters/{filter_name}/v1/training_history.json`
- Test results: `filters/{filter_name}/v1/test_evaluation.json`

**Evaluation command:**
```bash
python sandbox/analysis_scripts/evaluate_model.py \
    --model-dir filters/{filter_name}/v1/model \
    --test-data datasets/training/{filter_name}/test.jsonl
```
```

---

## Example Usage

### Invocation

```
Task: "Evaluate the trained sustainability_tech_deployment model using the
Model Evaluation Agent criteria from docs/agents/templates/model-evaluation-agent.md.

Model location: filters/sustainability_tech_deployment/v1
Test data: datasets/training/sustainability_tech_deployment/test.jsonl

Run test evaluation and generate production readiness report."
```

### Expected Agent Workflow

1. ✅ Read training metadata and history
2. ✅ Run test evaluation script
3. ✅ Analyze results against criteria
4. ✅ Generate structured report
5. ✅ Make DEPLOY/REVIEW/FAIL recommendation
6. ✅ Save report to `filters/{filter_name}/v1/model_evaluation.md`

---

## Success Criteria for Agent

**Agent completes successfully if:**
- ✅ Test evaluation runs without errors
- ✅ All CRITICAL checks performed
- ✅ Clear DEPLOY/REVIEW/FAIL decision made
- ✅ Report generated with specific numbers (not placeholders)
- ✅ Actionable recommendations provided
- ✅ Report saved to filter directory: `filters/{filter_name}/v1/model_evaluation.md`

**Agent quality markers:**
- Uses actual metrics from evaluation (not guessed)
- Identifies specific problematic dimensions
- Provides context (why certain dimensions struggle)
- Recommends concrete next steps
- Saves report to filter directory for portability

---

## Version History

### v1.0 (2025-11-13)
- Initial template
- Based on sustainability_tech_deployment training experience
- Criteria: MAE < 1.0, no overfitting, convergence
- Decision matrix: DEPLOY / REVIEW / FAIL
