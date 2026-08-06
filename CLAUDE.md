---
stack: Python 3.12, PyTorch, Transformers, PEFT/LoRA
status: Production
repo: github.com/ducroq/llm-distillery
framework: agent-ready-projects v1.15.0
framework_reconciliation: |
  v1.15.0 (2026-08-06) adopted. Skill scope: `curate` and `audit-context` are
  user-global — the project-local copies here were DELETED, not reconciled,
  because a global shadows a local silently and the local one was never
  loading. Do not re-create them. `review-changes` and `test-verify-memory`
  stay project-local; `review-changes` is re-mapped rather than copied, since
  the template's risk tiers key on paths this repo does not have.
  Verify with: agent-ready-projects/scripts/install-global-skills.sh --check ~/repos
  Declined: nothing.
---

# CLAUDE.md - LLM Distillery

## What Is This?

**LLM Distillery** is a knowledge distillation framework. It trains small, cheap, local classifiers (Gemma-3-1B + LoRA) to replicate expensive cloud LLM scoring (Gemini Flash) at 100x lower cost and 50x faster inference.

**Core workflow:** Oracle (Gemini Flash) scores articles on dimensions (0-10) → Train student model (Gemma-3-1B) → Deploy as filter package

**System context:** llm-distillery creates filters. NexusMind deploys them for production scoring. The interface is the filter package: `filters/{name}/v{N}/` directories copied between repos, plus HuggingFace Hub uploads.

**Downstream consumer (2026-08-01):** `veen-systems/persuasion-scorer` — the #78/#79 persuasion-technique scorer, split out because a verified taxonomy is a research project, not a deploy package (its DR-003). It **depends on** this repo's distillation machinery; it must never vendor a copy. #78/#79 stay open here as definition/origin.

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
- **The 300-char length floor is a labelling-time rule only (#93, 2026-08-03).** No `prefilter.apply_filter()` checks content length. The floor lives in `ground_truth.batch_scorer.make_oracle_prefilter` — its rationale is LLM framework leakage, which is a property of the oracle *prompt*, and the student sees no prompt. The scoring path stamps `content_length` on every result and applies at most one config-gated `short_content.cap` (off on every filter; the only candidate defect, solutions v6, is still confounded — #92). **That stamp does not survive to disk (2026-08-06): `content_length` is populated on 0 of 50,605 persisted rows** even though the deployed `filter_base_scorer.py` is md5-identical to this repo's and calls `_stamp_content_length` in both `score_article` and `score_batch` — it is lost between the scorer and the row. ADR-022's stamp half is therefore **not** holding in production; see ducroq/NexusMind#300. To reason about content length today use `len(content)` on the persisted row (pre-enrichment runs *before* scoring, so it is the post-enrich length) plus `pre_enriched` / `original_content_length`. Adding `check_content_length` to a prefilter re-creates what #93 removed. `validate_article` still rejects empty content — empty is not short.
- **Most per-filter prefilters have no lens rules at all — and a matching pass rate does not mean a gate is safe to enforce.** Measured 2026-08-02 over 8,283 production articles (NM#285): length's share of all blocking is **100%** for `nature_recovery v4` and `solutions v6` (both declare `EXCLUSION_PATTERNS = {}` by design — commerce is upstream, ADR-004 — and their `POSITIVE_PATTERNS` are force-pass overrides, a no-op with nothing to override), 96.8% belonging, 92.6% investment_risk, 86.3% uplifting, **0% cultural_discovery**. So "enforce the prefilter" mostly meant "enforce a 300-char length floor" — which is why `expected_pass_rate` was **deleted** from nr/solutions rather than corrected, and why #93 exists. *(Those shares describe pre-#93 behaviour, and NexusMind's copy until the sync lands. On the llm-distillery side since 2026-08-03 the length share is 0% by construction.)* Separately: cd's observed rate *matches* its declared 0.25 and enforcing it still costs 15.5% of surfacing articles (19.9% non-English vs 13.0% English). **Rate agreement and safety-to-enforce are independent properties — measure recall before any flip (ADR-021).**
- **A filter's `prefilter` config does NOT mean the prefilter runs in production.** The per-lens *rule* prefilter (`filters/{name}/v{N}/prefilter.py`, ADR-018/019) has never executed in the production scoring path — the GPU scorer builds every scorer with `use_prefilter=False` and calls `score_batch(skip_prefilter=True)` (NM#284, found 2026-08-01; dead since 2026-02-10). It *does* run in the llm-distillery oracle/training path, which is why this survived six months. Unaffected: the e5 probe, the commerce prefilter (ADR-004), the obituary/violence gates, the NM#189 source-type allowlist. NM#284 stage 1 logs observed vs declared pass rate; enforcement is not yet on. **Never check prefilter state from `data/filtered/*/filtered_*.jsonl`** — it only receives `passed_prefilter: true` rows NexusMind’s pipeline writes it only under an `if result["passed_prefilter"]:` guard, so it is 100% passers by construction; use the pipeline's `N scored, M prefiltered` line or the shadow log. **Don't infer runtime behavior from config keys** — see `memory/calibration-history.md` Dead Ends.

- **A score is not a function of the article alone — there is a measured `|Δ| ≤ 0.16` noise floor under every comparison (#95, 2026-08-03).** Same model, same weights, same GPU, same process: only the batch an article lands in differs. It changes decisions, not just digits — re-scoring the ±0.30 band around the op-point flipped 7.1% of `solutions v6` and 9.1% of `uplifting v7` verdicts. **A run-to-run difference below ~0.1 near an op-point is indistinguishable from noise; never report one as an effect** — this binds ground-truth gates, FN-delta comparisons, normalization CDF fits and before/after deploy checks alike. Since 2026-08-03 NexusMind seeds its per-cycle shuffle (`NEXUSMIND_RUN_SEED`, logged in the start banner) so **a cycle can be replayed exactly — that is replay, not stability**; the next cycle reshuffles and the article moves again. Corpus-wide the affected share is small (0.07–0.32%), so this is a measurement-trust problem, not a reader-visible one. Sibling with the same magnitude and a different cause: cross-box skew |0.16| — never compare scores from different machines. Details in `docs/FILTER_PLAYBOOK.md` §7.
- **Fit `calibration.json` after every training run.** Isotonic regression on the val set. Commit with the filter package. The base scorer auto-loads it.
- **`.nexusmind-owns` is empty by default.** The manifest mechanism stays in place as a controlled-divergence escape hatch — entries get added only with a tracked issue and a resolution deadline. Long-term silent divergence between repos is the failure shape that the 2026-05-04 "manifest as anti-pattern" gotcha-log entry warns against (concrete: normalization plumbing was deleted from NexusMind on 2026-04-16 and went unnoticed for 18 days because the manifest masked it). Production-runtime concerns now live in `NexusMind/src/scoring/production_scorer.py`, which composes the shared base scorer rather than mutating it. `filters/common/filter_base_scorer.py` and `filters/common/hybrid_scorer.py` are pure shared math; sync freely.

### Working rules (promoted from the gotcha log — these are non-negotiable, not tips)

Moved here from `memory/MEMORY.md` on 2026-08-06: they are always-needed
constraints, and the memory index is navigational. Each was promoted only after
repeating.

- **Before shipping any gate, cap, threshold, config key or stamp, name the caller that loads it — in writing.** *(5th occurrence, one self-inflicted.)* A mechanism that is present, configured and unreachable is this repo's defining failure: ducroq/NexusMind#284 (per-filter prefilters never ran, six months), #94 (a gatekeeper binding 0 times in 191,616 articles), ducroq/NexusMind#281 (a gate that could never fire), ducroq/NexusMind#300 (the #93 `content_length` stamp computed then dropped — 0 of 50,605 rows), and `filters/cultural_discovery/v6` (a `hybrid_inference` block and probe shipped into a package with no inference module — **written the same day the other four were documented**). That last one is the point: knowing this failure mode does not prevent it; only running the check against your own work does. **Never infer runtime behaviour from the presence of a config key.** Two smells that must trigger the check: a package that passes self-tests but has never been loaded end-to-end, and a field initialised to `None` and populated somewhere you have not read.
- **Before using any source as evidence, establish what it excludes.** *(3 instances in one day.)* Applies to data (`filtered_*.jsonl` is 100% passers by construction **and** drops source-type-excluded rows — worth 0.129 on investment_risk), to nested structures (`metadata.quality` is not `nexus_mind_attributes.<lens>.source_quality`), to prior work (`gh repo list` misses repos with no remote), to literature (a search snippet reported a model's *worst* two techniques as its best), and to **time** (`data/raw/` is pre-enrichment and cannot stand in for what the scorer saw: 0.008 vs a true 0.647). A clean-looking result from an unexamined source is the hardest kind to falsify, because being right supplies no pressure to check how you got there. If it is a denominator, a baseline, or a claim of absence — enumerate the source first, and if the owner knows the set, ask rather than infer.
- **A parallel agent session may be working in the same checkout, so no git verb may take the whole tree as its argument.** *(2nd occurrence.)* `git add -A`, bare `git stash`, `git checkout .`, `git clean` — each one's blast radius is every modified file, including work you did not make and cannot see. One sweep put a seven-file filter sync into a docs commit; another stashed a second session's `NexusMind/image_analysis.py` while baselining a test suite, producing a "before" measurement of a tree that never existed and 8 phantom failures. **Always pass explicit paths**; run `git status --porcelain` before committing and stage only what you recognise. If a sweep is found after push, record it — do not rebase history another session may hold.
- **`pgrep -f "<pattern>"` cannot answer "is it running?"** *(3rd occurrence, twice in one session.)* It matches the shell carrying the pattern, and over ssh the bracket trick does not survive quoting. It has blocked a production deploy, reported a false "still running", and hidden a restart that silently did not launch. The output *looks* like an answer, which is what makes it dangerous. Use `ps -eo pid,etime,args | grep -v grep`, ask the service manager (`systemctl is-active`), or read the log's last timestamp. **If a process check decides whether you act, print the matching line before believing it.**

## Production Filters

Full details in `memory/filter-status.md`. Summary:

| Filter | Version | MAE | Status |
|--------|---------|-----|--------|
| **uplifting** | v7 | — | Deployed (NO_HUB, hybrid inference) |
| **sustainability_technology** | v3 | 0.72 | **REMOVED 2026-08-03** — replaced by solutions; package deleted, recover from git history |
| **investment-risk** | v6 | 0.47 | Deployed (HF Hub) |
| **cultural-discovery** | v5 | 0.70 | Deployed (HF Hub, DeepSeek oracle) |
| **belonging** | v1 | 0.49 | Deployed (HF Hub) |
| **nature_recovery** | v4 | recall 0.65 / prec 0.85 | Deployed (recall-first probe, v5 planned #71) |
| **solutions** | v6 | 0.48 | **LIVE** — gate passed 2026-07-27, normalization fitted 2026-07-28 |
| **foresight** | v1 | 0.75 | **REMOVED 2026-08-03** — merged into solutions (#43); package deleted, recover from git history. Closes out #64. |
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

## How To Write Answers Here

Added 2026-08-03 after the owner said, plainly: *"many times, I have no idea
what you are talking about."* That was about answers in chat, not about the
code or the docs. This project has a lot of internal shorthand and it is easy
to write replies that only make sense to whoever just did the work.

1. **Answer the question first, in one line.** If asked "is X OK?", the first
   line is yes, no, or not yet. Detail comes after, and only the detail that
   would change what the owner does.
2. **Never invent a label and then use it as if it were shared.** "Chain 13",
   "Batch F", "the NM#284 shape" — coined mid-session and immediately reused as
   common vocabulary. If a cluster needs a name, define it once in the same
   sentence, or don't name it.
3. **Expand an issue number the first time it appears in a reply.** "#86 (the
   cultural-discovery gate)" — not "#86". The owner works across five repos and
   should not have to hold the numbering in their head.
4. **Separate measured from guessed, every time.** "Measured over 8,283
   articles" vs "I think" vs "not tested". This project's failure mode is a
   confident claim nobody verified — see the `feedback-claim-requires-verify` and
   `feedback-verify-call-path` entries in the assistant's own memory (they live in
   the Claude Code auto-memory directory, **not** in this repo's `memory/`).
5. **Keep the caveats, cut the recap.** Brevity must never come out of the
   verification detail. The obituary answer on 2026-08-03 was only trustworthy
   *because* of "max score among survivors is 0.8488, zero at or above 0.85".
   Cut preamble, restatement of the question, and lists of things not pursued.
6. **Say what you did to the owner's machine and how to undo it.**

Rejected alternative: the `i-have-adhd` output-formatting plugin
(github.com/ayghri/i-have-adhd) — installed and removed the same day. It fixes
length and burying the answer, but not undefined jargon, which was the actual
complaint; and its push toward short confident output works against rules 4
and 5. Re-add with `claude plugin marketplace add ayghri/i-have-adhd` if the
rules above prove insufficient.

## Before You Start

**Always read `memory/MEMORY.md` first** — it's the project memory index with current work status, gotchas, and pointers to topic files.

| When you're... | Read... |
|----------------|---------|
| Starting a new session | `memory/MEMORY.md` — project memory index, current work status |
| Resuming thriving v1 work | `memory/thriving-v1-scoring.md` — scoring status, resume commands, full pipeline |
| Starting calibration / scorer-training / oracle-prompt work | `memory/calibration-history.md` — Dead Ends section: which approaches are already known dead (#69) |
| **Touching a prefilter, or considering an enforcement flip** | **`memory/prefilter-length-floor-hypotheses.md`** — what each prefilter actually blocks (measured), why `expected_pass_rate` was deleted from two filters, and why a matching rate is not a safety argument. Then #93. |
| **A legal/compliance question, or changing where training data comes from** | `docs/decisions/2026-08-05-tdm-opt-out-training-data.md` — why AI-crawler opt-outs don't bar training here, and the two carve-outs still open (the oracle ships full article text to Gemini/DeepSeek; the six deployed filters were never assessed). Cross-repo companion: `ovr.news/docs/compliance-register.md`. |
| **Reading a number off NexusMind production data** | **`memory/nexusmind-data-sources.md`** — `filtered_*.jsonl` ALSO drops source-type-excluded rows (scored, then discarded — worth 0.129 on investment_risk), and `data/raw/` is pre-enrichment. Reconcile denominators before diffing two sources. |
| **Touching normalization (fitting, debugging a score/tier that looks wrong, ovr ranking)** | **`docs/NORMALIZATION_METHOD.md`** — canonical method (anchored CDF, guards, reproduction steps); ADR-014 for the decision record, `docs/FILTER_PLAYBOOK.md` §6 for the digest. Normalization exists only for ovr.news cross-lens ranking; tier is reassigned on the *normalized* score by design, so `raw >= threshold` + `tier: low` is expected. Fit at `raw >= the filter's tier threshold` — enforced by `tests/unit/test_normalization_invariant.py`. Both #161 and #205 were `raw_min` drifting off that threshold. |
| **Measuring anything near an operating point, or comparing two runs' scores** | **`memory/score-batch-shape-noise.md`** — #95: batch composition alone moves a score up to \|0.162\| and flips 7–9% of near-boundary verdicts. Below ~0.1 near an op-point, a difference is indistinguishable from noise. Cross-box skew is the same magnitude — never compare scores from two machines. |
| **Touching cultural_discovery v6, or citing its probe numbers** | **`memory/cd-v6-probe-hypotheses.md`** — #98: what is confirmed (per-language gap gone; probe is batch-invariant), refuted (screening is a REGRESSION vs the gate; 4 of 5 "recovered" positives are off-lens), and the traps (v6 cannot score at all — no inference module, no `calibration.json`, and `_load_calibration` fails silent). |
| **Anything obituary/grief-related, or reading the junk-gate state** | `memory/project-obituary-detector.md` — enforcement is ON at v5@0.85; carryover, the two live v5 false negatives, and the four SSH verify assertions live here. |
| **Creating OR retraining ANY filter (START HERE)** | **`docs/FILTER_PLAYBOOK.md`** — the single source of truth: every compiled lesson + the canonical reference (`nature_recovery v4`). Read before touching filter code. Then `docs/agents/filter-development-guide.md` (depth) / `docs/guides/filter-creation-workflow.md` (quick steps). |
| Deploying to NexusMind or gpu-server | `docs/RUNBOOK.md` — deployment, training, scoring how-to |
| Training on GPU server | `memory/gpu-server.md` — venv, PYTHONPATH, HF_HUB_OFFLINE |
| Debugging model loading or PEFT issues | `memory/gemma3-model.md` — Auto mapping fix, key format details |
| Making architectural decisions | `docs/adr/README.md` — 21 settled ADRs (001–019, 021, 022; 020 is a draft) |
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

*Last updated: 2026-08-06 afternoon (cd v6 e5 probe measured and committed — #98, held-out oracle FN 0/75 vs the keyword gate's 10/75; #99 English-only escape hatch filed; FS#120 answered — `pre_enrich` fires at 500; ducroq/NexusMind#300 — the `content_length` stamp does not reach disk)*
