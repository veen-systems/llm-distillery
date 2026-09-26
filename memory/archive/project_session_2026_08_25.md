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

## Afternoon — step 3 shipped, and an owner ruling paused a filter

### Migration step 3, the additive half (NexusMind `67b70e5`, `b26c384`) — DEPLOYED

`nexusmind.content` / `.signals` / `.corroboration` emitted beside `.run`/`.disposition`/
`.gates`. Lens copies untouched — dual-write, no reader changed. **Cost on 26,530
production rows: median +338 B, 6.09% of the median row, max +1,147 B.**

⛔ **The plan's premise was wrong by two fields: "13 lens-invariant" is 11.** Re-measured
over **4,838** multi-lens articles: `content_length` and `original_content_length` differ
on **4**, every one an article post-enriched mid-cycle. The 4 differing and the 4 enriched
are the **same 4**, 0 unexplained either way.

⛔ **`corroboration.other_sources` was declared as an array of STRING and never was one** —
every entry on disk is an object. Nothing emitted it, so nothing contradicted a declaration
written from the field's *name*. Schema 0.4.0 → 0.5.0.

⭐ **The rule the step established: THE DUAL-WRITE DUPLICATES SCALARS, NEVER PAYLOADS.**
Excluding `content.original` and `other_sources` took worst-case row growth 12,237 B →
1,147 B.

### ⛔ A RETRACTION, same session: `_corroboration` is not a dead declaration

The new top-level check reported it declared in Contract B and on 0 of 164,572 rows. I
wrote "the declaration is the wrong half" in **three documents** before opening the
declaration, which says *"Intermediate field — consumed by main.py and re-emitted under
source_quality before JSONL write."* It was right all along: 0 persisted rows **plus an
in-process reader** is an intermediate, not a corpse.

⭐⭐ **The keeper: a description is not a machine-readable fact.** Contract B 1.18.0 →
1.18.1 marks it `x-intermediate: true`; check A excludes marked fields and prints them
once. ⭐ **0 rows is a measurement; "dead" is a conclusion** — the gap between them held
the declaration's own words.

### The ordering effect — measured, then made moot by the pause

Pooled over 12 cycles / **31,596** multi-lens articles: **18 (0.057%)** carry a different
`content_length` per lens. Rare, but **perfectly systematic** — `solutions` got the short
text **18 of 18**, `uplifting` 17 of 18, the other four the full text 18 of 18. Median gap
**26×** (196 vs 4,559 chars). Cause: `enabled_filters` is an ORDERED list, and the lenses
at the front can never benefit from a later lens's fetch. Filed as evidence on NM#339/#331.

### ⭐ OWNER RULING — `investment_risk` PAUSED

Verbatim: *"aegis is dormant, nobody reads it - pause it"*. Evidence gathered **before**
the ruling: it was never an ovr.news lens (3 allow-list references, `validate.ts` calls it
*"an Aegis-only filter"*); its consumer chain was real but one-sided (export every cycle,
**251 daily archives since 2025-12-07**, published to a gist); **78.5% of its output landed
in `unclassified`** on the last run.

Applied: out of `pipeline.enabled_filters`, and `pipeline.aegis_export.enabled: false`
because that export aggregates only this filter. **PAUSED ≠ REMOVED** — package, HF Hub
repo, Contract C, archives all stay; un-pause is two config lines. Record:
`docs/decisions/2026-08-25-pause-investment-risk.md`.

⚠️ The gist FREEZES at today's file rather than disappearing. ⚠️ ovr.news's allow-list must
STAY (draining rows validate against it). ⚠️ `placements` drops 6 → 5. ⚠️ Every census over
`data/filtered/` keeps reporting six lenses for ~14 days — **history, not state**.

⭐ Predicted, not measured: the pause should take the ordering effect to ~zero, since
`investment_risk` was 51 of 70 post-scoring enrichments and ran third.

### ⛔ A third of my own: the watcher matched itself (5th occurrence)

A wait-loop `until ! ps -eo args | grep -q "[m]ain.py"` never exited. The bracket trick
protected the grep from itself — but the loop's own `echo "no main.py process running"`
put the literal pattern on its command line, so **the watcher matched itself and waited
forever**. It held the deploy ~20 minutes after the box had gone idle, and three polls
reported "a process" that was my own waiter. **The tell was in the output all along: the
matching line began `bash -c until`.** ⭐ **Print the matching line — a count cannot show
you that the match is you.**

### Deployed 2026-08-25 17:2x — sadalsuud at `c7af891`

Both changes landed in one pull, with the box verified `inactive` and the cleanup unit
`dead`. Config on the box reads 5 filters and `aegis_export: false`.

⏳ **Outcome proof is NOT in yet** — it needs the 20:03 cycle. Run
`python3 /tmp/verify_deploy_20260825.py` on the box (also in this repo's scratchpad
history). ⭐ **That verifier was proven in the FAILING direction first**: against the
pre-deploy state it exits 1 on all seven checks. Writing it that way caught a defect in
itself — it had defined "this cycle" as an exact timestamp match, but a cycle is a
**WINDOW** (today's spanned 17:10:29 → 17:17:46, one file per lens), so the first version
selected exactly one lens and would have reported the pause as having removed five filters.

## Next session

1. ⏳ **VERIFY THE DEPLOY** — first thing, after the 20:03 cycle:
   `python3 /tmp/verify_deploy_20260825.py` on sadalsuud. Expect 5 filters, no
   `investment_risk` in the newest cycle, `nexusmind.content/signals/corroboration` present
   AND populated, no Aegis export written. Then re-run the register (the 18 new paths are
   pre-classified, so it must still exit **0**).
2. **Re-run the ordering measurement** after a few paused cycles — the prediction that the
   pause takes it to zero is a prediction, not a result.
3. **Migration step 4** — the paid one: `nexus_mind_attributes` → `nexusmind.lenses` plus
   deleting the copies steps 1–3 created. Four ovr.news files and a Contract B bump. Its own
   session.
4. **#123** the index-budget guard is still open; today's trim bought ~1 entry, not a fix —
   and the live numbers are now in the issue.
