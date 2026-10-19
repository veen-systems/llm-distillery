# NexusMind data sources — archive

*Blocks moved VERBATIM out of `memory/nexusmind-data-sources.md` (#163, the read surface). The live file keeps a one-line pointer at each block's old position.*

## Moved 2026-10-16 (#163 round 6)

### From § WHICH length field to check

**RESOLVED (ducroq/ovr.news#312).** Both published stubs (106 and 131 chars) are far
under 500 and carry **no upstream-enriched flag of any kind** — verified across every
lens batch, top-level and per-lens, which eliminated `wasEnrichedUpstream`. The answer:
**enrichment ran, refused, and the refusal is silent by construction.**
`ovr.news src/lib/enrichment.ts:154–167` — when `resolveGoogleNewsUrl` returns nothing
(always, per NM#310), it emits a debug line and returns **before** the fetch, **before**
the `SKIP_DOMAINS` check, and **before** the `try/catch` at `:271` that calls
`logError`. Nothing is persisted. **Three other early returns in the same function have
the identical shape** (skip-domain, invalid URL, SSRF guard).

The refusal is *correct* — fetching an unresolvable GN link retrieves a 60–100 char JS
stub. **The silence is the defect**, and it falls at exactly the articles that trigger
it: every refused article is one where refusal cannot be told from no-attempt, and
those are precisely the ones an investigation picks.

Verified not a dead-table artefact: `enrichment_errors` holds **453 rows, last written
2026-08-11 10:56** — live. Separately, **`enrichment_history` has 0 rows ever**: its
writer (`db-enrichments.ts:273`) has no callers while `db-maintenance.ts:30` prunes it
at 90 days — maintenance for a table nothing writes.

**Whichever way the "should ovr enrich at all" question goes, #312 stands** — a silent
refusal is a defect at whichever layer performs it, and if enrichment moves upstream
the observability requirement must move with it rather than being re-lost.

### From § WHICH length field to check

**A retracted conclusion, recorded because the wrong version is the intuitive one**:
I first concluded the gate belonged at *publication*, reasoning that ovr.news
re-enriches so a scoring-time gate would withhold articles about to become
full-length. That was generalised from **one** article and the mechanism was never
checked. See below — it was an intra-NexusMind artefact.

### From § The exclusion list is NOT the same across filters

So "a `type_classification` change affects what reaches the filters" is **false
for five of six by construction** — the label is not in their lists. This came up
answering FluxusSource#144 (a plurality rule replacing any-intersection, so one
science section stops academicising a whole publisher, plus GN feeds without a
`site:` operator now labelled `proxy_aggregator`). Measured over 1,226,118 rows,
`collected_date` ≤ 2026-08-10 vs ≥ 2026-08-12 (08-11 excluded — the scorer is
batch-only, so the code date and the data date are different quantities and the
regeneration window cannot be pinned tighter than 11:13–18:45 CEST):

| `type_classification` | pre | post |
|---|---|---|
| `academic` | **25.4%** | **8.7%** |
| `proxy_aggregator` | **0%** | **15.7%** |
| `news_major` | 25.4% | 17.9% |
| `unknown` | 29.3% | 37.9% |

**`investment_risk v6` excludes both labels, so its excluded share went ~25.4% →
~24.4% — the volume barely moved and the composition changed.** Wrongly-
academicised publishers now reach it; GN proxy rows are now correctly kept out.
That is a correctness win, not a volume win, and it is confined to one filter.

### From § `live_articles` is NOT the reader population

⚠️ **The deployed view HAD drifted from its own source and could not reconverge —
FIXED 2026-08-16 by ovr#325.** *(Corrected 2026-08-17, reported by the ovr.news
session. The paragraph below described the world before that fix and was still
asserting permanence a day after it landed — a stale "permanent by construction"
claim is worse than no claim, because it discourages the check.)*

The drift was real: live DDL on sadalsuud filtered `tier IN ('high','medium')` while
`db-schema.ts:793` said `weighted_average >= 4.5`, and it had been that way since
**2026-04-10**. Mechanism: every statement in `createViews()` was
`CREATE VIEW **IF NOT EXISTS**`, a no-op where the view already exists, and
`recreateViews()` was exported and never called. **ovr#325 moved the view bodies into
`VIEW_DEFINITIONS` and `reconcileViews()` now runs unconditionally from
`initializeSchema`, writing only on mismatch — so the view self-heals.**

### From § `duplicate_url` is NOT all re-reads

**Not caused by, and not worsened by, the 2026-08-16 id-before-url reorder** — these rows
carry distinct ids, so the in-batch check never fires and the URL check drops them under
both orderings. Confirmed by replay.

## Moved 2026-10-19 (#163 round 10)

### From § WHICH length field to check

**Measured**: matched every filtered batch (84 files, back to 2026-07-28) against
`ovr.db` — **4,319 matched, 4,295 identical (99.4%), 24 different (0.6%)**.

**⚠️ Do NOT read that as "ovr.news does not enrich". IT DOES, and I concluded
otherwise from this number — wrongly.** The ovr.news session read the code:
`summarize.ts:453` calls `enrichArticles`, which mutates `.content` in place;
:459–464 keeps the longer of the two; `upsertArticle` (:845) persists it. Google News
redirect resolution lives *inside* that path (`enrichment.ts:154–155`).

### From § Post-scoring enrichment does not propagate across lenses

`global_news_euronews_0111e7cdda7d`, one cycle, six lens batches inside 8 minutes:
`uplifting` scored it **6.20** — above `pipeline.enrichment.min_score: 4.0` — so
`enrich_articles` fetched the body, **294 → 14,963 chars**. The four lenses scored
*after* it in the same cycle still saw **294**. Others: `investment_risk` 7,991 vs 200
for the other five; 10,238 vs 199; 2,526 vs 300.

### From § Post-scoring enrichment does not propagate across lenses

Reproduce: `/tmp/trace_one.py` and `/tmp/cross_lens_len.py` on sadalsuud; sources in
this session's scratchpad.

### From § THE LIVE WINDOW ROLLS

**Demonstrated, not asserted (2026-09-01):** all 18 rows of `datasets/adverse/uplifting.jsonl`
had been reduced to 300-char excerpts and were believed lost. **18 of 18 recovered** — 3 from
the live window, 15 from `nexusmind_2026-08.tar.gz` — every one matching its recorded
`content_original_length` exactly. Tool: `scripts/dataset/rehydrate_adverse.py`.
Record: `docs/evidence/2026-09-01-v8-phase-b-preflight/` §4.

### From § `data/filtered/<filter>/filtered_*.jsonl` excludes TWO populations

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

### From § `data/filtered/<filter>/filtered_*.jsonl` excludes TWO populations

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

### From § `data/filtered/<filter>/filtered_*.jsonl` excludes TWO populations

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

### From § And it is not producer bytes either

⚠️ **CORRECTED the same day — the trap is real, the discovery was a REDISCOVERY.**
NexusMind's contract validator **already strips these stamps** and reports clean:
`scripts/validate_production_contract.py:130`, `NEXUSMIND_STAMP_PREFIXES = ("_commerce_",
"_obituary_", "_violence_")`, merged 2026-08-14 — *before* this was "found". It was hit by
writing an ad-hoc validator instead of running the existing one. **So do not cite this as a
defect in their tooling.** It remains a live trap for **anyone hand-rolling a check over
`data/raw`**, which is the case this file exists for.

### From § `live_articles` is NOT the reader population

**This file said it was, from 2026-08-11 to 2026-08-16, and CLAUDE.md carried the
same line.** The view is **legacy and off the build path**. The site reads
`getArticlesForBuild` (`src/lib/db-articles.ts:270`, called at
`src/lib/data/pipeline.ts:83`) — a join over `article_filter_scores` + `articles` +
`summaries`, windowed on `ranking.maxAgeDays`, **returning only articles that have
been summarised**. Two comments inside ovr warn about this, one written after a
script made exactly this error. Verified here by grepping every `live_articles`
reference in `src/` and `scripts/`: outside the schema DDL there is one, a function
the build never calls.

### From § `duplicate_url` is NOT all re-reads

The two corpora give 9.85 and 12.5 per collection respectively — they differ only in rows
per day (13,016 vs 15,101), and the **rates agree to within 0.06pp**, which is the part
that carries. A single number from either side is false precision across two corpora at
different points in the pipeline. ⚠️ NexusMind's first per-day figure was **2× too high**
because the corpus span was read off a **file mtime** (`find_input_files` sorts by mtime)
rather than the `content_items_*` stamps — 07-12 → 07-26, 15 days, not 30. *Two orderings
in one head, one quoted as the other.*
