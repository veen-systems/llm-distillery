# LLM Distillery - TODO

## Commerce Prefilter SLM - NEEDS REWORK

ML classifier for commerce/promotional content detection. Cross-cutting prefilter for all filters.

**Status:** v1 complete but needs redo - concerns about multilingual embeddings and context size.

- [x] **v1 Training data collection** - 2,847 examples (commerce + journalism)
- [x] **v1 Model training** - DistilBERT, MiniLM, XLM-RoBERTa compared
- [x] **v1 Backtesting** - 56,336 articles, threshold optimization
- [ ] **Redo with proper multilingual embeddings** - Current approach may not handle Dutch/multilingual well
- [ ] **Redo with proper context size** - May need longer context

See `filters/common/commerce_prefilter/docs/` for full documentation.

---

## Filters

### Production Ready
- [x] **uplifting v6** - Deployed on HuggingFace Hub (private)
  - Val MAE: 0.673 (was 0.688 in v5), 12% faster inference
  - Gemma-3-1B base model (was Qwen2.5-1.5B)
  - 10,495 training articles with data sculpting: active learning (495 MEDIUM enrichment) + label correction (57 crime articles capped)
  - v5 crime news issue fixed via manual label correction in training data
- [x] **uplifting v5** - Superseded by v6
  - Val MAE: 0.68, 10,000 training articles
- [x] **sustainability_technology v1** - Deployed on HuggingFace Hub
  - Test MAE: 0.690
- [x] **sustainability_technology v3** - Deployed on HuggingFace Hub (private)
  - Val MAE: 0.734 (calibrated test: 0.724), Gemma-3-1B
  - 10,608 training articles (v2 10,039 + 569 active learning enrichment)
  - All 3 inference paths: local, Hub, hybrid (probe MAE 0.91)
- [x] **sustainability_technology v2** - Superseded by v3
  - Val MAE: 0.71, 7,990 training samples
- [x] **investment-risk v6** - Deployed on HuggingFace Hub (private)
  - Val MAE: 0.497 (calibrated: 0.465), Gemma-3-1B
  - 10,448 training articles (v5 10,198 + 250 active learning enrichment)
  - Tier simplification: RED/YELLOW/GREEN/BLUE/NOISE -> high/medium_high/medium/low
  - All 3 inference paths: local, Hub, hybrid (probe MAE 0.557)
- [x] **investment-risk v5** - Superseded by v6
  - Test MAE: 0.484 (excellent)
  - 10,000 training articles
- [x] **cultural-discovery v5** - Deployed on HuggingFace Hub + gpu-server (private) — 2026-05-31
  - Val MAE: 0.697 (v4 was 0.74), Gemma-3-1B
  - 8,551 training articles, DeepSeek V4 Flash oracle (first non-Gemini lineage)
  - Resolves llm-distillery#62 discovery-lens leakage via F/G/H/I/K soft-penalty flags (historical_harm_reckoning, commemoration, perpetrator_biography, decline, launch)
  - Provisional reference example for ADR-020 methodology (multi-oracle calibration + agent judging)
  - Target: ovr.news Discovery tab
- [x] **cultural-discovery v4** - Superseded by v5; on disk locally + git + HF Hub for rollback if needed
  - Calibrated test MAE: 0.74 (v3 was 0.77), Gemma-3-1B
  - 8,029 training articles (v3 7,827 + 202 active learning enrichment)
  - All 3 inference paths verified (local, Hub, hybrid)
- [x] **cultural-discovery v3** - Superseded by v4

### In Active Development (priority: ovr.news tabs)
- [x] **belonging v1** - Deployed, val MAE 0.49 (calibrated), 7,370 articles. Next: ovr.news tab
- [x] **nature_recovery v2** - Deployed to Hub + gpu-server + sadalsuud (Hub upload actually completed 2026-04-19 after #44; prior commit claimed it without uploading)
  - Val MAE 0.53 (calibrated), probe MAE 0.49, 3,517 articles
  - v1 had zero discrimination (#41); v2 uses sample weighting (scale=2)
  - Recall@20: 0.70 (v1: 0.55), NDCG@10: 0.86 (v1: 0.71), false negatives: 17% (v1: 41%)
  - Hub: `jeergrvgreg/nature-recovery-filter-v2` (private)
  - Remaining: normalization (needs production CDF), ovr.news Recovery tab frontend
- [x] **uplifting v7** - ADR-010 prompt rewrite, deployed with hybrid inference (2026-04-06)
  - v7 prompt: scope check, anti-hallucination, reframed assessment dimensions
  - Hybrid inference: probe MAE 1.10, threshold 1.00, 0.5% FN, 1.07x speedup
  - Evolved into thriving v1: renamed, social_cohesion_impact removed, 3-run averaging planned
- [ ] ~~**thriving v1**~~ - PARKED indefinitely. Uplifting v7 (MAE 0.67) stays as Thriving tab.
  - Root cause: orthogonal lens design created bimodal distribution (ADR-015)
  - A fixed thriving v2 would converge back to uplifting v7. Not worth retraining.
  - Assets preserved in `memory/thriving-v1-scoring.md` if ever revisited
- [x] **foresight v1** - Deployed on HuggingFace Hub (private) — was signs_of_wisdom
  - Val MAE 0.75, 3,480 training articles, 6 dimensions
  - Hybrid inference: probe trained, threshold 2.25 (default, calibrate on production data)
  - Remaining: ovr.news Foresight tab frontend integration

### Active Learning In Progress
- [ ] **cultural-discovery v5** - Training data ready (8,551 articles = v4 8,029 + 473 active-learning + 49 hard-negatives via #62)
  - Oracle-scored 473 production MEDIUM+ articles with Gemini Flash (active-learning lane, 2026-04-06)
  - Smooth distribution (bell curve centered at WA 4.8), no bimodality
  - 2026-05-29: #62 hard-negatives cohort added — 49 articles labeled with v5 oracle prompt (5 new pre-classification flags F,G,H,I,K)
  - v5 prompt deltas: TRAJECTORY OVER VOCABULARY principle, CAP ENFORCEMENT clamp rule, F carve-out covers wartime restitution (Modigliani fixed), J intentionally omitted (handled by `filters/common/obit_signal.py` per #51)
  - Cohort stats: production v4 mean 8.27 → v5 oracle mean 4.05; 44 hard-negatives + 5 calibration-confirmed positives (tagged `_v5_oracle_reclassified`)
  - Next: train on gpu-server, calibrate, retrain probe, deploy
- [x] **nature_recovery v2** - Trained, calibrated, deployed (2026-04-16)
  - Sample weighting (scale=2) + active learning enrichment (237 articles)
  - Remaining: normalization (needs production CDF), hybrid threshold recalibration

### Other Filters
- [ ] ~~**future-of-education**~~ - DROPPED: education stories land naturally in Breakthroughs (research)
- [ ] **ai-engineering-practice v2** - Ready for oracle scoring (not ovr.news, separate product)
  - FluxusSource hardware sources active (1,193 articles)
  - Prompt calibration complete (~60% tier accuracy)
- [ ] **seece** - Corporate excellence (not ovr.news)
- [ ] **sustainability_economic_viability** - Sustainability sub-dimension (not ovr.news)
- [ ] **sustainability_policy_effectiveness** - Sustainability sub-dimension (not ovr.news)

### Parked Ideas

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

## Code Quality (Feb 2026)

- [x] **FilterBaseScorer extraction** (#10) - Shared base class in `filters/common/filter_base_scorer.py`, all 4 production filters migrated
- [x] **load_lora extraction** (#11) - Shared `load_lora_model()` in `filters/common/model_loading.py`
- [x] **Code quality sweep** (#12-#19) - Resolved 8 issues: removed dead code, cleaned stale comments, fixed inconsistencies (-314 lines)

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
- [ ] **Generalize prefilter evaluation** - Apply to all filters
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
- [ ] **Harmonize prefilter structure across all 7 production filters (#52)** - Filed 2026-04-28. Survey shows 5 different override mechanisms, 3 with class/version drift between class name and dir, mixed flat-list vs dict containers. ~12-16h work; per-filter migration in priority order.
  - [x] **ADR-018** (2026-04-28) - Declarative shape decision documented; backwards-compatible BasePreFilter extension chosen
  - [x] **BasePreFilter extension** (2026-04-28) - EXCLUSION_PATTERNS / OVERRIDE_KEYWORDS / POSITIVE_PATTERNS / POSITIVE_THRESHOLD class attrs + default apply_filter() pipeline + _is_excluded / _has_override / _filter_specific_final_check helpers. All 7 production prefilters import + run unchanged (verified)
  - [x] **sustainability_technology v3 migrated** (2026-04-28) - 6/6 self-tests pass; behavior preserved
  - [x] **belonging v1 migrated** (2026-04-29) - 19/19 self-tests pass; behavior preserved. Data shape (EXCLUSION_PATTERNS dict, base-compiled patterns) harmonized; apply_filter stays custom because per-category positive-count thresholds + URL-based domain exclusions + obituary floor rule don't fit the base pipeline (ADR-018 explicitly permits this).
  - [x] **cultural-discovery v4 migrated** (2026-04-29) - 10/10 self-tests pass; behavior preserved. Data shape harmonized: EXCLUSION_PATTERNS dict + parallel EXCEPTION_PATTERNS_PER_CATEGORY dict (per-category exceptions don't fit base's single OVERRIDE_KEYWORDS slot). CULTURAL_DISCOVERY_BOOST_PATTERNS renamed to POSITIVE_PATTERNS so base compiles them. classify_content_type() preserved. Surfaced regression vs v3: v4's apply_filter doesn't call check_content_length (preserved as-is in this commit; tracked separately under Prefilter Quality below).
  - [x] **uplifting v7 migrated** (2026-04-29) - 12/12 self-tests pass; behavior preserved. Same EXCLUSION_PATTERNS + EXCEPTION_PATTERNS_PER_CATEGORY pattern as CD v4 for the 3 pattern-with-exception categories (corporate_finance, military_security, crime_violence); 4th category (pure_speculation) is count-based (speculation_count >= 3 AND outcome_count == 0) and stays as separate class attrs with an inline check after the dict iteration. classify_content_type preserved. ThrivingPreFilterV1 (which subclasses UpliftingPreFilterV7) verified working. Surfaced bug: Dutch `munitie` and similar multilingual patterns lack `\b` boundaries — fire on English substrings like "co-MMUNITIE-s" (preserved as-is; tracked under Prefilter Quality).
  - [x] **investment-risk v6 migrated + class drift fix** (2026-04-29) - 11/11 self-tests pass; behavior preserved. v6 now has its own InvestmentRiskPreFilterV6 class (was a re-export of V5). Backward-compat aliases (InvestmentRiskPreFilterV5 = V6, InvestmentRiskPreFilter = V6) + legacy prefilter()/get_stats() functions kept so existing imports don't break. base_scorer.py updated to reference V6 directly. Data-shape harmonization only — apply_filter stays custom because the source-based flow + matched-pattern reason strings + title-only clickbait don't fit the base pipeline.
  - [x] **nature_recovery v2 migrated** (2026-04-29) - 6/6 self-tests pass; behavior preserved. Single text-pattern category (disaster_no_recovery) with one parallel exception list (recovery framing) lives in EXCLUSION_PATTERNS / EXCEPTION_PATTERNS_PER_CATEGORY. Custom apply_filter retained because: (1) nature-relatedness check runs FIRST in the original order — base's final-check hook runs LAST and would change reason precedence; (2) reason strings are bare category names (not "excluded_<category>"); (3) original v2 doesn't call `check_content_length` — same gap as CD v4 (tracked under Prefilter Quality). Class-name drift V1→V2 deferred to the cleanup batch as planned.
  - [x] **foresight v1 migrated** (2026-04-29) - 10/10 self-tests pass; behavior preserved. Six block categories in EXCLUSION_PATTERNS dict; six positive-signal categories in custom POSITIVE_PATTERN_GROUPS dict (NOT base's POSITIVE_PATTERNS slot — semantics differ: foresight counts distinct *categories* with at least one match, while base's POSITIVE_THRESHOLD counts total matches). apply_filter stays custom for the distinct-categories-fired override + two pass reasons (`passed_positive_signals` for >=3 categories, `passed` for the no-block fall-through) + URL-based domain exclusions.
  - [x] **All 7 production filters now migrated** (2026-04-29) - sustech v3, belonging v1, cultural-discovery v4, uplifting v7, investment-risk v6 (+ class drift fix), nature_recovery v2, foresight v1. Only the deferred class-name drift cleanup batch remains as #52 work.
  - [ ] **Class-name drift cleanup batch** - sustech V2→V3, nature_recovery V1→V2 still pending. (investment-risk v6 own class — DONE 2026-04-29 as part of its #52 migration.) Deferred until remaining migrations done to avoid cross-repo coordination noise (NexusMind tests/unit/test_prefilter.py imports the V2 name).

## Post-#52 Review-Battery Followups

Items surfaced by the multi-agent code review of the migration commits (2026-04-29). Triaged in TODO.md as committed batches.

- [x] **RIP guard repair** (2026-04-29, commit `dd20749`). Code-reviewer caught that the `(?-i:\bRIP\b)` "fix" from `598fa72` was inert in production — `_get_combined_clean_text` lowercases input before pattern matching, so the inline case-sensitive flag had no uppercase chars left to enforce. Real fix: read the raw title directly and run a case-sensitive `\bRIP\b` against it. Title-only. 20/20 tests.
- [x] **POSITIVE_PATTERNS shadow rename** (2026-04-29, commit `7f22d01`). Refactoring agent flagged that belonging v1 + CD v4 shadowed `BasePreFilter.POSITIVE_PATTERNS` with incompatible semantics — a future maintainer setting `POSITIVE_THRESHOLD > 0` would silently activate wrong base behavior. Renamed to `POSITIVE_SIGNAL_PATTERNS` (belonging) / `DISCOVERY_PATTERNS` (CD) and compiled locally.
- [x] **CD v4 truncation** (2026-04-29, commit `e2595dc`). Security audit flagged CD v4 ran ~60 patterns against unbounded body. Added `[:MAX_PREFILTER_CONTENT]` slice in apply_filter + classify_content_type, matching uplifting v7's pattern.
- [x] **uplifting v7 multilingual `\b` boundary sweep** (2026-04-29, commit `d0916f4`). Far broader than the known `munitie`/communities bug — `viol`/`acquisition`/`fusion`/`auteur`/`association` were all unbounded multilingual alternations causing real false-positives on English content. All `\b` anchors added; locked-in test rewritten to expect correct `pure_speculation` outcome.
- [x] **Investment-risk v6 cleanups** (2026-04-29, commit `24af3f8`). `\bfed\b` keyword tightened (no longer fires on "fed up" / "force-fed"), `get_statistics` alias added for cross-filter naming consistency, reason-string raw-regex contract documented at construction sites.
- [x] **CD v4 colonial exception tightening** (2026-04-29, commit `ffffdf9`). Bare `\bcolonial\b` was too broad — bypassed celebrity_art on "colonial mansion auctioned by billionaire" et al. Dropped; surrounding repatriation/restitution/provenance patterns provide adequate coverage.
- [x] **`_check_domain_exclusions` hoist + `_pre_exclusion_check` hook** (2026-04-29, this commit). 4 identical implementations consolidated into `BasePreFilter._check_domain_exclusions` driven by a per-filter `DOMAIN_EXCLUSIONS` dict. Symmetric `_pre_exclusion_check` hook added to `BasePreFilter.apply_filter` (mirrors `_filter_specific_final_check` — useful for filters with a gate-in check that should short-circuit before exclusions). All 4 filter test suites pass; sustech v3 unaffected.
- [x] **ADR-019 first migration: belonging v1** (2026-05-22, commits `ba6b7cb` + `c1ebc98`). Per-category bypass logic (non-obit `has_exc OR pos >= threshold` rule, obit floor `pos >= 2 OR (has_exc AND pos >= 1)`) lifted out of `apply_filter` into `_compound_override_applies` hook. apply_filter shrank ~65 → ~30 LOC. Custom apply_filter retained for the three ADR-019-flagged reasons (URL-domain-first ordering, bare reason strings, case-sensitive `\bRIP\b` raw-title force-fire). 20/20 self-tests green; multi-agent review battery (code-reviewer + refactoring-guide + security-auditor in parallel) returned PASS with three inlinable findings (threshold>0 guard, assert on unhandled category, base docstring drift), all applied in `c1ebc98`.
- [ ] **Extend `_is_excluded` for per-category exceptions + migrate CD v4 / uplifting v7 to base pipeline** - Path narrowed by the belonging migration above: the architecturally-correct next move is the two-step path filed as **#66** (base `EXCLUSION_REASON_PREFIX` class attr + move domain checks into `_pre_exclusion_check`), which unblocks fully-declarative migration for belonging v1, CD v4, uplifting v7, foresight v1, and NR v2 simultaneously. ADR-019's hook signature widening (raw-article access) deferred until a second filter shows up needing case-sensitive raw fields. Original open questions still apply: (a) reason-string convention — covered by the prefix attr in #66; (b) CD v4 missing `validate_article` + `check_content_length` — base would add both, fixing the regression but changing observable behavior; (c) uplifting v7's count-based `pure_speculation` block doesn't fit the dict shape regardless.
- [ ] **Migrate nature_recovery v2 to fully-declarative shape via `_pre_exclusion_check`** - Bundle with #66 (the reason-prefix attr is the prerequisite). NR v2 has the same shape concerns as the post-#52 cluster: bare reason strings, missing `check_content_length`, and order-of-checks differences from the base pipeline.

## Prefilter Quality (Apr 2026)

- [x] **belonging v1 obituary leak (#45)** - 2026-04-28. 5 bypass classes patched (dies-with-verb, procession, vigil, RIP/rest in peace, killed-in-year), `dies at \d` → `\d+` bug fix, override floor on obit branch. Plus `(?-i:\bRIP\b)` follow-up after the case-insensitive false positive on "rip current".
- [x] **sustainability_technology v3 clickbait leak (#46)** - 2026-04-28. CLICKBAIT category added with 6 patterns (you-won't-believe, without-knowing, this-common, you're-probably, X-things-you-didn't, shocking-fact). Pattern 5 bounded `.{0,120}` after review caught cross-sentence FP risk.
- [ ] **cultural-discovery v4 missing content_length check** - Surfaced during #52 migration (2026-04-29). v4's `apply_filter` skips the `check_content_length` call that v3 had — short articles bypass the 300-char minimum and go straight to pattern matching. Likely unintentional regression when v4 was created. Low priority (oracle handles short articles fine; just slightly wasteful), but worth a one-line fix at the next CD version bump.
- [ ] **nature_recovery v2 missing content_length check** - Same gap as CD v4. v2's apply_filter doesn't call `check_content_length`. Likely the original was written without the base helper in mind. Low priority; bundle with the V1→V2 class rename at the next nature_recovery version bump or cleanup batch.
- [x] **uplifting v7 multilingual `\b` boundary leak** - FIXED 2026-04-29. Sweep of NL/DE/FR multilingual alternations added `\b` boundaries to every category in EXCLUSION_PATTERNS + EXCEPTION_PATTERNS_PER_CATEGORY. Big offenders cleaned up: `munitie` no longer fires inside "communities", `viol` no longer matches inside "violence"/"violation"/"viola"/"violin" (was a major crime_violence FP vector on English content), `fusion`/`acquisition` (false corporate_finance), `auteur` (false on "auteur theory"), `association` exception (over-broad bypass). Locked-in test case for "New Technology Could Transform Energy Production" rewritten — now correctly hits `pure_speculation` instead of bug-induced `military_security`. 12/12 tests pass; ThrivingPreFilterV1 subclass verified.
- [x] **Universal obituary detector (#51/#83)** — DONE through enforcement 2026-07-30 session 3: v5 trained (21 FN-delta hard positives), 3-reviewer battery corrected the eval (fair table excl-24; June-increment panel 0.71–0.83, threshold-insensitive), owner adjudicated 14 boundary rows (grief-vs-news rule, flips both sharpened-broad clauses), owner went recall-first ("I just hate obits coming through") → **ENFORCEMENT ON: v5 @ 0.85** (NexusMind `b904edc`, `obituary_blocked` in dedup gate, config-gated rollback via `pipeline.obituary_detector.enforce`). **Enforcement VERIFIED 2026-07-30 20:12 + overnight sanity check PASSED 2026-07-31** (1158→1208→1249 blocked, all-v5 stamps, zero post-enforcement obit leaks in 133 collected). ovr#204 handled ovr-side (editorial gate retired 2026-07-30; sentinel re-derivation ~5% after Aug 6; downstream death-rate 7.9%→2.9% past the boundary). Site carryover (47 flagged shadow-era articles + 2 v5 FNs) washes out by ~Aug 13 — owner accepted, no purge.
- [ ] **Obituary v6 (#85) — PARKED indefinitely (owner, 2026-07-30)**: v5@0.85 enforcement meets the recall-first requirement. Reactivate only if an obit reaches the site (owner flag) or over-blocking visibly hurts the feed. Plan preserved on the issue; b650 env + adjudicated golden set (14 rows) stay ready. **2026-07-31 FN evidence banked for reactivation** (memory/obituary-v4-hypotheses.md addendum 7 + #85 comment): community-mourning class regresses monotonically v3 0.68 → v4 0.44 → v5 0.12 (hard-negative interference); biography-rich obits are a stable all-version blind spot (~0.2–0.3, threshold can't reach).
- [x] **Violence promotion prefilter (#73)** — v1 shadow-deployed NM#274 (2026-07-28). Frozen mpnet-base-v2 + MLP(256,128), 1,957 training samples. OOF precision 0.936, recall 0.550 @0.95. Stamp-only per ADR-004. Next: shadow accumulation → panel validate → v2 retrain with more data (recall is low at 0.55).

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

## 2026-08-02 — Chain 4 measured: two of the previous day's own P0 conclusions overturned

Both P0 issues carried into this session had the **mechanism right and the target wrong**. Neither correction needed new tooling — one came from widening a sample, the other from reconciling a denominator.

- [x] **NM#285 measured, resolved as Option B** (`89f2e5b`, NexusMind main). Same-row full-vs-truncated replay, 4 cycles, n=8,283. Truncation effect: nature_recovery **+0.0000**, solutions **+0.0000**, cultural_discovery +0.0005, belonging +0.0008, uplifting +0.0028, investment_risk +0.0097. **The 0.638–0.649 cluster is NOT a truncation artifact.** Option C declined — its cost saving came almost entirely from the length floor, the one rule we now have evidence against enforcing; Option A buys a rounding error. Shipped instead: every shadow line carries `contract=title+content`, `pre_source_filter=true`, and `INCOMPLETE(inert:url,source)` derived from declared rule containers (not a hardcoded list), verified to flag exactly the four filters with a non-zero measured effect.
- [x] **Real cause of the cluster found.** `nature_recovery v4` and `solutions v6` prefilters are **pure length floors** — both declare `EXCLUSION_PATTERNS = {}` by design (commerce upstream, ADR-004) and their `POSITIVE_PATTERNS` are force-pass overrides, a no-op with nothing to override. Zero lens blocks across 8,283 articles. `expected_pass_rate` **deleted** from both (`3ed47e1`), not corrected — 0.644 is "fraction of articles ≥300 chars", a corpus statistic, not a lens spec.
- [x] **Larger, opposite-signed defect found underneath**: the shadow denominator counts articles `source_filter` discards *after* scoring. investment_risk logs 0.642 while the rate on articles that can reach production is **0.770** — 13× the truncation effect, other direction.
- [x] **LD#92 corrected at n=60/group** (660 articles, deepseek-chat, 0 errors). **uplifting does not replicate** (DiD +0.44, flat at every bar); the defect is in **solutions v6** (DiD −1.13 [−1.74, −0.52], MAE 1.51×). Not small-sample noise: 20k n=15 bootstrap draws give **P(DiD ≤ −1.24) = 0.0000**. Root cause looks like an op-point mix-up — LD#92 used **2.25**, which is *solutions'* op-point; uplifting's is **4.0**. The "924 / 15.0%" figure reproduces exactly at 2.25 and collapses to **117 / 1.9%** at 4.0. "~460 bad articles per 8 cycles" does not survive.
- [x] **NM#286 items 1+2 shipped together** (`23a9068`, NexusMind main): `pipeline.commerce_prefilter.enforce` (default **true** — unlike obituary's false, so a config predating the key cannot silently open a live gate), and `enrich_survivors.py` now reads the same key instead of re-deciding. 920 tests green.
- [x] **LD#86 answered — DO NOT FLIP.** cd's rate matches its declared 0.25, but enforcing it costs **15.5% of surfacing articles** (135/871 over 20 cycles), **19.9% non-English vs 13.0% English** (z≈2.6, p≈0.01), 0% of high tier. `no_cultural_topic_signal` is 86% of the loss. **A matching pass rate and safety-to-enforce are independent properties.**
- [ ] **NEW ROOT for Chain 4 — split the length floor out of the per-filter prefilters into a cap/penalty** (ADR-022 shape). Blocks LD#86 / LD#87 / LD#90 and every NM#284 enforce flip: for four of six filters "enforce the prefilter" is 87–100% "enforce a 300-char length floor".
- [ ] **NM#286 item 3** (violence stamping skipped in single-filter / `--no-dedup` / dedup-exception runs). Verified in code; **live blast radius zero today** (production runs multi-filter, violence `enforce: false`), so it is an audit gap, not admitted violence. Still a hard prerequisite for any violence enforce flip, with LD#82.
- [ ] **Fix `no_cultural_topic_signal` multilingual coverage**, then re-run the identical LD#86 recall check — falsifies whether the language skew is the gate or the corpus.
- [ ] **Retitle/relocate LD#92 to solutions** and correct the op-point in its body.

## 2026-08-01 — NM#281 gate contract + adversarial review of the day's own work

- [x] **NM#281 gate-contract harmonization** — shipped `0fd462b`, **corrected `b85a467`**, deployed. `_commerce_model` / `_violence_model` stamps; `pipeline.violence_promotion.enforce` (default false); `violence_blocked` accounting. Ships inert.
- [x] **Five-lens adversarial battery over the same day's changes** — found 2 blockers, both mine, both invisible to the tests shipped with them:
  1. **The violence gate could never fire.** Placed in `_is_duplicate`, which runs *before* violence stamping; `enforce: true` would have dropped 0 while logging `0 violence`. Commerce/obituary work there only because their preprocessors rewrite the input JSONL first. Fixed: drop moved to `_enforce_violence_promotion()` right after stamping; dead check removed; ordering asserted structurally (AST).
  2. **The shadow loader armed a dead branch.** Leaving `target.prefilter` populated makes `HybridScorer`'s third guard clause truthy — constructing the wrapper flipped a `use_prefilter=True` hybrid to blocking with null scores. Now restored to `None` after capture.
  Also fixed: the `MODEL_VERSION` getattr default was itself the v1-claiming bug the stamp prevents (→ `"unknown"`); shadow errors were dead code so a broken shadow logged nothing; digit-collapsing fragmented the histogram it existed to unify. **978 tests green** (was 969).
- [x] **NM#285 — RESOLVED 2026-08-02.** Measured: truncation is +0.0000 to +0.0097, so the cluster was never an artifact and the ~0.59 reading below was wrong. Option C **declined** on the measurement (see the 2026-08-02 section). Option B shipped `89f2e5b`.
- [x] **NM#286 — items 1+2 shipped 2026-08-02** (`23a9068`); item 3 still open and still blocks any violence enforce flip.

## 2026-08-01 — Cross-repo: ovr#280 cluster_id diagnosis corrected

- [x] **ovr#280 "upstream never sends cluster_id" — REFUTED 2026-08-01.** Measured on the live 12:4x cycle: **7,629 / 16,128 rows (~47%)** carry `nexus_mind_attributes.<lens>.source_quality.cluster_id`, with `corroborating_sources` + `other_sources` on exactly the same rows; present in the 2026-07-22 files too. The diagnosis had sampled `metadata.quality` (FluxusSource's block — its key list `bias_category, credibility_score, source_tier, type_classification` is quoted verbatim in the issue) instead of the per-lens NexusMind block one level deeper. **No NexusMind change needed**; ovr#280's Option A is already done, and the break is downstream between the JSONL and their DB. Posted to ovr#280.
- [ ] **NM#278 is the real fix for the reported symptom** — the five-articles-on-one-story report is a *threshold* problem, not a plumbing one: NexusMind clusters on source text pre-summarization, where cross-outlet paraphrases look far apart; two of the five only converge after ovr.news summarizes. Caution recorded on NM#278: NexusMind *removes* rather than *labels* (32%/run), and anything removed upstream can never surface as an "N sources" badge — so prefer labelling over dropping when re-tuning.

## 2026-08-01 — Post-deploy verification + NM#284 (prefilters never ran in production)

Verification of the 2026-07-31 deploys: **refits and the NM#280 tier gate both green** (closed NM#279, NM#280, LD#74, LD#76). The third check — LD#86's cultural_discovery topic gate — was red, and the cause turned out to be architectural rather than cd-specific: **per-filter prefilters have never run in the production scoring path** since 2026-02-10. See the NM#284 items below and `memory/calibration-history.md` Dead Ends (two new entries).

## 2026-07-31 — LD#76 Calibration Audit (11-agent battery, all verdicts adversarially verified)

Full synthesis: LD#76 issuecomment-5140079896. Headline: **no shared root cause, no scale-collapse anywhere, no retrains needed**. `% norm < 0.5` retired as health metric (≈ 1−base-rate by construction; healthy investment_risk is itself 75% "invisible" by it). Healthy criteria going forward (from ir reference): raw p90 above op-point + populated spread-out MEDIUM+ band + separation intact + anchored fresh fit.

- [x] **uplifting v7 normalization refit** (NM#279) — **EXECUTED 2026-07-31**, **VERIFIED LIVE 2026-08-01**: raw 5.00 → norm ≈5.18 (was ~3.0), `percentile` on 2647/2647 rows. NM#279 closed.
- [x] **belonging v1 normalization refit** (NM#279 / #74) — **EXECUTED 2026-07-31**, **VERIFIED LIVE 2026-08-01**: MEDIUM+ p90 norm 8.71 (n=205 over 3 cycles), visible share 1.03% → 2.68%. NM#279 + #74 closed.
- [x] **NexusMind `_assign_tier` double-cut (NM#280)** — **DEPLOYED 2026-07-31, VERIFIED LIVE 2026-08-01**: `count(tier != low) == count(raw >= op-point)` holds exactly for all six live filters across six consecutive cycles (live from the 07-31 12:5x cycle). Restored visibility: uplifting +196%, ir +70%, belonging +82%, cd +67%, solutions +33%, nr +33%. Caps path untested in production (0 caps applied in these cycles). NM#280 closed.
- [ ] **cd v5 dead prefilter (#86)** — the gate is **correct and now production-validated, but still not enforced**. Verified 2026-08-01 by NM#284 **in-path** shadow measurement on the 12:46 cycle: **0.255 observed vs 0.25 declared (n=2099, full cycle)**, matching the fix's own offline validation (0.245 on 14,923 rows). *(An earlier claim here — "production stamps 2647/2647 pass, replay gives 28.8%" — was retracted: that baseline came from `filtered_*.jsonl`, which only receives `passed_prefilter: true` rows, so it is 100% passers by construction. See NM#284 issuecomment-5151154862.)* **Root cause is not cd-specific: the per-lens rule prefilter has never run in production** (NexusMind `deploy/gpu-server/main.py` L915 `use_prefilter=False` + L1318 `skip_prefilter=True`, since `66582e7`, 2026-02-10). e5 probe, commerce/obituary/violence, and the NM#189 source allowlist all verified running. Filed **NM#284**. #86 closes when NM#284 stage 3 flips cd to enforcement — the fix itself needs no further work.
- [x] **NM#284 stage 1 — shadow measurement** — **IMPLEMENTED + DEPLOYED + VERIFIED LIVE 2026-08-01** (`cd4fc6d` + `5d53774`, deployed ~11:59 CEST). `ProductionScorer` loads each filter's prefilter via the `_load_prefilter` hook (without flipping `use_prefilter`, keeping evaluation and enforcement separate levers) and logs observed vs declared pass rate. Enforces nothing; no schema change. Rollback `NM_FILTER_PREFILTER_SHADOW=0`. First cycle (12:46): **cd 0.255 vs declared 0.25 — LD#86 gate validated in production**; uplifting 0.525 vs 0.20; solutions 0.591 vs 0.20; ir 0.589 (no declared rate). Two defects the first live run exposed and fixed: drift judged at n=1 (smoke test scores one article/filter → six false "gate appears inert" alarms; now `MIN_SHADOW_SAMPLE=50`), and `expected_pass_rate: ~0.25` parsed as a YAML *string* and silently dropped.
- [ ] **NM#284 stage 1b — per-row shadow stamps into the JSONL**: needs `prefilter_shadow_pass` / `prefilter_shadow_reason` plumbed through gpu-server `main.py` (Pydantic `FilterScoreResult` drops unknown keys at the service boundary) → `src/scoring/gpu_client.py` → the `analysis` dict in `scripts/main.py`. Blocked on unrelated uncommitted WIP in `scripts/main.py` (image-classifier thresholds, NM#282) — staging it would sweep that in. Log-based measurement is sufficient for the enforcement decision, so this is a convenience, not a blocker.
- [ ] **NM#284 stage 2 — global short-content gate before fan-out** (the actual speed win): `content_too_short` blocks the *identical* 853 articles for every filter — ~25% of all model inferences, screened six times over. Belongs upstream with commerce/obituary as one stamped, config-gated drop point (ADR-022), not as six per-filter flips. ~32% of production articles are below the length floor and currently scored by Gemma-3-1B anyway.
- [ ] **NM#284 stage 3 — per-filter enforcement flip**, once a few cycles of shadow data exist. cd is the only filter whose observed rate currently matches its declared one, and it is also the one LD#86 needs. Op-point / normalization re-derivation for affected filters is downstream of the flip (gates #87).
- [ ] **cd v6 lens fidelity scope (#87)** — ccc 0.25 weight ceiling (mean 0.64), 27% off-lens hard science in visible band, "4.5 display threshold" vs shipped 4.0 unreconciled. Design ticket; not urgent. The 3.5 op-point proposal was REFUTED (sampling artifact) — any re-derivation needs a randomized [3.0,4.5) sample **after NM#284 lands**: the v5 op-point and normalization CDF were both fitted on a distribution still containing the ~71% the prefilter should have removed.
- [x] **#75 CLOSED as measurement artifact 2026-07-31** (owner confirmed) — nature_recovery v4 is healthy.
- [ ] **Lens harmonization program (#90)** — owner directive 2026-07-31: bring all lens filters to the successful template (op-point at the distribution, fresh anchored fit, working positive gate, hybrid + stamps, ADR-021 gate) AND rename filters to exact lens names at version bumps (uplifting→thriving, cultural_discovery→discovery, nature_recovery→recovery).
- [ ] **Hygiene batch** — emit `stage_used` into row attrs; document nr runtime stage-1 threshold 0.75 (config.yaml says 3.225, inert); fix stale ir config tiers (3.0 vs live 4.0); note nr raw HIGH tier 7.0 > calibrated ceiling 6.8 (structurally dead).
- [ ] **NM#231 re-measure after uplifting refit** — non-English under-scoring is real but secondary; size the residual model-side gap before considering v8 work.
- [ ] **Drift guard** — uplifting violated the >20%-relative-pass-rate refit trigger by an order of magnitude for ~4 months, undetected; the prefilter kill (NM#284) hid for ~6 months the same way. Add per-cycle pass-rate logging or a scheduled drift check covering both normalization freshness and declared-vs-observed prefilter pass rate (owner question).

## 2026-07-27 Session — Small LD Issues Closed

- [x] **LD#49** — Remove 6 broken/superseded filter version dirs (`3e1ccec`). −61,314 lines.
- [x] **LD#68** — Add per-dim `description` field check to `verify_filter_package.py` (`c2ab571`).
- [x] **LD#63** — Branded/sponsored URL path blocking in uplifting v7 prefilter (`623ea51`).
- [x] **LD#57** — Schema gate for `source_filter:` block. Already implemented; closed.

## #52 belonging v1 migration notes (2026-04-29)

Belonging is the second prefilter migrated to ADR-018 declarative shape.
Diverged from sustech v3's "fully declarative" template in two ways:

1. **Data shape only.** Exclusion patterns moved into `EXCLUSION_PATTERNS`
   dict (compiled once by base `__init__`); per-category counts dropped from
   `get_statistics()` and rebuilt from the dict. Iteration order preserved.
2. **Custom apply_filter retained.** Belonging uses per-category
   positive-signal thresholds (3/3/3/2/3/2/special), not BasePreFilter's
   binary `OVERRIDE_KEYWORDS` bypass. Plus URL-based domain exclusions and
   the obit `pos>=1`-floor-when-exception-present rule. None of that fits
   the standard `apply_filter()` pipeline; ADR-018 explicitly allows
   "custom form" for this. The harmonization is at the *data* layer; the
   *control* layer stays specialized.

`POSITIVE_PATTERNS` class attr was kept (shadows `BasePreFilter.POSITIVE_PATTERNS`)
so base compiles it into `_compiled_positives`. `POSITIVE_THRESHOLD` stays at
0, so base's `_has_override` never reads it — belonging consumes the
compiled list directly via `count_pattern_matches`. Documented at the class
attr.

Pattern preservation verified by counts (9/7/9/9/7/6/11/6 exclusion
categories; 10 exceptions; 12 positives; 9 multilingual positives — all
identical to baseline) and 19/19 self-test pass.

No downstream consumers reference the renamed private attrs (verified via
grep across the repo); only the public class symbol + `apply_filter()`
contract are used by `base_scorer.py` and `verify_belonging_v1.py`.

## #52 cultural-discovery v4 migration notes (2026-04-29)

CD v4 is the third migrated prefilter. Same partial-declarative shape as
belonging — exclusion data harmonized, custom `apply_filter` retained.
But the divergence from base differs:

1. **Per-category exception lists.** Each exclusion category
   (appropriation_debate, political_conflict, tourism_fluff, celebrity_art)
   has its own escape-hatch list — celebrity_art has philanthropy /
   repatriation exceptions, political_conflict has reconciliation / peace
   exceptions, etc. BasePreFilter's single `OVERRIDE_KEYWORDS` slot is
   global; CD's exceptions are category-scoped. Modeled with a parallel
   `EXCEPTION_PATTERNS_PER_CATEGORY` dict keyed by exclusion-category name,
   compiled in `__init__` into `_compiled_exceptions_per_category`.

2. **classify_content_type method preserved.** Distinct from apply_filter
   — used (currently only by self-tests, but kept for API stability) to
   tag articles as `cultural_discovery` (>=2 positive boost matches) or
   one of the four exclusion categories or `general`. Rewritten on the
   new dict-based structure.

3. **CULTURAL_DISCOVERY_BOOST_PATTERNS → POSITIVE_PATTERNS.** Same trick
   as belonging: rename so base's `__init__` compiles them into
   `_compiled_positives`. POSITIVE_THRESHOLD stays at 0, so base's
   `_has_override` never reads them — only `classify_content_type` does.

4. **Surfaced bug: missing content-length check.** v3's `apply_filter`
   called `check_content_length` first; v4's does not. Looks like an
   unintentional regression when v4 was created. **Preserved as-is in
   this migration commit** (scope: zero behavior change). Tracked above
   under "Prefilter Quality" as a separate one-line fix at next CD bump.

Behavior preservation verified by 10/10 self-test pass plus identical
pattern counts (11/14, 17/12, 15/14, 15/14 across the four categories;
12 positives; 8/4/6 domain counts).

No downstream consumers (verified via grep): only `base_scorer.py`
references `CulturalDiscoveryPreFilterV4` as a class symbol +
`apply_filter()` call. Older CD versions (v1/v2/v3) keep their old
attr names internally — no cross-version import.

Next: uplifting v7 (flat-list-per-category, pattern-pair override — no count).

## #52 uplifting v7 migration notes (2026-04-29)

Uplifting v7 is the fourth migrated prefilter. Same shape as CD v4 for 3 of
4 categories, with one extra wrinkle: a count-based block.

1. **Three pattern-with-exception categories.** corporate_finance,
   military_security, crime_violence — all use the
   `EXCLUSION_PATTERNS` + `EXCEPTION_PATTERNS_PER_CATEGORY` pair, identical
   to CD v4's structure.

2. **One count-based block (pure_speculation).** Doesn't fit the
   pattern-with-exception shape. Outcome-evidence patterns are a parallel
   *count* check, not a per-pattern exception. Kept as separate
   `SPECULATION_PATTERNS` / `OUTCOME_EVIDENCE_PATTERNS` class attrs;
   inline check after the exclusion-dict iteration:
   `speculation_count >= 3 AND outcome_count == 0`.

3. **classify_content_type preserved.** Has a custom first-check ordering:
   "peace_process" wins when both military_security pattern AND its
   exception fire (e.g. military buildup article that's actually a peace
   accord). Standard category iteration follows. Speculation classification
   uses a looser threshold (>=2 / <=1) than apply_filter (>=3 / 0).

4. **Subclass ThrivingPreFilterV1 verified.** `filters/thriving/v1/prefilter.py`
   inherits from UpliftingPreFilterV7 with only a VERSION override. Public
   API preserved, so the subclass still works post-migration (verified with
   a smoke test exercising all 4 categories).

5. **Surfaced bug: multilingual `\b` boundary leak.** Dutch `munitie`
   (without `\b`) matches inside English "communities". Pre-existing v7
   FP — preserved here, tracked separately under Prefilter Quality.
   Same bug shape as the RIP/rip-current case (#45). Audit all 3
   multilingual exclusion lists at next uplifting version bump.

Behavior preservation verified by 12/12 self-test pass plus identical
pattern counts (21/11, 19/18, 37/25 across the three pattern-with-exception
categories; 7 speculation; 6 outcome-evidence; 8/4/6 domain counts).

No additional downstream consumers (verified via grep): only
`base_scorer.py` references `UpliftingPreFilterV7` directly, plus
`thriving/v1/prefilter.py` via inheritance — neither reaches into private
attrs.

Next: investment-risk v6 (re-exports v5; needs own class — class-name drift
fix is part of the migration).

## #52 investment-risk v6 migration notes (2026-04-29)

Investment-risk is the fifth migrated prefilter and the most structurally
divergent so far. Two things landed in this commit:

1. **Drift fix** — v6 was a thin re-export of v5 (importlib trick because
   the hyphen in `investment-risk` blocks normal imports). v6 now has its
   own `InvestmentRiskPreFilterV6` class. Backward-compat aliases
   (`InvestmentRiskPreFilterV5 = V6`, `InvestmentRiskPreFilter = V6`) plus
   legacy `prefilter()` / `get_stats()` functions preserved so existing
   imports keep working — including v6/base_scorer.py's import via
   importlib (now updated to call `InvestmentRiskPreFilterV6` directly).

2. **Migration to declarative shape** — but only data-shape harmonization;
   apply_filter stays custom for three reasons:
     - **Source-based filtering** runs against `source` / `source_type` /
       `id` fields, not URL or text. Has its own early-return flow:
       allowed-source -> pass, investment-keyword -> pass, blocked-source
       -> block, all before content patterns.
     - **Reasons include matched-pattern info** —
       `allowed_source:reuters`, `investment_keyword:recession`,
       `blocked_source:github`. The base pipeline's `excluded_<category>`
       shape would lose this signal.
     - **Clickbait operates on title only**, not combined text. Stays as
       a separate class attr with its own check below the EXCLUSION_PATTERNS
       iteration.

Three text-pattern categories did get the dict treatment:
fomo_speculation (8 patterns, no exceptions), stock_picking (6 patterns,
12 macro-context exceptions), affiliate_conflict (4 patterns, no
exceptions). The macro_context list is the only per-category exception
this filter has — modeled as `EXCEPTION_PATTERNS_PER_CATEGORY['stock_picking']`.

`(True, "default_allow")` and `(True, "passed")` are intentionally
distinct — investment-risk reports the *reason* an article passed, not
just the fact that it did. Default-allow means "no source/keyword/pattern
fired, falling through to the philosophy: when in doubt, score it."

Behavior preservation verified by 11/11 self-test pass plus identical
pattern counts (19 blocked sources, 25 allowed, 30 keywords; 8/0, 6/12,
4/0 across pattern-with-optional-exception categories; 5 clickbait).

Next: nature_recovery v2 (inline list in method form — simplest of the
remaining; class-name drift fix V1→V2 deferred to the cleanup batch).

## #52 nature_recovery v2 migration notes (2026-04-29)

Sixth migrated prefilter. Simplest of the lot — single text-pattern
category with a single recovery-pattern exception, plus a permissive
nature-relatedness gate.

The structure looked like a clean fit for *fully declarative* shape (sustech
v3 style — base apply_filter + `_filter_specific_final_check` for the
nature gate). But three behavior-preservation concerns ruled that out:

1. **Order**: nature-relatedness check runs FIRST today; base pipeline
   would run it LAST (via `_filter_specific_final_check`). Articles that
   are both off-topic and disaster-themed would change blocking reason
   from `not_nature_topic` to `excluded_disaster_no_recovery` — a
   user-observable change, no matter how rare.
2. **Reason strings**: current returns are bare (`"disaster_no_recovery"`,
   `"not_nature_topic"`); base prepends `excluded_<category>`.
3. **Content-length gap**: current v2 doesn't call `check_content_length`
   (same gap as CD v4 — see Prefilter Quality follow-ups). Base pipeline
   would add the call — also a behavior change.

Settled on data-shape harmonization with a custom apply_filter, same
strategy as belonging / CD v4 / uplifting v7 / investment-risk. The
disaster category fits the EXCLUSION_PATTERNS + EXCEPTION_PATTERNS_PER_CATEGORY
shape cleanly even though it's the only category in this filter.

Class-name drift (file v2 / class V1 / VERSION="1.0") preserved as planned
— part of the deferred cleanup batch alongside sustech V2→V3, gated on
NexusMind cross-repo coordination since their `tests/unit/test_prefilter.py`
imports the V1 name.

Behavior preservation: 6/6 self-test pass. Pattern counts: 33 nature
keywords (duplicate `deforestation` in the original list preserved
verbatim), 1 disaster regex, 1 recovery-exception regex.

Next: foresight v1 (count-based override — `POSITIVE_THRESHOLD = 3`).

## #52 foresight v1 migration notes (2026-04-29)

Seventh and final per-filter migration. Foresight's "count-based override"
turned out to NOT fit BasePreFilter's POSITIVE_THRESHOLD slot — the
semantics differ:

- Base `POSITIVE_THRESHOLD`: bypass when `sum(p.findall() for p in
  POSITIVE_PATTERNS) >= POSITIVE_THRESHOLD` — total match count.
- Foresight v1: bypass when `count(group_name for group in
  POSITIVE_PATTERN_GROUPS if any pattern in group matches) >= 3` —
  distinct categories with at least one hit.

A single repeated keyword in one foresight category counts as 1, not as N.
Migrating to base's semantics would have changed the bypass behavior —
some articles with 3+ matches all in one category would start bypassing
where they previously didn't, and vice versa.

Settled on: data-shape harmonization with a **custom slot**
(`POSITIVE_PATTERN_GROUPS`, not `POSITIVE_PATTERNS`) so the difference is
visible at the class definition. Six block categories DID move into
`EXCLUSION_PATTERNS` cleanly (no per-category exceptions). Custom
apply_filter retained for the distinct-categories-fired logic, the two
pass reasons (`passed_positive_signals` vs `passed`), and URL-based
domain exclusions.

Behavior preservation: 10/10 self-test pass; pattern counts
bit-for-bit identical to baseline (4/4/3/4/3/3 block; 8/4/4/6/3/15
positive; 8/5 domain).

## #52 retrospective (2026-04-29) — what we learned

**All 7 production filters now share a consistent EXCLUSION_PATTERNS data
shape**, even though only sustech v3 ended up using BasePreFilter's full
declarative pipeline. The other 6 retained custom apply_filter for one
or more of these reasons:

| Reason for custom apply_filter | Filters affected |
|---|---|
| URL-based domain exclusions | belonging v1, CD v4, uplifting v7, foresight v1 |
| Per-category exception lists | CD v4, uplifting v7, investment-risk v6 |
| Per-category positive-count thresholds | belonging v1 |
| Count-based block (not pattern-with-exception) | uplifting v7 (pure_speculation), foresight v1 (positive_categories) |
| Source-based filtering on non-URL field | investment-risk v6 |
| Matched-pattern reason strings (`allowed_source:reuters`) | investment-risk v6 |
| Title-only checks | investment-risk v6 (clickbait), belonging v1 (#45 obit) |
| Reason-precedence ordering depends on flow | nature_recovery v2 |
| Bare reason strings (no `excluded_` prefix) | belonging v1, CD v4, uplifting v7, NR v2, foresight v1 |
| Distinct pass reasons (`passed_positive_signals` etc.) | foresight v1 |
| Existing `check_content_length` gap to preserve | CD v4, NR v2 |

**The harmonization is in the *data*, not the *control flow*.** This is
the right call given the genuine variety of filter logic. ADR-018
explicitly permits "custom form" precisely for this case. Future filter
authors can:

1. Read EXCLUSION_PATTERNS to see what each filter blocks.
2. Read EXCEPTION_PATTERNS_PER_CATEGORY (or POSITIVE_PATTERN_GROUPS, or
   the filter-specific override slot) to see what pulls articles back through.
3. Read apply_filter for the specific control flow this filter needs.

That third step is no longer about hunting compiled-regex attributes and
helper methods scattered through the file.

**Surfaced bugs (preserved for zero-behavior-change scope; tracked under
Prefilter Quality):**
- CD v4 missing `check_content_length` call (regression vs v3).
- nature_recovery v2 missing `check_content_length` call.
- uplifting v7 multilingual `\b` boundary leak (Dutch `munitie` matches
  inside English "co-MMUNITIE-s"; same bug shape as RIP/rip-current #45).

**Remaining #52 work:**
- Class-name drift cleanup batch: sustech V2→V3, nature_recovery V1→V2.
  Deferred until cross-repo coordination with NexusMind (whose
  `tests/unit/test_prefilter.py` imports the V2 / V1 names).
- The three Prefilter Quality follow-ups above can be picked up with the
  next version bump on each filter.

