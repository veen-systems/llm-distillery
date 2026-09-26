# Session 2026-08-14 (late) — Contract A: the envelope, implemented

**Assignment:** implement the Contract A redesign (#112) — the (b) fields first, then
settle the shared envelope. **Five sessions in parallel** (llm-distillery, FluxusSource,
NexusMind, ovr.news, pipeline-atlas). **This session wrote no producer code and edited
no other repo**; it settled the envelope, coordinated, and kept the record.

**Decision record: `docs/decisions/2026-08-14-contract-a-envelope.md`.**
Five-repo detail: `docs/CONTRACTS_PLAN.md` § *Round 3*.

---

## What landed

⭐ **The envelope, in one line: the blocker was never `additionalProperties: false` —
it was assuming that DECLARING a field and EMITTING one are the same step.** Declare
the whole shape first, every block and property optional; after that every field ships
independently, in any order, with zero cross-repo coordination, and a typo inside a
block is still caught. Verified runtime-inert first: **no production path opens either
schema file.**

Verified against `origin/main`, not taken on report:

```
NexusMind/contracts/fluxussource-output.schema.json   version 1.20.0
root additionalProperties  false            ← the decision, intact
blocks   published · collected · fetch · content_meta · feed · origin · payload
published                  element · fabricated · had_timezone · precision · raw
language                   type: string     ← the collision, avoided
source_group declared      False            ← the hold, UNSPENT
required                   the original 8 keys, unchanged
```

NM#360 merged (`7d1086f`), NM#364 merged (`0652414`), 1,305 tests green.
**llm-distillery deployed nothing; sadalsuud unchanged at `b115fda`.**
⚠️ **FluxusSource deployed timestamp canonicalization to prod ~17:00** — theirs, not
this repo's, and it has a consequence recorded below.

## ⭐ The result: the redesign got SMALLER

| removed | why |
|---|---|
| the whole `language` block | already a live top-level **string** on 100% of rows, read as one at 8 production sites. Declaring it an object fails `type` on **every** row — optionality cannot help, the property is *present*, not absent |
| `source`, `item` | re-nesting a live flat field is a **relocation** — the one forbidden act |
| `published.instant` | **same moment as `published_date`.** No temporal information added, only an offset `origin.timezone`/`had_timezone` carry better — and the defect it was justified by is a **consumer bug** (ovr's JS reads naive as local) with a one-line fix |
| `collected.at`, `content_meta.raw_length`, `feed.title`, `feed.declared_language` | declared duplicates of live flat keys |

**Rule:** a new block carries only facts the row does not hold today. Declaring a new
name is safe; **relocating** is not; declaring a name that **already exists with a
different type** is fatal.

## The other repos

| | |
|---|---|
| **FluxusSource** | `content_meta.kind` built, moved to top-level, verified on 5,995 prod rows (5,739 RSS, 0 violations) — **undeployed**. Timestamp canonicalization **deployed**. |
| **ovr.news** | Three items committed: Contract B drop reader (`FilterStats.validation`, on `/ops/`), write-boundary test, archive comparator. ⚠️ **Backfill still NOT RUN** — and it is the *only* fix that reaches the delete boundary. |
| **pipeline-atlas** | Blind-spot section shipped with a mutation-tested verify command. Category G grain resolved. Units still **NOT ARMED**, correctly. |

## ⛔ Unassigned and likely to evaporate

- **The canonical-serialization defect** — biggest find of the day, **not part of the
  redesign, unfiled.** Four spellings of `published_date`, **2.805% non-canonical**,
  largest class **microseconds with no offset** (2,797 rows), **207 sources**. Must be
  fixed where the value is stored — one site in `ContentItem`.
- **Category G** — spec-ready, no implementer. **The canary** — nobody's, and it blocks
  W2.2.

## H-D1 opened and RESOLVED the same session

`memory/date-error-recency-boost-hypotheses.md`. `display_ranking.py` applies a flat
**1.3× boost under 24h** on `published_date`; the producer invents `now − 2h` for
date-less entries. ⭐ **Attributed to fabrication by a microsecond fingerprint** —
98.7% of ~2h-gap rows carry sub-second precision, which a timezone misparse cannot
produce. ⚠️ **The fingerprint was erased by the canonicalization deploy 20 minutes
later**; the archive keeps it. **H-D2 stays open**: NexusMind's 6h spike is *absent*
from the producer's window.

## The failure pattern, and it did not improve

**Roughly one wrong-sentence-beside-a-right-finding per exchange, all session, in every
repo.** Every underlying measurement was sound; every error was in the sentence
attaching a number to a claim. **Two were corrections of corrections.** Mine included:
"the gate is moot" (twice wrong), `published_date` "structurally cannot" carry an
offset (it declares `format: date-time`), "0% on api/social/data — 95.7% of rows"
(inverted the population), crediting the envelope with another commit's 4→1 fix, and a
foreclosure argument **my own envelope decision had dissolved**.

⭐ **The one that was PREVENTED rather than caught:** two owner answers on
`published.instant` existed at once and NexusMind held rather than take my relay.
**A relay cannot carry recency.**

## Next session

`docs/TODO.md` top block. First: **`fabricated` + `had_timezone` + `raw` together** —
not `fabricated` alone, because the accidental fingerprint that used to separate the
causes is now gone. Then deploy `content_meta.kind` (retires #93's floor). Then
`clock_source`, `fetch.*`, `element`, `precision` last.
