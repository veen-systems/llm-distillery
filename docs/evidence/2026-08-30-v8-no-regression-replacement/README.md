# Replacing the ADR-015 lens-overlap row in the no-regression set

**Date:** 2026-08-30 · **Spend:** $0 (read-only scans of production output; no oracle call) ·
**Ruling:** `docs/decisions/2026-08-30-v8-phase-b-rulings.md` §2 · **Registry:** `EXP-006`

The Rwanda–EU row failed its own `raw > 4.5` assertion under **every** prompt including the
deployed v7 (1.600 / 0.817 / 0.817), and a delta conversion fails too at **−0.783**. It was
dropped. This is how its replacement was found.

## Population, and what it excludes

`~/local_dev/NexusMind/data/filtered/{lens}/filtered_*.jsonl` on **sadalsuud**, five lenses,
window **`filtered_20260816_124523` .. `filtered_20260830_090728`, 83 cycle files**, enumerated
at scan time.

⚠️ **The archive rolls.** The window is part of the source: a scan next week is a different
population. Both scans print the window.

⛔ **What this population excludes, stated because a number's exclusions are part of it:**
`filtered_*.jsonl` is written under an `if result["passed_prefilter"]:` guard, so it is **100%
passers by construction** and also drops source-type-excluded rows
(`memory/nexusmind-data-sources.md`). That is fine here — a guard row must be one production
actually scored and surfaced — but no *rate* may be computed against it.

⛔ **Every score is conditioned on `stage_used == "stage2"` before it is read.** A `stage1_low`
row's `raw_weighted_average` is an **e5 probe estimate**, not a Gemma score. Counts of the rows
skipped for this reason are printed per lens (`scan_overlap.out.txt`), and they are large — for
`solutions`, 155,221 non-stage-2 rows against 79,555 distinct stage-2 ids.

## Scan 1 — cross-lens overlap (`scan_overlap.py` → `scan_overlap.out.txt`)

Distinct stage-2 ids per lens in the window: uplifting **207,994**, nature_recovery **191,780**,
belonging **186,370**, cultural_discovery **104,409**, solutions **79,555**.

Uplifting stage-2 rows at or above its **4.5** op-point (#102): **16,324**.

Overlap with each other lens, each measured against **that lens's own op-point** — the only
comparison ADR-015 licenses, since raw scores across filters are not the same construct (#96):

| also above its own op-point | op-point | articles |
|---|---|---|
| nature_recovery | 3.75 | **266** |
| solutions | 2.25 | **5,574** |
| cultural_discovery | 4.0 | **1,227** |

## Scan 2 — reproducible without the enricher (`scan_overlap_native_text.py`)

Restricted to rows whose **producer** text already clears the 300-char oracle floor, read off
`original_content_length` + `pre_enriched` (the fields `CLAUDE.md` names for historical length).
uplifting ∩ nature_recovery falls to **21**; uplifting ∩ solutions to **308**.

This is what eliminated Die Presse's *"18.736 Haushalten in Österreich bleibt die Delogierung
erspart"* (uplifting **6.352**, solutions **5.805**) — the sharpest available test of the
money-committed boundary, since it reports money **spent** with **42,291** counted beneficiaries
rather than money mobilised. Its **producer text is 149 chars**; the 2,033 it was scored on are
enrichment, so the row cannot be re-derived from producer bytes.

## Scan 3 — the non-Latin hole (`scan_non_latin_overlap.py`)

Script test on the **glyphs**, not the language tag (a tag is a declaration).

Non-Latin uplifting positives with native text ≥1,000 chars, in the whole window: **27**.
Cross-lens overlaps among them: **5** with solutions, **2** with cultural_discovery, **0** with
nature_recovery — and **every one of the 7 comes from a single source, `china_sciencenet_cn`**.
Margins over the op-point run **+1.09 to +1.80**.

⛔ **Not used to pick a row.** The best-scoring non-Latin candidates are science-institution
stories, the shape #107's narrowed Thriving predicate excludes. Adding a thin-margin guard row is
how the Rwanda–EU row happened. Filed as **#141** instead.

## The two rows adopted

`candidate_detail.py` → `candidate_detail.out.txt` (all five lenses, dimension vectors, flags).

| | row | lang | native ch | uplifting v7 raw | margin | also above its own op-point |
|---|---|---|---|---|---|---|
| A | Fast Company, *"London's Ultra Low Emission Zone cleaned up the city's air. Then children's lungs got bigger"* | en | 5,780 | **6.6831** | +2.183 | solutions 5.0322, cultural_discovery 4.3914 |
| B | Welingelichte Kringen, Greek lignite closures → up to 42% fewer cardiac admissions | nl | 2,601 | **6.4740** | +1.974 | solutions 5.2795, nature_recovery 4.4969, cultural_discovery 4.9067 |

Both: `_is_obituary` / `_is_violence_promotion` / `_is_commerce` false, `content_quality.pass`
true, `stage_used: stage2` on every lens.

⚠️ They are **not** two renderings of one story — I assumed that at first and it is wrong. A is
London ULEZ and children's lung growth; B is West Macedonia's lignite closures and cardiac
admissions. Two independent studies of the same *shape*, which is why both were taken.

### Why margin matters here

+2.183 and +1.974 sit far outside every noise term that applies: the #95 batch band (**0.16**)
and the oracle decoder run-to-run floor (**0.436** mean / **0.687** max,
`2026-08-12-cd-v5-cross-oracle-arm-a.md`, `…-op-point-band-followup.md`). ⛔ A floor belongs to a
population and a mechanism — these are the two that apply to an oracle re-score of a fixed
article, and neither is the library-stack or device term.

### Why #107 did the eliminating

The Thriving lens is *a process going well **for people***, excluding **harm-answered-only** and
**institution-beneficiary**. Both adopted rows have people as the measured beneficiary — 3,400+
children's lung growth over five years (Lancet Public Health); ~200,000 residents' cardiac
admissions — and both tell the outcome, not the wrong.

⛔ This eliminated every pure-ecology candidate despite strong uplifting v7 scores: the Rwandan
Grey Crowned Crane census (uplifting 6.282 / nature_recovery 6.738), Nexo Jornal's monkey-corridor
bridges (6.575 / 5.339), Xataka's oyster-shell reef restoration (6.769 / solutions 5.326).
**Selecting on v7's scoring behaviour rather than on the predicate v8 is being trained to is the
same error the Unifesp row made** — asserting an absolute band from a different prompt's score.

## Disjointness from training — checked, then enforced

Against `b650-gpu:~/v8_corpus/`: both rows **absent** from `corpus_v8_final.jsonl` (**6,590**)
and `recall_cohort_final.jsonl` (**600**), **present** in `pool_v2.jsonl` (**177,593**). Same
population as training, disjoint from it.

⛔⛔ **That was luck, not enforcement.** `draw_v8_corpus.py` had no exclusion for the
acceptance-test rows; the first draw came out disjoint only because all three rows then in the
set had aged out of the window, so the pool **could not** contain them — a negative carrying no
information. The two new rows **are** in the pool, in design cell `pos_clear|latin|-`, inclusion
probability **0.0794**.

Now removed before stratification, with the draw refusing to run on a missing or empty set.
Proven against the real pool, not a predicate:

```
no-regression set: 4 ids declared, 2 removed from the pool (2 not in this window)
corpus.jsonl: 6590 rows, guard ids present: []
"no_regression_ids_declared": 4, "no_regression_rows_removed": 2
```

Controls, exit status captured **directly** rather than through a pipe (`| tail; echo $?`
reports `tail`'s status — shipped twice in this repo):

| control | result |
|---|---|
| `--no-regression-set /does/not/exist.jsonl` | `FATAL: no-regression set not found…`, **exit 1** |
| set present but empty | `FATAL: … holds no rows…`, **exit 1** |
| either refusal | no output directory created |

Six tests in `tests/unit/test_draw_v8_corpus.py::NoRegressionExclusionTest`, each seeding its own
positive. Three mutations, all killed, mutator asserting it applied: dropping the pool filter
(2 failures), returning empty instead of raising on a missing set (1), and reporting the
*declared* count as the *removed* count (1).

## What this does not establish

- **Nothing about v8's behaviour on these rows.** They were selected on uplifting **v7**
  production scores. Their v8 baselines are established when Gate A next runs — that is what the
  assertions are for.
- **Whether the non-Latin concentration is a collection property or a scoring property.** Those
  need different fixes and this scan cannot separate them (#141).
- **Nothing about Google News rows**, which the corpus draw excludes.
