---
name: project_session_2026_07_28
description: Session 2026-07-28 — obituary v4 corrective retrain, violence_promotion v1 shadow-deploy, solutions v6 normalization fitted
metadata:
  type: project
---

# Session 2026-07-28

## Completed

### Obituary detector v4 corrective retrain (LD#77)
- 12 hard negatives added to training: 8 ovr.news production FPs (legacy/tribute pieces) + 4 heldout panel-confirmed FPs (crime/accident reports)
- All 12 resolved — max FP score 0.65 at threshold 0.95 (most <0.15)
- Heldout precision: 0.977 (v3: 0.973), FP count: 5 (v3: 7)
- Heldout recall: 0.608 (v3: 0.744) — acceptable tradeoff for prefilter
- Bharathiraja TP: 0.954 (v3: 0.913) — stronger
- Artifacts: `filters/common/obituary_detector/v4/` — same architecture, drop-in replacement
- Copied to NexusMind `filters/common/obituary_detector/v4/` — ready to swap
- **NOT yet enabled** — v3 still running in shadow. Wait for ≥1 production cycle

### Violence promotion v1 shadow-deploy (NM#274)
- Code + model artifacts already in NexusMind — just needed config flag enabled
- `config/app.yaml`: `violence_promotion.enabled: true`, threshold 0.95
- `_run_violence_promotion_prefilter()` already implemented in `main.py`
- Stamps `_is_violence_promotion` / `_violence_promotion_score`, drops nothing
- Smoke test passes: combat→0.997, recovery→0.035, weapons-as-progress→0.989, peace→0.000
- 1,957 training samples, OOF precision 0.936, recall 0.550
- NM#274 closed; GH #73 commented

### Solutions v6 normalization fitted
- 845 production articles at raw ≥ 2.25 (26× the 200 minimum)
- Percentile CDF anchored at op-point 2.25
- Raw range: 2.25-5.78 (compressed by design), maps to 0-10 normalized
- Deployed to llm-distillery + NexusMind + gpu-server
- Scorer restarted (needed explicit `start` — restart was canceled mid-run)
- 15/15 normalization invariant tests pass

### Housekeeping
- Closed GH #80 (commerce v2 rollback — resolved)
- Closed GH #43 (Broaden Solutions — executed as solutions v4/v6)
- Closed NM#274 (violence_promotion wiring done)
- Commented on GH #77 (obituary v4 complete)
- Commented on GH #73 (violence_promotion v1 deployed)

### Eyeball check: solutions v6 production quality
- Top-scoring articles are genuinely about solutions: policy changes, tech deployment, conservation programs, health interventions
- Nature_recovery overlap ~10% — acceptable (ADR-015)
- Score compression to 0-5.78 means `high_solution` tier unreachable pre-normalization
- Normalization (now deployed) will properly surface top articles

## Hypotheses written
- `memory/obituary-v4-hypotheses.md` — 6 confirmed/learned
- `memory/violence-promotion-v1-hypotheses.md` — 10 (4 confirmed, 4 open, 2 design decisions)

## Key decisions
- Obituary v4: wait for shadow accumulation before replacing v3 → enforce
- Violence v1: shadow-deploy first, panel-validate later, v2 retrain after more data
- Solutions normalization: proceed — 845 articles is sufficient

## Gotchas
- Solutions scores are nested in `nexus_mind_attributes.solutions.weighted_average` — not top-level
- gpu-server scorer restart canceled mid-run; needed explicit `systemctl start`
- `sentence_transformers` not available locally — smoke tests need gpu-server

## Next session
- Check obituary + violence shadow accumulation
- If enough data: panel-validate both detectors' top scorers
- LD#76 calibration audit (P0 umbrella for #74/#75/#72)
- LD#23 cd evidence_quality — needs model inference on val set for per-dim MAE
