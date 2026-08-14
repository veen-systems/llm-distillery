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
published    { raw, element, had_timezone, precision, fabricated }   ⏸ +instant?
collected    { clock_source }
origin       { country, region, timezone, method }
fetch        { url_requested, url_final, strategy, attempts, http_status,
               charset_declared, charset_detected, charset_used,
               content_encoding, at }
content_meta { kind, truncated, echoes_title }
feed         { cadence_hours, ttl_declared }
payload      { ... }                                  ← the one open region
```

⚠️ **This list is POST-narrowing.** The owner's scope call (below) removed
`collected.at`, `content_meta.raw_length`, `feed.title` and `feed.declared_language`
— every one a declared duplicate of a live flat key. What survives carries only facts
the row does not hold today. ⏸ **`published.instant` is dropped pending an owner
re-decision** — see the correction under the scope call.

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

⭐ **The rule this is an instance of — restated, because my first version was too
broad and NexusMind was right to push back.** I wrote *"re-nesting an existing flat
field is never additive."* That conflates two separable acts, and only one is
forbidden:

| act | verdict | why |
|---|---|---|
| Declaring a **new name** whose content duplicates a live field (`feed.title` beside `metadata.feed_title`) | ✅ **safe** | nothing reads the new path; the flat key stays authoritative and untouched |
| **Relocating** — populating the new name and retiring the flat one | ⛔ **the forbidden act** | breaks every existing reader at once |
| Declaring a name that **already exists** with a different type (`language`) | ⛔ **the fatal case** | the property is *present*, not absent, so optionality gives no protection and `additionalProperties: false` no warning |

**`language` is the third row, which is why it is dangerous — not the first.**
`feed`, `content_meta` and the rest are new root names, so declaring them costs
nothing today; the risk materialises only if a producer later *removes* the flat key.

⚠️ **But a declared duplicate must not be POPULATED in both places.** That is the
proposal's own test 1 — *a stored copy of a derivable value is a second source of
truth that will eventually disagree* — and it is the reason `word_count` is being
removed. Declaring `feed.title` is inert surface; populating it while
`metadata.feed_title` is authoritative reintroduces exactly what the redesign
deletes. **Declare freely, populate once.**

`source` and `item: { title, content, tags }` stay out of scope, but under the third
row, not the first: `source` is a live top-level string, and moving `title`/`content`/
`tags` is relocation by definition.

### ✅ Scope call ANSWERED by the owner, 2026-08-14: the ban extends

**Chosen: "extend to all live metadata keys" — no new name may be declared where a
live flat key already carries the fact.** *(Against my recommendation, which was to
keep the ban specific to the three language keys and rely on populate-once. The
owner's call is the stricter one and it is coherent — see below.)*

⭐ **This reaches further than `feed`, and the reach is an improvement.** The rule
reduces to: **a new block carries only facts that do not exist on the row today.**
That is the proposal's own test 1 applied to *declarations* rather than to values,
and it removes the possibility of a populate-once violation instead of policing it.

Consequences, derived rather than listed in the option:

| declared | live key carrying the same fact | verdict |
|---|---|---|
| `feed.title` | `metadata.feed_title` | ⛔ **drop** |
| `feed.declared_language` | `metadata.feed_declared_language` | ⛔ **drop** |
| `content_meta.raw_length` | `metadata.raw_content_length` | ⛔ **drop** |
| `collected.at` | `collected_date` | ⛔ **drop** |
| ⚠️ `published.instant` | `published_date` (declared `format: date-time`) | ⏸ **HELD — owner's call, see below** |
| `feed.ttl_declared`, `feed.cadence_hours` | none on the row | ✅ keep* |
| `published.{raw,element,had_timezone,precision,fabricated}` | none | ✅ keep |
| `collected.clock_source` | none | ✅ keep |
| `fetch.*` (all seven) | `url` conflates requested/final; rest none | ✅ keep |
| `content_meta.{kind,truncated,echoes_title}` | none | ✅ keep |
| `origin.*` | none | ✅ keep |

#### ⚠️ `published.instant`: dropped, argued for restoration on a WRONG reason, back with the owner

**Status: HELD, not restored.** NexusMind is correctly refusing to reverse it on my
say-so — the owner named `published.instant` explicitly when giving the five drops,
and reversing a by-name owner instruction on a peer relay is the strongest form of
the case the standing rule covers. Both readings are with the owner.

⛔ **My stated justification was wrong, and NexusMind checked it rather than taking
it.** I argued `published_date` **structurally cannot** carry the instant-with-offset.
It can: **Contract A already declares `format: "date-time"` on `published_date`,
which requires an offset.** NM#356 (`f55f708`, on that very branch) says so in terms —
*"Contract A declares `format: date-time` on the field, which requires an offset, so
the aware branch is the intended steady state rather than an edge case"* — and
normalizes offset-bearing input to UTC on ingest deliberately.

**So the producer emitting naive values is a producer DEFECT (NM#358), not a property
of the field.** Under the ban as literally stated, `published_date` *is* declared to
carry that fact and `instant` *is* a duplicate. ⭐ *(NM#358 is itself the `format`
trap this repo already documents: declared on three fields, asserted on none.)*

✅ **What survives is the foreclosure argument, and it never needed the wrong premise.**
Putting the offset on `published_date` is what breaks ovr's twenty raw `ORDER BY`
sites. Putting it on a **new** name does not touch them. So `instant` is not really a
duplicate of the fact — it is **the only non-breaking migration route to it**, and
dropping it forecloses that route without a second declaration commit, which is what
this envelope decision exists to prevent.

**That is an argument about migration mechanics, not about same-fact**, and it stands
whether or not `published_date` is capable. The owner has both readings: the ban as
written drops `instant`; the foreclosure risk argues for keeping it.

⭐ **And the consequence of getting it wrong was not a deferral, it was a
foreclosure.** #112 ranks the two-hour disagreement between NexusMind and ovr as the
**top live defect** — *"affects which articles readers see."* With `instant` dropped
there is no path to ever fixing it without a **second declaration commit**, which is
the exact thing this envelope decision exists to prevent. A field that costs nothing
to declare and is the only route to the headline fix is not a duplicate.

**The other four drops stand** — `collected.at`, `content_meta.raw_length`,
`feed.title` and `feed.declared_language` are each genuinely the same fact as a live
key, with no representational difference. Only this one was miscategorised.

**Lesson, and it is the sixth of its kind in this thread:** a rule phrased over
"facts" needs the fact stated at the resolution that matters. *"The instant"* and
*"the instant with its offset"* are different facts, and matching on the shorter
phrasing silently deleted the redesign's headline fix. **When applying a
same-fact test, name the fact precisely enough that its representation is part of
it.**

\* ⚠️ **The option's preview said `feed { ttl_declared }` and the rule says
`feed { cadence_hours, ttl_declared }`** — `cadence_hours` is measured by
`FeedHealthTracker` into the health report and **never reaches the row**, so no live
key carries it and the rule does not drop it. Outcome and rule differ on exactly this
one field. **Followed the rule; flagging the discrepancy** rather than silently
picking either.

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

⛔ **Exception, and it covers most of the new surface: a field whose absence is
STRUCTURAL can never earn `required`, at any observed rate, ever.** Cycles measure
*incidental* absence. They cannot see a field that is 0% on a source type by
construction, and a high rate is exactly what makes the trap spring — the promotion
looks earned.

**Which of the new fields this binds** *(FluxusSource, clean window, 101,917 rows)*:

| block | spans all source types? | why |
|---|---|---|
| `published.*` (the five) | ✅ **yes** | — |
| `collected.clock_source` | ✅ **yes** | — |
| `fetch.*` — all seven, incl. `strategy`/`attempts` | ⛔ **RSS only** | `RobustFeedParser` has exactly one aggregator caller, `rss_aggregator.py`; the two other users emit no rows |
| `content_meta.kind` (as scoped below) | ⛔ **RSS only** | derived from the feed entry at `rss_aggregator.py:548` |
| `metadata.feed_declared_language` | ⛔ **RSS only** | `rss_aggregator.py:671` |

RSS is **95.7% of rows in the producer's clean window** (97,526 of 101,917) — high
enough to look promotable across any number of cycles and never be, and the `fetch.*`
fields are *new*, so they will arrive looking like ordinary candidates. **Only
`published.*` and `collected.clock_source` can ever earn `required` honestly.**

⚠️ **Always state which corpus that share came from — three exist and they are not
interchangeable.** RSS share measures **95.7%** on the producer's clean window,
**97.29%** on NexusMind's 7,478-row live sample, and **~92.8%** across all 87 local
raw files (181,127 rss / 13,214 api / 892 social). All three support the argument;
none may be substituted for another. ⭐ **And phrase it as the RSS share, never as
"0% on 95.7% of rows"** — I wrote the latter to NexusMind and it inverts the
population, turning "present on nearly everything, so promotion looks earned" into
"absent from nearly everything", which implies the opposite conclusion from the same
sentence. The structural claim itself was independently **verified** there:
`rss_aggregator.py` is the only one of 30 aggregators importing `RobustFeedParser`.

⭐ **The general form, since it will recur:** `required` is a claim about *every* row,
so it must be checked against the population that structurally *can* carry the field,
not against an observed rate. Ask "which source types can produce this at all?"
before "how often is it present?" — the second question cannot answer the first.

#### Scope call: `content_meta.kind` ships RSS-only

FluxusSource asked before building, because spanning api/social means a **different
derivation per aggregator** (arXiv abstracts, GDELT title-and-URL, github, pubmed) —
a much larger job. **Ship RSS-only.**

1. It **narrows** the 300-char floor rather than retiring it — from a blanket rule to
   a fallback on a named minority. That is strictly better than today and does not
   block on the larger job.
2. **Absence is self-describing**: absent ⟺ non-RSS, derivable from `source_type`, so
   no consumer is misled and no extra flag is needed. ⚠️ **Write that into the field
   description**, or absence reads as "unknown" instead of "not applicable" — the
   `primary_literature` precedent, where the description carries the semantics.
3. ⚠️ **The number that should rank any later per-aggregator extension is NOT
   measured, and it is not 4.3%.** The floor bites at *labelling* time
   (`ground_truth.batch_scorer.make_oracle_prefilter`), so what matters is the
   non-RSS share of **training corpora**, not of production rows — and those
   populations are known to diverge sharply here (Google News is ~25% of production
   and 0–4.9% of training corpora). Rank the extension by that share once someone
   measures it; do not infer it from the production mix.

#### The GN split — the vivid number, and why it must not decide anything

FluxusSource split `kind` by Google News vs native RSS (clean window, 101,917 rows):

| | rows | `headline_only` | body p10 / p50 / p90 | under 300 |
|---|---|---|---|---|
| **GN proxy** | 25,607 | **0.0%** | 68 / 87 / 116 | **100.0%** |
| **native RSS** | 71,919 | 6.9% | 79 / 195 / 1410 | 66.7% |

⭐ **The 300-char floor discards 100% of Google News rows — all 25,607 — and not one
is headline-only.** They are complete GN snippets at a machine-bounded width (p10 68,
p90 116 is a fixed-width snippet, not article text). A quarter of production thrown
away in full, on rows that all carry real content.

⚠️ **And it must not decide the scope call — the producer applied point 3 back to
their own finding, correctly.** 100% and 77.2% are **production** shares; the floor
bites at labelling time; GN is 0–4.9% of training corpora against ~25% of production.
**So the floor's effect on the corpora that actually matter is *smaller* than these
figures make it look, not larger.** The split makes the production case vivid and
says nothing new about the training case. **The unmeasured training-corpus share is
still the number that ranks the decision.**

**Design consequence, and it does not need a new field.** A two-value `kind` labels
all 25,607 GN rows identically to a native 900-char summary — both are honestly
`feed_summary`. That is fine: GN is separable from `url` (below), so a consumer can
split them without a third value. `kind` alone will not say *why* a body is short,
and GN is the population where short is **structural rather than incidental**.

⚠️ **Match GN on the URL, never on the source-key prefix.** Clean window:
`'news.google.com' in url` → **25,607 = 25.13%**; `source.startswith('gn_')` →
15,655 = 15.36%, a **1.64× undercount** — the prefix names only the country-proxy
population, missing publisher-named feeds repointed to GN and topic queries that
proxy no publisher at all. *(Non-RSS agrees exactly across repos: 4,391 = 4.31%.)*

#### ✅ The 5:1 / 1.64× conflict — RESOLVED, and neither figure is wrong

I flagged `CLAUDE.md`'s "~5:1" as conflicting with 1.64×. Both peers reconciled it
independently and agree: **they count different things.** Measured (FluxusSource,
clean window; feed counts from the repo YAML):

| quantity | URL test | `gn_` prefix | ratio |
|---|---|---|---|
| **configured feeds** (enabled) | 302 | 59 | **5.12×** ← this is the `~5:1` |
| distinct sources emitting | 251 | 59 | 4.25× |
| **emitted rows** | 25,607 | 15,655 | **1.64×** |

The prefix catches the same 59 feeds under all three counts and **zero prefix hits
fall outside the URL test** — it is a strict subset, exactly as the rule assumes. So
all three ratios are quotable *once the denominator is attached*, which is the same
fix the 95.7% needed. "Unreconciled, don't quote either" was too pessimistic.

⭐ **Why they diverge is the part worth keeping, and it inverts the intuition.** The
59 `gn_*` country proxies are broad country-wide queries and individually
high-volume; the 243 publisher-named feeds repointed to GN are narrow and individually
small. **So the prefix misses 5× the feeds but only 1.64× the rows — it happens to
catch the biggest ones. That makes it MORE dangerous, not less:** a row-share sanity
check shows it undercounting by ~1.6 and reads as roughly-right, while the
feed-level population it describes is off five-fold. The rule holds unchanged under
every reading — match on `'news.google.com' in url`, never on the prefix.

⚠️ **Two live defects this surfaced, neither mine to fix:**
1. **`CLAUDE.md:197` (this repo) carries the bare ratio with no denominator**, in a
   sentence about *matching* — a feed ratio in a matching claim. Proposed to the
   owner; not edited here, since it is a normative surface and the measurement is not
   mine. *(FluxusSource's own `CLAUDE.md` is correct: it says "several-fold" and
   delegates the number to `memory/gn-proxy-protocol.md`, which is the right shape and
   the reason defect 2 below matters.)*

   ⭐ **A verification that lands on the wrong target returns confidently negative,
   not "unverified" — the fifth wrong-sentence instance in this thread, and the one
   worth generalising.** NexusMind checked a repo I had not named, found a *different*
   file saying something correct, and read that as disconfirming the claim. My message
   was the cause (I named no repo), but the failure mode is general and has no
   built-in signal: a search that misses its target does not report a miss. **Name the
   file, not just the claim**, whenever asking anyone to check one.
2. **FluxusSource `memory/gn-proxy-protocol.md:54-58` — "ratio sound, illustration
   mismatched", NOT "the file contradicts itself".** Their narrowing, and it matters:
   the file's own class table eight lines above gives A=59, B=230, C=13 → the 302 it
   then states outright, so **302/59 = 5.12× is self-corroborating within the file**.
   What is wrong is that the 2026-08-08 incident (202 `gn_*` vs 441 GN-URL **items**
   in one run, 2.18×) is attached as if it demonstrated the 5:1. Calling it a
   self-contradiction puts the ratio in doubt when the table settles it.

   ⭐ **And the illustration is worse than mismatched — that quantity is not stable.**
   The same item ratio was 2.18× on 2026-08-08 and 1.64× over 08-10→08-14. It moves
   with which feeds were due and how much each returned; the feed ratio is a property
   of the *configuration*. **So an item count cannot illustrate a fixed ratio in
   principle, not merely on that day.** This is "the denominator travels with the
   number" in its sharper form: **some denominators do not yield a stable ratio at
   all**, and picking one of those is a defect no amount of re-measurement fixes.

   Theirs to fix; NexusMind found it and correctly declined to edit another repo's
   memory. The 2026-08-08 incident text itself stands unchanged — that session's
   error was reaching for the prefix at all, and the lesson is untouched.
3. **NexusMind `scripts/research/phase2_296_cosine.py:111`** labels a stratum "GN on
   one side (77%)". If that stratum was built on the prefix, the 77% is on the
   undercounting population. **Flagged, deliberately not rewritten** — restating a
   past analysis silently is worse than leaving it labelled.

*(Also noted for later: 302 configured vs 251 emitting means **51 enabled GN feeds
produced nothing** in the clean window, so the feed-level and emitting-source ratios
will drift apart by construction. Producer's issue, not this contract's.)*

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

**3,835 of 3,835 rows.** ⚠️ **Corroborated by a second run, but they are NOT the same
run and must not be cited as one:** NexusMind measured **7,478 rows over mutated
`data/raw`** (`_121003` + `_160810`) at **100.00%**, against this one's unmutated
producer bytes. Different corpora, different instruments — theirs reports classes
this one does not. **They agree on `source_group` at 100% and nowhere else is a
comparison licensed.** FluxusSource separately spot-confirmed a live row: exactly one
undeclared key.

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

### ⚠️ THE OFFSET GATE HAS THREE PARTS, NOT ONE — corrected 2026-08-14

**An earlier version of this section treated ovr#321 as *the* gate. That
under-counts in two directions at once**, and the issue's own thread warns against
exactly this reading: *"Do not read the first half as the gate."*

**1. FS#171 is ALIVE and aimed at `published_date` itself** — not at any nested key.
Confirmed by FluxusSource (`gh issue view 171`: OPEN, 3 comments, *"RFC 3339 offsets:
99.4% of rows carry no UTC offset, and ovr.news is silently reading them as local
time"*). Nothing in the redesign folded it, and **it did not die with
`published.instant`.** So dropping `instant` removed a *second* path an offset could
take and left the original one untouched — my "the gate is moot" was wrong
independently of anything about `instant`. ovr's ADR-046 is accurate.

**2. ⭐ The CLOCK FIX is an independent prerequisite, and it bites first.** From
FS#171 comment 3:

> Adding an RFC 3339 offset **serialises whatever the value already is.** For every
> local-clock row that converts a silent 2-hour error into a durable, explicit,
> **wrong** one. **The clock fix is a prerequisite for W1.1, not a follow-up** — and
> it is independent of ovr.news#321, which gates only the serialisation change.

**3. ovr#321** gates the serialisation change only.

```
clock_source stamped  →  clock fixed  ─┐
                                       ├─→  offset on published_date
ovr#321 lands  ────────────────────────┘
        two INDEPENDENT gates, not a chain
```

⭐ **This is why stamp-before-fix was the right sequence, and the reason is sharper
than "provability".** 3.87% of rows are stamped on a +2h local clock. Serialising an
offset onto those converts a silent error into an **explicit, durable, authoritative-
looking wrong instant** — corruption that reads as precision. The stamp is what lets
anyone separate the two populations *before* that becomes irreversible.

### What ovr.news answered, 2026-08-14

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

**1. ⛔ RETRACTED — TWICE, and the second retraction restores the original.** ovr told
me emphatically that *"the backfill is the wrong gate predicate; canonicalisation at
the write boundary is what protects the sort."* I rewrote this record for it. **Their
own adversarial review then refuted it, and ADR-046's original wording was right: the
backfill IS the gate condition.**

⭐ **Why, and it is a clean structural argument:** `summarize.ts:429` applies
`filterByAge(articles, maxAgeDays = 10)`, so **only rows ≤10 days old ever reach
`upsertArticle`.** But `create-hot-db`'s DELETE boundary is row #6,000 by
`published_date DESC`, which on production (21,743 rows) sits at
`2026-07-25T08:20:00` — **~20.2 days old.** A row at the delete boundary was last
written at least ten days ago and **can never be re-canonicalised.**
**Canonicalisation-at-write structurally cannot reach the one site the entire tie
argument is about. Only the backfill can.**

⭐⭐ **And the shape nobody had: the exposure is FROZEN AND DRIFTING TOWARD THE CUT.**
New aware rows canonicalise on arrival, so the collision set cannot grow — it is the
79 legacy `+00:00` rows and their naive twins. All 14 colliding instants sit at DESC
ranks **87–3,956** today, comfortably above the 6,000 cut. They drift down as
articles arrive, and **they cross the boundary AFTER passing the 10-day window that
would let a write fix them.** So *"nothing is near the boundary today"* has a shelf
life, and **the backfill's value increases with delay** — the opposite of how the
priority was framed to me.

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
| **NexusMind** | ✅ Ran the validator, supplied the `language` blocker, initially **declined** the declaration commit pending their owner (correctly — the thread had been stood down there). ✅ **The owner then lifted the stand-down directly, in their own words, and the commit is DONE** — `012da1a` on local branch `feat/contract-a-envelope-declaration`, not pushed, no PR. |
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

## ✅ The consumer declaration landed, and the outcome test passed on production bytes

**`012da1a`, local branch `feat/contract-a-envelope-declaration`, not pushed, no PR.**

Definition-of-done item 5 — the outcome test, over **7,478 live sadalsuud rows**.

⚠️ **CORRECTED. An earlier version of this section read "4 violation classes → 1" and
credited the envelope with a fix that was not its own.** Re-measured across all four
schemas on the same rows:

| schema | classes |
|---|---|
| 1.0.0 (`main`) | **4** |
| **1.18.0 (branch base, pre-envelope)** | **1** |
| 1.19.0 (envelope) | **1** |
| 1.20.0 (post-narrowing) | **1** |

**1.18.0 already reads 1.** The 4 → 1 belongs to the NM#304 / #356 / #357 work sitting
on the base, which fixed `source_type`, `metadata.required` and `priority`. **The
envelope never removed a violation class and never could — it only adds optional
properties.** Its real claim is the weaker and correct one: **it introduced no new
class.**

⭐ **The sub-pattern is the valuable part, and it is invisible from the after-state
alone.** *1 class* is the right answer and looks like a pass however you arrived at
it. Only re-measuring the **baseline** distinguishes *"we fixed three classes"* from
*"three classes were already fixed"* — and a before/after only measures your change
if "before" is the commit your change sits on. The original figure compared against a
run of `main` and labelled it "pre-envelope". *(Caught by NexusMind, self-reported,
after the instruction to re-run rather than assume.)*

**No new class.** Exit 1, which is correct while the hold stands. `source_group`
undeclared and the hold unspent, **verified after the fact rather than intended** —
the commit touches exactly that file. Plus **five falsification controls**, each
failing the suite it should: declare a `required` inside a block; open a block; widen
`language` to `oneOf`; declare `source_group`; make a block root-required. 1,303 unit
tests green.

⭐ **My branch question was not moot, and the answer inverts it.** I suggested the
envelope work should not land underneath NM#360's unmerged stack. The opposite is
true: **the acceptance criterion cannot pass on `main`.** #360 already fixes three of
the four measured classes (`source_type` enum gains `social`; `metadata.required`
drops to `source_category` alone; `priority` max 8→10) and already contains the
frozenset-vs-`required` test (`830f0e5`) plus a
`test_source_group_is_deliberately_still_undeclared` guard protecting the hold. On
`main`, a post-commit re-run yields 4 classes and *"same single class, no others"*
fails for reasons having nothing to do with the envelope. **#360 is a prerequisite
for the test, not an unrelated stack** — and the reason I had it backwards is that I
was reasoning about merge hygiene while the criterion was about what the instrument
can resolve.
