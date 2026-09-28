# Per-lens harm flag rates above each op-point (#156 step 2) — 2026-09-28

`docs/TODO.md` numbered item 1. $0, no oracle, read-only on sadalsuud.

## What was measured

For each lens, the share of rows at or above **that lens's own op-point** whose
`_harm_is_subject_score` (harm detector v1, stamp-only) reaches a candidate threshold.

- **Population:** `NexusMind/data/filtered/<lens>/filtered_*.jsonl`, the last 12 files per lens
  (window 2026-09-26 ~09:24 → 2026-09-28 ~09:18, printed per lens in `harm_rates_12cycles.txt`),
  deduplicated by `id` within a lens.
- **Excludes** (a source's exclusions are part of it): source-type-excluded rows (`filtered_*.jsonl`
  never receives them), everything the commerce, obituary and **violence** gates dropped before
  persistence (violence has enforced since 2026-08-23), and rows scored `stage1_low` — 0 of those
  reached an op-point in this window. It is the scored-and-persisted population, **not** the
  reader population (`getArticlesForBuild`), so dedup and enrichment losses downstream are not in it.
- **Op-points:** `filters/<lens>/v<N>/normalization.json` `stats.raw_min` = the runtime
  `TIER_THRESHOLDS` cut: uplifting v7 4.5, human_thriving v9 4.5, solutions v6 2.25, belonging v1 4.0,
  nature_recovery v4 3.75, cultural_discovery v5 4.0006. Compared on `raw_weighted_average`
  (ADR-022: visibility = raw ≥ op-point).
- **Stamp presence:** 98.0–100% of op-point rows per lens. `stamp_census.py` on the whole filtered
  population: 99.28% of 195,901 rows (`--cycles 12`) and 100.00% of 43,092 (`--cycles 2`), after
  61.17% (2026-09-21) and 85.29% (2026-09-22) — the third read the TODO asked for; it has plateaued.

## Result (harm ≥ 0.5; Wilson 95%; full sweep in `harm_rates_12cycles.txt`)

| lens | rows ≥ op | flagged ≥ 0.5 | rate [95% CI] |
|---|---|---|---|
| belonging v1 | 1,176 | 128 | **10.9%** [9.2, 12.8] |
| human_thriving v9 | 235 | 18 | 7.7% [4.9, 11.8] |
| uplifting v7 | 2,496 | 143 | 5.7% [4.9, 6.7] |
| nature_recovery v4 | 38 | 2 | 5.3% [1.5, 17.3] |
| solutions v6 | 1,153 | 22 | **1.9%** [1.3, 2.9] |
| cultural_discovery v5 | 589 | 7 | 1.2% [0.6, 2.4] |

**Prediction written before the run:** Thriving lenses 3–10% (the v7/v8 panel gave 4.4% at 0.5),
solutions and nature_recovery **higher**, 10–25%; belonging and cd 3–15%. ⛔ **Solutions was
predicted highest and is second-lowest**; belonging is highest. Uplifting landed inside its range.

## What this does NOT establish

- **A flag rate is not a harm rate.** The detector was trained on `human_thriving v8` scoped labels
  (`calibration_report.json`: *"says nothing about solutions, belonging, nature_recovery or
  cultural_discovery"*). Its precision on those four lenses is **unmeasured**, and it is structurally
  blind to what it misses.
- **Title read, not labels** (`harm_titles_ge07_sample.txt`, 12 random rows ≥ 0.7 per lens, seed 0),
  my reading: uplifting's flags look mostly harm-dominated (court verdicts, "terrorists
  neutralised", expulsions); belonging's are mixed — some harm-dominated (Gaza strike, a funeral
  mix-up, quake survivors), some plausibly constitutive (Stolperstein remembrance); solutions'
  flags are **responses** to harm (police, legal aid), consistent with the ADR's "no cap, ever"
  argument for Solutions. Nobody labelled these.
- **nature_recovery: n = 38** — the CI spans 1.5–17.3%; no decision can rest on it.
- Two days of production; one window. `human_thriving` and `uplifting` share articles.

## Reproduce

```bash
scp harm_rates.py harm_titles.py sadalsuud:/tmp/
ssh sadalsuud 'python3 /tmp/harm_rates.py 12'
ssh sadalsuud 'python3 /tmp/harm_titles.py uplifting human_thriving solutions belonging nature_recovery cultural_discovery'
```

The window moves every cycle; re-running gives a later window, not these numbers.
