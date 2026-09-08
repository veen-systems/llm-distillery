# LLM Distillery Data Inventory

**Last Updated:** 2026-01-30
**Total Data Size:** ~5.6 GB
**Total Oracle-Scored Articles:** 95,696
**Estimated Reproduction Cost:** €105+

---

## Overview

This document catalogs all data assets in the LLM Distillery project. The scored datasets represent significant investment (Oracle API costs) and should be treated as valuable, irreplaceable assets.

---

## 1. Production Datasets

### 1.1 Scored Datasets (Oracle-Labeled)

Location: `datasets/scored/`

These are the most valuable assets - articles scored by the Oracle (Gemini Flash) with dimensional regression labels (0-10 scale).

| Filter | Version | Articles | Dimensions | Size | Status | Created |
|--------|---------|----------|------------|------|--------|---------|
| uplifting | v5 | 10,000 | 8 | 74 MB | **Production** | Dec 2025 |
| investment-risk | v5 | 10,248 | 5 | 66 MB | **Production** | Dec 2025 |
| sustainability_technology | v1 | 10,000 | 5 | 154 MB | **Production** | Dec 2025 |
| sustainability_technology | v2 | ~8,000 | 5 | 27 MB | **Production** | Jan 2026 |
| cultural-discovery | v1 | ~10,000 | 5 | 74 MB | **Production** | Jan 2026 |
| cultural-discovery | v2 | 2,919 | 5 | 46 MB | **Production** | Jan 2026 |
| cultural-discovery | v3 | 7,827 | 5 | - | **Production** | Jan 2026 |

**Total Production Scored:** ~51,167 articles (v3 is merged from v1+v2)

#### Data Format (scored)
```json
{
  "article_id": "source_domain_hash",
  "title": "Article title",
  "content": "Full article text...",
  "source": "domain.com",
  "published_date": "2025-11-15",
  "{filter}_analysis": {
    "dimension_1": {"score": 7.5, "evidence": "..."},
    "dimension_2": {"score": 4.0, "evidence": "..."},
    ...
  },
  "analyzed_at": "2025-12-01T10:30:00Z",
  "analyzed_by": "gemini-flash-api-batch"
}
```

### 1.2 Training Splits

Location: `datasets/training/`

Pre-split datasets ready for model training. Standard 80/10/10 split with stratification.

| Filter | Version | Train | Val | Test | Total |
|--------|---------|-------|-----|------|-------|
| uplifting | v5 | 7,999 | 1,000 | 1,001 | 10,000 |
| investment_risk | v5 | 8,157 | 1,020 | 1,021 | 10,198 |
| sustainability_technology | v1 | 7,990 | 999 | 1,000 | 9,989 |
| sustainability_technology | v2 | ~6,400 | ~800 | ~800 | ~8,000 |
| cultural-discovery | v1 | 3,995 | 500 | 501 | 4,996 |
| cultural-discovery | v2 | 2,333 | 292 | 294 | 2,919 |
| cultural-discovery | v3 | 6,261 | 783 | 783 | 7,827 |

**Total Training-Ready:** ~61,582 articles

#### Data Format (training)
```json
{
  "id": "source_domain_hash",
  "title": "Article title",
  "content": "Full article text...",
  "url": "https://...",
  "labels": [7.5, 4.0, 6.5, 3.0, 8.0],
  "dimension_names": ["dim1", "dim2", "dim3", "dim4", "dim5"],
  "oracle_meta": { "...": "the whole oracle analysis block, verbatim" },
  "source": "...", "published_date": "...", "language": "..."
}
```

⚠️ **`oracle_meta` and the source passthrough exist only in splits built on or
after 2026-09-08 (llm-distillery#155).** Every split file on disk before that
date carries the six keys only. The key is `id`, never `article_id`. Rebuild with
`training/prepare_data.py` rather than reading a scope field off an older split.

### 1.3 Trained Models

Location: `filters/{filter}/v{N}/model/`

| Filter | Version | Type | Base Model | Size | MAE |
|--------|---------|------|------------|------|-----|
| uplifting | v5 | LoRA | Qwen2.5-1.5B | 86 MB | 0.68 |
| investment-risk | v5 | LoRA | Qwen2.5-1.5B | 86 MB | 0.48 |
| sustainability_technology | v1 | LoRA | Qwen2.5-1.5B | 86 MB | 0.69 |
| sustainability_technology | v2 | LoRA | Qwen2.5-1.5B | 86 MB | 0.71 |
| cultural-discovery | v1 | Full | Qwen2.5-1.5B | 172 MB | 0.82 |
| cultural-discovery | v2 | LoRA | Qwen2.5-1.5B | 86 MB | 1.47 |
| cultural-discovery | v3 | LoRA | Qwen2.5-1.5B | 86 MB | 0.77 |

#### Model Contents
```
model/
├── adapter_model.safetensors  # LoRA weights (74 MB)
├── adapter_config.json        # LoRA configuration
├── tokenizer.json             # Tokenizer
├── tokenizer_config.json
├── vocab.json
├── merges.txt
├── special_tokens_map.json
├── chat_template.jinja
└── README.md
```

---

## 2. Raw Source Data

Location: `datasets/raw/`

Unprocessed article collections from various sources.

| Dataset | Articles | Size | Date Range | Sources |
|---------|----------|------|------------|---------|
| master_dataset_20251009_20251124.jsonl | 178,462 | 937 MB | Oct-Nov 2025 | Mixed |
| fluxus_20260113.jsonl | 276,822 | 433 MB | Jan 2026 | Fluxus |
| fluxus_20251130_20251219.jsonl | 102,930 | 172 MB | Nov-Dec 2025 | Fluxus |
| master_dataset_20250929_20251008.jsonl | 37,137 | 97 MB | Sep-Oct 2025 | Mixed |

**Total Raw Articles:** ~595,351

#### Sources Include
- Science: ArXiv, bioRxiv, Nature, Science Daily
- News: Reuters, BBC, Spiegel, Guardian
- Tech: Hacker News, Dev.to, TechCrunch
- Finance: Bloomberg, Financial Times
- Community: Reddit (various subreddits)

---

## 3. Calibration Data

Location: `datasets/calibration/`

Small, curated datasets for Oracle prompt tuning and validation.

| Dataset | Articles | Purpose |
|---------|----------|---------|
| uplifting_v5 | ~1,000 | Score validation |
| sustainability_technology_v1_updated_prompt_v3 | 1,000 | PCA analysis |
| commerce_prefilter_v1 | 50 | Prefilter tuning |
| investment-risk-v5-iter3 | ~30 | Iterative calibration |
| ai-engineering-practice_v2 | ~50 | Prompt calibration |

---

## 4. Historical/Archived Data

### 4.1 Previous Versions (Scored)

Location: `datasets/scored/`

| Filter | Version | Articles | Notes |
|--------|---------|----------|-------|
| uplifting | v4 | 6,748 | Superseded by v5 |
| investment-risk | v4 | 4,905 | Superseded by v5 |
| investment-risk | v3 | ~8,000 | Archive |
| investment-risk | v2 | ~10,000 | Archive |
| sustainability_tech_innovation | v1 | ~7,000 | Renamed filter |
| sustainability_tech_innovation | v2 | 5,000 | Renamed filter |

### 4.2 Legacy Archive

Location: `archive/datasets/`

| Directory | Size | Contents |
|-----------|------|----------|
| old_versions | 278 MB | Deprecated datasets |
| test | 584 MB | Test/experimental data |
| old_processing | 216 MB | Legacy processing outputs |
| batches/ground_truth_batch10 | 220 MB | Early scoring batches |

---

## 5. Research Data

Location: `research/embedding_vs_finetuning/`

Experimental data from embedding vs fine-tuning comparison study.

| Asset | Size | Description |
|-------|------|-------------|
| embeddings/ | 270 MB | E5, MPNet embeddings |
| models/ | 86 MB | Extended context experiments |
| results/ | ~10 MB | Evaluation metrics, reports |

---

## 6. Filter Dimensions Reference

### uplifting (v5) - 8 dimensions
1. personal_growth_inspiration (0.15)
2. community_positive_impact (0.15)
3. innovation_solution_focus (0.15)
4. resilience_overcoming (0.10)
5. kindness_compassion (0.10)
6. environmental_stewardship (0.10)
7. scientific_medical_progress (0.15)
8. evidence_credibility (0.10) [gatekeeper]

### investment-risk (v5) - 5 dimensions
1. financial_impact (0.25)
2. market_sentiment (0.20)
3. risk_severity (0.25)
4. time_horizon (0.15)
5. source_credibility (0.15) [gatekeeper]

### sustainability_technology (v1/v2) - 5 dimensions
1. innovation_novelty (0.25)
2. environmental_impact (0.25)
3. scalability_viability (0.20)
4. scientific_rigor (0.15)
5. implementation_readiness (0.15)

### cultural-discovery (v1/v2) - 5 dimensions
1. discovery_novelty (0.25)
2. heritage_significance (0.20)
3. cross_cultural_connection (0.25)
4. human_resonance (0.15)
5. evidence_quality (0.15) [gatekeeper]

---

## 7. Data Quality Notes

### Scoring Quality
- All scores are 0-10 continuous (half-point increments)
- Gatekeeper dimensions cap overall score if below threshold
- Evidence field provides reasoning for each score

### Known Issues
- **cultural-discovery v1**: 94% low-scoring articles (regression-to-mean)
- **cultural-discovery v2**: Applied screening filter, better distribution
- **evidence_quality**: Consistently hardest dimension to predict (MAE ~2.0+)

### Distribution Targets
| Tier | Score Range | Target % | Typical % (random) |
|------|-------------|----------|-------------------|
| High | 7.0-10.0 | 10-15% | 0.5-2% |
| Medium | 4.0-6.9 | 30-40% | 5-10% |
| Low | 0.0-3.9 | 50-60% | 85-95% |

---

## 8. Reproduction Costs

If all data were lost, approximate cost to recreate:

| Asset | Method | Est. Cost | Time |
|-------|--------|-----------|------|
| Scored datasets (95K) | Oracle API | €100+ | 2-3 days |
| Trained models (11) | GPU compute | €50+ | 8-12 hours |
| Raw data | Fluxus collection | €0 | 1 week |
| Calibration | Manual + API | €10 | 1 day |
| **TOTAL** | | **€160+** | **1-2 weeks** |

---

## 9. Backup Recommendations

### Critical (Daily)
- `datasets/scored/*/` - Cannot regenerate without API cost
- `filters/*/v*/model/` - Training compute cost

### Important (Weekly)
- `datasets/training/*/` - Can regenerate from scored
- `datasets/calibration/` - Quality assurance

### Archival (Monthly)
- `datasets/raw/` - Large, can re-collect
- `archive/` - Historical reference

---

*Document auto-generated. See `scripts/create_data_archive.py` for backup tooling.*
