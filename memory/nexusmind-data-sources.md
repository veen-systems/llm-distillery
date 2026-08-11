---
name: nexusmind-data-sources
description: What each NexusMind data artefact excludes — filtered_*.jsonl also drops source-type-excluded rows, data/raw is pre-enrichment
metadata:
  type: reference
---

# NexusMind Data Sources

## WHICH length field to check, and at which stage (measured 2026-08-11)

**Measured**: matched every filtered batch (84 files, back to 2026-07-28) against
`ovr.db` — **4,319 matched, 4,295 identical (99.4%), 24 different (0.6%)**.

**⚠️ Do NOT read that as "ovr.news does not enrich". IT DOES, and I concluded
otherwise from this number — wrongly.** The ovr.news session read the code:
`summarize.ts:453` calls `enrichArticles`, which mutates `.content` in place;
:459–464 keeps the longer of the two; `upsertArticle` (:845) persists it. Google News
redirect resolution lives *inside* that path (`enrichment.ts:154–155`).

**It is narrowly gated** (`summarize.ts:441–448`): `content.length < 500`
**AND NOT** `wasEnrichedUpstream(article)`. So ovr yields whenever NexusMind claims
it enriched, and never touches anything over 500 chars. **Most articles never enter
the path — which is why "content matches what NM sent" and "ovr does not enrich" look
identical from the outside.** A high identity rate is consistent with both stories and
distinguishes neither; only reading the code did.

**Consequence for gate placement**: content can still grow *after* NexusMind writes
the payload, so a gate at NexusMind's `enrich_articles` judges a length ovr may yet
change. **For the Google News class it does not matter** — per NM#310 the redirect can
never resolve, so no enrichment anywhere produces a body, and the withholding rule is
needed wherever it sits. **Whether ovr should enrich at all is an open architectural
question** — the owner's position is that enrichment is NexusMind's job; ovr's
CLAUDE.md documents the consolidation as deliberate. Unresolved, owner's call.

**Open, and nobody has an answer**: both published stubs (106 and 131 chars) are far
under 500 and carry **no upstream-enriched flag of any kind** — verified across every
lens batch, top-level and per-lens. So both *should* have entered ovr's enrichment
path, and neither left a row in `enrichment_errors` or `enrichment_history`. An
enrichment attempt that leaves no trace is indistinguishable from one that never
happened, on exactly the articles it exists for.

**Read `len(content)` AFTER `enrich_articles`, NOT the `content_length` stamp.** The
stamp is captured at scoring (`main.py:1240`), before post-scoring enrichment
(`:1245`) can grow the body — so a gate on the stamp withholds articles that were
already fixed. The stamp is *correct for what it measures* (verified equal to
`len(content)` on a current row); it measures the wrong moment for this purpose.
Three fields, three stages:

| stage | field | note |
|---|---|---|
| scoring | `nexus_mind_attributes.<lens>.content_length` | pre-`enrich_articles`; **not** at the row's top level |
| after enrichment / handoff | `len(content)` on the row | **the one a gate should use** |
| publication (ovr.db) | `LENGTH(content)` | no `content_length` column exists there |
| before 2026-08-08 | `len(content)` only | stamp absent or null |

**A retracted conclusion, recorded because the wrong version is the intuitive one**:
I first concluded the gate belonged at *publication*, reasoning that ovr.news
re-enriches so a scoring-time gate would withhold articles about to become
full-length. That was generalised from **one** article and the mechanism was never
checked. See below — it was an intra-NexusMind artefact.

## Post-scoring enrichment does not propagate across lenses (0.1%, real)

`global_news_euronews_0111e7cdda7d`, one cycle, six lens batches inside 8 minutes:
`uplifting` scored it **6.20** — above `pipeline.enrichment.min_score: 4.0` — so
`enrich_articles` fetched the body, **294 → 14,963 chars**. The four lenses scored
*after* it in the same cycle still saw **294**. Others: `investment_risk` 7,991 vs 200
for the other five; 10,238 vs 199; 2,526 vs 300.

**Scale: 11 of 21,437 articles seen by 2+ lenses over the last 8 cycles — 0.1%.**
Small, but a genuine correctness issue: *which* lens gets the real article is decided
by which one first scores it above 4.0, and lens order is fixed, so the same lenses
systematically lose. Interacts with NM#319 — a filter whose distribution sits below
4.0 (`solutions v6` scored 0 of 56 above it) never triggers enrichment for any
article, so it is permanently on the stub side.

Reproduce: `/tmp/trace_one.py` and `/tmp/cross_lens_len.py` on sadalsuud; sources in
this session's scratchpad.
 — what each one excludes

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

---

## ovr.news `ovr.db` — the published set (added 2026-08-11)

`~/local_dev/ovr.news/data/ovr.db` on sadalsuud, ~231 MB. **This is the only source
that answers "did a reader see it?"** — everything in NexusMind answers "was it
scored?" or "did it clear the op-point?", which are different and much larger
populations.

```bash
ssh sadalsuud 'sqlite3 -readonly ~/local_dev/ovr.news/data/ovr.db "SELECT COUNT(*) FROM live_articles;"'
```

Tables that matter: `live_articles` (the live window — 3,529 rows spanning 14 days
as of 2026-08-11), `archive_articles`, `article_filter_scores`, `editorial_decisions`.

**What it excludes:** `live_articles` holds only the live window, so items that
rotated out are absent — it cannot answer historical questions. `archive_articles`
is the other half and was **not** used in the 2026-08-11 panel.

**Trap:** `weighted_average` in `live_articles` is the **NORMALIZED** score, not
raw. A row reading 8.95 can have per-dimension raws of 4.4–7.2. Normalization is
rank-in-batch by design (ADR-014). Do not compare it to an op-point.

**Trap:** ovr#275's resolver can rewrite article URLs, so matching a source by URL
pattern may undercount. Cross-check by `source` as well — on 2026-08-11 both routes
independently gave 39 Google News articles, which is what made the number usable.

**Scale to expect:** a population that is 25.7% of the collected corpus and 16.1%
of what a filter surfaces can still be 1.1% of what is published. Surfacing share
and reader exposure are different quantities — conflating them produced a retracted
"96% removed downstream" claim.
