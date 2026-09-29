# LLM Distillery - System Overview

**Last Updated**: 2025-11-17
**Status**: Harmonization complete, training data scoring in progress

---

## Executive Summary

The LLM Distillery implements **knowledge distillation** for content filtering: large oracle models (Gemini Flash) score articles with detailed reasoning, then student models (Qwen2.5-7B) learn to replicate oracle judgments efficiently.

**Harmonization Milestone**: All filters now follow consistent architecture - oracles output **dimensional scores only**, tier/stage classification handled by **postfilters**. This enables flexible thresholds without retraining.

---

## Datasets

### Raw Data (datasets/raw/)

| Dataset | Articles | Date Range | Size | Status |
|---------|----------|------------|------|--------|
| **master_dataset_20251010_20251114.jsonl** | 402,818 | Oct 10 - Nov 14, 2025 | 1.8 GB | ✅ PRIMARY (training source) |
| master_dataset.jsonl | 51,869 | Oct 2025 | 204 MB | ✅ Active |
| master_dataset_20251009_20251025.jsonl | 51,860 | Oct 9-25, 2025 | 204 MB | ✅ Archive |
| master_dataset_20250929_20251008.jsonl | 37,137 | Sep 29 - Oct 8, 2025 | 97 MB | ✅ Archive |
| master_dataset_20251026_20251029.jsonl | 10,766 | Oct 26-29, 2025 | 59 MB | ✅ Archive |

**Primary Dataset Stats** (master_dataset_20251010_20251114.jsonl):
- **Total**: 402,818 articles
- **Languages**: 30 (76.8% English, 7.1% Dutch, 5.5% Spanish)
- **Sources**: 441 sources
- **Top sources**: arxiv_cs (19.7%), newsapi (6.0%), arxiv_math (5.7%)
- **Profile**: `datasets/raw/master_dataset_20251010_20251114_profile.json`

### Scored Data (datasets/scored/)

| Filter | Version | Status | Target | Progress |
|--------|---------|--------|--------|----------|
| sustainability_tech_innovation | v1 | 🔄 Scoring | 5,000 | In progress |
| investment-risk | v3 | ⏳ Queued | 5,000 | Ready to start |
| uplifting | v4 | ✅ Validated | TBD | 16 validation samples |
| sustainability_tech_deployment | v3 | 🔄 Scoring | 5,000 | In progress (background) |

---

## Filter Organization

### Directory Structure

**Active Filters** (`filters/`):
- `investment-risk/` - Capital preservation filter (v2, v3)
- `sustainability_tech_innovation/` - Tech that works filter (v1)
- `sustainability_tech_deployment/` - Deployment at scale filter (v3)
- `uplifting/` - Uplifting content filter (v4)

**Future/Planned Filters** (`filters/todo/`):
- `ai_augmented_practice/` - AI augmentation for professional practice
- `future-of-education/` - Educational innovation and transformation
- `seece/` - Social, economic, and environmental corporate excellence
- `sustainability_economic_viability/` - Economic aspects of sustainability
- `sustainability_movement_growth/` - Growth of sustainability movement
- `sustainability_nature_recovery/` - Nature restoration and recovery
- `sustainability_policy_effectiveness/` - Policy impact and effectiveness

**Organizational Principles**:
- ✅ **Active filters**: Production or in-development (scoring/training)
- ✅ **Todo filters**: Planned but not started, design/planning phase
- ✅ **Version control**: Each filter has versioned subdirectories (v1, v2, v3, etc.)
- ✅ **Clean separation**: Easy to see current focus vs future plans

---

## Filters - Harmonization Status

### ✅ sustainability_tech_innovation v1.1

**Status**: Harmonized, validated, scoring in progress
**Purpose**: Rate sustainable tech that WORKS (deployed, pilots, validated research)
**Philosophy**: "Pilots and research need real results, not just theory."

**Architecture**:
- **Prefilter**: Option D (Minimal Filtering) - 68% pass rate, blocks obvious out-of-scope
- **Oracle**: Dimensional scores (0-10) with per-dimension reasoning
- **Output**: deployment_maturity, technology_performance, cost_trajectory, scale_of_deployment, market_penetration, technology_readiness, supply_chain_maturity, proof_of_impact
- **Postfilter**: Tier classification (breakthrough/validated/promising/early_stage/vaporware)
- **Gatekeeper**: IF deployment_maturity < 3.0 OR proof_of_impact < 3.0 → all scores = 1.0

**Validation**: ✅ 31/50 articles scored, harmonization verified (no classification in oracle output)

**Files**: `filters/sustainability_tech_innovation/v1/`
- prompt-compressed.md
- config.yaml (v1.1)
- prefilter.py (Option D)
- FINAL_PROMPT_COMPARISON.md
- PROMPT_STRUCTURE_COMPARISON.md

---

### ✅ investment-risk v3.0

**Status**: Harmonized, ready to score (forked from v2)
**Purpose**: Capital preservation for defense-first portfolio management
**Philosophy**: "You can't predict crashes, but you can prepare for them."

**Architecture**:
- **Prefilter**: Blocks FOMO, stock picking, affiliate marketing, clickbait
- **Oracle**: Dimensional scores (0-10) only
- **Output**: macro_risk_severity, credit_market_stress, market_sentiment_extremes, valuation_risk, policy_regulatory_risk, systemic_risk, evidence_quality, actionability
- **Postfilter**: Signal tier classification (RED/YELLOW/GREEN/BLUE/NOISE)
- **Gatekeeper**: Evidence >= 5 for RED tier

**Why v3**: Clean fork from v2 with harmonized architecture, ensures no legacy classification artifacts in training data

**Files**: `filters/investment-risk/v3/`
- prompt-compressed.md (v3.0-harmonized)
- config.yaml (v3.0, updated 2025-11-17)
- prefilter.py (v1.0)
- postfilter.py
- README.md

**Changelog v3**: "HARMONIZED ARCHITECTURE: Oracle outputs dimensional scores only, signal tier (RED/YELLOW/GREEN/BLUE/NOISE) computed by postfilter. Clean separation enables flexible tier thresholds without retraining. Forked from v2 to preserve clean training data lineage."

---

### ✅ uplifting v4

**Status**: Harmonized, validated
**Purpose**: Rate content for uplifting semantic value (human/planetary wellbeing)
**Focus**: MEANING not TONE

**Architecture**:
- **Prefilter**: Blocks corporate finance, business news, military content
- **Oracle**: 8 dimensional scores (flat integer format, overall reasoning)
- **Output**: agency, progress, collective_benefit, connection, innovation, justice, resilience, wonder
- **Postfilter**: content_type is metadata only, NOT tier classification
- **Gatekeeper**: collective_benefit < 5 → max_overall = 3 (unless wonder >= 7)

**Validation**: ✅ 16/16 articles scored, harmonization verified

**Files**: `filters/uplifting/v4/`

---

### 🔄 sustainability_tech_deployment v3

**Status**: Scoring in progress (background)
**Purpose**: Track deployment at scale (GW-level renewable energy)

**Files**: `filters/sustainability_tech_deployment/v3/`

---

## Harmonization Architecture

### Core Principle

**Oracle → Dimensional Scores → Postfilter → Tier/Stage Classification**

```
┌─────────────┐
│   Article   │
└──────┬──────┘
       │
       v
┌─────────────────┐
│   Prefilter     │  Fast rule-based (blocks obvious noise)
└──────┬──────────┘
       │
       v
┌─────────────────┐
│  Oracle (LLM)   │  Scores 8 dimensions (0-10) + reasoning
└──────┬──────────┘  Output: dimensional_scores ONLY
       │
       v
┌─────────────────┐
│   Postfilter    │  Computes tier/stage from dimensional scores
└──────┬──────────┘  Applies gatekeeper rules
       │
       v
┌─────────────────┐
│  Final Output   │  Tier + dimensional scores + metadata
└─────────────────┘
```

**Why this matters**:
- ✅ **Flexible thresholds**: Adjust tier definitions without retraining
- ✅ **Clean distillation**: Student learns dimensional scoring, not classification
- ✅ **Consistent architecture**: All filters follow same pattern
- ✅ **Maintainability**: Easy to update tier logic in postfilter

### Harmonization Changes (2025-11-17)

**investment-risk v2 → v3**:
- ❌ OLD: Oracle outputted `signal_tier` classification
- ✅ NEW: Oracle outputs dimensional scores, postfilter computes `signal_tier`
- **Impact**: Breaking change, forked to v3 for clean training data

**uplifting v4**:
- Minor: Clarified `content_type` is metadata, NOT tier classification
- **Impact**: Minimal, already mostly harmonized

**sustainability_tech_innovation v1**:
- ✅ Built with harmonized architecture from start
- **Impact**: None, reference implementation

---

## Tools & Agents

### filter-harmonizer Agent

**Location**: `docs/agents/filter-harmonizer.md` <!-- placeholder -->
**Created**: 2025-11-17
**Purpose**: Automated filter consistency checking and harmonization

**Features**:
- Validates oracle output format (dimensional scores only)
- Checks structural consistency (ARTICLE placement, inline filters)
- Generates harmonization reports
- Auto-fixes common issues

**Documentation**:
- `docs/agents/filter-harmonizer.md` <!-- placeholder --> - Full specification
- `docs/agents/FILTER_HARMONIZATION_GUIDE.md` - Quick reference
- `docs/agents/FILTER_CHECKLIST.md` - Development checklist
- `docs/agents/README_FILTER_HARMONIZER.md` - Overview

**Usage**:
```
Use the filter-harmonizer agent to analyze filters/investment-risk/v3
```

---

## Training Pipeline

### Knowledge Distillation Workflow

1. **Score training data** (Oracle: Gemini Flash)
   - Target: 5,000+ articles per filter
   - Cost: ~$0.75 per filter @ $0.00015/article
   - Time: 2-3 hours per filter

2. **Train student model** (Qwen2.5-7B)
   - Learn dimensional scoring from oracle
   - Expected accuracy: 92-96%
   - Cost: GPU compute (local or cloud)

3. **Validate model**
   - Test on held-out validation set
   - Compare to oracle judgments

4. **Deploy**
   - Fast inference (20-50ms)
   - Zero API cost
   - Production-ready

### Current Training Queue

| Filter | Oracle Scoring | Student Training | Status |
|--------|---------------|------------------|--------|
| sustainability_tech_innovation v1 | 🔄 In progress | ⏳ Queued | Scoring 5K articles |
| investment-risk v3 | ⏳ Queued | ⏳ Queued | Ready to start |
| uplifting v4 | ⏳ Not started | ⏳ Queued | Need to score 5K |
| sustainability_tech_deployment v3 | 🔄 In progress | ⏳ Queued | Background scoring |

---

## Scoring Commands

### sustainability_tech_innovation v1 (IN PROGRESS)

```bash
python -m ground_truth.batch_scorer \
  --filter filters/sustainability_tech_innovation/v1 \
  --source datasets/raw/master_dataset_20251010_20251114.jsonl \
  --output-dir datasets/scored/sustainability_tech_innovation_v1 \
  --llm gemini-flash \
  --batch-size 50 \
  --target-scored 5000 \
  --random-sample
```

### investment-risk v3 (QUEUED - run after sustainability_tech_innovation completes)

```bash
python -m ground_truth.batch_scorer \
  --filter filters/investment-risk/v3 \
  --source datasets/raw/master_dataset_20251010_20251114.jsonl \
  --output-dir datasets/scored/investment-risk_v3 \
  --llm gemini-flash \
  --batch-size 50 \
  --target-scored 5000 \
  --random-sample
```

### uplifting v4 (READY)

```bash
python -m ground_truth.batch_scorer \
  --filter filters/uplifting/v4 \
  --source datasets/raw/master_dataset_20251010_20251114.jsonl \
  --output-dir datasets/scored/uplifting_v4 \
  --llm gemini-flash \
  --batch-size 50 \
  --target-scored 5000 \
  --random-sample
```

---

## Training Commands

### After Scoring Completes

```bash
# sustainability_tech_innovation v1
python -m training.knowledge_distillation \
  --filter sustainability_tech_innovation \
  --version v1 \
  --scored-data datasets/scored/sustainability_tech_innovation_v1 \
  --output-dir models/sustainability_tech_innovation_v1 \
  --base-model Qwen/Qwen2.5-7B \
  --epochs 3

# investment-risk v3
python -m training.knowledge_distillation \
  --filter investment-risk \
  --version v3 \
  --scored-data datasets/scored/investment-risk_v3 \
  --output-dir models/investment-risk_v3 \
  --base-model Qwen/Qwen2.5-7B \
  --epochs 3

# uplifting v4
python -m training.knowledge_distillation \
  --filter uplifting \
  --version v4 \
  --scored-data datasets/scored/uplifting_v4 \
  --output-dir models/uplifting_v4 \
  --base-model Qwen/Qwen2.5-7B \
  --epochs 3
```

---

## Cost Estimates

### Oracle Scoring (Gemini Flash @ $0.00015/article)

| Filter | Articles | Cost | Time |
|--------|----------|------|------|
| sustainability_tech_innovation v1 | 5,000 | $0.75 | 2-3 hrs |
| investment-risk v3 | 5,000 | $0.75 | 2-3 hrs |
| uplifting v4 | 5,000 | $0.75 | 2-3 hrs |
| **Total** | **15,000** | **$2.25** | **6-9 hrs** |

### Student Training (Qwen2.5-7B)

- **Compute**: GPU required (local or cloud)
- **Time**: ~2-4 hours per filter (depends on hardware)
- **Cost**: $0 (local) or ~$2-5/filter (cloud GPU)

### Production Deployment

- **Inference time**: 20-50ms per article
- **Cost per article**: $0.00 (local model)
- **Savings vs Oracle**: 100% cost reduction for high-volume filtering

---

## Next Steps

### Immediate (Waiting for Current Scoring)

1. ⏳ Wait for sustainability_tech_innovation v1 scoring to complete (~5K articles)
2. ⏳ Start investment-risk v3 scoring after step 1 completes

### Short-term (This Week)

3. 🎯 Score uplifting v4 training data (5K articles)
4. 🎯 Train all three student models (sustainability_tech_innovation, investment-risk, uplifting)
5. 🎯 Validate trained models on held-out test sets

### Medium-term (Next Sprint)

6. 📊 Benchmark student vs oracle performance
7. 🚀 Deploy distilled models to production
8. 📈 Monitor performance and iterate
9. 🔄 Re-score older filters if needed (uplifting v4, investment-risk v2)

---

## References

### Key Documents

- **This file**: System overview and current status
- `filters/sustainability_tech_innovation/v1/FINAL_PROMPT_COMPARISON.md` <!-- placeholder -->: Harmonization comparison
- `filters/sustainability_tech_innovation/v1/PROMPT_STRUCTURE_COMPARISON.md` <!-- placeholder -->: Pre-harmonization analysis
- `filters/investment_risk/v3/README.md`: investment-risk v3 documentation
- `docs/agents/filter-harmonizer.md` <!-- placeholder -->: Filter harmonization agent
- `reports/filter_harmonization_report_2025-11-17.md`: Harmonization changes report
- `datasets/raw/master_dataset_20251010_20251114_profile.json`: Dataset profile

### Dataset Profiles

- `datasets/raw/master_dataset_20251010_20251114_profile.json`: 402K articles (primary)
- `datasets/raw/master_dataset_profile.json`: 51K articles (older)
- `datasets/raw/dataset_profile_report.txt`: Human-readable report (older)

---

## Archive Notes

### Dataset Renaming (2025-11-17)

- **OLD**: `historical_dataset_19690101_20251115.jsonl` (misleading name)
- **NEW**: `master_dataset_20251010_20251114.jsonl` (accurate date range)
- **Reason**: Filename claimed 1969-2025 range, actual content is Oct-Nov 2025 only
- **Impact**: None - just filename correction for accuracy

### Filter Versions

- **investment-risk**: v2.1 → v3.0 (harmonization fork)
- **sustainability_tech_innovation**: v1.0 → v1.1 (gatekeeper fix + prefilter update)
- **uplifting**: v4 (harmonization clarifications)
- **sustainability_tech_deployment**: v3 (in progress)

---

**End of System Overview**
