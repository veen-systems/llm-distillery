# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records documenting significant technical and architectural decisions made in the llm-distillery project.

## What is an ADR?

An ADR captures an important architectural decision, the context that led to it, the decision itself, and its consequences. ADRs help future developers (including yourself) understand why things are the way they are.

## When to Create an ADR

Create an ADR when:
- Choosing between architectural approaches
- Selecting libraries, frameworks, or tools
- Making trade-offs with long-term impact
- Establishing patterns or conventions
- Changing or superseding previous decisions

See `docs/agents/agent-operations.md` for detailed criteria and the creation protocol.

## ADR Template

Use `docs/agents/templates/ADR-TEMPLATE.md` as the starting point for new ADRs.

## Active ADRs

### 2026-08-26: `data/prefiltered_out/` Gets a Retention Policy (#132)
**File:** `2026-08-26-prefiltered-out-retention.md`

The violence-promotion gate's shadow log was in neither the cleanup path nor the
archive path — it survived on the absence of a matching glob, so "leave it growing"
and "nobody has looked at this" were indistinguishable. Archived monthly to
`prefiltered_YYYY-MM.tar.gz` (one directory per gate), swept at 14 days fail-closed,
retention-cleaned and backed up off-site. ⚠️ **Not folded into the block ledger:**
pooled **88.3%** of flagged rows never reach it over the 12 joinable cycles
(per-cycle 72.5%–92.9%) — the flagged-but-KEPT population is what a threshold
argument is made on, and the ledger by construction never holds it.

### 2026-08-25: Pause `investment_risk` (owner ruling)
**File:** `2026-08-25-pause-investment-risk.md`

Aegis is dormant, so the filter and its export are off. **PAUSED ≠ REMOVED** — the
package, Hub repo, Contract C and 251 days of archives all stay. Un-pausing is
**three** files, not two: the missing `deploy/smoke_test_articles.jsonl` row failed
the fail-closed deploy gate and cost a production cycle.

### 2026-08-14: The Contract A Envelope
**File:** `2026-08-14-contract-a-envelope.md`

What belongs in the producer→NexusMind contract, and the rule that decides it: a
field belongs in Contract A iff only the collector can know it AND it is destroyed
if not recorded now.

### 2026-08-05: TDM Opt-Out Does Not Bar Distillation Training (#28)
**File:** `2026-08-05-tdm-opt-out-training-data.md`

AI-crawler opt-out directives in publisher `robots.txt` do not bar training here.
Grounds: they name third-party crawlers we do not operate; the student has a
regression head and cannot emit text, so no output substitutes for a publisher's work;
and the use is referral. Records the counter-argument against itself — "modelling is
not mining" is *not* a distinction the DSM Directive draws. Two carve-outs stay open:
the oracle ships full article text to Gemini/DeepSeek (risk accepted, recorded in
ovr.news's compliance register), and the six deployed filters were never assessed (#97).

### 2025-11-15: Dimensional Scoring Terminology
**File:** `2025-11-15-dimensional-scoring-terminology.md`

Adopt "scoring" terminology instead of "labeling" to accurately reflect dimensional regression. We produce continuous scores (0-10 per dimension), not discrete classification labels.

**Impact:** Renamed `batch_scorer.py` → `batch_scorer.py`, `datasets/scored/` → `datasets/scored/`, `--target-scored` → `--target-scored`. Aligns terminology with regression task architecture.

### 2025-11-14: Inline Filters for Fast Models
**File:** `2025-11-14-inline-filters-for-fast-models.md`

Restructure prompts to integrate critical filters inline with each dimension definition, rather than relying on top-level OUT OF SCOPE sections. Fast models (Gemini Flash, Claude Haiku) often skip top-level rules and jump directly to dimensional scoring.

**Impact:** Prompt calibration workflow updated with issue #5 (prompt structure). Inline filters reduced false positives from 87.5% to 0% for uplifting filter.

### 2025-11-14: Calibration/Validation Split
**File:** `2025-11-14-calibration-validation-split.md`

Apply train/test split pattern to prompt engineering. Use calibration sample to identify issues and fix prompt, then validate on fresh sample with different random seed to prevent overfitting.

**Impact:** Prompt calibration now includes mandatory validation step. Catches cases where prompt fixes work on calibration sample but don't generalize.

### 2025-11-13: Prompt Calibration Before Batch Scoring
**File:** `2025-11-13-prompt-calibration-before-batch-labeling.md` (v1.2)

Mandatory calibration step before batch scoring. Test oracle prompt on 50-100 article sample, identify systematic errors, fix prompt, validate, then proceed to batch scoring.

**Impact:** Prevents wasting $8-16 on mis-labeled datasets. Spent $0.047 on uplifting calibration to save $8+. Now at v1.2 with inline filters pattern.

### 2025-11-13: Remove Tier Classification from Oracle
**File:** `2025-11-13-remove-tier-classification-from-oracle.md`

Oracle outputs only dimensional scores (0-10 per dimension). Tier classification is computed post-processing from dimensional scores, not by the oracle.

**Impact:** Simplified oracle prompt, eliminated tier overfitting, post-filter controls tier thresholds.

### 2025-11-12: Dimensional Regression Training
**File:** `2025-11-12-dimensional-regression-training.md`

Train models on multi-dimensional regression (8 dimensional scores per article) rather than tier classification. Tier labels are metadata only.

**Impact:** Training, evaluation, QA workflows all focus on dimensional scores, not tier accuracy.

### 2025-11-12: Generic Training Data Preparation
**File:** `2025-11-12-generic-training-data-preparation.md`

Use a single generic script that reads filter configuration from config.yaml instead of separate scripts per filter.

**Impact:** Eliminates code duplication, enforces config.yaml as single source of truth, new filters require no code changes.

## Superseded ADRs

None yet.

## Deprecated ADRs

None yet.

## ADR Naming Convention

`YYYY-MM-DD-title-in-kebab-case.md`

Examples:
- `2025-11-12-dimensional-regression-training.md`
- `2025-11-12-generic-training-data-preparation.md`

## ADR Status Values

- **Accepted:** This is the current decision
- **Superseded:** Replaced by a newer decision (link to replacement)
- **Deprecated:** No longer applicable (explain why)

## Finding Related ADRs

When creating a new ADR:
1. Check if existing ADRs are affected
2. Link related ADRs in "References" section
3. Update superseded ADRs to point to new decision

## Maintenance

- Archive old ADRs to `archive/` if they become irrelevant
- Keep active ADRs up-to-date if implementation changes
- Use "References" section to link related documentation

## See Also

- `docs/agents/agent-operations.md` - Complete ADR creation protocol
- `docs/agents/templates/ADR-TEMPLATE.md` - Template for new ADRs
