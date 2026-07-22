# Session 2026-07-21 — Solutions v4 TRAINED + CALIBRATED + GATED (deploy decision pending)

**Branch:** `solutions-v4-calibration`. **Spend: $0** (no oracle calls; GPU only).
**State: model exists, through the ADR-021 gate. Deploy decision deferred to next session.**

## What happened (train → calibrate → gate, + two package gaps the build left)

Resumed from the train boundary. GPU synced/verified, trained, then hit two gaps the corpus-build
had left, fixed both, gated the model, and interpreted a recall shortfall.

**Train (gpu-server, ~68 min, $0):** Gemma-3-1B+LoRA, 3 epochs, head-tail 256+256, no sample-weight
(train mix 31.5% positive — not a needle). Val MAE **0.564** (steady 0.73→0.64→0.56, train/val gap
~0.07, no overfit). train.py/model_loading byte-identical to this branch (verified before training).
GPU scheduling: had to dodge the **FluxusSource 4h cron chain** (collection→nexusmind scoring→ollama
summarize), which drives the live scorer on the same 16GB GPU — killed a first launch, trained in the
idle window after the cycle's ollama summarize finished.

**Gap 1 — Step-8 runtime scorer never written.** Calibration failed with
`ModuleNotFoundError: filters.solutions.v4.inference`. The package was "train-ready" but had NO
`base_scorer.py` / `inference.py` / package `__init__.py` — workflow Step 8 ("write inference code")
was skipped between train (Step 7) and calibrate (Step 9). Wrote them copy-from-`nature_recovery v4`:
`BaseSolutionsScorer` (7 dims, weights from config sum 1.0, gatekeeper solution_concreteness 3.0/3.0,
tiers high_solution 7 / medium_high 5 / medium 3 / low 0) + `SolutionsScorer` (local LoRA). Constants
verified against config; construct-tested end-to-end (demo article scored sensibly, differentiated).

**Calibrate (ADR-008):** per-dim isotonic on val, evaluated on test. Marginal (+0.3% on test — model
already well-fit to DeepSeek). `calibration.json` written, `score_scale_factor 1.6093`. Top band
unreachable (calibrated max ~6.2 < high 7.0, §5 expected).

**Gap 2 — `ground_truth_gate.py` was nature_recovery-hardcoded.** Its `label_wa()`/WEIGHTS/DIMS/
gatekeeper were nr's 6 dims + `recovery_evidence` cap 3.5. Solutions was the 2nd filter through the
gate → **generalized it to read dims/weights/gatekeeper from `--config`** (completes the pattern it
already used for the threshold). Kept nr constants as defaults; **nr behavior provably unchanged**
(8/8 unit tests pass + a `load_scoring_spec(nr_config) == nr defaults` regression check). Added
`--gatekeeper-cap` sweep + `--recompute-model-wa`.

**Gate (ADR-021, 1,500 unscreened holdout, oracle=DeepSeek, op 3.0):**
recall **0.45** / prec **0.78** / spec 0.99 / F1 0.57 / Spearman 0.46. 111 positives → 50 tp, 61 fn,
14 fp. Scored the holdout `--no-prefilter` (pure model-vs-oracle on all 1500).

**Findings:**
- **Gatekeeper cap 3.0 ≡ 2.9** (byte-identical gate) → the demote-vs-exclude boundary I flagged is
  **inert** on this distribution → keep config-faithful 3.0. (Decision resolved by data.)
- **Recall ceiling ~0.58 is STRUCTURAL, not an op-point knob.** Sweep: best F1 ~2.25 (recall 0.56,
  prec 0.77). But of 61 misses, **52 scored <2.5** by the model (clear disagreement, not near-the-bar),
  spanning all bands incl. **13 clear high-band (oracle 4.5+)**. Root cause: the training corpus was
  e5-*screened* (the flat-gradient lens) → the model learned the screenable manifold; unscreened
  production solutions outside it are missed. This is the documented **access-bias limitation**
  (`docs/ideas/access-bias-and-the-haystack.md`) → a v2 item (external source expansion + AL on these
  misses), NOT fixable by op-point or a quick retrain.

## Committed this session
- `filters/solutions/v4/`: `__init__.py`×2, `base_scorer.py`, `inference.py`, `calibration.json`,
  `ground_truth_gate.json`, `training_metadata.json`, `training_history.json`, updated `config.yaml`
  (score_scale_factor), README (results). `model/` gitignored (gpu-server + local backup).
- `scripts/gate/ground_truth_gate.py` — generalized filter-agnostic (nr-safe).
- CLAUDE.md solutions row + date; DATA_SETUP_PLAN Round 5.

## NEXT SESSION — deploy decision + deploy
1. **Compare gate metrics to other deployed filters** (nature_recovery 0.65/0.85, belonging, cd v5…) —
   context for whether recall 0.45–0.56 is shippable for a flagship tab.
2. **Op-point decision:** 2.25 (recall 0.56, looser) vs 3.0 (recall 0.45, stricter) vs hold-for-v2.
3. If deploy: set op-point (`config.yaml` tiers + `TIER_THRESHOLDS`) → `inference_hub.py` (Step-8
   remainder) → normalization from **production-base-rate** rescore (NOT enriched) → Hub → NexusMind
   wire-in (`SolutionsPreFilterV4`) → retire foresight (NexusMind app.yaml + ovr filters.ts) →
   deploy checklist (FILTER_PLAYBOOK §8) → ADR-020 PROVISIONAL→Accepted.

## Still-open follow-ups (carried, not done)
- Upstream the OFF_LENS source-exclusion mask into `scripts/screening/embedding_screener.py`
  (still an ephemeral gpu-server scratch screener).
- File the NexusMind `ArticleFetcher.should_replace_content` consent-guard bug.
- **Ollama summarization model A/B — DONE** (ran end of session). Result:
  `docs/ideas/summarization-model-bakeoff-2026-07-21.md` (untracked → commit/move to ovr.news).
  Faithful gen (real `getBrandVoicePrompt`, 6 non-EN feed articles) + blinded in-session 3-judge
  panel (Opus/Sonnet/Fable, no API key). **`gpt-oss:20b` = 9.2× the offloaded 27b, ~0.5 quality
  behind, fully on-GPU → pragmatic swap; `qwen3:14b` OUT (unanimous Chinese-script leak); 27b =
  quality ceiling.** An ovr.news `ollamaConfig.model` decision. Re-run if `summaryMaxWords` changes.
  The 5.8GB VRAM "phantom" was student jobs (now gone); 27b still offloads ~20% (19-20GB > 16GB).
