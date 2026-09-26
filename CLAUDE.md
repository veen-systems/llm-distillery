---
stack: Python 3.12, PyTorch, Transformers, PEFT/LoRA
status: Production
repo: github.com/ducroq/llm-distillery
framework: agent-ready-projects v1.49.0   # a NUMBER, not a status
framework_reconciliation: see docs/decisions/framework-adoption-history.md (operative rules + per-release triage)
---

# CLAUDE.md - LLM Distillery

## What Is This?

**LLM Distillery** trains small local classifiers (Gemma-3-1B + LoRA) to replicate cloud LLM scoring (Gemini Flash) at ~100x lower cost and ~50x faster inference.

**Workflow:** oracle scores articles on dimensions (0-10) → train student → deploy as a filter package. llm-distillery creates filters; NexusMind runs them. The interface is `filters/{name}/v{N}/` (copied between repos) plus HuggingFace Hub uploads.

**Downstream:** `veen-systems/persuasion-scorer` (#78/#79, persuasion techniques) **depends on** this repo's machinery and **must never vendor a copy**. #116 (activation/arousal) is scoped there; it stays open here as the ethics decision.

## Tech Stack

- **Oracle**: Gemini Flash 2.5, real-time — **no Batch API call site exists**, so Batch pricing is not an option. DeepSeek V4.1 Flash is 2.44× cheaper than that path after the 2026-09-10 cut (cd v5 default). We call the `deepseek-chat` alias, so V4.1 replaced V4 unmeasured (#157). ⛔ **Never quote a $/article figure without naming the prompt** — `memory/oracle-pricing-scheduling.md`, `scripts/analysis/oracle_cost.py`.
- **Student**: Gemma-3-1B (`google/gemma-3-1b-pt`) + PEFT/LoRA. **Calibration**: per-dimension isotonic (ADR-008). **Hybrid inference**: e5-small probe (Stage 1) + fine-tuned model (Stage 2, ADR-006). **Data**: 5K-10K oracle-scored articles per filter, 80/10/10.

## Hard Constraints

- **Oracle outputs scores only** (0-10 per dimension), never tiers. Tiering is postprocessing; a threshold change must never require re-labelling.
- **Use `load_base_model_for_seq_cls()`** (`filters/common/model_loading.py`), never `AutoModelForSequenceClassification` — `gemma3_text` is not in the Auto mapping.
- **Keep PEFT adapters in OLD key format** (`.lora_A.weight` / `score.weight`). Never run `resave_adapter.py` before Hub upload — it breaks `PeftModel.from_pretrained()`.
- **The 300-char length floor is labelling-time only** (#93): it lives in `ground_truth.batch_scorer.make_oracle_prefilter`. No `prefilter.apply_filter()` checks length; never add `check_content_length` to a prefilter. Scoring stamps `content_length` (populated since the `filtered_20260808_17*` cycle; for older rows use `len(content)` — a POST-enrichment length — plus `pre_enriched` / `original_content_length`). Empty is not short — `validate_article` still rejects it. → `memory/stamp-contract-integrity.md`
- **A matching prefilter pass rate is not evidence a gate is safe to enforce** — measure recall first (ADR-021). cd matches its declared 0.25 and enforcing still costs 15.5% of surfacing articles (135/871). → `docs/FILTER_PLAYBOOK.md` §0b, `memory/prefilter-length-floor-hypotheses.md`
- **A filter's `prefilter` config does NOT mean it runs in production** — the per-lens rule prefilter has never run there (NM#284); it runs only in the oracle/training path. Never read prefilter state from `data/filtered/*/filtered_*.jsonl` (100% passers by construction); use the pipeline's `N scored, M prefiltered` line or the shadow log.
- **There is a `|Δ| ≤ 0.16` score noise floor from batch composition (#95).** A run-to-run difference below ~0.1 near an op-point is noise; two models whose bands overlap are NOT distinguishable. Owner: budget for it, don't remove it. `scripts/gate/ground_truth_gate.py --noise-floor`. ⚠️ 0.16 is the batch-composition floor only; library stack and device are separate terms that can exceed it, and a sub-floor term still flips verdicts — read the FLIP COUNT at the op-point, not max |Δ|. Measure with `box_parity.py` + `diff_box_parity.py --threshold`. → `memory/score-batch-shape-noise.md`
- **Optimise SPECIFICITY; never rank filters on MAE (ADR-023).** A false positive costs a reader, a false negative costs nothing visible. Compare filters ONLY on recall + specificity (precision and MAE are base-rate dependent), each with the split's positive rate, and state the priority beside any recall figure. Active learning samples ABOVE the op-point; ties inside the #95 band go to specificity. **Not** for the Stage-1 e5 probe (recall-safe screen: `train_probe.py --objective recall`). → `memory/filter-status.md`
- **Fit `calibration.json` after every training run** (isotonic on val) and commit it with the package.
- **`.nexusmind-owns` must stay empty** unless an entry has a tracked issue and a deadline. `filters/common/filter_base_scorer.py` and `hybrid_scorer.py` are shared math; sync freely.
- **An op-point lives in FOUR places; `config.yaml` is not the runtime one.** `base_scorer.py` `TIER_THRESHOLDS` scores; `normalization.json` `stats.raw_min` must equal it; `tests/unit/test_normalization_op_point.py` pins it. Move all four in one commit, refit normalization, verify by executing tier assignment. `MAX_NORMALIZATION_RAW_MIN = 4.5` (above it the loader silently falls back). NexusMind's `pipeline.enrichment.min_score` (4.0, reads the NORMALIZED score) is a separate constant — lowering an op-point or shipping a low-scoring filter can starve enrichment (NM#319). → `docs/NORMALIZATION_METHOD.md`

### Working rules — non-negotiable

Full text, evidence and occurrence counts: `memory/working-rules.md`. Read it before weakening any rule.

- **Before shipping any gate, cap, threshold, config key or stamp — or comparing against an option, price or quota — name the caller that would load it, then PROVE THE OUTCOME CHANGED at the end of the run.** Naming the caller is not sufficient; a green test on the predicate proves only the predicate. → `memory/working-rules.md`, `memory/gotcha-log.md` § *The unreachable-mechanism catalogue*
- **A failing check may be the CONTROL WORKING** — ask what its failure is buying you before repairing it. → `memory/working-rules.md`
- **`raw_weighted_average` is NOT always a model output — condition on `stage_used` first.** A `stage1_low` row carries an e5 probe estimate.
- **Before using any source as evidence, establish what it EXCLUDES** — data, structures, prior work, hosts, and time (a window is part of a source). Before believing a negative, prove the instrument could have said yes — and ask what would have made the "before" different. → `memory/working-rules.md`
- **Prefer a population the pipeline already computes to a hand-built one.** Make the missing case raise, never return `None`.
- **A parallel session may share this checkout:** never `git add -A`, bare `git stash`, `git checkout .`, `git clean`. Pass explicit paths; `git status --porcelain` before committing and stage only what you recognise.
- **`pgrep -f` and `systemctl is-active <one-unit>` cannot answer "is it running?"** Enumerate units (`systemctl list-units 'nexusmind*' --all`, including `OnSuccess=` chains); `pgrep`/`pkill -f` also match the shell carrying the pattern: use `ps -eo pid,etime,args | grep -v grep` and print the matching line before acting. → `memory/working-rules.md`

## Production Filters

Details: `memory/filter-status.md`.

| Filter | Version | Recall / Spec ⛔ read spec first | Status |
|--------|---------|-----|--------|
| **uplifting** | v7 | recall 0.61 / spec 0.97 | Deployed (NO_HUB, hybrid). Op-point 4.5 (#102). Its Thriving lens is narrower than the name (#107) |
| **investment-risk** | v6 | recall 0.72 / spec 0.97 | ⛔ **RETIRED downstream 2026-09-17** (NexusMind ADR-025, NM#499). Package here stays. Un-pausing is a project |
| **human_thriving** | v9 | spec 0.998 / recall 0.348 (adjudicated labels) | **LIVE 2026-09-25**, replacing v8 (NM#530). Thriving still reads `uplifting v7`; cutover #151 undecided |
| **cultural-discovery** | v5 | recall 0.59 / spec 0.98 | **LIVE** (v6 cutover failed 2026-08-13, reverted) |
| **cultural-discovery** | v6 | (v5's) | **NOT DEPLOYED** — fixed and verified offline (`dcf2860`), never redeployed. v5 already runs two-stage; v6 changes the probe and threshold. → `memory/cd-v6-probe-hypotheses.md` |
| **belonging** | v1 | recall 0.60 / spec 0.985 | Deployed (HF Hub) |
| **nature_recovery** | v4 | recall 0.65 / prec 0.85 | Deployed (recall-first probe, v5 planned #71) |
| **solutions** | v6 | recall 0.67 / spec 0.97 | **LIVE** |
| **sustainability_technology** v3, **foresight** v1 | — | — | Removed 2026-08-03, merged into solutions (#43) |
| **thriving** | v1 | — | PARKED indefinitely (ADR-015) |
| **ai-engineering-practice** | v1 | — | Separate product, not ovr.news |

## Key Decisions

Index: `docs/adr/README.md`; records: `docs/decisions/`.

- Dimensional regression, not classification (ADR-001); screen+merge for needle filters (ADR-003); commerce is the only universal prefilter (ADR-004); active learning for rare tiers (ADR-005)
- Oracle consistency over data volume; belonging v1 is the prompt template (ADR-010). Embedding screening with e5-small seeds replaces keyword screening (ADR-011)
- Lens-aligned naming is CLOSED: only `uplifting` → `human_thriving` (ADR-012 as amended)
- **English everywhere the framework speaks** — names, docs, comments, memory, commits (ADR-013). NOT match patterns, strippers or fixtures: those are data, and deleting an exclusion costs specificity
- Percentile normalization from the production CDF supersedes `score_scale_factor` (ADR-014). Lenses are perspectives, overlap is correct — never exclude adjacent lens content in oracle prompts (ADR-015). No tiers — pass/block + score (ADR-016)
- Declarative prefilter shape on `BasePreFilter` (ADR-018/019); **new filters ship NO per-lens prefilter** (amended 2026-08-21)
- Ground-truth deploy gate against held-out oracle labels, never the prior model (ADR-021). Stamp always, decide once — one config-gated drop point per concern, every enforcement decision a config flip; visibility = raw ≥ op-point, the normalized score is rank/badge only (ADR-022). Precision over recall (ADR-023)

## How To Write Answers Here

For chat replies:
1. Answer first, in one line (yes / no / not yet); then only detail that changes what the owner does.
2. Never coin a label and reuse it as shared vocabulary.
3. Expand an issue number the first time: "#86 (the cultural-discovery gate)". Qualify cross-repo numbers every time.
4. Separate measured from guessed, every time.
5. Keep the caveats, cut the recap.
6. Say what you did to the owner's machine and how to undo it.

## Before You Start

**Read `memory/MEMORY.md` first.** Pointer rows are capped at 250 chars (carve-outs at 400): a new lesson goes in the target file, not here (`check_index_budget.py --target pointers`).

| When you're... | Read... |
|----------------|---------|
| **Starting a session, or told only "continue"** | `memory/MEMORY.md`, then **`docs/TODO.md` ▶ START HERE** — a bare "continue" means that list, top down |
| Resuming thriving v1 work | `memory/thriving-v1-scoring.md` |
| Starting calibration / scorer-training / oracle-prompt work | `memory/calibration-history.md` — Dead Ends (#69) |
| Touching a prefilter, or considering an enforcement flip | `memory/prefilter-length-floor-hypotheses.md`, then #93 |
| A legal/compliance question, or the training-data source | `docs/decisions/2026-08-05-tdm-opt-out-training-data.md` — one carve-out open (oracle ships text to the vendor) |
| **Anything about the pipeline CONTRACTS** | `docs/decisions/2026-08-14-contract-a-envelope.md`, `docs/CONTRACTS_PLAN.md` § *Round 3*, `memory/stamp-contract-integrity.md`. ⛔ **Never quote a Contract A version from here** — read a delivered row (`scripts/contracts/contract_a_smoke.py`) |
| **Asking what an article field IS, or where a blocked article went** | `NexusMind/contracts/article-record.schema.json`, `NexusMind/docs/ARTICLE_RECORD_REGISTER.md`; blocked: `docs/BLOCK_LEDGER_SPEC.md`. ⛔ **Never quote a field count** — every count is a window |
| Adding a stamp / config key, or trusting a stamped field | `memory/stamp-contract-integrity.md` — run `NexusMind/scripts/stamp_census.py` before quoting a stamped field |
| **Reading a number off NexusMind production data** | `memory/nexusmind-data-sources.md`. ⛔ **`live_articles` is NOT the reader population** — use `getArticlesForBuild`; `weighted_average` there is NORMALIZED |
| **Quoting any Google News number, or touching the GN population** | `memory/google-news-corpus-hypotheses.md`. ⛔ **Never oracle-re-score a GN row**, never match GN on a `gn_` prefix, always name the fetcher (NM#310) |
| Touching normalization | `docs/NORMALIZATION_METHOD.md` — `raw >= threshold` with `tier: low` is expected |
| Reading a date or recency boost (`published_date`) | `memory/date-error-recency-boost-hypotheses.md` |
| Measuring near an op-point, or comparing two runs | `memory/score-batch-shape-noise.md` |
| Touching enrichment, or citing a pre/post-enrichment delta | `memory/enrichment-delta-hypotheses.md` |
| Changing a dimension weight, or calling one "dead" | `memory/solutions-v6-dimension-hypotheses.md` — a zero rate is base rate, not breakage |
| Quoting any #121 number (opinion/editorial genre) | `memory/opinion-genre-hypotheses.md` — #121's body uses a wrong `solutions` op-point |
| Touching cultural_discovery v6 | `memory/cd-v6-probe-hypotheses.md` |
| Obituary/grief, or the junk-gate state | `memory/project-obituary-detector.md` — enforcement ON at v5@0.85 |
| **Creating OR retraining ANY filter** | **`docs/FILTER_PLAYBOOK.md`** — read before touching filter code |
| Deploying to NexusMind or gpu-server | `docs/RUNBOOK.md` |
| Training on GPU server | `memory/gpu-server.md` |
| Debugging model loading or PEFT | `memory/gemma3-model.md` |
| Making architectural decisions | `docs/adr/README.md` |
| Planning work | `docs/TODO.md`, `docs/ROADMAP.md`; across repos: `memory/cross-repo-prioritization.md` |
| Understanding system design / reviewing quality | `docs/ARCHITECTURE.md`, `docs/checklists/` |
| Stuck on tooling or infra | `memory/gotcha-log.md` (+ `memory/archive/gotcha-log-archive.md`; grep both) |
| **Running `/review-changes`** | `.claude/review-profile.md` — REQUIRED; the skill stops without it. Confirm its 3 project lenses by NAME in the report |
| About to weaken or argue with a working rule | `memory/working-rules.md` |
| Touching corroboration or story-dedup | `memory/corroboration-feature-hypotheses.md` — the threshold is not the lever |
| Running anything long, or told "the GPU is free" | `memory/b650-gpu.md` — RTX 5090 since 2026-09-17; older CUDA numbers predate it |
| Checking which lens/tab a filter feeds | `memory/ovr-lens-set-current.md` |
| Writing docs for a deployed filter | `memory/filter-doc-standard.md` |
| Building on a DeepSeek oracle, or citing cd v5 | `memory/cd-v5-reference-status.md` |
| Retraining uplifting, Thriving FPs (#125), or the junk gates | `memory/uplifting-v7-training.md`, `memory/uplifting-oracle-genre-hypotheses.md`, `memory/obituary-v4-hypotheses.md`, `memory/violence-promotion-v1-hypotheses.md` |
| Wanting the whole chain, or live pipeline state | `veen-systems/pipeline-atlas` (Tailscale `http://100.78.93.76:8099/`) |
| **Concluding an experiment, or "did we ever test X?"** | `experiments/registry.jsonl` (`README.md` is its schema) |
| Memory past its month | `python3 scripts/maintenance/retire_memory.py {gotcha,sessions} --before <YYYY-MM-01> --apply` (dry run without `--apply`) |
| Ending a session / monthly | `/curate` / `/audit-context` |

## Getting Started

```bash
pip install -r requirements.txt
git config core.hooksPath .githooks          # once per clone: blocks unverified "deploy" claims (#44)
# HF token: config/credentials/secrets.ini

# Oracle scoring. ⛔ NAME --llm (default is `claude`); DeepSeek is scripts/score_deepseek_production.py
python -m ground_truth.batch_scorer --filter filters/{name}/v{N} --llm gemini-flash \
    --source datasets/raw/master_dataset.jsonl

# Training splits. ⛔ No --data-source flag; the wrong --filter writes 0 examples and exits 0
python training/prepare_data.py --filter filters/{name}/v{N} \
    --input datasets/scored/{name}_v{N}.jsonl --output-dir datasets/training/{name}_v{N}

# Calibration. ⛔ --no-config-update unless normalization.json exists (else it edits score_scale_factor)
PYTHONPATH=. python scripts/calibration/fit_calibration.py \
    --filter filters/{name}/v{N} --data-dir datasets/training/{name}_v{N} \
    --test-data datasets/training/{name}_v{N}/test.jsonl --no-config-update

# Normalization (after production data accumulates)
MSYS_NO_PATHCONV=1 PYTHONPATH=. python scripts/normalization/fit_normalization.py \
    --filter filters/{name}/v{N} --ssh sadalsuud \
    --remote-dir /home/jeroen/local_dev/NexusMind/data/filtered/{name}

# Hub upload
python scripts/deployment/upload_to_huggingface.py \
    --filter filters/{name}/v{N} --repo-name jeergrvgreg/{name}-filter-v{N} \
    --token $HF_TOKEN --private
```

Full commands: `docs/RUNBOOK.md`. Evidence for the four patterns of [augmented-engineering](https://github.com/ducroq/augmented-engineering) goes there as an issue (pattern, quantified result, claims supported).

---

*Framework: agent-ready-projects v1.49.0 — verify with `bash scripts/verification/check_framework_stamp.sh` (0 verified · 1 drift · 2 undecided). Bump the stamp only after its adopt items land. `curate`, `audit-context`, `review-changes` and `update-drift` are USER-GLOBAL — never re-create project-local copies (a global silently shadows them); `test-verify-memory` stays local. Triage and standing rules: `docs/decisions/framework-adoption-history.md`. A measured figure here is a copy — quote it from the file its bullet points to, which is kept current.*
