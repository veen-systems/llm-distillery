# Contract A — realization plan and per-repo briefs

**Written 2026-08-15 by the llm-distillery session, on owner instruction, for the
*next* session.** Two owner decisions are already taken and are recorded as such below.

⚠️ **This document is a brief, not an authorization.** Each repo's session still needs
its own owner go-ahead to write code — the FluxusSource session was explicit about that
(*"whether I start is my user's call, not mine to promise"*), and a peer telling them to
build would route around that decision rather than implement it. **Paste the per-repo
section; do not assume it has been read.**

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
| 5 | `published.element` | **pin an enum** | It records *which field the date came from* — a closed vocabulary. ⚠️ Wider than the 7 `date_fields`: `entry.time.datetime` and the `tags` term fallback also answer. Producer names it. |
| 6 | `collected.clock_source` | **pin an enum** | Closed set, and the producer already enumerated it: **three** clocks — 28 naive `datetime.now()` (local), 6 `utc_now()`, 2 `DateParser.get_timezone_naive_now()`. |
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

---

## Definition of done for the round

1. W0 items 1–4 merged on NexusMind, and **verified by reading the schema, not on
   report.**
2. FluxusSource emits `fabricated` + `had_timezone` + `raw` on real rows, and the
   **presence count is reported per field** — not a violation count. *(A violation
   count with no presence count beside it is how a vacuous confirmation reads as a
   pass; that happened on 2026-08-14 and two of three fields were empty.)*
3. `content_meta.kind` deploys **only after** W0 1–3, with `error` declared.
4. The canary exists, so "0 violations" becomes a statement about rows rather than
   about nothing.
