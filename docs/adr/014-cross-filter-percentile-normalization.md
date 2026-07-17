# ADR-014: Cross-Filter Percentile Normalization

**Date:** 2026-03-30
**Status:** Accepted
**Method reference:** `docs/NORMALIZATION_METHOD.md` — the canonical, self-contained write-up of
the final method (op-point-anchored CDF, 2026-07-16), including the guard architecture and
reproduction steps this ADR predates.

## Decision

Normalize filter weighted average scores to a common 0-10 scale using percentile rank mapping. Each filter's empirical CDF is computed from **existing production MEDIUM+ data** on sadalsuud. ovr.news consumes normalized scores for cross-tab ranking and tab assignment.

## Context

### The problem

ovr.news has two views that compare scores across filters:

1. **HOME tab**: Shows top-N articles from all tabs combined, ranked by score. Uplifting dominates because its raw scores are structurally higher — a mediocre uplifting article (WA 5.5) outranks an exceptional nature_recovery article (WA 5.0).

2. **Article-tab assignment**: When a user opens an article from the HOME tab, it opens in the tab where its raw score is highest. A #1 recovery article often scores even higher on uplifting (because uplifting scores everything higher), so it opens in the Uplifting tab instead of Recovery — confusing users.

### The cause

All 5 ovr.news filters produce radically different score distributions on the same production traffic (182K articles on sadalsuud):

| Filter | Pass rate (MEDIUM+) | HIGH rate | Mean WA (MEDIUM+) |
|--------|--------------------|-----------|--------------------|
| uplifting | 62.8% | 17.1% | 5.76 |
| sustainability_tech | 8.6% | 5.1% | 5.31 |
| cultural_discovery | 4.8% | 15.5% | 5.70 |
| belonging | 2.6% | 19.6% | 5.80 |
| nature_recovery | 0.3% | 1.8% | 5.16 |

Root causes are structural: different oracle prompts, different gatekeeper caps, different concept prevalence in news. Not fixable by adjusting individual filters.

## Relationship to Existing Mechanisms

**Supersedes `score_scale_factor`.** The current pipeline applies a linear scale factor (`weighted_avg * 1.53` for nature_recovery) to stretch calibrated scores back toward 0-10. This is a crude linear approximation of cross-filter normalization. Percentile normalization replaces it with a proper non-linear mapping fitted from production data. When ADR-014 is deployed, `score_scale_factor` should be set to 1.0 (identity) for all filters.

**Same pattern as ADR-008.** Both calibration and normalization are monotonic non-linear mappings stored as lookup tables with interpolation:

| | ADR-008 (Calibration) | ADR-014 (Normalization) |
|---|---|---|
| **What** | Per-dimension score correction | Cross-filter WA alignment |
| **Input** | Raw student prediction | Calibrated weighted average |
| **Output** | Oracle-aligned score | Percentile-normalized 0-10 score |
| **Fitted from** | Val set (student vs oracle) | Production MEDIUM+ data |
| **Stored as** | `calibration.json` | `normalization.json` |
| **Applied** | Before weighted average | After weighted average |

The inference pipeline becomes: raw prediction → calibrate (ADR-008) → weighted average → gatekeeper cap → normalize (ADR-014) → reassign tier on normalized → display_rank. Calibration and gatekeeper run inside `FilterBaseScorer` (shared); normalization and tier reassignment run inside NexusMind's `ProductionScorer` wrapper (production-only). See "Implementation" below.

## How It Works

### 1. Build the CDF (from existing production data)

For each filter, extract weighted average scores from the existing MEDIUM+ production output on sadalsuud (`~/local_dev/NexusMind/data/filtered/{filter}/filtered_*.jsonl`). Sort and store as the empirical CDF: a sorted array of (raw_score, percentile) pairs in `filters/{name}/v{N}/normalization.json`.

**Why production MEDIUM+ data:**
- **Not val sets:** Training val sets are enriched via screen+merge (ADR-003) and active learning (ADR-005). Nature_recovery's val set has ~10% high-scoring articles, but production has 0.3%. Val set CDFs are not representative of production (tested and confirmed — see Alternatives).
- **Not all articles:** LOW-scoring articles (below 4.0) are never shown to ovr.news users. Normalizing among "articles worth showing" is the correct reference population for HOME tab ranking and tab assignment.
- **No inference cost:** The production data already exists on sadalsuud — 114K uplifting, 15K sustainability_tech, 8K cultural_discovery, 4.8K belonging, 48 nature_recovery articles (refitted 2026-04-10 from genuine MEDIUM+ data).

### 2. Normalize at inference time

Given a calibrated weighted average score `s` for filter `f`:
1. Look up `s` in filter `f`'s CDF (linear interpolation between stored points)
2. Get the percentile rank `p` (0.0 to 1.0)
3. Map to normalized score: `normalized = p * 10.0`

### 3. Solve both ovr.news problems

- **HOME tab**: Rank articles by their normalized score. An article at the 99th percentile for nature_recovery gets the same normalized score as one at the 99th percentile for uplifting — fair cross-tab competition.
- **Tab assignment**: Open the article in the tab where its **percentile rank is highest**. A recovery-focused article may score 5.0 on uplifting (60th percentile) and 4.5 on nature_recovery (99th percentile) — it opens in Recovery because that's where it's most exceptional.

### 4. Update when filters change

When a filter is retrained or a new filter is added:
1. Let it run in production for 2-4 weeks to accumulate MEDIUM+ articles
2. Fit the CDF from the accumulated production data
3. Save `normalization.json` and deploy alongside the model

No other filters' normalization files need to change. For a brand new filter with no production history, temporarily use the val set CDF as a bootstrap — replace with production CDF once enough data accumulates.

### 5. Edge cases

**Ties at score boundaries:** MEDIUM+ data starts at WA ~4.0, so most ties-at-zero issues are avoided. If ties exist within the MEDIUM+ range, articles at the same score get the same normalized value (midpoint of the tied percentile range).

**Out-of-bounds scores:** If a production score exceeds the CDF's observed range (higher than any score in the reference corpus), normalize to 10.0. If below, normalize to 0.0.

**Missing normalization.json:** Scores pass through unchanged (same fallback as isotonic calibration). This ensures backward compatibility during rollout.

**Refit cadence:** Refit when a filter is retrained (new model = new score distribution). Consider refitting annually or when distribution drift is detected (e.g., pass rate changes >20% relative).

## Rationale

- **Percentile mapping is distribution-agnostic**: works for bimodal (thriving), skewed (nature_recovery), or roughly normal (uplifting) distributions.
- **Production MEDIUM+ CDF reflects the right population**: normalizes among articles that actually compete for user attention — no enrichment bias, no noise inflation.
- **Independent per filter**: adding or updating one filter doesn't invalidate others.
- **Preserves within-filter ordering**: monotonic — if article A scores higher than B on a filter, it still does after normalization.
- **Solves tab assignment**: percentile rank directly answers "how exceptional is this article for this filter?"

### Alternatives considered

- **Z-score normalization**: Assumes normal distribution. Nature_recovery and belonging are heavily skewed — z-scores produce poor results (tested: nature_recovery p95 only reaches 6.84).
- **P99 max-based scaling** (`score / p99 * 10`): Simple but doesn't align filters. Tested: nature_recovery's p90 only reaches 1.94 normalized. Fails because it doesn't account for distribution shape, only the upper tail.
- **Val set CDF**: Enriched training data is not representative of production. Tested: belonging has 70% of val articles at score 1.0, creating massive ties that break percentile ranking (54% of nature_recovery articles get identical normalized score).
- **Full-corpus inference pass**: Running all 182K articles through every filter gives the complete 0-10 CDF, but costs 2-3 hours per filter on GPU and includes 90%+ noise articles that ovr.news never shows. The MEDIUM+ production data is the right population and costs nothing.
- **Adjusting individual tier thresholds**: Fragile, requires per-filter tuning, breaks on retrain.
- **Retraining with normalized targets**: Too invasive — changes training objective for all filters.

## Consequences

**Positive:**
- HOME tab fairly represents all tabs, not just uplifting
- Articles open in the tab where they're most exceptional
- New filters automatically get comparable scoring
- No changes to training, oracle scoring, or isotonic calibration

**Negative:**
- Adds a postprocessing step to the NexusMind inference pipeline
- Raw weighted averages are no longer the scores ovr.news displays
- Production distribution drift may require periodic refitting (refit when pass rate changes >20% relative, or at filter retrain)
- Nature_recovery CDF is based on only 48 articles (refitted 2026-04-10) — thin but sufficient for a monotonic lookup; will improve as corrected pipeline accumulates more MEDIUM+ articles with `raw_weighted_average`

## Implementation

- `filters/common/score_normalization.py` — fit CDF, apply normalization, save/load (reuses patterns from `score_calibration.py`). Since 2026-07-16, `fit_normalization(anchor_min=...)` anchors the CDF's lower edge to the filter's operating point: a breakpoint `(op_point, 0.0)` is prepended when the sample minimum sits above it, so `stats.raw_min == op_point` by construction (dense or sparse) and the fit-convention invariant (`tests/unit/test_normalization_invariant.py`) holds deterministically. `stats.sample_min` records the lowest score actually observed, for bias audit.
- `filters/{name}/v{N}/normalization.json` — per-filter CDF lookup table (schema: `{"method": str, "filter_name": str, "filter_version": str, "fitted_from": str, "fitted_at": str, "n_articles": int, "x": [...], "y": [...], "stats": {"raw_min", "sample_min", "raw_max", "raw_mean", "raw_std", "percentiles"}}`, where x = raw WA scores, y = normalized 0-10 scores; anchored fits carry one extra leading breakpoint, and legacy pre-anchor fits lack `stats.sample_min`)
- `scripts/normalization/fit_normalization.py` — CLI tool: reads production MEDIUM+ data from sadalsuud, fits CDF, saves JSON
- **NexusMind `src/scoring/production_scorer.py`** (the application site, since 2026-05-04): a wrapper class that composes any `FilterBaseScorer`/`HybridScorer` instance, loads `normalization.json` (with `_MIN_NORMALIZATION_ARTICLES = 200` safety valve, llm-distillery#167), reads `score_scale_factor` from `config.yaml`, and post-processes scoring output to replace `weighted_average` with the normalized value, populate `raw_weighted_average` for audit, and set `normalization_method ∈ {"percentile", "scale_factor", "none"}`. Tier is reassigned on the normalized weighted average so `tier`/`weighted_average` stay coherent for consumers that route on tier (e.g. Aegis) or display tier badges next to scores. `filter_base_scorer.py` itself is pure shared math — model + calibration + gatekeeper + raw weighted average + tier assignment on raw — and is identical between repos.
  - The original 2026-03-30 placement was inside `NexusMind/filters/common/filter_base_scorer.py`. That conflated shared model logic with NexusMind-only runtime concerns and required `.nexusmind-owns` to mask the divergence; the manifest mechanism then hid the 2026-04-16 silent revert of the application code for 18 days. The wrapper extraction (NexusMind merge `0e80d92`) eliminates the divergence and lets the manifest go empty.
  - Ordering invariant unchanged: normalization runs **after** calibration, gatekeeper, and weighted average computation.
- Set `score_scale_factor` to 1.0 for all filters with a fitted `normalization.json` (superseded for those filters; retained as fallback path for filters without one, e.g. fresh version bumps before the first CDF is fitted).
- NexusMind `display_ranking.py`: `max(score, analysis["weighted_average"])` now works correctly because normalized scores are comparable across filters.

## References

- ADR-008: Isotonic Score Calibration (per-dimension, within-filter — complementary)
- ADR-003: Screening Filter for Training Data (explains why val sets are enriched)
- ADR-005: Active Learning for Filter Improvement (explains enrichment further)
- `filters/common/score_calibration.py` — existing calibration pattern to follow
- Production data analysis (2026-03-30): 182K articles, 5 filters, sadalsuud
