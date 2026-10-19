# Oracle canary rollout (#177, EXP-053): result, 2026-10-19

**Answer: all four canaries ship at k = 1.** cultural_discovery v5, nature_recovery v4 and solutions v6 (DeepSeek,
`score_deepseek_production.py`) and belonging v3 (Gemini, `ground_truth.batch_scorer`) each met the pre-registered
rule (`PREREGISTRATION.md`, written before any oracle call): every "score one point lower" run P1–P3 FAILED as a
k = 1 canary, and the first live canary L1 PASSED. Baselines: `config/canary/<filter>.baseline.json`. Every figure
below except the spend is in `result.txt`, recomputed from the lab copies by `analyse.py` (which also asserts that the
lab runs reproduce each committed baseline); the spend sums the scorer logs' `Estimated cost:` lines. Data: lab
`experiments/2026-10-19-oracle-canary-rollout/` (cited in this directory's `MANIFEST.json`).

## Measured (`result.txt`)

| filter | op | noise F1 / S1 | k = 1 FAIL bar | P1 / P2 / P3 (flips, shift) | P failed on | L1 |
|---|---|---|---|---|---|---|
| cultural_discovery | 4.0 | 5 / 0.0787 | flips > 6 or \|shift\| > 0.2287 | 8 −0.750 · 11 −0.765 · 11 −0.768 | flips + shift | PASS, 1 flip, −0.0044 |
| nature_recovery | 3.75 | 3 / 0.0313 | flips > 4 or \|shift\| > 0.1813 | 8 −0.449 · 8 −0.475 · 6 −0.463 | flips + shift | PASS, 1 flip, −0.0182 |
| solutions | 2.25 | 11 / 0.0730 | flips > 12 or \|shift\| > 0.2230 | 8 −0.241 · 9 −0.236 · 3 −0.311 | **shift only** | PASS, 6 flips, −0.0634 |
| belonging | 4.0 | 3 / 0.0467 | flips > 4 or \|shift\| > 0.1967 | 3 −0.279 · 5 −0.353 · 3 −0.285 | shift (P2 also flips) | PASS, 2 flips, −0.0179 |

All 36 B/P runs (9 per filter; L1 is the tenth) scored 100/100 items; every B run of a filter carries one prompt digest and one served model
(`deepseek-flash` for the three DeepSeek filters, `gemini-2.5-flash` for belonging).

**Gate proof** (`proof-<filter>.txt`), per filter, after L1: one labelling run was ADMITTED and its label stamped
with the PASS record; a second run on the same PASS was REFUSED ("already used"); the OTHER scorer with the same
prompt was REFUSED ("guarded for oracle …, no canary covers it"). So the outcome changed on the path a labelling
run takes, not only in the predicate.

## Against the predictions

- **F1 in 2–8:** hit for cd (5), nr (3), belonging (3); **missed for solutions (11).** "Higher for solutions and for
  cultural_discovery": right for solutions (at op 2.25, 15 of 100 baseline items sit within 0.5 of the op-point),
  missed for cd (5, the same as EXP-052's human_thriving).
- **P shift −0.4 to −0.6:** hit for nr only. cd overshot (−0.75); solutions (−0.24 to −0.31) and belonging (−0.28
  to −0.35) undershot. All FAILED anyway.
- **L1 PASS for all four:** hit.
- **Gemini 2.5 access** (TODO 4b): works — belonging's 10 runs were served `gemini-2.5-flash`.

## What it does NOT show

- **solutions' detection margin is thin, and belonging's is next.** solutions' P runs failed on shift alone, the
  closest by 0.013 (P2 −0.2356 vs the 0.2230 bar), and its flip bar (> 12) is wider than any P run's flips: a drift
  that moves its mean by less than 0.223, 0.85 of what the simulated one did (P triple −0.2625), would PASS.
  belonging's smallest P shift is 1.42 × its bar, and its flip channel missed P1 and P3 (3 flips vs > 4): only 3 of
  its 100 baseline items sit within 0.5 of the op. (cd 3.28 ×, nr 2.47 ×.) k = 3 would not change much (solutions'
  bar 0.2063); the bar is set by the rule, which this rollout does not revise.
- **The noise bar holds minutes of variance, not hours or days.** Each DeepSeek filter's B and P runs all ran
  inside 10:00–10:05Z, and L1 a few minutes later: L1 is a run the bar was not built from, but not a later hour or
  day (EXP-052 was the same). Read the first FAILs over the coming days as a possible bar problem before calling them
  drift.
- **The false-alarm rate at k = 1 is barely measured**: one out-of-sample clean run (L1) per filter, no C arm
  (pre-registered). solutions' L1 used 6 of its 12 allowed flips.
- **The P prompt simulates one kind of drift** (a uniform downward push). A drift that moves some dimensions up
  and others down, or only items far from the op-point, is untested.
- **A PASS covers one oracle key.** Scaleway's DeepSeek (`2026-10-19-scaleway-oracle-trial/`) or any model alias
  change is a different key and needs its own baseline.

## Spend (scorer estimates, not billing)

DeepSeek: 33 scorer invocations (27 runs + 3 resume passes + 3 L1) at an estimated $2.47 off-peak in total, plus 3
one-article proof runs. Inside the pre-registered $1.05–$3. Gemini (belonging): not re-estimated; batch_scorer
prints no cost.
