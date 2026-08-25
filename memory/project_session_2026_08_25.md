# 2026-08-25 — the register is populated, and the instrument found two ghosts on its way

No spend, no model, no filter. All code in **NexusMind** (`97677b3` … `651aa55`),
deployed to sadalsuud and outcome-verified. This repo carries the spec, the audit and
the evidence.

## What shipped

**`NexusMind/docs/ARTICLE_RECORD_REGISTER.md`** — generated, never hand-edited:

```
python3 scripts/stamp_census.py --cycles 12 --emit-register docs/ARTICLE_RECORD_REGISTER.md
```

It joins the measured half (a census of production rows) to the human half
(`docs/article_record_status.yaml`, **109 fields classified by hand**): population,
consumers, semantics, writer and migration target, one row per field.

- **`scope` is DERIVED from the contracts** (A / B / R / neither) and never hand-copied.
- **Semantics are referenced, not restated** — 70 of 109 render from a contract
  `description`; the 39 with none carry a `meaning:` in the YAML. **Zero fields render
  `-NO DEFINITION-`.**
- **It exits 1 on drift.** Observed-and-unclassified is an error; classified-and-not-
  observed is only reported, because the census reads a WINDOW.
- Window of the committed run: **72 files, 177,466 rows,
  `filtered_20260823_124537 .. filtered_20260825_131739`.**

**26 new tests** (18 register, 5 census, 3 CLI wiring); **1,457 pass** in the project
venv. 3 of the 5 census tests fail against the script they replace; the other 2 are
presence controls and pass on both sides by design.

## Two instrument defects fixed first — each produced a confidently wrong row

⭐ **F7 — check A could not see a top-level declaration, so a whole class of ghost was
invisible.** It read only `properties.nexus_mind_attributes.additionalProperties.properties`.
Reading every level found what the 08-23 audit predicted, on the first run:
**`_corroboration` + `.cluster_id` + `.other_sources` + `.total_sources`, declared in
Contract B, present on 0 of 164,572 rows.**

⛔ **RETRACTED, same session: that ghost is not one.** The declaration's own description
has always said *Intermediate field — consumed by `scripts/main.py` and re-emitted under
`source_quality` before JSONL write*, and that is exactly what happens
(`display_ranking._corroboration_boost` reads it in-process; `main.py:2028` pops it).
0 of 164,572 filtered rows **and** 0 of 3,000 block-ledger rows, **with an in-process
reader** — the shape of an intermediate, not of a corpse. ⭐ **The instrument could not
tell the two apart because the fact was in PROSE.** Contract B 1.18.0 → 1.18.1 marks it
`x-intermediate: true`; check A now excludes marked fields and prints them once. I wrote
"the declaration is the wrong half" in three documents before checking what the
declaration said. A second ghost, `source_quality.source_unreliable`, may be a rare field rather than
a dead one: it is written only when `source_tier == "override"` and credibility < 3.0.
**A ghost is a question, not a verdict.**

⭐ **F8 — a nullable object's population was the count of its own ABSENCE.** `flatten`
recorded a parent path only when the value was *not* a dict, so
`image_analysis.extracted_image_dimensions` read `NEVER-POPULATED (0 of 1,410)` while its
own `.height`/`.width` read 100%. **Nullable dicts were mis-reported by construction in
every census run before today.** Parents now record `<obj:N>`; constancy findings are
suppressed on those rows, because two objects of equal size are not equal objects.

## The zero was checked, not assumed

The clean run says *"every observed field is classified"*. Three mutations were seeded
into the status file and run against the same 12-cycle census — a deleted entry, an
invalid `status`, and a `record_path` the record schema does not declare — and **all
three were caught, exit 1**. A clean run that has never been shown to fail is not
evidence.

## Numbers this session moved

- ⚠️ **The undeclared set is 19, not the 20 this repo has been quoting.** The difference
  is `nexus_mind_attributes.*.scores.<dims>`: Contract B declares the `scores`
  *container*, and the per-dimension NAMES — what is really undeclared — are per-filter
  vocabulary the census collapses into one synthetic leaf. Both readings are defensible;
  the register states which one it used.
- ⛔ **109 owned fields of 260 observed is a 12-CYCLE WINDOW.** At 2 cycles the same
  script says 229 total. The register prints its window in its header.
- `nexusmind.*` reads `pres 57.88%` over the 12-cycle window **only because the window
  straddles the dual-write deploy**. Measured over the two most recent cycles (12 files,
  29,056 rows): **100.00%**. A presence figure spanning a deploy is a property of the
  window.

## Two of my own

1. ⭐ **A coverage predicate written for the ghost check, reused for attribution.**
   Prefix matching is right for "is this declared path observed" and wrong for "is this
   observed field declared" — and the wrong answer reported all 31 lens fields as
   declared, including the seven the register exists for. **2nd occurrence of *a check
   that answers a NARROWER question than the one asked, where the narrow answer is
   TRUE*.** Caught before shipping, by looking at the output rather than the code.
2. ⛔ **78 test failures explained away as "the environment"; it was `python3` instead of
   `venv/bin/python`.** 1,457 pass in the venv. **A dismissal is a claim and has to be
   tested as hard as the signal was.**

## Deploy note

The pull to sadalsuud was made while `nexusmind.service` read `activating`, deliberately
and with the premise checked: nothing under `src`, `scripts`, `deploy` or `filters`
imports `stamp_census` or `article_record_register` (one docstring mention in
`title_affinity.py`), and `scripts/main.py` is unchanged. **A rule whose premise you have
checked is a different thing from one you skipped.**

## Next session

1. **🅒 migration step 3** — free, no external reader: hoist the 13 lens fields measured
   identical on all 2,495 multi-lens articles. The register's `→ record` column is the map.
   ⚠️ Three more are invariant only because their VALUE is constant and must **not** move:
   `passed_prefilter`, `normalization_method`, `primary_literature_cap_would_apply`.
2. **`_corroboration`'s declaration** — Contract B declares a field nothing emits. The pop
   is deliberate, so the declaration is what should go; that is a Contract B bump.
3. **#123** the index-budget guard is still open; today's trim bought ~2.5k chars, not a fix.
