# Decision: the Contract A envelope — declare early, emit later, stay closed

**Date:** 2026-08-14
**Decider:** this session, on the owner's instruction ("settle the shared envelope")
**Status:** Accepted
**Issue:** llm-distillery #112 · proposal `docs/proposals/contract-a-redesign.md`
**Plan item:** W1.4 ("publish the envelope as a versioned fragment")

⚠️ **This supersedes a standing "not approved" in `docs/CONTRACTS_PLAN.md`.** That
file's 2026-08-14 status block lists the shared envelope (W1.4) among three open
owner decisions, *"NOT approved and NOT to be started."* The owner reopened and
delegated it the same day — *"then settle the shared envelope, because
`additionalProperties: false` on both schemas makes it a hard blocker for shipping
anything incrementally."* The plan's status block is updated to point here.

**The other two holds in that block are untouched and still binding:** do not declare
`source_group`, and do not make any check stricter until its drops reach a reader.

---

## The question

#112 named this a **hard blocker, not a design choice**:

> Both schemas set `additionalProperties: false` at the root — producer
> (`FluxusSource/config/schemas/output_schema.json`) and consumer
> (`NexusMind/contracts/fluxussource-output.schema.json`). So any added field fails
> at the consumer unless both move together. **A redesign cannot ship incrementally
> under the current shape.**

The redesign's own migration plan is "additive, never a flag day" — add the new
blocks alongside the old flat fields, let consumers migrate at their own pace. Those
two statements cannot both be true. Four repos read this stream and two are live.

## The reframing this rests on

**The blocker is not `additionalProperties: false`.** It is that *declaring* a field
and *emitting* a field were assumed to be the same step. They are not, and nothing
forces them to be:

- A schema property that is **declared and optional** is satisfied by every row that
  omits it. Declaring it costs nothing and breaks nothing.
- A closed root only rejects keys that are **undeclared**.

So the flag day is not per field — it is **exactly one, and it moves no data.**

## Decision

**1. `additionalProperties: false` stays** — at the root, and inside every new block.
It keeps the property that makes it worth having: a misspelled key is still a
violation rather than silently accepted into a bag.

**2. One declaration commit lands the entire target shape before any producer code
emits anything.** Every block optional, every property inside every block optional.
The blocks, from proposal §§A–F and §H:

```
published    { instant, raw, element, had_timezone, precision, fabricated }
collected    { at, clock_source }
origin       { country, region, timezone, method }
fetch        { url_requested, url_final, http_status,
               charset_declared, charset_detected, charset_used,
               content_encoding, at }
content_meta { kind, truncated, raw_length, echoes_title }
feed         { title, declared_language, cadence_hours, ttl_declared }
payload      { ... }                                  ← the one open region
```

`origin.*` is declared **even though nothing will populate it this pass.** Its cost
is editorial (~1,872 per-source YAML entries, ~932 bulk-seedable from geographic
shelves), it is sequenced separately (`docs/proposals/contract-a-origin-sequencing.md`),
and declaring it now costs nothing and saves a second declaration commit later.

### ⛔ `language` is NOT in that list, and the reason generalises

**Found by the NexusMind session, and it falsifies "one commit declares the whole
target shape" as I first wrote it.** The proposal's §B wants a `language` block. But
`language` **already exists at Contract A root**, declared `type: string` and emitted
as a string on **7,478 / 7,478 rows** measured 2026-08-14. Declaring it an object
fails `type` on every row — **optionality does not help, because the property is
present, not absent.** It is also read as a string at 8 production sites in NexusMind
(`src/scoring/display_ranking.py:254`, `src/enrichment/article_fetcher.py:741,1241,1463`,
`scripts/main.py:1506`, several feeding it into `title_affinity` as `language=`), where
a dict is a crash rather than a degradation.

**Resolution: there is no `language` block.** Once the owner's rename ban is applied,
the block was almost entirely a re-housing of fields that already exist and are
forbidden to move — and the separation §B asks for is *already in the data*:

| §B wanted | lives today as | rows (2026-08-14) |
|---|---|---|
| `language.code` (the answer) | top-level `language`, a string | 7,478 |
| `language.method` | `metadata.language_source` | 7,478 |
| `language.sample_chars` | `metadata.language_input_len` | 7,478 |
| `language.confidence` | `metadata.language_confidence` | 7,444 |
| `language.declared_by_feed` | `metadata.feed_declared_language` | 6,736 (see below) |
| `language.script`, `.scripts_present` | ⭐ **genuinely new** | — |

*(The `feed_declared_language` row is the NexusMind session's addition; the proposal
and my first draft both missed that it was already live.)* So the block carried **one
new fact and five relocations**, all five of them relocations the owner has forbidden.

#### ⚠️ `declared_by_feed` is a name that must NOT be created — two disjoint fields already sit under it

**FluxusSource, measured on the clean window** (runs from 2026-08-10 onward, 101,917
rows — see the retraction note below for why the window matters):

| | rows | population |
|---|---|---|
| `metadata.feed_declared_language` | 87,061 (85.4%) | the RSS feed's `<language>` element — **RSS only** |
| `metadata.language_source == 'declared'` | 707 (0.7%) | producer-supplied code (mastodon, gnews_eval) — **non-RSS only** |

⭐ **They never overlap.** `declared` fires on the one path that never reaches the
detector, which is precisely the non-RSS path; `feed_declared_language` exists only
where there is a feed document to read it from. **Anyone reading `declared_by_feed`
as "the rows where `language_source` is `declared`" merges 707 rows with 87,061 and
gets a field that is neither.** So `metadata.feed_declared_language` keeps its name;
introducing `declared_by_feed` would stand a third near-synonym beside two live ones.

**The 6,736 vs 87,061 is a population difference, not a discrepancy** — NexusMind's
sample is essentially RSS-only and ~7% the size. Their 6,736/7,478 = **90.1%** against
the producer's **89.3% of RSS rows**; those agree. Size the relocation on 87k/week.

⚠️ **And this field can never earn `required`**, however many cycles show it
populated — its absence is **structural** (0% of api, social and data rows, by
construction at `rss_aggregator.py:671`), not incidental. That is a limit on decision
point 5 below, and the first field found to have it.

**It is also not a redundant copy of `language`:** the declaration disagrees with the
final answer on **2,190 rows, 2.5%** of those carrying it. An independent signal that
survives being overridden — which is what makes it worth carrying at all.

Full clean-window `language_source` split, for sizing anything else: `detected`
100,025 (98.1%) · `script` 1,174 (1.2%) · `declared` 707 (0.7%) · `hint` 7 · `none` 4.

⚠️ **Why "clean window" — a retraction FluxusSource caught before it propagated, and
the lesson is reusable.** Their first measurement put `feed_declared_language` at
108,038 rows / 70.9%, which would have read as a 16× discrepancy against NexusMind's
6,736 and sent someone hunting a phantom. It was wrong: **`language_source` shipped
mid-window** — 0% of rows on 08-07 and 08-08, 26.2% on 08-09, 100% from 08-10 — so
any count over the 7-day hot window straddles the boundary and averages a field into
existence. ⭐ **Same 2026-08-10 boundary that FS#149's confidence floor is already
pinned to; nobody had connected that it equally poisons any metadata-*presence*
count.** Rule: **a presence rate for a recently-shipped stamp needs its window
checked against the stamp's own ship date**, or it measures the rollout rather than
the field.
The two new fields join the family that already exists, as
`metadata.language_script` / `metadata.language_scripts_present` — no collision, no
rename, no `oneOf` transition shape, no consumer audit.

⭐ **The rule this is an instance of: re-nesting an existing flat field is never
additive.** An added key is invisible to a consumer that ignores it; a *moved* key
changes the type at a name that is already being read. The redesign's "logical
grouping" diagram contains a second instance nobody had flagged — `source` is
likewise a live top-level string, and `item: { title, content, tags }` would move
three more. **That whole regrouping is out of scope for the same reason**, and this
decision does not attempt it. Blocks earn their place by carrying facts that do not
exist yet. `published`, `collected`, `origin`, `fetch`, `content_meta`, `feed` and
`payload` all clear that bar; `language`, `source` and `item` do not.

**3. Ordering: the consumer's declaration lands before or with the producer's, never
after.** Reversed, the validator reports `additionalProperties` violations against
the producer for keys the producer legitimately emits — a false red pointing at the
wrong repo. This is the same failure mode as invalidation item 1 (the strip list),
arriving by a second route.

**4. After the declaration commit, every field ships independently.** Any subset of
any block, in any order, from any repo, with zero cross-repo coordination. "Additive"
now means *populating a declared-but-empty slot*, which no closed envelope objects to.

**5. `required` is earned, never granted at declaration.** A stamp earns `required`
after it is observed populated across several cycles (NexusMind#300). The precedent
is already in the producer's own schema: `primary_literature` is stamped on every row
and is deliberately not required, with the reasoning written into its description.

## Why this is cheap: the declaration commit is runtime-inert, and that is verified

Neither production path opens either schema file. Checked by grepping every `.py`
and `.ts` in both repos for the schema filenames:

| repo | who reads the schema |
|---|---|
| **NexusMind** | `scripts/validate_production_contract.py`, `validate/validate_contract_a.py`, `tests/unit/test_contracts.py` — a reporting script, a standalone validator, and a test |
| **FluxusSource** | `scripts/validate_output.py`, `tests/test_output_schema_adr008.py`, `tests/test_source_group_field_adr010.py` — a standalone script and two tests |

The **only** production row-dropping check against Contract A is
`NexusMind/scripts/main.py:118`'s `_CONTRACT_A_REQUIRED` frozenset — hand-copied and
synced by a comment. It lists eight fields, all of which stay required and none of
which this decision touches. **Adding optional properties to either schema cannot
drop a row, because no row-dropping code reads either schema.**

⚠️ That is the divergence hazard, and it already has a guard: phase 0b's check
asserts `drift.contract_a_frozenset_vs_required`, reading `sev=clean` on the
2026-08-14 run. **So the requirement is not to build a comparison — it is to confirm
that class stays `clean` through the declaration commit.** Everything being declared
is optional, so it should never move; if it does, the commit added a `required` it
did not intend to.

## The live instance — measured, 100% of rows, and deliberately held

The consumer schema declares 14 top-level properties. `source_group` is not among
them, and the root is closed. FluxusSource has emitted `source_group` on every row
since ADR-010 (2026-08-13).

**This is measured, not inferred.** Phase 0b's check, run on genuine unmutated
producer bytes (`collection_20260814_121004`, 2026-08-14):

```
additionalProperties.<root>.source_group   asserted=True  rows=3835  sev=error
```

**3,835 of 3,835 rows.** Independently re-measured by the NexusMind session on a
later pull (`_121003` + `_160810`, **7,478 rows, 100.00%**) and spot-confirmed
against a live row by the FluxusSource session: exactly one undeclared key.

⚠️ **But it does NOT carry the argument I first put on it, and the NexusMind session
was right to push back.** I wrote that this was "the failure mode already realised."
It is not. `source_group` is the **acceptance control, deliberately held** — the
check firing on exactly the class it was left un-declared to catch. That is the
instrument working, not escaping. What the data says is *"the control is still held
and still fires on 100% of rows"*, and that is what belongs in the record.

The envelope argument stands on its own without it: declaration-lagging-emission
**would** produce a false red against the producer, and this is what that looks like
when it is done on purpose. The three unplanned violation classes NexusMind measured
alongside it (`metadata.priority` > max on 771 rows where the true ceiling is 10;
`metadata` required absent on 203 rows, all non-rss; `source_type` enum rejecting
`social` on 16) are already filed as NM#354–358 and are not this decision's.

⚠️ **Exposure is offline only, confirmed by both peers.** Live ingest enforces
`_CONTRACT_A_REQUIRED` (root-only, 8 keys), not `additionalProperties`, so **no
production row is dropped by any of this.** The red lives in the three offline
validators. That is what makes the declaration commit safe and also what let the
divergence persist.

**And the hold constrains this decision.** The plan holds W2.2 open on purpose:

> 🔒 **Do NOT declare `source_group` (W2.2)** until the check has reported it. It is
> the only test that proves the check *detects* rather than merely *runs*, and
> declaring it spends that permanently.

So the estate is knowingly accepting a false red aimed at the producer because the
control is worth more than the noise. That is a defensible trade and this decision
does not disturb it — but it means:

⛔ **The declaration commit must NOT declare `source_group`.** It is not one of the
new blocks, it is an existing flat field, and it is the only thing currently proving
the check detects anything. Landing it as tidy-up while editing the same file would
spend the control silently, in a commit whose stated purpose is something else
entirely. Stated here because that file is about to be edited for an unrelated
reason, which is exactly when a hold gets lost.

## Rejected alternatives

**Open the root on the consumer side** (`additionalProperties: true`). Unblocks
incremental shipping immediately and costs the one thing the closed envelope buys —
a typo'd or renamed producer field arrives as an accepted unknown. Contract B already
has this shape and the plan's W2.5 notes it means B *structurally cannot detect a
`source_group`-class event*. Taking the same trade on A would discard the detection
capability at the exact moment the field set is churning hardest.

**A reserved open namespace** (put new blocks under a `v2` object until they settle).
Works, and buys a second migration later when everything has to move out of it. The
declaration commit achieves the same unblocking with no future move.

**Per-field lockstep across both repos.** What #112 assumed was required. N flag days
across four repos, two live, each one an opportunity to land the halves in the wrong
order. This is the option being replaced.

## Where the envelope text lives

One fragment, published by the producer, **vendored by each consumer with a recorded
sha256**, checked in CI — not a network `$ref`. A validator that resolves a URL at
validation time fails offline, fails in cron, and turns a schema check into an
availability dependency. Hash-pinning is already this project's habit for exactly
this problem (`docs/CONTRACTS_CHECK_ARTEFACT.md` is pinned by hash from a tracked
line because the file itself is untracked).

## Definition of done

1. Both schemas declare the full block set above; all blocks and all inner properties
   optional; `payload` open; consumer landed before or with producer.
2. **`source_group` is still NOT declared** after the commit. Re-read the hold above
   before touching that file.
3. `validate_production_contract.py`'s strip list extended in the same commit
   (#112 invalidation item 1).
4. Phase 0b's `drift.contract_a_frozenset_vs_required` still reads `sev=clean`.
5. The check re-run after the commit shows **the same one violation class and no
   others** — `additionalProperties.<root>.source_group` at `rows=N`, N being that
   cycle's row count. Any second class is the declaration commit's own doing.

⭐ Item 5 is the outcome test, and it is unusually clean here: the pre-state is a
single known class on 100% of rows, so *anything* new is attributable. A declaration
commit that is genuinely inert must leave the report byte-comparable apart from the
row count. Do not accept "the tests pass" in its place — the tests read fixtures.

## What this decision does not settle

### The offset on `published.instant` — ⛔ GATE CLOSED, answered by ovr.news 2026-08-14

**Not yet.** `60ada82` is the **parser only** — zero of the comparison sites were
touched, and the lint rule that shipped with it greps for
`(new Date|Date.parse)([^)]*published_date`, so it cannot see an `ORDER BY`, a raw
SQL `>=`, or a `localeCompare`. The "~20" is exactly 20 raw `ORDER BY published_date`
sites, plus 1 JS `localeCompare` and 15 raw SQL `>=`, all enumerated in their reply.
The highest-stakes one is `scripts/create-hot-db.ts:59`, where a reversal doesn't
misorder a feed — it puts the **wrong articles** in the hot DB production reads.

**Until they confirm, the producer emits `published.instant` naive-UTC, byte-identical
to today's `published_date`.** FluxusSource has accepted this.

⚠️ **Two corrections to the proposal, both from ovr and both load-bearing:**

**1. The backfill is the wrong gate predicate.** Naive and canonical values are
lexicographically *compatible* — `'…T19:00:00'` vs `'…T18:30:00.000Z'` resolves at
the differing digit, and shape only breaks ties between identical instants. Today's
mixed corpus sorts correctly. What protects the sort is **canonicalisation at the
write boundary** (`canonicalizePublishedDate`, `src/lib/db-articles.ts:141`, the sole
writer of that column). Do not record "backfill applied" as the condition; it buys
shape uniformity for the raw `>=` sites, not sort safety.

**2. ⭐ The contract must pin the offset GRAMMAR, because the invariant has a hole.**
The write is `canonicalizePublishedDate(x) ?? x` — an unparseable value is stored
**verbatim** and lands straight in the lexicographic sorts. Measured against the
shipped parser:

| emitted | result |
|---|---|
| `+02:00`, `+0200`, fractional seconds, space-separated | canonicalised ✅ |
| bare `+02` | **REJECTED → stored raw** ⛔ |
| lowercase `z` (legal RFC 3339) | **REJECTED → stored raw** ⛔ |

So when the gate opens, **`published.instant` must emit an offset in ovr's
canonicalising set, and the schema pattern must enforce it.** Emitting bare `±HH` or
lowercase `z` breaks ovr *quietly*, and would do so even after a backfill. This is a
producer-side constraint that only the consumer could have discovered.

✅ **Satisfiable for free, and the pattern should be tighter than ovr's accepted set.**
FluxusSource: Python's `datetime.isoformat()` emits `±HH:MM` — `+02:00` / `+00:00` —
and **never** bare `±HH`, **never** lowercase `z`, and **never `Z` at all**, writing
`+00:00` for UTC. So the producer lands inside ovr's grammar with no special-casing,
and the schema `pattern` should encode **`±HH:MM` only** rather than also permitting
`Z`, since nothing on the producer side would ever emit it. Declare what is emitted,
not what the consumer happens to tolerate.

*(Also: `display_date` is not a column in ovr — only `published_date` and
`collected_date`. Correct the proposal's ovr line.)*

The outcome check ovr specified — an integration test upserting naive / `Z` / `+02:00`
rows through the real `upsertArticle` and reading them back through the production
query and `create-hot-db`'s prune — does not exist yet. Their existing
`tests/published-date.test.ts:113` tests the *helper*, not the path, and would stay
green if canonicalisation were deleted from the write boundary tomorrow. **The gate
opens when that test exists and is green**, not when the parser is confirmed.

### The replacement acceptance control — resolved, by splitting it in two

Assigned to pipeline-atlas, who **rejected the request as framed** and were right to:
*a control named in the design conversation is spent by being named.* `source_group`
worked because nobody chose it.

Their resolution, which I accept: `source_group` was doing **two jobs**, and only one
is on the critical path.

1. **Proof the detection path is live** — that root `additionalProperties: false`
   actually fires and reports a class. ✅ **Does not need an unanticipated class.** A
   deliberately injected **canary row** carrying an undeclared top-level key, asserted
   red in the acceptance fixture, does it — and does it *repeatably on every run*,
   which `source_group` never could, being one-shot. **This unblocks W2.2.**
2. **Proof the check catches classes nobody anticipated.** ⛔ Cannot be manufactured,
   by construction — choosing it is what destroys it. **Record its absence as a known
   gap**; let it be re-earned the next time the check surprises someone.

⚠️ **The failure mode to avoid is reading a green canary as evidence for (2).** The
canary answers *"does the detection path fire"*. Asked *"does this check catch things
we didn't anticipate"*, it answers confidently and wrongly. Two lines in the plan, not
one.

⚠️ **And a trap in the canary itself:** `validate_production_contract.py` strips keys
before validating (`_commerce_`/`_obituary_`/`_violence_` prefixes plus five named
keys). An underscore-led "obviously synthetic" canary name is a coin flip against that
list, and a **stripped canary produces a green run that looks like a passing check
while proving nothing** — the same subtraction the invariant warns about, arriving in
the instrument instead of the data. Give it a plain name and assert it goes red.

---

## Where this stands, end of 2026-08-14

All four peer sessions answered. **Nothing has been committed in any other repo, and
nothing was edited outside this one.**

| repo | answer |
|---|---|
| **FluxusSource** | ✅ **Takes all four (b) blocks.** Will write its own producer-side declaration commit; explicitly not touching NexusMind's. Sequence: `content_meta.kind` → `collected.clock_source` → `fetch.*` → `published.*` (time last, `precision` needs a double parse). Accepts both owner constraints. |
| **NexusMind** | ✅ Ran the validator, supplied the `language` blocker. ⛔ **Declines the consumer-side declaration commit pending the owner** — the owner stood the contracts thread down in that repo on 2026-08-14 (*"stand down, we were led astray"*), with a handoff that says in terms not to resume it on a peer's say-so. **That refusal is correct and I am not pressing it.** They have put it to the owner. |
| **ovr.news** | ⛔ **Gate closed** — see above. Confirms ovr's ingest does **not** close the top level (`validateRawArticle` inspects named fields only), so new top-level blocks survive ingest untouched and stop at the projection in `transform.ts`, which is the right place. ⚠️ But `nexus_mind_attributes` **is** closed with teeth: an unknown sub-key is a validation error and an errored article is **dropped**. Keep new blocks at the top level. |
| **pipeline-atlas** | ✅ Category G confirmed theirs *as model facts*; not taking implementation (the repo owns no pipeline code). Six corrections to the sidecar spec, the sharpest being that **the grain is wrong for the RSS tier** — `concurrent_rss` is one source name holding the whole feed tier, while `health_state` and `poll_interval_actual_h` are per-*feed* quantities. Resolved the control gate (above). |

**Two framing corrections I accepted from peers**, recorded because both were mine:
the `source_group` red is the control working, not the failure escaping; and the
state of the check is **"not armed, and measured red"**, not "armed but red" —
`nexusmind-contract-check.timer` reads NOT ARMED, and arming reads systemd, not the
verdict. The check has run by hand; nothing runs it on a schedule. ⭐ **Those are two
different arguments for arming, and the second is the stronger one** — *"nobody has
looked"* and *"someone looked, it is 100% red, and nothing watches it"* are not the
same case.

## The blocking item is now an owner decision, not an engineering one

The producer half can start. The consumer half cannot, and the reason is not
technical: **the owner stood this thread down in NexusMind, and the envelope commit
is the first thing that would resume it there.** The owner has since instructed this
session to settle the envelope and implement the redesign — but that instruction was
given here, and the NexusMind session is right that it does not reach their repo
through me.

**What is needed: the owner confirming, in NexusMind, that the consumer-side
declaration commit is in scope.** Until then the sequencing rule inverts into a stop —
the consumer must land first-or-with, and the consumer is held.
