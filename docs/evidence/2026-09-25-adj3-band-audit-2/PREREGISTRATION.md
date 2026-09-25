# adj3 band audit, RE-RUN — junk share per cut-off in [3.5, ∞), written BEFORE any article is judged

**2026-09-25.** The first run (`../2026-09-25-adj3-band-audit/`) failed its drift check (0.844 < 0.90)
and was not used. The owner then ruled on its unruled categories (`docs/decisions/2026-09-25-thriving-scope-rulings.md`:
4 sport results OUT unless more; 5 paywalled teasers OUT) and approved this re-run. Design is the
assistant's proposal. A MEASUREMENT for the owner to choose a cut-off from, not a gate.

## Changes from the first run, and why
1. **Fresh sample** (seed 20260927); every id in the first run's panel is excluded from the draw.
2. **The ≥ 4.5 stratum is re-sampled and re-judged** (40 rows) under the new rulings, so every point
   on the curve comes from one judging regime. The live audit's ≥ 4.5 estimate is NOT reused.
3. **Pass B is 40%** (was 20%): the first run's 32-row check could not tell 0.84 from 0.90 reliably.
4. **Six known-answer controls**: the pilot's 4, plus `balkan_klix_ba_80ffeaedf1e5` (veterans' judo
   medal, owner OUT → tests ruling 4) and `gn_africa_gn_tunisia_633f3342afd4` (headline-only item,
   owner OUT → tests ruling 5). Both excluded from the draw. **Pass A must return 6/6 or STOP.**
5. **Owner check shows the article text in translation**, not a one-line summary (the first run's
   #12 was a summary that left out a material fact).
6. `cannot_judge` is now only for broken text / not an article; a short teaser is `out_of_scope` (ruling 5).

## Population and strata (audit population of the live audit, 123,374 ids; adj3 calibrated scores)
| stratum | N | drawn |
|---|---|---|
| ≥ 4.5 | 826 | 40 |
| [4.25, 4.5) | 182 | 40 |
| [4.0, 4.25) | 197 | 40 |
| [3.75, 4.0) | 245 | 40 |
| [3.5, 3.75) | 313 | 40 |
N counts the whole stratum; the draw excludes first-run panel ids and the two new controls.

## Stops (unchanged in kind)
Controls 6/6 · drift A-vs-B ≥ 0.90 on the 40% (A/B split → not in scope) · owner check ≥ 18/20, else
withheld until ruled.

## Reported
For c ∈ {4.5, 4.25, 4.0, 3.75, 3.5}: junk(c) = Σ_{strata ≥ c} N_s·j_s / Σ N_s, per-cycle volume N/42,
95% bootstrap CI (within-stratum resampling, 10,000 draws, seed 20260927). **Guardrail:** a cut whose
CI upper bound reaches v8's live-audit point estimate (0.338) is reported "not shown to be better than
v8" and will not be recommended. ⚠️ v8's 0.338 was judged under the OLD rulings; with sport and
teasers now OUT it would likely be higher, so this guardrail is if anything conservative.
