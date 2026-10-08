# Belonging held-out set 3: pre-registration (2026-10-08)

*Written and committed BEFORE the draw, before any oracle call and before any judging. Set 2 was spent by c2a's FAIL
(`../2026-10-08-belonging-candidate2-plan/PLAN.md` § 9). Owner 2026-10-08: gate **c2b** (`filters/belonging/v1_c2b`, trained at
`49d52a9`) on a fresh set 3, drawn NOW from the wider production database ("why wait? we have a big database?").*

## Same as set 2 (`../2026-10-08-belonging-heldout2/PREREGISTRATION.md`), verbatim

Rubric v2.2 (sha `d450b79510418cf7`), the oracle scope prompt and Gemini settings, `judge_instructions_v2.md` (plus the one-line
repo-root note used in set 2), Claude Opus 5.5 judges, two blind passes; Gemini and judges read the text cut at 4,000 chars, while the gate
scores full text; bands on v1's PRODUCTION raw (`hi` ≥ 5.6, `mid` 4.0–5.6, `near` 2.5–4.0); **800 per band**; **100 sampled
Gemini-outs per band**; **the binding pass rule v2 unchanged**, with `K_MIN = ceil(31/44 × N_POS)`; the judge-statistics
**tripwire instead of an owner spot-check**: agreement in [0.90, 0.97] and hi both-in rate among Gemini-ins in [0.29, 0.48].

## What changes

- **Source.** Set 2 found only 378 unused `hi` rows in the retained `data/filtered/belonging/` window (harvest r1 and sets 1–2
  took the rest). Set 3 also draws from NexusMind's monthly archives `nexusmind_2026-08` and `nexusmind_2026-09`
  `belonging/scored.jsonl`, measured on sadalsuud 2026-10-08:
  - August: 510,834 rows: 316,810 stage2, 80,814 stage1_low, and 113,210 with NO `stage_used`. Rows without the stamp are out
    of the population, because the draw keeps `stage2` rows only.
  - September archive: 174,748 rows, covering 09-01 to ~09-12.
  - Every archived stage-2 row is stamped `version 1.0` (belonging v1, the live model), with percentile normalization.
  - Unused `hi` stage-2 rows: ~3,500 in August plus September's before exclusion (pool printed by the draw).
- **Window:** 2026-08-01 .. 2026-10-08, wider and older than sets 1–2 (09-04/09-10 .. 10-03/10-08). That is a different
  population in time, stated here, not corrected for. Archives are read FIRST, so their copy of a row wins the dedup.
- **Seeds:** draw 20261020, out-sample 20261021, judge shuffles 51/52, bootstrap 20261022.
- **Exclusions:** everything set 2 excluded, plus set 2's 2,400 drawn ids (a `belonging_exclusions` source). After the draw, set 3
  becomes a source too. Training twins found by gate3's own overlap check against c2b's manifest are dropped before any
  oracle call (as set 2's Amendment 1).

## Known before looking

- Only c2b is scored on set 3. One shot.
- Set 2 measured c2a's specificity as clearly better than v1 (CI [+0.003, +0.031]) and its recall as short (43/63). c2b is the same
  recipe without the 121 single-person negatives. It was expected to trade a little specificity for recall, which is a guess, not a measurement.
- The gate measures no volume. c2b flags 25 vs v1's 109 on the 5,000-row draw. Any switch is the owner's call beyond the gate.

## Predictions (Claude's, before the draw)

Positives 55–80; deciding negatives 300–360; hi Gemini-in rate 0.14–0.24.

## Result

*(filled after the judges; N_POS is then written into gate3.py, before c2b is scored)*
