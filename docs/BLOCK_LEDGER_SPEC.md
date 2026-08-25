# Block ledger — modelling what the pipeline throws away

**2026-08-23.** Owner requirement: *"all data is properly modelled. Gets saved to disk properly
too. We may need it later."*

Everything below was verified against the running box, not inferred.

---

## ✅ IMPLEMENTED 2026-08-23 (NexusMind, offline-verified, NOT yet deployed)

`src/archiving/block_ledger.py` + wiring in `scripts/main.py`. **Write-only: no admission
decision changes.** Rollback = `pipeline.block_ledger.enabled: false`.
Verify with `python3 scripts/verify_block_ledger.py`.

Offline proof over a real production input (`content_items_20260823_161050.jsonl`, 3,074 rows,
six filter loops): **428 unique blocked articles**, 404 carrying full content, every row
`placements: 6`, and the placement tallies reconcile exactly —
`commerce 1,698 = 283 × 6`, `obituary 330 = 55 × 6`, `too_old 396 = 66 × 6`,
`duplicate_title 144 = 24 × 6`. All 428 rows validate against
`contracts/article-record.schema.json` v0.3.0, with a negative control proving the schema is
not merely permissive.

**Three deliberate deviations from §3 below, each with its reason:**

1. ⭐ **The row is written in the prescriptive `nexusmind.disposition` shape, not the flat
   `_blocked_by`.** Owner ruled the record prescriptive the same day. Blocked rows are new data
   with no reader, so the new shape is free — and `nexusmind.{disposition,gates}` is
   **dual-written onto kept rows too** (also free: no reader outside NexusMind touches the gate
   stamps), so the kept and blocked populations can be compared with one reader.
2. ⛔ **"Mark blocked articles processed" is NOT part of this change.** It alters admission
   behaviour; the ledger does not. Instead the ledger keeps its own written-id index, so only
   genuinely new blocks are written. Without one it would rewrite ~19,000 rows every four hours,
   because a blocked article is re-read from `data/raw` on every cycle until its raw file expires.
   ⚠️ The index is **rebuildable from the ledger rows themselves** — it sits in a directory a
   cleanup pass sweeps and is protected there only by its `.json` extension, and *unlikely* is not
   the same as *recoverable*.
3. **`already_processed` produces no row.** Those articles are not lost — they are in `filtered/`
   and the archive — and at ~22,000 per cycle they would drown every real event.

### ⚠️ `placements` is NOT "how many lenses saw this article" — DIAGNOSED 2026-08-25

The smoke run made every row `placements: 6` and that read as an invariant. Production
found three exceptions in 194,405 rows — `{6: 194403, 3: 1, 1: 1, 5: 1}` — and both
mechanisms behind them are benign, but they change what the field means.

`placements` is `len(per_filter)`, and `per_filter` gets an entry only when a filter
loop drops the article **for a reason the ledger records**, in the cycle where the
article was **first** recorded (the written-id index means it is never revisited). So
it is *how many lenses filed a ledger-reason block for it that one cycle* — a number
that can legitimately be lower than the lens count, in two ways:

1. **An earlier loop dropped it for a NON-ledger reason.** `already_processed` is
   per-filter state and is deliberately not a ledger reason (item 3 above).
   `central_asian_kun_uz_275be95d0823` is marked processed in exactly `solutions`,
   `uplifting` and `investment_risk` — the first three in `enabled_filters` order,
   all on 2026-08-23 — and in none of the last three, which recorded it as `too_old`
   the next day. **`placements: 3`.** Verified against the per-filter stores
   (`data/raw/.processed_ids_*.json`), an instrument independent of the ledger.
2. ⭐ **The freshness cutoff MOVES BETWEEN LOOPS.** `load_articles` computes
   `cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_article_age_days)`
   **once per filter**, so the six loops of one cycle run against six cutoffs, seconds
   apart. An article whose `published_date` sits inside that spread is fresh for the
   earlier loops and `too_old` for the later ones. Both remaining exceptions have
   exactly that signature: published **12 s** and **6 s** before the cutoff in force
   when the ledger first recorded them, and their `per_filter` maps are the **last 1**
   and the **last 5** entries of `enabled_filters` order. All three anomalies are
   suffixes of that order; for random subsets that is a ~1-in-720 coincidence.

Consequences: **never divide a ledger row count by the lens count**, and never read
`placements < N` as a defect. Being fresh in an early loop does not mean the article
was scored there either — `shuffle_input` plus `max_items_per_filter` decides that
separately, and neither of these two was ever scored by any lens.

⚠️ **`placements` becomes 5, not 6, from 2026-08-25** — `investment_risk` is paused.
`scripts/verify_block_ledger.py` prints the histogram and asserts nothing about it, so
this changes no check; anything downstream that hard-codes 6 is now wrong.

⚠️ **What a blocked row structurally cannot tell you.** §3 wants every gate's verdict so that
gate overlap is answerable. Stage ordering caps that: an article dropped in `load_articles` was
never seen by `violence_promotion`, which stamps later. Those rows carry
`gates.violence_promotion.stamped: false` — *not judged*, distinct from *cleared*, and the schema
enforces the distinction. Measured on the smoke run: **all 428 rows**.

---

## 0. The article record: 132 fields, and no definition of it anywhere

`scripts/stamp_census.py --cycles 2` over 25,122 production rows: **132 distinct stamp fields.**
They *are* saved — on kept rows, in `data/filtered/`, and into the 730-day archive. What does not
exist is a **definition**. Contract A describes the producer's *input* fields; Contract B declares
`metadata` with zero properties. **Nothing declares the layer NexusMind adds.** The census
discovers it empirically, and finds **59 problems**.

The layer, by family:

| family | examples |
|---|---|
| gate verdicts | `_commerce_score` / `_is_commerce` / `_commerce_model`, same triple ×obituary ×violence |
| lens scoring | `nexus_mind_attributes.<lens>.{scores.*, raw_weighted_average, weighted_average, tier, version, normalization_method, gatekeeper_applied, passed_prefilter, cap_applied, prefilter_reason}` |
| provenance of time | `published.{raw, element, precision, had_timezone, fabricated}`, `collected.clock_source`, `fetch.at` |
| fetch/encoding | `fetch.{charset_declared, charset_detected, charset_detected_confidence, charset_used}`, `metadata.robust_parsing_used` |
| content shape | `content_meta.{kind, echoes_title}`, `content_quality.{pass, score, flags, reason}`, `original_content`, `content_hash` |
| enrichment | `enriched`, `enriched_at`, `original_content_length`, `pre_enriched`, `short_content_cap_applied` |
| source/identity | `source_group`, `origin.{country, region, timezone}`, `resolved_url`, `display_rank`, `pipeline_run_id` |
| features | `metadata.primary_literature.{detected, detector_version, evidence}`, `metadata.quality.*`, `image_analysis.*` |

### ⭐⭐ The finding that matters most, and today's flip caused half of it

```
_is_commerce   100.0%   1 distinct   CONSTANT 'False' across 25,122 rows
_is_obituary   100.0%   1 distinct   CONSTANT 'False' across 25,122 rows
_is_violence_promotion  100.0%  2 distinct
```

⛔ **`_is_commerce` and `_is_obituary` are not broken stamps — they are constant by
CONSTRUCTION.** The positives were dropped before persistence, so the saved population is the
gate's negatives and nothing else. **You cannot learn anything about either gate from the record,
ever, because the record contains only what it let through.**

⛔⭐ **`_is_violence_promotion` had 2 distinct values ONLY because it was in shadow. As of
2026-08-23 it is enforcing, so from the next cycle it becomes constant-`False` like the other
two.** Turning enforcement on **destroyed the only gate signal visible in the persisted record**,
and nobody planned that. **The block ledger (§3) is what restores it.** This is the strongest
argument for building it, and it is now time-sensitive rather than theoretical.

### Other census findings worth a decision, not just a note

- **Declared and never observed (3):** `enriched`, `enriched_at`, `short_content_cap_applied`.
  ⚠️ The script's own warning applies — rare fields are indistinguishable from dead ones at
  `--cycles 2`; re-run at `--cycles 12+` before calling any of them dead.
- **Never populated (4):** `content_quality.reason`, `nexus_mind_attributes.*.cap_applied`,
  `nexus_mind_attributes.*.prefilter_reason`, `image_analysis.extracted_image_dimensions`.
  ⭐ `prefilter_reason` being empty on 100% of rows is the NM#284 shape restated — the field
  exists for a prefilter that has not run in production since 2026-02-10.
- **Populated 100%, no consumer:** `_violence_promotion_score`, `pipeline_run_id`,
  `collected.clock_source`, `content_meta.echoes_title`, `feed.ttl_declared`, `fetch.charset_*`,
  `nexus_mind_attributes.*.{obit_pattern_count, original_content_length, should_translate,
  scores.<dims>}`.
- **`nexus_mind_attributes.*.scores.<dims>` — the per-dimension oracle scores — has NO consumer
  outside the writers.** That is the most detailed thing the pipeline computes.

### What to do about it

Write the definition. Not a contract (no counterparty) — a **declared field register** for the
NexusMind-added layer, one row per field, carrying: name, type, writer, populated-%, **and an
explicit status** from a closed vocabulary: `LOAD-BEARING` / `DIAGNOSTIC` / `DECLARED, NO KNOWN
CONSUMER` / `DEAD — SCHEDULED FOR REMOVAL`. `CONTRACTS_PLAN.md` W2.3 already calls for exactly
this shape for the 34 undeclared *metadata* keys; this is the same job for the other ~100.

⛔ **The register must record `pop%` and `distinct` beside each field**, because those two
columns are what turned "we stamp `_is_commerce`" into "that stamp can never be informative".
A field register without a population column is a list of intentions.

## 1. What is ALREADY right — do not rebuild this

| | measured |
|---|---|
| hot storage | `data/filtered/*` 14 days (`temporal.cleanup_older_than_days: 14`), 1.6 GB per lens |
| **archive** | `data/archived/*.tar.gz`, **19 GB, 17 monthly tarballs back to 2025-10** |
| archive retention | **730 days** (`temporal.archive_retention_days`) |
| archive throughput | **46,719 new articles in the last cycle; 779,224 in the current month** |
| raw data | archived too (`archive_raw_data`) |
| disk headroom | `data/` 30 GB on a 466 GB volume, **390 GB free (13% used)** |

⭐ **Kept articles are already durably modelled and stored, with every gate stamp on them**
(`_commerce_score`/`_is_commerce`/`_commerce_model`, same triple for obituary and violence).

⛔ **Correction to an earlier claim in this session:** 4 of 9 class-A articles were reported
"aged out of retention" because they were absent from `data/filtered/`. **They are in the
archive** — `tar xzOf data/archived/nexusmind_2026-08.tar.gz | grep <id>` returns 6 hits, one per
lens. *Absent from hot storage is not absent.* Search the archive before calling data lost.

⭐ **Disk is not the constraint and must not be used as an argument.** 390 GB free.

## 2. The gaps — small, specific, and both about things that never reach `data/filtered/`

**G1. Blocked articles are the ONLY class of data that is permanently lost.**
`FilteredArchiver` reads `self.filtered_dir`. An article dropped in `load_articles` never enters
that directory, so the archiver cannot see it and no archive contains it. Per cycle that is
~19,000 commerce, ~3,400 obituary, ~3,000 duplicate-title and 74 violence — gone with only a
counter surviving.

**G2. `data/prefiltered_out/` is in neither the cleanup path nor the archive path.**
It survives because it is 6.1 MB and nobody purged it — **luck, not policy.** The moment it
carries `content` (which §4 requires) it becomes GB-scale, and the first person to look for disk
will delete the one corpus that made #82 auditable.

## 3. The record — one shape, written once

A block event is a **ledger row**, not a contract (no counterparty; see `docs/CONTRACTS_PLAN.md`
— Contract A is producer→NexusMind, Contract B is NexusMind→ovr, and a blocked article crosses
neither).

```jsonc
{
  // identity — enough to find the article again anywhere
  "id": "south_african_herald_zw_5e7a6674c6d4",
  "title": "...", "url": "...", "source": "...", "source_type": "...",
  "language": "en", "published_date": "...", "collected_date": "...",
  "content_hash": "...",
  "pipeline_run_id": "674f5bd1-...",

  // ⛔ FULL content, never an excerpt. The 2026-08-23 audits were both crippled by
  // 300-char excerpts; adjudicating a block needs the article.
  "content": "...",

  // the decision
  "_blocked_by":    "commerce_blocked",   // the winning reason
  "_blocked_at":    "2026-08-23T16:46:22Z",
  "_blocked_stage": "load_articles",      // or "violence_enforce" — two different mechanisms

  // ⭐ EVERY gate's verdict, not just the winner. The checks are ORDERED and the first
  // one wins, so without all three you can never ask "would obituary have caught it too?"
  // or "how much do the gates overlap?" -- questions that decide whether a gate earns its cost.
  "_commerce_score": 0.97,  "_is_commerce": true,  "_commerce_model": "v1",
  "_obituary_score": 0.01,  "_is_obituary": false, "_obituary_model": "v5",
  "_violence_promotion_score": 0.00, "_is_violence_promotion": false, "_violence_model": "v1"
}
```

**Why each modelling choice:**
- **Winner + all verdicts.** Ordering means `commerce` is checked before `obituary`; recording
  only the winner makes gate-overlap unanswerable forever.
- **Model version per gate.** A retrain must be able to ask *which model made this call*.
- **Stage.** There are genuinely two drop mechanisms and they behave differently
  (`_is_duplicate` returns a reason string; `_enforce_violence_promotion` returns nothing).
- **Written exactly once**, because the owner ruled blocked articles are marked processed and
  never reprocessed. That also removes the ~22,000 pointless re-evaluations per cycle.

⚠️ **Vocabulary is closed and must be declared**: `superseded_in_batch`, `duplicate_in_batch`,
`already_processed`, `duplicate_url`, `commerce_blocked`, `obituary_blocked`, `duplicate_title`,
plus a new `violence_blocked` (which today produces **no reason string at all** — it must be
made to emit one).

## 4. Where it goes on disk

```
data/blocked/blocked_<ts>.jsonl        ← hot, same cadence as filtered/
data/archived/blocked_<YYYY-MM>.tar.gz ← archived on the SAME path as filtered/, 730 days
```

**Three requirements, each because something already went wrong without it:**

1. ⛔ **The blocked sink must be added to `FilteredArchiver`'s inputs.** If it is only written
   and not archived, it is G1 with extra steps — deleted at 14 days by the same cleanup.
2. ⛔ **`data/prefiltered_out/` must be brought under the same policy** or folded into
   `data/blocked/` outright. Violence's flagged files are the precedent for both the value and
   the fragility.
3. ⛔ **Seed the ledger without content on first run.** The backlog is ~22,000 already-blocked
   articles; writing them all with content is a one-off spike for rows whose content is already
   in `data/raw` archives. Capture content from first-block onward.

**Cost:** once blocked articles are marked processed, the standing ~22,000 collapse into
`already_processed` and only genuinely new blocks are written — order 300–500/cycle at ~3 KB,
so **single-digit MB/day, low single-digit GB/year.** Against 390 GB free this is not a
tradeoff.

## 5. What this is NOT

- **Not a contract.** No counterparty. Add the *kept-row* gate stamps to `CONTRACTS_PLAN.md`
  W2.3 ("declare the undeclared metadata keys, with status") instead — and note that they are
  measured **not to cross into ovr at all**: 0 of 6,000 `ovr.db` rows carry any gate stamp,
  because `summarize.ts` projects `metadata` down to `{quality}` on ingest.
- **Not a reason to keep bulk rows longer.** Hot storage at 14 days plus a 730-day archive is
  already sound. The gap is a *class* of data that never enters the archive, not the window.
