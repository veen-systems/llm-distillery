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

⛔ **SCOPE — what this file is NOT about (2026-08-29).** Everything here concerns the
**production article record**: stamps written by NexusMind onto a row that reaches a reader.
The **oracle labelling path** in this repo writes its own stamps onto
`datasets/scored/*.jsonl` — `scope_verdict`, `dominant_subject`, `content_type`,
`filter_version`, `analyzed_by`, `prompt_hash`, `prompt_file` — and **none of them is an
article-record field, none is in any Contract, and none reaches production.** Do not census
them with `NexusMind/scripts/stamp_census.py` (it reads article records) and do not add an oracle stamp to a
Contract because it looks like a stamp. Their integrity question is different and simpler:
*can this row be attributed to the prompt and model that produced it?* — which is why
`prompt_hash` exists (`scripts/score_deepseek_production.py`,
`ground_truth/batch_scorer.py`). ⚠️ `scripts/score_ollama_oracle.py` writes the two verdict
fields at the **record root** rather than inside the analysis field, and its #157 stamps
(`prompt_sha256`, `prompt_hash`; since 2026-10-16) sit there too — and the scorers hash the
prompt file differently (stripped vs raw), so never join across scorers on the hash. Read the
writer before joining outputs from two scorers.

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

**The first production run (2026-08-08: 908 violations, `image_confidence` a raw logit) and why fixtures could not catch it** — MOVED to [archive](archive/stamp-contract-integrity-archive.md) (2026-10-19); the rule is #8 below.

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

**A THIRD limit, found 2026-08-08 — check A false-positives on rare fields** (the `enriched` occurrence) — MOVED to [archive](archive/stamp-contract-integrity-archive.md) (2026-10-19).

**A rare-but-working field is indistinguishable from a never-written one at
small `--cycles`.** Before calling anything from check A dead, either raise
`--cycles` or find the writer's log line and match its count against the rows.
(The tally of the six fields check A flagged that day — MOVED to [archive](archive/stamp-contract-integrity-archive.md), 2026-10-19.)

## Unprompted findings from the first census run (15,118 rows, 2026-08-08) — MOVED to [archive](archive/stamp-contract-integrity-archive.md) (2026-10-19)

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

**My pass criterion was the wrong shape** (2026-08-08: a per-filter `stage1_low` share judged against an unattributed journal aggregate) — MOVED to [`archive/stamp-contract-integrity-archive.md`](archive/stamp-contract-integrity-archive.md) (2026-10-16).

## NM#300 (2026-08-08) — five allowlists in series — MOVED to [`archive/stamp-contract-integrity-archive.md`](archive/stamp-contract-integrity-archive.md) (2026-10-12)

The lesson that stays: **`absent` vs `null` localises a fault for free** — absent = nobody wrote the key, null = the last
hop wrote it after something upstream emptied it. Check `"k" not in d` separately from `d[k] is None`; a census that only
counts `is not None` throws it away. And patching a sender does nothing if the receiver's parser is also an allowlist.

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

# Contract A design rule (the 2026-08-14 REDIRECT notice above it — MOVED to [archive](archive/stamp-contract-integrity-archive.md), 2026-10-19)

**The design rule:** a field belongs in Contract A **iff** only the collector can know
it **and** it is destroyed if not recorded now. Today's contract fails both ways — it
stores derivable values (`word_count`, `reading_time_minutes`) and discards
irrecoverable ones (the publisher's stated timezone, the charset actually used, whether
a date was fabricated, whether a source was even asked).

**The seven exclusive+perishable categories, FluxusSource's answers, `clock_source`, the superseded triage list and the redesign blocker** — MOVED to [`archive/stamp-contract-integrity-archive.md`](archive/stamp-contract-integrity-archive.md) (2026-10-16). Historical: Contract A shipped 2026-08-16 (below); `clock_source` is live (`date-error-recency-boost-hypotheses.md`), `_get_tzinfos` is tracked there.

---

# The contracts layer (2026-08-13, five sessions in parallel)

**Plan: `docs/CONTRACTS_PLAN.md`; full round-1 review: `docs/CONTRACTS_PLAN-rounds-archive.md`. This section holds the
measurements and the traps.** Nothing was executed or committed in any repo.

## The finding (validators) · the 2026-08-13 single-run measurements · two SUPERSEDED counts — MOVED to [`archive/stamp-contract-integrity-archive.md`](archive/stamp-contract-integrity-archive.md) (2026-10-12)

What survives: exactly TWO shape checks are both automatically invoked AND look at real production bytes. ovr reads 2
metadata keys by name; consumer pipeline code reads 3 (`quality`, `og_image_url`, `priority`) — *by name*, not the only
keys that can break a consumer. ⛔ **Never derive a share from a single-run metadata key count** (27–107 per run, median
63.5) — quote counts with their window. Say **unscheduled**, never *never executed*.

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
   (NM#357 fix-branch status as of 2026-08-14 — MOVED to [archive](archive/stamp-contract-integrity-archive.md), 2026-10-19.)
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

(The 2026-08-16 delivery measurement — 17 of 18 fields, 0 errors — MOVED to [archive](archive/stamp-contract-integrity-archive.md), 2026-10-19; read a delivered row instead.)

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

(Why it went unseen for a week, and the literature name for the class — MOVED to [archive](archive/stamp-contract-integrity-archive.md), 2026-10-19.)

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
    (The live counter-example, the 08:10 `charset_detected` delivery — MOVED to [archive](archive/stamp-contract-integrity-archive.md), 2026-10-19.)
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

It joins the census (population + consumers) to NexusMind's `docs/article_record_status.yaml`
(**109 fields classified**), deriving `scope` from the contracts by EXACT path and
referencing each field's semantics from a contract `description` where one exists
(70 of 109) rather than restating it.

⭐ **It is a control, not a document: a field observed on production rows and
classified nowhere exits 1.** The reverse — classified and not observed — is reported
only, because the census reads a WINDOW. Proven by three seeded mutations against the
real 12-cycle census (a deleted entry, an invalid `status`, a `record_path` the record
schema does not declare): all three caught.

(The two ghosts found the day the register was built — MOVED to [archive](archive/stamp-contract-integrity-archive.md), 2026-10-19.)

### A ghost is a question — so the census now records the ANSWERS (2026-08-26)

(Why the answers are schema annotations, not prose — MOVED to [archive](archive/stamp-contract-integrity-archive.md), 2026-10-19.)

| annotation | means | check A prints |
|---|---|---|
| `x-intermediate: true` | built, consumed and popped inside one run — it can NEVER reach a row | excluded from ghosts, named once |
| `x-rare: true` | a live writer whose INPUT does not currently occur — it CAN appear at any time | `??` answered, with its description |

⭐ **They are handled differently on purpose.** An intermediate field leaves the
declared set. A rare one stays in it and is only re-labelled at report time, so the day
it fires nothing has to be un-suppressed. **An `x-rare` mark is only honest with a
FALSIFIER in the description** — the condition under which the field must start
appearing — and the census prints `NO DESCRIPTION` when it meets a mark without one,
because otherwise the annotation degrades into a way of silencing findings.

⚠️ **A mark covers its SUBTREE.** Applied to the parent only, `_corroboration` was
excluded while its three declared children went on printing as ghosts on 0 of 207,270
rows. Found by running the shipped script on production during the 08-26 verification,
not by review — the tests all passed. A rare descendant inherits its ancestor's
falsifier rather than printing bare.

⚠️ **`x-rare` speaks to the SCHEMA half of check A only.** The code half matches bare
key names scraped from the writers; suppressing those by leaf is the trap that let a
top-level ghost hide behind an identically-named lens field. Two instruments, two
matching rules, and an annotation on one is not evidence about the other.

**The first real answer — `source_unreliable`** (anti-correlated by policy, two repos upstream) — MOVED to [archive](archive/stamp-contract-integrity-archive.md) (2026-10-19).

⛔ **And the defect that answer surfaced is the transferable one.** The record schema's
`corroboration` section is `additionalProperties: false`, and the flag was declared in
neither that schema nor the dual-write's copied set — **the first row ever to carry it
would have been the first row to fail validation.** A field that only appears in an
emergency is the worst one to discover missing. Rule: **when you establish that a field
is rare rather than dead, check that its target still exists** — rarity is why nobody
ever exercised the path.

<!-- verify: R=/home/jeroen/repos/veen-systems/NexusMind; if [ ! -d "$R" ]; then echo "CANNOT VERIFY: NexusMind repo not at that path"; elif [ ! -x "$R/venv/bin/python" ]; then echo "CANNOT VERIFY: no project venv at $R/venv"; elif "$R/venv/bin/python" -m pytest "$R/tests/unit/test_article_record_register.py" -q > /tmp/reg_probe.txt 2>&1; then tail -1 /tmp/reg_probe.txt; else tail -3 /tmp/reg_probe.txt; exit 1; fi -->
