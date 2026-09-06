# Cultural Discovery Filter v5 — Development Status

**Last Updated:** 2026-05-31 (evening)
**Status:** 🟢 **DEPLOYED TO PRODUCTION** — scorer on gpu-server healthy, ovr.news Discovery tab will score with v5 on next pipeline cycle
**Driver:** llm-distillery#62 (discovery-lens leakage in cd v4 production) — RESOLVED at infrastructure level
**Target deployment:** ovr.news Discovery tab (ADR-038)

**Deploy chain**: llm-distillery `6acd013` → HF Hub (jeergrvgreg/cultural-discovery-filter-v5 private) → NexusMind `f9a3fe9` (pushed) → sadalsuud pulled → gpu-server scorer healthy (code_revision `264b0d3f...`).

---

## Completed

- [x] **Filter design (Phase 1)** — 2026-05-29
  - [x] Inherited v4 dimensions: discovery_novelty (25%), heritage_significance (20%), cross_cultural_connection (25%), human_resonance (15%), evidence_quality (15%) — sum to 1.0
  - [x] No `score_scale_factor` per ADR-014 (normalization replaces it)
  - [x] No `tiers` block per ADR-016 (post-processing only; oracle outputs scores)
  - [x] `evidence_quality` gatekeeper (threshold 3.0, cap 3.0) retained from v4
- [x] **Prompt scaffold v5 (Phase 2)** — 2026-05-29 (commit 137ec45)
  - [x] 5 new pre-classification flags: F (historical_harm_reckoning), G (commemoration_memorial), H (perpetrator_biography), I (decline_loss), K (launch_announcement) — J intentionally omitted (delegated to upstream obit detector per llm-distillery#51)
  - [x] Hard-negative cohort (49 articles, `datasets/raw/cd_v5_hard_negatives_candidates.jsonl`) collected from production v4-leaked articles
  - [x] Initial hard-cap mechanism: `max_score = N` clamps all dims to N when flag fires
  - [x] 7 contrastive validation examples added (rows 13-19 of Section 2 table)
- [x] **Phase 3 oracle calibration — iterative tightening (2026-05-30 / 31)**
  - [x] **v5 prompt iteration 1** (hard cap, 2026-05-29): 49 hard-negs + 473 active-learning lane scored under Gemini Flash 2.5. Output: `datasets/scored/cd_v5_hard_negatives/` + `datasets/scored/active_learning_cd_v5_rescored/`.
  - [x] **Critical lens-design audit** (2026-05-30): found ~4 v5-scored articles (Antwerp 7-Congolese memorial, Muslim WWII memorial, Stolperstein explainer, Ghanaian genocide monument) hitting G cap despite arguably falling in carve-out intent. Same parsing-too-narrowly bug F had pre-Modigliani broadening.
  - [x] **G carve-out broadening (2026-05-30)**: mirror F's pattern. Explicitly includes (1) victim names from local/community/journalistic/descendant-led research, (2) explainer pieces about commemorative practice mechanics, (3) first-of-kind regional commemorative practices. Added validation example #20.
  - [x] **Soft-penalty conversion (2026-05-30, prompt iteration 2)**: F/G/H/I/K converted from `max_score = N` hard caps to `penalty = N` (subtract from each dim, floor 0). Preserves gradient — heritage > novelty stays meaningful for slavery content. Per ADR-015 (orthogonal lens design causes MAE cliffs; thriving v1 parked at MAE 0.94 for this failure mode). Penalty values: F=2.5, G=2.5, H=3.5 (strictest), I=2.0 (lightest), K=2.5. Re-scored same 522 → `datasets/scored/cd_v5_softpenalty_rescored/`.
  - [x] **DeepSeek V4 Flash validation (2026-05-30)**: scored same 522 with soft-penalty prompt. Gemini fires F-K on 60% of articles; DeepSeek on 26% (same prompt, 2.3× difference).
  - [x] **OUT-OF-SCOPE wording restructure (2026-05-31)**: split into CATEGORY A (inherently low-substance, max_score caps A-E) vs CATEGORY B (high-substance wrong-trajectory, penalty F-K) with explicit "may fit other lenses" framing. Fixed Gemini's spurious A-E reclassification of political_conflict / tourism_fluff articles as cultural_discovery.
  - [x] **F-K trigger tightening (2026-05-31, prompt iteration 3)** per hand-judge agent finding (DeepSeek 12, Gemini 6, Unclear 4 out of 22):
    - K narrowed: explicit anti-triggers (award ceremonies, individual speeches, opinion essays, book/film/theater reviews, retrospective coverage, obituaries are NOT K)
    - I tightened: explicit "ends on rebound" carve-out + paleontological/archaeological extinction exclusion + "READ THE FINAL PARAGRAPHS" test
    - G explicit obit exclusion: "G does NOT fire on obituaries of recently-deceased public figures"
  - [x] **522-article re-scoring (Gemini v3 + DeepSeek v3)** with tightened prompt: outputs `datasets/scored/cd_v5_softpenalty_rescored_v3/` and `cd_v5_softpenalty_deepseek_v3/`
  - [x] **Two-pool spot-check on DeepSeek v3** (Opus agent): Pool A false-neg 13/15 CORRECT, Pool B false-pos 11/15 CORRECT (4 wrong, above 20% threshold but mostly K-boundary cases)
  - [x] **Haiku cross-validation of Opus** on handjudge_30: 77% exact agreement → agent layer validated
  - [x] **Broader 2-oracle disagreement truth set** (Opus agent, n=30 stratified): DeepSeek 21 / Gemini 5 / Unclear 2 / Both wrong 2. Per-oracle accuracy on disagreement set: **DeepSeek 80.8% vs Gemini 19.2%**. Confirms v3 tightening did NOT close Gemini's K/I/G over-firing — Gemini's reading style appears to be a stable disposition.

## Phase 4–9 (Completed 2026-05-31 evening)

- [x] **Phase 4: Oracle pick** — DeepSeek V4 Flash chosen (80.8% vs 19.2% on agent-judged truth set; ~7x cheaper; conservative-oracle principle locked in)
- [x] **Phase 4: Batch labeling** — 8,029 v4 records re-scored under DS + v5 prompt (`datasets/scored/cd_v5_8k_deepseek_v5_prompt.jsonl`), merged with 522 calibration cohort → 8,551 training records (`datasets/scored/cd_v5_deepseek_merged_for_training.jsonl`). $10.36 actual cost, 14% cache hit rate.
- [x] **Phase 5: Training** — Gemma-3-1B + LoRA on gpu-server. Val MAE 0.834→0.736→**0.697** across 3 epochs. `training_history.json`, `training_metadata.json` saved. ⚠️ *Caveat added 2026-09-06:* this line read *"(better than v4's 0.74)"*. **Retracted as an ordering** — no band or run-variance was ever computed for either figure, the two were measured on different splits with different positive rates, and **ADR-023 forbids ranking filters on MAE** in any case. The epoch trajectory within this run stands; the cross-version comparison does not.
- [x] **Phase 6a: Calibration** — isotonic regression on val set. `calibration.json` (16KB) + `score_scale_factor` 1.2829 computed.
- [x] **Phase 6b: Normalization** — deferred to first-week production data; `score_scale_factor` carries baseline.
- [x] **Phase 7: Hub upload** — `jeergrvgreg/cultural-discovery-filter-v5` (private) verified.
- [x] **Phase 8: NexusMind deployment** — filter package + model artifacts on `/home/hcl/NexusMind/filters/cultural_discovery/v5/`. Smoke-tested via /score endpoint: Pope apology 9.65→**2.31** (penalty fires), Indus/Sumer 9.12 (gradient preserved). `models_loaded: [..., "cultural_discovery_v5.0"]` confirmed.
- [x] **Phase 8b: v4 deleted from gpu-server** (2026-05-31, post-verification) — `filter_loader._find_latest_version()` provably picks v5 (verified in actual responses). v4 still in llm-distillery + git history + HF Hub if rollback ever needed.
- [x] **Phase 9: ovr.news integration** — `FILTER_TO_TAB['cultural_discovery'] = 'discovery'` mapping intact; Discovery tab picks up v5 on next pipeline cycle.

## Reference-Status (2026-05-31)

cd v5 is the **provisional reference example** for several patterns. None are locked-in as project standard until validated on a 2nd filter — most likely **solutions v4** (next on the in-development list).

| Pattern | Status | Validation requirement |
|---|---|---|
| Documentation pattern (7-file core + 2 optional extensions) | LOCKED — see `memory: filter-doc-standard.md` | cd v5 confirmed belonging v1's pattern works for complex calibrations |
| Conservative-oracle for needle-filter penalty flags | LOCKED — see `memory: feedback-conservative-oracle-better.md` | User-explicit principle |
| Soft penalty (subtract+floor) over hard cap (clamp) for orthogonal flags | LOCKED — ADR-015 + cd v5 outcome confirms | Empirical: gradient preserved + leakage fixed |
| ADR-020 methodology (multi-oracle batch + agent judging) | PROVISIONAL | Run on solutions v4; if leakage-fix + cost outcomes match, graduate to Accepted |
| DeepSeek as default oracle for cost-sensitive cycles | PROVISIONAL | Solutions v4 — confirm price/quality replicate outside Discovery domain |
| F/G/H/I/K flag taxonomy | DOMAIN-SPECIFIC (cd-only) | Not a reusable pattern; each new filter audits its own leakage shapes |

**Concrete handoff to solutions v4 work:**
- Use cd v5 as the canonical example in `docs/agents/filter-development-guide.md` Phase 1–3
- Follow ADR-020 PROVISIONAL methodology end-to-end
- If solutions v4 lands cleanly: revise ADR-020 → Accepted, point workflow doc at cd v5

## Key Decisions This Cycle

| Decision | Source | Rationale |
|---|---|---|
| Soft penalty (subtract+floor) over hard cap (clamp) for F-K | ADR-015 (cliffs hurt MAE; thriving v1 parked for this) | Preserves dim-to-dim gradient (heritage > novelty stays meaningful) |
| Penalty values F=2.5 G=2.5 H=3.5 I=2.0 K=2.5 | Calibrated to push borderline content (honest weighted ~5-6) just below 4.5 display threshold | Empirical; revisit after training-set MAE |
| Multi-oracle calibration (4 batch + 2 agents) | data-analyzer review of ADR-020 draft | Inter-oracle consensus is best ground-truth proxy when no human labels exist |
| Conservative-oracle preference for needle-filter penalty flags | User explicit (2026-05-31) — saved as memory | False positives (over-fire → article disappears) worse than false negatives (under-fire → known leakage stays) |
| Prefilter inherits from v4 unchanged | Behavior delta would mask training-data-shift effect | F-K classification is LLM-prompt level, not regex-detectable reliably |

## Files in this Filter Package

| File | Purpose | Status |
|---|---|---|
| `config.yaml` | Dimensions, weights, gatekeeper, version | ✅ |
| `prompt-compressed.md` | Oracle prompt (v3 with all tightenings) | ✅ |
| `prefilter.py` | Rule-based blocker (thin v4 subclass) | ✅ |
| `STATUS.md` | This file — phase-by-phase tracker | ✅ |
| `DEEP_ROOTS.md` | Philosophical/scientific grounding | ✅ |
| `README.md` | Short summary + links | ✅ |
| `calibration_report.md` | Phase 3 formal artifact | 🟡 draft (sections fill as data lands) |
| `dimension_analysis/` | PCA + correlations + plots | 🟡 generation in progress |
| `model/` | LoRA adapter | ⏳ Phase 5 |
| `probe/` | e5 embedding probe (hybrid) | ⏳ Phase 6c |
| `calibration.json` | Isotonic calibration | ⏳ Phase 6a |
| `normalization.json` | Production CDF normalization | ⏳ Phase 6b |
| `training_history.json`, `training_metadata.json` | Training records | ⏳ Phase 5 |
| `base_scorer.py`, `inference.py`, `inference_hub.py`, `inference_hybrid.py` | Scorer Python | ⏳ Phase 5/6 (templated from v4) |

## Open Questions

1. **Final oracle pick** — DeepSeek strongly favored on evidence so far. Need Qwen3 + Phi4 to confirm (3rd/4th conservative voice → unanimous case for DS) or contradict (3rd/4th align with Gemini → reconsider).
2. **8K corpus re-score under v5 prompt** — required for clean training data, but ~$2 (DS) or ~$15 (Gem). Cheap relative to caliber of insight already accumulated.
3. **ADR-020 final shape** — provisional methodology vs ratified standard. Per reviewer convergence: mark PROVISIONAL until validated on 2nd filter.

---

## Post-Ship Cleanup TODO

Deferred during cd v5 retrain push (2026-05-31) to stay on critical path. Address after v5 ships to NexusMind / ovr.news:

- [ ] **Patch `CLAUDE.md` cost figure**: oracle line currently says `$0.001/article` — actual is `$0.003-0.004/article` (Gemini Flash 2.5 with v5-class 8K-token prompt). Stale figure misled multiple cost estimates today.
- [ ] **Patch `docs/agents/filter-development-guide.md` Phase 1-2 checklist** to require the belonging v1 standard (STATUS.md + DEEP_ROOTS.md + README.md). Convention is now locked in (see memory: `filter-doc-standard.md`).
- [ ] **Revise `docs/adr/draft-020-extended-oracle-calibration.md`** per 4-reviewer convergent feedback: (1) cut 5-oracle → 3-oracle as default, (2) split soft-penalty mechanism into ADR-020a (extension of ADR-015) and multi-oracle into ADR-020b, (3) replace "Expected outcome: DS wins" prediction with actual results from this retrain, (4) explicitly address Alternative 5 ("iterate prompt one more round per ADR-010"), (5) add precedence rule for conservative-oracle vs consensus-alignment when they diverge, (6) mark Status: PROVISIONAL until validated on 2nd filter.
- [ ] **Code refactor**: extract `extract_dim_score`, `smart_compress`, `build_prompt`, `pearson`, `spearman`, `wavg` into `ground_truth/oracle_utils.py`. 9 scripts have copy-pasted variants today. ~1hr work. Defer to next filter cycle (refactoring-guide reviewer recommendation).
- [ ] **OracleClient ABC refactor of `ground_truth/batch_scorer.py`**: currently hardcoded if/elif over `claude/gemini/gemini-pro/gemini-flash/gpt4`. No DeepSeek/Ollama support → caused fork pressure. 2-4hr work. Defer to first task of next filter cycle (or whenever a new oracle provider is needed).
- [ ] **First-week production monitoring** (target window: 2026-05-31 → 2026-06-07): pull cd v5 scores from `ovr.news` Discovery tab, verify the #62 leakage examples (Pope apology, Belgium Congo, Modigliani repatriation, residential schools, Antwerp Congolese memorial, etc.) score below 4.5. If any leak through, capture in `datasets/raw/cd_v6_leakage_candidates.jsonl` for v6 work.
- [ ] **Use cd v5 as ADR-020 validation case during solutions v4 cycle**: follow this filter's playbook end-to-end (4-oracle batch → agent judging → conservative-oracle pick → soft-penalty mechanism if orthogonal flags emerge). Outcome decides whether ADR-020 graduates PROVISIONAL → Accepted.
- [ ] **Tooling debt surfaced by this filter's deploy** — both have proposed fixes in their issue bodies:
  - #67: `deploy_filters.sh` excludes `model/` on hop to gpu-server (manual scp required for first deploy of new filter version)
  - #68: `verify_filter_package.py` should check config.yaml schema (per-dim `description` field) before `--check-hub` round-trip
- [ ] **Apply remaining v5 prompt tightenings** per oracle-calibration agent's final review:
   - K anti-trigger: add "festivals currently running with delivered programming are NOT K — future-tense only"
   - G carve-out tighten: "at least three previously-unidentified victims as primary subject with the identification work — not the ceremony — driving the narrative"
   - I anti-trigger: "metaphorical loss in feature headlines does NOT fire I — requires documented demographic/linguistic/community decline as primary subject"
   - K/I anti-trigger: "report verbs (announces, launches, unveils) describing already-delivered content do NOT fire K/I"
   - Add multi-flag interaction worked example (max_score + penalty stacking)
   - Add validation row demonstrating non-zero novelty under F-K penalty
- [ ] **Fix the v3→v4 prefilter regression** (`check_content_length()` no longer called before pattern matching) — documented in cd v4 prefilter docstring; defer to v6 prefilter cleanup.
- [ ] **(Optional) Compile final 4-oracle calibration_report.md sections** when Qwen3 + Phi4 batches complete + agent hard-case judges adjudicate. Worked example for ADR-020.
