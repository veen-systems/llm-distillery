# Contracts: a five-repo plan

**Draft 1 + review round 1, 2026-08-13 evening. Written by the llm-distillery
session; reviewed by the FluxusSource, NexusMind, ovr.news and pipeline-atlas
sessions.** Every number is measured; provenance, the verify commands and the
instrument defects that constrain how these numbers may be quoted are in
`memory/stamp-contract-integrity.md` § *The contracts layer*.

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
See § *Round 3* for the four peer answers and what they changed.

**Two standing holds:**

- 🔒 **Do NOT declare `source_group` (W2.2)** until the check has reported it. It is
  the only test that proves the check *detects* rather than merely *runs*, and
  declaring it spends that permanently.
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

**Round 2 HAS been run** — see § *Round 2 — the sweep*.

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
API's pydantic models (two optional strings) — both detailed in § *Round 2*.

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
| W2.5 | Record Contract B's top-level-openness tradeoff | Deliberate-by-policy, defended nowhere in `contracts/CHANGELOG.md`, and it means **B structurally cannot detect a `source_group`-class event**. May well be the right call for B — but it should be a written decision |
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

## Review round 1 — outcome, 2026-08-13 evening

All four peers reviewed. **The plan's premise moved.** Beyond the corrections
already folded in above:

**New items, both prerequisites that draft 1's ordering missed:**

- **W2.7 (NexusMind) — normalize `parse_published_date` to UTC.** It returns `dt`
  as-is (8 call sites) while `story_dedup._parse_timestamp` normalizes. Diverges
  the moment offsets land: `filtered_archiver.py:146` buckets by
  `strftime("%Y-%m")`, so an article at `2026-08-01T00:30+13:00` is `2026-07-31`
  UTC and archives under `2026-08`. **Must land BEFORE W1.1.**
- **W3.4 (ovr.news) — normalize timestamp parsing.** **W1.1 CREATES a
  lexicographic hazard**: `'…T20:00:00+02:00' > '…T19:00:00'` as a string while
  being earlier in real time, across `idx_articles_published` and ~20
  `ORDER BY published_date` sites. In `story-dedup.ts:58-66` it pushes genuine
  duplicate pairs outside the window so **both publish** — a visible editorial
  failure. Pattern already exists in-repo at `source-funnel.ts:107`. **W1.1 depends
  on it.**

**Measured answers that closed open questions:**

- **The Cloudflare Pages build host is UTC.** ovr measured it without build-log
  access: RSS `pubDate` is build-host-computed, JSON-LD `datePublished` is the raw
  string, so their difference *is* the offset — **8/8 zero shift**. The 11
  build-time sites are correct today. **Nothing pins that TZ**, so ovr's
  correctness rests on a Cloudflare default. Make the two-URL diff the verify
  command.
- **sadalsuud is `CEST +0200` and more sites run there than draft 1 listed** —
  `calculateDisplayRank` too (`summarize.ts:414,:419,:1034,:1035`).
  `recencyBoost: 1.3` fires on `ageHours < 24`, a hard 30% step, so **~25
  articles/day rank ~30% below where they belong on sadalsuud while Cloudflare
  ranks the same articles correctly.**
- **Drop `collected_date` from W1.1's ovr-facing case** — ovr never passes the
  producer's value (`db-articles.ts:136` stamps its own; 100% of stored rows `Z`).
- **ovr reads exactly 2 metadata keys** — `og_image_url` (`summarize.ts:334`) and
  `quality` (`transform.ts:324`). Far better than draft 1's `word_count` example,
  which was a **name collision**: 49 occurrences at ovr, **zero** reading the
  upstream field. ⚠️ **The "2 of 52 / 96% undeclared" form is RETIRED — see round 2.**
  A single-run key count measures which aggregators were due in that tick: **27 to
  107 across 50 runs, median 63.5.** The 2 stands; the percentage never had a
  denominator.
- **`og_image_url` is read at `:334`, UPSTREAM of the `:887` projection, then
  discarded by it.** So a field can be load-bearing at ovr and leave **no trace in
  the stored row** — reading the projection literally understates ovr's dependency.

**Sequencing corrections beyond phase 0a:**

- **"Prove it sees the known defects" is circular** — those defects *are* the
  validator's own output, so reporting them shows it still runs, not that it
  detects. **The genuine control is `source_group`**: an independent commit,
  arriving against a closed top level, that the check was never shown. **It is
  time-limited — once W2.2 declares `source_group` the test is spent, so hold W2.2
  behind it.**
- **"exit 0 always" needs a shipped proof it can go red**, or the phase-3 flip is
  the first test of the wiring. pipeline-atlas has a register entry for exactly
  this: a CI guard that could never fail because `--self-test` always returned 0.
- **Phase 0/3 cannot see ovr's hop** — the `:887` gate is code, not a schema. A
  fully green check is compatible with ovr dropping all but 2 metadata keys, which is what
  it does. **Write that boundary in now**, because at phase 3 "the pipeline is
  contract-checked" is the natural misreading.

**W4 (pipeline-atlas) reshaped by its owner:**

- **Half of `reference/contracts.qmd` is GENERATED** from `model/chain.yml` via
  `ops/gen_views.py`. Editing the page or the `.html` is a named ops trap — the
  next run reverts it and `--check` fails CI. Edit the model, regenerate, commit
  both.
- **W4.3 accepted as reporting, REFUSED as running** — and rightly: *"a map that
  is the only instrument is not a map."* **W5.1's check writes a result artefact;
  the snapshot reads it.** With no file the panel reports **UNKNOWN, no result
  ever** — the visible form of "nothing runs the validator". **Blocking on
  llm-distillery: spec the artefact** (path, timestamp, per-defect-class counts,
  version stamp) so the reader can be written before the check exists.
- **Do NOT carry "Contract A is red on every cycle" onto the atlas** — it is a
  measurement *designed to become false*, and when W2.1 lands the sentence goes
  silently wrong. Counts become verify commands or nothing.

**Implementation trap for W5.1**, from pipeline-atlas: systemd units on sadalsuud
are **root-owned copies** installed by `deploy/install.sh`; `git pull` does not
update a changed unit. **A committed-but-uninstalled timer never runs — and a
check that never runs is indistinguishable from a check that passes**, which is
this plan's own thesis. The install step belongs in W5.1's definition of done, and
the snapshot should report the check **armed/not-armed**, not green/red.

**Two decisions with the right outcome and the wrong reason on record** — worth
naming as a pair, because it is the same shape twice in one plan:

1. **FluxusSource#164** keeps ~8 months of archives, justified as *"llm-distillery
   trains on this depth."* We do not read `data/archived/` at all. The retention is
   right for a different reason, recorded in *this* repo (`docs/TODO.md`): it is
   the only surviving copy of a displaced body, and therefore NM#306's only repair
   path. **Correct the reason, keep the retention.**
2. **ovr's `WebPage`-not-`NewsArticle`** was cited here as evidence that the
   schema.org question is closed. It is a choice of *type within* schema.org, made
   while **adopting** schema.org — as evidence about vocabulary adoption it points
   the other way. The scope call stands on its own grounds (four internal
   consumers, no external reader of the raw stream); its justification does not.

**Unmeasured hole spotted in passing, flagged not claimed:** `published_date` is
not in `validate.ts`'s required set, and `summarize.ts:866` falls back to
`rawArticle.published_date ?? new Date().toISOString()` — an article arriving
without a publication date is **silently dated "now" and ranks as maximally
recent**. Nobody has measured how often that fires.

---

## Filed by NexusMind, 2026-08-13 evening (their board, measured, no code committed)

- **NM#354** naive-on-arrival dates — needs producer-side sizing
- **NM#355** `_get_priority` non-strict tiering — the corrected version, explicitly
  **not** blocking the ceiling change
- **NM#356** `parse_published_date` returns aware datetimes unnormalized — the
  W2.7 prerequisite, and worth doing on its own for the `filtered_archiver`
  month-bucketing bug
- **NM#357** the validator grouping/labelling defect
- **NM#358** `format: date-time` declared and unchecked
- **NM#304** commented with the three additions, the `metadata:
  additionalProperties: true` scope correction, and the `_get_priority` retraction

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

## Round 2 — the sweep, 2026-08-14

**Method.** Swept all 20 directories under `veen-systems/` (16 git repos, 4 not)
for the *behaviour* — "reads structured data and checks it against a declared
shape" — across eight query classes rather than for any name: schema libraries
(`jsonschema`, pydantic), TS/JS schema libraries, other Python validation
libraries, required-field constants, missing-field accumulators, `validate_*`
definitions, validation error types, **DB-level DDL constraints**, and
**shell/`jq` field assertions inside CI and ops scripts**. Peer sessions
re-derived their own repos in parallel.

### The headline count is wrong again

Round 1 said **four**. The sweep finds **at least 21** under a consistent
definition. The four were not wrong, they were a subset selected by an instrument
that could only see one shape of thing.

**⭐ The single most telling result: a grep for TS/JS schema libraries
(`zod|ajv|yup|joi|superstruct|valibot|io-ts|typebox`) returns ZERO hits across all
20 repos — while `ovr.news/src/lib/data/validate.ts` demonstrably runs on every
cycle and drops rows.** Hand-rolled validators are structurally invisible to a
library grep. That is the miss shape, reproduced deliberately and confirmed.

### New on the news chain

| # | mechanism | runs? | why it was missed |
|---|---|---|---|
| **⭐ 6** | **`ovr.news/src/lib/db-schema.ts:179-199` — the `articles` table DDL** | **on every insert, unavoidably** | it is not a schema file and not code anyone calls a validator. **A SIXTH declaration of the row shape**, and the only *enforcing* one at ovr |
| 7 | `pipeline-atlas/ops/make_snapshot.py` | **every 20 min, 72×/day** | its name says "snapshot". **The estate's most-executed consumer-side shape check** — hand-rolled `isinstance` + key presence over two artefacts it does not own, plus a **cross-field consistency check** (re-derives newest run by `max(started_at)`, compares to the producer's declared `runs_order`) that no JSON Schema can express |
| 8 | `pipeline-atlas/_includes/ops-figures.qmd` | in every reader's **browser**, every page view | a validator written in JavaScript inside a Quarto include. Not a script, not a `.py`, no "validate" in its name or path |
| 9–14 | `gen_views.py --check`, `check_render.py`, `run_verifies.sh`, `check_framework_drift.py`, `smoke_architecture.py`, `publish.yml` | CI | six more; `gen_views.py --check` is *stronger* than schema validation — byte-identity against the projection of a declared source |
| 15 | `NexusMind/scripts/deploy_filters.sh`, `llm-distillery/scripts/deploy_to_nexusmind.sh` preflight guards | on deploy | shape checks on filter packages |

### ⭐⭐ The FIFTH Contract A mechanism — the only one that ENFORCES, and it validates against a hand-copied schema

*(Found by pipeline-atlas; **verified here against `main`**, not the feature branch.)*

`NexusMind/scripts/main.py:118`:

```python
# Contract A required fields (must match contracts/fluxussource-output.schema.json)
_CONTRACT_A_REQUIRED = frozenset({"id","title","content","source",
                                  "source_type","url","collected_date","content_hash"})
```

used inside the per-line load loop at `:1008`, which **drops the row**:

```python
if not self._CONTRACT_A_REQUIRED.issubset(article):
    stats.setdefault("schema_invalid", 0); stats["schema_invalid"] += 1
    if stats["schema_invalid"] <= 5: self.logger.warning(...)
    continue
```

**Verified 2026-08-14:** the frozenset and the schema's `required` currently match
exactly — both are the same 8 fields.

**Why this outranks the other four.** Of the mechanisms the plan names, this is
**the only Contract A check that runs on the production path and enforces.** The
others are the producer's own schema, ovr's TypeScript (Contract B), and two
unscheduled NexusMind validators. It is invisible to a validator sweep **twice
over**: it names no script, and **its only reference to the schema is a comment.**

⚠️ **The production gate and the schema are two artefacts with one name, and nothing
makes them agree.** The comment *is* the mechanism. **If W2.1 or W2.3 edit
`contracts/fluxussource-output.schema.json` and not `main.py`, the check validates
against the schema while production enforces against a copy that no longer matches
it — and both are green.** That is principle 3 with the roles reversed: the caller
exists, and the file it claims to follow is decorative.

⚠️ **And its output already goes nowhere.** `stats["schema_invalid"]` is counted per
cycle and logged five at a time. **Verified: `data/last_run.json` carries neither
`schema_invalid` nor `json_errors`.** So rows are dropped for Contract A violations,
counted, and **the count reaches no reader.**

⚠️ **Correction:** this document said the file's `stats` dict was *empty*. **It has
no `stats` key at all** — `'stats' in d` is `False`; the top level is seven flat
scalars. *Absent and empty are not the same, and reporting one as the other is this
repo's own dead-field trap.* Those seven **do** already flow to the atlas, because
`read_last_run` does `data.get("stats", data)` and surfaces every scalar it finds.
(`filter_stage_timings` is nested, so a scalar-scraping reader gets **seven, not
eight**.)

🚫 **ROUTED ASK 1 IS WITHDRAWN — it was cheap as an edit and WRONG AS A DESIGN.**
*(NexusMind, same day.)* This plan briefly recommended publishing `schema_invalid`
through `last_run.json` on the grounds that it was a one-key change costing the
reader nothing. **Verified: `_write_last_run_json` is defined at `scripts/main.py:3283`
and called at `:3577` — at the END of a pipeline run.** So for the key to be there,
something must compute it **inside the pipeline process**, which puts contract
checking back in the **cycle tail**, under the 4h `TimeoutStartSec`, in the same
systemd job as production scoring — **the one thing both consumers independently
ruled out**, and a constraint already recorded in this document.

> ⭐ **It was cheap precisely BECAUSE it rides a surface populated by the thing we
> agreed must not do the work.** "Zero work for the reader" is not a design
> argument; it is a description of who pays.

**The settled artefact has none of this**: a separate timer writes
`NexusMind/data/contract_check.json`, the snapshot reads that, `last_run.json` is
untouched. It costs the reader a second file read, not a publication path — **and it
buys the check its own liveness signal, which `last_run.json` cannot give it. A
stale `schema_invalid` inside `last_run.json` is indistinguishable from a fresh one,
because that file's timestamp belongs to the PIPELINE RUN, not to the check.**

**That is the second instance of this exact shape** — ovr's `validate.ts` drops rows
into a `warn` nobody reads. Two makes it a pattern, and it is the strongest argument
for W5.1's artefact: **the numbers already exist, they have nowhere to land.**

**Two routed asks (NexusMind's to accept or reject, not ours to make):**

1. Publish `schema_invalid` and `json_errors` in `last_run.json`. pipeline-atlas's
   snapshot surfaces every scalar in that file automatically, so they would appear
   on the atlas the same day with no work on the reader's side.
2. **Make "the frozenset equals the schema's `required`" a defect class in the
   artefact.** One line, and it is currently held together by a comment.

**⭐ Finding 6 in detail.** `articles` declares `title`, `url`, `source` and
`published_date` as `NOT NULL`, enforced by SQLite on every write. The
`published_date NOT NULL` constraint **can never fire**: `scripts/summarize.ts:866`
and `:1433` substitute `rawArticle.published_date ?? new Date().toISOString()`
*upstream of the insert*, and `validate.ts` does not mention `published_date` at
all — `grep -c` → **0**, with `grep -c 'title'` → **1** in the same file as a
control proving the instrument reads it (ovr.news session). So an article arriving
without a publication date is **silently dated "now" and ranks as maximally
recent**.

⚠️ **Causality corrected by ovr.news, and it reverses what draft 2 implied.** The
fallback is **not an oversight that happens to satisfy the constraint — it exists
BECAUSE of the constraint.** Without it, a dateless row throws on insert. So this
is a `NOT NULL` workaround, and the pair is the real finding: **a shape gate that
cannot fail, and a silent default written to keep it that way.** Neither half is
sloppy on its own; together they convert "we guarantee a publication date" into
"we guarantee a non-null string".

**Measured since: `published_date` is null or empty on 0 of 1,335,210 upstream rows
over 14 days**, so neither path fires today. **But the repair has an ORDER, and it
is not the obvious one** (ovr.news, 2026-08-14):

- **Require the field upstream FIRST.** The fallback then becomes dead code and can
  be deleted safely.
- **Delete the fallback first and a dateless row goes from a silent wrong date to a
  crashed pipeline run.**

So *"should `validate.ts` require `published_date`"* is a **sequenced decision, not a
tidy-up** — the fallback is not merely permitted by the `NOT NULL`, it is
**load-bearing for it**.

### ovr.news's own inventory — eight mechanisms, one of them a "validator" by name

*(Re-derived by the ovr.news session, 2026-08-14. Their library grep confirms the
miss shape from their side: zod/ajv/yup/joi/superstruct/valibot/io-ts return **0
files** under `src/`, `scripts/`, `functions/` and **0** in `package.json`.)*

Beyond `validate.ts` (drops rows at `:166`/`:191`; blind to everything outside
`['id','title','url','source']`) and the DDL above:

- **Two undeclared gates in series, not one.** The metadata projection
  (`summarize.ts:887`/`:1342`, since 2026-04-09) narrows to a single key, **and**
  an explicit field-by-field top-level mapping (`:825`/`:1028`/`:1335`) drops any
  top-level field nobody wrote a line for. **Neither announces itself, and a field
  must clear both.**
  ⭐ **Measured from the PRODUCER's side, which is stronger than inferring it from
  ovr's** (2026-08-14, NexusMind's filtered output on sadalsuud): `source_category`
  is present on **114,836 of 114,836 rows — 100% — and reaches ovr on none of them**,
  because the projection keeps only `quality`. Same for `word_count` at 113,667.
  Other named casualties: `stage_used`, `filter_version`.
- **`getArticlesForBuild`'s INNER JOIN on `summaries`** (`db-articles.ts:288`) — not
  a schema check, but structurally drops any article that failed summarization.
- **CODE LANDED AND LIVE ON THE HOST, CORPUS PENDING — ovr#321 / ADR-046,
  `60ada82` on master 2026-08-14.** ⚠️ **NOT `2583951`** — this document recorded
  that hash and it **no longer exists on any branch**: `origin` had moved under them
  (the pipeline's own auto-commit of `chain_metrics` / `qa-report` /
  `source-funnel`), so they rebased. Zero file overlap, tests and lint re-run green
  on the rebased state. *A commit hash recorded before a push is a claim about a
  history that has not happened yet.*
  ✅ **Verified ON THE HOST rather than inferred**: `git rev-parse HEAD` on sadalsuud
  returns `60ada829`, `src/lib/published-date.ts` is present, `db-articles.ts`
  carries the canonicalisation. **The write-boundary half is live**, which is the
  pull-before-backfill step. They checked on the box rather than trusting their own
  `git log` because of NexusMind's path-scoped-deploy warning. `parsePublishedDate` returns `null` rather than an Invalid Date,
  canonicalisation moved to the DB write boundary, and lint rule **[7/7] fails the
  build** on a bare `new Date(published_date)`. **The first declared-shape check on a
  field this plan is about.** Green on the committed state: 1,266 tests, lint clean,
  verify sweep 84/0, `tsc` byte-identical.
  ⚠️ **The BACKFILL IS AUTHORISED (owner, directly) AND NOT YET APPLIED.**
  **FS#171 stays blocked until ovr confirms it has RUN and been verified** — not when
  it was authorised, and the confirmation goes from ovr to FluxusSource directly.

  **Report-only against the real production DB, and the population was wrong all
  day:**

  | | quoted all day | actual |
  |---|---|---|
  | rows to rewrite | 6,000 | **21,700** |
  | sub-ms precision lost | 131 | **340** |
  | naive / offset | 98.87% / 1.13% | **99.64% / 0.36%** |

  **A trimmed 6,000-row hot copy stood in for the corpus, and survived a full day
  because the file is named `ovr.db` and looked like it.** Third instance of the same
  class. ⚠️ **The tell fired only because they went looking** — nothing caught it, and
  they had flagged the population caveat before running, so nothing downstream took
  the wrong figure.

  ⚠️⚠️ **IN FLIGHT, so it is not misread as the backfill's effect:** the pull is live,
  so the **~17:00 summarize run uses the new parser BEFORE the corpus is backfilled.**
  Every naive-dated row reads **2h younger** from that run onward, which moves the
  `recencyBoost` step and **changes which articles are selected.** That is the
  intended order — code first, corpus second — but **the selection change lands
  before the backfill does.** Anyone watching ovr's output in that gap is seeing the
  parser, not the backfill. Caveat from their own review: still host-dependent for non-ISO input (RFC 822
  etc.); exposure measured at **0 rows — latent, not live.**
- **`tests/contract-validation.test.ts`** — 22 cases, **on FIXTURES**. Worth naming
  separately: it is the only thing at ovr that *looks* like a contract check by
  name, and the only one that never sees production bytes.

**Line-number corrections to round 1**, from the same pass: `og_image_url` is read
at **`summarize.ts:336-337`**, not `:334`; `quality` is read back at **two** sites,
`transform.ts:292` (`sanitizeSourceQuality`) and `:324`.

### Off-chain, and this is where the plan should have looked first

**W5.1's problem is already solved twice inside the estate, on the energy chain.**

| mechanism | what it already does |
|---|---|
| `energydatahub/utils/data_quality.py` → `data/data_quality_report.json`, gated at `.github/workflows/collect-data.yml:83-95` | a result artefact + a scheduled caller + a gate that **fails when the file is MISSING**, and a severity ladder `critical > error > warning > info` (`data_quality.py:122`) with exactly one enforcing level — ADR-022's *stamp always, decide once*, already shipped |
| `energydatahub/scripts/detect_schema_drift.py` (`collect-data.yml:156`) | **a shape-drift tripwire with a scheduled caller**, comparing a shape signature against the previous commit's, with a deliberate exit-code taxonomy and a self-maintaining volatile/stable split. This is the contracts check, built, running, and unknown to the plan |
| `augur/scripts/wait_for_edh.sh` + `augur-daily.timer` | **a cross-repo reader of a result artefact on a systemd timer**, keyed on the artefact's own `timestamp`, with a written timeout policy |
| `art/sanderveen.art/scripts/validate_content.py` | real content vs a CMS schema, **two callers**: CI (`hugo.yml:55`) and a git hook |
| `RenkumSpot/.../content-validation.test.ts` | CI, over **real** JSON content, required-field + enum constants |

The artefact spec (`docs/CONTRACTS_CHECK_ARTEFACT.md`) is built on these rather
than invented.

### A category round 1 had no name for: FAKE validators

*(Raised by pipeline-atlas against their own repo; confirmed independently here.)*
Mechanisms whose **claim** is about behaviour and whose **evidence** is existence.
They inflate the estate's apparent coverage.

**Confirmed instance, and it is on the page W4.1 wants edited:**
`pipeline-atlas/_generated/contracts-table.qmd:10` (from `ops/gen_views.py:224`)
emits *"Declared in X, **validated against** Y"* for every contract edge — and the
only check behind the word *validated* is `<!-- verify: ls -1 X Y -->`. **Two
inodes exist, therefore validation happens.** The atlas asserts the signature
failure on the page where it commits it.

⚠️ **The category is NOT "existence-only", and getting this wrong sends someone off
to convert 42 healthy commands.** Estate-wide there are **44** existence-only verify
commands; pipeline-atlas audited their own — **102 verify commands, 4
existence-only, of which only 2 are the defect.** `ls -1 FluxusSource/config/sources/`
backing *"the registry is internal"* is **fine**: the claim is about location, so a
listing is direct evidence.

**The tell is: a check whose output does not change when the claim becomes false.**
Their second, worse instance: `reference/contracts.qmd` runs
`ls -1 FluxusSource/config/schemas/` under the claim *"still no schema for
logs_summary.json — the object's SHAPE remains undeclared."* **A negative claim
backed by a directory listing a human must read.** Add `logs_summary.schema.json`
and it prints five lines instead of four and still passes. Reading the *command*
cannot reveal this; you have to read the **claim** and ask what would falsify it.

That formulation also covers the `--self-test`-always-returns-0 register entry and
the `format: date-time` no-op. **Existence-only is a symptom; unfalsifiability is
the disease** — and it is mechanically testable by the mutation rule this repo
already has: simulate the defect, confirm the check goes red or empty.

### A live collision, and it is in THIS repo

*(Found by FluxusSource while inventorying their metadata namespace; verified here.)*
The plan's abstract point — *the blob crosses two contracts and is described by
neither* — has a concrete instance with a crash in it:

- FluxusSource emits **`metadata.sentiment` as a plain STRING** (32 rows in the
  current 7-day window, yfinance only: `"neutral"` / `"bearish"`).
- `llm-distillery/ground_truth/samplers.py:105` does
  `a.get('metadata', {}).get('sentiment', {}).get('compound', 0)` — i.e. it expects
  a **VADER dict**.

**On a string, `.get('compound', 0)` raises `AttributeError`; the `0` default never
applies.** The path presumably only ever sees NexusMind-enriched rows, so this is
**latent, not firing** — but it is the same key name meaning two things across a
contract boundary, which is precisely what an undeclared blob buys. FluxusSource has
marked their key RENAME. **Ours is a one-line fix and is not yet made.**

### 🔨 W2.4 is BUILT but NOT MERGED — and phase 0a's exit criterion was WRONG

⚠️ **Correction to an earlier reading in this session: `b8a191c` is NOT shipped.**
It sits on branch `fix/357-contract-validator-grouping` with two siblings —
`f55f708` (NM#356, W2.7's UTC normalization) and `99c74a4` (NM#304, "Contract A
meets production — 4 defects, source_group held"). **Main is at `010338d` and has
none of them; no PR has been opened.** The error came from reading `git log` in a
checkout that happened to be on that branch — *a branch is not a release, and `git
log` does not say which one you are on unless you ask.*

The fix itself reports **both units** — `"N error(s) on M row(s)"` — which is the
artefact spec's requirement E. It ships with 10 new tests that **do not share a code
path with the fix**, and reverting only the group key fails 5 of them. The test file
is covered by CI: `ci.yml:33` runs `pytest tests/` wholesale. *(Read `:29` alone and
you conclude it is not — the narrow line is listed first.)*

Their measurement, on 6 raw files / **10,677 rows**:

```
before: metadata [required] x751, message names only 'priority'
after:  metadata.priority   636 error(s) on 636 row(s)
        metadata.word_count 115 error(s) on 115 row(s)     (636+115 = 751)
```

⚠️⚠️ **PHASE 0a's EXIT CRITERION WAS WRONG AND IS REPLACED.** The plan said *"the
check reports per-row counts, verified against a hand count on one known class."*
**Insufficient — and it fails silently in the flattering direction.** Which field
disappears depends on **jsonschema's error order, not on the data**: the sadalsuud
run hid `priority`, this corpus hid `word_count`. So **a hand count on whichever
class happens to be printed reconciles perfectly while the other class is still
invisible**, and phase 0a signs off on a still-broken instrument.

> **New criterion, from NexusMind:** *the number of `required` groups equals the
> number of distinct missing properties.* That is what the merge actually destroys,
> and unlike a hand count it cannot be satisfied by the surviving half.

**Two further corrections to the plan's text.**

1. **"It hid the `priority` defect for five days" is a special case, not the
   defect.** The defect is that **an arbitrary one of the two is invisible**, chosen
   by error order.
2. **Do not reconcile 636/115 against the plan's 928/267/1,195.** Different corpora
   — 10,677 rows here, 21,636 over 6 cycles there. Adding them is the estate's most
   repeated error.

⚠️ **And instrument trap 1 was too narrow.** `memory/stamp-contract-integrity.md`
said the merge *"affects `required` only — `enum` and `maximum` key on leaf paths, so
78 and 2,774 are row counts."* **The counts survive; the breakdown does not.**
`(source_type, enum)` keys on the leaf, so every violating **value** merges into one
group carrying one example. On a corpus with both `social` and `data` violations the
report names **one of them**. Wherever you read violation counts *by value*, this
applies.

**Consequence for sequencing:** phase 0a is no longer a prerequisite to build — but
it is a harder prerequisite to *verify* than the plan claimed.

### ⚠️ "Zero callers" cannot be measured by grepping the script's name any more

Round 1's evidence was *`grep -rIl "validate_production_contract"` across five repos
returns zero files*. **It now returns 14 — and 13 of them are prose the five
sessions wrote while documenting the claim.** The grep measured its own
documentation.

The claim is about **callers**; a name-grep counts **mentions**. Restricted to
executable contexts the count is **1**, and it is the new unit test — a caller, not
a scheduler. So the durable statement is the one round 1 already insisted on:
**unscheduled**, never *never executed*.

`validate_contract_a` still holds at **3** mentions: its own definition plus this
plan and its memory file. **No caller.**

### Also established

- **llm-distillery has no `.github/workflows/` at all.** Our own
  `training/validate_training_data.py` is documented in seven places and invoked by
  hand. This confirms round 1's split — W5.1 is **specified** here and must be
  **implemented where it runs**, because there is no CI here to run it in.
### ⭐⭐ The thesis arriving as EVIDENCE: two hops, both internally consistent, disagreeing by two hours

*(Found by ovr.news 2026-08-14; **verified here on `main`**, independently.)*

The same naive timestamp is read as **two different instants** on either side of the
NexusMind → ovr.news boundary:

| hop | how a naive `published_date` is read | verified at |
|---|---|---|
| NexusMind | `pub_date.replace(tzinfo=timezone.utc)` — **UTC** | `src/scoring/display_ranking.py:180-181` |
| ovr.news | ECMAScript parses an offset-less ISO string as **LOCAL** | language spec; sadalsuud is CEST |

**Both then apply the same recency rule** — `recency_threshold_hours: 24`,
`recency_boost: 1.3` (`display_ranking.py:36-37`, applied at `:200`). So an article
NexusMind scores at 23h old is **25h old to ovr**: NexusMind grants the 30% boost,
ovr does not. And `getDisplayRank`'s fallback into NexusMind's `display_rank`
**silently mixes the two timebases**.

⭐ **Why this is the plan's central claim rather than another bug.** Neither hop's
contract could have surfaced it: **each is internally consistent, and neither
declares the field's SEMANTICS** — only its type. A schema saying
`"published_date": {"type": "string", "format": "date-time"}` is satisfied by both
readings. *A contract that describes shape and not meaning cannot catch a
disagreement about meaning*, and this one has existed for as long as both hops have.

**It also refutes "the timestamp work is cosmetic" for good.** W1.1's payoff is not
standards hygiene — it is that two systems currently disagree about which articles
are new.

### ⭐ The SECOND automatic production-bytes check — and it looks like validation without being it

*(NexusMind's inventory of 11 mechanisms; **verified here against `main`**.)*
`deploy/gpu-server/main.py:338` — pydantic v2 models on the scoring API, running on
**every scoring request**:

```python
class Article(BaseModel):
    title:   str = Field(default="", max_length=MAX_TITLE_LENGTH)
    content: str = Field(default="", max_length=MAX_CONTENT_LENGTH)
```

Three properties, all confirmed:

- **Both fields default to `""`.** A row arriving with no content is **accepted and
  scored as an empty string**. The boundary **cannot distinguish "the body failed to
  arrive" from "the body is empty"** — precisely the distinction NM#304 refused to
  destroy on `word_count`, destroyed here at a different boundary.
- **No `id` field.** Request and response are correlated **positionally**. A
  reordering or a dropped item is **undetectable at the schema layer.**
- **No `model_config`**, so pydantic v2's default `extra='ignore'` applies: **every
  other field of the row is silently discarded here.** Contract A and Contract B
  both stop at this boundary.

**Net: the estate's two automatic production-bytes checks assert, between them,
eight key names and two strings' maximum length.** That is the headline at the top
of this document.

### ⚠️ `jsonschema` is in NO dependency manifest — every schema mechanism runs on a coincidence

**Verified on `main`:** `requirements.txt` contains no `jsonschema` and no
`rfc3339-validator`, while `scripts/validate_production_contract.py` is the one
thing that imports `jsonschema`. CI works because `ci.yml:25` does
`pip install jsonschema pytest` **inline**; sadalsuud works because its venv happens
to have it. **A venv rebuilt from `requirements.txt` cannot run it.** The missing
`rfc3339-validator` is NM#358's whole point (instrument trap 2), so **NM#358 is a
two-part dependency change: `format_checker`, plus BOTH packages into the root
manifest.**

⚠️ **RETRACTED, same day: this section first said "three manifests, three absences"
and called NM#358 a three-part fix by counting `pydantic` too.** Verified since:
**zero files under `src/` or `scripts/` import pydantic** — it is used only by
`deploy/gpu-server/main.py`, a separate service whose **own manifest carries it**.
The two manifests are **properly separated, not jointly incomplete**, and the root
manifest is *correct* to omit it.

> **The shape matters more than the fact, because it is this review's own pattern:
> a defect claim was read off three correct greps without checking whether the
> absent thing was NEEDED.** Absence is only a defect relative to a consumer.
> ⚠️ **And note the direction: it escalated.** A three-part change sounds harder
> than a two-part one, **and nobody downstream re-derives a warning.** Errors that
> inflate an ask survive longer than errors that shrink one.

⭐ **Consequence for the artefact, and it is a hard requirement:**
`validate_production_contract.py` already exits **2** for "could not run" versus
**1** for "found violations" — a good distinction that is **worth nothing unless the
caller treats 2 as an alert.** Today *"no new violations"* and *"could not import
jsonschema"* both produce a non-1 exit. **The artefact must carry that distinction
explicitly** — see `status: "could_not_run"` in the spec. NexusMind's parallel:
`verify_decision_log.py` prints PARTIAL and exits 2 rather than passing, since
NM#326. ***Exit 2 = "I did not look" is a distinction worth stealing estate-wide.***

### ⭐ The un-reconstructed check already exists and has never been run

**`validate/validate_contract_a.py` reads FluxusSource's `data/current/`
DIRECTLY** — pre-mutation, no stamps to strip, no reconstruction.

That matters because `scripts/validate_production_contract.py` reads NexusMind's
**mutated** `data/raw/`, so it must strip `_commerce_*`, `_obituary_*`,
`_violence_*`, `nexus_mind_attributes` and `display_rank` to recover the producer's
shape. **It validates a RECONSTRUCTION of producer output, not producer output.**
(It prints the subtraction, which is right.) Its `--cycles` also **defaults to 2**,
so the default invocation sees a *window*, not the corpus.

> **If W5.1 wants producer bytes rather than our copy of them, revive
> `validate_contract_a.py` — do not write a new script.** The estate already
> contains the better observation point and has never run it.

⭐ **And the argument is stronger than "it reads the right directory"**
*(pipeline-atlas, verified on `main` for both scripts, so not branch-contaminated).*
`validate_production_contract.py`'s per-class counts are **conditional on its strip
list being complete.** If NexusMind adds a stamp and does not extend the strip, the
check begins reporting `additionalProperties` violations **against the producer, for
keys the producer never emitted** — a false red pointing at the **wrong repo**.

**That is the exact mirror of the frozenset drift class: two places that must agree,
held together by nothing.** It is therefore a defect class the artefact must carry
in its own right — `drift.strip_list_vs_observed_keys`.

**`validate_contract_a.py` has no such dependency**, because it reads the producer's
own directory. **It is the only Contract A check in the estate whose result does not
depend on a second list being maintained** — a much better reason to schedule it
than its `--latest` mode.

*(The script agrees with this framing in its own source: it carries the comment
"NexusMind MUTATES data/raw/*.jsonl in place … So data/raw is NOT FluxusSource's
output as emitted", plus a strip function documented as "Remove keys NexusMind adds
to data/raw after FluxusSource wrote it." The file named `raw` is **neither** the
producer's bytes **nor** the scorer's text — it is pre-enrichment too. pipeline-atlas
is proposing it for `reference/invariants.qmd` as an artefact **wrong in both
directions from its own name**, not for the contracts page, since the arrow's payload
has not changed.)*

**A second local pattern worth copying:** `tests/unit/test_aegis_export.py`
validates **the output of `export()`** rather than a stored fixture — *"the only
place in the estate where a schema automatically meets something a code path
produced."*

### ⭐ The `source_group` control is LIVE, DEMONSTRATED, and deliberately HELD

Independently re-derived by NexusMind, who **did not read this plan before
measuring**:

- Contract A: `additionalProperties: false` at the top level, 14 declared
  properties, **`source_group` not among them.**
- Producer emits it unconditionally — `content_item.py:838` in the to-dict path,
  field at `:408`, ADR-010.
- **Real bytes:** `data/raw/content_items_20260814_080752.jsonl`, **3,697/3,697 rows
  carry it.**
- **The one thing that could have made the control silently dead was checked:** the
  validator strips NexusMind's own stamps before validating, and `source_group`
  matches neither `NEXUSMIND_STAMP_KEYS` nor the `_commerce_`/`_obituary_`/
  `_violence_` prefixes. **It survives the subtraction.**
- **Run end-to-end it fires:** `<root> [additionalProperties] 3697 error(s) on 3697
  row(s)`, *"'source_group' was unexpected"*, **exit 1.** Not available in
  principle — demonstrated on production bytes.

**They fixed Contract A today and deliberately did NOT declare it**, having put the
tradeoff to their owner as *"declaring this spends llm-distillery's only
non-circular control"*. After their fix the same file goes from **5 defect classes
to exactly 1, and the 1 is `source_group`.**

⭐ **The decision is pinned in CODE, not a note:**
`tests/unit/test_contracts.py::test_source_group_is_deliberately_still_undeclared`
asserts a row carrying it is **rejected**, with a docstring saying to delete the test
in the same commit that declares the field. **Declare it and the test goes red and
names the consequence.** Also under *"Not changed, deliberately"* in
`contracts/CHANGELOG.md` 1.18.0. **W2.2 stays held.**

⚠️ **Caveat that cuts against the control's strength, and it is theirs:**
`source_group` is **INERT downstream, not merely harmless.** The ingestion gate is a
subset test (`_CONTRACT_A_REQUIRED.issubset(article)`, `scripts/main.py:1008`) and
`commerce.py` round-trips the whole dict through `json.loads`/`json.dumps`, so an
undeclared top-level key is **neither rejected nor dropped**. That is what makes
holding it free. **It also means the control measures the CHECK's sensitivity and
says nothing about the pipeline's** — never report it as evidence that anything
downstream would have caught the field.

### The `source_type` enum fix must not be scoped from the corpus

**Today's data: `{rss: 3535, api: 64, data: 98}` — `social` does not appear at
all**, and the 98 `data` rows are all ourworldindata. **So W2.1 scoped from the
older corpus ("add `social`") goes red on the next cycle.**

NexusMind instead declared the producer's **controlled vocabulary** —
`SOURCE_TYPES = {rss, api, social, data, video}` (`content_item.py`, ADR-008 item 5).
**Declaring only observed values writes a vocabulary the producer can already
violate.**

⚠️ **This plan's first relay of that got `video` BACKWARDS — corrected by
FluxusSource, and the correction is the point.** It was written up here as
"including `video`, which has never been observed", filed alongside Contract A's
declared-and-unemittable `email`/`web`/`patent`. **It is not that defect. It is the
opposite one.**

| | `email` / `web` / `patent` | `video` |
|---|---|---|
| in the controlled vocabulary | **no** | **yes** |
| has an emitter | **none** | **two** — `vimeo_aggregator.py:287`, `youtube_api_aggregator.py:391` |
| enabled today | — | **yes**, `vimeo` in `aggregator.enabled_sources` |
| rows in window | 0 | 0, because `vimeo` is in `aggregator-health-report.json` → `summary.enabled_without_record` |

**`video` is reachable, configured and silent — an estate health problem, not a
contract problem.** Narrowing the enum to the observed corpus would start rejecting
rows the moment `vimeo` recovers.

⭐ **And the stronger half: `social` is emitted — 466 rows in a 7-day window** carry
social-only keys (`all_domains`, `primary_domain`, from bluesky/mastodon/vimeo/
youtube). **So declaring from that single run's corpus would have rejected every
social row in the estate.** That is the *same single-run denominator error* the 96%
figure was retired over, arriving from the other end — one run measures which
aggregators were due in that tick, and here the consequence is a closed enum that
silently drops an entire `source_type`.

> **Write this down, because the principle does not say it on its own:**
> **"Declare from the REACHABLE set" reads as "declare from what you OBSERVED"
> unless someone states that they differ. Reachable means the code can produce it,
> not that it appeared in your window.**

⚠️ **Trap they hit and avoided:** grepping `source_type=` literals in FluxusSource
surfaces **`atom`** — which is `SourceConfig.source_type`, a feed's **wire format**,
a different vocabulary entirely (`content_item.py:340` says so). It was nearly
declared.

### Relayed to FluxusSource, not a plan item

`config/schemas/source_schema.yaml` describes `priority` as *"1=highest,
10=lowest"*. **Production is the opposite** — 10 is `disaster_alerts_gdacs_alerts`,
9 the major-outlet tier, 5–6 the long tail — and their own
`docs/CONFIGURATION.md` agrees with production. **The 1..10 range is sound and is
what the ceiling fix used; only the polarity string is inverted.** A consumer
copying that description would invert its own semantics.

### Still open after round 2

- **The artefact spec is written** (`docs/CONTRACTS_CHECK_ARTEFACT.md`) and revised
  once against pipeline-atlas's review, which rejected `"armed"` as a field, forced
  the path inside their systemd mount namespace, and added the "a defect class may
  be `null`-with-a-reason, never absent" requirement. **Not yet accepted.**
- **The document needs restructuring before it reaches a cold reader** — see
  pipeline-atlas's review: undefined terms on first use, four genres in one file,
  a third of the body superseded, and roughly a dozen figures that **this plan's
  own success will falsify** (`2,774`, `928`, "one commit ever", "34 undeclared",
  "no caller at all"). Their rule: *a figure is safe in prose only if the mechanism
  that produced it would have to change for the figure to change.* Not yet done.
- Invert every "returns zero" verify command — **and the obvious inversion does not
  work**: `grep -rIl X . | wc -l` prints `0` but still **exits 1** under
  `-uo pipefail`. Use `echo "n=$(grep -rIl X . | wc -l)"`, which isolates the exit
  status and labels the number. Also: **do not use the ` — expect …` suffix in this
  file** — that convention is `run_verifies.sh`'s and does not travel; the curate
  runner hands the em-dash to the shell as a filename.
- Owner decisions 1, 2, 4 remain open.

---

## Round 3 — implementing the redesign, 2026-08-14

**Trigger:** the owner put the llm-distillery session on implementing the Contract A
redesign (#112), starting with the (b) fields and then the envelope. Four peer
sessions were briefed and all four answered. **Nothing was committed in any repo;
no session edited another's checkout.** The envelope decision is
`docs/decisions/2026-08-14-contract-a-envelope.md`; only what that record does *not*
carry is below.

### What the peers changed in my brief — every one of the four found something

⭐ **Three of the four corrections landed on claims I had inferred from code shape
rather than measured, and each peer measured its own repo.** That is the division of
labour working; it is also the fourth occurrence of *don't infer runtime behaviour
from structure* in this thread.

#### FluxusSource — takes all four (b) blocks; four specifics wrong in my brief

Measured on sadalsuud `data/current/`, 7-day hot window, **152,422 rows / 47 runs**.

1. ⭐ **`had_timezone` cannot be captured where I pointed.** `normalize_timezone:175`
   does branch on `tzinfo` — but it is called from *inside* `parse_date_string`
   (:127, :145). By the time `extract_date_from_rss_entry:110` calls it again the
   value is **already naive**, so that second call can never see an offset. Capture
   belongs inside `parse_date_string`.
2. ⭐ **`precision` is new code, not a capture.** The dateutil path (:126) is tried
   *first* and succeeds for nearly everything; `common_formats` (:132) is only the
   fallback. So "which format matched" answers precision for the rare tail, not the
   common case — the date-only-stored-as-midnight problem is **the default path, not
   an edge case**. Producer will parse twice with different `default=` sentinels and
   diff which fields dateutil actually filled. Most expensive of the five.
3. **`fabricated` has two sites with two populations, and they don't compose.**
   `rss_aggregator:592-593` calls both back to back, and since
   `extract_date_from_rss_entry` defaults to `fabricate_fallback=True` it never
   returns None there — so `ensure_valid_date:214` is **dead on the RSS path** and
   live only for `fabricate_fallback=False` callers (feed-health staleness, FS#98).
   One stamp reading as one mechanism would be wrong.
4. **`element` needs a wider vocabulary than the 7 `date_fields`** — `entry.time.datetime`
   (:74) and the `tags` term fallback (:91) also answer.

**`collected.clock_source`: three clocks, not two.** Of 36 `collected_date=` stamp
sites: **28 naive `datetime.now()`** (local, wrong), 6 `utc_now()`, and **2
`DateParser.get_timezone_naive_now()` which are correct** — the third clock I missed.
My "~27 vs 6" also described the wrong population: across `src/aggregators/*.py` there
are 138 `datetime.now()` in 21 files, mostly **cutoff arithmetic, not stamps**. The
stamp population is 36 and it is the one that matters.

⭐ **Measured effect, and it reprices the field.** Local is UTC+2 on sadalsuud, so a
wrong-clock row is stamped ~2h ahead of an RSS row in the same run. Against the
per-run RSS median: **5,901 of 152,422 rows = 3.87%** sit at +1.98h, across 14
families (newsapi_general 2,804 · pubmed 943 · github 723 · ClinicalTrials 424 ·
hackernews 279 · CrossRef 253 · arxiv 167 · …). All 144,844 RSS rows and all social
sit at ±0.03h. **So `clock_source` is ~96% constant from birth** and the fix is
bounded and fully enumerated (28 sites, 19 files). Stamp-before-fix still holds — the
stamp is what makes the fix provable — but plan for a 4% field, not a coin flip.

**`fetch.*`: the trap is one layer below `resp.encoding`.** Every strategy in
`RobustFeedParser` returns `response.content` (bytes), and `_fix_encoding_issues()` —
where `charset_used` is decided — **never sees the headers**. Same shape as the date
five, one function lower. The vehicle already exists: `fetch_ctx`, a dict created at
`parse_feed:333` and threaded through all four strategies, already carrying
`saw_5xx`/`hard_http`. Open question they raised and I agree with: the ladder makes
several requests, so the triple must describe **the request that produced the returned
bytes** — last-success-wins, stamped only on the winning branch.

**`content_meta.kind`: `full_text` is unemittable for a second reason.**
`rss_aggregator` never reads `entry.content` at all (feedparser's `content:encoded`
mapping), only `summary`/`description` at :548 — so even a publisher serving full text
in-feed arrives as a summary. ⚠️ **And the discriminator cannot be attribute presence**:
`:548` is `getattr(entry, 'summary', getattr(entry, 'description', ''))` and feedparser
routinely supplies an **empty string** rather than omitting the attribute — the exact
shape that made `hasattr(tag, 'term')` wrong in FS#138. Test the cleaned body's
truthiness.

⭐⭐ **And the measurement that strengthens LD#93 beyond what the proposal claimed.**
Of 144,844 RSS rows: 7,529 empty body (5.2%) + 204 body == title (0.1%) = **5.3%
`headline_only`**. The other 94.7% are feed summaries — median body **143 chars**,
p10 70, p90 914; 60.0% under 200, **77.2% under 300**. So the 300-char floor discards
77.2% of RSS rows, and what it discards is overwhelmingly **complete feed summaries,
not truncated articles**. `kind` is what licenses saying so: length was never the
quality signal.

⚠️ **A presence rate for a recently-shipped stamp needs its window checked against
that stamp's ship date.** FluxusSource retracted a `feed_declared_language` figure
(108,038 rows / 70.9%) before it propagated — `language_source` shipped **mid-window**
(0% on 08-07/08-08, 26.2% on 08-09, 100% from 08-10), so any count over the 7-day hot
window measures the rollout rather than the field. **Same 2026-08-10 boundary FS#149's
confidence floor is already pinned to**, and nobody had connected that it equally
poisons presence counts. Clean-window figures, and the disjoint-populations trap that
kills the name `declared_by_feed`, are in the envelope decision record.

#### pipeline-atlas — Category G confirmed as model facts; six corrections

Confirmed the two refusal sites and the asymmetry (`model/chain.yml` `gate:` block,
`gate.qmd` Level 4; the model's own comment: *"Same word, 'skip'; opposite
consequences."*). **They are not taking the implementation** — that repo owns no
pipeline code. Corrections, sharpest first:

1. ⭐ **The grain is wrong for the RSS tier, and this is the one that makes the
   sidecar useless.** `concurrent_rss` is **one source name holding the entire feed
   tier** (the breaker registry keys on source name, so an open breaker refuses every
   feed at once). But `health_state` runs per *feed*, and `poll_interval_actual_h`
   comes from per-feed `update_frequency` for RSS vs `aggregator_frequencies` for
   everything else — **two registries**. A per-source row for that name either
   aggregates N feeds into one meaningless value or silently reports the first.
   **Decide the grain per tier, or the tier carrying most of the feeds is the one the
   sidecar cannot describe.**
2. ⭐ **`outcome` must be written at the refusal site, not derived.** Derived from
   `collection_stats` it inherits the defect it exists to expose: Site B's
   `_record_skip` output is *already* classified downstream as `empty_sources`
   (`'error' not in stats and items == 0`), so `refused_in_aggregator` and `empty`
   are indistinguishable there **by construction** — a field that can never emit two
   of its four values. The `uncomputed_at_callsite` variant arriving in the block's
   first field.
3. **`health_state` must name *which* health.** Three "healthy" counts across two
   files, no two meaning the same: `summary.healthy_feeds` (fetch reliability),
   `summary.states.HEALTHY` (freshness/cadence ladder), and
   `logs_summary.json → health.feed_summary.healthy` (an unmarked **copy** of the
   first, up to a day stale). Worse, `HEALTHY` on the ladder is the **fall-through** —
   it means *unclassified*, not *fine*.
4. **"Measured at fetch" requires adding a read that does not exist.** The collection
   path constructs the health tracker and only ever writes to it; there is no
   "should I fetch this?" query anywhere. A new coupling from collector into the
   health subsystem — fine if intended, but an explicit spec line, not a free field.
5. **The enum is refusal-shaped and misses a live non-refusal defect.** Site A has a
   third branch: a plugin in `enabled_sources` with no `aggregator_frequencies` entry
   and no self-scheduled declaration falls through to `else`, warns, and **collects it
   every tick** (FS#121) — a weekly source on the collection cadence. `outcome` has no
   value for *"fetched, but on the wrong cadence"*, and `poll_interval_actual_h` only
   exposes it if **measured from consecutive fetches**; read from config it confidently
   reports the interval the source is failing to be polled at.
6. **`poll_interval_actual_h` has two semantics with no flag distinguishing them** —
   the due-time advance is guarded on the name already holding a row in
   `data/source_states.json`, and rows exist only for aggregators carrying scheduling
   metadata.

#### ✅ The grain blocker RESOLVED — and it makes G smaller

*(pipeline-atlas, same day, unprompted: they had sent the problem without the
resolution and noticed the plan now blocked on it.)*

⭐ **The test is: which fields presuppose a fetch? The collision is entirely inside
those, and none of them is what G is for.**

Both refusal sites decide at **source-name** granularity. Site A selects source names;
Site B's breaker registry is keyed on source name — which is *why* an open breaker on
`concurrent_rss` refuses the whole tier **before per-feed dueness is consulted at
all**. So the non-event itself, the thing G exists to record, is **natively per source
name and has no grain problem**:

```
collection (per source name, per cycle)
  outcome         fetched | refused_pre_dispatch | refused_in_aggregator | empty
  refusal_site    "A" | "B" | null
  refusal_reason  disabled | not_due | circuit_open | no_feeds_due | ...
  first_seen_run  "collection_20260801_120500"
```

**The four colliding fields — `health_state`, `poll_interval_actual_h`,
`raw_item_count`, `items_emitted` — all describe *how a fetch went*.** By this plan's
own framing that puts them in categories A–F. They drifted in from the neighbours and
**brought the grain problem with them.** Move them out and G is clean, per source
name, and still the least-blocked item in the redesign.

Two refinements not to flatten:

- **`poll_interval_actual_h` may be worth keeping in G**, because it is per-*source*
  for exactly the population that needs it: the FS#121 collect-every-tick sources fall
  through `select_sources_to_collect` **precisely for having no per-feed scheduling
  metadata**, so for them there are no feeds to disagree about. It is per-feed only for
  `concurrent_rss`, which is not the overpoll case. Keeping it with per-tier semantics
  declared costs less than losing the only field that can expose #121.
- ⚠️ **`refusal_reason` at Site B's `no_feeds_due` exit is an AGGREGATE** over per-feed
  decisions — the one place a source-name-grained field summarises feed-level facts.
  **Name it as an aggregate in the spec**, or *"the tier was refused"* and *"no
  individual feed happened to be due"* arrive as the same value. That is the
  four-states-collapse-to-one shape G was written to stop, **reappearing inside G.**

**Ownership as they framed it:** they own the chain model, so the grain *fact* is
theirs to supply; the schema is FluxusSource's data model and the spec is this repo's.
Recommendation, not decision.

✅ **And their blind-spot section shipped** — `reference/contracts.qmd`, standing, so
silence there cannot be read as a pass. ⭐ **The never-walked detector's null result
travels with the claim as a verify command rather than prose, and it is
mutation-tested in BOTH directions**: a url-less key in an examined file moves it
0 → 1 and names it, **and a new else-branch file — the case the old check could not
see at all — now appears in a named not-examined list instead of vanishing silently.**

⚠️ **Quote that null as "0 among the files it examines, with 5 excluded and named",
never as "0, clean"**, and "shown capable of firing" carries "on the shape it
examines". ⭐ **The general form, volunteered by pipeline-atlas against their own
artefact one turn after correcting me for the same thing: an instrument's null result
is only as broad as its denominator, so THE DENOMINATOR HAS TO TRAVEL TOO.** The
scope error was committed hours after the rule it violates was written down — their
own logged finding that knowing a class does not reduce the first-attempt error rate,
it only ensures the error is caught.

**On readership, in their words:** if the sidecar's only consumer is the ops snapshot,
it has failed READER BEFORE STRICTER and `raw_item_count` has repeated itself one
level up. The atlas can *report* it; that is display, not readership.

⭐ **Two declared blind spots they named — classes no row-schema check can ever see:**

- **The non-event one level up.** The source loader walks one level: a key holding a
  `url` becomes a source, a key that does not is skipped *without descending*. **A
  block of European feeds sat `enabled: true` collecting nothing for most of a year** —
  no error, no warning, no zero-yield alert, because a source that was never walked
  cannot report zero. A contract check validates rows that exist; a source emitting no
  rows is invisible to it **at any strictness**. This is Category G's own argument one
  level up, and it is the strongest case for doing G.

  ⚠️ **The incident is evidence; the detector is not.** pipeline-atlas re-ran the
  config-shape check that would catch the class against the live config —
  **2,080 source keys, 0 with no `url` of their own, across the 107 of 112 files
  declaring a top-level `sources:` key.** ⚠️ **The other 5 were not examined and the
  output said so nowhere** — `bluesky_accounts`, `mastodon_accounts`,
  `vimeo_channels`, `youtube_channels` reach the same one-level walk via the loader's
  else-branch. *(Not a live defect: those tiers are collected by aggregators reading
  their own files directly rather than through `get_sources()`, so excluding them is
  correct and widening the check would cry wolf. The defect was that the exclusion was
  invisible. Fixed at `4b71a7b`.)* It has never returned a
  positive, *"and an instrument that has never fired has not been shown to be able
  to. It is written against the shape of the incident rather than validated by it."*
  ⭐ **That strengthens the case for G rather than weakening it** — the only existing
  instrument for this class is an unvalidated config-shape grep, not a check on the
  data. But the caveat has to travel with the claim, or this thread's own failure
  class arrives inside the argument for the fix.
- **Attribution through the reconstruction.** The strip list is a hardcoded
  enumeration, so a key added on the NexusMind side and not added to it is reported as
  a *producer* violation for a key the producer never emitted. The check detects
  correctly and **attributes wrongly**.

#### NexusMind and ovr.news

Both are carried in the envelope decision record: the `language` name collision and
the four measured violation classes (NexusMind), and the closed offset gate, the
offset-grammar hole, and the ingest confirmation (ovr.news). Two items from NexusMind
that belong here rather than there:

- ⚠️ **`validate_production_contract.py` printed `metadata [required] x222` for what
  is 203 rows** — errors merged across two fields, and the example it printed was
  `word_count` (the 19-row minority), so `priority` (203 rows) **never appeared in the
  output at all**. NM#357 reproduced live on today's bytes; cite it.
- ⚠️ **Unreconciled numbers.** This document records `priority`-absent at **928** and
  `word_count` at **267**; NexusMind measures **203** and **19**. Different corpora
  (mutated `data/raw` vs FluxusSource `data/current`) and possibly errors-vs-rows
  again. **Nobody has chased it. Do not quote either pair until someone does.**

### Status at end of round 3

| | |
|---|---|
| Envelope | ✅ **settled** — declare-before-emit, closed at every level, `language`/`source`/`item` excluded |
| Producer-side (b) work | ✅ **accepted by FluxusSource**, sequenced kind → clock → fetch → time |
| Consumer-side declaration commit | ✅ **LANDED** — owner lifted the stand-down directly; `012da1a` on `feat/contract-a-envelope-declaration`, unpushed. Outcome test on 7,478 live rows: **introduced no new class** (⚠️ NOT "4 → 1" — the branch base 1.18.0 already read 1; the 4 → 1 belongs to NM#304/#356/#357). Hold unspent, falsification controls green. Based on **#360, which is a prerequisite** — the criterion cannot pass on `main` |
| `published.instant` offset | ⛔ **gate closed** by ovr.news; reopens when their write-boundary integration test exists and is green |
| Acceptance control | ✅ **resolved by splitting** — repeatable canary for "detection fires", declared gap for "catches the unanticipated" |
| `origin.*` | ⏸ **sequenced separately**, `docs/proposals/contract-a-origin-sequencing.md`; T0 (GDELT passthrough + `origin.method`) is the only engineering tranche |
| Category G sidecar | ⏸ spec needs the per-tier grain decision before anything else |

⭐ **Both halves are now unblocked.** The producer's declaration commit is written and
parked behind the consumer's, which has landed. What remains open is scope, not
permission: whether the rename ban extends past the three language keys (if it does,
`feed` collapses to `ttl_declared` alone), and whether `content_meta.kind` stays
RSS-only.


---

## Round 3 addendum — two blockers found by checking, 2026-08-14 late

### ⛔ 1. `NM#360` does NOT merge cleanly, and "merges clean" was a stale observation

```
gh pr view 360 --json mergeable,mergeStateStatus
  {"mergeable":"CONFLICTING","mergeStateStatus":"DIRTY"}
  9 ahead / 6 behind main · 14 files · CI green (test + GitGuardian, 14:18-14:23Z)
```

⚠️ **CORRECTED AGAIN, by NexusMind, against their own favour — it was not stale, it
was WRONG.** `origin/main` is at `4758226`, **the identical commit it was at when they
checked**. Nothing moved. Their command used the **old 3-arg `git merge-tree`, whose
output format does not emit the markers they grepped for**, so it returned 0 matches
and was read as 0 conflicts.

⭐ **A check whose pattern cannot match the thing it looks for reports clean whatever
the truth is** — a control that cannot fail, which is the exact class this thread has
been naming in everyone else's work all day. *(So my "a merge state is a relationship
with a moving branch" was a tidy generalisation of something that had not happened.
Correct in general; not what occurred here.)*

Verified properly, `git merge-tree --write-tree` exits 1:

```
CONFLICT (content): memory/MEMORY.md
Auto-merging  memory/project_session_2026_08_14.md   (clean)
```

✅ **Exactly one conflicted file and one conflicted ROW inside it — a docs index row.
No code conflicts at all.** `main` says *"MORNING ONLY — not current state"*; #360 says
*"Current state — no code changed"*. Both were true when written and both are
combinable. **So #360 is a small unblock, not a large one.**

**NexusMind's recommendation, which I endorse: merge `main` in, do not rebase.** #360
is a pushed PR with a green CI run from 14:23Z; rebasing 9 commits over 6 force-pushes
the branch, discards that CI result, and can replay the conflict several times. A
merge resolves it once, in a table row.

### ✅ And that conflicted row CLOSES the 928/267 vs 203/19 discrepancy

Both of us had recorded it as unreconciled. **#360's own side of the conflict already
contained the answer and neither of us had read it:**

> `priority`-absent vs `word_count`-absent was recorded as **928 / 267** — **that pair
> is host- and window-dependent** (sadalsuud's last 6 at midday 2026-08-14: 901/252;
> this checkout's last 6: 636/115) and must never be quoted without its corpus; the
> stable finding is that `word_count`-absent is a strict SUBSET.

Confirmed independently on the 7,478-row sample: all **19** `word_count`-absent rows
are among the **203** `priority`-absent ones. ⭐ **So the reconciliation is: the RATIO
is corpus-dependent and unquotable; the SUBSET RELATION is the stable finding.** Both
measurements were right and neither was comparable — the fourth
denominator-must-travel instance in this thread, and the answer was sitting in a
branch nobody had merged.

### ⛔ 2. RETRACTED: nothing downstream protects ovr from FS#171

I told ovr.news that NexusMind's `astimezone(timezone.utc)` stood between
FluxusSource's FS#171 and ovr's 20 lexicographic sort sites. **False, and backwards.**

**NexusMind RELAYS `published_date` byte-for-byte; it does not produce it.**
`scripts/main.py:1505` emits `article.get("published_date")` verbatim;
`parse_published_date` serves only *their* freshness cutoffs, archive buckets and
dedup, and **its return value is never serialized to output.** Proven by joining raw
to filtered on `id`: **6,024 matched rows, byte-identical strings, zero reformatted.**

**Consequences, both inverted from what I recorded:**

1. **The two-spelling defect is FluxusSource's, not NexusMind's.** The
   `+00:00`-with-microseconds form is in the producer's own bytes
   (`2026-07-13T15:23:03.480000+00:00`): **0.21%** of 7,478 live raw rows, **1.03%** of
   195,233 local raw, **0.58%** of 1,133,205 filtered — one phenomenon measured at
   three points on a pass-through, and it matches ovr's independent 68/6,000.
2. ⛔ **FS#171 is an ovr-facing hazard TODAY**, gated only on FluxusSource not yet
   emitting offsets. When it does, `+02:00` lands in ovr's filtered JSONL **unchanged**.
   ovr's offset test is not a guard on a hypothetical path; it is the real thing.

⭐ **And the fix moves repo.** Making it `Z` in NexusMind would mean **rewriting
producer data on a relay path** — a materially larger decision than a serialization
tweak, and the wrong site: **fixing it in FluxusSource fixes it for every consumer at
once**, including any that never read NexusMind. NexusMind declined and put
relay-verbatim to the owner as a property to keep or lose deliberately, which is
right.

⚠️ **The fix is a single canonical serialization, not an offset choice.** The prefix
collision (`'…T13:32:48'` is a prefix of `'…T13:32:48.480000+00:00'`) comes from the
**microseconds** as much as the offset — two rows at the same second with different
sub-second precision collide identically. And it is separable from W1.1: it changes
no instant and no ordering semantics, so it is not gated on ovr#321 or the clock fix.

*(Sixth wrong-sentence-beside-a-correct-finding here, and the costliest: it would have
sent the fix to the wrong repo AND left ovr believing they were protected.)*


### Round 3 addendum, later — the tie defect is 9 not 17, and the corrections cancel

**ovr.news, correcting their own figure in this record's disfavour.** ADR-046's *"17
unordered pairs share a second across the two shapes"* **overstates it.** Sharing a
*second* is not being the same *instant*: `'…T13:32:48'` vs
`'…T13:32:48.496000+00:00'` differ by 496ms, and text order is **correct** for them.
Exhaustively, naive-vs-`+00:00` has **0 inversions**.

**The true equal-instant / unequal-text count is 9** — all whole-hour timestamps where
the aware spelling carries no fraction (`…T04:00:00` vs `…T04:00:00+00:00`). It
remains the only thing that bites **without** an offset.

⭐ **So the two corrections move in OPPOSITE directions: the offset half is bigger
than recorded and the tie half is smaller.** Neither side should claim the net
position — this record had the mechanism backwards (NexusMind normalizes ⇒ ovr
protected) while ovr had the disproof sitting in their own numbers (**99.5% naive
output is impossible if NexusMind serialized its own aware parse — an aware datetime
cannot `isoformat()` to a naive string**). The original ranking survived by accident
on both sides.

### ⭐⭐ Predicate-vs-outcome, finally as a MEASURED result

The thread's running example was an argument: *"`published-date.test.ts:113` tests the
helper, not the path, and would stay green if canonicalisation were deleted."* ovr
built the outcome test and mutated the invariant to check:

| with `canonicalizePublishedDate` deleted from `db-articles.ts:141` | |
|---|---|
| ovr's new outcome test | **fails 7 of 9** |
| `published-date.test.ts` | **22 / 22 PASSING** |

**A green helper suite over a corpus that has silently reverted.** What makes it hold
is that `create-hot-db`'s prune was *extracted* so the test exercises the real `DELETE`
statement rather than a copy of it. **Cite this rather than the argument.**

*(Also shipped there: `FilterStats.validation` as the Contract B drop reader —
persisted, printed when non-zero, on the ops dashboard, and left **optional** so
absent ≠ zero for runs predating it. And `compareByPublishedInstant` with an
`article_id` tie-break so idempotent re-merges don't churn the month file.)*


### ⭐⭐ The spelling defect has FOUR classes, and the biggest one has no offset at all

**FluxusSource measured their own bytes** — hot window, 152,422 rows, 2026-08-07→14:

| spelling | rows | share |
|---|---|---|
| `…T09:12:03` — naive, no micro (canonical) | 148,147 | 97.195% |
| `…T01:41:14.720000` — **naive, MICROSECONDS** | **2,797** | **1.835%** |
| `…T06:51:12+00:00` — offset, no micro | 940 | 0.617% |
| `…T23:20:42.720000+00:00` — offset + micro | 538 | 0.353% |
| **non-canonical total** | **4,275** | **2.805%** |

Zero `Z`, zero non-zero offsets — those halves hold.

⛔ **The microsecond-only class is the LARGEST non-canonical population and is
invisible to any offset-based query.** 2,797 rows carry sub-second precision with **no
offset at all** — nearly **double** the entire offset-bearing population (1,478). This
record said microseconds matter *"as much as"* the offset; on the producer's data they
matter **roughly twice as much**, and ⭐ **a fix framed as choosing between `Z` and
`+00:00` would leave the biggest class untouched.**

**The collision is live at the producer too, and mostly not about offsets.** Grouping
every `published_date` to the same UTC instant at second precision: **459 seconds in
the 7-day window carry more than one spelling of that same instant**, and four of the
first five differ by microseconds only.

⚠️ **Do not read 459 against ovr's 9 as a discrepancy** — different populations (a
7-day producer window vs ovr's hot DB) and different units (*seconds carrying multiple
spellings* vs *unordered pairs*). Only the direction transfers.

⭐ **And this decides the fix SITE: it is not a rogue producer.** **207 distinct
sources** are affected across all three source types — `french_le_parisien` (700),
`newsdata_eval_td` (178), `mastodon_engineering` (172), `kathmandu_post`,
`nikkei_asia`, `sydsvenskan`, the `gdelt_*` arms. It is **publisher-supplied precision
flowing through untouched**, so a per-producer fix is 207 fixes and is wrong again for
producer 208. **It has to be canonicalized where the value is STORED** — one site in
`ContentItem`, the same rule that put `redact_secrets`, tag normalization and language
folding in one place each — and that fixes every consumer at once, including any that
never read NexusMind.

**Separable and ungated**, confirmed by the producer: `…T13:32:48+00:00` → `…T13:32:48`
changes no instant under naive-means-UTC, and dropping `.480000` discards precision no
publisher meaningfully asserted. Neither touches ordering *semantics* — it makes
existing values self-consistent, which is what the text sorts already assume. **Own
issue, not riding the three-part gate.**

⏸ **NOT STARTED.** New scope beyond the four items, rewriting bytes on a live field
with ~20 downstream sort sites. With the producer's owner, correctly not taken on a
peer's report.

✅ **`content_meta.kind` moved to top-level** (`f3e8954`, branch
`feat/contract-a-content-meta-kind`, **undeployed**) — it also needed the producer
schema to declare it, since that root is `additionalProperties: false` and
`validate_output.py` exits 1. Replayed over 5,995 prod rows: emitted on exactly the
5,739 RSS rows, **0 schema violations**, kind split unchanged. 22 tests, suite 1,224
green.


### ✅ #360 green, #364 open — and a green tick that is not a test result

**NM#360** merge-forward done (`origin/main` merged in, **not** rebased — it was a
pushed PR with a CI result, and rebasing 9 over 6 would have force-pushed and replayed
the conflict). `5b86c5f..5fb92d9`. **Verified independently from this repo:**

```
gh pr view 360 --json state,mergeable,mergeStateStatus
  {"state":"OPEN","mergeable":"MERGEABLE","mergeStateStatus":"CLEAN"}
```

Ready to merge, **waiting only on the owner** — NexusMind correctly did not merge it.

The conflicted row **was** the 928/267 reconciliation, and resolving it meant combining
both sides rather than picking one, plus the third corpus (203/19) and the invariant
promoted to the headline: **`word_count`-absent is a strict subset of
`priority`-absent** — the part that survives every corpus.

**NM#364** open behind it — `feat/contract-a-envelope-declaration` →
`fix/357-contract-validator-grouping`, 1,305 tests green *locally*, acceptance still 1
class on 7,478 production rows.

⚠️⚠️ **#364 SHOWS "ALL CHECKS PASSED" AND HAS NOT RUN THE TESTS.** `.github/workflows/ci.yml`
triggers on `pull_request: branches: [main]` only, so a **stacked** PR gets GitGuardian
and nothing else. Confirmed from here:

```
gh pr view 364 --json statusCheckRollup
  checks: [ {"name":"GitGuardian Security Checks","conclusion":"SUCCESS"} ]
                        ← no `test` job, at all
```

⭐ **A green tick whose meaning is "the tests were not run" is the purest instance of
this whole thread's failure class** — the signal exists, is truthful about what it
measured, and is read as something it never claimed. It gets real CI the moment it
retargets `main`, i.e. after #360 merges. **The only test evidence for #364 today is
that someone ran them locally and said so.** *(Flagged by NexusMind unprompted, which
is the right instinct: the danger is exactly that nobody looks at which checks ran.)*


### ✅ #360 MERGED, #364 green on real CI — and a two-session collision

**NM#360 merged** `7d1086f`, 15:55:32Z. **NM#364 retargeted to `main` and its `test`
job ran for the first time.** Verified from this repo after the fact:

```
#364  base=main  mergeable=MERGEABLE  mergeState=CLEAN
      test=SUCCESS   test=SUCCESS   GitGuardian=SUCCESS
```

So the 1,305 local passes are now corroborated by real CI on the merged tree. **Not
red** — but it was worth forcing, because until then the only evidence was someone
saying they had run them.

⭐⭐ **Three mechanism findings, none of which is about this PR:**

1. **`--merge` without `--delete-branch` leaves a stack pointing at a merged branch,
   silently.** GitHub's auto-retarget fires only when the base branch is *deleted*.
2. ⭐ **Retargeting does not re-run checks under default `pull_request` types**
   (`opened`, `synchronize`, `reopened` — a base change fires `edited`). So a
   *corrected* PR can carry a stale empty green, **and this is the nastier one,
   because the correction increases the PR's apparent legitimacy while changing the
   evidence not at all.**
3. ⭐ **Two sessions given the same owner "go" will both act, and the duplicate-work
   fingerprint only appears afterwards.** Here: `gh pr merge 360` returned *"already
   merged"* to the NexusMind session — this repo's merge had landed seconds earlier —
   and both sessions then close/reopened #364, leaving **two `test` check runs** as
   the visible trace. **Cheap only because every action taken was idempotent** (merge,
   retarget, reopen). It would not have been if either side had pushed a commit, and
   the other session nearly pushed an empty one to fire CI before choosing reopen.
   **Convention worth adopting: under one owner instruction spanning repos, say which
   side is taking the action before taking it.**

⚠️ **And one more state-vs-mechanism instance, self-reported.** The NexusMind session
told the owner #364 *"auto-retargeted to main"*. It did not — this session retargeted
it with `gh pr edit`. They read the *state* (`base: main`) and inferred the
*mechanism*, without checking that the branch had been deleted. It had not.
**Reading a state and inferring what produced it** is the same move as their
`merge-tree` grep and as every wrong-sentence-beside-a-right-finding in this thread.

⏸ **`published.instant` remains DROPPED and CONTESTED** — the one thing in #364 that
is not settled, recorded there as a live decision with the foreclosure argument
attached.
