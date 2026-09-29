# Plan: Head+Tail Model Deployment

**Created:** 2026-01-26
**Status:** Waiting for GPU availability on llm-distiller

## Background

Head+tail extraction (first 256 + last 256 tokens) achieves MAE 0.655 vs baseline 0.680 - a 3.7% improvement with no inference slowdown. The preprocessing code is implemented and ready.

## Filters to Update

| Filter | Current Version | Action |
|--------|-----------------|--------|
| uplifting | v5 | Retrain with head+tail |
| sustainability_technology | v2 | Retrain with head+tail |

---

# Execution Order

When GPU becomes available:

```
1. Train uplifting v5 (Part A)           ~45 min
2. Train sustainability_tech v2 (Part B)  ~45 min
3. Copy models to local                   ~5 min
4. Update docs, push to HuggingFace       ~15 min
5. Sync NexusMind via git                 ~10 min
6. Test locally                           ~10 min
7. Deploy to Sadalsuud (git pull)         ~5 min
8. Deploy to llm-distiller (git pull)     ~5 min
9. Run belonging data assessment (Part D) ~30 min (while monitoring deploys)
```

---

# Deployment Workflow

## Source of Truth

**llm-distillery** is the single source of truth for all filters.

- Code changes → push to **llm-distillery git**
- Model updates → push to **HuggingFace**
- Deploy = copy to local NexusMind → push NexusMind git → other servers pull

## Flow Diagram

```
                    llm-distillery (source of truth)
                              |
         +--------------------+--------------------+
         |                                         |
         v                                         v
    git push                              HuggingFace push
  (code changes)                          (model updates)
         |
         v
    copy filters to local NexusMind
         |
         v
    git push NexusMind
         |
         +--------------------+--------------------+
         |                    |                    |
         v                    v                    v
    Sadalsuud           llm-distiller          (local)
    git pull             git pull               already
                                                 there
```

_(Old NexusMind-only diagram removed)_

```
┌─────────────┐     git push      ┌─────────────┐
│   Local     │ ───────────────▶  │   GitHub    │
│  (develop)  │                   │   (origin)  │
└─────────────┘                   └─────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │ git pull          │ git pull          │ git pull
                    ▼                   ▼                   ▼
             ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
             │ Sadalsuud   │     │llm-distiller│     │   Local     │
             │ (production)│     │ (production)│     │  (testing)  │
             └─────────────┘     └─────────────┘     └─────────────┘
```

## Standard Deploy Process

```bash
# 1. Push code changes to llm-distillery repo
cd C:\local_dev\llm-distillery
git add -A
git commit -m "Update uplifting v5 with head+tail"
git push origin main

# 2. Push model to HuggingFace (if model updated)
cd filters/uplifting/v5/model
huggingface-cli upload jeergrvgreg/uplifting-filter-v5 .

# 3. Deploy to NexusMind (copies filter + common, commits, pushes, shows server commands)
./scripts/deploy_to_nexusmind.sh uplifting v5 --push

# 4. Pull on deployment servers (commands shown by script above)
ssh user@sadalsuud "cd ~/NexusMind && git pull origin main"
ssh jeroen@llm-distiller "cd ~/NexusMind && git pull origin main"
```

## Version Tracking

```bash
# Compare NexusMind commits across all instances
echo "Local:" && git -C C:\local_dev\NexusMind rev-parse --short HEAD
ssh user@sadalsuud "cd ~/NexusMind && git rev-parse --short HEAD"
ssh jeroen@llm-distiller "cd ~/NexusMind && git rev-parse --short HEAD"
```

---

# PART A: Uplifting Filter v5

## Prerequisites

- [x] Implement `extract_head_tail()` utility in `filters/common/text_preprocessing.py`
- [x] Update `base_scorer.py` to support head+tail at inference time
- [x] Add `preprocessing.head_tail` section to `config.yaml`
- [x] Add `--use-head-tail` flag to `training/train.py`
- [x] Sync code changes to llm-distiller
- [ ] GPU available on llm-distiller (currently in use by coworker)

## Step 1: Train on llm-distiller

Once GPU is free:

```bash
ssh jeroen@llm-distiller

cd ~/llm-distillery
source venv/bin/activate

# Verify GPU is free
nvidia-smi

# Run training with head+tail
PYTHONPATH=/home/jeroen/llm-distillery python training/train.py \
    --filter filters/uplifting/v5 \
    --data-dir datasets/training/uplifting_v5 \
    --output-dir filters/uplifting/v5 \
    --use-head-tail \
    --epochs 3 \
    --batch-size 8
```

**Expected duration:** ~30-45 minutes for 3 epochs on RTX 4080
**Expected result:** MAE ~0.655 (vs current 0.680)

## Step 2: Copy Model to Local

```bash
# From local Windows machine
scp -r jeroen@llm-distiller:~/llm-distillery/filters/uplifting/v5/model/* \
    C:\local_dev\llm-distillery\filters\uplifting\v5\model\

scp jeroen@llm-distiller:~/llm-distillery/filters/uplifting/v5/training_history.json \
    C:\local_dev\llm-distillery\filters\uplifting\v5\

scp jeroen@llm-distiller:~/llm-distillery/filters/uplifting/v5/training_metadata.json \
    C:\local_dev\llm-distillery\filters\uplifting\v5\
```

## Step 3: Update Documentation

### 3.1 Update config.yaml

Enable head+tail preprocessing:

```yaml
preprocessing:
  head_tail:
    enabled: true  # Change from false
    head_tokens: 256
    tail_tokens: 256
    separator: " [...] "
```

### 3.2 Update README.md Scorecard

Update the Model Performance table in `filters/uplifting/v5/README.md` <!-- placeholder -->:

| Metric | Old (baseline) | New (head+tail) |
|--------|----------------|-----------------|
| Overall MAE | 0.68 | 0.655 |

Add note about head+tail preprocessing in the Training section.

### 3.3 Update model/README.md (HuggingFace card)

Add preprocessing requirements for users loading from Hub.

## Step 4: Push to HuggingFace

```bash
cd filters/uplifting/v5/model

# Login if needed
huggingface-cli login

# Push updated model
huggingface-cli upload jeergrvgreg/uplifting-filter-v5 . \
    --repo-type model \
    --commit-message "Update to head+tail preprocessing (MAE 0.655)"
```

## Step 5: Deploy to NexusMind

Use the deploy script (copies filter + common, commits):

```bash
cd C:\local_dev\llm-distillery
./scripts/deploy_to_nexusmind.sh uplifting v5
```

## Step 6: Test Locally + Production Validation

```python
from filters.uplifting.v5.inference import UpliftingScorer

scorer = UpliftingScorer()

# Verify head+tail is enabled
print(f"Head+tail enabled: {scorer.use_head_tail}")  # Should be True

# Test on sample article
result = scorer.score_article({
    "title": "Community Solar Program Provides Free Energy to 1,000 Low-Income Families",
    "content": "A new community solar initiative... [long article text]"
})
print(f"Score: {result['weighted_average']:.2f}, Tier: {result['tier']}")

# Production validation: compute MAE on test set
# Expected MAE ~0.655 (vs baseline 0.680)
```

## Step 7: Deploy via Git

```bash
# Push to origin
cd C:\local_dev\NexusMind
git push origin main

# Deploy to Sadalsuud
ssh user@sadalsuud "cd ~/NexusMind && git pull origin main"

# Verify on Sadalsuud
ssh user@sadalsuud "cd ~/NexusMind && python -c \"from filters.uplifting.v5.inference import UpliftingScorer; s=UpliftingScorer(); print('head_tail:', s.use_head_tail)\""

# Deploy to llm-distiller
ssh jeroen@llm-distiller "cd ~/NexusMind && git pull origin main"

# Verify on llm-distiller
ssh jeroen@llm-distiller "cd ~/NexusMind && python -c \"from filters.uplifting.v5.inference import UpliftingScorer; s=UpliftingScorer(); print('head_tail:', s.use_head_tail)\""

# Confirm all versions match
echo "=== Version Check ==="
git -C C:\local_dev\NexusMind rev-parse --short HEAD
ssh user@sadalsuud "cd ~/NexusMind && git rev-parse --short HEAD"
ssh jeroen@llm-distiller "cd ~/NexusMind && git rev-parse --short HEAD"
```

## Rollback Plan

If issues arise:

1. Set `preprocessing.head_tail.enabled: false` in config.yaml
2. Restore previous model from HuggingFace Hub (version history)
3. The inference code is backward compatible - disabling the flag restores baseline behavior

## Verification Checklist (Uplifting)

- [ ] Training completes with MAE <= 0.66
- [ ] Model loads correctly on local machine
- [ ] Head+tail preprocessing is applied (check logs)
- [ ] HuggingFace push succeeds
- [ ] NexusMind integration test passes (local)
- [ ] Sadalsuud deployment verified
- [ ] llm-distiller deployment verified

---

# PART B: Sustainability Technology Filter v2

Same process as uplifting, applied to sustainability_technology.

## Step 0: Code Changes (Prerequisites)

Before training, need to update sustainability_technology v2 with head+tail support:

- [ ] Add `yaml` import to `NexusMind/filters/sustainability_technology/v2/base_scorer.py` (removed here 2026-08-03)
- [ ] Add `_load_preprocessing_config()` method
- [ ] Update `score_article()` to apply head+tail
- [ ] Update `score_batch()` to apply head+tail
- [ ] Add `preprocessing.head_tail` section to `config.yaml`
- [ ] Sync code changes to llm-distiller

## Step 1: Train on llm-distiller

```bash
ssh jeroen@llm-distiller

cd ~/llm-distillery
source venv/bin/activate

PYTHONPATH=/home/jeroen/llm-distillery python training/train.py \
    --filter filters/sustainability_technology/v2 \
    --data-dir datasets/training/sustainability_technology_v2 \
    --output-dir filters/sustainability_technology/v2 \
    --use-head-tail \
    --epochs 3 \
    --batch-size 8
```

## Step 2: Copy Model to Local

```bash
scp -r jeroen@llm-distiller:~/llm-distillery/filters/sustainability_technology/v2/model/* \
    C:\local_dev\llm-distillery\filters\sustainability_technology\v2\model\

scp jeroen@llm-distiller:~/llm-distillery/filters/sustainability_technology/v2/training_history.json \
    C:\local_dev\llm-distillery\filters\sustainability_technology\v2\

scp jeroen@llm-distiller:~/llm-distillery/filters/sustainability_technology/v2/training_metadata.json \
    C:\local_dev\llm-distillery\filters\sustainability_technology\v2\
```

## Step 3: Update Documentation

- [ ] Enable `preprocessing.head_tail.enabled: true` in config.yaml
- [ ] Update README.md scorecard with new MAE
- [ ] Update model/README.md (HuggingFace card)

## Step 4: Push to HuggingFace

```bash
cd filters/sustainability_technology/v2/model
huggingface-cli upload jeergrvgreg/sustainability-technology-filter-v2 . \
    --repo-type model \
    --commit-message "Update to head+tail preprocessing"
```

## Step 5: Deploy to NexusMind + Test Locally

```bash
# Deploy using script
cd C:\local_dev\llm-distillery
./scripts/deploy_to_nexusmind.sh sustainability_technology v2

# Test locally
cd C:\local_dev\NexusMind
python -c "from filters.sustainability_technology.v2.inference import SustainabilityTechnologyScorer; s=SustainabilityTechnologyScorer(); print('head_tail:', s.use_head_tail)"
```

## Step 6: Deploy via Git

```bash
# Push and deploy (same as uplifting)
git push origin main
ssh user@sadalsuud "cd ~/NexusMind && git pull origin main"
ssh jeroen@llm-distiller "cd ~/NexusMind && git pull origin main"

# Verify versions match
echo "=== Version Check ===" && git rev-parse --short HEAD
ssh user@sadalsuud "cd ~/NexusMind && git rev-parse --short HEAD"
ssh jeroen@llm-distiller "cd ~/NexusMind && git rev-parse --short HEAD"
```

## Verification Checklist (Sustainability Technology)

- [ ] Training completes successfully
- [ ] Model loads correctly on local machine
- [ ] Head+tail preprocessing is applied
- [ ] HuggingFace push succeeds
- [ ] NexusMind integration test passes (local)
- [ ] Sadalsuud deployment verified
- [ ] llm-distiller deployment verified

---

# PART C: Commerce Prefilter Improvement

## Problem

Commercial/promotional content is leaking through the prefilter into scored articles. No systematic collection of examples yet.

## Current State

| Setting | Value |
|---------|-------|
| Model | DistilBERT multilingual (135M params) |
| Context window | 512 tokens |
| Languages | 104 |
| Recommended threshold | 0.95 |
| Current threshold | ? (needs verification) |

## Step 1: Verify Current Threshold in Production

Check what threshold NexusMind is using:
- [ ] Check Sadalsuud NexusMind config
- [ ] Check llm-distiller NexusMind config
- [ ] Confirm both use threshold 0.95

## Step 2: Set Up Leakage Collection

Add logging to capture commerce that slips through:

```python
# In NexusMind scoring pipeline, after prefilter passes:
if commerce_score > 0.5 and commerce_score < threshold:
    log_potential_leakage(article, commerce_score)
```

Collect:
- Article title, source, URL
- Commerce score
- Final filter scores
- Date flagged

## Step 3: Weekly Review Process

- [ ] Review collected examples weekly
- [ ] Categorize: true commerce vs borderline vs false positive
- [ ] Track patterns (sources, keywords, languages)

## Step 4: Evaluate v2 Need

After 2-4 weeks of collection, decide:
- If most leakage is threshold-related → adjust threshold
- If model blind spots → implement v2 (embeddings + MLP)
- If new patterns → add to training data, retrain v1

## Known Issues to Watch For

From backtest report:
- **Aldi-type retail commercials** - grocery/retail deals
- **Product launches disguised as news** - "Company X announces new product"
- **Gift guides** - "Best X for Y" articles
- **Non-English commerce** - Portuguese (canaltech), Spanish (xataka)

## v2 Design (If Needed)

Already documented in `filters/common/commerce_prefilter/docs/V2_DESIGN.md`:
- Frozen embeddings + MLP classifier
- 98.3% F1 vs 97.8% F1
- Simpler to retrain (just MLP, not full transformer)
- ~8-12 hours development + 1 week shadow mode

## Verification Checklist (Commerce Prefilter)

- [ ] Threshold verified at 0.95 on both servers
- [ ] Leakage collection logging implemented
- [ ] First batch of examples reviewed
- [ ] Decision made: adjust threshold / retrain v1 / implement v2

---

# PART D: Belonging Filter v1

## Problem

Belonging content (community bonds, intergenerational ties, rootedness) is rare in our tech/news corpus. Need to assess data availability before committing to full training.

## Current State

| Item | Status |
|------|--------|
| Concept & dimensions | ✅ Complete (6 dimensions) |
| Prefilter | ✅ Complete (10/10 tests passing) |
| Oracle prompt | ✅ Complete |
| Candidate articles | 72 extracted |
| RSS sources | 15/24 working in FluxusSource |
| Training data | ❓ Unknown - need assessment |

## Step 1: Data Assessment (Do First!)

Run oracle on sample to assess data availability:

```bash
# Sample 100 articles that pass prefilter
python -m ground_truth.batch_scorer \
    --filter filters/belonging/v1 \
    --source datasets/raw/fluxus_20260113.jsonl \
    --sample 100 \
    --output belonging_assessment.jsonl
```

**Decision criteria:**
- If **>20% score high** (tier high/medium): Proceed to training
- If **10-20% score high**: Expand RSS sources, wait 2-4 weeks
- If **<10% score high**: Park filter, pivot to resilience (see Fallback below)

## Fallback: Pivot to Resilience Filter

If belonging data assessment fails (<10% high-scoring), switch to **resilience v1**:

| Aspect | Belonging | Resilience |
|--------|-----------|------------|
| Content type | Community bonds, roots | Recovery from adversity |
| Data availability | Rare in news | Common in news |
| Status | Prompt ready | Design complete |
| Next step | - | Write prompt, prefilter |

**Why resilience has more data:**
- News covers disasters, crises, setbacks constantly
- Recovery/response stories are a natural follow-up
- "How X recovered from Y" is a common news format

**Resilience pivot steps:**
1. Write `prompt-compressed.md` based on existing design
2. Implement `prefilter.py`
3. Run data assessment (expect >30% high-scoring)
4. Proceed with oracle calibration and training

## Step 2: Expand Data Sources (If Needed)

If assessment shows insufficient data:

1. Review RSS sources in FluxusSource (`rss_belonging.yaml`)
2. Add more community/local news sources:
   - Local newspapers
   - Community foundations
   - Religious/cultural publications
   - Rural/regional news
3. Wait 2-4 weeks for collection
4. Re-run assessment

## Step 3: Oracle Calibration

Once data looks sufficient:

```bash
python -m ground_truth.calibrate_oracle \
    --filter filters/belonging/v1 \
    --source belonging_candidates.jsonl \
    --models gemini-flash \
    --sample-size 50
```

- Verify dimension scoring makes sense
- Check score distributions
- Adjust prompt if needed

## Step 4: Training Data Collection

Score 5K+ articles with oracle:

```bash
python -m ground_truth.batch_scorer \
    --filter filters/belonging/v1 \
    --source datasets/raw/master_dataset_20251009_20251124.jsonl \
    --output datasets/scored/belonging_v1.jsonl
```

## Step 5: Train Model

```bash
python training/train.py \
    --filter filters/belonging/v1 \
    --data-dir datasets/training/belonging_v1 \
    --use-head-tail \
    --epochs 3
```

## Step 6: Deploy

Same as uplifting:
- Copy to NexusMind
- Test locally
- Deploy to Sadalsuud
- Deploy to llm-distiller

## Verification Checklist (Belonging)

- [ ] Data assessment completed
- [ ] Decision: proceed / expand sources / pivot
- [ ] Oracle calibration passed
- [ ] 5K+ training articles scored
- [ ] Model trained (target MAE < 0.80)
- [ ] Deployed to Sadalsuud
- [ ] Deployed to llm-distiller
