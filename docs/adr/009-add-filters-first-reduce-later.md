# ADR-009: Add Filters First, Reduce Later

**Date:** 2026-03-04
**Status:** Accepted

> **Note (2026-10-07, owner ruling 2026-10-01 on LD#160):** this record predates ADR-013 (English everywhere the
> framework speaks) and is kept as written. Its Dutch tab names map to today's English lenses: **Welzijn** →
> Thriving (scored by `uplifting`), **Vooruitgang** → Solutions (then `sustainability_technology`), **Erfgoed** →
> Discovery (`cultural_discovery`). `scripts/analysis/cross_filter_landscape.py`, cited below, now uses the
> English names. `scripts/verification/check_framework_language.py` exempts this file as a historical record.

## Decision

Deploy new filters (belonging, ai-engineering-practice, nature_recovery, signs_of_wisdom) to ovr.news as separate tabs without pre-optimizing the taxonomy. Merge or remove tabs later if they feel redundant in practice.

## Context

Cross-filter correlation analysis on belonging v1 (7,370 articles) revealed two independent filter clusters:

- **"Human connection" cluster**: belonging (r=0.51 with uplifting, r=0.55 with cultural-discovery), uplifting, cultural-discovery (r=0.38 between the latter two)
- **"Technical/analytical" cluster**: sustainability_technology, investment-risk (|r| < 0.2 with everything)

This raised the question: does belonging overlap too much with uplifting/cultural-discovery to justify its own tab?

Analysis showed:
- 498 belonging MEDIUM+ articles are truly exclusive (LOW on all other filters)
- 374 belonging MEDIUM+ articles don't appear in any other filter's data at all
- Belonging's unique content is "quiet community stories" — intergenerational bonds, rootedness, mutual care — distinct from uplifting (systemic wellbeing) and cultural-discovery (heritage novelty)
- Estimated ~54 MEDIUM+ articles/day, enough for a viable tab

A dedup strategy (suppress welzijn articles that also score on other tabs) was considered but makes the volume imbalance worse (3.6x vs 2.9x) and is premature optimization.

## Rationale

1. **Splitting is harder than merging.** If we merge belonging into uplifting now, its unique signal gets buried. Separating it later requires retraining and UX changes. Deploying separately and merging later if redundant is cheaper.

2. **We have 4+ filters in the pipeline.** Belonging, ai-engineering-practice, nature_recovery, signs_of_wisdom. Better to see what 5-7 tabs feels like with real users than to over-optimize a 3-tab structure.

3. **Each filter answers a different question.** Even correlated filters serve distinct editorial purposes:
   - Welzijn: "Who is flourishing?" (individual/systemic wellbeing)
   - Erfgoed: "What wisdom emerges?" (heritage, cultural discovery)
   - Belonging: "Where do people find community?" (bonds, rootedness, care)
   - Vooruitgang: "What solutions work?" (technology, sustainability)

4. **ovr.news caps at 50 articles/filter/run.** Volume differences between filters don't affect user experience — each tab shows its best content regardless of total pool size.

## Consequences

**Positive:**
- Each filter gets editorial breathing room to prove its value
- Users can self-select into the perspectives they care about
- No premature merging of genuinely distinct signals

**Negative:**
- More tabs = more NexusMind scoring cost (+33% per additional filter)
- Risk of tab fatigue if too many tabs feel similar
- Must monitor: if two tabs consistently surface the same articles, merge them

**Mitigation:**
- Track cross-tab article overlap in production (if >50% of a tab's articles also appear on another tab, investigate merging)
- Allow articles to appear on multiple tabs — dedup is optional, not mandatory
- Review tab taxonomy after all planned filters are deployed

## Future: Intelligent Dedup

Not implementing now — premature before seeing 4+ tabs in production. If welzijn feels bloated or tabs feel samey, consider suppressing articles from welzijn when they also score MEDIUM+ on a more specific tab (erfgoed, belonging, etc.). Implementation: ~10 lines in ovr.news `pipeline.ts` at tab assignment. Analysis script ready at `scripts/analysis/cross_filter_landscape.py`.

## References

- Cross-filter correlation analysis: `scripts/analysis/cross_filter_landscape.py`
- Belonging v1 STATUS.md: dimension correlation, training results
- ADR-001: Moderate dimension correlations are acceptable (same principle at filter level)
