# Use Regression-Only Student Models (No Reasoning Generation)

**Date:** 2025-11-13
**Status:** Accepted

> ⚠️ **AMENDMENT 2026-09-08 — what this record does NOT decide.**
> The title reads as though it settles "regression head vs any other head". It does not.
> The question decided here is **regression vs GENERATIVE** — whether a student should emit
> *reasoning text* alongside its scores — and it is decided on inference latency (200 ms vs
> 800 ms per article) and validation complexity. **It says nothing about a classification
> head**, and it is not a precedent against one.
>
> This matters because a **binary scope gate is a step function a regression head cannot
> represent**, measured on `human_thriving v8`: the oracle zeroes all six dimensions at
> `scope_verdict != in_scope`, and the student returns 4.66–4.85 on articles the oracle scores
> 0.80–0.90 — a ~4-point gap, landing just above the 4.50 operating point. See
> `docs/decisions/2026-09-08-scope-gate-two-head.md` and llm-distillery#150.
>
> ⛔ **Do not cite this record against a two-head (classifier + regression) proposal.** Cite it
> against putting a text generator in the production scoring path, which is what it is about.

## Context

After training the first student model (sustainability_tech_deployment, 1.5B, MAE 0.978), we considered whether student models should generate reasoning/explanations alongside dimensional scores, similar to how the oracle labels include reasoning.

**Current approach:**
- Student models: Regression head → Output: `[7, 6, 8, 5, 4, 6, 5, 7]` (dimensional scores only)
- Oracle labels: Include both scores AND reasoning text

**Question:** Should student models also generate reasoning to explain their scores?

## Decision

**Use regression-only models for production inference.** Student models will output dimensional scores only, without generating reasoning text.

**Reasoning generation remains oracle-only** (for ground truth labeling), not for production student models.

## Rationale

### 1. Scale Requirements

**Production workload:**
- 1,000 articles/day
- 15 filter models per article
- Total: 15,000 article-filter scoring operations/day

**Performance comparison:**

| Approach | Time per Article | Daily Total (Batched) | Feasible? |
|----------|-----------------|---------------------|-----------|
| Regression (current) | 200ms | 6 minutes | ✅ Excellent |
| Generative (with reasoning) | 800ms | 25 minutes | ✅ Acceptable |
| Generative (selective) | Hybrid | 21 minutes | ✅ Good |

**Conclusion:** While generative is feasible, regression is 4x faster with acceptable scale.

### 2. Use Case Analysis

**When reasoning is NOT needed:**
- Bulk filtering (most articles)
- Automated scoring pipeline
- Tier classification (scores → tiers via post-filter)
- Analytics/metrics (score distributions)

**When reasoning IS needed:**
- Human review of borderline cases
- Debugging model decisions
- Publishing featured articles
- Training/calibration

**Observation:** 90% of use cases only need scores, not explanations.

### 3. Engineering Simplicity

**Regression approach:**
- ✅ Simple training (MSE loss)
- ✅ Deterministic output (numbers)
- ✅ Easy validation (MAE/RMSE metrics)
- ✅ Fast inference (classification head)
- ✅ Proven working (MAE 0.978 achieved)

**Generative approach:**
- ⚠️ Complex training (next-token prediction, JSON formatting)
- ⚠️ Non-deterministic output (sampling)
- ⚠️ Validation complexity (parse JSON, check scores AND reasoning quality)
- ⚠️ Slower inference (text generation)
- ⚠️ Requires instruction-tuned base model

### 4. Flexibility

**Can add reasoning later** via:

**Option A: Hybrid system (two-tier)**
- Tier 1: Regression models filter all articles (fast)
- Tier 2: Generative model explains top N articles (selective)

**Option B: Separate explainer**
- Regression model scores article
- If explanation needed → call separate explainer model
- Explainer sees: article + scores → generates reasoning

**Option C: Oracle on-demand**
- For critical articles requiring explanation
- Re-run oracle (Gemini Flash) to get reasoning
- Cost: ~$0.001/article (acceptable for small volumes)

**Conclusion:** Regression doesn't prevent adding reasoning later.

## Consequences

### Positive

- ✅ **4x faster inference** - 6 min vs 25 min daily
- ✅ **Simpler deployment** - Regression models are proven and stable
- ✅ **Lower GPU memory** - Classification head vs full text generation
- ✅ **Deterministic scoring** - No sampling variance
- ✅ **Easy metrics** - MAE/RMSE are clear success criteria
- ✅ **Works today** - Already trained and validated (MAE 0.978)

### Negative

- ❌ **No explanations** - Scores are "black box" without reasoning
- ❌ **Harder debugging** - Can't see why model scored X vs Y
- ❌ **Less transparency** - Users don't see justification
- ⚠️ **Potential re-work** - If reasoning becomes critical, need to retrain generative models

### Neutral

- Can add reasoning selectively later (hybrid approach)
- Oracle still generates reasoning (ground truth has explanations)
- Post-filter logic remains unchanged (scores → tiers)

## Alternatives Considered

### Alternative 1: Generative Models with Reasoning
**Output:** JSON with scores + reasoning per dimension

**Pros:**
- Full transparency
- Matches oracle format
- Human-readable decisions

**Cons:**
- 4x slower inference (800ms vs 200ms)
- Complex training (JSON generation)
- Non-deterministic output
- Already rejected - see rationale above

**Decision:** Rejected - Speed and simplicity more important for production scale.

### Alternative 2: Hybrid Two-Tier System
**Approach:** Regression for all → Generative for subset

**Pros:**
- Fast bulk filtering
- Explanations where needed
- Best of both worlds

**Cons:**
- Two models to maintain
- Complexity managing which articles get reasoning
- Only 15 min time savings vs pure generative

**Decision:** Defer - Start with regression only, add tier 2 if demand emerges.

### Alternative 3: Oracle On-Demand for Explanations
**Approach:** Regression for scoring → Oracle (Gemini Flash) for explanations when needed

**Pros:**
- Simplest architecture
- Oracle reasoning is highest quality
- Pay-per-use ($0.001/article)

**Cons:**
- API dependency for explanations
- Cost for high volumes
- Latency for real-time explanations

**Decision:** Keep as backup option for selective use.

## Implementation

**Current state:** ✅ Complete
- Regression models trained and validated
- Test MAE 0.978 (sustainability_tech_deployment)
- Ready for deployment

**Production pipeline:**
```
Articles (1000/day)
    ↓
15 Regression Models (parallel)
    ↓
Dimensional Scores [7, 6, 8, ...]
    ↓
Post-Filter (scores → tiers)
    ↓
Filtered Articles by Tier
```

**Total time:** ~6 minutes/day (with GPU batching)

## Selective Reasoning for Top Articles

**Decision (2025-11-13):** Use **Oracle on-demand** for generating reasoning for top-scoring articles.

**Architecture:**
```
Stage 1: Bulk filtering (all articles)
  Articles (1000/day) → Regression models (15 filters) → Dimensional scores
  Time: 6 minutes/day
  Cost: $0 (self-hosted)

Stage 2: Selective reasoning (top articles only)
  Top scorers (10-20/day) → Oracle (Gemini Flash) → Reasoning + scores
  Time: <1 minute/day
  Cost: $0.01-0.02/day (10-20 × $0.001)
```

**Rationale:**
- ✅ **Low volume**: Only 10-20 articles/day need explanations
- ✅ **Negligible cost**: $0.02/day vs training separate explainer model
- ✅ **Highest quality**: Oracle reasoning is better than student model would be
- ✅ **Zero training effort**: No need to train/maintain explainer models
- ✅ **Already working**: Oracle (Gemini Flash) generates excellent reasoning

**Use cases for reasoning:**
- Featured articles for publishing
- User-requested explanations ("Why did this score high?")
- Borderline tier cases requiring human review
- Debugging/calibration

**Implementation approach:**
- Post-filter identifies top scorers (tier 1 or score threshold)
- API endpoint triggers oracle reasoning on-demand
- Cache reasoning to avoid re-generating for same article

**When to reconsider:**
- If volume exceeds 100+ articles/day needing explanations → train explainer model
- If API costs become significant (>$3/day = 3000 articles/day)
- If offline/air-gapped deployment required → train explainer model

## Success Metrics

**Regression model performance:**
- ✅ Test MAE < 1.0 (achieved: 0.978)
- ✅ Inference time < 300ms/article (achieved: 200ms)
- ✅ Daily processing < 30 minutes (achieved: 6 min)

**If these hold true → Decision validated**

## References

- Training results: `filters/sustainability_tech_deployment/v1/training_metadata.json`
- Test evaluation: `filters/sustainability_tech_deployment/v1/test_evaluation.json`
- Oracle labeling format: `datasets/scored/sustainability_tech_deployment/labeled_articles.jsonl`
- Related: `docs/decisions/2025-11-12-dimensional-regression-training.md`

## Discussion

**Key insight:** Production inference needs are different from oracle labeling needs.

**Oracle (labeling):**
- Slow is okay (batch processing overnight)
- Reasoning helps validate labels
- Human review of ground truth
- Cost-per-label acceptable

**Student (production):**
- Speed critical (real-time or near-real-time)
- Volume is high (15k scorings/day)
- Scores sufficient for filtering
- Cost-per-inference must be near-zero

**Principle:** Optimize each component for its use case. Oracle optimizes for quality + explainability. Student optimizes for speed + scale.
