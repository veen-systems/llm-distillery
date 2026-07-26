# Changelog

All notable changes to LLM Distillery will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [July 2026] — violence_promotion Prefilter Scaffolded

### Added (2026-07-26)

**violence_promotion v1** — stamp-only cross-cutting binary classifier for the ovr.news constructive-news feed. Flags articles that promote, normalize, or present as desirable any form of mass violence: active combat, weapons manufacturing as progress, military force as solution, state violence against citizens, or instruments of violence as normal.

- `filters/common/violence_promotion/v1/prompt.md` — DeepSeek oracle rubric: 0–10 violence_score scale, key signals, 11 contrastive examples (active combat, weapons-as-progress, recovery, peace, disarmament, demining tech)
- `filters/common/violence_promotion/v1/oracle.py` — `ViolencePromotionOracle` wrapping DeepSeek API (deepseek-chat, temp=0), resumable ThreadPoolExecutor batch scoring, per-status-code HTTP retry logic
- `filters/common/violence_promotion/training/collect_examples.py` — collects calibration (~300) and training (~2000) samples from NexusMind filtered JSONLs, with cookie-wall detection and date-filtered file selection
- Calibration gate passed: 300 articles scored, 89.3% at 0–3 (clean negatives), 1.7% ambiguous middle (4–6), 8.7% at 7–10 (positives), 0.3% errors. Total DeepSeek spend <$0.10
- Architecture: two-stage (embedding-similarity probe → MLP classifier), per ADR-006/ADR-011. Phase 2 (full training) pending
- Downstream: NexusMind wiring tracked in NM#274, ovr.news exclusion in cross-repo-dependencies.md Chain 1

### Changed
- `filters/common/armed_conflict/` renamed to `filters/common/violence_promotion/` (broader scope: weapons industry, state violence, not just active combat)

---

## [November 2025] - Training Data Validation Complete

### Added (2025-11-20)

**🎯 Training Data Pipeline Complete** - All three filters have validated, production-ready training datasets:

**Training Data Generation:**
- **uplifting v4**: 6,705 examples (5,365 train / 669 val / 671 test)
- **sustainability_tech_innovation v2**: 4,968 examples (3,976 train / 496 val / 496 test)
- **investment-risk v4**: 4,880 examples (3,902 train / 488 val / 490 test)

**Validation Pipeline:**
- `training/validate_training_data.py` - Comprehensive quality validation
  - Structural integrity (required fields, ID uniqueness, label array length)
  - Data distribution (train/val/test splits at 80/10/10)
  - Label quality (score range [0-10], no NaN values, sufficient variance)
  - Content quality (non-empty titles/content, reasonable lengths)
  - Consistency (dimension names match across splits and config)
  - Score distributions per dimension

- `training/deduplicate_training_data.py` - Cross-split duplicate removal
  - Removes duplicate IDs across train/val/test (prevents data leakage)
  - Keeps duplicates in train, removes from val/test

- `scripts/validation/generate_validation_summary.py` - Validation report generator
  - Auto-generates concise validation reports for filter documentation
  - Saved to each filter directory (TRAINING_DATA_VALIDATION.md)

**Filter Development Guide Updates:**
- Added Phase 5 final validation step (validate → deduplicate → report)
- Updated validation criteria to include duplicate checks and split proportions
- Added Issue 4: Duplicate IDs across splits (common issue documentation)

**Repository Cleanup & Scripts Reorganization:**
- Moved architecture docs from root to docs/ (ARCHITECTURE.md, SYSTEM_OVERVIEW.md, DECISIONS.md)
- Organized scripts/ into phase-based subfolders (validation/, training/, oracle/, deployment/, dataset/)
- Moved 10 utility scripts to appropriate phase directories
- Archived obsolete filter-specific scripts (5 files to archive/scripts/obsolete/)
- Archived filter-specific validation scripts (6 files to archive/scripts/filter_specific/)
- Deleted temporary patch files (prepare_data_patch.py, prepare_data_v2.py)
- Moved filter reports to filter directories (self-contained packages)
- Root directory clean (only README.md, CHANGELOG.md remain)
- Updated README.md to reflect current state (training data ready)
- Updated docs/README.md with comprehensive documentation index
- Created comprehensive scripts/README.md documenting all utility scripts

### Changed (2025-11-20)

**Data Preparation:**
- `training/prepare_data.py` - Added score-bin stratification fallback
  - When no tiers defined (like investment-risk v4), uses score bins (0-2, 2-4, 4-6, 6-8, 8-10)
  - Ensures balanced distribution even without tier config
  - Prints stratification distribution during splitting

### Validation Results (2025-11-20)

**All filters PASS validation:**
- ✅ Zero duplicate IDs across train/val/test splits
- ✅ Perfect split ratios (80.0% / 10.0% / 10.0%)
- ✅ All scores in valid range [0-10]
- ✅ Sufficient variance (not all 0s or all 10s)
- ✅ Complete dimension coverage
- ✅ Consistent dimension names across splits and config
- ✅ Ready for model training

**Next Phase:** Model training (Qwen2.5-7B fine-tuning)

---

## [November 2025] - Harmonization Milestone

### Added

**🎯 Harmonized Architecture** - All filters follow consistent oracle output discipline:
- **Oracle outputs dimensional scores ONLY** (0-10 per dimension + reasoning)
- **Tier classification in postfilters** (enables flexible thresholds without retraining)
- **Consistent prompt structure** across all filters (scope → gatekeepers → article → dimensions)
- **Inline filters for every dimension** (fast model compatibility)

**New Filters:**
- **investment-risk v3** - Clean fork with harmonized architecture
  - Removed signal_tier from oracle output
  - Postfilter handles tier classification (RED/YELLOW/GREEN/BLUE/NOISE)
  - Philosophy: "You can't predict crashes, but you can prepare for them."

- **sustainability_tech_innovation v1** - Tech that works filter
  - 8 dimensions: deployment, performance, cost, scale, market, readiness, supply_chain, proof
  - Gatekeeper enforcement: IF deployment_maturity < 3.0 OR proof_of_impact < 3.0 → all scores = 1.0
  - Philosophy: "Pilots and research need real results, not just theory."
  - Prefilter Option D (68% pass rate, minimal false negatives)

**Filter Development Tools:**
- **filter-development-guide agent** - End-to-end lifecycle guidance (9 phases: planning → deployment)
  - Comprehensive checklists for each phase
  - Validation criteria and common pitfalls
  - Production readiness scoring

- **filter-harmonizer agent** - Automated consistency checking
  - Validates oracle output format (dimensional scores only)
  - Checks structural consistency (ARTICLE placement, inline filters)
  - Generates harmonization reports with Pass/Warning/Critical findings

- **Supporting documentation:**
  - FILTER_HARMONIZATION_GUIDE.md - Quick reference
  - FILTER_CHECKLIST.md - Development checklist
  - README_FILTER_HARMONIZER.md - Agent overview

**Filter Organization:**
- **Active filters** (filters/) vs **planned filters** (filters/todo/)
- Planned sustainability pillar filters (7 filters):
  - ai_augmented_practice
  - future-of-education
  - seece
  - sustainability_economic_viability
  - sustainability_movement_growth
  - sustainability_nature_recovery
  - sustainability_policy_effectiveness

**Dataset & Infrastructure:**
- **master_dataset_20251010_20251114.jsonl** - 402K articles (Oct-Nov 2025)
  - 76.8% English, 441 sources
  - Dataset profiling completed
  - Primary training data source

- **Documentation improvements:**
  - DOCUMENTATION_IMPROVEMENTS.md - Comprehensive audit
  - SYSTEM_OVERVIEW.md - Filter organization section
  - README.md - Updated to November 2025 status
  - filters/README.md - Complete rewrite with harmonization details
  - docs/agents/README.md - Added filter development agents

### Changed

**Filter Updates:**
- **uplifting v4** - Harmonization clarifications
  - Clarified content_type is metadata only (NOT tier classification)
  - Already mostly harmonized, minimal changes

- **investment-risk v2 → v3** - Clean architecture fork
  - Removed signal_tier from oracle output (breaking change)
  - Ensures training data has no legacy classification artifacts

- **sustainability_tech_innovation v1.0 → v1.1** - Major improvements
  - Gatekeeper enforcement: 85.7% false positives → 0% (FIXED)
  - Prefilter optimization: 16% → 68% pass rate (Option D)
  - False negatives: 62% reduction (84 → 32 blocked articles)
  - Added Philosophy line to prompt
  - Moved ARTICLE placement to after gatekeeper rules

**Dataset Renaming:**
- **OLD**: historical_dataset_19690101_20251115.jsonl (misleading - claimed 1969-2025)
- **NEW**: master_dataset_20251010_20251114.jsonl (accurate Oct-Nov 2025 date range)

**Directory Structure:**
- Reorganized filters into active (filters/) vs planned (filters/todo/)
- Clear separation of current focus vs future plans

### Fixed

**sustainability_tech_innovation v1:**
- **Gatekeeper enforcement** - 85.7% false positives → 0%
  - Problem: Articles with low deployment/proof scores still getting high overall scores
  - Fix: Postfilter correctly enforces gatekeeper rule (IF dm<3.0 OR poi<3.0 → all=1.0)
  - Validation: 20/20 articles with dm<3.0 correctly capped to 1.0

- **Prefilter false negatives** - 62% reduction
  - Problem: Option A blocked 84/134 good articles (62.7% false negative rate)
  - Fix: Option D minimal filtering (blocks only obvious out-of-scope)
  - Result: 32/134 blocked (23.9% false negative rate), 68% pass rate

- **Prompt harmonization** - 3 inconsistencies resolved
  - Added Philosophy line (missing from header)
  - Moved ARTICLE placement to after gatekeeper rules
  - Removed duplicate gatekeeper reminder section

**Oracle output discipline violations:**
- investment-risk: Removed signal_tier classification from oracle output
- sustainability_tech_innovation: Removed deployment_stage classification from oracle output
- uplifting: Clarified content_type is metadata, not classification

**Documentation accuracy:**
- README.md status updated from October → November 2025
- filters/README.md rewritten to reflect current versions
- Dataset filename corrected to accurate date range

### Validation

**sustainability_tech_innovation v1.1:**
- Scored 31/50 validation articles
- Gatekeeper enforcement: 100% working (20/20 articles correctly capped)
- Score distribution: Not skewed (35.5% low, 22.6% mid, 12.9% high)
- Minor issues: 2/31 out-of-scope articles (Mars, solar physics) - 6.5%

**uplifting v4:**
- Validated 16 samples
- Harmonization verified (no tier classification in oracle output)

### In Progress

**Training Data Generation:**
- sustainability_tech_innovation v1 - Scoring 5K articles (in progress)
- investment-risk v3 - Queued (after sustainability_tech_innovation)
- uplifting v4 - Queued
- sustainability_tech_deployment v3 - Scoring in background

**Knowledge Distillation:**
- Qwen2.5-7B student model training (blocked by training data generation)
- Target: 92-96% accuracy vs oracle

---

## [October 2025] - Initial Framework

### Added

**Core Framework:**
- Ground truth generation pipeline (Claude/Gemini API integration)
- Batch labeling system with timeout protection
- Oracle calibration framework (compare Flash/Pro/Sonnet)
- Prefilter calibration (measure blocking effectiveness)
- Secrets management (env vars + secrets.ini)

**Initial Filters:**
- **uplifting v1** - Uplifting content filter
  - 8 dimensions: agency, progress, collective_benefit, connection, innovation, justice, resilience, wonder
  - Philosophy: MEANING not TONE

- **sustainability v1** - Sustainability impact filter
  - 8 dimensions: climate_impact, technical_credibility, economic_viability, deployment_readiness, systemic_impact, justice_equity, innovation_quality, evidence_strength

- **investment-risk v1** - Capital preservation filter
  - 8 dimensions: macro_risk, credit_stress, sentiment, valuation, policy, systemic, evidence, actionability
  - Philosophy: Defense-first portfolio management

**Infrastructure:**
- Dataset sampling and profiling tools
- Generic batch labeler (universal labeling engine)
- Filter package structure (prompt, prefilter, postfilter, config.yaml)
- Model decision: Qwen2.5-7B-Instruct selected for local inference

### Documentation

- README.md - Project overview and quick start
- SYSTEM_OVERVIEW.md - Comprehensive system status
- docs/decisions/ - Architecture Decision Records
- filters/README.md - Filter development guide
- docs/agents/ - AI assistant workflow documentation

---

## Upcoming

### Next Sprint

- Complete training data generation for all active filters
- Train Qwen2.5-7B student models (3 filters)
- Validate student models on held-out test sets
- Benchmark student vs oracle performance

### Future

- Model evaluation framework (automated comparison)
- Production deployment (inference server with pre-filter + model)
- Additional sustainability pillar filters (7 planned in filters/todo/)
- Multi-task learning across filters
- Active learning for efficient data collection
- Model compression (quantization, pruning)

---

**Last Updated**: 2025-11-20
