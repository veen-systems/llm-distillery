# Filter Playbook — Single Source of Truth

**Read this first before creating or retraining ANY filter.** It compiles every hard-won
lesson so you don't re-scavenge the repo or fall into the same pits. Each rule links to its
source (ADR / memory / gotcha) so it stays maintainable — fix the source, not just this page.

- **This page's job:** the rules + the canonical example, not the step-by-step. Everything else is subordinate to it — the map below says what each doc is for so you never scavenge.

### Documentation map (what to open, what's dead)
| Doc | Use it for | Status |
|-----|-----------|--------|
| **`docs/FILTER_PLAYBOOK.md`** (this) | START HERE — compiled lessons + canonical example | **live, SSoT** |
| `docs/agents/filter-development-guide.md` | Full lifecycle depth (per-phase checklists, validation) | live |
| `docs/guides/filter-creation-workflow.md` | Quick step-by-step commands | live (companion) |
| `docs/RUNBOOK.md` | Deploy / train / score operations | live |
| `memory/gpu-server.md` | gpu-server env (venv, PYTHONPATH, HF_HUB_OFFLINE, scp-not-rsync) | live |
| `docs/adr/README.md` | Settled decisions (21 ADRs) | live |
| `memory/gotcha-log.md` + `memory/feedback-*.md` | Problem→fix archive + behavioral rules (the source of the pits below) | live |
| `docs/_archive/guides/getting-started.md` | — | **DEPRECATED** (Qwen-era) |
| `docs/_archive/guides/ground-truth-generation.md` | batch-scorer mechanics only | **DEPRECATED** (rest is stale) |
| `docs/_archive/guides/gpu-training-guide.md` | — | **superseded** → RUNBOOK + `memory/gpu-server.md` |
| `docs/_archive/guides/remote-sync-guide.md` | — | **superseded** (FreeFileSync → scp/rsync; see `memory/gpu-server.md`) |

---

## The canonical reference: `nature_recovery v4`

Copy its *shape*, not its metrics. It is the most complete worked example of the needle-filter
lifecycle + the V&V/gate/oracle-selection methodology (deployed 2026-07-10).

- **Package:** `filters/nature_recovery/v4/` · **Report:** `docs/reports/nature_recovery_v4_report.pdf`
- **Evidence data:** `docs/articles/nature_recovery_v4_evidence/` · **Deploy write-up:** `docs/nature_recovery_v4_DEPLOY_COMPLETION.md`
- Other references, each for its domain: **`belonging v1`** = prompt precision / oracle consistency (ADR-010) · **`cd v5`** = multi-oracle bake-off (ADR-020 draft) · **`solutions v6`** = probe-split retraining + iterative improvement of deployed filters (the technique that dropped MAE 0.564→0.476 while improving recall).

---

## The pits — rules by lifecycle stage

Format: **the pit → the rule** (source). Skim the bold before each stage.

### 0. Oracle selection (highest-leverage decision — get it right first)
- **Defaulted to one oracle out of habit → wrong labels.** Select per-filter with a small bake-off (score ~300 stratified, judge the ~30-disagreement set with strong models). `feedback-oracle-selection-criteria`, ADR-020 draft.
- **Switched oracle to cut NOISE → wrecked BIAS ($100–200 lesson).** Noise (self-consistency) ≠ bias (editorial alignment). Choose the oracle for *bias*; cut noise by averaging k runs of the correctly-biased oracle, **never** by switching to a cleaner-but-differently-biased one. A clean, consistent, *wrong* teacher looks like progress. `feedback-oracle-bias-vs-noise`.
- **On penalty/exclusion flags, prefer the oracle that UNDER-fires** (a false penalty demotes a good article; a missed one is softer). `feedback-conservative-oracle-better`.
- **Treated oracle scores as truth.** The oracle is a *consistent labeler*; its self-MAE sets the student's floor (ADR-017). Stubborn high MAE on a dim → suspect label noise, fix the *prompt*, don't add data. `feedback-oracle-not-ground-truth`, ADR-010.

### 0b. Prefilter — know what it does and doesn't do (NM#284)
- **Wrote a prefilter, assumed production used it → it never ran.** A filter's `prefilter.py` (the per-lens *rule* prefilter) gates **oracle spend** in phases 3/5 and runs in llm-distillery's training path. It does **NOT** run in NexusMind's production scoring path: the gpu-server scorer builds every scorer with `use_prefilter=False` and calls `score_batch(skip_prefilter=True)`. True since 2026-02-10, found 2026-08-01. Unaffected: the e5 probe, the commerce/obituary/violence gates, the NM#189 source-type allowlist. NM#284 stage 1 now logs observed vs declared pass rate; enforcement is not yet on. **Don't size a filter's production volume on its prefilter's pass rate.** NM#285 measured the shadow's two biases (truncation +0.0000 to +0.0097; denominator −0.129 on investment_risk) and its log now states both on every line; the blocker for enforcement is #93, the length-floor split.
- **Verified prefilter state from `filtered_*.jsonl` → circular evidence.** That file only receives rows where `passed_prefilter` is true NexusMind `scripts/main.py`’s `if result["passed_prefilter"]:` write guard, so it is 100% passers by construction and can never show a block. The first NM#284 write-up cited "0 blocks per cycle" from it and had to be retracted. Use the pipeline line `Filter X complete (N scored, M prefiltered)` or the shadow log — both see pre-drop counts. **General rule: before using a data source as a denominator, establish what it is filtered on.**
- **Copied the prefilter from the template → inherited someone else's intent.** `solutions v6` shipped `nature_recovery v4`'s *deliberate* commerce-only pass-through while keeping a description claiming a keyword net and declaring `expected_pass_rate: 0.20` against ~0.59 actual. Byte-identical `EXCLUSION_PATTERNS` between two filters is a smell, not proof of a defect — nr v4's zero lens-blocks are documented and correct (topic gates removed in v4: English-only, cost 21.6% recall, screening moved to the e5 probe). ~~**The check is: does observed pass rate match declared, and does `description` match actual behavior?**~~ **Superseded 2026-08-02 — that check passes a filter with no gate at all.** Both filters were measured at zero lens blocks over 8,283 articles, so the answer was to delete `expected_pass_rate` and rewrite the description, not to reconcile a number. See the two rules below. LD#90, #93.
- **Quoted a prefilter's total block rate as lens signal.** Split base-class rules (`content_too_short`, `missing_content`) from lens rules first — the length floor blocks the *identical* articles for every filter and dominates the total. **Measured 2026-08-02 (n=8,283):** length's share of all blocking is **100%** for `nature_recovery v4` and `solutions v6`, 96.8% belonging, 92.6% investment_risk, 86.3% uplifting, **0%** cultural_discovery. `memory/prefilter-length-floor-hypotheses.md`. **Fixed at the root 2026-08-03 (#93): no prefilter checks length any more**, so a block rate measured after that date *is* lens signal. Pass rates measured before it are not comparable to ones measured after.
- **The 300-char floor is a labelling rule, not a scoring rule (#93).** It exists because short articles make an LLM analyse the evaluation framework instead of the article — a hazard of the oracle *prompt*. The student sees no prompt. So the floor lives in `ground_truth.batch_scorer.make_oracle_prefilter` (what gets *labelled*) and nowhere in `apply_filter` (what gets *scored*). Scoring stamps `content_length` on every result and applies at most one config-gated `short_content.cap`, off everywhere until #92's selection confound is resolved. Writing `check_content_length` into a new prefilter re-creates the thing #93 removed.
- **"Does observed match declared" is the wrong first question — ask whether the filter has a lens gate at all.** `nature_recovery v4` and `solutions v6` emit *zero* lens blocks across 8,283 articles; their declared 0.85 / 0.20 described gates that do not exist. The fix was **deleting** `expected_pass_rate`, not correcting it: the observed 0.644 is "fraction of articles ≥300 chars", a property of the corpus. **Never re-declare a rate from an observed number without first establishing which rules produced it** — that encodes a corpus statistic as a lens spec. LD#90, #93.
- **A matching pass rate is NOT a safety argument for enforcement.** `cultural_discovery v5` is the one filter whose observed rate matches its declared one (0.2605 vs 0.25) — and enforcing it would still block **15.5% of surfacing articles** (0% of high tier). Rate agreement says the *volume* is right; it says nothing about *which* articles. **Before any enforcement flip, measure recall against articles the scorer already ranks above the op-point** (ADR-021 applied to gates, not just models). LD#86.
- **Compared two scores and read the difference as signal.** A student score is not a function of the article alone — it also depends on the batch it was scored in. Measured 2026-08-03 (#95): max |Δ| **0.162**, mean 0.004, and **7-9% of articles within ±0.3 of an op-point flip tier/visibility** purely on batch composition. Aggregates (MAE, DiD, calibration) average it out and are safe; **threshold tests are not** — tier, `raw >= op-point`, and any per-article before/after check carry a ~0.17 worst-case noise floor. Pin `batch_size` before measuring anything at a boundary. `memory/score-batch-shape-noise.md`.
- **Reconcile two denominators before diffing them.** A shadow log counted 8,759 articles where the corresponding `filtered_*.jsonl` held 8,283 — the gap is `source_filter`'s post-scoring exclusions, which are scored but discarded. Reading the two as the same set put investment_risk's prefilter rate 0.129 off. `memory/nexusmind-data-sources.md`.

### 1. Prompt design
- **"max_score" cap read as advisory → oracle emitted raw scores.** Caps must be ARITHMETIC ("no dimension may exceed X"), and verify on a calibration sample before labeling. Or express as a per-dim SUBTRACTION (soft penalty, ADR-015) — the oracle follows those. gotcha 2026-05-29 / 2026-07-08.
- **Abstract carve-out language parsed too narrowly.** Enumerate carve-outs exhaustively + one contrastive example each. gotcha 2026-05-29.
- **Oracle outputs SCORES only** (0–10 per dim), never tiers — so thresholds change without re-labeling (ADR-016). Lenses overlap; never exclude adjacent-lens content (ADR-015).

### 2. Training data
- **Trained on the raw feed → 99%+ noise, student predicts zero.** ENRICH: screen the corpus for signal-bearing articles first (ADR-003), use e5-seed screening for needles (ADR-011), active-learning for rare tiers (ADR-005). Raw nature_recovery is ~0.3% MEDIUM+; training is enriched to ~15%.
- **Val set is NOT production-representative** (enriched) — don't fit normalization or read "real" rarity off it. ADR-014.

### 3. Metrics (needle filters especially)
- **Judged by MAE → shipped a floor-predictor that surfaces nothing.** For needle filters (MEDIUM+ < ~25%), MAE is the wrong yardstick — a "no to everything" model wins MAE and is useless. Use **Recall@k / NDCG@k / FN@MEDIUM+**. MAE is fine only for balanced filters. gotcha "MAE Is Misleading", dev-guide Issue 4.

### 4. Stage-1 probe (hybrid inference, ADR-006) — **REQUIRED for needle-in-haystack filters**

**Gate check before deploy: `probe/embedding_probe_e5small.pkl` must exist.**
A 1B-param model cannot simultaneously screen for topic relevance AND score
dimensional quality in a single forward pass. The solutions v4 quality gate
(2026-07-26) proved this: without the probe, 27% of medium+ articles were
policy/regulation false positives. The e5 probe handles screening; the model
only has to score. See `memory/gotcha-log.md` 2026-07-26 entry.

- **Probe trained as L1 regression → floor-collapsed, dropped needles.** Train it **recall-first** on the FULL labeled set (`scripts/train_probe.py --objective recall`): binary MEDIUM+ target, class-weighted BCE, threshold from the val recall curve at a target FN — not by minimizing error. Report FN@MEDIUM+, not probe MAE. `feedback-probe-training-data`.
- The shared `EmbeddingStage` screens on `weighted_avg(6-dim) >= threshold` and does NOT apply the gatekeeper at Stage 1 — keep the 6-dim output contract; don't change shared math for one filter. dev-guide Phase 6c.
- **Commit the probe pkl** (`filters/<name>/v<N>/probe/*.pkl`) — it's ~0.5 MB, needed for hybrid inference, and the source package isn't reproducible without it. As of 2026-07-10 the `.gitignore` commits filter probes by default (the old blanket `filters/**/probe/` + `*.pkl` double-ignore was fixed with a `!filters/*/v*/probe/*.pkl` negation); just confirm `git status` shows it staged.

#### 4a. Probe-split retraining — the improvement loop for deployed filters

Once a filter is live, you can improve it without starting from scratch. The key insight:
**the probe knows which articles are out-of-domain, and those articles are free to zero out
in training.** The oracle only needs to re-label the mid-range where the model and probe
disagree.

**When to use:** a deployed filter has too many false positives (low precision) or
too many false negatives (low recall), and you want to improve both without a full
re-labeling campaign.

**The method** (proven on solutions v6, 2026-07-26):

1. **Score the full production corpus** with the current probe + model. Every article
   now has a probe score and a model score.
2. **Zero out probe-negatives in training.** Articles the probe correctly screened out
   are non-solutions — set their oracle labels to all-zero. These cost nothing (no
   oracle re-scoring needed).
3. **Re-score the mid-range.** Articles where the probe passes but the model score
   is in the ambiguous band (roughly raw 1.5–4.5 for a 0–10 scale) are the ones worth
   re-labeling. Use a **tightened oracle prompt** (same dimensions, sharper
   critical-filters — close the blind spots you found in production). These cost
   oracle money (~$0.001/article) but are a small fraction of the corpus.
4. **Keep probe-high + model-high articles as-is** — the model already gets them right.
5. **Retrain on the cleaned corpus.** The combination of zeroed noise + re-scored
   mid-range + kept high-quality positives produces a model with better precision AND
   better recall.

**Results (solutions v6):** 702 false positives dropped from training, 2,401 articles
re-scored ($2.96), val MAE 0.564→0.476, gate recall 0.559→0.671, gate F1 0.647→0.739.
The production score distribution shifted from bimodal (median 0.0, spike at 7–10) to
continuous (median 0.17, gradual taper).

**Important:** the probe itself stays unchanged. This technique improves the Stage-2
model; the Stage-1 probe is a separate recall-first training problem (§4).

#### 4b. Production-feedback retraining — the same pattern without a probe

The probe-split pattern assumes a runtime probe that partitions the corpus for free.
Not every filter has one — sklearn-MLP filters (obituary detector, commerce prefilter)
are single-stage: embed → classify → score. But the same principle applies: **the model's
own production predictions tell you where to spend labeling budget.**

**When to use:** a deployed single-stage filter is flagging articles in production, and
you've verified (via panel or spot-check) that some flags are false positives. You want
to fix the error pattern without a full re-labeling campaign.

**The method** (obituary detector v3→v4, 2026-07-27):

1. **Shadow-deploy the model** on the production stream. Every article gets a score;
   articles above the enforcement threshold are candidate blocks.
2. **Collect the flagged articles** — these are the model's production positives. They
   represent the distribution the model actually faces, not the training distribution.
3. **Panel-verify a sample.** A multi-model blind panel (or owner spot-check) labels
   each flagged article against the labeling rule. FPs are articles the model would
   wrongly block; TPs confirm the model is working.
4. **Add confirmed FPs as hard negatives to training.** You already know they're wrong —
   no oracle re-scoring needed. Each FP is one row: `label: negative`, same features.
5. **Retrain on the augmented corpus.** The model now has explicit counterexamples for
   the error pattern. For sklearn-MLP filters this is a full retrain (same as §4a step 5);
   for fine-tuned models it's a fine-tuning epoch on the augmented set.

**Results (obituary detector ovr.news investigation, 2026-07-27):** 203 ovr.news
borderlines scored with v3 MLP → 3 flagged at ≥0.95 threshold, all 3 confirmed FPs
(historical legacy/tribute pieces in Greek/Spanish/Chinese — the model confuses
posthumous-legacy language with obituary language in non-English text). 5 more FPs
in the 0.70–0.90 band. Adding these 8 hard negatives costs $0 in oracle budget
(the labels come from the investigation, not from re-scoring) and closes a known
multilingual blind spot. Same pattern as §4a step 2–5 but at article-scale instead
of corpus-scale, and the "uncertainty oracle" is the model score threshold, not a
probe-model disagreement band.

**How this differs from probe-split (§4a):**

| | Probe-split (§4a) | Production-feedback (§4b) |
|---|---|---|
| Acquisition function | Probe-model disagreement band | Model score ≥ threshold |
| Scale | Corpus-wide (2,401 re-scored) | Article-scale (8–50 FPs) |
| Oracle cost | Yes — re-score mid-range with tightened prompt | Usually none — FPs confirmed by panel |
| Zeroing step | Yes — probe-negatives zeroed in training | No — no probe to partition with |
| Best for | Improving recall AND precision simultaneously | Fixing a specific production error pattern |
| Example | solutions v6 (MAE 0.564→0.476) | obituary detector v3→v4 (multilingual legacy FP) |

The two patterns compose: use §4b for quick targeted fixes, escalate to §4a when the
error pattern is broad enough to justify corpus-wide re-scoring.

### 5. Calibration + the top band
- **Fit `calibration.json` after every training run** (per-dim isotonic on val, ADR-008). Auto-loaded by the base scorer. Commit it.
- **Top of the scale is unreachable** (data density: ~2 articles at 8–10). Calibration can't invent range. Clip/ceiling the top; do NOT per-band-isotonic 2–3 points. Fix = more high-band data (active learning), not loss tricks.
- **Retrained models produce compressed raw scores — that's correct, don't stretch.** A model trained on a probe-split corpus (false positives zeroed out) naturally maxes at ~5–6 on the raw 0–10 scale, not 10. The old inflated scores came from training on noise — the model learned to shout to be heard. The compressed range is a *better* representation (cleaner signal, continuous distribution, no bimodal spike). Do NOT fight it with `score_scale_factor` — set it to 1.0 and let `normalization.json` handle the 0–10 mapping (ADR-014). Stretching via scale factor recreates the v2 trap: inflated scores defeat the gatekeeper/threshold design. `feedback-score-compression-is-correct`, solutions v6.

### 6. Cross-filter comparability

- **The complete method (math, fit convention, guard table, reproduction steps, incident numbers) is `docs/NORMALIZATION_METHOD.md`** — the canonical reference; this section is the operational digest.
- **Read `docs/adr/014-cross-filter-percentile-normalization.md` before touching normalization.** Everything below is a consequence of it, and on 2026-07-14 an agent spent hours "discovering" a bug that ADR-014 specifies on purpose. The three things it gets wrong when unread:
  - **Normalization exists ONLY for ovr.news** — HOME-tab cross-lens ranking and article-tab assignment. It is *not* a filter-quality mechanism. Uplifting passes 62.8% MEDIUM+ and nature_recovery 0.3%, so raw scores are not comparable across lenses; percentile rank makes "how exceptional is this *for its own lens*" comparable. Don't reason about it as if it gates quality.
  - **Tier is REASSIGNED on the normalized score, by design** (ADR-014's pipeline: calibrate → weighted average → gatekeeper → normalize → *reassign tier* → display_rank). So **`raw >= threshold` together with `tier: low` is CORRECT, not a bug** — the article is at the bottom of its own MEDIUM+ population. Both an agent and a review model read this as a defect on the same day. `production_scorer.py`'s module docstring explains it; read that before filing anything.
  - **Fit at `raw >= the filter's own tier threshold`** — that is what ADR-014's "production MEDIUM+ data" means. 7 of 10 fitted files sit at exactly `raw_min == 4.0` (the other 3 are the incident exemptions). This is now enforced: `tests/unit/test_normalization_invariant.py`.

- **`raw_min` off the tier threshold is the only normalization failure this project has ever had — in both directions.** Fit **too low** → sub-visibility content maps into the visible band: nature_recovery v2 at 1.5 (fit-set median 2.19) mapped correctly-scored doom at raw 2.2–3.3 to normalized 5.2–8.3, put decline stories on the Recovery lens at 8.34/10, was misdiagnosed as a *model* failure, and spawned a keyword cap that took 14 months to retire (**NexusMind#161**). Fit **too high** → everything between the threshold and `raw_min` clamps to ~0 via `np.interp`'s edge behaviour: foresight v1 at 5.01 sent raw 4.60 → wavg 0.02 (**NexusMind#205**). Guards now exist on both sides — `MAX_NORMALIZATION_RAW_MIN=4.5` at load, and the fitter refuses `--min-score` below the op-point — but the invariant test is what catches it at commit time. Since 2026-07-16 the fitter also **anchors** the CDF's lower edge to the op-point (`raw_min == op_point` by construction, dense or sparse), so `raw_min` can no longer drift; the bias signal moved to `stats.sample_min` (lowest article actually observed) — a `sample_min` far above the op-point means the fit population never reached the visibility threshold (the #205 root cause; the fitter hard-blocks it above 4.5 and the invariant test rejects it in a package). Guard-relaxed fits require `--analysis-only` with an `--out` not named `normalization.json`.

- **Scope the fit to one version.** `fit_normalization.py` now defaults `--filter-version` to the config's own version. It previously defaulted to None and the documented command omitted it, so a fit blended distinct models' distributions: fitting nature_recovery v4 against the live rolling window pulls in **114,252** articles from other versions. Two sessions were burned on CDFs that were quietly blended.

- **A fit under 200 articles is not a fit.** `MIN_NORMALIZATION_ARTICLES=200`; below it ProductionScorer silently falls back to linear `score_scale_factor`, so a thin fit yields a file that looks deployed and is inert. The fitter now refuses. For a needle filter that's weeks of live accumulation — don't wait, rescore a production-representative historical harvest (below).
- **Linearly rescaling each filter to 0–10 → the compressed filter hijacks the shared feed.** Calibration is within-filter (vs its oracle); cross-filter comparison needs **percentile normalization** from the *production* CDF (ADR-014), non-linear, refit per version. Don't retry z-score / P99 / val-CDF (all tested-dead, `calibration-history.md`).
- **A fresh version ships without `normalization.json` → a weeks-long cold-start where it's mis-ranked against every other lens.** With no normalization, `production_scorer.py` emits RAW `weighted_average`; every OTHER lens emits *normalized* scores. Cross-lens assignment (ovr `canonical-lens.ts` picks the highest `weighted_average` across scorers) and ovr's uniform display gate (`ranking.displayScoreThreshold`, calibrated for normalized scores) then both treat the new filter unfairly — under-ranked and under-shown — until ≥200 production MEDIUM+ accrue, which is **weeks for a needle** (nature ≈ 0.3% MEDIUM+ → ~3–4/batch). **Close the cold-start at deploy: rescore a *production-representative historical harvest* with the new model to synthesize the production CDF, then fit `normalization.json` before go-live** — don't wait for live accumulation. The corpus exists (FluxusSource `~/local_dev/FluxusSource/data`, 1.2 GB; NexusMind filtered output, 100K+ articles). **It must be at the production base rate** (~0.3% MEDIUM+ → ~145K rescored articles to reach 200 MEDIUM+), NOT the enriched training/val set (§2 — enrichment skews the CDF harsh). `production_scorer.py`'s `MIN_NORMALIZATION_ARTICLES=200` guard enforces this: a thin fit (e.g. 33 articles) is silently rejected and the filter stays raw. Why this wasn't the default: ADR-014 framed normalization as fit-from-*live*-production and the doc encoded "wait for ≥200 production articles" — nobody separated "don't use *enriched* data" (true) from "you *can* rescore *historical production* data now" (also true). **Evidence:** nature_recovery v4 shipped raw-only 2026-07-10; for the ~10-day v2→v4 window overlap, still-in-window *inflated* v2 scores out-ranked fresh v4 articles on ovr → "no new nature articles" even though v4 was producing *more* genuine MEDIUM+ than v2 (v2's fuller feed was ~90% normalization inflation of raw≈2 tier=low articles). gotcha 2026-07-11.

### 7. The deploy gate (trust)
- **There is a measured noise floor under every score comparison: `|Δ| ≤ 0.16`.** A score is **not a function of the article alone** — it also depends on which batch the article was scored in. Same model, same weights, same GPU, same process; only batch composition differs (#95, measured 2026-08-03 on real Gemma-3-1B + LoRA, 120 production articles). Consequences, in order of how easily they bite:
  - **A run-to-run difference below ~0.1 near an op-point is indistinguishable from noise.** Do not report one as an effect. This applies to ground-truth gates, FN-delta comparisons, normalization CDF fits, and before/after deploy checks alike.
  - It **changes decisions**, not just digits: re-scoring only the band within ±0.30 of the op-point flipped the verdict or tier for **7.1%** of `solutions v6` (2/28) and **9.1%** of `uplifting v7` (3/33). Flips occurred within 0.077 / 0.039 of the op-point.
  - Corpus-wide the share is small (0.07% / 0.32%), so this is a **measurement-trust problem, not a reader-visible one**. Size your response accordingly.
  - Since 2026-08-03 NexusMind seeds its per-cycle shuffle (`NEXUSMIND_RUN_SEED`, logged in the start banner), so **a cycle can be replayed exactly**. That does *not* make scores stable across cycles — the next cycle reshuffles. Replay the seed when you need two runs to be comparable.
  - Sibling, different cause, same magnitude: cross-box score skew |0.16| (gotcha 2026-07-30). Do not compare scores produced on different machines.
  - **The decision rule (owner, 2026-08-06 — #95 step 2).** Pinning a batch size was never available: `DEFAULT_BATCH_SIZE = 16` is already fixed and never varies in production; the variable is batch *composition*. So the floor is not removed, it is **budgeted for**. An article predicted within **0.16** of the surfacing threshold is **indeterminate** — its verdict is an artifact of the batch it landed in. Every metric computed at that threshold therefore carries a band, and **two models whose bands overlap are NOT DISTINGUISHABLE**, whatever their point estimates say. `scripts/gate/ground_truth_gate.py` computes and prints this automatically (`--noise-floor`, default 0.16; pass 0 only to reproduce a pre-2026-08-06 run). Worked example, `solutions v6` on its own held-out test set: 19 of 1,032 articles indeterminate → **F1 0.739 [0.712, 0.771]**, recall 0.671 [0.659, 0.707]. A candidate landing anywhere inside that band has not beaten v6.
  - **Not attempted, still open:** whether fixed-length padding (rather than padding to the longest article *in the batch*) would make scores a function of the article alone. Falsifiable in a few hours on GPU; deferred by owner decision 2026-08-06 in favour of the band above.
- **Gate judged the candidate against the PRIOR model → false FAIL.** Judge against **held-out ORACLE ground truth** (the oracle you chose = the editorial line), not the previous model. `scripts/gate/ground_truth_gate.py`, ADR-021.
- **Reference cohort was a different oracle's labels** (a `_v2_split`-tagged Gemini cohort +1.775 inflated) → the whole "12 student errors" was an artifact. On any surprising FAIL, **reproduce** — read the actual per-item labels before retraining. gotcha 2026-07-09, augmented-engineering#25.
- **"unit-tested"/"promoted to X.md" claimed but the file didn't exist.** A claim is false until the artifact exists — grep for it. `feedback-claim-requires-verify`.
- **Run the multi-agent review battery BEFORE any paid oracle run or "verified" claim**, not after. gotcha 2026-07-08.
- **Gate file cross-contamination: `ground_truth_gate.json` is filter-specific, not a shared template.** The gate script's `--report` path must point to the correct filter's directory. Running the gate for `solutions/v6` and writing to `nature_recovery/v4/ground_truth_gate.json` silently replaces nr's gate results with solutions data (found 2026-07-27: nr v4's gate file had solutions v6 model data with threshold 2.25 instead of nr's 3.75). Verify after every gate run: the threshold, model names, and n_labeled must match the filter. `feedback-gate-file-hygiene`.

### 8. Deploy (the outage-prone part — follow the checklist below)
- **Version-bump: inference modules still imported vN-1 → crashed the real entrypoint.** Repoint imports AND the `inference_hub.py` `repo_id: str = "...-vN"` default; construct the REAL scorer class (not `load_filter_package`, which masks stale imports by name-substring). `verify_filter_package.py` catches the repo_id. gotcha 2026-07-08, cluster #44/#52.
- **Keep PEFT adapters in OLD key format** (`.lora_A.weight`, `score.weight`). Never run `resave_adapter.py` before Hub upload (ADR-007). Verify: 0 `.default.` keys.
- **A config value read by NO code is inert — grepping for it "verifies" nothing.** nature_recovery v4's tuned operating point (`scoring.tiers.medium.threshold: 3.75`) was consumed by zero scoring code; the runtime `TIER_THRESHOLDS` hardcoded medium=4.0, so v4 ran at the un-tuned 4.0 for its whole deploy while every doc claimed 3.75 (ovr.news hides tier=low, so the [3.75,4.0) band was scored+hidden). The deploy check was `grep -q '3.75' config.yaml` — it passed on the inert field. Verify a config value is actually **read + applied at runtime** (trace it to the code path, or assert the live behavior it should produce), never that the string exists. Same shape as the score_scale_factor pit below. Found by the multi-model review, 2026-07-10 (F1).
- **A fresh version must ship `score_scale_factor: 1.0` AND no `normalization.json`.** Production (`production_scorer.py`) applies `score_scale_factor` as the linear fallback when normalization.json is absent — a stale v2 value silently stretches scores + defeats the gatekeeper/threshold design. Only a LIVE-scoring check catches it (the base-scorer smoke test skips the wrapper). gotcha 2026-07-10.
- **Scaffolded `normalization.json` was a stale v2 copy** → would normalize vN through the old CDF. A fresh version ships with NO normalization.json; refit on ≥200 vN production articles — **or synthesize the CDF at deploy via a production-representative historical rescore (§6) to avoid the weeks-long cold-start.** gotcha 2026-07-09, ADR-014.
- **`deploy_filters.sh` excludes `*/model/`** (#67) → code lands without weights → strict startup weight-check crashes the WHOLE scorer (discovery uses LATEST version, so a new dir auto-activates). **Pre-place the model** on gpu-server before the rsync (it's preserved by the exclude). gotcha #67 + investment-risk symlink outages.
- **Same-seed re-train ≠ the evaluated model** (CUDA nondeterminism gave recall 0.55 vs 0.67). Back up the approved model+calibration+metadata together at approval time; if you must re-train, re-run the gate on the new weights. gotcha 2026-07-09.
- **`deploy_to_nexusmind.sh` swept unrelated WIP / is Windows-pathed.** Explicit-stage only the deploy paths; watch `filters/common` rsync for contamination (obituary_detector, 2026-07-09); it still needs Linux porting (`C:/local_dev`, `python`→`python3`). gotcha 2026-05-23.
- **`.nexusmind-owns` empty by default** — production-runtime concerns live in NexusMind's `production_scorer.py` wrapper, not in shared `filters/common` math. Sync common freely; don't let a manifest hide 18-day silent divergence. gotcha "Manifest as Anti-Pattern".

---

## Deploy safety checklist (each item = a past outage it prevents)

Canonical chain: **llm-distillery git → NexusMind git → sadalsuud `deploy_filters.sh` → gpu-server.** Full write-up: `docs/nature_recovery_v4_DEPLOY_COMPLETION.md`.

1. `verify_filter_package.py --check-hub` passes (imports / repo_id / version / Hub fresh). *(→ #44)*
2. Ground-truth gate PASS vs held-out oracle labels; no regression vs incumbent. *(→ ADR-021)*
3. Remove stale `normalization.json` if the version is fresh. *(→ ADR-014)*
4. NexusMind commit is **only** the filter dir — no model weights (gitignored), no `filters/common` contamination. *(→ 2026-05-23)*
5. **Pre-place `model/` on gpu-server** before `deploy_filters.sh` (survives the `*/model/` exclude). *(→ #67)* — **ENFORCED since 2026-08-13**: `preflight_deploy_guards.py` guard D probes gpu-server for `{filter}/{version}/model/adapter_model.safetensors` and aborts the deploy if it is absent, or if it cannot ask (fails closed; `--weights-preplaced` is the offline override). This was an instruction from #67's close in 2026-05-31 until then, and the consequence has grown since: the scorer validates weights for **every discovered filter at startup**, so a weightless highest version means the scorer never starts and the cycle scores nothing for all six — unattended, since `deploy_filters.sh` is `ExecStartPre` on the 4-hourly `nexusmind.service`.
6. Scorer restarts healthy: `/health` OK + **all N filters have weights** + live smoke test scores the fixture in range (wrong weights → <1.0). *(→ investment-risk outages, systemd-context gotcha)*
7. Keep the prior version as fallback (rollback = delete the new dir; discovery falls back). Normalization refits once ≥200 production articles — **or fit at deploy from a production-representative historical rescore (§6) to avoid the cold-start where the new version is mis-ranked against normalized lenses.** *(→ 18-day normalization regression, 2026-07-11 cold-start)*
8. Full Fluxus→Nexus→ovr run confirms on the next harvest cycle — verify with a **disk-based** check, never a transient port. *(→ 2026-07-04 phantom-outage gotcha)*

---

## When you point me here

Say *"new filter"* or *"retrain <filter>"* or *"improve <filter>"* and start from this page. I will:

**New filter / full retrain:**
1. Read this + the canonical `nature_recovery v4` package.
2. Run the oracle bake-off (bias first), design/verify the prompt, enrich the data.
3. Train student + recall-first probe, judge on ranking metrics, calibrate.
4. Gate against held-out oracle ground truth, then deploy via the checklist above.

**Improve a deployed filter (probe-split retrain, §4a):**
1. Score the full production corpus with current probe + model.
2. Zero out probe-negatives in training (free — they're noise).
3. Re-score the probe-pass / model-uncertain mid-range with a tightened oracle prompt.
4. Retrain on the cleaned corpus (zeroed negatives + re-scored mid-range + kept positives).
5. Re-run the gate, compare against incumbent, deploy via the checklist.

**Fix a specific production error pattern (production-feedback retrain, §4b):**
1. Shadow-deploy, collect model-flagged articles from production.
2. Panel-verify a sample — confirm which flags are FPs.
3. Add confirmed FPs as hard negatives to training ($0 oracle cost).
4. Retrain on the augmented corpus.
5. Re-run the gate, confirm the error pattern is closed, deploy via the checklist.
