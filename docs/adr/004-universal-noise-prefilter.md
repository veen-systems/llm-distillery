# ADR 004: Commerce Prefilter as Universal Noise Filter

**Date**: 2026-01-31
**Status**: Proposed
**Context**: sustainability_technology active learning revealed 40% oracle waste on out-of-scope articles

## Decision

1. **Commerce prefilter remains the only truly universal noise filter** - commerce/shopping content is noise for all editorial filters

2. **Other noise categories are filter-specific, not universal** - what's noise for one filter may be signal for another

3. **Filter-specific noise should be handled by**:
   - The trained student model (learns in-scope vs out-of-scope)
   - Filter-specific keyword prefilters (for obvious cases)
   - Accept some oracle waste during training as cost of not missing edge cases

Architecture:
```
[Training time]
Article → Commerce Prefilter → Filter-Specific Prefilter → Oracle
                ↓                        ↓
          Blocks deals           Blocks obvious off-topic
          (universal)            (filter-specific keywords)

[Inference time]
Article → Commerce Prefilter → Filter-Specific Prefilter → Trained Model
                ↓                        ↓                       ↓
          Blocks deals           Blocks obvious           Scores low on
          (universal)            off-topic                learned noise
```

## Context

### The Problem

During sustainability_technology active learning, we found:
- 83 articles passed the keyword prefilter
- 33 (40%) were scored as out-of-scope by the oracle (all zeros)
- These represent wasted oracle API calls during training
- At inference time, these would waste model compute and pollute output

### Initial Hypothesis: Universal Noise Prefilter

We initially considered building a "universal noise prefilter" to catch categories like:
- Software/ML tutorials
- Farming practices
- Policy/economic discussions
- Consumer product reviews

### The Key Insight: One Man's Noise Is Another Man's Signal

Upon analysis, we realized most "noise" categories are **filter-specific**:

| Category | sustainability_tech | nature_recovery | dev_productivity | policy_analysis |
|----------|---------------------|-----------------|------------------|-----------------|
| Software tutorials | NOISE | NOISE | **SIGNAL** | NOISE |
| Farming practices | NOISE | **SIGNAL** | NOISE | NOISE |
| Policy discussion | NOISE | NOISE | NOISE | **SIGNAL** |
| Consumer electronics | NOISE | NOISE | NOISE | NOISE |
| Commerce/deals | NOISE | NOISE | NOISE | NOISE |

**Only commerce/deals is universally noise** across all editorial filters.

### Why Keyword Prefilters Fail for Semantic Distinctions

The oracle correctly distinguishes things keywords cannot:
- "GNN training framework" (out) vs "GNN for transit prediction" (in)
- "Docker optimization" (out) vs "heat pump control system" (in)
- "sustainable farming practices" (out) vs "precision agriculture tech" (in)

### Why Source Exclusion Fails

| Source | Out-of-scope | In-scope | Precision |
|--------|-------------|----------|-----------|
| `science_arxiv_cs` | 4 | 8 | **33%** |
| `positive_news_the_better_india` | 5 | 4 | **56%** |

Source exclusion would block legitimate applied research:
- [5.7] "Optimising for Energy Efficiency and Performance in Machine Learning"
- [4.8] "Laboratory and field testing of a residential heat pump retrofit"

**Conclusion**: Source-based filtering causes unacceptable false negatives.

## Rationale

### Commerce Is Truly Universal Noise

Commerce/shopping content (deals, discounts, affiliate content, price comparisons) is noise for ALL editorial filters because:
- It's promotional, not informational
- It lacks substantive content about any domain
- No filter exists where "50% off solar panels at Best Buy" is the target signal

The existing commerce prefilter v2 (embeddings + MLP, 97.8% F1) handles this well.

### Other Noise Categories Are Filter-Specific

| Category | Why It's NOT Universal |
|----------|------------------------|
| Software tutorials | Signal for developer-productivity filter |
| Farming practices | Signal for nature_recovery, agriculture filters |
| Policy discussion | Signal for policy_analysis filter |
| Medical research | Signal for health/biotech filters |
| Pure ML research | Signal for AI-engineering filter |

Building a "universal" prefilter for these would create false negatives when we later build filters where they're signal.

### How Filter-Specific Noise Should Be Handled

**At training time (oracle scoring):**
1. Accept some oracle waste (~30-40%) as cost of not missing edge cases
2. The oracle correctly distinguishes semantic boundaries (that's its job)
3. These "wasted" scores become valuable negative examples for the student model

**At inference time (production):**
1. The trained student model learns what's in-scope vs out-of-scope
2. Filter-specific keyword prefilters catch obvious cases (trade show coverage, etc.)
3. Model scores out-of-scope articles low, postfilter removes them

### The Training Data Insight

Articles scored as out-of-scope by the oracle (zeros) are NOT wasted - they're **valuable negative training examples**. The student model needs to see:
- What software tutorials look like (to score them low)
- What farming practices look like (to score them low)
- What the boundary between "applied ML" and "pure ML" looks like

This is how the model learns filter-specific scope.

## Consequences

### Positive

- **Clarity**: Commerce prefilter remains the only universal noise filter
- **No false negatives**: Filter-specific noise categories won't be blocked for future filters where they're signal
- **Training data reuse**: Oracle "zeros" become valuable negative training examples
- **Simpler architecture**: No new universal prefilter to build/maintain

### Negative

- **Oracle costs**: Accept ~30-40% oracle waste during training data collection
- **Inference waste**: Some out-of-scope articles will reach the model at inference time

### Trade-off Accepted

We accept higher oracle costs during training in exchange for:
1. No risk of false negatives from overly aggressive prefiltering
2. Rich negative examples that teach the model filter-specific scope
3. Simpler overall architecture

## Implementation Plan

### Commerce Prefilter (Already Done)

Commerce prefilter v2 exists and handles universal noise:
- Location: `filters/common/commerce_prefilter/v2/`
- Architecture: Embeddings + MLP
- Performance: 97.8% F1

### Filter-Specific Prefilters (Existing)

Each filter maintains keyword-based prefilters for obvious exclusions:
- sustainability_technology: excludes gaming hardware, smartphone reviews, etc.
- uplifting: excludes pure commerce, tragedy porn, etc.

### Oracle Scoring (Accept Waste)

During training data collection:
- Accept that ~30-40% of articles will score zeros
- These zeros are valuable training data, not waste
- No new prefilter needed

### Student Model (Learns Scope)

The trained model learns filter-specific scope from:
- High-scoring articles (what IS in scope)
- Zero-scoring articles (what is NOT in scope)
- Boundary cases (subtle distinctions)

## Alternatives Considered

### 1. Universal Noise Prefilter (Embeddings + MLP)

- **Initially proposed**: Build classifier for software, consumer, farming, policy, etc.
- **Rejected**: These categories are filter-specific, not universal
- **Risk**: Would create false negatives for future filters where they're signal

### 2. Source-Level Exclusion

- **Analyzed**: Exclude `arxiv_cs`, `dev.to` sources entirely
- **Rejected**: 33-56% precision causes unacceptable false negatives
- **Evidence**: Would block "heat pump retrofit testing" paper (score 4.8)

### 3. Expanded Keyword Prefilters

- **Considered**: Add patterns for "Docker", "AWS tutorial", etc.
- **Partially adopted**: For obvious cases in filter-specific prefilters
- **Limitation**: Keywords can't distinguish "Docker efficiency" from "energy efficiency"

### 4. Per-Filter Scope Classifiers

- **Considered**: Train embedding + MLP classifier per filter
- **Deferred**: High maintenance cost (N models for N filters)
- **May revisit**: If oracle costs become prohibitive at scale

### 5. Accept Oracle Waste (ADOPTED)

- **Adopted**: Accept 30-40% oracle waste during training
- **Rationale**: These zeros become valuable negative training examples
- **Trade-off**: Higher oracle cost, but richer training data and no false negatives

## References

- Analysis: ~~`datasets/curation/sustainability_tech_review/prefilter_gap_analysis.md`~~
- Commerce prefilter v2: `filters/common/commerce_prefilter/v2/`
- Data collected: `datasets/training/universal_noise_prefilter/` (repurpose for filter-specific training)
