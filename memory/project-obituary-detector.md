---
name: project-obituary-detector
description: Obituary detector v3 status, NM#185 handoff, v4 corrective retrain plan
metadata:
  type: project
---

## Status

**v4@0.90 swap committed (NexusMind `02da4fe`, pushed 2026-07-30); production ran v3@0.95 at wrap-up.** No manual deploy needed: `nexusmind.service` ExecStartPre `deploy_filters.sh` auto-pulls on the next cycle (commit touches `deploy/gpu-server/main.py`, which IS in `SCORER_PATHS` — the RUNBOOK §durability note claiming main.py doesn't auto-propagate is stale) and ships scorer + config atomically, so the mixed v3@0.90 regime can't occur via the timer. **Never `git pull` on sadalsuud without `deploy_filters.sh`** — that WOULD create v3@0.90 stamps. Next session step 1: VERIFY the auto-deploy landed — `curl gpu-server:8000/health` lists `obituary_detector_v4`; rescore Farouq article → 0.937, flagged at 0.90.

**Owner gate before enforcement (2026-07-30):** quantify the FN delta — which articles does v4@0.90 miss that v3@0.95 caught (~20 on heldout, recall 0.744 vs 0.683)? Panel-grade them; if they're real obituaries of the class the owner flags, consider v5 or a lower op-point. See LD#83 comments.

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

LD#51 (train v3) ✅ → LD#77 (ovr.news validation) ✅ → NM#185 (NexusMind shadow deploy) ✅ deployed 2026-07-27 → **v4 corrective retrain** ✅ trained 2026-07-28 → **v4 shadow replace + enforce** ← NEXT (after ≥1 production cycle of shadow accumulation) → ovr#204 (ovr removes hardcoded filter)

## v4 corrective retrain (EXECUTED 2026-07-28)

12 hard negatives added to training (11,295 → 11,308 rows):
- 8 ovr.news production FPs (legacy/tribute pieces in Greek/Spanish/Chinese)
- 4 heldout panel-confirmed FPs (crime/accident reports)

**Results at threshold 0.95:**
- All 12 FPs score <0.65 (max 0.65, most <0.15)
- Heldout precision: **0.977** (v3: 0.973), FP count: **5** (v3: 7)
- Heldout recall: **0.608** (v3: 0.744) — tradeoff from added conservatism, not a concern for shadow mode
- Bharathiraja TP: **0.954** (v3: 0.913) — stronger

Artifacts: `filters/common/obituary_detector/v4/models/` (mlp_classifier.pkl + scaler.pkl). Same architecture, drop-in replacement for v3.

### Old v4 plan (pre-execution, kept for reference)

(Superseded — executed 2026-07-28, see above.)

## Production flag 2026-07-29 (v3 TP, v4 MISS at 0.95)

Owner flagged `arabic_thearabweekly_d056412bf8cf` ("Farouq Hilal, the last guardian of Iraq's musical taste") via ovr.news flag API — a memorial for a recently deceased person, i.e. a true obituary per the labeling rule.

- **v3: 0.977** → caught (shadow stamped `_is_obituary: True`; reached the site only because shadow mode doesn't drop)
- **v4: 0.937** → **below the 0.95 op-point — v4 would MISS it.** The recall tradeoff (0.744→0.608) biting on a real production case. (Verify: rescore the gitignored worksheet below with v3+v4 models on gpu-server — same embed+scale+predict_proba as `validation/score_borderlines.py`.)
- v4 OOF sweep (`v4/calibration_report.json`, threshold_sweep) says 0.90 threshold ≈ v3-level recall (0.749) at precision 0.916 (vs 0.927 at 0.95) — and 0.90 catches this article. But the OOF numbers are oracle-label-based; the heldout check at 0.90 came next (see Resolution below).

**Resolution (2026-07-30): v4 promoted at op-point 0.90.** Evidence:

- Heldout sweep (1,562 rows; verify: `ssh gpu-server "wc -l ~/llm-distillery/filters/common/obituary_detector/training/data/heldout_corpus.jsonl"`): v4's 5 FPs at 0.90 are the *identical set* as at 0.95 (all score ≥0.95) — the threshold drop costs zero heldout FPs and recovers recall 0.608 → 0.683. v4@0.90 beats v3@0.95 on precision (0.979 vs 0.973) at −6pt recall. Caveat: heldout labels are DeepSeek-oracle, and the 5 surviving FPs were never independently panel-checked (the panel budget went to the new 0.90–0.95 band).
- 4-model blind panel on the June-holdout marginal band [0.90, 0.95), n=37: **35/37 majority-obituary** (band precision ≈0.946). 1 FP (crime-report class), 1 split. phi4:14b dropped out mid-run (ollama down — pipeline had started on gpu-server); 3-lab majority for most rows.
- Artifacts: `validation/artifacts/v4_oppoint_check_2026-07-30.json`, `grades_panel_v4_band_2026-07-30.jsonl`. Farouq article (gitignored): `validation/artifacts/worksheet_ovrnews_flagged_2026-07-29_farouq.jsonl`.

NexusMind `02da4fe`: v3→v4 swap + threshold 0.90, still SHADOW, committed+pushed but not deployed (see Status). Sequence: deploy → smoke test → one shadow cycle → FN-delta check (owner gate, see Status) → owner sign-off → enforce → ovr#204.

The issue's original "FN just wastes 5ms" framing was wrong — an FN is an obituary on the site (that's what the owner keeps flagging); recall is the product metric, FP-precision is the safety constraint.

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
