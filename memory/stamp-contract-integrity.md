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

## Unprompted findings from the first census run (15,118 rows)

- `stage_used`, `stage1_estimate` — assigned by a writer, on **no** row. This is
  **LD#88 item 1**, open.
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
