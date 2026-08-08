---
name: nexusmind-data-sources
description: What each NexusMind data artefact excludes — filtered_*.jsonl also drops source-type-excluded rows, data/raw is pre-enrichment
metadata:
  type: reference
---

# NexusMind Data Sources — what each one excludes

Established 2026-08-02 during the NM#285 measurement. Both traps below produced
a clean-looking wrong number before being caught. Concrete instances of the
standing rule in `memory/MEMORY.md`: *before using any source as evidence,
establish what it excludes*.

## `data/filtered/<filter>/filtered_*.jsonl` excludes TWO populations

The documented one: rows are written only under
`if result["passed_prefilter"]` (`scripts/main.py`), so the file is 100%
passers by construction. Already in CLAUDE.md.

**The one that is easy to miss:** `src/scoring/source_filter.py` sets
`passed_prefilter = False` *after* scoring, for articles whose
`metadata.quality.type_classification` is in the filter's
`excluded_source_types`. All six production filters run this in enforce mode
(`shadow_mode: false`). Those articles **were scored** — so anything reading the
GPU scorer's log counts them — but they never reach the file and never reach
ovr.news.

**A sixth excluded type SHIPPED 2026-08-08 (LD#101): `eval_aggregator`.**
*(Live in all 6 filters on sadalsuud, `shadow_mode: false`. Verified by executing
`apply_source_filter` against the deployed config: `eval_aggregator` →
`passed_prefilter False`, `news_regional` → `True`, `excluded_count 1`. Cycle-log
confirmation still pending.)* FluxusSource's three FS#120 evaluation arms
(`gnews_eval`, `newsdata_eval`, `gdelt_constructive`) are an A/B measurement rig,
not a content source — but the stamp had **zero consumers**, so they were scored
by every filter and **published**: 30 rows in `ovr.news/data/ovr.db`, including a
funeral/murder story at tier `high` and Taiwanese local news under a Madagascar
query. They now join the population below: **scored, then dropped, absent from
`filtered/`.** The exclusion stops new ones; it does not retract the 30 already
published.

Two traps this creates, live now:

- **Any corpus statistic over `data/filtered/*` silently omits the eval arms**,
  exactly as it already omits the five types below. If you are measuring
  FS#120's funnel, take the numbers from the **GPU scorer's log**, not from
  `filtered/` — the file cannot answer "would this have been published".
- **Do not identify eval rows by source name.** `source LIKE '%_eval_%'`
  undercounts: it misses `gdelt_constructive_*` entirely (no `_eval_` in the
  name). That error cost 2 of 30 rows when first measured. Key on
  `metadata.quality.type_classification == 'eval_aggregator'`, which is verified
  to survive end-to-end into `ovr.db`.

*Why post-scoring exclusion rather than a publish-time gate in ovr.news: because
`apply_source_filter` **already is** a publish-time gate — it runs on
already-scored articles. A first version of this decision proposed building the
same behaviour in a third repo, on the mistaken premise that
`excluded_source_types` prevents scoring. It does not.*

Measured 2026-08-02 over 4 cycles:

| filter | scored | written to `filtered/` | excluded |
|---|---|---|---|
| the five common filters | 8,759 | 8,283 | **476** (`code_repo`, `developer_aggregator`, `firehose_aggregator`) |
| investment_risk | 8,765 | 6,572 | **2,193** (also `academic`, `social`) |

Consequence: **log-derived and file-derived denominators are different sets.**
For investment_risk the logged 0.642 and the written-set 0.770 differ by 0.129.

⚠️ **Treat 0.129 as an upper bound on the discrepancy, not a measured bias**
(corrected 2026-08-02 by adversarial review). The excluded rows' actual pass
rate is **unmeasured**: reconstructing them from `data/raw/` gave 0.008, which
is invalid for the reason in the next section, and the only other estimate
(0.647, as a residual) is derived from the reconciliation it would support.
Measuring it properly means instrumenting the pipeline, not replaying a file.

A related trap: two numbers computed over these two different populations may
*agree* closely and that agreement proves nothing. The replay's 0.5901 and the
shadow's 0.5934 for uplifting look like harness validation and are not — the
extra 476 rows simply happen to pass at a rate near the overall one.

> Reconcile the two explicitly before diffing them. Sum the per-batch `n` from
> the scorer log for one cycle and compare against `wc -l` of that cycle's
> filtered file; the difference should equal the source-type exclusions.

## `data/raw/content_items_*.jsonl` is PRE-enrichment

`ArticleFetcher.pre_enrich` fetches full article text **before** scoring, and
deliberately targets exactly the short-content articles. So a raw row is the RSS
stub as collected, not what the scorer saw.

Using raw as a stand-in for the scored article gave a prefilter pass rate of
**0.008** for a population whose true in-path rate was **0.647** — an 80× error,
because nearly all of those rows fail a 300-char length floor at collection time
and pass it after enrichment.

- **Fine** for `url`, `source`, `source_type`, `id`, `metadata` — enrichment does
  not touch those.
- **Wrong** for anything keyed on `content` or its length.

## Related

- `memory/prefilter-length-floor-hypotheses.md` — the measurement these came out of
- `memory/gotcha-log.md` — session entries
- CLAUDE.md Hard Constraints — the `filtered_*.jsonl` passers-only rule
