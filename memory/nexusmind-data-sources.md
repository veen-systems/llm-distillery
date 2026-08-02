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

Measured 2026-08-02 over 4 cycles:

| filter | scored | written to `filtered/` | excluded |
|---|---|---|---|
| the five common filters | 8,759 | 8,283 | **476** (`code_repo`, `developer_aggregator`, `firehose_aggregator`) |
| investment_risk | 8,765 | 6,572 | **2,193** (also `academic`, `social`) |

Consequence: **log-derived and file-derived denominators are different sets.**
For investment_risk this moved the prefilter pass rate from 0.642 (as logged by
the NM#284 shadow) to 0.770 (on the population that can actually surface) — a
0.129 gap that looks like a measurement bug and is not.

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
