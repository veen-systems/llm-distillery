# Cultural Discovery Filter v5

**Status:** Phase 3 Oracle Calibration in progress (2026-05-31). See `STATUS.md`.

**Purpose:** Detect new findings, insights, and connections about art, culture, and history that expand human understanding — *the past opening up*. Target deployment: ovr.news Discovery tab.

**Driver:** llm-distillery#62 — fix discovery-lens leakage in cd v4 production (institutional apologies, commemorations, and decline narratives were scoring too high).

---

## Quick Reference

| Aspect | Value |
|---|---|
| Filter name (in code) | `cultural_discovery` |
| Version | 5.0-draft |
| Dimensions | 5: discovery_novelty (25%), heritage_significance (20%), cross_cultural_connection (25%), human_resonance (15%), evidence_quality (15%) — sum 1.0 |
| Gatekeeper | evidence_quality < 3.0 → overall capped at 3.0 |
| Base student model | google/gemma-3-1b-pt + LoRA |
| Oracle (calibration in progress) | Gemini Flash 2.5 + DeepSeek V4 Flash + Qwen3:14b + Phi4:14b (multi-oracle, ADR-020 draft) |
| Production oracle (post-calibration) | TBD — leading: DeepSeek V4 Flash |

---

## v5 vs v4 — what changed

| Aspect | v4 (deployed) | v5 (in calibration) |
|---|---|---|
| Pre-classification flags A-E | max_score caps (political_conflict 3.0, tourism_fluff 2.0, etc.) | Same |
| Pre-classification flags F-K (NEW) | did not exist | **Soft penalties** (F=2.5, G=2.5, H=3.5, I=2.0, K=2.5) for historical_harm_reckoning, commemoration_memorial, perpetrator_biography, decline_loss, launch_announcement |
| Cap enforcement mechanism | Hard clamp | Soft penalty (subtract from each dim, floor 0) per ADR-015 (cliffs hurt MAE) |
| OUT-OF-SCOPE structure | Single list | Split into CATEGORY A (low-substance, cap) vs CATEGORY B (high-substance wrong-trajectory, penalty) with "may fit other lenses" framing |
| Calibration methodology | Single-oracle | **Multi-oracle batch (4) + agent judges (Opus+Haiku)** per ADR-020 draft |
| Lens framing | "Culture" → "Discovery" rename per ovr.news ADR-038 | Inherited from v4 |

---

## Filter Package Contents

| File | Status | Purpose |
|---|---|---|
| `config.yaml` | ✅ | Dimensions, weights, gatekeeper |
| `prompt-compressed.md` | ✅ | Oracle prompt (latest with F-K tightenings + A-E split) |
| `prefilter.py` | ❌ | Deleted 2026-10-01 with every per-lens prefilter (decision 0, NexusMind#284); it never ran in production |
| `STATUS.md` | ✅ | Phase-by-phase tracker — read this for current state |
| `DEEP_ROOTS.md` | ✅ | Philosophical/scientific grounding (Pinker/Rosling, trajectory principle) |
| `calibration_report.md` | 🟡 draft | Phase 3 formal artifact — fills in as multi-oracle data lands |
| `dimension_analysis/` | 🟡 partial | PCA + correlations + plots |
| `model/` | ⏳ | LoRA adapter (Phase 5) |
| `probe/` | ⏳ | e5 embedding probe (Phase 6c, hybrid inference) |
| `calibration.json` | ⏳ | Isotonic calibration (Phase 6a) |
| `normalization.json` | ⏳ | Production CDF normalization (Phase 6b) |
| `base_scorer.py`, `inference*.py` | ⏳ | Scorer Python (templated from v4 at Phase 5) |
| `training_history.json`, `training_metadata.json` | ⏳ | Training records (Phase 5) |

---

## How to Pick Up Where We Left Off

1. **Read `STATUS.md`** first — phase-by-phase tracker, last decision, next step
2. **Read `calibration_report.md`** for the formal calibration outcome (when finalized)
3. **Read `DEEP_ROOTS.md`** for "why this filter exists" context
4. **For oracle-level changes:** edit `prompt-compressed.md`, document in `config.yaml` changelog, re-run calibration
5. **For training:** see `docs/RUNBOOK.md` in repo root + `docs/agents/filter-development-guide.md` Phase 5+

---

## Open Architectural Questions

- ADR-020 (draft) — multi-oracle calibration methodology; under review, marked PROVISIONAL until validated on 2nd filter
- ovr.news Phase 3 lens-fit — not shipping near-term; v5 soft-penalty mechanism is designed to work without it (capped articles stay in candidate pool with demoted scores)
- Conservative-oracle principle for needle-filter penalty flags — user-confirmed preference, saved as memory

---

## Related

- `../v4/` — predecessor, currently deployed
- `../v3/calibration_report.md` — template/precedent for the calibration report convention
- `docs/adr/draft-020-extended-oracle-calibration.md` — methodology this filter is the worked example for
