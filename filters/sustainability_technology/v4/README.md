# Sustainability Technology v4 — CALIBRATED, AWAITING RE-SCORE SIGN-OFF

**Status: calibration batch COMPLETE (2026-07-17).** 350 articles scored by
DeepSeek + Gemini (ADR-020 method), disagreement set judged, criteria
evaluated — see `calibration_report.md` for results and the open engineer
decisions. Do NOT score the full corpus until those decisions are made
(oracle ratification, tab-volume acceptance, gate rewrite).

## What this is

v4 is the broadened Solutions lens design. It keeps ST v3's LCSA spine
but covers governance and community solutions in addition to clean tech.
Foresight v1's top governance articles are the gap this version is meant
to capture — see [llm-distillery#43](https://github.com/ducroq/llm-distillery/issues/43).

## What changed from v3

| Dimension change | v3 | v4 |
|---|---|---|
| **Gatekeeper shape** | `technology_readiness_level` (TRL) — tech-only | `solution_concreteness` — universal across tech/governance/community |
| **NEW** governance dim | n/a | `governance_intervention_strength` (0.15) — scores 0 for pure tech |
| **NEW** community dim | n/a | `community_practice_strength` (0.10) — scores 0 for pure tech/policy |
| **Renamed/broadened** | `life_cycle_environmental_impact` (0.30) | `systemic_impact` (0.20) — covers tech LC + governance reach + community replicability |
| **Slimmed** | `economic_competitiveness` (0.20) | `economic_viability` (0.10) — kept for investment-DD use case |
| **Added pre-step** | (implicit) | Step-1 scope check (`is this an article about a solution?`) before per-dim scoring |
| **Added pre-step** | (implicit) | Step-2 type tag (tech / governance / community / hybrid) |

Total weight: 1.00. Seven scored dimensions (solution_concreteness,
systemic_impact, evidence_strength, governance_intervention_strength,
community_practice_strength, equity_access, economic_viability) plus the
type tag.

## Decisions inherited from #43 sign-off

- **Fork 1 = C** — broaden v3 in place rather than redesign from scratch
- **Fork 2** — combine ST v3 (10.6K) + foresight v1 (3.5K) corpora and
  re-score with v4 prompt after the calibration batch
- **Fork 3** — foresight v1 stays parked through v4 calibration; retire
  on v4 production deploy

## Next step

~~Run the calibration batch~~ **DONE 2026-07-17** — 350 articles (as-run
composition in `config.yaml :: calibration_batch`), both oracles, $1.00.
Results, criteria tally, judge verdicts, and DeepSeek recommendation:
`calibration_report.md`. Prompt is `prompt-compressed.md` (the form
`batch_scorer.load_filter_package()` prefers; no separate `prompt-full.md`,
matching cd v5's single-prompt shape); review-hardened over two rounds.

Next: engineer decides the 4 open items in `calibration_report.md`; then
apply the small prompt/pipeline fixes listed there and re-score the combined
ST v3 (10.6K) + foresight v1 (3.5K) corpora with DeepSeek off-peak (~$10-15),
then proceed to training.

## Files in this directory at draft stage

- `config.yaml` — dimension architecture, weights, gatekeeper, calibration batch spec
- `prompt-compressed.md` — v4 oracle prompt (drafted 2026-07-17; encodes the
  Step-1 scope check, Step-2 type tag, A/B/C soft caps, and all 7 dims)
- `README.md` — this file
- (no model, no calibration.json yet — those land after the calibration
  batch decides direction)
