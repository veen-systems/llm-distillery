---
name: project-obituary-detector
description: Obituary detector v3 status, NM#185 handoff, v4 corrective retrain plan
metadata:
  type: project
---

## Status

**v5 TRAINED + EVALUATED 2026-07-30 (afternoon session) — awaiting owner op-point
sign-off, then deploy to shadow.** Owner decisions (2026-07-30): keep v4@0.90 as
interim shadow; v5 retrain on gpu-server approved and executed same day.

v5 = v4 corpus + the 21 panel-graded FN-delta hard positives (11,329 rows, 2,694
pos; seed `training/data/v5_train_seed.jsonl` on gpu-server, same train_v1.py
recipe). Results (heldout n=1529 after excluding the 33 panel-graded rows —
28 FN-delta + 5 FP5, labels suspect/moved to training; eval:
`validation/artifacts/v5_eval_2026-07-30.json`, script `validation/eval_v5.py`):

- **v5@0.90: precision 0.983 / recall 0.750** (4 FPs: elephant obit, Einstein
  historical, Comédie Française tribute, dead-diplomat report — last two look
  like oracle mislabels again). v5@0.92: 0.987 / 0.734. Compare v3@0.95:
  0.987 / 0.722; v4@0.90: 1.000 / 0.744 *on this subset, which omits v4's 21
  confirmed misses* — on the gate set itself v5 fits 19/21 at ≥0.90 (2 near
  misses at 0.866 / 0.876), v4 caught 0/21.
- **Farouq: v5 = 0.9546** (v4 0.9372, v3 0.9768) — caught at 0.90, even at 0.95.
- **No hard-negative regression**: all 12 v4 hard negatives ≤ 0.44 under v5;
  Bharathiraja TP strengthened to 0.976.
- **June (unlabeled) flag volume**: v5@0.90 flags 432/1870 ≈ v3@0.95's 427
  (v4@0.90: 377) — recall recovered to v3 level. v5-new flags are dominated by
  recent-death/crime-death pieces (the class v4 overcorrected on).
- Proposed op-point: **0.90** (0.92 if the owner wants the extra precision at
  −1.6pt recall). Next: owner sign-off → shadow deploy v5 (NexusMind swap, same
  path as v4) → shadow cycle → enforce → ovr#204.

**v4@0.90 shadow DEPLOYED + VERIFIED 2026-07-30 12:08 cycle** (auto-pull clean
fast-forward to c5f1df2; scorer logs "Obituary detector v4 loaded successfully";
health lists `obituary_detector_v4`; Farouq rescores **0.9372 → flagged** via the
deployed endpoint). `_obituary_model` version stamp + hoisted `has_model` guard
shipped in NexusMind `3f5c328` (next cycle).

**OWNER GATE FAILED (2026-07-30): enforcement sign-off BLOCKED, v5 retrain needed.**
FN-delta panel (4-model blind, n=28 gap articles v3@0.95 catches / v4@0.90 misses):
**21/28 majority-obituary** (12 unanimous), 5 split, 2 not. Five confirmed misses
score <0.70 on v4 — unrecoverable by threshold; the v4 hard-negative set
overcorrected on the crime/accident-death class (which the sharpened-broad rule
BLOCKS when death is the main subject). FP5 counter-check: only 2/5 of v4's
heldout FPs are real (3 are oracle mislabels incl. "Bardot funeral hoax") — v4
true precision > measured 0.979. Evidence: `validation/artifacts/
rollup_fn_delta_fp5_2026-07-30.json` + grades files (aaef1d0); LD#83 comment.

**v5 retrain direction:** add the 21 panel-confirmed FN-delta articles as hard
POSITIVES (ready-made, panel-graded) to balance v4's 12 hard negatives.
**Open owner decision:** interim shadow = keep v4@0.90 (Farouq class + ovr-FP fix,
stamps attributable via `_obituary_model`) vs revert to v3@0.95 (better recall,
21 real obits, near-equal precision). Asked in LD#83 comment 2026-07-30.

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
