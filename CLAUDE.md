---
stack: Python 3.12, PyTorch, Transformers, PEFT/LoRA
status: Production
repo: github.com/ducroq/llm-distillery
framework: agent-ready-projects v1.10.6
---

# CLAUDE.md - LLM Distillery

## What Is This?

**LLM Distillery** is a knowledge distillation framework. It trains small, cheap, local classifiers (Gemma-3-1B + LoRA) to replicate expensive cloud LLM scoring (Gemini Flash) at 100x lower cost and 50x faster inference.

**Core workflow:** Oracle (Gemini Flash) scores articles on dimensions (0-10) → Train student model (Gemma-3-1B) → Deploy as filter package

**System context:** llm-distillery creates filters. NexusMind deploys them for production scoring. The interface is the filter package: `filters/{name}/v{N}/` directories copied between repos, plus HuggingFace Hub uploads.

## Tech Stack

- **Oracle**: Gemini Flash 2.5; DeepSeek V4 Flash proven cheaper alternative (cd v5). Per-article pricing + scheduling levers: `memory/oracle-pricing-scheduling.md`.
- **Student**: Gemma-3-1B (`google/gemma-3-1b-pt`) with PEFT/LoRA adapters
- **Calibration**: Per-dimension isotonic regression (ADR-008)
- **Hybrid inference**: e5-small embedding probe (Stage 1) + fine-tuned model (Stage 2, ADR-006)
- **Training data**: 5K-10K oracle-scored articles per filter, 80/10/10 splits

## Hard Constraints

- **Oracle outputs scores only.** Dimensional scores (0-10), never tier/stage classifications. Tier assignment is postprocessing. Changing thresholds must never require re-labeling.
- **Use `load_base_model_for_seq_cls()`** from `filters/common/model_loading.py`. Never use `AutoModelForSequenceClassification` directly — Gemma-3-1B's `gemma3_text` config isn't in the Auto mapping.
- **Keep PEFT adapters in OLD key format.** `.lora_A.weight` / `score.weight`, not `.lora_A.default.weight`. Never run `resave_adapter.py` before Hub upload — it breaks `PeftModel.from_pretrained()`.
- **A filter's `prefilter` config does NOT mean the prefilter runs in production.** The per-lens *rule* prefilter (`filters/{name}/v{N}/prefilter.py`, ADR-018/019) has never executed in the production scoring path — the GPU scorer builds every scorer with `use_prefilter=False` and calls `score_batch(skip_prefilter=True)` (NM#284, found 2026-08-01; dead since 2026-02-10). It *does* run in the llm-distillery oracle/training path, which is why this survived six months. Unaffected: the e5 probe, the commerce prefilter (ADR-004), the obituary/violence gates, the NM#189 source-type allowlist. NM#284 stage 1 logs observed vs declared pass rate; enforcement is not yet on. **Never check prefilter state from `data/filtered/*/filtered_*.jsonl`** — it only receives `passed_prefilter: true` rows NexusMind’s pipeline writes it only under an `if result["passed_prefilter"]:` guard, so it is 100% passers by construction; use the pipeline's `N scored, M prefiltered` line or the shadow log. **Don't infer runtime behavior from config keys** — see `memory/calibration-history.md` Dead Ends.

- **Fit `calibration.json` after every training run.** Isotonic regression on the val set. Commit with the filter package. The base scorer auto-loads it.
- **`.nexusmind-owns` is empty by default.** The manifest mechanism stays in place as a controlled-divergence escape hatch — entries get added only with a tracked issue and a resolution deadline. Long-term silent divergence between repos is the failure shape that the 2026-05-04 "manifest as anti-pattern" gotcha-log entry warns against (concrete: normalization plumbing was deleted from NexusMind on 2026-04-16 and went unnoticed for 18 days because the manifest masked it). Production-runtime concerns now live in `NexusMind/src/scoring/production_scorer.py`, which composes the shared base scorer rather than mutating it. `filters/common/filter_base_scorer.py` and `filters/common/hybrid_scorer.py` are pure shared math; sync freely.

## Production Filters

Full details in `memory/filter-status.md`. Summary:

| Filter | Version | MAE | Status |
|--------|---------|-----|--------|
| **uplifting** | v7 | — | Deployed (NO_HUB, hybrid inference) |
| **sustainability_technology** | v3 | 0.72 | Retired — replaced by solutions |
| **investment-risk** | v6 | 0.47 | Deployed (HF Hub) |
| **cultural-discovery** | v5 | 0.70 | Deployed (HF Hub, DeepSeek oracle) |
| **belonging** | v1 | 0.49 | Deployed (HF Hub) |
| **nature_recovery** | v4 | recall 0.65 / prec 0.85 | Deployed (recall-first probe, v5 planned #71) |
| **solutions** | v6 | 0.48 | **LIVE** — gate passed 2026-07-27, normalization fitted 2026-07-28 |
| **foresight** | v1 | 0.75 | PARKED — merged into solutions (#43) |
| **thriving** | v1 | — | PARKED indefinitely (ADR-015) |
| **ai-engineering-practice** | v2 | — | Separate product, not ovr.news |

## Key Decisions

- **Dimensional regression (0-10)** — not classifications (ADR-001)
- **Screen+merge for needle-in-haystack filters** (ADR-003)
- **Commerce is the only universal prefilter** (ADR-004)
- **Active learning for rare tiers** (ADR-005)
- **Fine-tuning beats embedding probes** — research confirmed
- **Gemma-3-1B** — replaced Qwen2.5; better MAE, faster inference
- **Add filters first, reduce later** — deploy as separate tabs, dedup later (ADR-009)
- **Lens-aligned filter naming** — rename filters to match ovr.news lens names at version bumps (ADR-012)
- **Oracle consistency over data volume** — prompt precision predicts MAE better than dataset size; use belonging v1 as template (ADR-010)
- **Embedding screening for needle filters** — use Phase 3 positives as e5-small seeds to screen corpora; replaces keyword screening (ADR-011)
- **English lens names** — all lens/tab names in English, no Dutch (ADR-013)
- **Cross-filter percentile normalization** — non-linear mapping from production CDF; supersedes score_scale_factor (ADR-014)
- **Lenses as perspectives, not partitions** — overlap between lenses is correct; never exclude adjacent lens content in oracle prompts (ADR-015)
- **Drop tier assignments** — filters output pass/block + continuous score only; tiers add no value over the score itself (ADR-016)
- **Declarative prefilter shape** — extend `BasePreFilter` with `EXCLUSION_PATTERNS` / `OVERRIDE_KEYWORDS` / `POSITIVE_PATTERNS` / `POSITIVE_THRESHOLD` class attrs; standard `apply_filter()` pipeline lives on the base (ADR-018, #52)
- **Per-category exclusion overrides** — `CATEGORY_OVERRIDES` dict (TypedDict-typed) + `_compound_override_applies()` Template Method hook on `BasePreFilter`. Subclasses inject only special-case rules; base owns the fallback chain (compound hook → dict → global `_has_override`). Unblocks belonging/foresight/sustech/cultural-discovery from custom `apply_filter()` (ADR-019, #52)
- **Ground-truth deploy gate** — judge each model against held-out ORACLE ground truth, never against the prior deployed model (ADR-021)
- **Stamp always, decide once** — gate modules stamp score+flag+model version always; exactly one config-gated drop point per concern; every enforcement decision is a config flip. Tier semantics follow the same principle: visibility = raw ≥ op-point, normalized score is rank/badge only (ADR-022, NM#280)

See `docs/adr/README.md` for full ADR index, `docs/decisions/` for detailed records.

## Before You Start

**Always read `memory/MEMORY.md` first** — it's the project memory index with current work status, gotchas, and pointers to topic files.

| When you're... | Read... |
|----------------|---------|
| Starting a new session | `memory/MEMORY.md` — project memory index, current work status |
| Resuming thriving v1 work | `memory/thriving-v1-scoring.md` — scoring status, resume commands, full pipeline |
| Starting calibration / scorer-training / oracle-prompt work | `memory/calibration-history.md` — Dead Ends section: which approaches are already known dead (#69) |
| **Touching normalization (fitting, debugging a score/tier that looks wrong, ovr ranking)** | **`docs/NORMALIZATION_METHOD.md`** — canonical method (anchored CDF, guards, reproduction steps); ADR-014 for the decision record, `docs/FILTER_PLAYBOOK.md` §6 for the digest. Normalization exists only for ovr.news cross-lens ranking; tier is reassigned on the *normalized* score by design, so `raw >= threshold` + `tier: low` is expected. Fit at `raw >= the filter's tier threshold` — enforced by `tests/unit/test_normalization_invariant.py`. Both #161 and #205 were `raw_min` drifting off that threshold. |
| **Creating OR retraining ANY filter (START HERE)** | **`docs/FILTER_PLAYBOOK.md`** — the single source of truth: every compiled lesson + the canonical reference (`nature_recovery v4`). Read before touching filter code. Then `docs/agents/filter-development-guide.md` (depth) / `docs/guides/filter-creation-workflow.md` (quick steps). |
| Deploying to NexusMind or gpu-server | `docs/RUNBOOK.md` — deployment, training, scoring how-to |
| Training on GPU server | `memory/gpu-server.md` — venv, PYTHONPATH, HF_HUB_OFFLINE |
| Debugging model loading or PEFT issues | `memory/gemma3-model.md` — Auto mapping fix, key format details |
| Making architectural decisions | `docs/adr/README.md` — 19 settled ADRs |
| Checking priorities or planning work | `docs/TODO.md` and `docs/ROADMAP.md` |
| Understanding system design | `docs/ARCHITECTURE.md` |
| Reviewing work quality | `docs/checklists/` — architect, test, implement, QA gates |
| Stuck on tooling or infra | `memory/gotcha-log.md` — problem/fix archive |
| Ending a session | Run `/curate` |
| Monthly or after major restructuring | Run `/audit-context` |

## Getting Started

```bash
pip install -r requirements.txt

# One-time per clone: enable the commit-msg hook that blocks unverified "deploy"
# claims (see .githooks/commit-msg, llm-distillery#44 for background).
git config core.hooksPath .githooks

# Configure: add HF token to config/credentials/secrets.ini
# Oracle scoring
python -m ground_truth.batch_scorer --filter filters/{name}/v{N} --source datasets/raw/master_dataset.jsonl

# Prepare training splits
python training/prepare_data.py --filter filters/{name}/v{N} --data-source datasets/scored/{name}_v{N}.jsonl

# Fit calibration (after training)
PYTHONPATH=. python scripts/calibration/fit_calibration.py \
    --filter filters/{name}/v{N} --data-dir datasets/training/{name}_v{N} \
    --test-data datasets/training/{name}_v{N}/test.jsonl

# Fit normalization (after production data accumulates)
MSYS_NO_PATHCONV=1 PYTHONPATH=. python scripts/normalization/fit_normalization.py \
    --filter filters/{name}/v{N} --ssh sadalsuud \
    --remote-dir /home/jeroen/local_dev/NexusMind/data/filtered/{name}

# Upload to Hub
python scripts/deployment/upload_to_huggingface.py \
    --filter filters/{name}/v{N} --repo-name jeergrvgreg/{name}-filter-v{N} \
    --token $HF_TOKEN --private
```

See `docs/RUNBOOK.md` for full operational commands.

## Cross-Repo Evidence

This project is a source project for [augmented-engineering](https://github.com/ducroq/augmented-engineering) — a proposition about what's new when engineers work with AI agents. When you discover evidence relevant to the four patterns (verification findings, context architecture lessons, reproduce-don't-assess examples, LLM behavioral properties), file an issue at `ducroq/augmented-engineering` (renamed from agentic-engineering) with the pattern name, quantified results, and which claims it supports.

---

*Last updated: 2026-08-01*
