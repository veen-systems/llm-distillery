# Session 2026-08-15 (late) — Contract A handed out and built; three of my calls corrected

**Nothing deployed, no filter package touched, no spend.** Commits `1c02bf8` (records)
and this one. This repo wrote **no code** — its whole contribution was relay, verification
and record-keeping.

---

## What the session was

The owner authorized two peer repos to write code **through this session** — the thing the
previous session's plan explicitly said llm-distillery could not do on its own. Scope was
pinned before anything was sent:

| session | standing | outcome |
|---|---|---|
| **nexusmind** | AUTHORIZED — W0 shape pass | Contract A **1.21.0 → 1.23.0**, 43 contract tests, suite 1319, 16 mutations all biting. **Uncommitted.** |
| **fluxussource** | AUTHORIZED — Track A | `published.fabricated`+`had_timezone`+`raw` built, 1283 tests, 788 live rows clean. **Uncommitted, undeployed.** |
| **ovr-news** | information only | Answered the backfill inquiry; **no work assigned** |
| **pipeline-atlas** | information only | Delivered both owed Category G spec lines |

Two items went out at deliberately **different standing**: `content_meta.error` as an owner
**ruling**, `published.had_timezone` nullability as a **recommendation**. Every message
carried *"if your session holds a more recent owner answer, yours wins"* — **a relay cannot
carry recency.**

---

## ⭐ THE FINDING: three of my own calls were wrong, and none failed where I was looking

**Every one was caught because the receiving session RE-DERIVED instead of adopting.**
This is the second consecutive session with that shape; it is now the reliable mechanism,
not a lucky one.

1. **`content_meta.error` "(string, nullable)"** — the owner ruling settled *whether to
   declare*. The type was this repo's **parenthetical in a table cell, inheriting authority
   by adjacency** from the ⛔ ruling beside it. NexusMind asked rather than assumed;
   `return {'error': type(exc).__name__}` has no null branch, so nullable would oblige a
   consumer branch that can never be tested. **A formatting choice silently widened an
   owner decision.**
2. **"'measured at fetch' requires adding a READ that does not exist"** — it requires a new
   **WRITE**. "A read" implies the value exists and needs plumbing out, which is exactly
   the wrong instinct: the nearest existing field (`SourceState.last_collected`) is
   populated, plausible, and wrong twice — last-**success** not last-**fetch**
   (`json_source_state_manager.py:348` is inside the `collected_sources` loop; the
   `failed_sources` loop leaves it untouched, so backoff inflates it into a false
   under-polling reading), and its rows **do not exist for the population the field exists
   to expose** (state rows come from `aggregator_frequencies`; FS#121 *is* the `else`
   branch).
3. ⛔ **I recommended spending the only non-circular acceptance control.** See below.

---

## ⛔ The one worth promoting: A FAILING CHECK MAY BE THE CONTROL WORKING

Verified fact: validating 788 live producer rows against Contract A 1.22.0 gives
**788/788 violations**, all `source_group` unexpected at a closed root (21 root properties,
`source_group` not among them). **The facts were right; the inference was the error.**

`source_group` is the production contract check's **only non-circular acceptance control** —
an independent field the check **was never shown**, and therefore the only evidence the
check *can fail at all*. Already recorded (NM#304, `contracts/CHANGELOG.md` 1.18.0) and
guarded by `tests/unit/test_contracts.py:178`, which failed by design the moment it was
tried.

⭐ **Declaring it spends that control PRECISELY IN ORDER TO DRIVE A VIOLATION COUNT TO ZERO
— the very number whose trustworthiness the control exists to establish.** A synthetic
replacement is circular in exactly the way the original is not: an injected key proves the
check catches **what you already knew to look for**; `source_group` proves it catches
**something nobody designed it to catch.** Not replaceable once spent.

**So 788/788 argues for building the canary SOONER, not for spending the control first.**
Promoted to `memory/working-rules.md`, beside its opposite-signed sibling from 2026-08-12
(*the archive survived only because the purge was broken*): **before changing a thing that
is failing or dead, establish what its failure or deadness is currently buying you.**

Two number corrections that do **not** change it: `source_group` is on **20.5%** of
delivered rows, not 100% (true of today's producer, false of the archive) — and that makes
the control **more** discriminating, since it distinguishes archive vintages. And
**`eval_query` is a SECOND undeclared root field** (511 rows); all three sessions had been
saying *the* undeclared field.

---

## ✅ CLOSED: the ovr.news corpus backfill — the answer is NO

Carried for weeks as *"authorised and not run"*, and it kept coming back at the owner
partly because **this repo's own decision record asserted a growing-hazard framing that
measurement killed three times over** — twice by ovr refuting its own reasoning.

- Population was never "79 rows plus naive twins": **21,520 of 21,925 = 98.2%**, because
  the canonical form is `toISOString()` and every naive row differs from it too.
- **"Value increases with delay" is FALSE** — the naive population is **closed** (newest
  naive row 2026-08-14T08:30; all 153 rows since are canonical).
- **No time trigger AND no event trigger.** The write boundary canonicalises an offset to
  `.000Z` **before storage**, so an offset never reaches `ORDER BY` as an offset. The only
  two shapes that ever meet in a sort are legacy naive and canonical `Z`, and one is always
  a **prefix** of the other ⇒ they can only tie. Measured: **0 adjacent inversions in
  21,948 production rows**, and 0 in a seeded post-FS#174 simulation.
- **The last benefit fails on SCOPE:** it rewrites `articles.published_date` only, while
  the append-only archive is ovr's **durable** copy since ADR-022/#262 — so it would leave
  the working copy canonical and the durable copy mixed **forever**.

✅ **llm-distillery is a structural non-stakeholder**: reads no ovr archives (grep empty
against a positive control that prints), and both `sort_articles_by_date` impls truncate at
`'T'`, so the sort key is `YYYY-MM-DD` and the whole spelling hazard cannot reach it.

**Real follow-up that came out of it, and it is not the backfill:**
`ovr.news/tests/published-date-write-boundary.test.ts:52-53` asserts in its header that
every naive value has no fractional part — **false, 313 naive rows carry one**, and that is
the one shape that genuinely *can* invert against a `+00:00` row inside the same second.

---

## New findings filed elsewhere in this repo

- **`data/raw` is not producer bytes** → `memory/nexusmind-data-sources.md`. NexusMind's own
  preprocessing stamps `_commerce_*`/`_obituary_*` back into it, so all 4 violation classes
  were ours. ⭐ **The corpus predates `source_group`, so the one class that SHOULD appear is
  absent while four that should not are present — and they cancel into a plausible total.**
  Sound corpus exists locally: the sadalsuud mirror, 52 collections / 165,107 rows.
- **A fifth fabrication class at ~0h**, **a third substitution site (`date_normalized`)**,
  the **`had_timezone` TRUE-on-100% trap**, and the **CEST→LMT bug** →
  `memory/date-error-recency-boost-hypotheses.md`.
- **A sample with no negatives cannot license an absolute** → `memory/working-rules.md`.
  "Expect ~100%" came from 662/662 and 737/737; an independent sample read **97.2%**.
  ⭐ **The check that catches a broken instrument is NOT the check that bounds the rate** —
  a differently-derived cross-check validates *agreement on the rows you have*, never *the
  representativeness of the rows you chose*.
- **Refuting a figure in place beats deleting it — but only inside one repo.** The refuted
  `99.22%` still lives at `FluxusSource/src/utils/date_parser.py:242`.

## Category G — both spec lines delivered (pipeline-atlas), still no implementer

`poll_interval_actual_h` needs a new **write** (`last_fetch_attempt_at`, on every dispatch,
all enabled sources). `outcome` must **not** gain an over-polled value — the missing field
is **`selection_branch`**, written at the branch that fires. ⚠️ **Amended by its author
before it set:** the FS#121 fall-through population is **EMPTY today** (reproduced here: 20
enabled, 24 scheduled), so `selection_branch` is a **regression detector, not a live-defect
detector** — sell it as that or its first cycle reads as "found nothing" and it gets cut.
⭐ Its real value: it closes the gap between *"no source is unscheduled in the checkout"*
and *"no source was unscheduled on this tick, on this host"* — **"a test passes" is not
"the mechanism ran"** (11th occurrence, and the first where the unreachable mechanism is a
*passing test*).

---

## NEXT SESSION

1. **Two owner decisions, nothing else blocked:** commit NexusMind 1.21.0–1.23.0; commit
   and deploy FluxusSource Track A. Both sessions are idle and will not move without it.
   ⚠️ The Track A deploy carries an **unagreed storage commitment**: +95 bytes/row,
   ~1.5 MB/day, against archives kept indefinitely since #164.
2. **Canary + W2.2 in the ORIGINAL order** — do not resequence, see above.
3. **`CLAUDE.md` is 37.4k against a 35k soft target**, and there is **no padding to
   reclaim** (measured: −15 bytes, no formatter installed). Content is the only lever;
   recommend `/audit-context` over a hand-trim.
4. Unowned: `eval_query`, the CEST→LMT bug (FluxusSource's), #115 (our merge scripts).
