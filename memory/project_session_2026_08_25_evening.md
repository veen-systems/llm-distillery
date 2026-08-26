# Session 2026-08-25 evening → 08-26 morning — the wait that found five defects

**No spend, no model, no filter training.** All code in NexusMind; this repo carries
the specs, the evidence and the memory. Started as "fix things while we wait for the
20:03 cycle to verify migration step 3"; the cycle never ran, and the reason was ours.

## What was verified (the original purpose)

Step 3's dual-write, deployed 2026-08-25 17:32, **VERIFIED LIVE 2026-08-26** against
the 00:00 and 04:00 cycles — both "All smoke tests passed":

1. `filtered_20260826_051337.jsonl` first row →
   `['content', 'corroboration', 'disposition', 'gates', 'run', 'signals']`.
2. `verify_block_ledger.py` **exit 0** — 10 files, **205,427 rows**, all conformant to
   `article-record.schema.json` **v0.6.0**.
3. Register regenerated, **exit 0**, every observed field classified — **125 owned
   fields** in the window `filtered_20260823_204645 .. filtered_20260826_051752`
   (109 was the 08-25 window; the count is a property of the WINDOW).
4. `placements per row` `{6: 194403, 3: 1, 1: 1, 5: 11022}` — the pause's own proof.

⭐ **And last session's own verifier, run post-cycle, exit 0** —
`NexusMind/scripts/research/verify_pause_and_hoist.py` (committed as that name; the
`/tmp/verify_deploy_20260825.py` the index cited never existed under that name in any
repo). It adds what the four checks did not: the namespace on **200 of 200 sampled
rows** rather than the first one, 5 filters scored and the paused one absent, the
newest flush at `{5: 3270}`, and **the Aegis export stopped** — `narrative_risk.json`
last written 2026-08-25 17:18:50, before the pause took effect.

## ⛔ The incident: a two-line config change had a THIRD file

`nexusmind.service` FAILED 2026-08-25 20:09:54; the 20:03 cycle never ran.

```
ERROR: smoke fixture references filters not in app.yaml enabled_filters: ['investment_risk']
```

`deploy/smoke_test_articles.jsonl` still named the paused filter and
`deploy_filters.sh` is fail-closed on that mismatch (the smoke test would 404 against
`/filter/investment_risk/score`). **The gate is the control working.** Fixed by
removing the fixture row, not by weakening the gate (`5c94a0e`) — the reversible
direction, since a forgotten un-pause now WARNs instead of failing. Then moved earlier:
a unit test (`adcf3c9`), **validated by running it against `c7af891`, the commit that
actually broke production, where it fails with the gate's own message.**

⭐ **16th occurrence of "prove the outcome changed"**, and the sharpest so far: the
outcome check existed, was named in advance, and was **deferred to the very cycle that
then never ran**. The plan contained its own gap. No data lost — collection succeeded,
the next cycle reads the whole 14-day window.

## Five defects, four of them found by running things rather than reading them

| # | Defect | Found by |
|---|---|---|
| 1 | `source_unreliable`: rare, not dead — and its migration target did not exist | tracing a ghost to two repos upstream |
| 2 | `other_sources`: 51.4% of entries carry hardcoded `unknown`/`null` | the same trace, incidentally |
| 3 | `.processed_ids_*.json` inside a deletion path (`pathlib` glob matches dotfiles) | asking what the cleanup sweep can reach |
| 4 | the smoke fixture / `enabled_filters` pair | production, three hours later |
| 5 | `x-intermediate` not covering its children (3 false ghosts on 207,270 rows) | running the shipped script during verification |

**1 — `source_unreliable` is RARE, not dead.** Needs `source_tier == "override"` AND
`credibility_score < 3.0`. `override` = a curator entry in FluxusSource
`config/domains/credibility.yaml`: 733 entries, exactly **5** below 3.0 (infowars 1.0,
rt.com / sputniknews / sputnikglobe / tass 2.0); **3 of those 5 are `enabled: false`
feeds** on editorial grounds (unblock = NM#253), the other 2 are in no source config.
Over **237,132 distinct articles** (510 files, 08-11 .. 08-25) `override`'s minimum
credibility is **3.8** and all **204** sub-3.0 articles are `verified` tier, which the
predicate excludes. **The two halves of the AND are anti-correlated by policy.** Ships
as `x-rare` + FALSIFIER (Contract B 1.18.2); the census now prints such a field as
ANSWERED rather than re-asking it every run.
⛔ **The keeper**: the record schema's `corroboration` is `additionalProperties: false`
and the flag was declared in neither that schema nor the dual-write's copied set — **the
first row ever to carry it would have been the first row to fail validation.** Rule:
*when you establish a field is rare rather than dead, check its target still exists —
rarity is why nobody exercised the path.*

**2 — `other_sources` has two shapes.** A cross-run entry hardcodes
`source_tier: "unknown"` / `credibility_score: null` because the saved cluster record
never persisted quality: **104,201 of 202,893 entries (51.4%)** over 110,645 articles,
and **97.7% of the field's `unknown` is bookkeeping**. NexusMind#404 filed for the
stored-shape question.

**3 — a data sweep reached state.** `pathlib.Path.glob("*.json")` matches dotfiles;
`glob.glob` does not. A running filter rewrites its store every cycle so it never aged —
**the population that made the bug look impossible is the one that hid it.** A PAUSED
filter's store does age: `investment_risk`'s would have been deleted ~2026-09-08,
turning a two-line un-pause into re-scoring the whole window.

**5 — a mark is a statement about a SUBTREE.** `_corroboration` was excluded; its three
declared children went on printing as ghosts. Tests all passed — they were written from
the same model as the code.

## The `placements` diagnosis (three anomalies, two mechanisms, both benign)

`placements` is **not** "how many lenses saw this article" — it is how many filed a
LEDGER-REASON block in the cycle where it was FIRST recorded. (a) An earlier loop
dropped it for a non-ledger reason: one article is marked processed in exactly the first
three filters and none of the last three, verified against
`data/raw/.processed_ids_*.json`, an instrument independent of the ledger. (b) ⭐ **The
freshness cutoff moves between loops** — `load_articles` recomputes
`now − max_article_age_days` once per filter, so one cycle runs against six cutoffs
seconds apart; the other two published **12 s** and **6 s** before the cutoff in force.
All three maps are suffixes of `enabled_filters` order (~1-in-720 by chance).
⚠️ Now that normal is 5, the pre-pause 5-placement anomaly is no longer distinguishable.

## Also shipped

- **#123 CLOSED** — the memory index is split by lifetime: topic pointers + the newest
  **four** session entries; older ones **MOVED VERBATIM** to `memory/session-log.md`.
  **26,868 → 14,443 chars**, 60 bullet lines before and 60 after. The guard now counts
  entries and says MOVE, not trim (a WARN, never a FAIL — a hard failure would land on
  whoever is writing the entry).
- **NM#403** — off-site backup extended to `blocked_*` and `raw_*`, verified against a
  stub rclone (all three `--include` flags on the real command line). First
  `blocked_2026-08.tar.gz` ~2026-09-07.
- ⛔ **"Nothing prunes the ledger index" was WRONG** — `_prune_index` runs every flush at
  30 days; the growth seen so far is the fill phase, plateau ≈45 MB.
- **#132** filed: `prefiltered_out/` is in neither cleanup nor archive. **Not redundant
  with the ledger** — 414 flagged rows vs 39 blocked in the same cycle, so **90.6% is the
  flagged-but-KEPT shadow population** the ledger by construction never holds.
- **augmented-engineering#36** — evidence issue: 1,485 green tests, 0 defects found by
  them, 2 found by running the artifact on production.

## Next session

1. **NM#404** — decide whether the stored `other_sources` shape should carry real quality.
2. **#132** — archive `prefiltered_out/` or document leaving it; doing nothing currently
   reads as the second.
3. **NM#403 stays open** until a weekly run has uploaded a blocked tarball (~09-07).
4. **CLAUDE.md is 39.3k of a 40k warn** and de-padding reclaims nothing (12 chars). The
   next structural session has to cut content, not whitespace — same shape as #123, one
   layer up.
