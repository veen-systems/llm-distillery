# Contracts: a five-repo plan

**Draft 1 + review round 1, 2026-08-13 evening. Written by the llm-distillery
session; reviewed by the FluxusSource, NexusMind, ovr.news and pipeline-atlas
sessions.** Every number is measured; provenance, the verify commands and the
instrument defects that constrain how these numbers may be quoted are in
`memory/stamp-contract-integrity.md` § *The contracts layer*.

**Status: NOT APPROVED, NOT EXECUTED. No repo has an owner greenlight. Nothing
was committed in any repo. Round 2 has not been run.**

⚠️ **Draft 1's headline premise was FALSE and is corrected below.** It asserted
that nothing anywhere runs a consumer schema against real producer bytes. There
are **four** validators; see § *The problem*. The claim came from grepping for one
script *name* rather than for the *behaviour* — the error this plan exists to fix,
committed while writing the plan. Left visible rather than silently patched.

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
Phase 0a FIX THE INSTRUMENT first                            -> per-ROW counts, verified vs a hand count
Phase 0b build the check, reporting-only, exit 0 always      -> proves it sees the known defects
Phase 1  fix the wrong declarations                          -> check goes green on those
Phase 2  declare the undeclared, with status                 -> check stays green
Phase 3  flip the check to fail the build                    -> now it guards
```

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
| W2.4 | Fix `validate_production_contract.py`'s grouping + labelling | It counts **errors, not rows**, and merges distinct `required` failures into one line — which hid the `priority` defect for five days. No baseline file exists, so zero migration cost. **Must land with a test**: one row missing two required properties → two distinct groups |
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
| W5.1 | **Specify the CI job** (phase 0 above) | The load-bearing item. Specify here, implement where it runs — probably NexusMind CI plus a scheduled run against real bytes |
| W5.2 | **Correct FluxusSource#164's stated justification** | See below — this is ours to answer and the reason on record is wrong |
| W5.3 | Keep `CONTRACTS-BRIEF.md` current | Four sessions are working from it |

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
- **ovr reads exactly 2 of 52 metadata keys** — `og_image_url` (`summarize.ts:334`)
  and `quality` (`transform.ts:324`). A **96% undeclared projection**, and a far
  better figure than draft 1's `word_count` example, which was a **name
  collision**: 49 occurrences at ovr, **zero** reading the upstream field.
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
  fully green check is compatible with ovr dropping 50 of 52 keys, which is what
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

## Round 2 — not run

Open when it resumes:

- Rewrite the premise around *four validators, none watching the failure* (done
  above; peers have not re-reviewed it).
- **Spec the result artefact** — blocking pipeline-atlas.
- Re-run the hand-rolled-validator sweep across all 20 `veen-systems/` repos
  before any of this reaches the atlas. Two were missed by searching for a script
  name instead of a behaviour; assume more.
- Invert every "returns zero" verify command so the true state prints.
- Owner decisions 1, 2, 4 remain open.
