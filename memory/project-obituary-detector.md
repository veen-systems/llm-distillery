---
name: project-obituary-detector
description: Obituary detector v3 status, NM#185 handoff, v4 corrective retrain plan
metadata:
  type: project
---

## Status

v3 trained + validated. **NM#185 Phase 3 DEPLOYED 2026-07-27** — owner gate removed, shadow mode live (`_obituary_score` / `_is_obituary` stamps in harvest output, drops nothing). v4 corrective retrain next.

## What it is

Multilingual obituary/death-memorial classifier: frozen `paraphrase-multilingual-mpnet-base-v2` → StandardScaler → sklearn MLP(256,128) → predict_proba. Blocks obituaries upstream of lens scoring in NexusMind. Same architecture as commerce_prefilter v2.

## v3 key numbers

- **Training:** 11,295 rows (2,672 positive, 23.5%), DeepSeek oracle, sharpened-broad labeling rule
- **June holdout (temporally disjoint, leakage-free):** 0 FPs at ≥0.95 (0/58), precision 1.0 excl-split
- **Recommended op-point:** 0.95
- **Model artifacts:** gpu-server `~/llm-distillery/filters/common/obituary_detector/v3/models/` (mlp_classifier.pkl + scaler.pkl)

## ovr.news investigation (2026-07-27)

Scored 203 ovr.news Phase-1 borderlines with v3 MLP:
- **186/203 (91.6%) score <0.50** — model is confident these are NOT obituaries
- **3/203 (1.5%) at ≥0.95** — all false positives: historical legacy/tribute pieces in Greek/Spanish/Chinese
- **1/203 at ≥0.90** — Bharathiraja tribute (true positive, recent death June 2026)
- **Bottom line:** v3 generalizes well to ovr.news. The Phase-1 concern about over-blocking was driven by a different model (Claude screener), not the v3 MLP.

## Dependency chain

LD#51 (train v3) ✅ → LD#77 (ovr.news validation) ✅ → **NM#185 (NexusMind shadow deploy)** ✅ deployed 2026-07-27 → **v4 corrective retrain** ← NEXT → ovr#204 (ovr removes hardcoded filter)

## v4 corrective retrain plan (§4b pattern)

8 confirmed FPs from ovr.news investigation (3 at ≥0.95 + 5 at 0.70–0.90), all the same error class: historical legacy/tribute pieces in non-English. Add as hard negatives to training → retrain → re-validate. $0 oracle cost (labels from investigation). See `docs/FILTER_PLAYBOOK.md` §4b for the pattern.

**Why not do v4 before NM#185 (retrospective):** shadow mode is safe (scores only, no drops), the chain had been waiting since June 14, and v3 at 0.95 blocks only ~1.5% of production with 0 FPs on English content. Shipped v3 first — v4 retrains next.

## Validation harness

All scripts in `filters/common/obituary_detector/validation/`:
- `score_borderlines.py` — score articles with v3 MLP (needs gpu-server for sentence-transformers)
- `panel_obit.py` — 4-model blind panel (gemini + gemma3:27b + qwen3:14b + phi4:14b)
- `panel_audit_deepseek.py` — 3-lab Ollama audit of DeepSeek oracle
- `rollup_obit.py` — panel-majority vs model, block precision
- `relabel_deepseek.py` — DeepSeek oracle labeling (resumable)

Key artifacts in `validation/artifacts/`:
- `v3_june_validation.json` — temporally-disjoint June holdout (0 FPs)
- `v3_heldout_validation.json` — in-corpus heldout (3 FPs at ≥0.95)
- `worksheet_ovrnews_scored_2026-07-27.jsonl` — 203 ovr.news borderlines with v3 scores (gitignored, content)
- `ovrnews_phase1_borderlines_2026-07-16.jsonl` — 203 borderlines with Claude model_verdict
- `grades_panel_ovrnews_2026-07-21.jsonl` — Claude 3-model panel on 66 borderlines

## NM#185 handoff

What NexusMind needs:
1. Copy v3 model artifacts from gpu-server
2. Wire into prefilter pipeline (same pattern as commerce_prefilter v2)
3. Shadow-deploy: stamp `_obituary_score` / `_is_obituary`, log would-block, drop nothing
4. Run for ≥1 production cycle, collect flagged articles
5. Report back: how many flagged, any obvious FP patterns beyond the 3 we know about

The commerce_prefilter v2 integration is the template — same artifact contract (mlp_classifier.pkl + scaler.pkl), same inference pattern.

## Labeling rule (owner-endorsed 2026-06-14)

- **Block (obituary):** fresh obituaries / death notices / mourning pieces whose PRIMARY purpose is to mark a specific person's recent death.
- **Keep (not_obituary):** memorial events, anniversary/commemoration pieces, legacy tributes, laws/programs prompted by a death, profiles of the living, any story that merely mentions death.
