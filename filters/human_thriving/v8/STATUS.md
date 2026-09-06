# human_thriving v8 — STATUS

**NOT DEPLOYED. TRAINED, PROBED, CALIBRATED AND GATE-MEASURED.** Labelled, adjudicated; prompt settled at v8.4. Last updated 2026-09-06.

✅ **It can score an article ON `b650-gpu`.** `base_scorer.py`, `inference.py`,
`inference_hybrid.py`, `probe/embedding_probe_e5small.pkl` and `calibration.json` all exist
as of 2026-09-04 (**EXP-016**, `docs/evidence/2026-09-04-v8-probe-calibration/`).
⛔ **The weights are not in this repo** (gitignored as large model checkpoints,
`.gitignore` § *Model checkpoints (large files)*; ⚠️ **NOT #97** — that issue is the TDM assessment and it concluded the
models are CLEAN, corrected 2026-09-05) — they live on `b650-gpu` only, so
a fresh clone loads the package and cannot run the student. "Scoreable" is a statement about
one host.

✅ **THE ADR-021 DEPLOY GATE HAS RUN, 2026-09-06 (EXP-026).** Against held-out ORACLE ground
truth at the ruled op-point, on **CUDA**: **recall 0.343, specificity 0.992**, precision 0.706,
n=660, 35 positives (5.30% unweighted). `ground_truth_gate.json`,
`docs/evidence/2026-09-06-v8-deploy-gate/`.
⛔ **READ THE SPECIFICITY FIRST — we prioritise HIGH CERTAINTY over HIGH DETECTION.** The
0.343 is the decision working, not the model failing: ADR-023 chooses being right about what
is surfaced over surfacing more, because a false positive reaches a reader and a false
negative is invisible. v8 surfaces about a third of what the oracle calls on-lens and is
right about **70%** of what it does surface. **A change that raises recall here without
holding specificity is a regression**, and "recall is low" is not on its own a finding.
⛔ **Do NOT set that recall beside the fleet's 0.59–0.72** — v7 and v8 do not share a positive
class (Jaccard **0.246** on these same rows), so those are two quantities with one name.
✅ **The op-point is no longer inherited**: **4.50 on the CALIBRATED scale**, re-derived on v8's
own held-out split and ratified by the owner 2026-09-05
(`docs/decisions/2026-09-05-v8-op-point.md`). ⚠️ Gate B-A's **k** is still inherited rather
than measured.

⛔ **The doc set is still incomplete** (`memory/filter-doc-standard.md`). `config.yaml`, the
prompt and now `calibration_report.md` are here; `DEEP_ROOTS.md`, `README.md` and
`README_MODEL.md` are still owed, and Phase F1 of the plan gates shipping on package parity
with `nature_recovery v4`. This file exists because v8's state is complicated enough that
"not deployed" is not a useful summary.

## Where it actually stands

| phase | state |
|---|---|
| Prompt (Phase A) | ✅ **`prompt-candidate-tail.md` ADOPTED** 2026-08-30, on the label argument |
| Corpus (Phase 0) | ✅ 6,590 drawn, manifested, `sha256 5e2cf729…`; guard rows excluded by construction |
| Oracle | ✅ **DeepSeek**, ruled 2026-09-01 (`docs/decisions/2026-09-01-v8-oracle-ruling.md`) |
| Labels (Phase B) | ✅ **6,586 at k=3, $6.8853**, `--aggregate all`. `EXP-010` |
| Label review | ✅ 2026-09-02 — `docs/evidence/2026-09-02-phase-b-label-review/` |
| Class-A adjudication | ✅ 2026-09-03 — v8 demotes **32 of 47**; the 15 survivors are 11 events. `docs/evidence/2026-09-03-classA-supplement-adjudication/` |
| Phase B2 hard negatives | ⚠️ **12 rows of headroom, not a corpus** — the draw took 47 of the 59 available and 32 already carry low labels. `docs/evidence/2026-09-03-phase-b2-headroom/` |
| Phase C **train** | ✅ **2026-09-04, EXP-015.** Epoch 4 of 6, selected on `recall_medium` @4.5. Weights on `b650-gpu` only: `~/llm-distillery/filters/human_thriving/v8/model/`, MAE-selected arm preserved at `model_baseline_mae/`. `docs/evidence/2026-09-04-v8-checkpoint-selection/` |
| Phase C **probe** | ✅ **2026-09-04, EXP-016.** e5-small, recall objective, seed 42, CPU. Threshold **1.75**, chosen to hold the ruled ~88.6% routing (weighted **0.8876** val / **0.8935** test), FN@MEDIUM+ **0/31** and **0/35**. ⛔ The threshold is pinned to this exact probe — a seed change moves routing 14 pp |
| Phase C **calibrate** | ✅ **2026-09-04, EXP-016.** Isotonic on val. ⛔ **Does NOT improve held-out MAE** (test 0.6029 → 0.6142) and the two arms are the SAME RANKER (Spearman 0.9977, AUC 0.9474 → 0.9488). Ships per ADR-008 + ADR-023's specificity tie-break, not because it helped. `calibration_report.md` |
| Phase D gate | ⛔ not started. ⚠️ **Criterion 1 is NOT stably failing** — the 4.400 was a k=3 mean on a coin-toss row; at k=6 under unchanged v8 it is **3.608 ± 2.560, PASS**. `docs/evidence/2026-09-03-v8-1-gate/` |
| **ADR-021 deploy gate** | ✅ **2026-09-06, EXP-026.** recall **0.343** / spec **0.992** at 4.50 calibrated, on **CUDA**. ⭐ The device does not matter here — CPU and CUDA give **0 verdict flips** and identical confusion matrices (max \|Δ\| 0.1428 calibrated), which had to be measured because v7's device term reached 0.1956 and flipped 3 rows at the same bar (#104) |
| Phase E normalization | ⛔ **BLOCKED, and the ordering is why** — `fit_normalization.py` reads NexusMind production output and needs ≥200 rows above the op-point; sadalsuud has **no `human_thriving`** at all. Normalization comes AFTER deployment, as it did for `solutions v6`. ⛔ Do not substitute the test split: it is a 25.1× design-weighted sample |
| Phase F deploy | ⛔ not started — but no longer blocked on a missing gate number |

⚠️ **The labelled corpus is 6,586, not 6,590** — four scrape-junk skips, all JavaScript-required
boilerplate at 357–489 chars, all *above* the 300-char floor.

## NM#319 — the enrichment gate, answered in two regimes (2026-09-06)

NexusMind gates post-scoring enrichment on `weighted_average >= 4.0`, and that field is the
**normalized** score (`production_scorer.py:17-18`, `article_fetcher.py:1374`).

- **At deploy, before Phase E:** v8 has no `normalization.json` and `score_scale_factor: 1.0`,
  so the raw score passes straight through and **every surfaced article (raw ≥ 4.5) clears the
  4.0 gate.** Nothing to do.
- **After Phase E:** the fitter anchors the CDF's lower edge to the op-point, so
  `stats.raw_min == 4.5` and **normalized(4.5) = 0.0 by construction** — the gate then bites in
  the middle of the surfaced population. Measured on `uplifting v7`, already in that state at
  the identical op-point, over 82 production cycles 2026-08-23 → 2026-09-06 (251,461 rows):
  **18,041 surface (7.17%), and only 60.0% of them clear normalized ≥ 4.0** — 7,224 surfaced
  articles are silently un-enriched, the gate's effective bar being raw ≈ 5.05–5.13.

⚠️ That is v7's CDF as a proxy; v8's share will differ, the mechanism will not. It is not a v8
regression — it is what percentile normalization plus a 4.0 gate already does — but it means
**fitting normalization is the step that takes ~40% of surfaced articles below the enrichment
gate**, and whether that is intended is an owner question.
`docs/evidence/2026-09-06-v8-deploy-gate/README.md` §3.

## ✅ Pre-deploy parity against the five deployed packages (2026-09-04)

Compared part-by-part against `uplifting v7`, `cultural_discovery v5`, `belonging v1`,
`nature_recovery v4` and `solutions v6` — the packages that demonstrably work in production.
**No part of the scorer is missing or misimplemented.** Class attributes, methods, runtime
constants, probe dimensionality and every `config.yaml` key NexusMind reads all check out;
the one constant v8 lacks (`DEFAULT_THRESHOLD`) is deliberately removed and guarded.
⛔ `verify_filter_package.py`'s **7/7 is not this evidence** — it checks presence, not mutual
consistency (`566254b`). Full comparison:
`docs/evidence/2026-09-04-v8-probe-calibration/PREDEPLOY_PARITY.md`.

⭐ **Two invariants nobody was checking are now pinned fleet-wide**
(`tests/unit/test_filter_package_consistency.py`), both silent-failure shapes:
1. **`config.yaml`'s `preprocessing.head_tail` must match `training_metadata.json`'s
   `use_head_tail`** — otherwise inference truncates articles differently than training did,
   with no error. v8 is consistent (both false) but **consistent by ABSENCE**: the five
   deployed filters all declare `enabled: true`, v8 declares no block. ⛔ **H-V8-15 arm (b) is
   `--use-head-tail`** — retrain with it and forget the config block and the model is silently
   mis-fed. The test fails in exactly that case.
2. **The probe's `output_dim` must equal the filter's dimension count** — `EmbeddingStage`
   rebuilds from the pickle's own config, so a mismatched probe loads fine and weights the
   wrong slots. Not 6 everywhere: cd v5 is 5, solutions v6 is 7.

⚠️ **`prompt_hash` is `None`** for v8 (no `prompt-compressed.md`; `_compute_prompt_hash` looks
for that exact name). It feeds `get_metadata()`, which nothing in NexusMind reads — provenance
only. Resolve at Phase F **by copying, never renaming**.

## ⛔ Known-failing and known-missing, before anyone reads the state as green

- ✅ **PHASE C DID THE THING v8 EXISTS FOR — measured 2026-09-04 on held-out data.** Of the
  **87** test rows `uplifting v7` surfaced that the v8 oracle demotes, the student removes
  **79 (90.8%) raw / 82 (94.3%) calibrated**; AUC on those disputed rows is **0.8454 raw /
  0.8521 calibrated against v7's own 0.7218**, so it learned a distinction v7 lacked rather
  than merely scoring everything lower. Cost: of the **30** rows both definitions call
  positive it keeps **17 (56.7%) raw / 12 (40.0%) calibrated**. ⛔ Still open: the student
  under-learns class-A on the highest v7 rows — **2 of 6** score ~5 against an oracle ~1.
  `docs/evidence/2026-09-04-v8-probe-calibration/PHASE_C_REVIEW.md`.
- ⚠️ **Its numbers are not comparable to the fleet's.** Test @4.5 (n=660, 35 positives, 5.30%), both arms from one CPU forward
  pass: raw **recall 0.486 / spec 0.9856**, calibrated **recall 0.343 / spec 0.9920** — and the
  gate says the #95 bands **OVERLAP on recall, specificity and F1: NOT DISTINGUISHABLE**.
  ⛔ **DO NOT SET THESE BESIDE THE FLEET'S 0.59–0.72. That comparison is VOID** (corrected
  2026-09-04, `docs/evidence/2026-09-04-v8-probe-calibration/PHASE_C_REVIEW.md`): v7 and v8
  do not have the same positive class. On the same 660 rows v7 calls **117** positive and v8
  calls **35**, agreeing on **30** — **Jaccard 0.246**, v8 keeps **25.6%** of v7's positives.
  Recall is conditional on the true class, which is why it survives a change of base RATE and
  does **not** survive a change of DEFINITION. Two recalls of two different classes are two
  quantities with one name. ⭐ **And the low recall is not a defect to fix**: under ADR-023 it
  is the cheap error, and moving 4.5 → 4.0 buys 5 good articles while letting 7 junk ones back
  through — the wrong direction under the project's own loss function.
  ⛔ **CORRECTED 2026-09-06 — EXP-015's 0.514 raw is NOT a device difference.** This file said
  it was the CPU→CUDA **0.1956** term landing near the bar. Measured directly (EXP-026,
  `docs/evidence/2026-09-06-v8-deploy-gate/device_delta.py`): on this split CPU and CUDA give
  **0 verdict flips on both arms** and the same 17 TP, so the device cannot produce 18. Nor can
  the gatekeeper or the clamp — applying and removing them moves **0 rows** across 4.5 on either
  device. What differs is **the program**, in at least three ways at once: **dtype** (production
  holds 342 bfloat16 params against 364 fp32, score head included, read off the loaded object;
  `eval_ht_v8.py` forces `torch_dtype=torch.float32`), **adapter loading** (`load_lora_local` →
  `get_peft_model` + a hand-rolled remap vs `PeftModel.from_pretrained`) and **batch size**
  (16 vs 8). ⛔ **Only the dtype was measured to be PRESENT; none of the three was isolated**,
  so "it is the dtype" is the leading candidate and not a demonstrated cause. ⭐ **What is
  established is the part that matters: production serves bf16 through `load_lora_local` at
  batch 16 — this gate's own path — so 17 is production's number and 18 belongs to a program
  that is not what ships.** Neither is wrong; they are not the same measurement — but the
  reason recorded here was. `memory/filter-status.md`'s figures are post-calibration **and** post-gate — do
  not put any of these in that table.
- ⛔⛔ **4.5 ON THE CALIBRATED SCALE IS A STRICTER OPERATING POINT THAN 4.5 RAW.** Isotonic
  compresses the top (`human_wellbeing_impact` student max 7.9 → calibrated 6.8), so the same
  number flags **17** rows where raw flags **26** — a 35% cut in surfaced volume. The two arms
  are the same ranker (Spearman **0.9977**, AUC 0.9474 → 0.9488, every matched-volume recall
  difference ≤2 articles). **Carrying v7's 4.5 across is not "keeping the op-point"; it is
  silently tightening it.** ✅ **RE-DERIVED AND RATIFIED 2026-09-05, and the tightening is now
  the CHOSEN behaviour rather than an accident**: on the calibrated arm every step from 3.75
  up costs ~1 agreed-good article per junk article removed, and ADR-023 breaks a 1:1 trade
  toward specificity. 4.50 calibrated removes **94.3%** of what the v8 oracle says v7 was
  wrong to surface and keeps **12 of 30** both call good, spec **0.9920**; design-weighted,
  95.0% / 40.2%. ⚠️ The frontier bends at **3.50** (−3 good buys −11 junk) — that is where to
  go if volume is ever wanted, not 4.0 or 4.25, which buy it at par.
  `docs/decisions/2026-09-05-v8-op-point.md`.
- ⛔ **The Stage-1 threshold (1.75) is pinned to the exact probe it was derived against.**
  Same data, objective and code with `--seed 7` gives a probe on which 1.75 routes
  **0.7406/0.7567** instead of **0.8876/0.8935** — ~14 pp fewer articles reaching Stage 2,
  FN unchanged at 0. Stage 1 is silent, so there is no symptom. `config.yaml` records
  `probe_sha256` beside the threshold and `inference_hybrid.py` refuses to construct on a
  mismatch. **Retrain the probe → re-derive the threshold and regenerate BOTH hashes in one
  commit**: `config.yaml`'s `probe_sha256` *and* `probe/embedding_probe_e5small.pkl.sha256`
  (⚠️ `train_probe.py` does not write the companion file — do it by hand).
- ⚠️ **The multilingual question is half-answered, and the answered half is adverse.** At
  1.75 non-Latin content is routed to Stage 2 **less** often than Latin: design-weighted
  0.8218 (n=131) vs 0.8979 (n=1,187), **gap 0.0762, z = 2.65** (unweighted 0.0693, z 2.53;
  both SEs binomial, measured Kish deff 1.068). FN was **0 in every cell**, but on
  8 non-Latin positives the rule-of-three upper bound is **0.375** — the instrument could
  not have said otherwise. **Routing asymmetry confirmed; recall asymmetry not measured.**
  This is the layer that replaced the Latin-only keyword prefilter (ADR-018/019 Amendment
  2026-08-21). llm-distillery#141 is the blocker.
- ⛔⛔ **The checkpoint was NOT produced by any commit now on a branch.** It was trained by the
  tree that became `1878e7b` via `git commit --amend`, so the exact sha (`0697f5a`) is dangling
  and will not survive `git gc`. `1878e7b` resolves this filter to the same 4.5 and does not
  change `recall_at_k` at n=658, so the numbers reproduce — but *the verified artifact is not
  the shipped one* until it is retrained under a real commit. **Decide before Phase F: retrain
  (~90 min on b650) or record the exception.**
- ⚠️ **The two committed metadata files use the PRE-AMEND schema** (`select_metric`,
  `select_metric_available`, `medium_threshold`). `1878e7b` writes `requested_*` plus
  checkpoint-scoped fields and `checkpoint_saved`, so a future run's file will not match these
  key-for-key. Not drift — a schema change, dated here.
- ⚠️ **The epoch was chosen by a TIE-BREAK, not by the metric.** `recall_medium` saturates at
  **0.5806 across epochs 4, 5 and 6**; selection's strict `>` keeps the earliest. Epoch 6 is
  better on `recall_at_20` (0.65 vs 0.55) and NDCG. On test the two arms are **not
  distinguishable** — every gap is two articles, and they swap rank at 4.25.
  llm-distillery#144.

- ⛔⛔ **CORRECTED 2026-09-03: acceptance criterion 1 was never stably failing.** The 4.400
  that read as a FAIL is a **k=3 mean on a bimodal row**. At **k=6 under the unchanged v8
  prompt** the nursery row is **3.608, sd 2.560, 3 `in_scope` / 3 `response_to_harm` — a PASS**.
  With that sd the standard error at k=3 is **1.48** against a 0.55 margin, so the k=3 verdict
  never cleared its own band, which Gate B-A's rule requires. ⭐ **On a bimodal row a k=3 mean
  is a sample of a coin flip, not a measurement** (#135: the scope gate is a step function and
  `1/√k` does not describe it). The gate's k must be re-derived before Phase D.
- ✅ **`prompt-v8-4.md` is the settled prompt** (`sha c4705408c477`) — **B** (§2 commencement)
  + **C** (§3 jurisdiction) + **A3** (§5 nothing-has-taken-effect). Validated at **k=12** on all
  13 gate rows: Gate B-A **9/9**, worst class-A sd **2.250 → 0.205**, `in_scope` runs on class A
  **3 of 108 → 0**, no-regression **4/4**. ⭐ **The gain is variance, not verdict** — both
  prompts pass 9/9; v8.4 makes the labels stable.
- ⛔⛔ **D (§5 judicial relief) is DROPPED, so the convict-relief ruling is NOT implemented.**
  Three corpus rows keep their labels and decision 2 stands unexecuted until a wording is found
  that does not license a positive. **The four clauses are not additive**: each is individually
  safe, and their union scores the #91 origin row **5.921 with 12/12 `in_scope`** where v8 pins
  it at **0.900 sd 0.000**. Leave-one-out isolates a **B×D interaction** — D held the only
  sentence among the four that licenses a positive (*"the release **is** the repair and **scores
  normally**"*), and deleting that sentence helped but was not sufficient.
  ⭐ **Never validate a multi-clause prompt change by its parts**: ablate to attribute, validate
  the artifact you intend to ship. ⭐ A placebo of **+996 chars** of §1 restatement left the row
  at **0.883 ± 0.037**, refuting length and location — *a rule stated as a **test** inside a
  reasoning step becomes a question asked of every article; the same rule as a **category** in an
  exclusion list does not.* `docs/evidence/2026-09-03-v8-1-gate/` PART 2.
- **A v8.1 prompt fix is owed**, ~6 calls. ✅ **Ruled 2026-09-03** — the fix is on
  **commencement** (a policy change that has not taken effect is an announcement), bounded
  **inside §2**, not on prominence and not extended into §1
  (`docs/decisions/2026-09-03-v8-1-commencement-clause.md`). ⛔ **Unwritten and untested** —
  criterion 1 stays FAILING until it is measured, with the Travelodge row as negative control.
- ⭐ **A SECOND v8.1 candidate, distinct from the first**: §1's announcement rule is written in
  terms of **money** (*"funding secured, mobilised, pledged or allocated"*), so a **legislative
  proposal** has no rule pointing at it. Six above-op rows name a proposal, plan or
  *preparations* in the oracle's own `dominant_subject` and score 4.55–6.33 anyway.
- ✅ **The 47-row class-A supplement is ADJUDICATED** (2026-09-03). v8 demotes **32 of 47
  (68.1%)**; the 15 survivors are **11 distinct events**, one of which (the US removing Syria
  from its terrorism list) is **9 above-op rows corpus-wide**. Two owner questions remain: the
  Syria cluster under §3, and judicial relief granted to convicted offenders.
- ⚠️ **The prompt is not named `prompt-compressed.md`**, which is what `load_filter_spec` derives
  from `config.yaml` and what the doc standard's item 2 calls for. Every run so far passed
  `--prompt` explicitly. Left as-is on purpose: the 6,586 labels record
  `prompt_file: filters/human_thriving/v8/prompt-candidate-tail.md` as provenance, and renaming
  now would break that pointer. Resolve at Phase F, by copying rather than renaming.
- **`config.yaml` now carries the `hybrid_inference` block** (Phase C, 2026-09-04) and it is the
  **only filter in the repo where that key is live** — every other `inference_hybrid.py`
  carries a module-level `DEFAULT_THRESHOLD` and reads nothing. ⚠️ **The value is not 1.00
  across the fleet** (measured 2026-09-04: 0.75 / 1.00 / 1.225 / 1.25 / 1.50 / 2.25 / 2.50;
  only 2 of 13 are 1.00), and on `nature_recovery v4` the config says **3.225** against a
  runtime **0.75** — so "they agree today" is false where it matters. Still **no
  normalization anchor** (Phase E). `prefilter` and `content_type_caps` remain omitted **with
  the reason written where the block would be**.
- ⚠️ **`score_scale_factor` stays 1.0, and `fit_calibration.py` tried to change that.** Its
  default behaviour computes `10.0 / weighted_max` and edits `config.yaml`; on this run it
  produced **1.3787**, which with no `normalization.json` would stretch every score by 1.38×
  (`FILTER_PLAYBOOK` §8, ADR-014). Suppressed with the new `--no-config-update` and proven
  suppressed by an unchanged `sha256(config.yaml)`. ⛔ **Any filter fitted before its
  normalization gets the same edit** — the flag is opt-in, so the next person must pass it.

## Open questions that do not block

- **Plan §9 Q4** — is `social_cohesion_impact` at 0.20 right for Thriving? ⭐ Does **not** gate
  anything: a weight change needs no re-labelling (ADR-001), and dropping a dimension is free.
  Only *adding* one would force a re-score.
- **`benefit_distribution` has a median of exactly 0.00**, the only dimension that does. Watch at
  Phase C; not acting on it now.

## Provenance

Corpus and labels are **not in this repo** — article text at corpus scale (#97). They live at
`datasets/scored/human_thriving_v8/` (gitignored) and the corpus is staged on `b650-gpu`.
Journal: `docs/HUMAN_THRIVING_V8_JOURNAL.md`. Plan: `docs/HUMAN_THRIVING_V8_PLAN.md`.
