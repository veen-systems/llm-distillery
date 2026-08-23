# Block ledger — modelling what the pipeline throws away

**2026-08-23.** Owner requirement: *"all data is properly modelled. Gets saved to disk properly
too. We may need it later."*

Everything below was verified against the running box, not inferred.

---

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
