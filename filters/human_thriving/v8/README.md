# Human Thriving Filter v8

**Version**: 8.0
**Status**: ⛔ **NOT DEPLOYED** — trained, probed, calibrated and gate-measured. See `STATUS.md`.
**Question**: *Does this article contain a process that is going well **for people**, **now**?*
**Purpose**: Surface documented outcomes delivered to people — not emotional tone, not funding, not intent
**Target**: ovr.news **Thriving** tab (replacing `uplifting v7`, ADR-012 as amended)
**Oracle**: DeepSeek (`deepseek-chat`), ruled 2026-09-01
**Grounding**: `DEEP_ROOTS.md`. Prompt lineage: `PROMPTS.md`. Current prompt: `prompt-v8-4.md` (`c4705408c477`)

---

## ⛔ Read the specificity first

At the operating point, against held-out **oracle** ground truth (ADR-021 gate, 2026-09-06,
CUDA, n=660, 35 positives = 5.30% unweighted):

| | value | #95 band |
|---|---|---|
| **specificity** | **0.992** | [0.9872, 0.9952] |
| precision | 0.706 | [0.579, 0.833] |
| recall | 0.343 | [0.314, 0.429] |
| F1 | 0.462 | [0.407, 0.566] |

**The 0.343 is the project's loss function working, not the model failing.** ADR-023: a false
positive reaches a reader; a false negative is invisible and the slot refills. v8 surfaces
about a third of what the oracle calls on-lens and is right about **70%** of what it does
surface. **A change that raises recall here without holding specificity is a regression**, and
"recall is low" is not on its own a finding.

⛔ **Do not set that recall beside the fleet's 0.59–0.72.** v7 and v8 do not share a positive
class: on the same 660 rows v7 calls **117** positive, v8 calls **35**, and they agree on
**30** — Jaccard **0.246**. Recall is conditional on the true class, so it survives a change of
base *rate* and does **not** survive a change of *definition*. Two recalls of two different
classes are two quantities with one name.

Full gate output: `ground_truth_gate.json`, `docs/evidence/2026-09-06-v8-deploy-gate/`.

## What v8 is for

`uplifting v7` scores emotional register and reach. It surfaces an arrest, a pledge, a funding
round, a helpline, a policy announcement — anything with a hopeful shape — because none of its
dimensions ask whether *anyone actually received anything*.

v8 asks that question first and lets the answer veto everything else. The oracle prompt emits
`dominant_subject` and `scope_verdict` **before** any dimension, and any verdict other than
`in_scope` forces all six dimensions to 0–2:

| `scope_verdict` | means |
|---|---|
| `in_scope` | a process is going well for people, now — score normally |
| `harm_is_subject` | the dominant subject **or the occasion** is a harm, crime, bereavement, abuse, worsening statistic or institutional failure |
| `response_to_harm` | the only good news is a *response* to a harm, not repair delivered to people |
| `no_person_benefits` | the benefit reaches an animal, an institution, a market or a jurisdiction — not a person |
| `out_of_scope` | nothing has taken effect yet: proposal, draft law, plan, preparations |

⚠️ **`in_scope` is not the default.** If the prompt cannot name a process going well for people
in `dominant_subject`, the verdict is not `in_scope`.

**#107 narrows the consumer predicate further**: harm-answered-only and institution-beneficiary
content is out **even when v7 scored it high**. That narrowing is scoped, not reversed, and it
is what eliminated every pure-ecology candidate from the no-regression search.

### Measured: v8 does the thing it exists for

Of the **87** held-out test rows that `uplifting v7` surfaced and the v8 oracle demotes, the
student removes **82 (94.3%)** on the calibrated arm. On those disputed rows its AUC is
**0.8521** against v7's own **0.7218** — so it learned a distinction v7 lacked rather than
merely scoring everything lower. Cost: of the **30** rows both definitions call positive it
keeps **12 (40.0%)**.
`docs/evidence/2026-09-04-v8-probe-calibration/PHASE_C_REVIEW.md`.

## Dimensions (6)

Keys and weights are **v7's, carried verbatim** — the rewrite is in the prompt, not the
schema, so v8 is a drop-in for the training and scoring pipeline.

| # | Dimension | Weight | What it measures |
|---|-----------|--------|------------------|
| 1 | `human_wellbeing_impact` | 30% | Improvement in health, safety, livelihoods, or basic needs |
| 2 | `social_cohesion_impact` | 20% | Bonds among people: trust, belonging, cooperation between groups |
| 3 | `justice_rights_impact` | 15% | Rights expanded, accountability delivered, injustice actively addressed |
| 4 | `change_durability` | 15% | How lasting the change is: episodic, sustained, or structural |
| 5 | `evidence_level` | 10% | Verification **of the thriving outcome**, not general journalism quality |
| 6 | `benefit_distribution` | 10% | Distribution **of the benefit** — who receives it, not audience size |

Impact domains 65%, assessment 35% — the v7 rebalance, kept.

⚠️ **Open, and not blocking**: Plan §9 Q4 asks whether `social_cohesion_impact` at 0.20 is
right for a Thriving lens rather than a Belonging one. Carrying v7's weight is the null option,
not an answer. A weight change needs **no** re-labelling (ADR-001); only *adding* a dimension
would force a re-score.

⚠️ `benefit_distribution` has a **median of exactly 0.00**, the only dimension that does. That
is a base rate, not breakage (`memory/solutions-v6-dimension-hypotheses.md`).

## Operating point — 4.50 on the **calibrated** scale

Re-derived on v8's own held-out split and ratified by the owner 2026-09-05
(`docs/decisions/2026-09-05-v8-op-point.md`). It is **not** inherited from v7 by default.

⛔ **4.5 calibrated is a stricter point than 4.5 raw.** Isotonic compresses the top
(`human_wellbeing_impact` student max 7.9 → calibrated 6.8), so the same number flags **17**
rows where raw flags **26** — a 35% cut in surfaced volume. Carrying v7's 4.5 across is not
"keeping the op-point"; it is silently tightening it. The tightening is now the **chosen**
behaviour: every step from 3.75 up costs about one agreed-good article per junk article
removed, and ADR-023 breaks a 1:1 trade toward specificity.

⚠️ **If volume is ever wanted, the frontier bends at 3.50** (−3 good buys −11 junk) — go there,
not to 4.0 or 4.25, which buy it at par. 5.00 was never available:
`MAX_NORMALIZATION_RAW_MIN = 4.5`, strict `>`.

⛔ An operating point lives in **four** places and `config.yaml` is not the runtime one — see
CLAUDE.md § Hard Constraints before moving it.

## Two-stage inference

| stage | what | detail |
|---|---|---|
| 1 | e5-small embedding probe | recall objective, seed 42. Threshold **1.75** → ~88.8% of articles routed to Stage 2 (weighted 0.8876 val / 0.8935 test), FN@MEDIUM+ **0/31** val and **0/35** test |
| 2 | Gemma-3-1B + LoRA | 6-dimension regression, then per-dimension isotonic calibration |

⛔ **The 1.75 threshold is pinned to the exact probe it was derived against.** Same data,
objective and code with `--seed 7` gives a probe on which 1.75 routes 0.74/0.76 instead —
~14 pp fewer articles reaching Stage 2, with no symptom, because Stage 1 is silent.
`config.yaml` records `probe_sha256` beside the threshold and `inference_hybrid.py` refuses to
construct on a mismatch. Retraining the probe means re-deriving the threshold and regenerating
**both** hashes in one commit (`train_probe.py` does not write the `.sha256` companion — do it
by hand).

⚠️ **v8 ships no per-lens prefilter** (ADR-018/019 Amendment 2026-08-21). Keyword screening is
Latin-script only; the multilingual probe replaces it. `_load_prefilter` sets
`self.prefilter = None` deliberately — it is an `@abstractmethod`, so omitting it would raise
at scorer startup.

## Language coverage — half-answered, and the answered half is adverse

At threshold 1.75, non-Latin-script content is routed to Stage 2 **less** often than Latin:
design-weighted **0.8218** (n=131) vs **0.8979** (n=1,187) — gap 0.0762, **z = 2.65**
(unweighted 0.0693, z 2.53). False negatives were **0 in every cell**, but on 8 non-Latin
positives the rule-of-three upper bound is **0.375**: the instrument could not have said
otherwise. **Routing asymmetry confirmed; recall asymmetry not measured.** llm-distillery#141
is the blocker.

⚠️ `README_MODEL.md`'s YAML frontmatter declares `language: en`. That is the shared model-card
template's default, and it is not a measured claim about this filter.

## Training

- **Model**: `google/gemma-3-1b-pt` + LoRA (13,052,672 trainable / 1,012,945,536 total)
- **Oracle**: DeepSeek at k=3, **6,586 labels for $6.8853**; 456 above-op rows re-labelled under `prompt-v8-4.md`
- **Splits**: 5,268 train / 658 val / 660 test
- **Config**: 6 epochs, batch 8, lr 2e-5, max_length 512, no head/tail, no sample weighting
- **Checkpoint**: **epoch 4**, selected on `recall_medium` @4.5 — ⚠️ by a **tie-break**, not by the metric (it saturates at 0.5806 across epochs 4, 5 and 6; selection's strict `>` keeps the earliest). On test the arms are not distinguishable. llm-distillery#144
- **Calibration**: per-dimension isotonic on val (ADR-008)

⛔ **The calibration does not improve held-out MAE** (test 0.6029 → 0.6142, worse in 5 of 6
dimensions) and that is not why it ships. The two arms are the **same ranker** (Spearman
0.9977, AUC 0.9474 → 0.9488); calibration ships per ADR-008 and ADR-023's specificity
tie-break. `calibration_report.md`.

⛔ **Never rank this filter against another on MAE** (ADR-023).

## Package contents

| file | what |
|---|---|
| `config.yaml` | dimensions, weights, tiers, gatekeepers, `hybrid_inference` block |
| `prompt-compressed.md` | the oracle prompt — a **byte copy** of `prompt-v8-4.md`, see below |
| `prompt-v8-*.md`, `prompt-candidate*.md` | the lineage. ⛔ Do not tidy away: evidence runs stamp these paths |
| `PROMPTS.md` | which prompt is which, and why the rejected ones stay |
| `STATUS.md` | current state, everything known-failing and known-missing |
| `DEEP_ROOTS.md` | the lens rationale — what the question is and why it is that question |
| `README_MODEL.md` | Hub model-card source, generated by `upload_to_huggingface.py --card-only` |
| `NO_HUB` | why v8 is not on the Hub, and what would change that |
| `base_scorer.py`, `inference.py`, `inference_hybrid.py` | the scorer |
| `calibration.json`, `calibration_report.md` | isotonic fit and its narrative |
| `probe/` | e5-small probe + `.sha256` companion |
| `ground_truth_gate.json` | the ADR-021 gate result |
| `training_history.json`, `training_metadata.json` | per-epoch metrics and run config |

**Not here**: the LoRA weights (`model/`, gitignored as large checkpoints — ⚠️ **not #97**,
which is the TDM assessment and concluded the models are clean) and `normalization.json`
(Phase E, which cannot run until v8 is deployed and has produced ≥200 production rows above
the op-point).

### On `prompt-compressed.md`

`FilterBaseScorer._compute_prompt_hash` looks for that exact filename, so before it existed
`prompt_hash` was `None`. It is a **byte copy** of `prompt-v8-4.md` (both
`c4705408c477a511…`), never a rename: the 6,586 Phase B labels record
`prompt_file: filters/human_thriving/v8/prompt-candidate-tail.md` as provenance and renaming
would break that pointer.

⚠️ **The copy therefore reports v8.4's hash while 6,130 of the 6,586 training labels were
produced under `prompt-candidate-tail.md` (`003cd35a5122`).** `prompt_hash` names the current
oracle prompt, not the one that labelled the majority of the training data. It feeds
`get_metadata()`, which nothing in NexusMind reads — provenance only.

⚠️ Both files still carry v7's heading (*"Uplifting Content Analyst Prompt (v7 …)"*). It is
left as-is on purpose: editing the bytes would change `c4705408c477`, which the Phase-B2 gate
evidence stamps.

## What is not done

1. **Deployment.** v8 is absent from sadalsuud's `NexusMind/filters/`, and the weights exist
   in exactly one place — `b650-gpu:~/llm-distillery/filters/human_thriving/v8/model/`.
2. **Phase E normalization.** Blocked by ordering, not by preference: `fit_normalization.py`
   fits the CDF from NexusMind production output and refuses below 200 rows above the
   op-point. It comes **after** deployment, as it did for `solutions v6`. ⛔ Do not substitute
   the test split — it is a 25.1× design-weighted sample and a CDF fitted on it would describe
   a population that does not exist.
3. **The dangling checkpoint.** The shipped weights were trained by the tree that became
   `1878e7b` via `git commit --amend`, so the training commit (`0697f5a`) is unreachable and
   will not survive `git gc`. `1878e7b` reproduces the numbers, but *the verified artifact is
   not the shipped one* until it is retrained under a real commit. Retrain (~90 min on b650)
   or record the exception — owner's call, and it is recorded in `STATUS.md`.
4. **The v8.1 commencement fix**, ruled 2026-09-03 and unwritten. Acceptance criterion 1 stays
   FAILING until it is measured, with the Travelodge row as negative control.
