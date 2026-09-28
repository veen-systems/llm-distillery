# LLM Distillery - TODO

## ▶️ START HERE — the ordered queue, as of 2026-09-27 (evening close)

*A bare "continue" means this list, top down. Each line names the FIRST action. The previous
START HERE block (2026-09-26/27: H-DP3, ADR-024 step 3, adj4p, the #151 cutover rulings, the
read-surface steps −1.1–4) moved VERBATIM to `docs/TODO-archive.md` § *Moved 2026-09-27 (evening)*
— grep there before concluding something was never recorded.*

0. ✅ **CLOSED 2026-09-28 — NexusMind PR #553 is in production.** On sadalsuud: HEAD `5976fd2`, `0cbfd4c` is an
   ancestor; `filters/common/obituary_detector` holds only `v5`, `commerce_prefilter` only `v1`;
   `verify_detector_package.py verify --all --strict` printed 4× OK. Cycles since the merge: 17:06, 21:09, 05:32,
   09:18 Finished; **00:58 OOM-killed in pre-enrichment** (23.1G peak) — already NexusMind#558, not caused by #553
   (the kill came during fetch, after detector load). ⚠️ gpu-server orphans still there: the 08:09 sync logs
   `cannot delete non-empty directory: common/obituary_detector/{v3,v4}, common/commerce_prefilter/v2` (plus
   `investment_risk/v5`, `uplifting/v5`) — NexusMind's to `rm`, as predicted.

1. ▶ **THE READ SURFACE (`#163`) — owner, standing since 2026-09-22 and re-stated 2026-09-27: "prune, thin,
   mechanize, retire."** Order: **mechanize → retire → thin → prune**; ⛔ retiring is not deleting (move
   verbatim, prove lossless with an independent checker); ⛔ a new check ships only WITH the prose it lets
   you delete. Measured 2026-09-27 close (`wc -c`): `docs/TODO.md` 80,441 → 57,999 (this close);
   `memory/gotcha-log.md` 149,894; `memory/hypothesis-ledger.md` 85,687; `memory/cross-repo-prioritization.md`
   61,176; `CLAUDE.md` 17,933; `memory/MEMORY.md` 10,677; always-loaded layer PASS 30,750 / 60,000.
   First actions, in order:
   a. ✅ **DONE 2026-09-28: ledger retire.** 8 rows (`H-TV1`–`H-TV4`, `H-LA1`, `H-HC1`, `H-DP1`, `H-DP3`) moved
      verbatim to `memory/archive/hypothesis-ledger-archive.md`; ledger 85,726 → 81,818 B. Lossless by an
      independent `sort | comm` multiset check (0 lost, 4 header lines added; two mutations caught; order kept).
      Kept live on purpose: `H-JO1` (partial for Thriving), `H-CTX-*` (kept 2026-09-27 too), and the `cd-v6`/
      `sol-v6` index rows (they index live topic files; `check_doc_claims.py` pins `cd-v6-row`).
   b. ✅ **DONE 2026-09-28: TODO body audit** (`ec4ddc5`, `ba1b26c` + next). All `[x]` lines of the four named
      sections and 16 carried-over boxes moved verbatim to `docs/TODO-archive.md`, each box with its closing reason;
      lossless by `sort | comm`. The ~19 boxes left are LIVE: each cites an OPEN issue or waits on an owner call —
      ⚠️ notably **decision 0** (delete the old per-lens prefilters, NexusMind#284): the 2026-08-21 ruling covers
      NEW filters only, so the five boxes hanging on it stay. Finding: NexusMind#286 item 3 (on its box).
   c. **Gotcha log**: on/after 2026-10-01, `python3 scripts/maintenance/retire_memory.py {gotcha,sessions}
      --before 2026-10-01` (dry run first, then `--apply`).
   d. *Option, not ruled:* a hook blocking a commit that shrinks `CLAUDE.md`/`memory/MEMORY.md` by > 10% unless
      the message cites a clause-loss review.
   e. *Optional mechanize:* gotcha-log § Mechanized row `check_committed_idiom.py` (`proposed`; `ls-files` used
      as a "committed" test) — build only with a seeded positive AND a prose line it retires.

2. **ADR-024 steps 4–5 are NexusMind's** (step 4: loaders read `MANIFEST.json`, log-only flag, per detector;
   its start is the owner's call. Step 5: commerce `model.safetensors` is gitignored there). Nothing of ours
   unless they ask. Also theirs: retire gpu-server `/commerce/predict` (unreachable from the pipeline, LD#80).

3. *Owner, not urgent:* H-TV5 (watch Thriving while uplifting v7 drains, ~10 days from 2026-09-26); obituary v5 /
   violence v1 have no recorded sklearn version (the Q5 skew check has no baseline until a rebuild); the deploy
   script's `C:/` default roots (changing them makes an env-less run hit real repos). NexusMind owns the
   Venezuela Thriving story cluster (NexusMind PR #542). *Later:* Nature recovery v5 (#71),
   `docs/evidence/2026-09-25-nature-recovery-relabel/PILOT_RESULT.md`.

4. **Then the numbered work items below** (1–8). ⚠️ Item 1's date gate (~2026-09-24) has passed; it is
   executable. Item 2 is an owner spend decision. Numbers are NOT reused when an item closes.

1. ⏳ **DATE-GATED (earliest ~2026-09-24) — THE PER-LENS HARM FLAG RATES (`#156` step 2).**
   🆕 **MEASURED 2026-09-28 (journal, sadalsuud): the harm stage has reported `0 files deferred` every cycle
   since 2026-09-27 04:17** — the cycle before it said 132. In that one cycle `already stamped` went 57,000 →
   108,000 (+51,000 against a 6,000 cap; 2,834 stamped) and `too old` 1,537 → 454,072. ⛔ **Cause unknown** — no
   matching NexusMind commit since 2026-09-26; an out-of-band backfill is a GUESS. So the "unstamped tail
   persists" premise below may be void, but part of the old tail left by AGEING OUT, not by being stamped.
   The census is still the instrument that decides it.
   **First command: `NexusMind/scripts/stamp_census.py`** on sadalsuud — CLAUDE.md's rule is to
   run it before quoting any stamped field, and it is the mandated instrument for exactly this.
   ⛔ **DO NOT WAIT FOR THE BACKLOG TO CLEAR** (`H-HD13`, `NM#522`): the 3,000/run cap sits below
   the intake measured so far, so the unstamped tail persists **at the current cap and intake**
   and is systematically the OLDEST rows. ⚠️ **Not "permanent"** — both sources carry a dated
   expiry: GN retires **2026-10-15** (6.71% of delivered rows) and the deficit may close on its
   own. ⚠️ And the deficit rests on **n=2 cycles**, one of which (3,072) is only 2.4% above the
   cap. Wait instead for filtered-population presence to plateau — two census reads so far,
   **61.17%** (2026-09-21, 23,520 rows) and **85.29%** (2026-09-22, 36,838 rows); ⛔ two points
   are not a plateau, so take a third before calling it one.
   Method: for each lens, among rows at/above **that lens's own op-point**, the share with
   `_harm_is_subject_score` above candidate thresholds. ⛔ **Per-lens, never pooled** — every harm
   figure that exists today is the `uplifting v7` / `human_thriving v8` panel. `solutions`,
   `belonging`, `nature_recovery` and `cultural_discovery` have **no computed rate** (their rows
   *are* stamped — what is missing is the analysis, not the data), and for **Solutions and Nature
   Recovery** the ADR argues "no cap, ever" may be right: one is about responses to harm, the
   other is literally about recovering from damage. Then, and only then, a cap on `uplifting v7`.

2. ⏸️ **OWNER DECISION, STILL OPEN: the ~$3.2–3.6 adverse-pool spend (`#156`).** ⚠️ **Item 1
   did NOT answer this** — the shadow stamp counts what the detector FINDS and is structurally
   blind to what it misses, so it narrows the per-lens GATING decision, not this one.
   `EXP-039` closed the last free route with a negative — the per-run votes buy nothing — so the
   pool is now the route to new signal rather than a ranked option. ⛔ **Do not re-run the free
   arm**; its one untested variant needs a bigger positive class AND a new pre-registered bar.
   The pool is sha256-pinned, so nothing degrades while it waits.
   Owner said 2026-09-17: *"i need to think about this later."*

3. **LD#134 step 3 — the MARKING PASS over the live tier.** Steps 1 and 2 are done and must
   not be redone (`docs/decisions/2026-09-17-refcheck-docs-tier.md`). The tier is in code;
   `--docs-live` prints the promotion preview. ⛔ **Read the record before quoting a number
   here** — this line deliberately carries none, and the "~8× faster" framing it used to
   carry was refuted: that was a count over a population that grew 168 → 242 files.
   Promotion to the default set comes AFTER marking, in a separate change.
4. **The retracted 19.9%/13.0% framing is still live in the always-loaded file** — `CLAUDE.md`'s
   prefilter constraint, plus `docs/HUMAN_THRIVING_V8_PLAN.md:176` and
   `memory/cross-repo-prioritization.md` (grep `19.9%`; its line numbers moved 2026-09-27 when dated sections were retired). Two copies carry the correction, four
   carry the retraction. Deserves its own review. ⚠️ **Cite it by name, not by line** — it was
   `CLAUDE.md:74` until 2026-09-17 and the frontmatter edits move these numbers every session.
5. **LD#160 — two Dutch-name violations**, owner call pending: `docs/adr/009-...:25,34,35,37,60`
   and `scripts/analysis/cross_filter_landscape.py` (39 occurrences). Mechanize with
   `check_framework_language.py` whose allowlist **is** the carve-out table; show it go red first.
   ⚠️ It now has a `proposed` row in `memory/gotcha-log.md` § Mechanized — move it to `live`
   only after a seeded positive, not after writing the script.
6. **H-MECH-1 — watch, do not act yet. ⚠️ BATTERY 1 of 3 HAS RUN and the column DID move**
   (to 1) — `memory/hypothesis-ledger.md` already records it, with a raised bar: an increment
   must name whether the check *could* have fired. **Two batteries left**, so this line's old
   "check whether it ever moved" is already answered and must not be re-asked.
7. **The HELDOUT detector band (`#158`'s remaining half).** `EXP-040` measured out-of-fold bands;
   the issue quotes **heldout** recall and the two are not comparable. Cheap on the 5090 (embed +
   5 fits per detector) and it is what would give the live 0.85 obituary op-point a defensible
   range. ⛔ Heldout corpora are on b650 at `filters/common/obituary_detector/training/data/`.
8. **`#104` item 1 — the only arm that measures PRODUCTION's configuration.** `EXP-041` did the
   device axis on one box; gpu-server's own GPU is untouched, and CUDA-to-CUDA across the two
   boxes is now a comparison across two GPU ARCHITECTURES. ⚠️ Needs a gap between pipeline cycles
   (`nexusmind-scorer` has `Conflicts=ollama.service`), which is what makes it the expensive one.
   ⛔ This is NOT blocking anything: the shipped decision was stamp-and-band, already done.

⚠️ **Before quoting `references 23 → 0`** (2026-09-17 audit): that is the DEFAULT scan set only,
and `docs/` is still opt-in. See item 3.

---

## Commerce Prefilter SLM - NEEDS REWORK

ML classifier for commerce/promotional content detection. Cross-cutting prefilter for all filters.

**Status:** v1 complete but needs redo - concerns about multilingual embeddings and context size.
**v1 is the version running in production** — force-pinned by LD#80 because **v2 underperformed v1** on production traffic. There is no v3.
**v2 is RETIRED (2026-09-27, owner):** it no longer ships (`RETIRED_DIRS`, `3e7f565`) and NexusMind PR #553 deleted it
downstream — confirmed on sadalsuud 2026-09-28. The package stays here as a record.

- [ ] **Re-measure the miss rate before retraining** ← **DO THIS FIRST (added 2026-08-07)**
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
- [x] ~~**sustainability_technology v3**~~ — **REMOVED 2026-08-03**, replaced by solutions. Package deleted; recover from git history. Entry kept for the training record below, not as a statement of what is deployed.
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
- [x] ~~**foresight v1**~~ — **REMOVED 2026-08-03**, merged into solutions (#43, closing out #64). Was signs_of_wisdom. Package deleted; recover from git history.
  - Val MAE 0.75, 3,480 training articles, 6 dimensions
  - Hybrid inference: probe trained, threshold 2.25 (default, calibrate on production data)
  - Remaining: ovr.news Foresight tab frontend integration

### Active Learning In Progress
- [x] **cultural-discovery v5** - **DEPLOYED** (HF Hub, DeepSeek oracle, MAE 0.70). Stale `[ ]` corrected 2026-08-03 — the entry below describes the training-data prep that has long since shipped. Live follow-ups are #86 (prefilter is dead in production — measured, DO NOT enforce) and #87 (v6 scope: lens-fidelity + op-point re-derivation).
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
- [ ] `H-V8-26`: its revisit trigger is a ~50-article hand-audit of v8's reader-facing precision; no audit record was found (review 2026-09-27). Moot now that v9 is live? Owner call.

## ☐ Unchecked boxes carried out of the archived sections (2026-09-24)

*Copied mechanically from `docs/TODO-archive.md`: every `- [ ]` line in a moved section, under
that section's heading. ⚠️ **Not re-verified** — many are probably done or overtaken; the
queue is ▶ START HERE, not this list. Close or delete a line once checked against its section.*


**From:** 🔵 PREVIOUS SESSION — **ADR-013 widened to all framework text; review found my own evidence unsound and the compliance zero FALSE. Framework 6 releases behind, s
- [ ] **Mechanize the language rule (#160)** — `scripts/verification/check_framework_language.py` whose

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
- [ ] **Owner call**: does `ducroq/augmented-engineering` (34 open, **1 closed

**From:** 2026-08-06 evening — four owner decisions taken, three backlogs closed

**From:** 2026-08-06 — cd v6 probe (#98), the English escape hatch (#99), and an instrument for FS#120
- [ ] **sadalsuud carries the pre-`80dd399` cd gate** (235 topic stems vs 453). Zero production effect — that prefilter does not run (NexusMind#284) — but flipping enforcement without syncing restores the exact skew #86 removed. Recorded on #86 as a trap; **do not close it by syncing**, since #98 deletes the file.

**From:** 2026-08-05 — TDM / training-data position, and the two carve-outs it leaves open
- [ ] **The `tdm_opt_outs.json` scan is unscheduled.** It has run exactly once (2026-08-04). A reservation added tomorrow is invisible. Quarterly is enough for a signal that moves this slowly — the implementation sketch in #28 is retained there as the thing to build **if this decision is ever reversed**, not as work to do now.

**From:** 2026-08-02 — Chain 4 measured: two of the previous day's own P0 conclusions overturned
- [ ] **Fit the solutions short-content cap** (#93 step 4) — **#92 no longer blocks it; #95 still does.** The second-op-point re-run ran 2026-08-05 and the defect is **identified**: D1 (both arms ≥2.25) −0.790, D2 (≥4.00) −0.861, **D3 (matched percentile depth) −1.119** [−1.61,−0.61], cluster-bootstrap p Holm-corrected 0.0032 / 0.0012 / <1.5e-4. The selection artifact predicted D2 markedly more negative and D3 → 0; D2 moved −0.071 and D3 is the *largest*. A gemini-2.5-flash cross-check on the same D3 sample gives **−1.351** [−1.73,−0.96] — two oracles with clearly different absolute bias, same gap, which rules out "the judge penalises short input". Harness + fixtures committed (`scripts/diagnostics/ld92_*.py`, `tests/fixtures/ld92/`). **Remaining blocker is Batch F.1 (#95)**: the cap value is a threshold fit and inherits the |Δ| ≤ 0.16 batch-composition noise floor. Also weigh the recall cost against NM#231/#292 before setting a value — `gn_africa_*` / `gn_asia_*` feeds lead solutions' short-and-clearing list.
- [ ] **Does the scorer share the summariser's fixed-budget failure? (NEW, ovr#299)** For English sources, summary content words absent from the article *and* title run 31.6% (1000+ chars) → 73.9% (120–299) → **83.4% (<120)**, monotone over 18,756 summaries. The mechanism there is a fixed output length target (medians 1159/968/875/1065 against a 40× input range) that the model fills — compressing an article, generating from a headline. **Open for this repo: whether the student has an analogous behaviour, or whether its short-content error is purely vocabulary-without-subject.** The fixes differ — one is a budget, the other a cap — so this is worth one experiment before building either.
- [ ] **Re-run the NM#284 shadow** now that the length floor is out of the prefilters *(deployed to gpu-server 2026-08-03 ~15:45 CEST, rev `2d5c54aa…`; first cycle carrying it is 16:10)* — its pass rates finally describe lens behaviour, which is what LD#90 item 2 needs. Rates measured before 2026-08-03 are not comparable to ones measured after.
- [ ] **NM#286 item 3** (violence stamping skipped in single-filter / `--no-dedup` / dedup-exception runs). Verified in code; **live blast radius zero today** (production runs multi-filter, violence `enforce: false`), so it is an audit gap, not admitted violence. Still a hard prerequisite for any violence enforce flip, with LD#82.
  - ⛔ **2026-09-28: the premise is gone and the fix is not in.** Violence has ENFORCED since 2026-08-23 (`config/app.yaml` comment on sadalsuud); `_run_violence_promotion_prefilter` still returns with NO stamps when `_article_cache` is empty (read on sadalsuud today), and `_enforce_violence_promotion` fails open. Live multi-filter cycles stamp, so today's exposure is a shared-dedup exception or an ad-hoc single-filter run. The 09:05 cycle logged `10344 unstamped articles left in place` — cause NOT measured (dedup-removed copies is a guess). NexusMind's code; owner to decide whether to raise it on NM#286.
- [ ] **Fix `no_cultural_topic_signal` multilingual coverage**, then re-run the identical LD#86 recall check — falsifies whether the language skew is the gate or the corpus.

**From:** 2026-08-01 — Cross-repo: ovr#280 cluster_id diagnosis corrected
- [ ] **NM#278 is the real fix for the reported symptom** — the five-articles-on-one-story report is a *threshold* problem, not a plumbing one: NexusMind clusters on source text pre-summarization, where cross-outlet paraphrases look far apart; two of the five only converge after ovr.news summarizes. Caution recorded on NM#278: NexusMind *removes* rather than *labels* (32%/run), and anything removed upstream can never surface as an "N sources" badge — so prefer labelling over dropping when re-tuning.

**From:** 2026-07-31 — LD#76 Calibration Audit (11-agent battery, all verdicts adversarially verified)
- [ ] **cd v5 dead prefilter (#86)** — the gate is **correct and now production-validated, but still not enforced**. Verified 2026-08-01 by NM#284 **in-path** shadow measurement on the 12:46 cycle: **0.255 observed vs 0.25 declared (n=2099, full cycle)**, matching the fix's own offline validation (0.245 on 14,923 rows). *(An earlier claim here — "production stamps 2647/2647 pass, replay gives 28.8%" — was retracted: that baseline came from `filtered_*.jsonl`, which only receives `passed_prefilter: true` rows, so it is 100% passers by construction. See NM#284 issuecomment-5151154862.)* **Root cause is not cd-specific: the per-lens rule prefilter has never run in production** (NexusMind `deploy/gpu-server/main.py` L915 `use_prefilter=False` + L1318 `skip_prefilter=True`, since `66582e7`, 2026-02-10). e5 probe, commerce/obituary/violence, and the NM#189 source allowlist all verified running. Filed **NM#284**. #86 closes when NM#284 stage 3 flips cd to enforcement — the fix itself needs no further work.
- [ ] **NM#284 stage 1b — per-row shadow stamps into the JSONL**: needs `prefilter_shadow_pass` / `prefilter_shadow_reason` plumbed through gpu-server `main.py` (Pydantic `FilterScoreResult` drops unknown keys at the service boundary) → `src/scoring/gpu_client.py` → the `analysis` dict in `scripts/main.py`. Blocked on unrelated uncommitted WIP in `scripts/main.py` (image-classifier thresholds, NM#282) — staging it would sweep that in. Log-based measurement is sufficient for the enforcement decision, so this is a convenience, not a blocker.
- [ ] ⚠️ **SUPERSEDED PENDING DECISION 0 (2026-08-12) — do not act on this.** The top-block recommendation is to **DELETE** the per-lens prefilters rather than flip enforcement on, because enabling them would ship #99's English-only `DISCOVERY_PATTERNS` back door (still live in v5) into production for the first time. Resolve decision 0 before touching this line. ~~**NM#284 stage 3 — per-filter enforcement flip**, once a few cycles of shadow data exist.~~ cd is the only filter whose observed rate currently matches its declared one, and it is also the one LD#86 needs. Op-point / normalization re-derivation for affected filters is downstream of the flip (gates #87).
- [ ] **cd v6 lens fidelity scope (#87)** — ccc 0.25 weight ceiling (mean 0.64), 27% off-lens hard science in visible band, "4.5 display threshold" vs shipped 4.0 unreconciled. Design ticket; not urgent. The 3.5 op-point proposal was REFUTED (sampling artifact) — any re-derivation needs a randomized [3.0,4.5) sample **after NM#284 lands**: the v5 op-point and normalization CDF were both fitted on a distribution still containing the ~71% the prefilter should have removed.
- [ ] **Lens harmonization program (#90)** — owner directive 2026-07-31: bring all lens filters to the successful template (op-point at the distribution, fresh anchored fit, working positive gate, hybrid + stamps, ADR-021 gate) **The rename half is CLOSED as of 2026-08-06 — do not re-open it here.** ADR-012 amended: `cultural_discovery` and `nature_recovery` KEEP their names (their Hub repos are public standalone artefacts; `discovery-filter-vN` / `recovery-filter-vN` drop the qualifier that says what the model is about), `solutions` confirmed as-is, and `uplifting` → **`human_thriving`** at v8 — not bare `thriving`, which is an existing parked directory. What remains under #90 is the template half only.
- [ ] **Hygiene batch** — emit `stage_used` into row attrs; document nr runtime stage-1 threshold 0.75 (config.yaml says 3.225, inert); fix stale ir config tiers (3.0 vs live 4.0); note nr raw HIGH tier 7.0 > calibrated ceiling 6.8 (structurally dead).
- [ ] **Drift guard** — uplifting violated the >20%-relative-pass-rate refit trigger by an order of magnitude for ~4 months, undetected; the prefilter kill (NM#284) hid for ~6 months the same way. Add per-cycle pass-rate logging or a scheduled drift check covering both normalization freshness and declared-vs-observed prefilter pass rate (owner question).
