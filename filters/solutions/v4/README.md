# Solutions v4 (renamed from sustainability_technology, ADR-012) — TRAINED + GATED, deploy decision pending

**Status (2026-07-21): student trained, calibrated, and through the ADR-021
ground-truth gate. Deploy decision deferred to next session.** The model exists
(`model/`, gitignored; backed up on gpu-server + locally). Oracle is ratified
(DeepSeek). **Do not re-score the old corpora as-is** (see the pivot below).

## Training + gate results (2026-07-21)

- **Training:** Gemma-3-1B + LoRA, 3 epochs, head-tail 256+256, no sample-weighting
  (train mix 31.5% positive). Val MAE **0.564** (steady 0.73→0.64→0.56, no overfit).
- **Calibration:** per-dim isotonic on val (ADR-008); marginal effect (+0.3% on test —
  the model is already well-fit to DeepSeek). `calibration.json` committed. Calibration
  produced `score_scale_factor 1.6093`, but the deployed config sets it to **1.0** —
  cross-lens scaling is `normalization.json` (ADR-014); a non-1.0 fallback is the nr v2
  stale-inflation trap (#167/#205).
- **ADR-021 gate** (1,500-article *unscreened* holdout, oracle = DeepSeek, op-point 3.0):
  recall **0.45** / precision **0.78** / specificity 0.99 / F1 0.57 / Spearman 0.46
  (`ground_truth_gate.json`). Precision-strong, **recall-weak**.
- **Op-point frontier** (threshold sweep): best F1 at ~2.25 → recall 0.56 / precision 0.77.
- **Gatekeeper cap 3.0 vs 2.9 = identical** → the demote-vs-exclude boundary is **inert**
  on this distribution; cap stays config-faithful at 3.0.
- **Recall ceiling ~0.58 is structural, not an op-point knob:** of 61 missed positives, 52
  scored *below 2.5* by the model (clear disagreement, spans all bands incl. 13 clear
  high-band). Root cause = the training corpus was e5-*screened* (flat-gradient lens), so
  the model learned the screenable manifold; unscreened production solutions outside it get
  missed. This is the documented **access-bias limitation** → a v2 item (external source
  expansion + active-learning on these misses), NOT fixable by op-point or a quick retrain.

**Deploy decision (2026-07-22): DEPLOY at op-point 2.25.** Chosen over 3.0 (stricter,
recall 0.45) and hold-for-v2. Rationale: v4 replaces sustech v3 (tech-only) AND parked
foresight v1 (wrong lens — the Solutions tab is currently ~91% foresight-fed), so even a
recall-weak but high-precision (0.77) purpose-built Solutions scorer is a relevance
upgrade over the status quo; 2.25 buys +0.11 recall (0.45→0.56) at −0.01 precision. The
recall/Spearman weakness (Spearman 0.46 vs nature_recovery v4's 0.82) is the structural
access-bias limitation → the explicit solutions v2 mandate (external source expansion +
active learning on the misses), not a reason to keep running the worse status quo.
Comparison context: nature_recovery v4 gate = recall 0.65 / prec 0.85 / F1 0.74 /
Spearman 0.82 (op 3.75); nr v2 (prev deployed) = 0.58 / 0.61 / 0.60 / 0.80.

Config now reflects 2.25: `config.yaml scoring.tiers.medium.threshold` and
`base_scorer.py TIER_THRESHOLDS` both = 2.25; `filter.version` = "4.0";
`inference_hub.py` written (`SolutionsScorerHub`, Hub repo `jeergrvgreg/solutions-filter-v4`).
Gatekeeper cap stays 3.0 (near-inert; see `base_scorer.py` for why it's safe above the
op-point). **`ground_truth_gate.json` still records the op-3.0 evaluation — regenerate at
2.25 when the model is next loaded (Phase B).**

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

## What's next (deploy, next session)

Deferred to next session, pending the op-point decision above:
1. **Compare gate metrics to other deployed filters** (context for the recall call).
2. Set the op-point in `config.yaml` (`tiers.medium.threshold`) + `TIER_THRESHOLDS`.
3. `inference_hub.py` (Step-8 remainder, needed for Hub upload).
4. Normalization from a **production-base-rate** historical rescore (NOT the enriched
   corpus) — v4 replaces BOTH tab scorers, so it must ship with `normalization.json`.
5. Hub upload → NexusMind wire-in (`SolutionsPreFilterV4` loader) → retire foresight
   (NexusMind `app.yaml` + ovr `filters.ts`) → deploy checklist (FILTER_PLAYBOOK §8).
6. **v2 backlog:** external source expansion + active-learning on the recall misses
   (`docs/ideas/access-bias-and-the-haystack.md`); optional Stage-1 hybrid probe (held —
   flat e5 gradient makes it uncertain; decide by measuring probe FN@MEDIUM+).

## Files in this directory

- `config.yaml` — dimensions, weights, gatekeeper, tiers, `score_scale_factor` (calibrated)
- `prompt-compressed.md` — v4 oracle prompt (Step-1 scope, Step-2 type tag, A/B/C soft caps, 7 dims)
- `prefilter.py` — `SolutionsPreFilterV4`, multilingual commerce-only pass-through (nr v4 template)
- `base_scorer.py` — `BaseSolutionsScorer` (constants + prefilter binding; logic in `FilterBaseScorer`)
- `inference.py` — `SolutionsScorer` (local LoRA load)
- `calibration.json` — per-dim isotonic (ADR-008)
- `ground_truth_gate.json` — ADR-021 gate result (op-point **2.25**: recall 0.559 / prec 0.768 / F1 0.647)
- `inference_hub.py` — `SolutionsScorerHub` (Hub load; NexusMind production path)
- `normalization.json` — anchored-CDF cross-lens normalization (ADR-014), fit at deploy.
  **Provenance:** 40,000 random *non-commerce* raw production articles (sadalsuud
  `data/raw/content_items_*.jsonl`, seed 20260722) scored by solutions v4 →
  11,178 prefilter-passers → 536 at raw≥2.25 (the op-point). raw_min anchored to
  2.25; range 2.25–5.23; NOT the enriched corpus (production base-rate per §6).
- `training_metadata.json` / `training_history.json` — hyperparameters + per-epoch curves
- `model/` — LoRA adapter + tokenizer (gitignored; on gpu-server + local backup)
- `calibration_report.md` — oracle bake-off + the superseded-corpus pointer
- `DATA_SETUP_PLAN.md` — the corpus/model pipeline (source of truth for the build)
- **Not present yet**: hybrid Stage-1 probe (v2, held)
