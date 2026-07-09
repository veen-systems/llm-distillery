# LLM Distillery - Roadmap

## Now (Current Sprint) — Priority: ovr.news tabs

- **belonging v1 → ovr.news** - Add Belonging tab (filter deployed, frontend work only). Prefilter obituary leak patched 2026-04-28 (#45).
- **nature_recovery v2** - Deployed (val MAE 0.53 calibrated, Recall@20 0.70) → ovr.news Recovery tab (normalization + frontend)
- **nature_recovery v4** - Ground-truth gate PASSED 2026-07-09 (beats v2 on every metric vs held-out DeepSeek: precision 0.85 vs 0.61, recall 0.67 vs 0.60 at op-point 3.75). #70 protection scope + multilingual prefilter fix (21.6%→0%) + recall-first e5 probe. Deploying (first checkpoint, scale 2.0). Recall is the soft axis → v5 active-learning enrichment (#71). Oracle stays DeepSeek for conservative *bias*.
- **sustainability_technology v3** - Prefilter clickbait leak patched 2026-04-28 (#46). v4 retraining still on the cards for classifier-side off-topic (Eiffel Tower etc.)
- ~~**thriving v1**~~ - PARKED indefinitely. Uplifting v7 stays as Thriving tab. Orthogonal lens design caused bimodal distribution (ADR-015); a fixed v2 would just be uplifting v7 again
- ~~**foresight v1**~~ - PARKED 2026-04-16 (#43). Captures governance solutions, not foresight. Lens folding into broadened Solutions at sustainability_technology v4.

## Next (Coming Soon)
- **cultural-discovery v5** - Active learning enrichment complete (473 articles), training data ready (8,502). Train on gpu-server.
- ~~**nature_recovery v2 normalization**~~ - Deployed 2026-04-28 (n=1,397 v2 articles; `fit_normalization.py` got `--filter-version` flag)
- **Prefilter structure harmonization (#52)** - Filed 2026-04-28. 7 filters, 5 override-mechanism shapes, 3 with class/version drift. ~12-16h, per-filter migration. Blocks clean per-filter consumption for #51's universal detectors.
- **Universal obituary detector (#51)** - Filed 2026-04-28, simplified to universal block + tunable threshold. Extends ADR-004 (no supersede). ~2-3 weeks calendar (labeling-bound).
- **Breakthroughs lens** - Best candidate for new ovr.news tab. Blocked on science journalism full-text harvesting (NexusMind#143).
- ~~**future-of-education v1**~~ - DROPPED: education stories covered by Breakthroughs (research)
- **ai-engineering-practice v2** - Oracle scoring + training (not ovr.news, separate product)

## Later (Backlog)

- **Energy-efficient inference (#24)** - CPU-viable scoring for when GPU access ends
  - Naive PyTorch INT8 rejected (MAE +0.63, see `docs/experiments/`)
  - Next: ONNX Runtime calibrated INT8, or smaller base model (SmolLM-360M)
- **Prefilter strategy documented** - ADR-004: Commerce is only universal noise
- **seece filter** - Corporate excellence (not ovr.news)
- **sustainability_economic_viability / sustainability_policy_effectiveness** - Sustainability sub-dimensions (not ovr.news)
- **Batch processing pipeline** - High-volume scoring infrastructure
- **Production monitoring** - Accuracy drift detection

## Completed

### Filters
- [x] **nature_recovery v1** - Deployed on HuggingFace Hub (private) - 2026-03
  - Val MAE: 0.540 (calibrated: 0.507), Gemma-3-1B
  - 3,280 training articles (screen+merge via ADR-011 embedding screening)
  - 6 dimensions, probe MAE 0.50 (best across all filters)
- [x] **belonging v1** - Training complete - 2026-03
  - Val MAE: 0.534 (calibrated: 0.489), Gemma-3-1B
  - 7,370 training articles (5K scope candidates + 2.5K random negatives, deduplicated)
  - 6 dimensions, isotonic calibration fitted on 738 val articles
- [x] **uplifting v6** - Deployed on HuggingFace Hub (private) - 2026-02
  - Val MAE: 0.673 (v5 was 0.688), Gemma-3-1B, 12% faster inference
  - Data sculpting: active learning (495 MEDIUM enrichment) + label correction (57 crime articles capped)
  - See `filters/uplifting/v6/README.md` for full documentation
- [x] **sustainability_technology v3** - Deployed on HuggingFace Hub (private) - 2026-02
  - Val MAE: 0.734 (calibrated test: 0.724), Gemma-3-1B (was Qwen2.5-1.5B in v2)
  - 10,608 training articles (v2 10,039 + 569 active learning enrichment)
  - Hybrid probe: MAE 0.91, threshold 1.25
  - All 3 inference paths: local, Hub, hybrid
- [x] **cultural-discovery v5** - Deployed on HuggingFace Hub + gpu-server (private) - 2026-05-31
  - Val MAE: 0.697 (v4 was 0.74), Gemma-3-1B
  - 8,551 training articles, DeepSeek V4 Flash oracle (first non-Gemini lineage in production)
  - F/G/H/I/K soft-penalty flags (historical_harm_reckoning, commemoration, perpetrator, decline, launch) resolve llm-distillery#62 discovery-lens leakage
  - Provisional reference example for ADR-020 (multi-oracle calibration + agent judging)
- [x] **cultural-discovery v4** - Superseded by v5 - 2026-02
  - Calibrated test MAE: 0.74 (v3 was 0.77), Gemma-3-1B (was Qwen2.5-1.5B)
  - 8,029 training articles (v3 7,827 + 202 active learning enrichment)
  - Hybrid probe: threshold 1.25, 3% FN, 1.51x speedup
  - All 3 inference paths verified (local, Hub, hybrid)
- [x] **cultural-discovery v3** - Superseded by v4 - 2026-01
  - Val MAE: 0.77, 7,827 training articles (merged random+screened)
- [x] **uplifting v5** - Production ready, deployed HuggingFace Hub (private) - 2024-11
  - Val MAE: 0.68, 10K training articles
- [x] **sustainability_technology v1** - Deployed HuggingFace Hub - 2024-11
  - Test MAE: 0.690
- [x] **sustainability_technology v2** - Complete (prefilter + model) - 2025-01
  - Val MAE: 0.71, 7,990 training samples
  - Prefilter: FP Block 88.2%, TP Pass 89.0%
- [x] **investment-risk v6** - Deployed on HuggingFace Hub (private) - 2026-02
  - Val MAE: 0.497 (calibrated: 0.465), Gemma-3-1B (was Qwen2.5-1.5B in v5)
  - 10,448 training articles (v5 10,198 + 250 active learning enrichment)
  - Tier simplification: RED/YELLOW/GREEN/BLUE/NOISE -> high/medium_high/medium/low
  - Hybrid probe: MAE 0.557, threshold 1.50
  - All 3 inference paths: local, Hub, hybrid
- [x] **investment-risk v5** - Superseded by v6 - 2024-12
  - Test MAE: 0.484, 10K training articles

### Research
- [x] **Quantization feasibility** - PyTorch dynamic INT8/FP16 on Gemma-3-1B - 2026-03
  - INT8: 2.6x faster, 3.3x smaller, but MAE +0.63 (unusable)
  - FP16: NaN on CPU, 4x slower (no native fp16 ALUs)
  - Naive quantization rejected; calibrated (ONNX) or smaller models needed
- [x] **Context length experiments** - 1024/2048/head+tail strategies - 2025-01
  - head+tail (256+256) deployed to production
  - See `docs/IDEAS.md` for full results
- [x] **Embedding vs fine-tuning** - Confirmed fine-tuning beats probes by ~18% MAE
  - Probes fast enough for Stage 1 screening in hybrid pipeline
- [x] **Stage 2 model comparison** - Gemma-3-1B adopted as default - 2026-02
  - Beats Qwen-1.5B on both uplifting (MAE 0.652 vs 0.660) and cultural-discovery (0.743 vs 0.755)
  - 8% faster inference, 38% faster training, fewer parameters (1B vs 1.5B)

### Hybrid Inference Pipeline
- [x] **Shared infrastructure** - embedding_stage.py, hybrid_scorer.py - 2026-02
- [x] **Uplifting v5 integration** - probe + inference_hybrid.py - 2026-02
- [x] **Threshold calibration** - 24K articles, threshold 4.5, 2.09x speedup - 2026-02
- [x] **Stage 2 model decision** - Gemma-3-1B adopted as default - 2026-02
- [x] **Generalize to all filters (Phase A)** - inference_hybrid.py + probe dirs + calibration fix for 3 filters - 2026-02
- [x] **Train probes + calibrate (Phase B)** - e5-small MLP probes for all 3 filters - 2026-02
  - sustainability_technology v2: MAE 0.707, threshold 1.25, 1.2% FN, 1.25x
  - investment-risk v5: MAE 0.497, threshold 1.50, 0.8% FN, 1.07x
  - cultural-discovery v3: MAE 0.609, threshold 1.25, 0.0% FN, 1.52x
- [x] **Cultural-discovery v4 probe** - Retrained for Gemma-3-1B model - 2026-02
  - Probe MAE 0.87, threshold 1.25, 3% FN, 1.51x speedup
- [x] **Sustainability_technology v3 probe** - Trained for Gemma-3-1B - 2026-02
  - Probe MAE 0.91, threshold 1.25 (to be calibrated with production data)
- [x] **Investment-risk v6 probe** - Trained for Gemma-3-1B - 2026-02
  - Probe MAE 0.557, threshold 1.50

### Hybrid Deployment
- [x] **Deploy hybrid inference to NexusMind** - 2026-03
  - embedding_stage.py, hybrid_scorer.py, inference_hybrid.py synced to NexusMind repo
  - Probe directories for all 4 production filters deployed

### Score Calibration
- [x] **Isotonic regression calibration** (ADR-008) - 2026-02
  - Per-dimension isotonic regression corrects MSE score compression at inference time
  - Shared library: `filters/common/score_calibration.py` (fit, apply, save, load)
  - CLI tool: `scripts/calibration/fit_calibration.py` (works for any filter)
  - Applied to uplifting v6: val MAE 0.673 -> 0.653, tier distribution closer to oracle
  - Applied to cultural-discovery v4: test MAE 0.77 -> 0.74 (+4.4%)
  - Applied to sustainability_technology v3: test MAE 0.725 -> 0.724 (+0.2%)
  - Applied to investment-risk v6: val MAE 0.497 -> 0.465 (+6.5%)
  - Backwards compatible: scores pass through unchanged if `calibration.json` absent

### Filter Harmonization
- [x] **Harmonize filters: llm-distillery as single source of truth** - 2026-02
  - Fixed drift between llm-distillery and NexusMind (sadalsuud + gpu-server)
  - base_prefilter.py: thread-safe commerce detector loading (threading.Lock)
  - investment-risk v5: unified source-based + content-pattern prefilter, removed academic blocking
  - uplifting v5 + cultural-discovery v3: deployed (academic domain exclusion already removed)
  - All production prefilters verified identical across 3 locations

### Code Quality
- [x] **deploy_to_nexusmind hardening** - 2026-05-23 (commits `4cf75dd` + `dd11727`)
  - Refuse-on-dirty pre-flight check + `--force-dirty` escape hatch
  - Explicit `git add $FILTER_PATH filters/common/` replaces blanket `git add -A`
  - Closes origin-contamination hazard discovered during 2026-05-22 belonging deploy
  - Printed server-pull instructions corrected to match actual deploy flow
- [x] **ADR-019 hook-only consolidation for belonging v1** - 2026-05-22 (commits `ba6b7cb` + `c1ebc98`)
  - Per-category bypass logic moved into `_compound_override_applies` Template Method hook
  - apply_filter ~65 → ~30 LOC; 20/20 self-tests still green
  - Multi-agent review battery returned PASS (code-reviewer + refactoring-guide + security-auditor)
  - Follow-up #66 filed: fully-declarative path via base `EXCLUSION_REASON_PREFIX` attr + domain in `_pre_exclusion_check`
- [x] **HF Hub model-card relicensing MIT → EUPL-1.2** - 2026-05-22 (commits `fb67d05` + `41d2108`, #65)
  - Source-side: `upload_to_huggingface.py:28` template fixed
  - Hub-side: all 14 `jeergrvgreg/*` repos updated via one-shot script
- [x] **Extract FilterBaseScorer** (issue #10) - 2026-02
  - Shared abstract base class in `filters/common/filter_base_scorer.py`
  - Deduplicated ~1,200 lines across 4 production base_scorer.py files
  - Standardized gatekeeper naming to `GATEKEEPER_*` across all filters
  - New filters need ~55 lines instead of ~450
- [x] **Code quality sweep** (issues #11-#19) - 2026-02
  - Extract `load_lora_local()` / `load_lora_hub()` into `model_loading.py` (#11) — 8 inference files simplified to 3-line delegations
  - Pin all dependency upper bounds (#16), harden batch_scorer path validation (#18)
  - Add pickle integrity verification with SHA-256 hashes (#15)
  - Fix calibration script hardcoded 3-tier scheme (#14), stale Qwen refs (#12), model card template (#13)
  - Update stale tests to v6 (#17), remove debug print + deprecated method (#19)
  - Net: -314 lines across 20 files
- [x] **Close backlog issues** (#2, #9, #20) - 2026-02
  - #2 (score all articles): addressed by hybrid inference pipeline; remaining work is NexusMind config
  - #9 (LLMBase API): closed as not planned — NexusMind is primary target
  - #20 (config.yaml single source of truth): closed as not planned — Python constants preferred after #10

### Infrastructure
- [x] **Ground truth generation pipeline** - 2024-11
- [x] **Oracle output discipline** - Scores only, tier in postfilter - 2024-11
- [x] **Data preparation pipeline** - Stratified splits - 2024-11
- [x] **Training data validation** - Quality checks - 2024-11
- [x] **Training script** - Qwen2.5-1.5B + LoRA working - 2024-11
- [x] **Prefilter evaluation framework** - For sustainability_technology - 2025-01

---

*Last updated: 2026-05-23*
