---
name: stamp-contract-integrity
description: What validates the per-article stamps and what does not — Contract B checks shape only and had never met a production row; scripts/stamp_census.py checks population and consumers. Read before adding a stamp, a config key, or trusting a stamped field.
metadata:
  type: project
---

# Stamp & contract integrity

**Established 2026-08-08.** The owner observed that the stamps are "basically
creating features per item" — which is exactly right, and reframes ADR-022's
*"stamp always, decide once"* as the ML-ops split between feature computation and
decision policy. That is also why the hard constraint says changing thresholds
must never require re-labelling.

An article carries **~40+ numbers**: 6 lenses × 6–7 dimensional scores, plus
per-lens flags, plus 12 top-level model stamps (`_commerce_*`, `_obituary_*`,
`_violence_*`), plus `content_quality`, `image_analysis`, `source_quality`, and
FluxusSource's `metadata.*`.

## The trap: a feature store with silently-null columns is worse than none

Every stamp failure this project has had is one of three shapes, and **none of
them is a shape error**, so none is catchable by a schema:

| Shape | Instance |
|---|---|
| **Absent** — key never reaches the row | NM#300, `content_length` on 0 of 50,605 |
| **Null** — key written, value emptied upstream | NM#300 after a partial fix (see below) |
| **Constant** — present, never discriminates | LD#94, `gatekeeper_applied` in 191,616 |
| **Unread** — populated, zero consumers | LD#101, `type_classification` → an A/B rig published |
| (and the sibling) **Unreachable** | NM#284, per-filter prefilters, six months |

## What validates what

**`contracts/*.schema.json` (NexusMind) — SHAPE only, and it is permissive.**
`additionalProperties: true` at the root, at `nexus_mind_attributes.<lens>` and
at `source_quality`; only **five** lens fields are `required`. It can catch
*present-but-wrong*. It is structurally blind to absent, constant and unread.

**Worse, until 2026-08-08 it had never been run against a production row.**
NexusMind's `tests/unit/test_contracts.py` validates `tests/fixtures/`. First run against
2,400 live rows: **908 violations**, one field —
`image_analysis.image_confidence`, declared `0..1`, actually a **raw logit**
(range −12.330..6.365, median −2.696, **68.4%** outside the bound). The producer
was self-consistent all along (`ml_confidence_threshold` default **2.944**,
stated in `src/preprocessing/image_analysis.py:546,575`); the **contract** was
wrong from the day it was written.

*Why fixtures could never have caught it:* the `url_pattern` layer emits `1.0`
and `domain_duplicate` emits `0.9`, so every hand-written example looked like a
probability. **A fixture encodes the author's belief about the data; a test over
fixtures can only confirm that belief.** Filed as **NM#303** (add production
validation). Contract B is now **1.15.0**.

**`scripts/stamp_census.py` (NexusMind, `e64a45f`) — POPULATION and CONSUMERS.**
Three checks: (A) declared-but-never-observed, by scanning writers for
`result["x"] =` and comparing against reality; (B) never-populated / nearly-empty
/ constant, with constancy computed **per filter**; (C) populated with no reader
outside the writer files.

```
ssh sadalsuud 'cd ~/local_dev/NexusMind && python3 scripts/stamp_census.py --cycles 2'
```

**Its acceptance test is that it rediscovers all four failures above, and v1
failed that test.** It missed NM#300 (the key is *absent*, so a census keyed on
observed fields never mentions it → check A exists because of this) and missed
LD#94 (six filters averaged together hide a single-filter constant → per-filter
constancy exists because of this). Do not weaken either without re-running the
acceptance test.

**Two limits, printed after every run:** `filtered_*.jsonl` holds **survivors
only**, so a 0% can mean "stamped only on rows this file never sees"; and the
reader count is textual, so it cannot see dynamic access and 0 readers is a
question, not a verdict.

**A THIRD limit, found 2026-08-08 — check A false-positives on rare fields.**
`--cycles 2` reported `enriched` / `enriched_at` as "assigned in a writer, but
present on 0 of 32,040 rows", and I read that as a dead branch. It is not: the
branch fires and works. Post-scoring enrichment succeeds **0–3 times per filter
per cycle**, so two cycles can legitimately contain zero. Verified by pairing
the log line with the row — `Enrichment complete: 3 fetched, 3 replaced` at
12:51 → `enriched=True` on exactly **3** of 1,843 investment_risk rows.

**A rare-but-working field is indistinguishable from a never-written one at
small `--cycles`.** Before calling anything from check A dead, either raise
`--cycles` or find the writer's log line and match its count against the rows.
Of the six fields check A flagged that day: three were real
(`content_length`, `stage_used`, `stage1_estimate` — all NM#300's allowlists),
one was config-off by design (`short_content_cap_applied`), and **two were false
positives**.

## Unprompted findings from the first census run (15,118 rows)

- `stage_used`, `stage1_estimate` — assigned by a writer, on **no** row. This was
  **LD#88 item 1**; ~~open~~ **fixed and verified the same day** (100% populated
  from the 17:10 cycle), LD#88 closed. Kept as the worked example of check A
  finding a real defect unprompted.
- `short_content_cap_applied` — never observed; LD#93's cap is off on every
  filter by config (expected, but now visible).
- `normalization_method` constant `percentile`; `passed_prefilter` constant
  `True` (the latter is NM#284's fingerprint plus the survivors-only bias).
- Five fields stamped on every row and declared in no contract:
  `raw_weighted_average`, `normalization_method`, `content_length`,
  `original_content_length`, `obit_pattern_count`. **`raw_weighted_average` is
  the one that matters** — ADR-022 says visibility keys on it while
  `weighted_average` is rank-in-batch, and it being undeclared while
  `weighted_average` was declared is plausibly how the two got conflated.

## VERIFIED FIXED — 17:10 cycle, 2026-08-08

`content_length` **100% populated in all six filters** (2,189–2,647 rows each),
up from 0 of 50,605. `stage_used` / `stage1_estimate` likewise 100% (LD#88).
<!-- verify: bash scripts/verification/check_content_length_populated.sh -->
<!-- verify: manual — the probe-never-surfaces result below is a property of the CURRENT thresholds, not a law. Re-run the stage_used vs op-point cross-check after any filter version bump or probe-threshold change. -->

**Unprompted result from the first cycle that carried `stage_used`: no surfacing
article is ever probe-scored.** `stage1_low` rows peak at raw **0.75–1.50**
against op-points of 2.25 (`solutions`) and 3.75-4.5 (the rest — 4.0 for
`belonging` / `cultural_discovery`, 3.75 `nature_recovery`, 4.25
`investment_risk`, 4.5 `uplifting`; this line read "4.0 (the rest)" until
2026-08-16, correct when written and stale from the 08-11 moves. The finding
is unaffected: every move but one was UPWARD, and 3.75 is still far above the
stage1_low peak), so
`surfacing AND stage1_low` is **0** in every filter. Probe-derived scores cannot
reach the visible band, which is the hybrid design's core safety claim and had
never been checked on production rows. It also means any analysis of surfacing
scores is measuring **student output only**, not a mixture.

**My pass criterion was the wrong shape and I published it anyway.** I
pre-registered "`stage1_low` should be a nonzero *minority*, the 08:00 journal
showed 17–32%". Observed: solutions **64.6%**, cultural_discovery **51.5%** —
both "fail" that wording. The 17–32% came from journal lines whose filter I never
identified, so the baseline was not the same quantity; and a screening rate has
no reason to be a minority. The right criterion is *populated, discriminating
(≥2 values), and no `stage1_low` row above the op-point*. **A per-filter quantity
compared against an unattributed aggregate is not a check** — third instance
today, after `source_filter excluded N` and the GN population split.

## NM#300 is FIVE allowlists in series (2026-08-08, proven by outcome)

It was diagnosed as "two drops in series", both fixed and deployed — and the
next cycle still read **0 of 2,170**, with both fixes provably loaded. There are
five explicit allowlists between the scorer and the persisted row:

| # | location | |
|---|---|---|
| 1 | NexusMind `deploy/gpu-server/main.py` — `FilterScoreResult` (Pydantic) | server |
| 2 | `src/scoring/gpu_client.py:141` — `FilterScoreResult` **dataclass** | client |
| 3 | `src/scoring/gpu_client.py:815` — its construction from `response.json()` | client |
| 4 | `scripts/main.py:481` — dataclass → dict conversion | consumer |
| 5 | `scripts/main.py:1099` — the `analysis` dict | consumer |

The first diagnosis fixed 1 and 5 and checked the wrong seam for a third: it
verified that `analysis` is attached whole and written with
`json.dumps(article)` — true, and not where the loss is. **When a value crosses
a process boundary, patching the sender does nothing unless the receiver's
parser is also an allowlist — and here it was, twice.**

**`absent` vs `null` localises the fault for free.** After hops 1+5 were fixed,
`content_length` went from *absent* to *present-and-null*. Absent = nobody wrote
the key. Null = the last hop wrote it and something upstream had already emptied
it. That distinction pins the fault to the middle hops without reading code —
and a census that only counts `is not None` throws it away. Check `"k" not in d`
separately from `d[k] is None`.

## Rules

1. **Before adding a stamp, name its consumer.** If there is none yet, say so in
   the commit; an unread stamp is a liability, not an asset (LD#101).
2. **Never promote a field to `required` on the strength of the code that writes
   it.** `content_length` was assigned unconditionally and reached zero rows.
   Promote only after the census shows it populated.
3. **Run the census before quoting any stamped field in an analysis.** A field at
   0% or constant will otherwise look like a clean finding.
4. `metadata.*` is FluxusSource's namespace. NexusMind not reading it is normal;
   the census excludes it from the no-reader finding for that reason.

Related: `nexusmind-data-sources.md` (what each artefact excludes),
`prefilter-length-floor-hypotheses.md`, `docs/adr/` ADR-022.

---

# ⭐ REDIRECTED 2026-08-14 — the contract is being REDESIGNED, not patched

**Read `docs/proposals/contract-a-redesign.md` before anything below.** The owner
stopped the incremental work: a day across five sessions produced **four corrected
values in one schema file** plus a large amount of verification process. Everything
below remains true as *measurement* and is superseded as *plan*.

**The design rule:** a field belongs in Contract A **iff** only the collector can know
it **and** it is destroyed if not recorded now. Today's contract fails both ways — it
stores derivable values (`word_count`, `reading_time_minutes`) and discards
irrecoverable ones (the publisher's stated timezone, the charset actually used, whether
a date was fabricated, whether a source was even asked).

**Seven categories of exclusive+perishable fact**, A–F from defects tripped over and
**G supplied by pipeline-atlas from the chain model**: time · language (incl. `script`)
· origin (country/region/IANA tz) · fetch (charset triple, redirects) · content fidelity
· feed · **the non-event**.

⭐ **G is the one nobody would find from symptoms.** A–F all presuppose a fetch
happened. Two sites refuse work *before the network* — one leaves **no trace at all**,
the other records `items: 0` with no error key, so it reads as a successful empty visit.
**"This publisher went quiet" and "we stopped asking" are indistinguishable downstream,
and they have opposite editorial meanings.**

✅ **BOTH ANSWERED by FluxusSource at close.** `content_meta.kind` is **(b), one line —
and it COLLAPSES**: FluxusSource never fetches bodies (~~`full_text_fetcher.py`~~ deleted,
enrichment moved to NexusMind), so `full_text` is not emittable and `kind` reduces to
`feed_summary` vs `headline_only`, both decidable at parse time. **This retires the
300-char floor.** `origin.*` is **(c)** and no country/timezone exists anywhere — but
**the unit is ~1,872 per-source YAML entries, not ~30 aggregators**, ~932 bulk-seedable
from geographic shelves: **an editorial cost, not an engineering one.** Most of TIME is
(b) and threading-out rather than computing; **most of LANGUAGE already exists** as
`language_source`/`language_confidence`/`language_input_len` — ⚠️ **do not rename them**,
two are inputs and #149's floor is fitted on the others.

⭐ **And the field this proposal MISSED: `collected.clock_source`. 19 of 26 aggregators
build `collected_date` from local `datetime.now()`** — byte-identical downstream to a
UTC value and wrong by the host offset, unrecoverable. The same defect as
`published_date`'s, on *our own* clock, and nobody had noticed.

**Superseded, kept to date the correction:**

1. ~~**FluxusSource feasibility triage**~~ — which proposed fields are already in hand at
   collection, which are one line, which need new plumbing. Two decide the sequencing:
   does `origin.country`/`timezone` exist in source config in *any* form, and is
   `content_meta.kind` (full body vs feed summary vs headline) knowable at collection?
   **If the second is yes it retires the 300-char floor outright.**
2. **`_get_tzinfos` third population** — still UNMEASURED, and it fails in the direction
   of looking correct (an unrecognised tz abbreviation is silently relabelled UTC and
   arrives *aware but wrong*). Do not let "unmeasured" decay into "small".

⚠️ **Blocker the redesign inherits:** both schemas set `additionalProperties: false`, so
**a redesign cannot ship incrementally under the current shape** — the shared-envelope
question arrives as a hard blocker rather than a design choice. Full invalidation list
(6 items, ranked by how quietly each breaks) is in the proposal.

---

# The contracts layer (2026-08-13, five sessions in parallel)

**Plan and full round-1 review: `docs/CONTRACTS_PLAN.md`. This section holds the
measurements and the traps.** Nothing was executed or committed in any repo.

## The finding

**The estate has FOUR contract validators and none watches the failure.** Draft 1
of the plan claimed nothing ran a validator at all; **that was false**, refuted by
ovr.news. The claim came from grepping for one script *name* rather than for the
*behaviour* — `a grep for a pattern is not a grep for a behaviour`, broken while
auditing contracts.

| validator | on real bytes | blind to |
|---|---|---|
| `FluxusSource/scripts/validate_output.py` | yes, with a track record | consumers' beliefs — its own schema only |
| `ovr.news/src/lib/data/validate.ts` (`summarize.ts:404`, since 2026-03-03) | yes — and **drops rows** into an unread log | `published_date` **and** `metadata`: `grep -c` → **0** |
| `NexusMind/scripts/validate_production_contract.py` | when invoked | — **unscheduled** |
| `NexusMind/validate/validate_contract_a.py` | has `--latest` | — **no caller** |

Say **unscheduled**, never *never executed*: no file naming a script is not proof
nobody ran it interactively.

## Measured, run `content_items_20260813_161006` (3,514 rows) unless stated

- Top level **12 fields on 100%**; `metadata` **52 distinct keys** — ⚠️ **a
  SINGLE-RUN count, and NOT a namespace measurement.** Reproduces exactly, and is
  still the wrong quantity for almost every question: per-run counts range **27 to
  107, median 63.5** across 50 runs. **Never derive a share or a percentage from it**
  — see the retirement note below before quoting this line.
- FluxusSource's schema declares **7** metadata keys, Contract A declares **12**,
  **overlap ZERO**. Provenance half vs operational half. 34 declared by neither —
  **legal**, Contract A's `metadata` is `additionalProperties: true`; only its top
  level is closed.
- Contract A defects over 6 cycles / 21,636 rows: `social` missing from the enum
  (78 rows); `priority` ∈ {9,10} over `maximum: 8` (**2,774**); `word_count`
  absent (**267**) and `priority` absent (**928**) though both `required`.
- **ovr reads exactly 2 metadata keys** — `og_image_url`, `quality`. `og_image_url`
  is read at `summarize.ts:334` **upstream** of the `:887` projection that discards
  it, so a field can be load-bearing at ovr and **leave no trace in the stored row**.
  ⚠️ **The "2 of 52 / 96% undeclared" form is RETIRED (2026-08-14), and the reason
  is stronger than "wrong denominator".** The **2 is solid.** But **a single-run key
  count is not a namespace measurement at all** — it measures which aggregators
  happened to be due in that tick. FluxusSource counted distinct metadata keys per
  run across all 50 runs in the hot window: **min 27** (`…_20260808_160714`, 494
  rows), **median 63.5**, **max 107** (`…_20260813_001014`, 3,814 rows) — a **4×
  spread**. The run this file used gives 52; the next morning's gives 55. Sampling
  six hours either side would have produced a visibly different percentage over the
  same estate. **52 reproduces exactly** (`collection_20260813_161007`, 3,514 rows,
  independently confirmed by the producer), so it is a correct number answering a
  question nobody wanted asked.
  - The producer's inventory counts **168** keys, **154 of the 168 confined to a
    single `source_type`**. That is the **hot-window union** — `data/current/`, 50
    runs, 2026-08-06→08-14. **Do not call it "the full namespace":** `data/archived/`
    is kept indefinitely since FS#164, so keys retired before 08-06 sit outside it.
  - **3** keys are read by name in consumer pipeline code: `quality`,
    `og_image_url`, `priority`. ⚠️ **Carry this caveat with the 3 every time** — it
    means *read by name*, **not** *the only keys that can break a consumer*.
    NexusMind passes the whole `metadata` blob through untouched into
    `data/filtered/*.jsonl`, so a key nobody names still travels and can still be
    depended on downstream. Without that sentence the 3 reads as a safety margin it
    is not.
  - **Quote the 2, the 3 and the 154/168 with its window; do not reconstruct the
    percentage.** It also moves the wrong way: declaring more keys (principle 1)
    makes it look worse.
- Byte budget: 1,700 B/row · `metadata` **37.5%** (larger than `content` at 23.8%)
  · repeated JSON keys **30.3%** · gzip 4.5×.
- Standards: `language` 3,509/3,514 two-letter, `zh-cn` ×5; `published_date` /
  `collected_date` **99.4–99.7% carry no UTC offset**; `url` 100% absolute.

## ⛔ Two counts that are SUPERSEDED — kept only to date the correction

*Moved here from `memory/MEMORY.md` on 2026-08-17 (`/audit-context`); the index was
their only home, and an index entry is a hook, not a record.*

- **"FOUR validators" was an undercount**, by an instrument that could only see one
  shape. A behaviour sweep over all 20 repos found **21+** — and counting them was the
  wrong question anyway. The finding in its final form: **exactly TWO shape checks are
  both automatically invoked AND looking at real production bytes, and between them they
  assert eight key names and two strings' max length.**
- **"ovr reads 2 of 52" is retired.** The **2 stands**; the 52 was a single-run count
  ranging **27–107** across runs, so the derived 96% never had a denominator.
- **The two schemas over one stream overlap on ZERO metadata keys.** (2026-08-13,
  § *The contracts layer*.)

## ⚠️ Instrument traps — read before quoting any number above

1. **NexusMind's `validate_production_contract.py` counts ERRORS, not rows, and merges
   distinct `required` failures.** Groups key on `(path, validator)` (`:131`) and a
   missing-required error reports the **parent** path, so `word_count` and
   `priority` collapse into one group whose message is whichever arrived first
   (`:137`). 267×2 + 661×1 = **1,195**, which is what it prints.
   ⚠️ **CORRECTED 2026-08-14 — "affects `required` only" was too narrow.** The
   *counts* for `enum`/`maximum` are row counts (they key on leaf paths), **but the
   breakdown BY VALUE is destroyed the same way**: `(source_type, enum)` merges every
   violating value into one group carrying one example, so on a corpus with both
   `social` and `data` violations the report names **one of them**. Trust the totals;
   never trust the named example, for any validator. *(NexusMind, measured.)*
   **Fix built** on branch `fix/357-contract-validator-grouping` (`b8a191c`,
   NM#357) — keyed on the missing property via an anchored regex with an explicit
   fallback to the parent key, and reporting `"N error(s) on M row(s)"`. **Not
   merged; main has none of it.**
2. **`format` is declared and never asserted — and the obvious fix silently
   no-ops.** Contract A declares `format: "date-time"` on all three timestamp
   fields; RFC 3339 requires an offset, so 99.4% of rows violate a declaration it
   has always carried. `Draft7Validator(schema)` has no `format_checker` — and
   passing `FormatChecker()` changes nothing without `rfc3339-validator`
   installed: verified, `'not-a-date'` **passes either way**. Enabling it is a
   **two-part** change or you get a false green.
3. **`data/raw/*.jsonl` is mutated in place by NexusMind.** Not FluxusSource's
   output as emitted; the validator strips its own stamps first, and without that
   subtraction you get a false root `additionalProperties` violation on ~98%.
4. **Don't grep bare field names.** `domain`, `category`, `score`, `instance` are
   common words in code — a bare-name grep returned 98–417 false hits. Search the
   access pattern (`metadata["x"]`, `.get("x")`, `.x`). And beware **name
   collisions**: ovr has 49 `word_count` occurrences and **none** read the upstream
   field.
5. **`grep -rIl` returning nothing is a broken verify command** — pipeline-atlas's
   `run_verifies.sh` treats empty output as failure. Invert every "returns zero"
   figure to print its count.

## Rules this added

6. **Declare from the REACHABLE set, never wider than emitted.** Contract A's
   `email`/`web`/`patent` have never existed. A proposal here to declare
   `language` as **BCP 47** was withdrawn for the *same defect from the opposite
   direction* — it would admit `pt-BR`, the exact value the producer folds away
   because ovr dispatches translation on the bare code.
7. **Declaring is nearly free; a wrong declaration and a missing one are what
   cost.** *(Owner ruling.)* Do not cut a field for having no reader —
   `source_category` measured zero readers for months **because** it was
   undeclared, and two repos reverse-engineered it independently.
8. **Greenness is not evidence that a schema tracks reality.** Four
   demonstrations, which is a pattern: a producer schema green because it asks
   less; Contract B green *and* declaring `metadata` with zero properties; CI green
   on fixtures; and `format` declared but unasserted.

---

## ✅ CONTRACT A IS IMPLEMENTED (2026-08-15 evening → 08-16 morning)

**17 of 18 declared fields ride on delivered rows**, four consecutive deliveries, **0
validation errors against both schemas**, measured by this session and by FluxusSource
independently with identical results. Detail and the per-block counts:
`docs/TODO.md` and `docs/CONTRACTS_PLAN.md` § *Round 4*. The 18th,
`content_meta.error`, is correctly absent — it exists only on a derivation fault.

**Verify (the script is in-repo now, not a loose file on the box):**

```bash
ssh sadalsuud 'cd /home/jeroen/local_dev/FluxusSource && venv/bin/python -' \
  < scripts/contracts/contract_a_smoke.py
```

### ⭐⭐ THE GAP THE WHOLE CONTRACT COULD NOT SEE — and it is a documented class

**A row carrying ZERO Contract A blocks validates CLEAN.** Nothing in any block is
`required`, correctly, because absence is legitimate three different ways. Demonstrated in
the direction that can fail, which is the only direction worth demonstrating:

```
a row with no Contract A blocks at all        VALIDATES CLEAN
the same row + one undeclared key             REJECTED (additionalProperties)
```

**So a block that STOPPED being emitted was invisible — which is exactly what production
looked like for the week the contract was fully declared and the producer emitted none of
it.** This is a named failure mode in the data-quality literature (*"when all fields are
optional, validation cannot detect missing fields that should have been present"*), not a
local quirk.

Closed by two classes in NexusMind's check (their #382, merged `9cf2861`, deployed):
`emission.structural_block_absent` and `freshness.input_stale`.

### Rules this added

9. **A schema validates rows that EXIST. Coverage of what stopped existing is a
   different instrument.** The five-pillar framing names them: schema (Contract A),
   volume/completeness (`emission.*`), freshness (`freshness.*`), distribution
   (**we have nothing**), lineage (pipeline-atlas).
10. ⚠️ **ZERO-BECAUSE-NEVER ≠ ZERO-BECAUSE-STOPPED, and fusing them makes the check
    unusable.** The first emission implementation flagged any structural block at zero —
    which would have condemned FluxusSource on every cycle before 2026-08-15 and would
    condemn any new producer or a rollback. Judge against a baseline (the check's own
    previous artefact), carried forward so a regression keeps firing instead of being
    learned as the new normal after one cycle.
11. ⚠️ **FLAG ZERO, NEVER A LOW SHARE — and the industry default would have failed here.**
    GX Cloud's completeness detection flags *"10% deviation from the baseline average of
    the last five runs"*. On this corpus `origin` swung **12.2% → 38.8%** between two
    consecutive deliveries purely by which shelves were due. **A share moves with
    composition; zero on a structurally-total block cannot be produced by composition.**
    The live counter-example: the 08:10 delivery emitted **no** `charset_detected` at all
    because every body decoded as strict UTF-8 — a *healthy* cycle any floor would have
    reddened, and a check that cries wolf on healthy data is ignored on the run that
    matters.
12. **An unmeasurable population is NOT ASSERTED, never clean** — a delivery with no RSS
    rows says nothing about whether `content_meta` works. With a deliberate precedence: a
    **proven** absence outranks an unmeasurable one, so a delivery that both proves one
    block gone and cannot judge another still goes red.
13. **Measure the cadence, do not declare it.** `freshness` derives the delivery interval
    from the median gap over the last 8 collections (**14,452s live, against a real 4h
    cadence**) because both available constants are wrong: `period_seconds` is the
    *check's* schedule, and a hardcoded 4h is a number nobody maintains the day the
    collection timer changes. Judged at **3×** the median — a late run is not a defect.
14. ⚠️ **ABSENCE NOW MEANS THREE DIFFERENT THINGS and they must not be merged:**
    *not instrumented* (`published`, `collected`, `fetch`, `feed`), *not applicable*
    (`content_meta` — `source_type` sits beside it and determines it), *not yet filled*
    (`origin` — editorial data). **A consumer that merges them reads `origin`'s emitting
    subset as a sample of the corpus.**
15. **A per-row health field can only report what the row's own construction knew.**
    `content_meta.error` works because the producer *knows* it faulted. A generic
    `health: ok` field would be an anti-pattern: an always-ok field is indistinguishable
    from one nobody sets any more, and it dies by the same code path as the thing it
    reports on. ⚠️ Only `content_meta` records its fault today — a fault in the other four
    block builders **raises out of `to_dict`, so the ROW IS DROPPED, not degraded**
    (verified 2026-08-16), and a vanished row is attributable to nothing.

## The Article Record register (2026-08-25)

`NexusMind/docs/ARTICLE_RECORD_REGISTER.md` is **generated**, never hand-edited:

```
python3 scripts/stamp_census.py --cycles 12 --emit-register docs/ARTICLE_RECORD_REGISTER.md
```

It joins the census (population + consumers) to `docs/article_record_status.yaml`
(**109 fields classified**), deriving `scope` from the contracts by EXACT path and
referencing each field's semantics from a contract `description` where one exists
(70 of 109) rather than restating it.

⭐ **It is a control, not a document: a field observed on production rows and
classified nowhere exits 1.** The reverse — classified and not observed — is reported
only, because the census reads a WINDOW. Proven by three seeded mutations against the
real 12-cycle census (a deleted entry, an invalid `status`, a `record_path` the record
schema does not declare): all three caught.

⛔ **Two ghosts the old instrument could not report**, both found the day the register
was built: `_corroboration` and its three children are **declared in Contract B and on
0 of 164,572 rows** (the dict is popped at `scripts/main.py:2028`, deliberately), and a
nullable object's population used to be *the count of its own absence*.

<!-- verify: R=/home/jeroen/repos/veen-systems/NexusMind; if [ ! -d "$R" ]; then echo "CANNOT VERIFY: NexusMind repo not at that path"; elif [ ! -x "$R/venv/bin/python" ]; then echo "CANNOT VERIFY: no project venv at $R/venv"; elif "$R/venv/bin/python" -m pytest "$R/tests/unit/test_article_record_register.py" -q > /tmp/reg_probe.txt 2>&1; then tail -1 /tmp/reg_probe.txt; else tail -3 /tmp/reg_probe.txt; exit 1; fi -->
