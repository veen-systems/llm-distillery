---
stack: Python 3.12, PyTorch, Transformers, PEFT/LoRA
status: Production
repo: github.com/ducroq/llm-distillery
framework: agent-ready-projects v1.49.2   # a NUMBER, not a status
framework_reconciliation: see docs/decisions/framework-adoption-history.md (operative rules + per-release triage)
---

# CLAUDE.md - LLM Distillery

Trains small local classifiers (Gemma-3-1B + LoRA) to replicate cloud-LLM oracle scoring. Oracle scores articles on dimensions (0-10) → train student → ship `filters/{name}/v{N}/` (copied to NexusMind, which runs them) plus HuggingFace Hub uploads. `veen-systems/persuasion-scorer` **depends on** this repo's machinery and **must never vendor a copy**.

**Lite profile since 2026-10-22** (`docs/decisions/2026-10-22-framework-lite.md`; pre-switch copy: `memory/archive/CLAUDE-pre-lite-2026-10-22.md`). A lesson is promoted only as a CHECK (test, hook, script), never as more prose here. No session log: the commit message is the record.

## Tech Stack

- **Oracle**: Gemini Flash 2.5 real-time (no Batch call site exists); DeepSeek (`deepseek-chat` alias, #157) is cheaper. ⛔ **Never quote a $/article figure without naming the prompt** — `memory/oracle-pricing-scheduling.md`, `scripts/analysis/oracle_cost.py`.
- **Student**: `google/gemma-3-1b-pt` + PEFT/LoRA. Per-dimension isotonic calibration (ADR-008). Hybrid inference: e5-small probe → fine-tuned model (ADR-006). 5K-10K oracle-scored articles per filter, 80/10/10.

## Hard Constraints

- **Oracle outputs scores only** (0-10 per dimension), never tiers. A threshold change must never require re-labelling.
- **Use `load_base_model_for_seq_cls()`** (`filters/common/model_loading.py`), never `AutoModelForSequenceClassification`.
- **Keep PEFT adapters in OLD key format** (`.lora_A.weight` / `score.weight`). Never run `resave_adapter.py` before Hub upload.
- **The 300-char length floor is labelling-time only** (#93): it lives in `ground_truth.batch_scorer.make_oracle_prefilter`; never add `check_content_length` to a prefilter. Empty is not short. → `memory/stamp-contract-integrity.md`
- **A matching prefilter pass rate is not evidence a gate is safe to enforce** — measure recall first (ADR-021). → `docs/FILTER_PLAYBOOK.md` §0b, `memory/prefilter-length-floor-hypotheses.md`
- **There are NO per-lens prefilters** (deleted 2026-10-01, decision 0); `tests/unit/test_no_per_lens_prefilters.py` enforces it. The oracle path's whole gate is `make_oracle_prefilter`.
- **There is a `|Δ| ≤ 0.16` batch-composition noise floor (#95).** Overlapping bands are NOT distinguishable. It is the batch term only (library stack and device are separate); read the FLIP COUNT at the op-point, not max |Δ|. `box_parity.py` + `diff_box_parity.py --threshold`. → `memory/score-batch-shape-noise.md`
- **Optimise SPECIFICITY; never rank filters on MAE (ADR-023).** Compare on recall + specificity only, each with the split's positive rate. Not for the Stage-1 e5 probe (`train_probe.py --objective recall`). → `memory/filter-status.md`
- **Fit `calibration.json` after every training run** (isotonic on val) and commit it with the package.
- **`.nexusmind-owns` must stay empty** unless an entry has a tracked issue and a deadline. ⚠️ The decision-0 sync is one NM commit with the packages and NM's tests (`docs/TODO.md` item 1).
- **An op-point lives in FOUR places; `config.yaml` is not the runtime one**: `base_scorer.py` `TIER_THRESHOLDS`, `normalization.json` `stats.raw_min`, `tests/unit/test_normalization_op_point.py`. Move all in one commit and verify by executing tier assignment. `MAX_NORMALIZATION_RAW_MIN = 4.5`. NexusMind's `min_score` 4.0 is separate (NM#319). → `docs/NORMALIZATION_METHOD.md`

### Working rules — non-negotiable

Evidence and counts: `memory/working-rules.md`. Read it before weakening any rule.

- **Before shipping any gate, cap, threshold, config key or stamp — or comparing against an option, price or quota — name the caller that would load it, then PROVE THE OUTCOME CHANGED.** A green predicate test proves only the predicate. → `memory/working-rules.md`
- **A failing check may be the CONTROL WORKING** — ask what its failure is buying you before repairing it.
- **`raw_weighted_average` is NOT always a model output — condition on `stage_used` first.**
- **Before using any source as evidence, establish what it EXCLUDES** (data, hosts, time window); before believing a negative, prove the instrument could have said yes. → `memory/working-rules.md`
- **Prefer a population the pipeline already computes to a hand-built one.** Make the missing case raise, never return `None`.
- **situla is the single source of truth; GPU hosts are scratch.** Pull runs with `scripts/lab/lab.py pull` into `~/lab/llm-distillery`; host deletes need the owner's go, except FINISHED b650 runs held by a restic snapshot. → `docs/decisions/2026-10-10-situla-single-source-of-truth.md`
- **A parallel session may share this checkout:** never `git add -A`, bare `git stash`, `git checkout .`, `git clean`. Stage explicit paths only.
- **`pgrep -f` and `systemctl is-active <one-unit>` cannot answer "is it running?"** Enumerate units; use `ps -eo pid,etime,args | grep -v grep`.

## Production Filters

Details: `memory/filter-status.md`. ⛔ Read spec before recall.

| Filter | Version | Recall / Spec | Status |
|--------|---------|-----|--------|
| **uplifting** | v7 | recall 0.61 / spec 0.97 | Deployed (NO_HUB, hybrid), op-point 4.5; draining from Thriving |
| **investment-risk** | v6 | recall 0.72 / spec 0.97 | ⛔ RETIRED downstream 2026-09-17 (NM ADR-025) |
| **human_thriving** | v9 | spec 0.998 / recall 0.348 | **LIVE** 2026-09-25; Thriving reads it |
| **cultural-discovery** | v5 | recall 0.59 / spec 0.98 | **LIVE** |
| **cultural-discovery** | v6 | (v5's) | **NOT DEPLOYED** — verified offline (`dcf2860`) → `memory/cd-v6-probe-hypotheses.md` |
| **belonging** | v3 | recall 0.92 / weighted spec 0.930 | **LIVE** 2026-10-09; rollback rule: `filters/belonging/v3/STATUS.md` |
| **nature_recovery** | v4 | recall 0.65 / prec 0.85 | Deployed (v5 planned #71) |
| **solutions** | v6 | recall 0.67 / spec 0.97 | **LIVE** |
| **thriving** | v1 | — | PARKED indefinitely (ADR-015) |
| **ai-engineering-practice** | v1 | — | Separate product |

## Key Decisions

Index `docs/adr/README.md`; records `docs/decisions/`. Dimensional regression (ADR-001); commerce is the only universal prefilter (ADR-004); oracle consistency over volume (ADR-010); e5 screening (ADR-011); only `uplifting` → `human_thriving` renamed (ADR-012); **English everywhere the framework speaks, not in match patterns or fixtures** (ADR-013); percentile normalization (ADR-014); lenses overlap by design (ADR-015); pass/block + score, no tiers (ADR-016); ground-truth deploy gate, never the prior model (ADR-021); stamp always, decide once (ADR-022); precision over recall (ADR-023).

## How To Write Answers Here

1. Answer first in one line; then only detail that changes what the owner does.
2. Never coin a label and reuse it as shared vocabulary. Expand an issue number the first time; qualify cross-repo numbers every time.
3. Separate measured from guessed. Keep the caveats, cut the recap.
4. Say what you did to the owner's machine and how to undo it.

## Before You Start

Read `memory/MEMORY.md` (the index), then **`docs/TODO.md` ▶ START HERE** — a bare "continue" means that list.

| When you're... | Read... |
|----------------|------|
| Creating or retraining ANY filter | **`docs/FILTER_PLAYBOOK.md`** |
| Deploying / GPU training | `docs/RUNBOOK.md`; `memory/gpu-server.md`; `memory/b650-gpu.md` (RTX 5090 since 2026-09-17) |
| Model loading or PEFT | `memory/gemma3-model.md` |
| Calibration, scorer training, oracle prompts | `memory/calibration-history.md` (Dead Ends, #69) |
| A prefilter or enforcement flip | `memory/prefilter-length-floor-hypotheses.md` |
| Anything about the pipeline CONTRACTS, or a stamped field | `docs/decisions/2026-08-14-contract-a-envelope.md`, `memory/stamp-contract-integrity.md` — never quote a Contract A version from here (`scripts/contracts/contract_a_smoke.py`) |
| Asking what an article field IS, or where a blocked article went | `NexusMind/contracts/article-record.schema.json`, `docs/BLOCK_LEDGER_SPEC.md` — never quote a field count |
| Reading a number off NexusMind production data | `memory/nexusmind-data-sources.md` — `live_articles` is NOT the reader population |
| Quoting any Google News number | `memory/google-news-corpus-hypotheses.md` — never oracle-re-score a GN row |
| Normalization | `docs/NORMALIZATION_METHOD.md` |
| Dates / recency boost | `memory/date-error-recency-boost-hypotheses.md` |
| Comparing runs near an op-point | `memory/score-batch-shape-noise.md` |
| Enrichment deltas | `memory/enrichment-delta-hypotheses.md` |
| Dimension weights | `memory/solutions-v6-dimension-hypotheses.md` |
| #121 (opinion genre) | `memory/opinion-genre-hypotheses.md` |
| cultural_discovery v5 / v6 | `memory/cd-v5-reference-status.md`, `memory/cd-v6-probe-hypotheses.md` |
| Junk gates (obituary, violence) | `memory/project-obituary-detector.md`, `memory/obituary-v4-hypotheses.md`, `memory/violence-promotion-v1-hypotheses.md` |
| Uplifting / Thriving | `memory/uplifting-v7-training.md`, `memory/uplifting-oracle-genre-hypotheses.md`, `memory/thriving-v1-scoring.md` |
| Corroboration / story-dedup | `memory/corroboration-feature-hypotheses.md` |
| Lens → tab mapping; filter docs | `memory/ovr-lens-set-current.md`; `memory/filter-doc-standard.md` |
| Oracle cost | `memory/oracle-pricing-scheduling.md` |
| Planning; cross-repo | `docs/TODO.md`, `docs/ROADMAP.md`; `memory/cross-repo-prioritization.md` |
| Architecture / ADRs | `docs/ARCHITECTURE.md`, `docs/adr/README.md` |
| "Did we ever test X?" | `experiments/registry.jsonl`, `memory/hypothesis-ledger.md` |
| Stuck on tooling | `memory/gotcha-log.md` (+ `memory/archive/gotcha-log-archive.md`) |
| Legal / training-data source | `docs/decisions/2026-08-05-tdm-opt-out-training-data.md` |
| Weakening a working rule | `memory/working-rules.md` |
| Running `/review-changes` | `.claude/review-profile.md` (REQUIRED) |
| Live pipeline state | `veen-systems/pipeline-atlas` (`http://100.78.93.76:8099/`) |

## Getting Started

```bash
pip install -r requirements.txt
git config core.hooksPath .githooks          # once per clone (#44)
# HF token: config/credentials/secrets.ini; tests run under .venv/bin/python

# Oracle scoring. ⛔ NAME --llm (default is `claude`); DeepSeek is scripts/score_deepseek_production.py
# ⛔ Prompts with config/canary/*.baseline.json are GUARDED (#177): `python scripts/oracle/canary.py run --filter {name}` first
python -m ground_truth.batch_scorer --filter filters/{name}/v{N} --llm gemini-flash \
    --source datasets/raw/master_dataset.jsonl

# Training splits. ⛔ No --data-source flag; the wrong --filter matches 0 rows and exits 1
python training/prepare_data.py --filter filters/{name}/v{N} \
    --input datasets/scored/{name}_v{N}.jsonl --output-dir datasets/training/{name}_v{N}

# Calibration. ⛔ --no-config-update unless normalization.json exists
PYTHONPATH=. python scripts/calibration/fit_calibration.py \
    --filter filters/{name}/v{N} --data-dir datasets/training/{name}_v{N} \
    --test-data datasets/training/{name}_v{N}/test.jsonl --no-config-update
```

Normalization, Hub upload and the rest: `docs/RUNBOOK.md`. Evidence for the four patterns of [augmented-engineering](https://github.com/ducroq/augmented-engineering) goes there as an issue.

---

*Framework: agent-ready-projects v1.49.2 — FROZEN (lite profile, `docs/decisions/2026-10-22-framework-lite.md`); `update-drift` will still list the gap. Verify: `bash scripts/verification/check_framework_stamp.sh`. `curate`, `audit-context`, `review-changes`, `update-drift` are USER-GLOBAL — never re-create local copies. A figure here is a copy — quote it from the file its row points to.*
