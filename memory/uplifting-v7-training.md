---
name: uplifting-v7-training
description: Uplifting v7 training history. V7 IS deployed on Hub (hybrid inference added 2026-04) and serves the Thriving tab; thriving v1 was attempted as successor but PARKED (ADR-015).
type: project
---

# Uplifting v7 (current Thriving-tab filter)

## Status: Deployed to NexusMind (local file copy — v7 has NO HF Hub repo, no inference_hub.py). Hybrid inference added 2026-04. Serves the ovr.news Thriving tab. Thriving v1 was the intended successor but is PARKED indefinitely per ADR-015. **CLAUDE.md currently says "Deployed (HF Hub, private)" which is wrong for v7 — see audit 2026-04-19.** <!-- verify: ssh -o BatchMode=yes -o ConnectTimeout=10 gpu-server 'test -f ~/NexusMind/filters/uplifting/v7/model/adapter_model.safetensors && echo PASS || echo FAIL' 2>/dev/null || echo ERROR -->
<!-- 2026-07-17: verify command rewritten — the old one probed C:/local_dev (Windows workstation, stale) and the LOCAL clone's model/, which is gitignored and absent on this Linux machine. The deployment claim is about gpu-server, so probe gpu-server; ERROR here means no SSH route from this workstation, not a false claim. NB: v7 weights are NO_HUB and absent from both local repos on this machine — the only copies are gpu-server + the old Windows box. -->

The sections below are kept as training-run history — useful when re-training or comparing future successors, but no longer the current production status.

## Training complete

- **Best epoch**: 6/6, val MAE **0.787** (clamp-to-1.0 targets)
- **Calibration**: fitted but hurts on test (raw 0.811 → calibrated 0.841)
- **HIGH tier detection broken**: oracle finds 11 HIGH on test, calibrated model finds only 2
- Model files at `filters/uplifting/v7/model/` (local)
- `calibration.json` saved but calibration is overfitting val set

## Training history (all on gpu-server)

| Run | MAE | Notes |
|-----|-----|-------|
| Unclamped, 3 epochs | 0.96 | Bimodal zero-inflated distribution |
| Clamp 0→1.0, 6 epochs | 0.78 | Best so far |
| Round to integers, 6 epochs | 0.91 | Coarser targets hurt |
| Clamp 0→1.0, 6 epochs (final) | **0.787** | Completed |

## Root cause of high MAE vs v6 (0.67)

- V7 prompt (ADR-010) produces bimodal scores: 30-43% zeros per dimension (v6 had 0-9%)
- V7 has only 15-17 discrete score values per dimension (v6 had 250+ continuous floats from multi-run averaging)
- V7 has less training data: 5,271 vs 8,396
- Clamping zeros to 1.0 helped (0.96 → 0.78) but not enough

## Evolution to thriving v1 (2026-03-18)

Rather than patching v7, created thriving v1:
- Renamed from uplifting → thriving (ADR-012)
- Removed social_cohesion_impact (overlaps Belonging's community_fabric)
- 5 dimensions: human_wellbeing (0.40), justice_rights (0.25), evidence (0.10), distribution (0.10), durability (0.15)
- Filter dir: `filters/thriving/v1/`
- Oracle averaging script: `scripts/oracle/average_oracle_runs.py`
- Next: 3-run oracle scoring with 5-dim prompt → average → train → deploy
- Can't reuse v7 oracle data (dimensions changed)

## Previous plan: multi-run oracle averaging (now applied via thriving v1)

**Why:** V6's 250+ continuous float values came from averaging multiple oracle runs. V7's 15-17 discrete integers are much harder for the student to learn. This is the biggest lever.

**How to apply (via thriving v1):**
1. Score all articles 3x with thriving v1 prompt (~$18)
2. Average 3 runs → continuous targets, fewer zeros
3. Train on smoothed data
4. Calibrate and deploy

## Data locations

- Oracle scored: `datasets/scored/uplifting/` + `datasets/scored/uplifting_enrichment/uplifting/`
- Combined: `datasets/scored/uplifting_v7_combined/all_scored.jsonl`
- Splits: `datasets/training/uplifting_v7/` (5,271 train / 659 val / 660 test)
- Training data: `train.jsonl` / `val.jsonl` / `test.jsonl` (clamp-to-1.0), `*_original.jsonl` (unclamped backups)
- GPU server log: `~/llm-distillery/training_uplifting_v7_final.log`

## Code changes made

1. `filters/uplifting/v7/base_scorer.py` — new, v7-specific constants (updated weights from ADR-010)
2. `filters/uplifting/v7/inference.py` — new, local inference pipeline
3. `filters/uplifting/v7/calibration.json` — fitted (but overfitting, may discard)
4. `ground_truth/batch_scorer.py` — added `filter_version` + `prompt_hash` to scoring metadata
5. `filters/common/filter_base_scorer.py` — added `scoring_metadata()` method + `_compute_prompt_hash()`
6. GitHub issues created (previous session): NexusMind #103, ovr.news #115
