# Contracts: a five-repo plan

**Draft 1 + review round 1, 2026-08-13 evening. Written by the llm-distillery
session; reviewed by the FluxusSource, NexusMind, ovr.news and pipeline-atlas
sessions.** Every number is measured; provenance, the verify commands and the
instrument defects that constrain how these numbers may be quoted are in
`memory/stamp-contract-integrity.md` § *The contracts layer*.

⛔ **Review rounds 1–4 (2026-08-13 → 08-15) are in `CONTRACTS_PLAN-rounds-archive.md`**, moved verbatim 2026-09-27. This file keeps the plan, its decisions and the baseline. The plan has had no edit since 2026-08-15: re-check any status here before acting on it. The last status of unexecuted items is § *Standing after round 4*, kept at the end of this file.

## ✅ STATUS 2026-08-14: PHASE 0 APPROVED BY THE OWNER. Phases 1–3 are NOT.

**Approved:** build the check in **reporting mode**, write the artefact, install its
timer on sadalsuud, and ship pipeline-atlas's reader. **Owner explicitly approved the
systemd unit install**, which NexusMind had correctly refused to do without it.

**NOT approved and NOT to be started:** phases 1–3 and `eval_query`. **None of them
blocks phase 0** — they can stay open throughout it.

⚠️ **The envelope (W1.4) and its additive path came OFF this list later the same
day.** The owner reopened and delegated both — *"then settle the shared envelope,
because `additionalProperties: false` on both schemas makes it a hard blocker for
shipping anything incrementally"* — in the context of implementing the Contract A
redesign (#112). **Settled: `docs/decisions/2026-08-14-contract-a-envelope.md`.**
See `CONTRACTS_PLAN-rounds-archive.md` § *Round 3* for the four peer answers and what they changed.

**Two standing holds:**

- 🔒 **Do NOT declare `source_group` (W2.2)** until the check has reported it. It is
  the only test that proves the check *detects* rather than merely *runs*, and
  declaring it spends that permanently.
  ⭐ **UPDATE 2026-08-15: the check HAS reported it** (`asserted=true, rows=2722,
  errors=2722`, `collection_20260815_120555`) — **and the hold still stands**, on the
  second half of the condition: the run was a hand invocation and the timer has never
  fired. See `CONTRACTS_PLAN-rounds-archive.md` § *Round 4*. **Reported-by-hand and reported-by-the-caller are different
  events, and only the plan's own sequencing rule ("the CALLER, then W2.2") separates
  them.**
- 🔒 **Do NOT make any check stricter** until its drops reach a reader — see
  *reader before stricter*.

### Phase 0 progress, 2026-08-14

| item | state |
|---|---|
| arming panel (pipeline-atlas) | ✅ **SHIPPED**, `ff9dcc6` — both units render **NOT ARMED · unit not installed** |
| phase 0b check + artefact (NexusMind) | 🔨 **BUILT + PR'd, NOT INSTALLED** — PR **#361**, depends on **#360** (`#357`+`#356`+`#304`, 8 commits) |
| artefact reader (pipeline-atlas) | ⏸ **DEFERRED by their owner** until the spec stopped moving. It has now stopped |
| install on sadalsuud | ⛔ **NOT DONE, and owner-held** — *"build and commit, do NOT install."* It needs interactive sudo, so it may stay with the owner permanently |

⭐ **MEASURED ON GENUINE, UNMUTATED PRODUCER BYTES** —
`collection_20260814_121004`, **3,835 rows**:

```
status: found_violations | overall: error | not_asserted: 2 | rows: 3835
  drift.contract_a_frozenset_vs_required     asserted=True  sev=clean
  published_date.format.date_time            asserted=False
  unreported.schema_invalid                  asserted=False
  additionalProperties.<root>.source_group   asserted=True  rows=3835  sev=error
```

**One violation class, and it is the held control.** Nothing else — which is **#304
confirmed against producer output rather than our reconstruction of it**, a stronger
statement than every Contract A figure measured earlier in this document.

⚠️ **`overall_status` CANNOT read `clean` today, by construction, and that is the
rung working — not a panel bug.** Two classes are permanently unassertable:
`published_date.format.date_time` (no `rfc3339-validator`) and
`unreported.schema_invalid` (counters exist, no surface to publish on). Since
`overall_status` may not read `clean` while `classes_not_asserted > 0`, the best
attainable today is `info`.

**Assignments:** phase 0b → **NexusMind** (their validator, their data, their box).
Reader → **pipeline-atlas**, shipping *now* in its UNKNOWN state. **Units:
`nexusmind-contract-check.timer` / `nexusmind-contract-check.service`** — matching
sadalsuud's existing `<project>-<function>` convention (`fluxus-collection`,
`pipeline-atlas-refresh`, `ovrnews-backup`).

**Round 2 HAS been run** — see `CONTRACTS_PLAN-rounds-archive.md` § *Round 2 — the sweep*.

⚠️ **"Nothing was committed in any repo" is NO LONGER TRUE and the correction
matters.** NexusMind has **four commits on branch
`fix/357-contract-validator-grouping`** (`b8a191c` NM#357, `f55f708` NM#356,
`99c74a4` NM#304, `830f0e5`), scoped from issues that **predate this plan**.
**`main` is `010338d` and contains none of them; no PR has been opened.**
FluxusSource and ovr.news both have verified work uncommitted in their trees.

⭐ **"Built" is not "merged" and "merged" is not "running"** — all three states are
live in this estate right now, and two sessions (including this one) reported a
branch as shipped today. `deploy_filters.sh` only auto-pulls when the **scorer
paths** differ, so a merged non-scorer commit waits for an unrelated filter change
to drag it in. See `memory/gotcha-log.md`, *"Detection is path-scoped, the action is
repo-wide"*.

⚠️ **Draft 1's headline premise was FALSE and is corrected below.** It asserted
that nothing anywhere runs a consumer schema against real producer bytes. There
are **four** validators; see § *The problem*. The claim came from grepping for one
script *name* rather than for the *behaviour* — the error this plan exists to fix,
committed while writing the plan. Left visible rather than silently patched.

⚠️⚠️ **AND "four" IS ALSO WRONG — corrected in round 2, 2026-08-14, by the sweep
that round 1 asked for.** Sweeping for the *behaviour* across all 20
`veen-systems/` repos finds **at least 21** mechanisms that check structured data
against a declared shape, of which round 1 counted four. **This is the same method
error a third time**: round 1 searched one script *name*, then searched for
*validators* — but not for validation done by code that is not called a validator,
by a database, or in a browser. **Do not quote "four".**

---

### ⭐⭐ THE FINDING, in its final form (NexusMind, round 2)

**Counting validators is the wrong instrument, and "unscheduled" is not the
finding.** State it this way instead:

> **The estate has exactly TWO shape checks that are both automatically invoked AND
> looking at real production bytes. Between them they assert eight top-level key
> names and two strings' maximum length.**
>
> **Everything with real coverage has no caller. Everything with a caller has no
> production data.**

That survives someone adding a caller to one script, it does not decay when a count
changes, and it names the gap instead of counting the furniture. **Every "N
validators" figure in this document is subordinate to it.**

The two are `scripts/main.py:1008` (8 key names, drops the row) and the GPU scoring
API's pydantic models (two optional strings) — both detailed in `CONTRACTS_PLAN-rounds-archive.md` § *Round 2*.

**Scope of the "exactly two", stated so the absolute is bounded** *(tested here
against the producer, not inherited)*: it counts mechanisms that **check a row's
shape and reject or drop on it**. `FluxusSource/scripts/validate_output.py` does run
on real bytes but has **no automatic caller** (3 executable mentions: itself, one
reference, one test), so it does not qualify. `ContentItem.__post_init__` **is**
automatic on real bytes but **normalises rather than rejects** — a different category,
not a counter-example. If a third mechanism is found that both fires automatically
and drops on shape, this number moves and the sentence must move with it.

---

## The problem, in one paragraph

FluxusSource emits ~3,500 rows/cycle as JSONL. Three schemas claim to describe
that stream — the producer's `output_schema.json`, NexusMind's Contract A, and
NexusMind's Contract B — and **none of them tracks it.** Contract A was red on
every production cycle measured (three defect classes, plus `source_group`) and
has had exactly one commit ever. The producer's schema is green because it asks
less. Contract B is green *and undescriptive* — it declares `metadata` with zero
properties.

**The estate has FOUR contract validators, and none of them watches the thing
that broke.** *(Corrected in review round 1 by the ovr.news session, which refuted
draft 1's "nothing runs a validator"; the extra two were then found here by
sweeping for validators rather than for one script name.)*

| validator | runs on real bytes? | watches? |
|---|---|---|
| `FluxusSource/scripts/validate_output.py` | **yes**, with a track record — found 559 relative-URL rows in its first week and dated the 4-class cluster to `collection_20260807` | its own schema only — structurally blind to what consumers believe |
| `ovr.news/src/lib/data/validate.ts` | **yes**, at `summarize.ts:404`, per filter, **since 2026-03-03** — and it **drops rows** (`:148`, `:174`) into a log with no reader | `grep -c "published_date\|metadata"` → **0**. Blind to both fields this plan is about. A **third undeclared gate** at ovr |
| `NexusMind/scripts/validate_production_contract.py` | yes, when invoked | **no scheduled caller** |
| `NexusMind/validate/validate_contract_a.py` | yes, has a `--latest` mode | **no caller at all** |

Plus NexusMind CI, which runs `tests/unit/test_contracts.py` on **fixtures**.

**So the defect is not absence — it is that the validators which run are blind to
the failure, and the validators which would see it are unscheduled.** State it as
*unscheduled*, never *never executed*: no file naming a script is not proof
nobody ran it interactively (pipeline-atlas's caveat; they re-derived the
zero-caller result across all **20** repos under `veen-systems/`, not five).

⚠️ **`grep -rIl` returning nothing is a broken verify command**, because
pipeline-atlas's `run_verifies.sh` treats empty output as failure — the strongest
evidence in this plan becomes a check that fails while being right. Every
"returns zero" figure here needs inverting to print its count.

**The through-line: greenness is not evidence that a schema tracks reality.**
**Four** independent demonstrations, which is a pattern rather than an anecdote —
and the fourth is the strongest because a reader can run it in ten seconds.

1. FluxusSource's own schema is green because it asks less (no `required`, open
   `metadata`, 7 of 52 keys declared).
2. Contract B is green **and undescriptive** — `metadata` declared with zero
   properties.
3. NexusMind CI is green on **fixtures**, which can only confirm the belief that
   wrote them.
4. **⭐ Contract A already declares `format: "date-time"` on `published_date`,
   `collected_date` and `original_published_date` — and it has never been
   checked.** *(Found by NexusMind in review round 1; verified independently
   here.)* RFC 3339 `date-time` **requires** a UTC offset, so the 99.4% naive rows
   violate a declaration Contract A has carried since its single commit. Nobody
   saw it because `validate_production_contract.py:121` is `Draft7Validator(schema)`
   with no `format_checker`. **And the obvious one-line fix silently does
   nothing:**

   ```
   jsonschema 4.19.2   date-time checker registered: False
                                     bare    with format_checker=FormatChecker()
     '2026-07-26T06:00:03'           PASS    PASS
     '2026-07-26T06:00:03+02:00'     PASS    PASS
     'not-a-date'                    PASS    PASS      <-- not even a date
   rfc3339_validator NOT installed
   ```

   `format_checker=FormatChecker()` **no-ops for `date-time` unless
   `rfc3339-validator` is installed** — so enabling it looks like a fix, turns
   nothing on, and produces a green check that validates less than the reader
   believes. **This sits inside the very tool phase 0 is built on.**

   **Consequence for the plan: W1.1 is NOT a new ask on the producer.** It closes
   an already-declared, never-enforced requirement — a much easier conversation,
   and it means both schemas already agree on the intent. Enabling format
   assertion is a **two-part** change (`format_checker=` **and** the
   `rfc3339-validator` dependency); ship one without the other and you get a false
   green.

---

## Four principles this plan is built on

1. **Declare more, cut nothing.** *(Owner ruling, 2026-08-13.)* A declaration is
   nearly free; a **wrong** declaration and a **missing** one are what cost.
   `source_category` rode on 100% of rows for months undeclared, and two repos
   independently reverse-engineered it out of the flat `source` string. **Zero
   readers today may be a consequence of not declaring, not evidence of
   uselessness.**
2. **Declare from the REACHABLE set, never wider than emitted.** *(FluxusSource's
   principle; both failure directions now demonstrated.)* Contract A's
   `email`/`web`/`patent` are wider-than-emitted and have never existed. A
   proposal in this session to declare `language` as BCP 47 was **withdrawn for
   the same defect from the opposite direction** — it would have admitted `pt-BR`,
   the exact value the producer folds away because ovr.news dispatches
   translation on the bare code.
3. **The load-bearing fix is a caller, not a file.** A correct schema with no
   caller decays to a stale schema on the same timetable.
4. **Producer owns the envelope; each consumer owns its expectations.** Not
   unification — the two schemas overlap on **zero** metadata keys, so merging
   deletes a half.

---

## Explicitly OUT of scope

Named so nobody re-opens them mid-review:

- **schema.org / IPTC NewsML-G2 vocabulary migration.** ovr.news already emits
  schema.org JSON-LD and deliberately publishes `WebPage`, not `NewsArticle`
  (*"ovr.news is an aggregator, not the original publisher"*). The consumer facing
  the outside world has decided. Field-level standards yes; document-level
  vocabulary migration no — four internal consumers, no external reader of the
  raw stream.
- **Nesting the language diagnostics into `language_provenance`.** Withdrawn:
  two of the five are *inputs* read by the producer to make the decision, so
  nesting inverts the dataflow.
- **Deleting any field**, including `metadata.hashes`. See principle 1.
- **Changing the storage format.** JSONL fits: append-only, streamable, survives
  a truncated write, greppable. The format is not the defect. (Budget, for the
  record: 1,700 B/row, `metadata` 37.5%, repeated keys 30.3%, gzip 4.5×.)
- **Widening any schema to make a check green.** NM#303's rule: a green check
  bought by loosening is worth less than a red one.
- **IEEE anything.** Nothing applicable.

---

## Sequencing — the one non-obvious ordering decision

The CI job (principle 3) is the load-bearing item, but it **cannot go last** —
if it lands after the fixes it will never have proven it catches anything — and
it **cannot go first as a gate**, because it would be red on day one and get
switched off.

**So it goes first in REPORTING mode, and becomes a gate last.**

```
Phase 0a FIX THE INSTRUMENT first                            -> per-ROW counts; group count == distinct missing properties
Phase 0b build the check, reporting-only, exit 0 always      -> AND give every existing drop point a reader
Phase 1  fix the wrong declarations                          -> check goes green on those
Phase 2  declare the undeclared, with status                 -> check stays green
Phase 3  flip the check to fail the build                    -> now it guards
```

### ⭐⭐ READER BEFORE STRICTER — a phase-0 rule, adopted 2026-08-14

*(Raised by ovr.news from their ADR-041; generalised and ruled here after a second
instance was measured independently.)*

> **No hop may add a required field to a mechanism that DROPS rows until that
> mechanism's removals reach a reader.**

**Two measured instances, at two different hops:**

| hop | drops | records | class |
|---|---|---|---|
| `NexusMind/scripts/main.py:1008` | `continue` | `stats["schema_invalid"]` exists, first 5 logged — dies at the `last_run.json` boundary (verified: carries neither it nor `json_errors`) | **log-with-no-reader** |
| `ovr.news/summarize.ts:404` | returns only valid rows | ⭐ **destroyed at the callsite** | **uncomputed** |

⭐ **The two are not the same defect, and ovr's is worse.** `validateArticles`
returns `{ valid, summary }` — `summary` carries total / valid / invalid and the full
error list. The callsite is:

```ts
const { valid } = validateArticles(articles, `summarize:${filter}`);
```

**`summary` is computed, returned, and discarded in the same expression.** So *even
giving the log a reader would not recover the structured count* — you would get a
warn line's text and nothing enumerable. NexusMind's shape is better by one step: the
value **exists** somewhere before it is dropped.

> **Name them separately in the artefact.** `unreported.*` (the value exists, nothing
> reads it) and **`uncomputed_at_callsite.*` (no amount of downstream plumbing
> helps)**. The second is likely commoner, *because it leaves no trace at all to
> notice* — there is not even a warn line to grep for.

**Consequence for phase 0b: "the artefact IS the reader" is necessary and not
sufficient.** The artefact can only read what a producer hands it. **ovr's phase-0b
task is two steps — stop discarding `summary`, then land it** — and any hop of the
`uncomputed` class is the same.

**Instance 1 CONFIRMED by measurement (ovr.news, 2026-08-14):** nothing anywhere
consumes ovr's `Contract B validation` lines. Four hits estate-wide, all emitters,
docstrings or test headers; no log transport in `logger.ts`;
`scheduled_summarize.sh:88` runs with no redirect so stdout goes to the journal; no
journal grep in any script, unit or crontab on sadalsuud. ⚠️ **And their own verify
probe greps for the string's presence IN SOURCE, not for log output — it would pass
unchanged if every line were emitted into a black hole**, which is what happens.

⚠️ **COUNT CORRECTED: n = 2, not 3 — and the inflation was committed HERE, in the
section cataloguing it.** This paragraph previously called the measurement above a
*"third instance"* and concluded *"three instances is a pattern"*. **It is not a
third instance. It is instance 1 (ovr's `validate.ts`) measured properly** — a
confirmation counted as a new case.

**And the third hop has no such mechanism at all** *(ovr.news, checking
FluxusSource on request)*: **FluxusSource does not self-validate.** There is no
FS-side contract validator that checks its own output and drops rows; what exists is
field-level normalisation held where the value is stored (`__post_init__`,
deliberately, so ~30 aggregators cannot each get it wrong). **FluxusSource's contract
is checked DOWNSTREAM, by NexusMind's validator running against FS's bytes** — so the
question *"does anything consume FluxusSource's validator output"* has **no
subject**, and the three Contract A defects are NexusMind's validator's output, whose
unread status is already instance 2.

> **The honest statement: every validate-and-drop mechanism found so far has unread
> output — n = 2 — with a third hop that has no such mechanism to check.** Still a
> pattern, on a smaller denominator than it looked. *The denominator is the thing
> this thread keeps getting wrong, and this is the fourth time today.*

**The healthy case, for contrast, and it is instructive.** FluxusSource records a
drop **in the DATA rather than a log**: `content_item.py:643` stamps
`metadata['tags_dropped']` when tag normalisation discards a blank or non-string tag
(#138). That is **structurally better than both other hops** — the count travels with
the row and survives to any consumer. Measured on sadalsuud over 3 days: **0 of
311,879 rows carry it**, with a positive control proving the instrument sees
`metadata` at all (114,836 of 114,836 rows carry a non-empty dict;
`source_category` 114,836, `quality` 114,836, `word_count` 113,667). **The zero is
real: the producer bug it was built to expose was fixed at source.** Instrumentation
correctly placed, with nothing to report.

*Low-value sub-finding worth one line for the catalogue:* `tags_dropped` is **absent
when zero**, like every optional metadata key, so a reader **cannot distinguish "no
drops occurred" from "the mechanism was removed" from "this producer never had it"**
— the same defect the artefact spec's `asserted: false` exists to prevent, occurring
in a data field rather than a probe.

**Why it is a rule and not an observation.** Tightening a silently-dropping
validator **trades a silent wrong value for a silent disappearance.** The direction
is right and the loss becomes unobservable — so "make the check stricter" is not a
phase-1 item *anywhere* until "give the check a reader" is a phase-0 item.

This does **not** rest on ADR-041, which is ovr's and cannot bind other repos. The
same conclusion follows from **ADR-022 in this repo — *stamp always, decide once* —
applied to drops rather than to scores.**

⭐ **It resolves rather than adds work: the artefact IS the reader.**
`unreported.schema_invalid` is already a named defect class in
`docs/CONTRACTS_CHECK_ARTEFACT.md`. So phase 0b — build the check, give the drops
somewhere to land — is the unblocking step for strictness at *every* hop. **The
existing sequencing gets more right, with one rule added rather than a reordering.**

**Immediate consequence, already taken:** ovr will **not** make `validate.ts` require
`published_date`, even though it is measured free today (0 null, 0 empty in
1,335,210 upstream rows over 14 days). The prerequisite is not more measurement —
it is a reader.

Phase 0b is also the acceptance test for phases 1–2: each fix must move a number
the check already prints. **No fix lands without the check having reported it
first.** That is this project's own "prove the outcome changed" rule applied to
the contracts work.

⚠️ **Phase 0 is TWO steps and the order matters — correction from FluxusSource's
review, and it is the same defect twice.** If phase 0 captures its baseline using
`validate_production_contract.py` as it stands, the baseline is in **errors, not
rows**, inflated on any group keyed on a parent path (the 1,195-vs-928). W2's
`required` fix would then move a number that does not correspond to rows, and the
acceptance test would read as a bigger win than it is. **Phase 0a's exit criterion
is "the check reports per-row counts, verified against a hand count on one known
class"** — otherwise phase 0 proves the check *runs*, not that it *measures*.

**Phase 0b's producer half already exists and should not be rebuilt.**
FluxusSource's `validate_output.py` validates real JSONL against a real schema and
has the track record phase 0 wants: it found 559 relative-URL rows in its first
week and dated the four-class cluster to `collection_20260807`. **The gap is the
CONSUMER side running against real bytes with a caller** — that is W5.1 and
nothing else.

---

## Workstreams by repo

Ownership below is *proposed*. Each repo's session should confirm or reject its
own list; no session should accept work assigned by another.

### W1 — FluxusSource (producer)

| # | item | why here | size |
|---|---|---|---|
| **W1.1** | **RFC 3339 offsets on `published_date` / `collected_date`** | **99.4–99.7% of rows carry NO UTC offset.** No longer a standards item — see below, it is a live defect. Already ADR-008 item 2, open. | long pole, but smaller than first drawn |
| W1.2 | Tighten `language` to the reachable set | Both current descriptions are wrong in opposite directions: says "ISO 639-1" (too narrow — `zh-cn`/`zh-tw` are legal and intended) over a pattern that admits `pt-br` and `abc-defg` (too wide, unemittable) | small |
| W1.3 | Three statuses for the language family | `language` = **the answer**; `language_hint` + `feed_declared_language` = **input to the decision, never an answer**; the other three = **diagnostic of the decision**. States an input/output distinction no layer currently states | small |
| W1.4 | Publish the envelope as a versioned fragment | The shared piece consumers `$ref` — top-level set, types, `additionalProperties: false` | medium |
| W1.5 | `OUTPUT_CONTRACT.md` corrections | `source_group` presence, the "adding a field is safe" rewording, the two-gates note. **Already in their working tree** | done, unmerged |

**W1.1 is ranked first across the whole plan on the producer side** — on
**recoverability and on ovr's measured 2-hour shift**, not on any claim about
corrupted instants upstream.

⚠️ **RAISED AND REFUTED, recorded so it is not re-litigated.** NexusMind argued
(and withdrew within the hour) that naive timestamps carry a **per-source bias up
to ±14h**, making W1.1 a prerequisite for enabling the `story_dedup` temporal
term and voiding any `sigma_hours` tuning across it. **The producer settles it:**
`FluxusSource/src/utils/date_parser.py:173` `normalize_timezone` converts to UTC
**and then** strips the offset, and every RSS entry reaches it via
`extract_date_from_rss_entry` → `parse_date_string`, with RFC 822 `pubDate`
requiring a timezone. **So stored naive values already are UTC; naive→UTC is
correct, not an approximation.** No per-source bias, no corrupted Δt, no σ figures
affected, and **W1.1 does not gate the temporal work.**

⚠️⚠️ **DO NOT READ "W1.1 does not gate the temporal work" AS "W1.1 CAN SHIP."**
*(Flagged by FluxusSource, relayed and confirmed by ovr.news, 2026-08-14 — the two
sentences look interchangeable and are opposite in consequence.)*

- **The refuted claim** was that naive timestamps carry a per-source bias, making
  W1.1 a *prerequisite* for NexusMind's temporal work. That is dead: **the
  producer's hop needs no wait.**
- **The live claim is the other direction.** **ovr.news BREAKS when offsets are
  ADDED** — W3.4's lexicographic hazard (`'…T20:00:00+02:00' > '…T19:00:00'` as a
  string while being earlier in time) across `idx_articles_published` and ~20
  `ORDER BY published_date` sites. That is real regardless of the refutation.

**FS#171 is open, unstarted, and recorded in FluxusSource's repo as blocked on
ovr#321 as a HARD GATE.** Nothing about the temporal refutation releases it.
**Shipping W1.1 before ovr#321 lands publishes duplicate story pairs** — both
members fall outside the dedup window and both go live, a visible editorial failure.

What survives is much smaller: `normalize_timezone`'s `else` branch keeps a
*naive input* as-is, so a feed publishing an offset-less date yields something
that may be publisher-local and is read as UTC. **That population cannot be sized
downstream** — every row is naive by the time NexusMind sees it, so the two cases
are indistinguishable by construction. It needs a producer-side count of entries
whose source date parsed without a timezone. **NM#354.**

#### W1.1 detail — it is a LIVE DEFECT, not a standards nicety

*Established in review round 1 by FluxusSource, mechanism verified here.*

**NexusMind is a no-op.** It already implements naive-means-UTC in both paths —
`utils/datetime_utils.py:33-35` and `scoring/display_ranking.py:178-180` both
coerce `tzinfo is None` → UTC. Stamping the offset cannot change a number there.

**ovr.news is where it lands.** ECMAScript parses an ISO date-time *without* an
offset as **local time**. Demonstrated on a Europe/Amsterdam host:

```
naive  '2026-08-13T16:10:06'        -> 2026-08-13T14:10:06.000Z
offset '2026-08-13T16:10:06+00:00'  -> 2026-08-13T16:10:06.000Z    delta 2h
```

Articles read **older than they are**, and **the 0.6% carrying an offset are read
correctly** — so ovr's corpus is internally inconsistent by 1–2 hours between two
populations of its own rows. That is "the instant is not recoverable" made
concrete, and it is a better motivation than the standards argument.

⚠️ **BLAST RADIUS IS UNRESOLVED AND SPLITS BY HOST — ovr.news must answer.**
12 call sites found. **`scripts/summarize.ts:375`** (the cutoff comparison) runs
on **sadalsuud, confirmed `Europe/Amsterdam`/CEST — live and affected.** The other
11 run at Astro build time on **Cloudflare Pages**, whose TZ **nobody has
checked**: `lib/ranking.ts:40`, `feed.xml.ts:30,:42`, `feed/[lens].xml.ts:39,:50`,
`data/pipeline.ts:172`, `editor/rules/story-dedup.ts:58,:64`,
`[lang]/[tab].astro:177,:208`, `[lang]/artikel/[id].astro:177,:883`,
`[lang]/index.astro:159`. If that host is UTC they are all currently correct.
**Do not guess it.**

**And the answer does not decide whether to do W1.1.** If the build host is UTC,
ovr.news's correctness depends on an **unstated environmental invariant** — a
Cloudflare default nobody chose, wrote down, or would be told about if it changed.
Making the instant explicit in the data removes that dependence whether or not it
is presently biting.

**Not a corpus migration** — this shrinks the item. Naive-means-UTC is an
invariant by construction (`DateParser` converts to UTC *then* strips tzinfo), so
the ~8 months of archives are **under-specified, not wrong**, and any reader can
apply the rule retroactively. Nothing is stranded.

**The real cost is a CODE AUDIT of ~30 aggregators, not the serialization.**
A local-naive and a UTC-naive timestamp are **byte-identical**, so this cannot be
detected from the data. If any aggregator emits a local-time naive datetime,
stamping `+00:00` converts an unknown instant into a confidently wrong one — worse
than leaving it naive. *"Add an offset" reads like a one-liner and is not.*

### W2 — NexusMind (consumer #1, owns Contract A and B)

| # | item | why here |
|---|---|---|
| W2.1 | Fix Contract A's three wrong declarations | enum → producer's vocabulary; `maximum: 8` → **10**; drop `word_count` + `priority` from `required` (267 and 928 rows legitimately omit them) |
| W2.2 | Declare `source_group` (+ decide `eval_query`) | Arrives tonight; NM#304 argues `eval_query` should stay failing since ADR-007 retires the eval arms — **that is a decision to record, not an omission** |
| W2.3 | Declare the 34 undeclared metadata keys, with status | Principle 1. Include "declared, no known consumer" as an explicit status |
| 🔨 **W2.4 BUILT, NOT MERGED** (`b8a191c`, NM#357, branch `fix/357-…`) — see round 2 | Fix `validate_production_contract.py`'s grouping + labelling | It counts **errors, not rows**, and merges distinct `required` failures into one line — which hid the `priority` defect for five days. No baseline file exists, so zero migration cost. **Must land with a test**: one row missing two required properties → two distinct groups |
| W2.5 | Record Contract B's top-level-openness tradeoff | Deliberate-by-policy, defended nowhere in `NexusMind/contracts/CHANGELOG.md`, and it means **B structurally cannot detect a `source_group`-class event**. May well be the right call for B — but it should be a written decision |
| W2.6 | Land the four NM#304 additions | priority ceiling is 10 not 9; `priority`-absent at 928; `source_group`; the `_get_priority` collision |

✅ **RETRACTED in review round 1 — draft 1 claimed `_get_priority` made this the
plan's only live behavioural risk, and gated W2.1 on an owner decision. Both were
wrong.** NexusMind measured what they had previously inferred: `credibility_score`
is a **[0,10] float** and the multiplier is exactly 10, so tiers touch at *every*
adjacent boundary — composite `70.0 ← {6,7}`, `80.0 ← {7,8}`, `90.0 ← {8,9}`,
present in production today. **Raising `maximum` to 10 does not introduce, worsen,
or interact with it.** W2.1 absorbs the ceiling change quietly and open decision
#5 is deleted.

What survives is smaller and *not part of this plan*: `priority*10 + credibility`
is non-strict by construction, making the tiering advisory rather than ordered.
Bounded — `_has_real_image` is the primary key and ties break on content length.
**Its own NexusMind issue, unlinked from contracts, gating nothing.**

### W3 — ovr.news (consumer #2)

**Why ovr is a necessary participant and not a courtesy copy:** NexusMind passes
the FluxusSource `metadata` blob straight through into `data/filtered/*.jsonl`
(16 keys today), and Contract B declares `metadata` with zero properties. **The
blob crosses two contracts and is described by neither at the point ovr reads
it.**

| # | item | why here |
|---|---|---|
| W3.1 | State what ovr actually requires | ovr has **no contract of its own**. `word_count` has ~1 reader in NexusMind and **24 occurrences across 5 files** in ovr — so NexusMind's contract is not the place to decide what the producer emits |
| W3.2 | Document/declare the ingest projection | `metadata: rawArticle.metadata ? { quality: … } : undefined` (`summarize.ts:887`, `:1342`) is a **second undeclared gate**. A field must clear both, and neither announces itself |
| W3.3 | Confirm or reject the schema.org scope call | This plan assumes ovr's `WebPage`-not-`NewsArticle` decision stands and closes the vocabulary question. **ovr should confirm that reading** |

### W4 — pipeline-atlas (the record)

| # | item | why here |
|---|---|---|
| W4.1 | `reference/contracts.html`: the two-contract split | Currently the only page describing this layer to a reader, and it cannot presently say that the blob crosses both contracts undescribed |
| W4.2 | Numbers become verify commands, not prose | Their own standing rule. Every figure in the brief has a command |
| W4.3 | Add the contracts check to the ops snapshot | Once W5.1 exists, "is Contract A green" is exactly the kind of armed/not-armed state the snapshot already reports for drop points |

### W5 — llm-distillery (this repo; oversight)

| # | item | why here |
|---|---|---|
| W5.1 | **Specify the CI job** (phase 0 above) | The load-bearing item. Specify here, implement where it runs. **Artefact spec: `docs/CONTRACTS_CHECK_ARTEFACT.md`**, rev 3, 🔒 frozen at `schema: 1` |

#### 🔒 The frozen spec is pinned by hash, because the file is UNTRACKED

⚠️ **Caught by pipeline-atlas, and it is this plan's own thesis one level up.** The
freeze banner was declared on a file `git status` reports as `??` — no history, no
diff, no blame. **"Frozen" and "unversioned" are two halves of a claim that cannot be
checked**, and the protocol depended entirely on the author remembering to follow it.
Same failure as W5.3's round-1 brief, which lived in a session scratchpad and is gone.

Until the file is committed, **this tracked line vouches for the untracked one**:

```
docs/CONTRACTS_CHECK_ARTEFACT.md   rev 5, frozen 2026-08-14
sha256  3504204f07ec3ed83600aab0c6f39b3ba21465b6031b21fef8c8484bd68de737
bytes   25896        lines  457
```

*(rev 3 `46fea1a2…` / rev 4 `fc66c9a5…`, both **hash-verified** by pipeline-atlas.
rev 4 clarified the phase-3 proof; rev 5 corrected the unit names in the JSON
skeleton. Both keep `schema: 1` and require no reader change.)*

⚠️ **"Hash-verified" is NOT "reviewed", and the distinction cost something.** This
line previously said pipeline-atlas had *"verified rev 3 independently"*. **They
computed a sha256 and confirmed it matched the one announced — they never read rev
3.** A hash verifies **identity**, that the reader holds the bytes the author
announced, and says **nothing about what is in them**. They discovered this by
spot-checking rev 4's "no field added" claim against `artefact_version`,
`expected_cadence_seconds`, `checker_version`, `schema_sha256`, `hops_not_covered`,
`rows_invalid` — **all six returned zero, which momentarily looked like the
announcement was false.** It was not: those are **rev 2** names, and rev 3 had
restructured onto the `to_json()` shape they themselves proposed. **They had carried
a two-revision-stale model of the shape while believing it was checked.**

✅ **How to read three revisions in one evening — and it is NOT as an error rate.**
*(pipeline-atlas, correcting this document's author.)* **Revisions found by review
BEFORE anyone builds against the spec are the cheap ones — that is the process
working.** The expensive version is rev 3 shipping unchallenged, a reader built
against the unprefixed skeleton, and the panel reporting NOT ARMED forever against a
check that is running fine — discovered weeks later, if at all, by someone wondering
why the contracts row never changes.

> **A freeze that produces three ANNOUNCED revisions is doing its job. A freeze that
> produces none because nobody looked is the failure mode.**

**The genuine signal is narrower: the revisions were cheap to FIND and expensive to
VERIFY.** Each one cost the reviewer greps and a false alarm where a diff would have
cost two lines. **That is an argument about version control, not about anyone's rate
of error.**

⚠️⚠️ **And the freeze protocol's own boundary, demonstrated by use:** rev 3 no longer
exists anywhere — the file is untracked and was overwritten in place — so **nobody
can diff rev 3 → rev 4**, and *"no field added, removed or retyped"* is taken **on
trust**. **Announcement + hash proves identity; only version control proves what
changed.** Those are different guarantees. Had the file been committed, that check
would have been a two-line diff instead of four greps and a false alarm.

```bash
echo "spec sha256: $(sha256sum docs/CONTRACTS_CHECK_ARTEFACT.md | awk '{print $1}')"
```

An implementer records that hash beside their reader; **a changed spec then fails
loudly on their side instead of silently.** *(Verified independently by
pipeline-atlas: computed hash, byte count and line count all match.)*

⚠️⚠️ **NOT YET IN FORCE — and this is the last layer of the same defect.** The
sentence above says a tracked file vouches for an untracked one. **The vouching line
is itself uncommitted.** `docs/CONTRACTS_PLAN.md` is tracked but ` M`, and
`git show HEAD:docs/CONTRACTS_PLAN.md | grep <hash>` finds nothing — HEAD is
`fd80018`. **So there are currently TWO unversioned facts, not one versioned and one
not**, and a silent edit to the spec could be matched by a silent edit to this hash
line with no diff anyone could find.

The construction is sound and **takes effect only when the commit lands.** A hash is
the weaker of the two fixes regardless — it pins the current text and gives no
history, and *a revision without a commit is just a paragraph*. **Committing both
files is the real close, and is pending an owner decision.**

**W5.1 definition of done — three items that are each one line and each get
dropped for being too small to look like work:**

1. **Install the systemd unit.** Units on sadalsuud are root-owned copies; `git pull`
   does not update a changed unit, and a committed-but-uninstalled timer is
   indistinguishable from a passing check.
2. **Mode 0644, traversable parent.** The reader runs `User=jeroen`; a root-owned
   0600 artefact is EACCES forever, and that failure **has no visible cause from
   either side**.
3. ✅ **DONE — tell pipeline-atlas the two unit names.** `nexusmind-contract-check.timer`
   and `nexusmind-contract-check.service`, delivered; they shipped the arming half as
   `ff9dcc6` and both render **NOT ARMED · unit not installed**.
4. ⭐ **STILL OWED: tell pipeline-atlas the moment `deploy/install.sh` has run**, so
   they flip `must_exist` to `True`. **This is not optional bookkeeping.**
   `LoadState=not-found` means **two opposite things**, and the flag is the only thing
   that separates them:

   | `must_exist` | meaning of `not-found` | renders |
   |---|---|---|
   | `False` (today) | named but **not installed yet** | **NOT ARMED**, bold upright |
   | `True` (after install) | should be installed and is **GONE** | **alarm / unknown**, amber italic |

   **Correct today, wrong the day after install** — an installed-then-deleted unit
   would read as merely not-armed. Same handoff shape as the names themselves, and
   equally easy to drop for being too small to look like work.

⚠️ **The trap confirmed live by pipeline-atlas while building it:** `systemctl show`
on **both** of these unit names exits **0** and reports
`ActiveState=inactive, Result=success` — byte-identical to a healthy stopped unit. A
snapshot querying the obvious properties would have drawn **two clean idle rows for
units that do not exist.** `LoadState` is the only discriminator.
| W5.2 | **Correct FluxusSource#164's stated justification** | See below — this is ours to answer and the reason on record is wrong |
| W5.3 | Keep `memory/stamp-contract-integrity.md` § *The contracts layer* current | It is the only surviving copy of the measurements and traps. ⚠️ The round-1 working brief lived in a **session scratchpad and is gone**; its content was folded into that section before the session closed. If a peer cites a `scratchpad/CONTRACTS-BRIEF.md` path, it no longer exists — send them here |

#### W5.2 — the FS#164 answer, resolved

FluxusSource#164 removed a 730-day purge and keeps ~8 months of archives
(1,476 dirs) **indefinitely**, justified in their CLAUDE.md as *"llm-distillery
trains on this depth."*

**Measured here: that reason is wrong as stated.** llm-distillery has **zero
references to `data/archived/`** for training. It does train on FluxusSource raw
ingest — the obituary detector on 585K `content_items_*.jsonl`, solutions v4/v5
on `data/raw/content_items_*.jsonl` — but via **point-in-time copies taken at the
time**, not on-demand archive reads.

**The retention decision is right for a better reason, and it is recorded in this
repo:** `docs/TODO.md:1367` — *"the only surviving copy of a displaced body is in
`FluxusSource/data/archived/`, keyed by the same `id`"*. That is the repair path
for NM#306's already-stored corrupted bodies. Deleting the archive deletes the
only route to repair.

**Recommendation: correct the reason, keep the retention.** Do not propose a
retention change — deletion is irreversible and 1.2 GB is cheap.

---

## Cross-repo ordering

```
W5.1 (check, reporting-only)  ─┬─> W2.1 W2.2 W2.4  ─┬─> W2.3 W1.2 W1.3  ──> Phase 3: flip to gate
                               │                     │
W1.5 (already written)  ───────┘                     └─> W4.1 W4.2
W1.1 (timestamps) ─── independent, longest, start early
W3.1 W3.2 ─── independent, feed W1.4's envelope
W1.4 (envelope) ─── needs W3.1 (cannot define a shared envelope without both consumers)
```

**W1.1 and W1.4 are the two long poles.** Everything else is small.

---

## Decisions the owner needs to take

1. **Does W1.4 (a shared versioned envelope) happen at all**, or do we stop at
   "each schema is correct and checked"? The envelope is the larger structural
   change and the plan works without it.
2. **Closed envelope needs an additive path or it will not survive.** NexusMind's
   proposal: envelope closed, **version bump mandatory on any field addition,
   consumers pin a minor range** so additive bumps auto-pass while the drift check
   still fires and records it. Without something like it, closed-envelope reverts
   to open within two months and nobody writes down why.
3. ~~**Where does the CI job run?**~~ **RESOLVED in round 1 — both consumers
   independently rejected the cycle tail.** A **separate systemd timer on
   sadalsuud**, own unit, decoupled from `nexusmind.service`, writing a result
   artefact the atlas snapshot reads. NexusMind: the run has a 4h
   `TimeoutStartSec` and one job, and contract validation is not worth a
   production cycle. pipeline-atlas: **do not wire it with `OnSuccess=` — it goes
   silent exactly on the cycles that failed, and silence is indistinguishable
   from green** (2026-08-13's 16:04 failure is the demonstration). Committed-sample
   rejected as fixtures again. *Owner confirmation still wanted; the engineering
   question is closed.*
4. **`eval_query`: declare-as-expiring, or leave failing?** NM#304 argues leave
   failing. Either is defensible; it must be a decision. Note FluxusSource **does**
   declare it — say "the producer declares it and we don't", not "undeclared".
5. ~~**The `_get_priority` collision**~~ — **DELETED, see W2. The premise was
   false.**

---

## Baseline — every figure, its command, and when it was measured

**The rule, from pipeline-atlas and adopted here: a figure is safe in prose only if
the mechanism that produced it would have to change for the figure to change.**
Zero-overlap passes. "Parses as local time" passes. **Every count of rows, files,
occurrences or percentage-of-a-live-corpus fails** and belongs here instead, with
the body saying *"the check reports N (see baseline)"*.

Three conventions, each with a receipt:

1. ⚠️ **The obvious inversion of a "returns zero" command still fails.**
   `grep -rIl X . | wc -l` prints `0` **and still exits 1** under `-uo pipefail`.
   Use `echo "n=$(grep -rIl X . | wc -l)"` — command substitution isolates the exit
   status and the label states the claim.
2. ⚠️ **No ` — expect …` suffix in this file.** That convention belongs to
   pipeline-atlas's `run_verifies.sh`, which splits on it. The framework's curate
   runner does **not** split, and hands the em-dash to the shell as a filename. Put
   expectations in prose.
0. ⚠️⚠️ **Every git command MUST name its ref, and every sweep MUST record which
   tree it read.** These checkouts are shared with parallel peer sessions, so
   "the working tree" is not a state this document can refer to. **B1 was measured
   as 1, and reads 2 in a checkout sitting on `fix/357-…` — and it CHANGED value
   mid-session, because a peer committed `99c74a4` to that branch while the table
   was being written.** A bare `git log --` answers about whichever branch someone
   else last checked out. *(pipeline-atlas found the same defect in their
   `run_verifies.sh`, which resolves siblings from the parent directory and greps
   whatever is checked out — an unknown number of their 100 checks are currently
   answering about unmerged work, and nothing in the output says which tree it
   read.)* **Same class as the `origin/main` gotcha: a source that cannot say "I
   don't know which state you meant" answers confidently about whichever one it
   has.**
3. ⚠️⚠️ **Every "zero references" command MUST exclude prose, or it measures the
   documentation of its own claim.** Found twice on 2026-08-14, hours apart: `grep
   -rIl "validate_production_contract"` went **0 → 14** (13 of them prose the five
   sessions wrote), and `grep -rIl "data/archived" llm-distillery/` reads **5**, all
   prose, **0** in executable code. Both claims survive; both original commands are
   now unusable.

**What this checkout excludes:** no FluxusSource or NexusMind *data* is present on
the workstation — it lives on sadalsuud. Every row-level figure below is therefore
remote or peer-supplied, and is marked as such rather than silently inherited.

### Measured here, 2026-08-14, all commands executed

⚠️ **The commands are in the code block below, NOT in the table.** A shell pipe
inside a markdown table cell must be written `\|`, and a reader who copies that gets
a literal backslash-pipe that breaks the command. *A table of verify commands whose
commands do not run is this document's own thesis, and draft 3 shipped it for about
four minutes.*

| id | figure | value |
|---|---|---|
| B1 | Contract A commits, ever **on `main`** | **1** (⚠️ **2** in a working tree sitting on `fix/357-…` — see the ref convention below) |
| B2 | Contract A declared metadata keys | **12** |
| B3 | Producer declared metadata keys | **7** |
| B4 | **Overlap between B2 and B3** | **0** — Category 3, mechanism-bound |
| B5 | Contract B declared metadata properties | **0** |
| B6 | `validate_contract_a` mentions / callers | **3 / 0** (definition + this plan + its memory file) |
| B7 | `validate_production_contract` mentions / executable callers | **15 / 1** — ⚠️ **the 15 is unstable by construction, see below.** The **1** is the claim: a unit test, i.e. a caller and **not** a scheduler |
| B8 | llm-distillery `data/archived/` refs **in code** | **0** (unrestricted: 5, all prose — **W5.2 stands**) |
| B9 | TS/JS schema libraries, all 20 repos | **0** — the sweep's headline, while ovr's hand-written validator runs every cycle |

⚠️ **B7 demonstrated the whole rule while being written.** It read **14** when the
sweep ran and **15** an hour later, executed verbatim — because *writing the figure
into this table added a mention of the script's name.* The figure incremented itself
by being recorded. **A name-grep count over a repo that documents the name is not a
measurement of anything**; only `B7 executable` is a claim. Left in rather than
patched, because it is the cheapest available proof of the rule at the top of this
section.

```bash
# Run from ~/repos/veen-systems. All executed 2026-08-14, exit 0 under `set -uo pipefail`.
cd ~/repos/veen-systems

# B1 -- NAME THE REF. Without `main` this reads whatever branch the checkout is on.
echo "B1 n=$(git -C NexusMind log --oneline main -- contracts/fluxussource-output.schema.json | wc -l)"

# B2 B3 B4 B5
python3 - <<'PY'
import json
def keys(p):
    s = json.load(open(p))
    return set(s.get('properties', {}).get('metadata', {}).get('properties', {}))
a = keys('NexusMind/contracts/fluxussource-output.schema.json')
b = keys('FluxusSource/config/schemas/output_schema.json')
c = keys('NexusMind/contracts/nexusmind-output.schema.json')
print(f"B2 n={len(a)}  B3 n={len(b)}  B4 overlap={len(a & b)}  B5 n={len(c)}")
PY

# B6 B7 -- mentions, then executable-only. The second number is the claim.
echo "B6 mentions=$(grep -rIl --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=venv 'validate_contract_a' . | wc -l)"
echo "B7 mentions=$(grep -rIl --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=venv 'validate_production_contract' . | wc -l)"
echo "B7 executable=$(grep -rIl --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=venv --include=*.py --include=*.sh --include=*.yml --include=*.service --include=*.timer 'validate_production_contract' . | wc -l)"

# B8 -- prose excluded, or it measures its own documentation
echo "B8 code=$(grep -rIl --exclude-dir=.git --include=*.py --include=*.sh --include=*.yaml 'data/archived' llm-distillery/ | wc -l)"

# B9
echo "B9 n=$(grep -rIl --exclude-dir=node_modules --exclude-dir=.git -E 'from .(zod|ajv|yup|joi|superstruct|valibot|io-ts).' --include=*.ts --include=*.js . | wc -l)"
```

### Peer-supplied or remote — command given, NOT run from this checkout

| figure | value | source and command |
|---|---|---|
| Contract A `required` defects, per class | **priority 636 rows / word_count 115 rows** on 10,677 rows | NexusMind `b8a191c`. `python3 scripts/validate_production_contract.py` on sadalsuud. ⚠️ **Do not reconcile against the 928/267/1,195 figures** — different corpora |
| Metadata keys per run | **min 27, median 63.5, max 107** across 50 runs | FluxusSource, hot window 2026-08-06→08-14. ⚠️ **A single-run count measures which aggregators were due in that tick.** This is why "2 of 52 / 96%" is retired |
| Metadata keys, hot-window union | **168, of which 154 confined to one `source_type`** | FluxusSource inventory over `data/current/`, 50 runs, 171,336 rows. **Not "the full namespace"** — `data/archived/` sits outside it |
| Keys read by name in consumer pipeline code | **3** (`quality`, `og_image_url`, `priority`) | FluxusSource. ⚠️ **Carry the caveat**: read *by name*, not *the only keys that can break a consumer* — NexusMind passes the whole blob through untouched |
| ovr metadata keys consumed | **2** (`og_image_url` at `summarize.ts:336-337`, `quality` at `transform.ts:292` and `:324`) | ovr.news, re-derived 2026-08-14 |
| ⭐ **ovr blobs surviving the projection** | **3,000 of 3,000 most recent blobs carry exactly ONE top-level key** | ovr.news `current-state`. **The denominator-independent half of the claim**: it counts what ovr *stores*, so it is unaffected by how many keys arrived in any given tick. This is the figure to quote for the phase-3 boundary |
| `published_date` null or empty, upstream | **0 and 0** in **1,335,210** rows over 14 days | ovr.news. Neither the fallback nor the `NOT NULL` fires today — **the ordering below still matters for when one does** |
| `validate.ts` blindness | `published_date` **0**, `metadata` **0**, control `title` **1** | ovr.news. **The control is required** — an empty grep and a broken grep are indistinguishable without it |
| `published_date` / `collected_date` with no UTC offset | **99.4–99.7%** | round 1, sadalsuud. Drifts continuously as rows land |
| Cloudflare Pages build-host TZ | **8/8 zero shift** | ⚠️ **Category 2, the worst kind: nothing pins that TZ and staleness leaves no trace** — no commit, no release, no diff. The two-URL RSS-vs-JSON-LD diff must be the *only* form this figure appears in |
| sadalsuud offset | **CEST +0200** | ⚠️ **False every March and October. Print the offset, never literal it**: `ssh sadalsuud date +%z` |

### ⭐ The remedy for Category 1: a probe that GOES RED WHEN THE FIX LANDS

*(Built by ovr.news, 2026-08-14, while fixing a fake validator in their own docs —
and it is the mechanism this section was missing.)*

Category 1 figures are the ones **this plan's own success falsifies**. Prose cannot
protect them: the sentence survives, the claim evaporates, and nobody re-derives a
paragraph. A verify command that merely confirms the defect still exists has the same
problem inverted — it goes quiet exactly when the work succeeds.

**The shape that works: assert the finding's PREMISES by count, so fixing the defect
FAILS the probe and forces the document to be rewritten.** ovr's now asserts three
things and fails on each, positive-controlled all three ways:

| assertion | count | a positive would be |
|---|---|---|
| the callsite still discards `summary` | `w=1` | someone fixes the callsite |
| `validateArticles` still returns `summary` | `d=1` | someone removes it |
| `validate.ts` still omits `published_date` | `p=0` | someone requires the field |

> **The probe guards the FINDING'S CURRENCY, not the defect's existence.** If someone
> repairs the callsite, the probe goes red — which is correct, because the write-up
> is then wrong. That is the opposite of a check that quietly passes forever.

**Apply this to every Category 1 figure below** rather than restating them in prose.

### Category 1 — figures this plan's own success will falsify

Listed so nobody quotes them after the fix lands. Each **reads as an indictment and
becomes a lie on the first commit**: `priority` over `maximum: 8` (**2,774**, zeroed
by W2.1 by construction); `word_count`/`priority` absent (**267**/**928**, which stop
being defect counts and become bare populations); **"Contract A has had exactly one
commit ever"**; **34 undeclared metadata keys** (W2.3 drives it to 0); *"metadata
declared with zero properties"*; **"no scheduled caller" / "no caller at all"** —
**W5.1 is a caller**, so after phase 0b the validator table's right-hand column is
wrong, and that table is the plan's headline.

### Category 3 — safe in prose, mechanism-bound

The two schemas overlap on **zero** metadata keys · naive-means-UTC is an invariant
by construction (`DateParser` converts *then* strips) · `priority*10 + credibility`
is non-strict by construction · **ECMAScript parses an offset-less ISO string as
local time** — a language specification, not a measurement, and safe forever.

---

### Standing after round 4

| | |
|---|---|
| Canary | ✅ merged, installed, armed, **has reported the control** — first automatic fire 02:22 |
| W2.2 `source_group` | ⛔ **held to that fire**; replacement control named, `edges_not_covered` must move in the same commit |
| `eval_query` / NM#367 | ✅ ruled — stays undeclared, closes as a decision |
| `content_meta.truncated` | ✅ ruled — out of Contract A, re-filed to enrichment |
| Track B `content_meta.kind` | ⏳ split landed, **owner: merge + deploy** |
| `echoes_title` wording | ⏳ NexusMind description fix, 1.24.0 |
| `published.precision` | ⏳ FluxusSource, confirmed unwritten, deliberately last |
