# Contract A — realization plan and per-repo briefs

**Written 2026-08-15 by the llm-distillery session, on owner instruction, for the
*next* session.** Two owner decisions are already taken and are recorded as such below.

⚠️ **This document was a brief, not an authorization.** Each repo's session needed its
own owner go-ahead to write code — the FluxusSource session was explicit about that
(*"whether I start is my user's call, not mine to promise"*), and a peer telling them to
build would route around that decision rather than implement it.

✅ **HANDED OUT 2026-08-15 by the owner, through this session.** Scope, as authorized:

| session | standing |
|---|---|
| `nexusmind` | **AUTHORIZED to write code** — W0, the pre-build shape pass |
| `fluxussource` | **AUTHORIZED to write code** — Track A (`fabricated` + `had_timezone` + `raw`, together) |
| `ovr-news` | information only, no work assigned this round |
| `pipeline-atlas` | information only; Category G needs an implementer, not a decision |

Two items went out at **different standing, deliberately**: `content_meta.error` is an
**owner ruling** (implement, don't relitigate); `published.had_timezone` nullability is a
**recommendation** the receiving session may improve on. Track B stays blocked on W0 1–3.
Each message also carried *"if your session holds a more recent owner answer, yours wins"* —
**a relay cannot carry recency.**

---

## The state, measured

| | |
|---|---|
| Contract A on NexusMind `main` | **1.20.0** (`25dc482`), root `additionalProperties: false`, 7 blocks, `required` unchanged at 8 keys |
| Fields declared | ~20 across `published` · `collected` · `fetch` · `content_meta` · `feed` · `origin` · `payload` |
| Fields **emitted** | **0**, across 14,409 rows / 6 collection runs |
| Validation status | **clean — because everything declared is optional and nothing emits.** A check that examines nothing reports success. |

---

## ⭐ The sequence in the old savepoint is BACKWARDS

The ordering everyone has been using is *"`kind` first, it's built; the three
`published.*` fields are the hard part."* Both halves are wrong.

**`content_meta.kind` is the MOST blocked item.** It is built and verified
(`7bc20a0`, 5,995 rows) and it **cannot ship**, because three shapes disagree and one
fails validation closed. None of that is coding work — it is one decision round.

**The three `published.*` fields are the LEAST blocked.** All declared, all optional,
all correctly typed (`raw`/`element` are `["string","null"]`, `fabricated` boolean).
**Nothing cross-repo gates them.** They can start the moment the owner says go.

⚠️ **`7bc20a0`'s own gate reads *"not for deploy until NexusMind's envelope declaration
merges."* It merged.** So the gate reads **green** while all three mismatches stand.
**A gate written as "wait for X to merge" tracks whether X happened, never whether the
two shapes agree.** Do not treat that commit message as a green light.

---

## W0 — the pre-build shape pass (do this FIRST, it is cheap and it is free now)

The `content_meta` defect class is **already latent in the fields nobody has built
yet**. Fixing it while **nothing emits** costs one schema commit; fixing it after
costs a coordinated redeploy.

⚠️ **A mechanical "string with no enum" scan flags 16 of 23 fields and is useless** —
`published.raw` is a publisher's literal string, `fetch.url_requested` is a URL. The
list below is after judgement. **Do not re-run the naive scan and treat its output as
the backlog.**

| # | field | change | why |
|---|---|---|---|
| 1 | `content_meta.error` | **DECLARE it** (string, nullable) | ⛔ **The only item that fails closed.** The producer emits it on derivation fault, `content_meta` is `additionalProperties: false`, so **the path added to keep a fault visible turns the fault into a contract violation.** ✅ **OWNER RULING 2026-08-15: NexusMind declares it** — consistent with the envelope finding that declaring is nearly free while a *missing* declaration is what costs, and dropping it would delete the signal in order to satisfy the checker. |
| 2 | `content_meta.kind` | **pin** `enum: ["feed_summary","headline_only"]` | Description names four notions; producer emits two. `full_text` is unemittable for **two independent reasons** (enrichment moved downstream, *and* `rss_aggregator` never reads `entry.content`), so removing one does not reopen it. |
| 3 | `content_meta.echoes_title` | **producer splits its one line** | `headline_only if not body or body == title` **fuses *empty* with *echoes-title***; the schema separates exactly those. **The schema's model is the better one** and both halves already exist in that line. Consumer of `echoes_title` cannot derive it from `kind` today, and vice versa. |
| 4 | `published.had_timezone` | **make nullable**, `null` when fabricated | ⭐ **The sharpest of these.** On a fabricated date there was no publisher value, so `false` conflates *"the publisher stated no timezone"* with *"there was no publisher value at all"* — **the same conflation as #3, one block over.** `had_timezone` exists specifically to make `fabricated` interpretable, and as declared **it cannot distinguish the case `fabricated` is about.** |
| 5 | `published.element` | ~~pin an enum~~ **DO NOT PIN — the premise is wrong** | ⚠️ **CORRECTED by FluxusSource 2026-08-15.** It records *which field the date came from*, and **the vocabulary is CLOSED FOR RSS (9 values) but OPEN OVERALL**: the API aggregators pass their own JSON keys (`publishedAt`, `created_at`, `publicationDate`, `year`, `atom:published`), so **a new aggregator adds a value.** Item 5 as written assumed one closed set. Producer captured it and **deliberately did not emit it**, so live data does not force the decision. *(`tags.term` stays in the vocabulary though it is **reachable in code and dead in data** — its gate is `'date' in term` and it then parses the whole term, so a term qualifies only by containing the word that makes dateutil refuse it. Narrower-than-emittable fails closed. Independently re-derived, and it matches FS#138's guard from the other side.)* |
| 6 | `collected.clock_source` | **pin an enum — but TWO values, not three** | ⚠️ **CORRECTED by FluxusSource 2026-08-15.** **Three call sites, TWO clocks.** `utc_now()` and `DateParser.get_timezone_naive_now()` read the **same** clock (one aware, one naive-UTC) and after canonicalization **serialize identically**. So "three clocks — 28/6/2" is an accurate count of *call sites* and would be a **misleading enum**. Verified 28+6+2=36 with no other spelling. Proposed: `host_local` (`datetime.now()`, the FS#176 defect) and `utc`. A three-value split is available if the call-site distinction is wanted for debugging — but that is a debugging affordance, not the vocabulary. |
| 7 | `published.precision` | **pin an enum when the producer names it** | The only field that is genuinely new code rather than threading-out. Record the requirement now so it is not discovered at build time. |
| 8 | `fetch.at` | **add the canonical timestamp `pattern`** | It is a timestamp, and the canonicalization work (`94e7337`, FS#174) established one spelling. Declaring it unconstrained re-opens the defect that work closed. |
| 9 | `content_meta.truncated` | **reassign or drop, deliberately** | **Declared with no producer, and against the wrong one.** *"Whether the **source** truncated the body, as opposed to the body simply being short"* is real — but unanswerable from a feed: it needs the feed body compared against the full article, and full-text fetch lives downstream since `full_text_fetcher.py` was deleted from FluxusSource. |

**Lower priority, and `origin.*` is sequenced separately anyway:**
`origin.country` / `origin.region` / `origin.timezone` are unpinned strings that
plausibly want ISO 3166 / IANA vocabularies. Note, don't block on it.

---

## The two tracks, and they are independent

### Track A — `published.*` (UNBLOCKED, can start immediately)

`fabricated` + `had_timezone` + `raw`, **together, never `fabricated` alone.**

⚠️ **`fabricated` has TWO call sites with two populations that do not compose.**
`extract_date_from_rss_entry:106` (RSS, `fabricate_fallback=True` so it never returns
None) **and** `DateParser.ensure_valid_date:217`, which serves the
`news_api`/`github`/`academic`/`patent` aggregators. **One stamp reading as one
mechanism would be wrong.**

⚠️ **`had_timezone` cannot be captured where the original brief pointed.**
`normalize_timezone:175` is called from *inside* `parse_date_string`, so by the time
`extract_date_from_rss_entry:110` calls it the value is **already naive** and that call
can never see an offset. **Capture belongs inside `parse_date_string`.**

**Why this is now urgent rather than tidy:** the microsecond fingerprint that used to
identify fabricated dates was **erased in production** by the canonicalization deploy
(first clean run `collection_20260814_193603`). It was an accidental, undocumented
signal and it vanished when someone touched serialization for an unrelated reason.
`published.fabricated` is what replaces it, **explicitly and on purpose.**

⭐ **And inference cannot substitute — this is settled, not arguable.** At least
**three** mechanisms produce a ~2h `collected − published` gap and only one is
fabrication (see `memory/date-error-recency-boost-hypotheses.md`). Worse, a *fourth*
combination — `ensure_valid_date` fabrication **plus** the FS#176 local-clock skew —
lands at **4h**, outside FS#173's own detection window. **Measured: 46 rows at
`4h ± 5s` over 155,513, 32 `semantic_scholar`, 32/32 microsecond-fingerprinted with
published and collected agreeing to ~35µs.** So **FS#173 undercounts fabrication**, and
a fixed-gap detector is keyed on **the producer's clock** — a new constant per
aggregator *and* after every DST transition.

### Track B — `content_meta.kind` (BLOCKED on W0 items 1–3)

Built, reviewed, verified over 5,995 production rows (emitted on exactly the 5,739 RSS
rows, 0 schema violations). ⚠️ **The commit is `7bc20a0` on
`feat/contract-a-content-meta-kind` — NOT `f3e8954`**, which was amended away, is an
ancestor of no branch, and is GC-eligible.

**Consumer-side spec** (llm-distillery, `#93`), written but deliberately **not built**
— `kind` is emitted on 0 of 14,409 rows today, so it would be dead code with green
tests:

- **The fallback keys on `source_type`, NOT on the field's absence.** Absence means
  **not applicable, not unknown** — there is no feed document behind an api/social/data
  row, which is also why `kind` can never become `required`. RSS row with no `kind` ⇒
  pre-deploy data, fall back to length. Non-RSS row ⇒ do not apply a document-shaped
  prefilter at all.
- ⚠️ **`kind` does NOT retire the 300-char floor on its own — that is `#114`.** Its
  derivation never looks at length; the floor's documented rationale is oracle
  framework-leakage, which is a function of **how much text the oracle sees.** A
  143-char `feed_summary` still hands the oracle 143 chars. **Three repos hold three
  views of why that floor exists and none has evidence.** Ship `kind` for what it does
  measure — headline-only vs complete-short — and leave the floor alone.

### Then, in order

`collected.clock_source` → `fetch.*` → `element` → `precision` last.

⭐ **`clock_source` has a second, independent justification now: FS#176.** The clock
defect is a **correctness bug in its own right**, not discriminator hygiene —
`collected_date` is on the host local clock for 8 of 768 sources, and canonicalization
gave that value the *identical shape* to a correct UTC one, so the skew is now
invisible in the field itself.

---

## Per-repo briefs — paste these

### ▸ fluxussource

> Contract A realization. **Track A is unblocked and can start now; Track B cannot.**
>
> **Build `published.fabricated` + `had_timezone` + `raw` TOGETHER** — never
> `fabricated` alone. Two things the original brief got wrong: `fabricated` has **two**
> call sites (`extract_date_from_rss_entry:106` and `ensure_valid_date:217`, the latter
> serving news_api/github/academic/patent) whose populations do not compose; and
> `had_timezone` must be captured **inside `parse_date_string`**, because by
> `extract_date_from_rss_entry:110` the value is already naive.
>
> **Ask NexusMind to make `published.had_timezone` nullable before you emit it.** On a
> fabricated date there was no publisher value, so `false` conflates *"publisher stated
> no timezone"* with *"there was no publisher value"* — the field exists to make
> `fabricated` interpretable and as declared it cannot distinguish the case it is for.
>
> **`content_meta.kind` is blocked, not ready** — despite `7bc20a0`'s gate reading
> green. Three shapes disagree: `error` is undeclared on a closed `content_meta`
> (**fails validation closed** — owner has ruled NexusMind will declare it), `kind`'s
> enum is unpinned, and `echoes_title` is a split your one line collapses. **Adopting
> their split is cheap — both halves are already in
> `'headline_only' if not body or body == title else 'feed_summary'`.**
>
> **Name two vocabularies** so NexusMind can pin them: `collected.clock_source` (you
> already enumerated three clocks) and `published.element` (wider than the 7
> `date_fields` — `entry.time.datetime` and the `tags` fallback also answer).
>
> Unchanged: **FS#174 stays on its ~2026-08-21 hold.** FS#176 (the local-clock
> `collected_date` on 8 sources) is a correctness bug and gives `clock_source` its
> second justification.

### ▸ nexusmind

> Contract A realization. **You own W0, the pre-build shape pass, and it blocks the
> producer.** Nine items in `llm-distillery/docs/CONTRACT_A_REALIZATION.md` § W0; the
> first four matter most.
>
> 1. **Declare `content_meta.error`** (string, nullable). ✅ **Owner ruling
>    2026-08-15.** It is the only mismatch that fails closed: FluxusSource emits it on
>    derivation fault, your `content_meta` is `additionalProperties: false`, so the path
>    that exists to keep a fault *visible* turns it into a contract violation.
> 2. **Pin `content_meta.kind`** → `enum: ["feed_summary","headline_only"]`.
> 3. **Keep `echoes_title` — your split is the better model**, and tell FluxusSource so;
>    their `headline_only` fuses *empty* with *echoes-title*.
> 4. **Make `published.had_timezone` nullable.** Same conflation, one block over, and it
>    defeats the field's whole purpose.
>
> Then: pin `published.element` and `collected.clock_source` (FluxusSource is naming
> both), add the canonical timestamp `pattern` to `fetch.at`, and **decide
> `content_meta.truncated` deliberately** — it is declared against the wrong producer,
> since detecting source truncation needs a full-article comparison and full-text fetch
> lives downstream.
>
> **Still yours and still blocking: the canary.** Until it exists, "0 schema violations"
> means "nothing was checked" — currently literally true, since **0 of ~20 declared
> fields are emitted across 14,409 rows**. It blocks W2.2 declaring `source_group`,
> which is emitted on every row and declared nowhere.

### ▸ ovr-news

> No Contract A work is assigned to you this round; you are downstream of the producer.
> Two carried items, neither new:
>
> - **The corpus backfill is still authorised and not run** — and it is the only fix
>   that reaches `create-hot-db`'s delete boundary, since rows there are ~20 days old
>   and only ≤10-day rows get rewritten.
> - **`published_date` is relayed byte-for-byte** by NexusMind (proven on a 6,024-row
>   byte-identical join), so anything FluxusSource changes about its spelling reaches
>   your ~20 lexicographic sort sites unchanged. FS#174's offset tightening is on hold
>   until ~2026-08-21; the canonicalization that already shipped narrowed the spellings
>   to one.

### ▸ pipeline-atlas

> **Category G's grain decision is TAKEN** (llm-distillery, 2026-08-14) — it was never
> spec-ready, and the blocker was a decision rather than an implementer. Your correction
> drove it: the grain problem was not intrinsic to G, it **arrived with four fields that
> were never G's**. `health_state`/`raw_item_count`/`items_emitted` move out to A–F;
> `poll_interval_actual_h` stays (the only field that can expose FS#121);
> `refusal_reason` is named an aggregate; `outcome` is written at the refusal site.
>
> **G now needs an implementer, not a decision** — candidate FluxusSource, after Track
> A. Two spec lines are still owed and they are yours: *"measured at fetch"* requires
> **adding a read that does not exist**, and the enum has no value for FS#121's
> *"fetched, but on the wrong cadence"*.
>
> If the atlas ever displays a collection-lag figure: **that number is a property of the
> tick, not of the source's timeliness.** arXiv's gap reads 14.08h / 2.06h / 6.12h /
> 10.10h across four consecutive deliveries because it publishes at a fixed instant and
> the collector walks.

#### ✅ DELIVERED 2026-08-15 — both spec lines, and one of them corrects this brief

pipeline-atlas returned the normative text the same day. **The lag-figure trap was
already answered on their side** — `fluxussource.qmd:62` carries the sawtooth prose
(*"that age is a phase of the tick, not a measure of freshness"*), landed `b8514fb`.

⚠️ **Correction to the brief above: "measured at fetch" needs a new WRITE, not a new
read.** Verified here against FluxusSource's code rather than adopted on report.

**Spec line 1 — `poll_interval_actual_h`.** Normative: elapsed hours between this fetch
and the previous **ATTEMPTED** fetch of the same source name, recorded at the collection
path. **MUST NOT be read from configuration** — `config.update_frequency` is the interval
the source is *supposed* to be polled at, and FS#121 is exactly the case where actual and
configured disagree, so a config-sourced value confidently reports the interval the source
is failing to be polled at. Requires a new per-source-name `last_fetch_attempt_at`, written
on **every dispatch** (failures and post-dispatch refusals included) for **all enabled**
source names, not the scheduled subset. `null` on the first cycle after that store exists,
and **`null` MUST mean "no prior attempt recorded", never "interval is fine"**.

⛔ **The trap an implementer reaching for the nearest field will fall into.** The only
persisted per-source timestamp is `SourceState.last_collected`, and it fails on both
counts — **verified 2026-08-15**:
- **The rows don't exist for the population that needs them.** State rows are created by
  iterating `aggregator_frequencies` (`content_collection.py:390-391`); the FS#121
  population **is** the `else` branch at `:184`, i.e. sources with no
  `aggregator_frequencies` entry. No prior timestamp to subtract from, for exactly the
  sources the field exists to expose.
- **It is a last-SUCCESS timestamp, not a last-FETCH one.** `last_collected = now` is at
  `json_source_state_manager.py:348`, inside the `collected_sources` loop (`:342`); the
  `failed_sources` loop (`:356-373`) advances `consecutive_failures` and `next_due_time`
  and leaves it untouched. **On a source in exponential backoff, `now − last_collected` is
  inflated by the whole failure streak and reads as UNDER-polling while the source is being
  polled on schedule and failing.** One value, two meanings — the shape G exists to stop.

*Corollary:* every cadence-fit state FluxusSource has today is derived against the
**configured** interval — `FeedHealthRecord.update_frequency_hours` is a "snapshot of
configured poll interval" (`feed_health_tracker.py:153`), fed from `config.update_frequency`
(`concurrent_rss_aggregator.py:252`), and both the `THROTTLED` and `OVER_POLLED` branches
read it. **So `OVER_POLLED` cannot see FS#121 either.** That is the argument for keeping
`poll_interval_actual_h` at all.

**Spec line 2 — `outcome` was already right; the missing field is the SELECTION BRANCH.**
Normative: **`outcome` MUST NOT gain an over-polled value.** FS#121's shape is not a
refusal — the source is fetched and delivers items; the defect is the cadence, and a
cadence judgement does not belong in a field recording what happened to *this* fetch.
`outcome: fetched` / `refusal_site: null` is the correct record. G carries
**`selection_branch`** instead, one value per Site A branch —
`always_run | due | self_scheduled | unscheduled_fallback` — **written at the branch that
fires, never derived.**

⚠️ **AMENDED by pipeline-atlas the same day, before the text set — and the amendment is
the more useful half.** The original line read *"`unscheduled_fallback` is the FS#121
signal, available on the first cycle."* True as written, **misleading by omission: nobody
had checked whether the fall-through fires at all. It does not.** Measured, and
**reproduced independently here 2026-08-15**: 20 enabled sources, 24 scheduled,
**unscheduled population EMPTY**, with `test_source_registration_121.py:59-69` asserting
exactly that set difference. Replacement text, as pinned:

> `unscheduled_fallback` is expected to be **EMPTY on ships-day** — the static case is
> already held by `test_no_enabled_source_falls_through_to_every_tick`. The field exists
> to catch **what that test cannot: a divergence between the config CI reads and the
> config the tick ran against.** Its value is a per-tick observation of the running
> system, not a first-cycle finding.

**So `selection_branch` is a REGRESSION detector, not a detector of a live defect** — sell
it as that, or its first cycle reads as *"the field found nothing"* and it gets cut. ⚠️ It
also narrows the standing claim that `poll_interval_actual_h` is *"the only field that can
expose FS#121"*: **there is currently nothing to expose**, and the static case is guarded
in CI, so the field's value is confined to the case the test cannot see — **name that case
in the spec rather than leaving it implicit.**

⭐ **And that case is this plan's own signature shape.** The guard asserts a property of
**the checkout's** `config/app.yaml` at **CI time**. Neither it nor CI can see the tick
that actually ran, on the host, against the config that was actually live. **"A test
passes" is not "the mechanism ran"** — present, configured, tested, and still able to
diverge where nobody is looking. *(11th occurrence of the unreachable-mechanism shape.)*

⚠️ **The instrument trap, recorded because it was nearly shipped as the finding:**
`grep "has no entry in aggregator_frequencies" logs/` returns **n=0, and that zero is
uninterpretable** — the control reached for, `"not due yet"`, also returns 0, but that line
is `logger.debug` and the log captures INFO and above. **A zero from an instrument whose
denominator you have not established.** The measurement that replaced it carries a mutation
(drop `patent` from `aggregator_frequencies` ⇒ prints `['patent']`) so the instrument is
shown able to go non-empty, and an `assert` so an unparseable config fails rather than
reads zero.

All four branches of `select_sources_to_collect` (`content_collection.py:165-197`) append
to `sources_to_collect` identically, so **`news` every tick (correct) and a weekly source
every tick (a 42× over-poll, per the branch's own comment) are indistinguishable in G's
output today.** The discriminator is not missing from the system — the `else` branch
already logs a warning naming the source and issue #121 at `:191-196`. **It exists, and it
is discarded at the log boundary.**

⭐ **SEQUENCING, and this is the part to act on: build `selection_branch` FIRST.** It costs
no new measurement and is observable on the **first** cycle after G ships;
`poll_interval_actual_h` needs a new store and **two** cycles. The branch field is the
cheaper and earlier instrument, and it is what makes the interval number interpretable when
it arrives. **The call survives the amendment above and gets a better justification:**
`selection_branch` is precisely the field that closes the gap between *"no source is
unscheduled in the checkout"* and *"no source was unscheduled on this tick, on this host."*
⚠️ Expect it to report `always_run | due | self_scheduled` for all 20 and
`unscheduled_fallback` for none — **that is the correct first-cycle result, not a null
finding.**

*Also verified in code rather than asserted:* `self_scheduled_sources` is exactly
`{'concurrent_rss'}`, so the one source name for which `poll_interval_actual_h` would be
per-**feed** takes the self-scheduled branch and never the `else` branch.

**Still true: G needs an implementer, and was not authorized to anyone this round.**
Candidate remains FluxusSource, after Track A. pipeline-atlas deliberately did not copy
them in.

---

## Definition of done for the round

1. ✅ **DONE.** W0 items 1–4 merged on NexusMind — **Contract A 1.22.0** (1.21.0 took
   1–3; this pass took 4 and 8, recorded 5–7 as owed), verified by reading the schema
   back, not on report. 39 contract tests, full suite 1315 green, ten mutations each
   reverting exactly one change and **all ten bite** — including *loosening* `fetch.at`
   to accept `Z` and *inventing* a `clock_source` enum, i.e. mutations in **both**
   directions. Two deliberate divergences, both accepted: `content_meta.error` is
   **non-nullable** (no branch of `return {'error': type(exc).__name__}` can yield null,
   so a nullable declaration obliges a consumer branch that can never be tested — and
   the ruling settled *whether to declare*, the `(string, nullable)` here was this
   document's parenthetical inheriting authority by adjacency), and nullability extended
   to `published.precision` for coherence. **Uncommitted; the commit is the owner's call.**
2. ✅ **DONE.** FluxusSource emits `fabricated` + `had_timezone` + `raw` on real rows,
   **reported as a presence count per field.** Live 45-feed sample + live academic APIs,
   2026-08-15: RSS 687 rows, `published` block / `raw` / `had_timezone` / `fabricated`
   all **687/687 = 100.00%**, `fabricated=true` **25/687 = 3.64%**. API 101 rows,
   `published` / `fabricated` **101/101**, `raw` / `had_timezone` **76/101 = 75.25%**.
   Producer-schema violations 0/788, **reported beside the presence counts, not instead.**
   ⚠️ The 75.25% is deliberate: PubMed's date is **real but assembled** from separate
   `<Year>/<Month>/<Day>` elements, so no publisher string exists to quote, and nulling
   `raw`/`had_timezone` there would put **the fabricated spelling on a non-fabricated
   row.** Producer rule: **`null` ⟺ `fabricated`; an unrecorded observation is OMITTED.**
   Validates against 1.22.0 as written; a one-line doc amendment is with NexusMind.
   **Uncommitted, not deployed — the deploy is the owner's call.**
3. `content_meta.kind` deploys **only after** W0 1–3, with `error` declared. *(Still
   unmerged on `feat/contract-a-content-meta-kind`; Track B was not authorized.)*
4. The canary exists, so "0 violations" becomes a statement about rows rather than
   about nothing.
5. ⛔ **RETRACTED THE SAME DAY — I RECOMMENDED SPENDING THE ONLY ACCEPTANCE CONTROL.**
   I recorded here that the 788/788 `source_group` failure made W2.2 a **prerequisite**
   for the canary. **That was wrong, and NexusMind declined it correctly.** The facts are
   unchanged and verified — 1.22.0 root is `additionalProperties: false`, 21 root
   properties, `source_group` not among them, so a consumer-side "0 violations" is
   unobtainable from real rows. **The inference from them was the error.**

   ⭐ **`source_group` is not merely undeclared — it is the production contract check's
   ONLY NON-CIRCULAR ACCEPTANCE CONTROL**, and that was already written down: NM#304,
   `contracts/CHANGELOG.md` 1.18.0, guarded by a pre-existing test I had not read
   (`tests/unit/test_contracts.py:178`, `test_source_group_is_deliberately_still_undeclared`),
   which failed by design the moment NexusMind tried it. An independent field
   **that the check was never shown** — and therefore the only evidence the check
   **can fail at all.**

   ⚠️ **Two corrections to the numbers (2026-08-15, conformance run on 165,107 DELIVERED
   rows), and neither changes the decision.** (a) **`source_group` is on 33,787 / 165,107
   = 20.5%, not 100%** — the 100% figure is true of *today's* producer and false of the
   delivered archive, so a canary's day-one failure rate there is ~21%, not 100%. Less
   dramatic than the argument assumed — **and yet the hold gets STRONGER, because a
   control firing on a fifth of rows rather than uniformly is MORE discriminating: it
   distinguishes archive vintages, which a synthetic replacement could not.**
   (b) **`eval_query` is a SECOND undeclared root field, 511 rows**, same fail-closed
   mechanism. All three sessions had been saying *the* undeclared field; there are two.

   ⭐⭐ **The trap, which is the transferable part: declaring it spends that control
   PRECISELY IN ORDER TO DRIVE A VIOLATION COUNT TO ZERO — the very number whose
   trustworthiness the control exists to establish.** A synthetic replacement is circular
   in exactly the way the original is not: injecting a key you chose proves the check
   catches **what you already knew to look for**, while `source_group` proves it catches
   **something nobody designed it to catch.** Not replaceable once spent.

   **So the original ordering was load-bearing, not arbitrary, and 788/788 is an argument
   for building the canary SOONER — not for spending the control first.** The "automatic
   caller" the parked test names *is* the canary. Item 4 stands as written; this item is
   kept as the record of the error, not as an instruction.

   *(The compounding observation survives and is sharper: local `data/raw` reads clean,
   delivered bytes read 100% failure, both wrong in opposite directions. What changed is
   which one gets fixed first.)*

6. ✅ **Contract A 1.23.0** — `clock_source` pinned `["host_local","utc"]` (the
   two-clocks correction, verified against the producer's call sites); the `99.22%` figure
   **inverted rather than deleted** in `had_timezone`, now reading *"EXPECT ~100% TRUE,
   NOT ~1%"* with the measured 737/737 and the note that **~100% is also what the bug
   looks like**; the assembled-date third state documented. 43 contract tests, full suite
   1319, **sixteen mutations all biting** — including two asserting the reverts stay
   reverted and one that pins `element` flat and must fail.

   ⚠️ **Two reverts, both driven by pre-existing tests, both worth carrying.**
   `required: ["fabricated"]` was added to disambiguate the producer's three states and
   reverted when `test_no_property_inside_a_block_is_required` and
   `test_an_empty_block_is_valid` failed — their stated purpose is that a producer
   emitting a block **one property at a time is never red while behaving correctly**,
   which is the envelope decision's core invariant. Per NM#300 **`required` is EARNED from
   production presence, never granted at declaration** — and Track A is built but *not
   deployed*, so its 788 rows are a working-tree measurement, not production presence. The
   disambiguation became a read-time obligation on the consumer instead. **No test was
   modified: a failing test is a finding, not an obstacle.**

   `published.element` diverges from my "do not pin" and **the divergence is better than
   my call.** It is not a flat enum but a root conditional — `if source_type == 'rss'
   then element ∈ RSS_DATE_ELEMENTS ∪ {null}`, unconstrained otherwise — which constrains
   exactly the half that is closed and leaves the open half open. My objection was to a
   flat pin assuming one closed set; this is not that. Tests assert both directions,
   including that `publishedAt` **passes** on an api row, so it cannot silently become a
   flat enum. `element` is not emitted, and it is one commit to revert.
