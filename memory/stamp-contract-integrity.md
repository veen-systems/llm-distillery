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
`tests/unit/test_contracts.py` validates `tests/fixtures/`. First run against
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
against op-points of 2.25 (solutions) and 4.0 (the rest), so
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
| 1 | `deploy/gpu-server/main.py` — `FilterScoreResult` (Pydantic) | server |
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
