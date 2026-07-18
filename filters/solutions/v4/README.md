# Solutions v4 (renamed from sustainability_technology, ADR-012) — labeling designed, model NOT built

**Status (2026-07-18): oracle/prompt/prefilter designed + validated; no trained
model yet.** Calibration is done and the oracle is ratified (DeepSeek). The
training corpus is NOT built and NO model exists — see `DATA_SETUP_PLAN.md` for
the remaining pipeline. **Do not re-score the old corpora as-is** (see the pivot
below).

## What this is

v4 is the broadened **Solutions** lens. It keeps ST v3's LCSA spine but covers
governance and community solutions in addition to clean tech. Foresight v1's top
governance articles are the gap this version is meant to capture — see
[llm-distillery#43](https://github.com/ducroq/llm-distillery/issues/43). v4
replaces BOTH the old sustainability_technology-v3 and foresight-v1 scorers that
feed ovr.news's Solutions tab.

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
community_practice_strength, equity_access, economic_viability) plus the type tag.

## Engineer decisions (#43) — RATIFIED 2026-07-18

- **Fork 1 = C** — broaden v3 in place rather than redesign.
- **Oracle** = DeepSeek (both ADR-020 judges); thinner-but-cleaner tab accepted.
- **Fork 2 (combine ST v3 10.6K + foresight v1 3.5K and re-score as-is) —
  SUPERSEDED.** A diagnostic showed those corpora are ~85% `not_a_solution`
  under the Solutions lens (reproducible:
  `scripts/diagnostics/solutions_v4_corpus_noise_check.py`). Corpus sourcing
  moved to e5-seed screening → enriched corpus. See `DATA_SETUP_PLAN.md`.
- **Fork 3** — foresight v1 retires at v4 go-live (two repos + normalization).

## What's next → `DATA_SETUP_PLAN.md`

The remaining pipeline (all gated; no paid step until the pre-spend gate passes):
seed → per-type e5 screen → enriched corpus → **DeepSeek score (~$13–18, the one
paid step)** → prepare_data → train Gemma-3-1B student + e5 probe → calibration →
ground-truth gate (ADR-021) → runtime scorer → go-live (Hub + NexusMind + ovr +
normalization). The runtime `prefilter.py` (`SolutionsPreFilterV4`) is drafted;
wiring it into the NexusMind loader is a go-live step.

## Files in this directory (draft stage)

- `config.yaml` — dimension architecture, weights, gatekeeper, calibration batch spec
- `prompt-compressed.md` — v4 oracle prompt (Step-1 scope, Step-2 type tag, A/B/C soft caps, 7 dims); review-hardened over two rounds + 4 calibration fixes
- `prefilter.py` — `SolutionsPreFilterV4`, multilingual commerce-only pass-through (nr v4 template)
- `calibration_report.md` — oracle bake-off + the superseded-corpus pointer
- `DATA_SETUP_PLAN.md` — the corpus/model pipeline (source of truth for what's left)
- `README.md` — this file
- **Not present yet** (land during the pipeline): `model/`, `probe/`,
  `calibration.json`, `normalization.json`, `ground_truth_gate.json`,
  `base_scorer.py`, `inference*.py`, `training_metadata.json`.
