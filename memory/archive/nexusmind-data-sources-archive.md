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
