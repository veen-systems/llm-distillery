---
name: nexusmind-data-sources
description: What each NexusMind data artefact excludes — filtered_*.jsonl also drops source-type-excluded rows, data/raw is pre-enrichment
metadata:
  type: reference
---

# NexusMind Data Sources

## ⚠️ `collected_date` IS NOT UNIFORMLY UTC — 8 of 768 sources carry a +2h skew (FS#176, 2026-08-14)

**Standing rule until FS#176 lands. Archives are NOT being backfilled**, so this
applies to `data/current/` *and* to every archived run, indefinitely.

`collected_date` is stamped from the **host local clock (CEST = UTC+2)** for:

```
newsapi_general · github · hackernews · stackoverflow · ourworldindata
NASA APOD · two Dev.to author-named sources
```

The other ~760 sources are UTC. **`published_date` is unaffected.** So **any analysis
treating `collected_date` as uniformly UTC is wrong by 2h on that slice** — and after a
DST change it is wrong by 1h instead, because the skew tracks the host's offset.

⚠️ **`94e7337` (canonical timestamps) made this HARDER to see, not easier.** The skewed
value used to carry microseconds and look visibly odd; it now has the **identical shape**
to a correct UTC value. Only cross-source comparison *within a single run* exposes it.

⚠️ **Do not detect the skew by comparing a source to the run median** — that is what I
did, and it under-measured the offset as `+1.98h` because `newsapi_general` **runs first
in the cycle**, so the measurement was *offset minus head start*. Compare against the
earliest `collected_date` of a known-UTC source in the same run, or just apply the
2h correction from the source list above.

⭐ **Downstream consequence worth knowing**: fabricated-in-UTC + collected-on-local-clock
produces a **4h** `collected − published` gap, not 2h — which is why FS#173's 2h
detection window undercounts fabrication. See
`memory/date-error-recency-boost-hypotheses.md`.

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
`if result["passed_prefilter"]` (NexusMind `scripts/main.py`), so the file is 100%
passers by construction. Already in CLAUDE.md.

**The one that is easy to miss:** NexusMind's `src/scoring/source_filter.py` sets
`passed_prefilter = False` *after* scoring, for articles whose
`metadata.quality.type_classification` is in the filter's
`excluded_source_types`. All six production filters run this in enforce mode
(`shadow_mode: false`). Those articles **were scored** — so anything reading the
GPU scorer's log counts them — but they never reach the file and never reach
ovr.news.

### The exclusion list is NOT the same across filters, and one label matters to exactly one filter (measured 2026-08-12)

Read off the deployed configs on sadalsuud. **Only `investment_risk v6` excludes
`academic`, and only it excludes `proxy_aggregator`**; the other five exclude
`code_repo`, `developer_aggregator`, `firehose_aggregator`, `eval_aggregator` and
nothing else. `uplifting v7` has no `source_filter` block at all.

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

⚠️ **NexusMind's `scripts/stamp_census.py:20` says `type_classification` is
"stamped, ZERO consumers → an A/B".** That is contradicted by the enforcing
caller at `scripts/main.py:1313` with `shadow_mode: False`. This file is right and
that note is stale — do not reason from it.

⚠️ **And this file is the wrong instrument for measuring a
`type_classification` change's effect on scores**, because the rows whose
treatment changed are exactly the rows that appear or disappear from it. Use the
pipeline's own excluded counts per cycle, or
`NexusMind/scripts/validate_shadow_exclusions.py`.

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

### ⚠️ And it is not producer bytes either — NexusMind WRITES BACK into it (2026-08-15)

Found by the NexusMind session while validating Contract A, and it is a second,
independent reason not to treat `data/raw/` as "what FluxusSource delivered":

**NexusMind's own preprocessing stamps into the raw files.** `src/preprocessing/commerce.py`
writes `_commerce_score` / `_is_commerce` / `_commerce_model`; the obituary path writes
`_is_obituary` / `_obituary_score` / `_obituary_model`. So a "raw" row is
**post-our-own-stamping**, and every one of the 4 schema-violation classes measured against
`data/raw` over 10,677 rows was **ours, not the producer's**.

⭐ **The shape worth carrying, because it is how the error survived:** the local corpus
also **predates `source_group`**, which is emitted on every delivered row and present on
**0** of these. So **the one violation class that should appear is absent, while four that
should not are present — and they partly cancel into a plausible total.** A total that
looks reasonable is not evidence that its parts are.

- **Cheap detector:** a violation whose key starts with `_` is ours, not theirs.

⚠️ **CORRECTED the same day — the trap is real, the discovery was a REDISCOVERY.**
NexusMind's contract validator **already strips these stamps** and reports clean:
`scripts/validate_production_contract.py:130`, `NEXUSMIND_STAMP_PREFIXES = ("_commerce_",
"_obituary_", "_violence_")`, merged 2026-08-14 — *before* this was "found". It was hit by
writing an ad-hoc validator instead of running the existing one. **So do not cite this as a
defect in their tooling.** It remains a live trap for **anyone hand-rolling a check over
`data/raw`**, which is the case this file exists for.

**The canary's real constraint is corpus VINTAGE, not contamination:** local `data/raw`
predates `source_group`, so a check run there misses the emitted-undeclared class entirely
regardless of stamp handling. Point it at sadalsuud's delivered bytes — a mirror exists at
`~/mirrors/sadalsuud/local_dev/FluxusSource/data/current/collection_*/` (52 collections,
165,107 rows).

⭐ **And `source_group`'s 20.5% presence is a DATE, not a rate.** It landed mid-window on
**2026-08-13 16:57 — 0% before, 100% after.** A presence-based check must key on **run
date**; reading 20.5% as a sampling rate would make every threshold derived from it wrong.

## Related

- `memory/prefilter-length-floor-hypotheses.md` — the measurement these came out of
- `memory/gotcha-log.md` — session entries
- CLAUDE.md Hard Constraints — the `filtered_*.jsonl` passers-only rule

---

## ovr.news `ovr.db` — the published set (added 2026-08-11)

`~/local_dev/ovr.news/data/ovr.db` on sadalsuud, ~231 MB. **This is the only DB
that answers "did a reader see it?"** — everything in NexusMind answers "was it
scored?" or "did it clear the op-point?", which are different and much larger
populations.

### ⛔ `live_articles` is NOT the reader population — corrected 2026-08-16

**This file said it was, from 2026-08-11 to 2026-08-16, and CLAUDE.md carried the
same line.** The view is **legacy and off the build path**. The site reads
`getArticlesForBuild` (`src/lib/db-articles.ts:270`, called at
`src/lib/data/pipeline.ts:83`) — a join over `article_filter_scores` + `articles` +
`summaries`, windowed on `ranking.maxAgeDays`, **returning only articles that have
been summarised**. Two comments inside ovr warn about this, one written after a
script made exactly this error. Verified here by grepping every `live_articles`
reference in `src/` and `scripts/`: outside the schema DDL there is one, a function
the build never calls.

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

⛔ **What has NOT changed: `live_articles` is still not the reader population.** It
remains off the build path, and its only reader `getLiveArticles()`
(`db-articles.ts:183-186`) is itself uncalled. Keep it out of your denominators for
that reason, not for the drift reason.

**Use the build query, or the `articles` table as a superset.** A superset claim is
the robust move: if a population is 0 in `articles`, it is 0 in any window over it.

```bash
# superset — every article ovr ever stored (22,191 rows, 2026-04-04 → 08-16)
ssh sadalsuud 'sqlite3 -readonly ~/local_dev/ovr.news/data/ovr.db "SELECT COUNT(*) FROM articles;"'
# what the deployed view ACTUALLY is, before quoting any count off it
ssh sadalsuud 'sqlite3 -readonly ~/local_dev/ovr.news/data/ovr.db "SELECT sql FROM sqlite_master WHERE name=\"live_articles\";"'
```

Tables that matter: `articles` (the superset), `article_filter_scores`, `summaries`,
`archive_articles`, `editorial_decisions`.

**What it excludes:** any `live_articles` window holds only the live window, so items
that rotated out are absent — it cannot answer historical questions. `archive_articles`
is the other half and was **not** used in the 2026-08-11 panel.

**Trap:** `articles.content_hash` exists, is written by the upsert, and is **0 of
22,191 rows non-null** — read by nothing. The producer's `content_hash` does not reach
this DB (#119).

### ⛔ `duplicate_url` is NOT all re-reads — ~0.44–0.50% of rows are distinct articles (NM#390)

**Added 2026-08-16.** `_normalize_url` **strips the query string**, so for any publisher
whose article URLs differ *only* by query parameter, every article collapses to one
normalised URL and all but the first are dropped as `duplicate_url`. Different titles,
different ids, same stripped URL.

**Measured twice, independently, and the rates agree:**

| side | lost | of | rate |
|---|---:|---:|---|
| NexusMind `data/raw`, 87 deliveries | 857 | 195,233 | **0.439%** |
| FluxusSource delivered rows, last 6 collections | 75 | 15,101 | **0.497%** |

Same sources both times: `science_plos_one`, `disaster_alerts_gdacs_alerts`,
`china_solidot`, the `hackernews` feeds. `journals.plos.org/plosone/article` alone
carries **244 distinct ids with 244 distinct titles**; one survives.

⚠️ **Quantity — quote the BRACKET, not a point estimate.** ~**10–12 newly lost articles
per collection**, **800–1,000 distinct articles never scored per fortnight**. Not 857 ×
cycles: like the `too_old` population these rows are never marked processed, so the same
ones are re-dropped every load rather than the loss accumulating.

The two corpora give 9.85 and 12.5 per collection respectively — they differ only in rows
per day (13,016 vs 15,101), and the **rates agree to within 0.06pp**, which is the part
that carries. A single number from either side is false precision across two corpora at
different points in the pipeline. ⚠️ NexusMind's first per-day figure was **2× too high**
because the corpus span was read off a **file mtime** (`find_input_files` sorts by mtime)
rather than the `content_items_*` stamps — 07-12 → 07-26, 15 days, not 30. *Two orderings
in one head, one quoted as the other.*

**Prefer the reader-window form when this travels**: *"roughly eight hundred to a thousand
distinct articles never scored, and therefore never available to ovr.news, in any given
fortnight."* It is the only phrasing with one interpretation; "857" reads as a per-cycle
catastrophe or a one-off depending on the reader.

⛔ **It is self-concealing: the drop lands in `duplicate_url`, which reads to an operator
as "correctly removed a re-read".** Never treat that counter as a clean measure of
re-reads, and never use "rows that reached scoring" as a denominator without subtracting
this.

⭐ **The indictment is of the method, not the counter.** Two sessions spent an afternoon
building instruments *around* `duplicate_url` — one built a collision check on it, the
other reordered the check that feeds it, and both compared its values across two code
versions to four significant figures — **and neither asked what was inside it.** We were
treating an aggregate over an unopened category as an observation. Before comparing a
counter across versions, open it once.

**Not caused by, and not worsened by, the 2026-08-16 id-before-url reorder** — these rows
carry distinct ids, so the in-batch check never fires and the URL check drops them under
both orderings. Confirmed by replay.

⚠️ **If anyone fixes it: measure old-vs-new KEPT SETS on identical input, never counter
deltas.** `duplicate_url` falling is the *intended* effect and cannot distinguish a good
fix from one that simply stops deduplicating.

**Trap:** `weighted_average` in `live_articles` is the **NORMALIZED** score, not
raw. A row reading 8.95 can have per-dimension raws of 4.4–7.2. Normalization is
rank-in-batch by design (ADR-014). Do not compare it to an op-point. Note the build
query reads `afs.weighted_average` from `article_filter_scores`, a *different column
in a different table* from `articles.weighted_average`.

**Trap:** ovr#275's resolver can rewrite article URLs, so matching a source by URL
pattern may undercount. Cross-check by `source` as well — on 2026-08-11 both routes
independently gave 39 Google News articles, which is what made the number usable.

**Scale to expect:** a population that is 25.7% of the collected corpus and 16.1%
of what a filter surfaces can still be 1.1% of what is published. Surfacing share
and reader exposure are different quantities — conflating them produced a retracted
"96% removed downstream" claim.
