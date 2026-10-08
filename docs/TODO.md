# LLM Distillery - TODO

## ▶️ START HERE — the ordered queue, as of 2026-10-08 (session close)

*A bare "continue" means this list, top down. Each line names the FIRST action.*

0. ▶ **BELONGING v1 → adj1 retrain: run the build, check it, train, gate** (tracked in #170, the belonging adj1 retrain). Plan `~/.claude/plans/splendid-purring-acorn.md`;
   session `memory/project_session_2026_10_07_commerce_gate_runner.md`; build `docs/evidence/2026-10-07-belonging-adj1-build/`
   (README = this build's FMEA status); gate `docs/evidence/2026-10-03-belonging-heldout/GATE.md` (+ `gate.py`).
   All owner rulings are in (2026-10-03 adjudication; 2026-10-07 full text everywhere, hard negatives = 121
   one-moment rows, ~800 production easy negatives at k=1). History before 2026-10-08: `docs/TODO-archive.md`.
   ▶ **Next, in order:**
   1. ✅ **Easy negatives: the 2 permanent failures DROPPED 2026-10-08** (deterministic, ~3.7 s per failure across the
      whole loop; reason in the build README § FM-L5). The build now passes coverage and refuses only at 1b.
      ⚠️ **Owner: check Google billing for 2026-10-07 ~20:00 → 10-08 08:19** — a `batch_scorer` bug (since fixed) retried them
      ~74k times overnight; whether failed calls were billed is unknown.
   1b/1c/2. ✅ **Ruled + built 2026-10-08:** 1b = (a) drop all 61 (pinned in `build_adj1.py`); 1c = train anyway, the gate
      judges. Build + validator exit 0; results in the build README § *Result* (FM-T1 still coupled as accepted; a
      NEW FM-D2 French skew among positives: read the gate FPs by language).
   ▶ **Owner 2026-10-08: no new data yet; train, CHECK, then gate.** Epochs = **6, keep best** (read
      `training_history.json` per epoch; if recall_medium saturates on the 29 val positives (#144), tell the owner before
      using the checkpoint). **New step 5b (before the one-shot gate):** score a few thousand UNLABELLED production rows
      (in neither training nor the held-out set) with the candidate and with live v1, and compare flag rate (raw ≥ 4.0) by
      length bin and by collector language. If the candidate flags far more long or French rows than v1 → buy long
      production negatives (~1,900 rows ≈ $6.70 est., k=1) and rebuild BEFORE gating. Otherwise → gate. **Leak rule (owner
      2026-10-08, fixed BEFORE looking):** leaked if, among >4k-char rows OR among French rows, the candidate's flag rate
      is ≥ 1.5× v1's AND the 95% bootstrap CI of the gap excludes 0. 1.5× is a judgement call, not a measured figure.
   3. **Stage the candidate** `filters/belonging/v1_adj1/` (untracked on b650, as `v8_adj3` was): copy v1's package, REWRITE every
      `filters.belonging.v1.` import to `v1_adj1` (v1's code loads `v1/model` otherwise; `gate.assert_loads_from` refuses it),
      copy `training_manifest.jsonl` in. rsync the build + language stamps + easy-neg files to b650 (gitignored data).
   4. **Train on b650** (RUNBOOK § *Train on GPU*): commit+push first (train.py refuses a dirty/unpushed tree); check
      `curl -s localhost:11434/api/ps` shows no `gemma3:27b`. Flags: `--epochs 6 --batch-size 8 --seed 42 --select-metric recall_medium
      --medium-threshold 4.0 --use-head-tail --head-tokens 256 --tail-tokens 256`. ⚠️ **Epochs are a choice to settle
      first:** v1 trained 3; the human_thriving adj retrains used 6 with checkpoint selection. recall_medium saturates on a
      thin val positive count (#144), so read `training_history.json` per epoch.
   5. **Fit calibration** on the candidate's val (`scripts/calibration/fit_calibration.py ... --no-config-update`).
   6. **Gate** (one shot): `gate.py score --package filters/belonging/v1_adj1 --order forward|reversed` on b650, then
      `gate.py evaluate --candidate filters/belonging/v1_adj1`. v1's full-text reference is already scored (`fe12a2f`).
      Exit 0 PASS / 1 FAIL / 2 REFUSED. Then plan phase 6 secondary (v1 test split under treatment) and phase 7 live audit.
   7. Open, not blocking: harvest round 2 (~$9.70 est.); FM-S1 judge strictness (re-judge the 92 held-out hi Gemini-ins in
      dense batches).
   ⛔ **Never name the curator** in this repo or on GitHub (guards: `.githooks/`, gitignored `config/credentials/forbidden_names.txt`).

1. **Decision-0 sync to NexusMind** — ONE NexusMind commit. The sequence is in the archived block (item 1):
   - dry-run diff first
   - copy `filters/common/{filter_base_scorer,hybrid_scorer,cli}.py` together with every live package, deleting their `prefilter.py`
   - retarget NM's `test_prefilter.py` / `test_shared_infrastructure.py`
   - run the NM unit suite
   - ⚠️ since NexusMind#395 step 1, sadalsuud no longer auto-pulls: a **manual pull + scorer-image rebuild** is needed
   NexusMind's session runs it; ours is to tell them. LD#52 and LD#86 are closed.

2. **THE READ SURFACE (#163) — owner: "prune, thin, mechanize, retire".**
   - **Done 2026-10-02:**
     - 2a: six dated entries moved out from under the gotcha-log template heading, verbatim (103.2 → 92.1 KB).
     - The START HERE block went 19.1 KB → this one.
     - Default refcheck 1 → 0 (a moot recall-cost hypothesis was marked).
     - Afternoon: § *Filters* `[x]` history moved verbatim to `docs/TODO-archive.md` (TODO 37.4 → 33.0 KB). Read surface
       measured at 908,775 chars (`/curate` Step 0's command).
   - **Done 2026-10-02 (evening):** `memory/session-log.md` rotated, 153 KB → 70 KB. Entries before 2026-09-01 and the
     frozen appendix moved VERBATIM to `memory/archive/session-log-2026-08-and-appendix.md` (0 lines lost, checked).
     Read surface: **911,068 → 838,699 chars** (`/curate` Step 0's command).
   - **Open, in order:**
     - c. **The unreachable-mechanism catalogue** (55 dated `###` entries).
       - **Keep-rule CHANGED (owner, 2026-10-02):** an entry whose class has a `live` row in § *Mechanized* moves
         VERBATIM to `memory/archive/`.
       - **Measured 2026-10-02:** 0 of the 55 entries NAME a live check, so this needs a per-entry judgement of which
         live check covers each class. ▶ First action next time: that pass, then move the covered entries.
     - d. ✅ session-log rotated (above). **Next: `corroboration-feature-hypotheses.md` (79 KB) and `working-rules.md`
       (65 KB)**. Retire closed rows verbatim into `memory/archive/`. Also the hypothesis ledger (50 KB): move CLOSED rows
       into `memory/archive/hypothesis-ledger-archive.md`.
     - e. **`docs/TODO.md` below START HERE** (~31 KB of section backlog). Audit each section: close, archive or
       keep. Example: § *Commerce Prefilter SLM* and § *Prefilter Quality (Apr 2026)*. Check them against
       decision 0 and ADR-004 before touching them.

3. **Owner, standing:**
   - H-TV5: one last look at the Thriving tab ~2026-10-06, then close.
   - #156 adverse pool (~$3.2–3.6): DEFERRED.
   - Belonging shadow harm cap: a NexusMind change, low priority, v2's before/after instrument.

4. **Small, ours** (detail in the archived block's numbered items):
   - ✅ `cultural_discovery v5` `raw_min` 4.0006 vs 4.0 — **closed 2026-10-07, no change:** a pre-anchor legacy fit
     (2026-07-10; the fitter anchors raw_min to the op-point since 07-16). The tolerance IS recorded:
     `OP_POINT_EPS = 0.01` (`scripts/normalization/fit_normalization.py`), enforced by
     `tests/unit/test_normalization_invariant.py` (passes). Effect: raw in [4.0, 4.0006) normalizes to percentile 0.
     A refit would be a NexusMind deploy for a 0.0006-wide band. `test_normalization_op_point.py` reads only
     `base_scorer.py`, which is why it never saw this.
   - LD#134 step 3, the marking pass (`docs/decisions/2026-09-17-refcheck-docs-tier.md`).
   - ✅ The retracted 19.9%/13.0% framing — **closed 2026-10-07:** already gone from `CLAUDE.md`; the 3 remaining copies
     (`docs/HUMAN_THRIVING_V8_PLAN.md`, `memory/cross-repo-prioritization.md` ×2) now carry the retraction beside them.
   - ✅ LD#160 **done 2026-10-07** as ruled: ADR-009 dated note (no rewrite); `cross_filter_landscape.py` renamed to
     English; `scripts/verification/check_framework_language.py` built and shown RED first (exit 1, 64 violations,
     all in that script), green after (`tests/unit/test_framework_language.py` seeds the class). ⚠️ **LD#160 follow-up
     (owner call):** the checker found a site nobody had listed: `filters/nature_recovery/{v1,v2,v4}/config.yaml`
     carry `ovr.news 'Herstel' tab` in a notes string. v4 is DEPLOYED, so editing it changes a live package's bytes at
     the next NexusMind sync. Listed as KNOWN OPEN in the checker until ruled.
   - H-MECH-1: watch, 2 batteries left.
   - #158: the heldout detector band (b650).
   - #104 item 1: likely MOOT if gpu-server is retired.

5. **NexusMind's, nothing of ours:**
   - NexusMind#395: step 1 LIVE on sadaltager since 2026-09-29.
   - ⚠️ **gpu-server answers SSH again** (2026-10-02 07:03, `up 99 days`): it never went down; the
     2026-09-28 "outage" was reachability. Tell the owner and the NexusMind session before they decide anything
     on "gpu-server is gone" (#104 item 1, orphan dirs).
   - NM#286 item 3 (PR #561): its outcome check.
   - ADR-024 steps 4–5.
   - NexusMind#558 (OOM).

**Cloud pilots: STOPPED by the owner 2026-09-29.** Do not start one without the owner.
---

## Commerce Prefilter SLM - NEEDS REWORK

ML classifier for commerce/promotional content detection. Cross-cutting prefilter for all filters.

**Status:** v1 complete but needs redo - concerns about multilingual embeddings and context size.
**v1 is the version running in production** — force-pinned by LD#80 because **v2 underperformed v1** on production traffic. There is no v3.
**v2 is RETIRED (2026-09-27, owner):** it no longer ships (`RETIRED_DIRS`, `3e7f565`) and NexusMind PR #553 deleted it
downstream — confirmed on sadalsuud 2026-09-28. The package stays here as a record.

- [ ] **v1 @0.95 OVER-BLOCKS — owned here (owner, 2026-10-06)**, evidence on ducroq/NexusMind#527.
      One judge (blind Claude subagents, v1 `prompt.md`): 60/80 uniform blocked rows are journalism
      (rubric ≤4); second judge gemma3:27b agrees (70.0% on n=230, κ 0.61). Scores stable (0 flips,
      two CPU generations; gate decides on round(score,4)). Reader cost: 4/228 blocked rows reachable,
      all below 0.990, so 0.990/0.993/0.995 are reader-identical. **PROPOSAL POSTED 2026-10-06**
      (NM#527 comment 6025385135): 0.990 + decide at the gate on `_commerce_score` (config-only
      change = ~3-day ramp); 0.995 the owner's alternative. ✅ **APPROVED 2026-10-07; DEPLOYED 2026-10-07 21:28 CEST** (NexusMind PR #618, `78f4dd1`); **VERIFIED by outcome** (NM#527, 2026-10-08): commerce blocks per cycle 34,385 → 13,597 (39.5%; predicted 38.9%), obituary unchanged, 1,557 released articles reach all 6 lenses, 0 stale `_is_commerce: true` in Contract B. Nothing left on our side; NexusMind closes NM#527. A v3 retrain is NOT planned. 0.95 was chosen on 0/3 high-tier sustainability_technology rows
      (`BACKTEST_REPORT.md`) — never a general-traffic FP measurement. Data: sadalsuud `~/nm527/`.
      Likely cause (untested): test-split negatives are 57/101 arXiv, positives consumer-tech.
      NexusMind changes nothing until the owner approves a proposal.
- [ ] **Re-measure the miss rate before retraining** ← **DO THIS FIRST (added 2026-08-07)**
      (partly answered 2026-10-06: 0/120 rubric ≥7 in the reader-reachable 0.5–0.95 band, NM#527)
- [ ] **NM#223 is a live input to this and is blocked** (found 2026-08-07 late) —
      NER entity-density as an *additive* commerce signal, explicitly "does not
      replace the v3 retrain planned in NM#185 Phase 2". It is blocked on
      **NM#232**, not on the closed `FluxusSource#85` its body still names.
      Nothing here should assume entity features will be available.
- [ ] **Redo with proper multilingual embeddings** - Current approach may not handle Dutch/multilingual well
- [ ] **Redo with proper context size** - May need longer context

### The v3 case is tracked in ducroq/NexusMind#185, and its evidence has decayed

Found 2026-08-07 while re-querying the cross-repo chains. NM#185 bundles the
obituary blocker (shipped, enforcing at 0.85 since 07-30) with a **commerce v3
retrain that was never started** — which is why Chain 1 read as complete when it
was half done.

**Before any v3 training run, re-measure.** NM#185's commerce evidence is the
2026-06-25 reader-flag audit, whose headline was that the recoverable miss set
was **100% scored by `sustainability_technology`** — a filter **deleted
2026-08-03** (#64, superseded by `solutions`). The product-launch-in-
sustainability-framing pattern presumably still arrives, but it is now scored by
`solutions v6`, which has a different prompt, a different op-point and an e5
probe in front of it.

**Open hypothesis:** the commerce miss rate under the current five-lens set is
materially lower than the 2026-06-25 audit implies, and v3 may not be warranted
at all. Unmeasured. Deciding it costs one count, not a training run.

See `filters/common/commerce_prefilter/docs/` for full documentation.
<!-- verify: ls filters/common/commerce_prefilter/ | grep -E '^v[0-9]+$' -->
<!-- verify: gh issue view 185 -R ducroq/NexusMind --json state --jq .state -->

---

---

## Filters

*The `[x]` history that stood here (Production Ready, In Active Development, Active Learning In Progress) moved
VERBATIM to `docs/TODO-archive.md` § *Moved 2026-10-02 (afternoon): § Filters history* (read surface, #163 item e).
Current filter state lives in `memory/filter-status.md` and the `CLAUDE.md` table.*

### Other Filters
- [ ] ~~**future-of-education**~~ - DROPPED: education stories land naturally in Breakthroughs (research)
- [ ] **ai-engineering-practice v2** - Ready for oracle scoring (not ovr.news, separate product)
  - FluxusSource hardware sources active (1,193 articles)
  - Prompt calibration complete (~60% tier accuracy)
- [ ] **seece** - Corporate excellence (not ovr.news)
- [ ] **sustainability_economic_viability** - Sustainability sub-dimension (not ovr.news)
- [ ] **sustainability_policy_effectiveness** - Sustainability sub-dimension (not ovr.news)

### Parked Ideas

- [ ] **Measuring "true AI adoption" in SMEs and larger companies** - PARKED 2026-08-11 by Jeroen ("interesting, park it as an idea"). Owner side question. **Answer: not as asked** — our corpus is articles, adoption happens at firms, so it measures adoption *discourse*, not adoption. SMEs are ~99% of firms and ~0% of coverage; 25.7% of the corpus is GN headline stubs; no firm-level ground truth to validate against. **What it WOULD answer well:** of AI-adoption claims in the press, what share are concrete deployments vs announcements — the `solutions v6` shape, whose tech/hybrid tiebreak already makes that discrimination. **The pivot that reaches the literal question: job postings** (firm-level, size-linkable, exists for SMEs; needs a FluxusSource vacancies feed). **Cheap first probe with a kill criterion: base-rate screen of the existing corpus, ~1h, no oracle spend — if AI-adoption content is a fraction of a percent, stop.** Precedent for that kill: `solutions v6`'s `community_practice_strength` is a sourcing problem, not a modelling one. Full note in **`docs/ideas/ai-adoption-measurement.md`**. Re-check #103 (DeepSeek price rise) before any oracle spend.

- [ ] **Re-enchantment outlets (wonder lens / standalone digests)** - PARKED 2026-07-16 by Jeroen ("some other time"). Byung-Chul Han-inspired exploration: wonder/mystery/myth as lens or standalone oracle-only outlet (no distillation needed at digest scale, ~$6.50/wk). Six ideas + four cheap probe plans (<$3 total: Residue query $0 → Wonder probe ~$0.50 → form-scoring feasibility ~$1-2 → Ledger design note $0) with kill criteria in **`docs/ideas/re-enchantment-outlets.md`**. Hard constraint if resumed: "unexplained" needs an `epistemic_honesty` gatekeeper (misinformation magnet otherwise). Below solutions v4 (#43) and the #62 check in priority.

## Training Pipeline

- [x] **Data preparation pipeline** - Stratified splits working
- [x] **Training script** - Gemma-3-1B + LoRA working (was Qwen2.5-1.5B)
- [x] **Context length experiments** - 1024/2048/head+tail tested
  - 1024tok: MAE 0.652, 2048tok: MAE 0.627
  - head+tail (256+256): MAE ~0.69 (deployed to production)
  - See `docs/IDEAS.md` for full results
- [x] **Stage 2 model comparison** - Gemma-3-1B adopted as default Stage 2. Wins on both uplifting (MAE 0.652 vs 0.660) and cultural-discovery (MAE 0.743 vs 0.755). 8% faster, fewer params. Qwen-0.5B rejected (MAE 0.760)
- [x] **Gemma-3-1B training support** - `training/train.py` updated with `load_base_model_for_seq_cls()` for both initial and resume paths
- [x] **Stage 2 model selection** - Gemma-3-1B adopted as default (was Qwen2.5-1.5B). Larger models deferred.
- [ ] **Training monitoring improvements** - Better logging, early stopping

## Score Calibration (ADR-008)

Post-hoc isotonic regression to correct MSE score compression at inference time.

- [x] **Shared calibration library** - `filters/common/score_calibration.py` (fit, apply, save, load)
- [x] **CLI fitting tool** - `scripts/calibration/fit_calibration.py` (works for any filter)
- [x] **Uplifting v6 calibration** - Fitted on 1,049 val articles, val MAE 0.673 -> 0.653 (+3.1%)
- [x] **Cultural-discovery v4 calibration** - Fitted on 803 val articles, test MAE 0.77 -> 0.74 (+4.4%)
- [x] **Base scorer integration** - `_load_calibration()` + `apply_calibration()` in `_process_raw_scores()`
- [x] **sustainability_technology v3 calibration** - Fitted on 1,061 val articles, test MAE 0.725 -> 0.724
- [x] **investment-risk v6 calibration** - Fitted on 1,045 val articles, val MAE 0.497 -> 0.465 (+6.5%)
- [x] **belonging v1 calibration** - Fitted on 738 val articles, val MAE 0.534 -> 0.489 (+8.3%)
- [x] **nature_recovery v1 calibration** - Fitted on 328 val articles, val MAE 0.540 -> 0.507 (+6.2%)
- [x] **nature_recovery v2 calibration** - Fitted on 352 val articles, val MAE 0.632 -> 0.533 (+15.7%)

## Hybrid Inference Pipeline (ADR-006)

Two-stage pipeline: fast embedding probe (Stage 1) + fine-tuned model (Stage 2).

- [x] **Shared infrastructure** - `filters/common/embedding_stage.py`, `hybrid_scorer.py`
- [x] **Uplifting v5 integration** - `inference_hybrid.py` + MLP probe
- [x] **Calibration script** - `evaluation/calibrate_hybrid_threshold.py`
- [x] **Threshold calibration** - Calibrated on 24K production articles. Probe retrained (v2): MAE 0.49, bias +0.007. Threshold 3.5 → 1.7% FN rate on MEDIUM+
- [x] **Speed benchmark** - RTX 4080: e5-small 1.3ms + Qwen 37.9ms. Threshold 4.5 → 2.09x on skewed data, ~2.5-3x in production
- [x] **Stage 2 model evaluation** - Gemma-3-1B adopted as default Stage 2 model. Confirmed on two filters: uplifting v5 (MAE 0.652 vs 0.660, tier 86.6% vs 85.4%) and cultural-discovery v3 (MAE 0.743 vs 0.755, tier 94.6% vs 94.5%). 8% faster inference, 38% faster training
- [x] **Generalize to other filters** - Phase A complete: inference_hybrid.py + probe dirs + calibration fix for sustainability_technology v2, investment-risk v5, cultural-discovery v3
- [x] **Train probes + calibrate thresholds** - Phase B complete: e5-small MLP probes trained and calibrated for all 3 filters
  - sustainability_technology v2: probe MAE 0.707, threshold 1.25, 1.2% FN, 1.25x speedup
  - investment-risk v5: probe MAE 0.497, threshold 1.50, 0.8% FN, 1.07x speedup
  - cultural-discovery v3: probe MAE 0.609, threshold 1.25, 0.0% FN, 1.52x speedup
- [x] **Cultural-discovery v4 probe** - Retrained for Gemma-3-1B, MAE 0.87, threshold 1.25, 3% FN, 1.51x speedup
- [x] **Sustainability_technology v3 probe** - Trained for Gemma-3-1B, MAE 0.91, threshold 1.25 (to be calibrated)
- [x] **Investment-risk v6 probe** - Trained for Gemma-3-1B, MAE 0.557, threshold 1.50
- [x] **Belonging v1 probe** - Trained for Gemma-3-1B, MAE 0.54
- [x] **Nature_recovery v1 probe** - Trained for Gemma-3-1B, MAE 0.50
- [x] **Nature_recovery v2 probe** - Retrained for v2 model, MAE 0.49 (early stop epoch 24)
- [x] **Foresight v1 probe** - Trained for Gemma-3-1B, threshold 2.25
- [x] **Foresight v1 calibration** - Fitted, calibration.json committed with filter package
- [x] **Uplifting v7 probe** - Trained for Gemma-3-1B, MAE 1.10, threshold 1.00 (#34)
- [x] **Harmonize all filters** (2026-04-06) - All 7 production filters now have hybrid inference with calibrated thresholds and `--compare` CLI. Fixed investment-risk import path bug (hyphen vs underscore). Deployed to sadalsuud + gpu-server.

## Energy-Efficient Inference (#24)

- [x] **PyTorch dynamic quantization experiment** - 2026-03-07
  - Tested FP32/FP16/INT8 on uplifting v6, CPU-only
  - INT8: 2.6x faster, 3.3x smaller, but MAE +0.63 (unusable)
  - FP16: NaN on CPU (no native fp16 ALUs)
  - **Verdict:** Naive quantization rejected
  - See `docs/experiments/quantization-benchmark-2026-03-07.md`
- [ ] **ONNX Runtime INT8** - Calibrated quantization with representative data
- [ ] **Smaller base model retraining** - SmolLM-360M or similar sub-1B models
- [ ] **llama.cpp / GGUF** - Purpose-built CPU inference engine

## Deployment

- [ ] **Inference server** - Unified prefilter + model + postfilter pipeline
- [ ] **Batch processing** - High-volume article scoring
- [ ] **Production monitoring** - Latency, accuracy drift detection

## Infrastructure

- [x] **Prefilter evaluation framework** - Complete for sustainability_technology
- [ ] **Dataset QA pipeline** - Automated quality checks
- [ ] **Cost tracking** - Monitor API usage for oracle scoring
- [x] **Hub scorers: add torch_dtype parameter** - All 6 `inference_hub.py` files now accept optional `torch_dtype` param and pass it to `from_pretrained()`. Use `torch_dtype=torch.float16` on hardware without bfloat16 support.
- [x] **Deploy all filters to NexusMind** (#7) - All 6 filters deployed to gpu-server + sadalsuud + HuggingFace Hub
- [x] **Auto-compute score_scale_factor** (#22/#26) - Calibration script writes `score_scale_factor` to config.yaml; backfilled to all 6 filters
- [x] **Harmonize filters: llm-distillery as single source of truth** - Fixed drift between llm-distillery and NexusMind
  - base_prefilter.py: threading.Lock() for commerce detector (was bool flag)
  - investment-risk v5: merged source-based + content-pattern approaches, removed academic source blocking
  - Deployed all production prefilters to NexusMind (sadalsuud + gpu-server)
  - Verified 0 diff between all three locations
- [x] **Manifest-aware deploy script (#50)** - 2026-04-28. `.nexusmind-owns` at repo root + `--dry-run` + `--force-skip-owned-drift` in both `.sh` and `.ps1`. Lists `filter_base_scorer.py` and `hybrid_scorer.py` (NexusMind-owned). Deploy now exits non-zero on drift between distillery and NexusMind copies.

## Post-#52 Review-Battery Followups

Items surfaced by the multi-agent code review of the migration commits (2026-04-29). Triaged in TODO.md as committed batches.

- [ ] **Extend `_is_excluded` for per-category exceptions + migrate CD v4 / uplifting v7 to base pipeline** - Path narrowed by the belonging migration above: the architecturally-correct next move is the two-step path filed as **#66** (base `EXCLUSION_REASON_PREFIX` class attr + move domain checks into `_pre_exclusion_check`), which unblocks fully-declarative migration for belonging v1, CD v4, uplifting v7, foresight v1, and NR v2 simultaneously. ADR-019's hook signature widening (raw-article access) deferred until a second filter shows up needing case-sensitive raw fields. Original open questions still apply: (a) reason-string convention — covered by the prefix attr in #66; (b) CD v4 missing `validate_article` + `check_content_length` — base would add both, fixing the regression but changing observable behavior; (c) uplifting v7's count-based `pure_speculation` block doesn't fit the dict shape regardless.
- [ ] **Migrate nature_recovery v2 to fully-declarative shape via `_pre_exclusion_check`** - Bundle with #66 (the reason-prefix attr is the prerequisite). NR v2 has the same shape concerns as the post-#52 cluster: bare reason strings, missing `check_content_length`, and order-of-checks differences from the base pipeline.

## Prefilter Quality (Apr 2026)

- [ ] **Obituary v6 (#85) — PARKED indefinitely (owner, 2026-07-30)**: v5@0.85 enforcement meets the recall-first requirement. Reactivate only if an obit reaches the site (owner flag) or over-blocking visibly hurts the feed. Plan preserved on the issue; b650 env + adjudicated golden set (14 rows) stay ready. **2026-07-31 FN evidence banked for reactivation** (memory/obituary-v4-hypotheses.md addendum 7 + #85 comment): community-mourning class regresses monotonically v3 0.68 → v4 0.44 → v5 0.12 (hard-negative interference); biography-rich obits are a stable all-version blind spot (~0.2–0.3, threshold can't reach).

## Cross-Filter Normalization (ADR-014)

- [x] **uplifting v6 normalization** - Fitted on production CDF
- [x] **belonging v1 normalization** - Fitted on production CDF
- [x] **cultural-discovery v4 normalization** - Fitted on production CDF
- [x] **sustainability_technology v3 normalization** - Fitted on production CDF
- [x] **uplifting v7 normalization** - Fitted on 73,986 production articles (2026-04-06)
- [x] **foresight v1 normalization** - Fitted on 623 articles (thin LUT, improves as data accumulates)
- [x] **nature_recovery v1 normalization** - Refitted on 76,500 articles (still clamped — extreme needle filter, #32)
- [x] **nature_recovery v2 normalization** - Fitted on 1,397 v2 production articles (filter_version=2.0, weighted_average >= 1.5), deployed to sadalsuud + gpu-server (2026-04-28). Patched `fit_normalization.py` with `--filter-version` to exclude v1 leftovers (19,948 articles correctly skipped). Curve: raw range 1.50–7.08, p95=4.49.
  - [x] **Follow-up VERIFIED 2026-05-04**: sustainability_technology JSONL on sadalsuud (1142 articles, 19:22 UTC pipeline run) shows `weighted_average=1.81`, `raw_weighted_average=4.42`, `normalization_method="percentile"` — both audit fields populated end-to-end for the first time since 2026-04-16. The verification revealed that the runtime application code itself had been silently deleted from NexusMind and gone unnoticed for 18 days; fix landed via Path B extraction into `NexusMind/src/scoring/production_scorer.py` wrapper class (NexusMind merge `0e80d92`). All 7 filters now populate the audit fields. See `memory/gotcha-log.md` "Manifest as Anti-Pattern" entry for full diagnosis.

## Documentation

- [ ] **Update filters/README.md** - Current status is outdated (Nov 2025)
- [ ] **Training guide** - Step-by-step for new filters
- [ ] **Deployment guide** - Production setup instructions
- [x] **HF Hub model card relicensing** (2026-05-22, commits `fb67d05` + `41d2108`, #65 closed). Source-side: `upload_to_huggingface.py:28` now declares `license: eupl-1.2` in the model-card YAML frontmatter. Hub-side: one-shot script `scripts/deployment/relicense_hub_repos.py` walked all 14 `jeergrvgreg/*` repos and rewrote the frontmatter `license:` line; verified post-upload on 3 repos (public uplifting-filter-v5, private belonging-filter-v1, private sustainability-technology-v3). Repo LICENSE + pyproject + upload template + 14 Hub model cards now all carry EUPL-1.2 consistently.
- [x] **deploy_to_nexusmind hardening: refuse-on-dirty + explicit staging** (2026-05-23, commits `4cf75dd` + `dd11727`). Fix for the origin-contamination hazard discovered during the 2026-05-22 belonging deploy: `git add -A` on NexusMind's working tree swept ~1,400 lines of unrelated story-dedup WIP into commit `7a595c4` and pushed it to origin without the author's review. Both `.sh` and `.ps1` now do (a) pre-flight `git status --porcelain` refuse-on-dirty check with `--force-dirty`/`-ForceDirty` escape hatch, and (b) explicit `git add $FILTER_PATH filters/common/` instead of blanket add. Printed server-pull instructions also corrected (sadalsuud at `~/local_dev/NexusMind`, gpu-server deploy via `bash scripts/deploy_filters.sh` from sadalsuud — not `git pull` on a stale `llm-distiller` hostname). Cross-referenced with NexusMind-side gotcha-log entry and `b12d554` documentation commit.

---

*Last updated: 2026-08-01*

## ☐ Open threads inside ARCHIVED ledger rows (2026-09-27 retire; rows in `memory/archive/hypothesis-ledger-archive.md`)
- [ ] `H-V8-3`: the reorder's multiplicity question "is still open": no pre-registered family was ever run. v8 is superseded by v9, so likely moot; close it or run it.
- [x] `H-V8-26`: its revisit trigger is a ~50-article hand-audit of v8's reader-facing precision; no audit record was found (review 2026-09-27). Moot now that v9 is live? Owner call. **CLOSED 2026-10-01 (owner): moot — v8 no longer serves readers; the live question is `H-TV5`.**

## ☐ Unchecked boxes carried out of the archived sections (2026-09-24)

*Copied mechanically from `docs/TODO-archive.md`: every `- [ ]` line in a moved section, under
that section's heading. ⚠️ **Not re-verified** — many are probably done or overtaken; the
queue is ▶ START HERE, not this list. Close or delete a line once checked against its section.*


**From:** 🔵 PREVIOUS SESSION — **ADR-013 widened to all framework text; review found my own evidence unsound and the compliance zero FALSE. Framework 6 releases behind, s
- [x] **Mechanize the language rule (#160)** — done 2026-10-07: `scripts/verification/check_framework_language.py`
  (names in framework text; commit messages still unread). See START HERE item 4.

**From:** 2026-08-09 — corroboration: the shippable change was refuted, the gate is the lever

**From:** 2026-08-08 (afternoon) — proven by outcome, and a self-inflicted outage
- [ ] Re-measure gated on **measured GN-URL share per cycle**, not on "migration

**From:** 2026-08-08 — the checks failed, the analysis didn't
- [ ] **Loose thread:** eval-arm articles cluster at **9.4–9.99** on uplifting and
- [ ] Promote `content_length` to `required` in Contract B **only after** the

**From:** 2026-08-07 (night) — the dedup question answered by mechanism, and a deadline in trouble
- [ ] **Remediate the 30 already-published rows** — reader-facing, ovr.news side,
- [ ] **Check the Zimbabwe funeral row against the obituary gate** (enforcement is

**From:** 2026-08-07 (late) — coverage pass, a refuted plan, one instrument shipped

**From:** 2026-08-06 evening — four owner decisions taken, three backlogs closed

**From:** 2026-08-06 — cd v6 probe (#98), the English escape hatch (#99), and an instrument for FS#120

**From:** 2026-08-05 — TDM / training-data position, and the two carve-outs it leaves open
- [ ] **The `tdm_opt_outs.json` scan is unscheduled.** It has run exactly once (2026-08-04). A reservation added tomorrow is invisible. Quarterly is enough for a signal that moves this slowly — the implementation sketch in #28 is retained there as the thing to build **if this decision is ever reversed**, not as work to do now.

**From:** 2026-08-02 — Chain 4 measured: two of the previous day's own P0 conclusions overturned
- [ ] **Fit the solutions short-content cap** (#93 step 4) — **#92 no longer blocks it; #95 still does.** The second-op-point re-run ran 2026-08-05 and the defect is **identified**: D1 (both arms ≥2.25) −0.790, D2 (≥4.00) −0.861, **D3 (matched percentile depth) −1.119** [−1.61,−0.61], cluster-bootstrap p Holm-corrected 0.0032 / 0.0012 / <1.5e-4. The selection artifact predicted D2 markedly more negative and D3 → 0; D2 moved −0.071 and D3 is the *largest*. A gemini-2.5-flash cross-check on the same D3 sample gives **−1.351** [−1.73,−0.96] — two oracles with clearly different absolute bias, same gap, which rules out "the judge penalises short input". Harness + fixtures committed (`scripts/diagnostics/ld92_*.py`, `tests/fixtures/ld92/`). **Remaining blocker is Batch F.1 (#95)**: the cap value is a threshold fit and inherits the |Δ| ≤ 0.16 batch-composition noise floor. Also weigh the recall cost against NM#231/#292 before setting a value — `gn_africa_*` / `gn_asia_*` feeds lead solutions' short-and-clearing list.
- [ ] **Does the scorer share the summariser's fixed-budget failure? (NEW, ovr#299)** For English sources, summary content words absent from the article *and* title run 31.6% (1000+ chars) → 73.9% (120–299) → **83.4% (<120)**, monotone over 18,756 summaries. The mechanism there is a fixed output length target (medians 1159/968/875/1065 against a 40× input range) that the model fills — compressing an article, generating from a headline. **Open for this repo: whether the student has an analogous behaviour, or whether its short-content error is purely vocabulary-without-subject.** The fixes differ — one is a budget, the other a cap — so this is worth one experiment before building either.
- [ ] **NM#286 item 3** (violence stamping skipped in single-filter / `--no-dedup` / dedup-exception runs). Verified in code; **live blast radius zero today** (production runs multi-filter, violence `enforce: false`), so it is an audit gap, not admitted violence. Still a hard prerequisite for any violence enforce flip, with LD#82.
  - ⛔ **2026-09-28: the premise is gone and the fix is not in.** Violence has ENFORCED since 2026-08-23 (`config/app.yaml` comment on sadalsuud); `_run_violence_promotion_prefilter` still returns with NO stamps when `_article_cache` is empty (read on sadalsuud today), and `_enforce_violence_promotion` fails open. Live multi-filter cycles stamp, so today's exposure is a shared-dedup exception or an ad-hoc single-filter run. `10344 unstamped articles left in place` (the **05:21** enforcement line, not 09:05 as first written) = dedup-removed copies: nexusmind-55 matched it exactly in 3 cycles (1,724 × 6 filters = 10,344; 1,395 × 6 = 8,370; 1,518 × 6 = 9,108), removed afterwards by per-filter cached dedup — arithmetic identity, not an id-level join. Confirmed unfixed at NexusMind HEAD `9dfcf2a`; scheduling is the owner's call in that session, fix = NM#286's plus an outcome check (unstamped SURVIVORS after dedup = 0). NexusMind's code; owner to decide whether to raise it on NM#286.

**From:** 2026-08-01 — Cross-repo: ovr#280 cluster_id diagnosis corrected
- [ ] **NM#278 is the real fix for the reported symptom** — the five-articles-on-one-story report is a *threshold* problem, not a plumbing one: NexusMind clusters on source text pre-summarization, where cross-outlet paraphrases look far apart; two of the five only converge after ovr.news summarizes. Caution recorded on NM#278: NexusMind *removes* rather than *labels* (32%/run), and anything removed upstream can never surface as an "N sources" badge — so prefer labelling over dropping when re-tuning.

**From:** 2026-07-31 — LD#76 Calibration Audit (11-agent battery, all verdicts adversarially verified)
- [ ] **cd v6 lens fidelity scope (#87)** — ccc 0.25 weight ceiling (mean 0.64), 27% off-lens hard science in visible band, "4.5 display threshold" vs shipped 4.0 unreconciled. Design ticket; not urgent. The 3.5 op-point proposal was REFUTED (sampling artifact) — any re-derivation needs a randomized [3.0,4.5) sample **after NM#284 lands**: the v5 op-point and normalization CDF were both fitted on a distribution still containing the ~71% the prefilter should have removed.
- [ ] **Lens harmonization program (#90)** — owner directive 2026-07-31: bring all lens filters to the successful template (op-point at the distribution, fresh anchored fit, working positive gate, hybrid + stamps, ADR-021 gate) **The rename half is CLOSED as of 2026-08-06 — do not re-open it here.** ADR-012 amended: `cultural_discovery` and `nature_recovery` KEEP their names (their Hub repos are public standalone artefacts; `discovery-filter-vN` / `recovery-filter-vN` drop the qualifier that says what the model is about), `solutions` confirmed as-is, and `uplifting` → **`human_thriving`** at v8 — not bare `thriving`, which is an existing parked directory. What remains under #90 is the template half only.
- [ ] **Hygiene batch** — emit `stage_used` into row attrs; document nr runtime stage-1 threshold 0.75 (config.yaml says 3.225, inert); fix stale ir config tiers (3.0 vs live 4.0); note nr raw HIGH tier 7.0 > calibrated ceiling 6.8 (structurally dead).
- [ ] **Drift guard** — uplifting violated the >20%-relative-pass-rate refit trigger by an order of magnitude for ~4 months, undetected; the prefilter kill (NM#284) hid for ~6 months the same way. Add per-cycle pass-rate logging or a scheduled drift check covering both normalization freshness and declared-vs-observed prefilter pass rate (owner question). **RULED 2026-10-01 (owner): keep, rescoped to NORMALIZATION FRESHNESS only (the prefilter half died with decision 0); later, after belonging v2.**
