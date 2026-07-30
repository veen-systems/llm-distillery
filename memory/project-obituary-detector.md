---
name: project-obituary-detector
description: Obituary detector v3 status, NM#185 handoff, v4 corrective retrain plan
metadata:
  type: project
---

## Status

**v5@0.92 SHADOW swap committed 2026-07-30 evening (owner: "do it all") —
NexusMind `89f3c58`, CI green, auto-deploys next pipeline cycle (~20:00; verify
same way as the v4 deploy: health lists `obituary_detector_v5`, log "Obituary
detector v5 loaded successfully", stamps `_obituary_model: "v5"`).** Vendored
v5 pkl+sha256 into NexusMind, updated EXPECTED_HASHES + all 9 swap literals
(deploy-risk review map). Threshold 0.92.

**June-increment panel MEASURED (2026-07-30, 40/65 v5-new flags, 4-model):
29 obit / 6 unanimous-not / 5 split → maj-prec 0.725, strict 0.829; at deployed
0.92: 0.714/0.806; at 0.95: 0.684 — THRESHOLD-INSENSITIVE (all 6 over-blocks
score ≥0.92).** v4's marginal band was 0.946. Enforcement stays blocked:
the fix is owner adjudication (`adjudication_worksheet_2026-07-30.md`, 14 rows,
awaiting owner verdicts) feeding a v6 with owner-authoritative labels on the
crime/accident-death + memorial/tribute boundary. Grades:
`grades_panel_v5_june_increment_2026-07-30.jsonl` (d332edc).

**b650 (Arian's box) ONLINE 2026-07-30: RTX 3090 Ti 24GB, CUDA 12.0, account
`jeroen` (not jwasys), sudo pw in owner's Bitwarden, Ollama at
100.87.225.76:11434 (qwen3:14b pulled). uv venv at ~/llm-distillery/venv
(system python3.12-venv is broken — use `~/.local/bin/uv`); obituary corpora +
v3/v4/v5 models copied to ~/llm-distillery/filters/... — target box for the v6
retrain; ends Ollama-vs-training contention on gpu-server.**

Owner decisions (2026-07-30): keep v4@0.90 as interim shadow (superseded same
evening by the v5@0.92 swap on "do it all"); v5 retrain on gpu-server approved
and executed same day.

v5 = v4 corpus + the 21 panel-graded FN-delta hard positives (11,329 rows, 2,694
pos; seed `training/data/v5_train_seed.jsonl` on gpu-server, same train_v1.py
recipe). Results (heldout n=1529 after excluding the 33 panel-graded rows —
28 FN-delta + 5 FP5, labels suspect/moved to training; eval:
`validation/artifacts/v5_eval_2026-07-30.json`, script `validation/eval_v5.py`):

**3-reviewer battery 2026-07-30 (correctness/methodology/deploy-risk, all
findings below verified by hand before recording):** the original excl-33 table
was misleading — it deleted v4's own 5 FPs (hence its fake "precision 1.000")
and 12 panel-graded rows NOT in v5's training set, which are exactly where v5's
over-block signal lives (v5 flags 6/7 panel-REJECTED FN-delta rows + both
panel-confirmed-real FP5 rows). **Corrected table** (exclude only the 21
training rows + 3 v4-hard-negatives that sat unexcluded in heldout since
07-28, n=1538): v3@0.95 prec 0.979 / rec 0.728; v4@0.90 0.979 / 0.728;
**v5@0.90 0.964 / 0.749 (+7 TP, +4 FP)**; **v5@0.92 0.967 / 0.734** —
statistically marginal either way (in-corpus heldout also has ~15% near-dup
contamination vs training; June is the only clean holdout and is unlabeled).

- **v5@0.92 dominates 0.90**: fits the same 19/21 gate articles (misses are
  0.866/0.876, below both), catches Farouq (0.9546), one fewer heldout FP,
  12 fewer June flags. Propose 0.92.
- **Strongest v5 evidence** (reviewer-added): ovr.news 203 production
  borderlines — v5 flags only the known Bharathiraja TP at 0.90 (v3 flagged 4).
  No over-blocking on the production distribution; v4's legacy-tribute fix kept.
- Hard-negative regression: none (12 v4 hard negatives ≤0.4402); Farouq caught.
- **OPEN before ENFORCE sign-off** (shadow-deploy at 0.92 is low-risk anytime):
  (1) panel-grade ~40 of the 65 v5-new June flags — est. 17–20% are
  rule-violating over-blocks (health explainers, alive-person stories, TV
  schedule pieces); "June recall recovered" is partly precision lost, increment
  unmeasured; (2) owner adjudication of ~10 disputed labels — the 4-model panel
  drifts broader than the owner rule (memorial events / legal-process /
  legacy-tribute classes graded "obituary"; ≥2 of the 21 hard positives violate
  the KEEP clause, e.g. the Filip memorial festival) — circular since the same
  panel failed v4 and labeled v5's training rows; (3) v5's own new FPs (elephant
  obit 0.994, Einstein 0.989) are NOT oracle mislabels — earlier framing wrong.
- OOF sweeps are fold-seed-noisy ±5pt (v4b spans 0.61–0.71 rec@0.95 across
  seeds) — never compare OOF across versions; the 0.70→0.60 "drop" is mostly
  noise, real shift ≈2pt.
- Deploy prep for the eventual swap (from deploy-risk review): NexusMind
  `deploy/gpu-server/main.py` pins v4 pickle SHA256s (`EXPECTED_HASHES`,
  enforce-on, load in lifespan without try/except — stale hashes crash the
  WHOLE scorer). v5 hashes: mlp `6f271360d42a…`, scaler `16c79508a516…`. Swap
  blast radius: main.py + src/preprocessing/obituary.py + config/app.yaml
  (~9 literals). v5 pkls + .sha256 companions must be vendored into NexusMind's
  own repo first — deploy_filters.sh archives NexusMind HEAD, never reads
  llm-distillery. Until then gpu-server is the only v5 binary holder besides
  the workstation working tree.
- Reproducibility fixed post-review: `training/build_v5_seed.py` +
  `validation/artifacts/graded_ids_2026-07-30.json` committed.

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
