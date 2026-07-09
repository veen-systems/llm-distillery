# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records documenting important technical decisions made in the LLM Distillery project.

## What are ADRs?

ADRs are short documents that capture important architectural decisions along with their context and consequences. They help teams understand:
- Why decisions were made
- What alternatives were considered
- What trade-offs were accepted

## ADR Index

- [ADR-001: Moderate Dimension Correlations Are Acceptable](001-moderate-correlation-acceptable.md) - Clarifies when dimension correlations reflect real domain relationships vs problematic redundancy
- [ADR-002: Modern Prompt Format Support](002-modern-prompt-format.md) - Introduces flexible prompt format without wrapper sections, supports JSON examples and custom structures
- [ADR-003: Screening Filter for Training Data](003-screening-filter-for-training-data.md) - Enriches training data with signal-bearing content before oracle scoring
- [ADR-004: Commerce Prefilter as Universal Noise Filter](004-universal-noise-prefilter.md) - Only commerce is universal noise; filter-specific noise handled by model (PROPOSED)
- [ADR-005: Active Learning for Filter Improvement](005-active-learning-for-filter-improvement.md) - Use model predictions to guide training data collection; includes needle hunting strategy
- [ADR-006: Hybrid Inference Pipeline](006-hybrid-inference-pipeline.md) - Two-stage pipeline: fast embedding probe (Stage 1) + fine-tuned model (Stage 2)
- [ADR-007: Adapter Format and Deployment](007-adapter-format-and-deployment.md) - PEFT adapter key format conventions for local and Hub loading
- [ADR-008: Isotonic Score Calibration](008-isotonic-score-calibration.md) - Post-hoc per-dimension isotonic regression to correct MSE score compression
- [ADR-009: Add Filters First, Reduce Later](009-add-filters-first-reduce-later.md) - Deploy new filters as separate tabs; merge later if redundant in practice
- [ADR-010: Oracle Consistency Over Data Volume](010-oracle-consistency-over-data-volume.md) - Prompt precision and anti-contamination design matter more than training data volume for student MAE
- [ADR-011: Embedding-Based Screening for Needle Filters](011-embedding-screener-for-needle-filters.md) - Use Phase 3 positives as e5-small embedding seeds to screen large corpora for batch labeling candidates
- [ADR-012: Lens-Aligned Filter Naming](012-lens-aligned-filter-naming.md) - Rename filters to match ovr.news editorial lens names at next version bump
- [ADR-013: English Lens Names](013-english-lens-names.md) - All lens and tab names use English; no Dutch naming (amends ADR-012)
- [ADR-014: Cross-Filter Percentile Normalization](014-cross-filter-percentile-normalization.md) - Normalize scores across filters using percentile rank mapping; supersedes score_scale_factor
- [ADR-015: Lenses as Perspectives, Not Partitions](015-lenses-as-perspectives-not-partitions.md) - Lenses are overlapping perspectives; oracle prompts must not exclude adjacent lenses' content
- [ADR-016: Drop Tier Assignments](016-drop-tier-assignments.md) - Filters output pass/block + continuous score only; tiers removed from pipeline (gradual, consumer-first)
- [ADR-017: Inter-Oracle MAE as Distillation Floor](017-inter-oracle-mae-as-distillation-floor.md) - Frontier LLMs disagree by 0.6-1.0 MAE; distilled models at or below this floor need prompt improvements, not more training
- [ADR-018: Declarative Prefilter Shape](018-prefilter-shape-harmonization.md) - Extend BasePreFilter with EXCLUSION_PATTERNS / OVERRIDE_KEYWORDS / POSITIVE_PATTERNS; per-filter migration in priority order (#52)
- [ADR-019: Per-Category Exclusion Overrides](019-per-category-exclusion-overrides.md) - Extend `_is_excluded` with per-category override config dict (`CATEGORY_OVERRIDES`) + `_category_override_applies()` hook so 4/7 filters can drop custom `apply_filter`; unblocks #51 per-filter consumption
- [ADR-021: Ground-Truth Deploy Gate](021-ground-truth-gate.md) - A deploy gate judges each model against held-out ORACLE ground truth (the chosen editorial line), not against the prior deployed model; supersedes `agreement_gate.py` (which false-FAILed v4 by judging it against a Gemini-labeled v2 reference)

## Format

Each ADR includes:
- **Date** - When the decision was made
- **Status** - Proposed, Accepted, Deprecated, Superseded
- **Decision** - The decision in 1-2 sentences
- **Context** - Background and problem being solved
- **Rationale** - Why this decision was made
- **Consequences** - Positive and negative outcomes
- **References** - Related documents, code, data
