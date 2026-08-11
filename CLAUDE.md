---
stack: Python 3.12, PyTorch, Transformers, PEFT/LoRA
status: Production
repo: github.com/ducroq/llm-distillery
framework: agent-ready-projects v1.21.0
framework_reconciliation: |
  v1.21.0 (2026-08-11) triaged same day: NOTHING adopter-facing here.
  Its content is the `install-global-skills.sh` release guard (a framework
  maintainer tool), `templates/release.md` Step 1 (we publish no package),
  `templates/coordination.md` (we have none) and a `docs/GUIDE.md` sentence.
  The only two template edits are stamp bumps. All three user-global skills
  verified byte-identical to the v1.21.0 TAG. Adopter action from its notes
  ('refresh globals only after the release tag is pushed and verified')
  is satisfied by that check, not by a reinstall.
  Stamp = which framework surfaces were reconciled. It does NOT assert that any
  behaviour changed, nor that a skill has since been run.
  Per-release history: `docs/decisions/framework-adoption-history.md`.
  OPERATIVE RULES (these govern; the history file is provenance only):
  - `curate` and `audit-context` are USER-GLOBAL. The project-local copies were
    DELETED, not reconciled — a global shadows a local silently and the local was
    never loading. Do not re-create them.
  - `review-changes` and `test-verify-memory` stay PROJECT-LOCAL.
    `review-changes` is re-mapped, not copied: the template's risk tiers key on
    paths this repo does not have, so a verbatim install would tier every change
    here as LOW and quietly do nothing.
  - No `hypothesis-log.md` at either path, by choice — hypotheses live in
    per-topic memory files. `curate` Step 0.6 is a deliberate no-op here.
  - DECLINED v1.20.0's gotcha-log `Occurrences` column: no Promoted table exists
    here, promotion targets § "Working rules", and the rate is already in prose.
    So `curate` Step 2 asks every session to increment a column with no home —
    expected, not a bug to fix.
  - OPEN, pre-dating the v1.19/v1.20 gap: this file has no framework-drift
    session row (`templates/project-file.md:25` ships one). Its absence is the
    likely reason that drift sat two releases unreviewed. Engineer's call.
  Verify installs: agent-ready-projects/scripts/install-global-skills.sh --check ~/repos
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
- **The 300-char length floor is a labelling-time rule only (#93, 2026-08-03).** No `prefilter.apply_filter()` checks content length. The floor lives in `ground_truth.batch_scorer.make_oracle_prefilter` — its rationale is LLM framework leakage, which is a property of the oracle *prompt*, and the student sees no prompt. The scoring path stamps `content_length` on every result and applies at most one config-gated `short_content.cap` (off on every filter; the only candidate defect, solutions v6, is still confounded — #92). **That stamp reached 0 of 50,605 rows from 2026-08-06 and is FIXED as of the 2026-08-08 17:10 cycle — `content_length` is now populated on 100% of rows in all six filters** (ducroq/NexusMind#300, `7a0509d`). It was **five explicit allowlists in series**, not the two first diagnosed: the server Pydantic model, the `gpu_client.py` dataclass, that dataclass's construction, `NexusMind/scripts/main.py`'s dict conversion, and that same file's `analysis` dict. The first fix corrected hops 1 and 5 and the next cycle still read 0/2,170 — *code-proven is not outcome-proven*. Rows written **before** `filtered_20260808_17*` still have it absent or null, so any historical analysis must still use `len(content)` on the persisted row (pre-enrichment runs *before* scoring, so it is the post-enrich length) plus `pre_enriched` / `original_content_length`. Same commit fixed `stage_used` / `stage1_estimate` (llm-distillery#88), now also 100%. Adding `check_content_length` to a prefilter re-creates what #93 removed. `validate_article` still rejects empty content — empty is not short.
- **Most per-filter prefilters have no lens rules at all — and a matching pass rate does not mean a gate is safe to enforce.** Measured 2026-08-02 over 8,283 production articles (NM#285): length's share of all blocking is **100%** for `nature_recovery v4` and `solutions v6` (both declare `EXCLUSION_PATTERNS = {}` by design — commerce is upstream, ADR-004 — and their `POSITIVE_PATTERNS` are force-pass overrides, a no-op with nothing to override), 96.8% belonging, 92.6% investment_risk, 86.3% uplifting, **0% cultural_discovery**. So "enforce the prefilter" mostly meant "enforce a 300-char length floor" — which is why `expected_pass_rate` was **deleted** from nr/solutions rather than corrected, and why #93 exists. *(Those shares describe pre-#93 behaviour, and NexusMind's copy until the sync lands. On the llm-distillery side since 2026-08-03 the length share is 0% by construction.)* Separately: cd's observed rate *matches* its declared 0.25 and enforcing it still costs 15.5% of surfacing articles (19.9% non-English vs 13.0% English). **Rate agreement and safety-to-enforce are independent properties — measure recall before any flip (ADR-021).**
- **A filter's `prefilter` config does NOT mean the prefilter runs in production.** The per-lens *rule* prefilter (`filters/{name}/v{N}/prefilter.py`, ADR-018/019) has never executed in the production scoring path — the GPU scorer builds every scorer with `use_prefilter=False` and calls `score_batch(skip_prefilter=True)` (NM#284, found 2026-08-01; dead since 2026-02-10). It *does* run in the llm-distillery oracle/training path, which is why this survived six months. Unaffected: the e5 probe, the commerce prefilter (ADR-004), the obituary/violence gates, the NM#189 source-type allowlist. NM#284 stage 1 logs observed vs declared pass rate; enforcement is not yet on. **Never check prefilter state from `data/filtered/*/filtered_*.jsonl`** — it only receives `passed_prefilter: true` rows NexusMind’s pipeline writes it only under an `if result["passed_prefilter"]:` guard, so it is 100% passers by construction; use the pipeline's `N scored, M prefiltered` line or the shadow log. **Don't infer runtime behavior from config keys** — see `memory/calibration-history.md` Dead Ends.

- **A score is not a function of the article alone — there is a measured `|Δ| ≤ 0.16` noise floor under every comparison (#95, 2026-08-03).** Same model, same weights, same GPU, same process: only the batch an article lands in differs. It changes decisions, not just digits. **A run-to-run difference below ~0.1 near an op-point is indistinguishable from noise; never report one as an effect** — this binds ground-truth gates, FN-delta comparisons, normalization CDF fits and before/after deploy checks alike. **Owner decision 2026-08-06: budget for the floor, don't try to remove it.** An article predicted within 0.16 of the surfacing threshold is *indeterminate*; every metric at that threshold carries a band, and **two models whose bands overlap are NOT DISTINGUISHABLE** whatever their point estimates say. `scripts/gate/ground_truth_gate.py` prints it (`--noise-floor`, default 0.16). Sibling with the same magnitude and a different cause: cross-box skew |0.16| — **never compare scores from different machines.** A seeded cycle replays exactly; **that is replay, not stability.** Flip rates, the run-seed mechanism and the corpus-wide share: `memory/score-batch-shape-noise.md`, `docs/FILTER_PLAYBOOK.md` §7.
- **A false positive costs a reader; a false negative costs nothing visible. Optimise SPECIFICITY, and NEVER rank filters on MAE (ADR-023, owner 2026-08-09).** Owner, verbatim: *"letting junk through is way worse than not catching positives. Junk kills readers; positives they don't know about don't hurt them."* This was always the target and was written down nowhere, so on 2026-08-09 an agent produced a six-filter quality ranking on mean absolute error and recommended a calibration change on it — both retracted. **MAE is the wrong instrument twice over**: it weights every article equally while the product only cares about the thin band at the op-point; and each filter's test split has its own positive rate, so a more enriched split carries larger per-article error *for identical model quality*. **But do not overstate the retraction either** — composition explains only ~27% of the gap that ranking was built on, so the residual may still be real. The ranking was invalid *as made* and MAE is the wrong objective regardless. **Precision is base-rate dependent too — only recall and specificity are conditional on the true class and comparable across splits.** Report both, always with the split's positive rate. Consequences: **active-learning batches sample ABOVE the op-point** (where junk reaches readers), not below it (which hunts the cheap error); ties inside the #95 band go to specificity. **Does NOT apply to the Stage-1 e5 probe**, which is a recall-safe screen by design — there the FN is the expensive error, hence `train_probe.py --objective recall`. Per-filter recall/specificity, the split positive rates and the composition arithmetic: `memory/filter-status.md`.
- **Fit `calibration.json` after every training run.** Isotonic regression on the val set. Commit with the filter package. The base scorer auto-loads it.
- **`.nexusmind-owns` is empty by default.** The manifest mechanism stays in place as a controlled-divergence escape hatch — entries get added only with a tracked issue and a resolution deadline. Long-term silent divergence between repos is the failure shape that the 2026-05-04 "manifest as anti-pattern" gotcha-log entry warns against (concrete: normalization plumbing was deleted from NexusMind on 2026-04-16 and went unnoticed for 18 days because the manifest masked it). Production-runtime concerns now live in `NexusMind/src/scoring/production_scorer.py`, which composes the shared base scorer rather than mutating it. `filters/common/filter_base_scorer.py` and `filters/common/hybrid_scorer.py` are pure shared math; sync freely.

- **An operating point lives in FOUR places, and `config.yaml` is NOT the runtime one.** `base_scorer.py`'s `TIER_THRESHOLDS` is what scores; `config.yaml scoring.tiers` is documentation. Changing the config alone is a **no-op in production**. The other two are `normalization.json` `stats.raw_min` (which `tests/unit/test_normalization_invariant.py` requires to equal the tier threshold — both NM#161 and NM#205 were that drifting) and the expectation in `tests/unit/test_normalization_op_point.py`. **Any op-point move changes all four in one commit and refits normalization**, and `MAX_NORMALIZATION_RAW_MIN = 4.5` caps how high it can go (strict `>`, so 4.5 is accepted with zero margin; above that the production loader silently falls back to `score_scale_factor`). Caught 2026-08-11 by `fit_normalization.py` refusing to agree with itself — not by review. Verify by **executing** the tier assignment, not by re-reading the config. **A FIFTH place holds the same number and is NOT a tier boundary: NexusMind's `pipeline.enrichment.min_score` (`config/app.yaml`), which gates post-scoring enrichment at 4.0.** It is an independent constant that happens to share the value — moving a filter's op-point does **not** move it, and a filter whose distribution sits below 4.0 goes silently un-enriched (NM#319). Raising an op-point cannot starve it further; **lowering one, or shipping a filter that scores low, can.** ⚠️ **That gate reads the NORMALIZED score**, so a rescale cannot move a filter across it — a percentile CDF maps it straight back (`memory/solutions-v6-dimension-hypotheses.md` R3).

### Working rules (promoted from the gotcha log — these are non-negotiable, not tips)

Moved here from `memory/MEMORY.md` on 2026-08-06: they are always-needed
constraints, and the memory index is navigational. Each was promoted only after
repeating.

- **Before shipping any gate, cap, threshold, config key or stamp, name the caller that loads it — and then prove the outcome changed at the END of the run.** *(9th occurrence 2026-08-11 afternoon; 8th 2026-08-11 midday — five self-inflicted.)* **Naming the caller is not sufficient.** Guards have shipped with *correct callers on the right paths* and still done nothing — one reverted downstream by a `COALESCE` merge, one short-circuited by an earlier commit point. Both passed unit tests on the predicate; a green test on the predicate proves only the predicate. If a guard's whole value is that it changes an outcome, **run it and print the resulting state**, and ask "is this the only writer of this field?" — not just "is my code reached?". **Never infer runtime behaviour from the presence of a config key.** Three smells that must trigger the check: a package that passes self-tests but has never been loaded end-to-end; a field initialised to `None` and populated somewhere you have not read; and **a feature validated on "production data" without naming WHICH STAGE** (the arXiv announce prefix is a 91.6% detector at collection and **0.000** after enrichment — both are production data). Two related traps: **a comment explaining why code is safe is a claim like any other**, and **if a criterion depends on "now", encode the criterion, never its answer**. → The catalogue of occurrences (NM#284, #94, NM#281, NM#300, cd v6) is in `memory/gotcha-log.md` § *The unreachable-mechanism catalogue*.
- **Before using any source as evidence, establish what it excludes.** *(6th occurrence 2026-08-11 afternoon — a PEER asserted a population claim from a doc whose caveat section they had read that same session and not re-read; verifying against their source rather than their report surfaced two further exclusions. 5th 2026-08-11 midday — see below; 4th 2026-08-09 — and this one was a **machine**, not a file.* I inventoried b650-gpu, found no judge verdicts, and reported the precision panel as UNADJUDICATED, blocking a whole track. The verdicts existed and had for three days: they live in the NexusMind checkout under `data/research/precision_panel*/`, which `.gitignore:230` excludes, so they were never copied to the GPU box. **A host is a source with an exclusion list too** — "I looked on the machine where the work was done" is the same error as "I read the file that only holds passers".*)* Applies to data (`filtered_*.jsonl` is 100% passers by construction **and** drops source-type-excluded rows — worth 0.129 on investment_risk), to nested structures (`metadata.quality` is not `nexus_mind_attributes.<lens>.source_quality`), to prior work (`gh repo list` misses repos with no remote), to literature (a search snippet reported a model's *worst* two techniques as its best), and to **time** (`data/raw/` is pre-enrichment and cannot stand in for what the scorer saw: 0.008 vs a true 0.647). A clean-looking result from an unexamined source is the hardest kind to falsify, because being right supplies no pressure to check how you got there. If it is a denominator, a baseline, or a claim of absence — enumerate the source first, and if the owner knows the set, ask rather than infer.
- **A parallel agent session may be working in the same checkout, so no git verb may take the whole tree as its argument.** *(2nd occurrence.)* `git add -A`, bare `git stash`, `git checkout .`, `git clean` — each one's blast radius is every modified file, including work you did not make and cannot see. One sweep put a seven-file filter sync into a docs commit; another stashed a second session's `NexusMind/image_analysis.py` while baselining a test suite, producing a "before" measurement of a tree that never existed and 8 phantom failures. **Always pass explicit paths**; run `git status --porcelain` before committing and stage only what you recognise. If a sweep is found after push, record it — do not rebase history another session may hold.
- **`pgrep -f "<pattern>"` cannot answer "is it running?"** *(3rd occurrence, twice in one session.)* It matches the shell carrying the pattern, and over ssh the bracket trick does not survive quoting. It has blocked a production deploy, reported a false "still running", and hidden a restart that silently did not launch. The output *looks* like an answer, which is what makes it dangerous. Use `ps -eo pid,etime,args | grep -v grep`, ask the service manager (`systemctl is-active`), or read the log's last timestamp. **If a process check decides whether you act, print the matching line before believing it.**

## Production Filters

Full details in `memory/filter-status.md`. Summary:

| Filter | Version | MAE | Status |
|--------|---------|-----|--------|
| **uplifting** | v7 | recall 0.61 / spec 0.97 | Deployed (NO_HUB, hybrid inference). **Op-point 4.5 since 2026-08-11 (#102)** |
| **sustainability_technology** | v3 | 0.72 | **REMOVED 2026-08-03** — replaced by solutions; package deleted, recover from git history |
| **investment-risk** | v6 | recall 0.72 / spec 0.97 | Deployed (HF Hub, private). **Op-point 4.25 since 2026-08-11** |
| **cultural-discovery** | v5 | recall 0.59 / spec 0.98 | Deployed (HF Hub, DeepSeek oracle) — **still the live version** |
| **cultural-discovery** | v6 | (v5's) | **NOT LIVE — but no longer blocked (2026-08-08).** Package parity 2026-08-06 (#98): v5's student + e5 probe + commerce-only prefilter, no retrain. Hub repo created (private, v5 adapter verbatim, md5-identical); `normalization.json` fitted n=3,680 from `filter_version=5.0` rows — valid because the student is unchanged and the probe removes 1 of 2,653 rows above the 4.0 op-point; `--check-hub` 9/9; loaded end-to-end and scored. **Remaining: the cutover deploy itself, then refit normalization from real 6.0 rows.** |
| **belonging** | v1 | recall 0.60 / spec 0.985 | Deployed (HF Hub) |
| **nature_recovery** | v4 | recall 0.65 / prec 0.85 | Deployed (recall-first probe, v5 planned #71) |
| **solutions** | v6 | recall 0.67 / spec 0.97 | **LIVE** — gate passed 2026-07-27, normalization fitted 2026-07-28 |
| **foresight** | v1 | 0.75 | **REMOVED 2026-08-03** — merged into solutions (#43); package deleted, recover from git history. Closes out #64. |
| **thriving** | v1 | — | PARKED indefinitely (ADR-015) |
| **ai-engineering-practice** | v1 | — | Separate product, not ovr.news (table read v2; only v1 is on disk) |

## Key Decisions

- **Dimensional regression (0-10)** — not classifications (ADR-001)
- **Screen+merge for needle-in-haystack filters** (ADR-003)
- **Commerce is the only universal prefilter** (ADR-004)
- **Active learning for rare tiers** (ADR-005)
- **Fine-tuning beats embedding probes** — research confirmed
- **Gemma-3-1B** — replaced Qwen2.5; better MAE, faster inference
- **Add filters first, reduce later** — deploy as separate tabs, dedup later (ADR-009)
- **Lens-aligned filter naming — the rename backlog is CLOSED, don't re-open it at a version bump.** Rename to the lens name only where it stands alone out of context; otherwise keep the filter name, or build `{qualifier}_{lens}`. Settled 2026-08-06: `cultural_discovery` and `nature_recovery` **keep their names** (their Hub repos are public standalone artefacts, and `discovery-filter-vN` / `recovery-filter-vN` drop the qualifier that says what the model is about); `solutions` is **confirmed as-is** (already migrated once at v4, second cross-repo change not worth it); `uplifting` → **`human_thriving` at v8** — not bare `thriving`, which is an existing parked directory. ADR-012's three stated audiences were all internal; the Hub was never weighed (ADR-012, amended)
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
- **Asymmetric loss — precision over recall** — a false positive reaches a reader, a false negative is invisible and the slot refills; optimise specificity at the op-point, never rank filters on MAE, compare only on recall + specificity (ADR-023)

See `docs/adr/README.md` for full ADR index, `docs/decisions/` for detailed records.

## How To Write Answers Here

Rules for **chat replies**, not for code or docs. Origin and the rejected
alternative: `feedback-plain-answers` in the Claude Code auto-memory.

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

## Before You Start

**Always read `memory/MEMORY.md` first** — it's the project memory index with current work status, gotchas, and pointers to topic files.

| When you're... | Read... |
|----------------|---------|
| Starting a new session | `memory/MEMORY.md` — project memory index, current work status |
| Resuming thriving v1 work | `memory/thriving-v1-scoring.md` — scoring status, resume commands, full pipeline |
| Starting calibration / scorer-training / oracle-prompt work | `memory/calibration-history.md` — Dead Ends section: which approaches are already known dead (#69) |
| **Touching a prefilter, or considering an enforcement flip** | **`memory/prefilter-length-floor-hypotheses.md`** — what each prefilter actually blocks (measured), why `expected_pass_rate` was deleted from two filters, and why a matching rate is not a safety argument. Then #93. |
| **A legal/compliance question, or changing where training data comes from** | `docs/decisions/2026-08-05-tdm-opt-out-training-data.md` — why AI-crawler opt-outs don't bar training here, and the two carve-outs still open (the oracle ships full article text to Gemini/DeepSeek; the six deployed filters were never assessed). Cross-repo companion: `ovr.news/docs/compliance-register.md`. |
| **Adding a stamp / config key, or trusting a stamped field in an analysis** | **`memory/stamp-contract-integrity.md`** — the stamps are a per-article feature set (~40+ numbers) and until 2026-08-08 nothing validated them. `contracts/*.schema.json` checks SHAPE, is permissive, and had **never been run against a production row** (first run: 908 violations). Run `NexusMind/scripts/stamp_census.py` for population + consumers before quoting any stamped field. |
| **Reading a number off NexusMind production data** | **`memory/nexusmind-data-sources.md`** — `filtered_*.jsonl` ALSO drops source-type-excluded rows (scored, then discarded — worth 0.129 on investment_risk), and `data/raw/` is pre-enrichment. Reconcile denominators before diffing two sources. **ovr.db `live_articles` is the ONLY source that answers "did a reader see it?"; its `weighted_average` is NORMALIZED, not raw.** |
| **Quoting any Google News number, or touching the GN population** | **`memory/google-news-corpus-hypotheses.md`** — GN is 25.7% of the corpus and **100.0% sub-300-char headline echoes** that can never be enriched (NM#310). Training corpora are 0–4.9% GN. Five claims are already REFUTED there, four of them denominator errors. **Never oracle-re-score a GN row** (median 89 chars, below the floor that exists for exactly that reason), and never match GN on a `gn_` key prefix — it under-counts ~5:1. |
| **Touching normalization (fitting, debugging a score/tier that looks wrong, ovr ranking)** | **`docs/NORMALIZATION_METHOD.md`** — canonical method (anchored CDF, guards, reproduction steps); ADR-014 for the decision record, `docs/FILTER_PLAYBOOK.md` §6 for the digest. Normalization exists only for ovr.news cross-lens ranking; tier is reassigned on the *normalized* score by design, so `raw >= threshold` + `tier: low` is expected. Fit at `raw >= the filter's tier threshold` — enforced by `tests/unit/test_normalization_invariant.py`. Both #161 and #205 were `raw_min` drifting off that threshold. |
| **Measuring anything near an operating point, or comparing two runs' scores** | **`memory/score-batch-shape-noise.md`** — #95: batch composition alone moves a score up to \|0.162\| and flips 7–9% of near-boundary verdicts. Below ~0.1 near an op-point, a difference is indistinguishable from noise. Cross-box skew is the same magnitude — never compare scores from two machines. |
| **Changing a dimension WEIGHT, or calling any dimension "dead"** | **`memory/solutions-v6-dimension-hypotheses.md`** — `solutions v6`'s `community_practice_strength` is zero on 83% of on-topic articles and is **not dead, just rare**: highest conditional correlation (r=0.622) and lowest false-fire (4.0%) of the seven. Re-weighting is inert (0.7% churn at matched volume), and its apparent +19.5pp at an absolute 4.0 is an **artifact** — the enrichment gate reads the NORMALIZED score, and a percentile CDF removes any monotone rescale. A dimension's zero rate is base rate, not breakage. |
| **Touching cultural_discovery v6, or citing its probe numbers** | **`memory/cd-v6-probe-hypotheses.md`** — #98: what is confirmed (per-language gap gone; probe is batch-invariant), refuted (screening is a REGRESSION vs the gate; 4 of 5 "recovered" positives are off-lens), and the traps (v6 cannot score at all — no inference module, no `calibration.json`, and `_load_calibration` fails silent). |
| **Anything obituary/grief-related, or reading the junk-gate state** | `memory/project-obituary-detector.md` — enforcement is ON at v5@0.85; carryover, the two live v5 false negatives, and the four SSH verify assertions live here. |
| **Creating OR retraining ANY filter (START HERE)** | **`docs/FILTER_PLAYBOOK.md`** — the single source of truth: every compiled lesson + the canonical reference (`nature_recovery v4`). Read before touching filter code. Then `docs/agents/filter-development-guide.md` (depth) / `docs/guides/filter-creation-workflow.md` (quick steps). |
| Deploying to NexusMind or gpu-server | `docs/RUNBOOK.md` — deployment, training, scoring how-to |
| Training on GPU server | `memory/gpu-server.md` — venv, PYTHONPATH, HF_HUB_OFFLINE |
| Debugging model loading or PEFT issues | `memory/gemma3-model.md` — Auto mapping fix, key format details |
| Making architectural decisions | `docs/adr/README.md` — 22 settled ADRs (001–019, 021–023; 020 is a draft) |
| Checking priorities or planning work | `docs/TODO.md` and `docs/ROADMAP.md` |
| Understanding system design | `docs/ARCHITECTURE.md` |
| Reviewing work quality | `docs/checklists/` — architect, test, implement, QA gates |
| Stuck on tooling or infra | `memory/gotcha-log.md` — problem/fix archive |
| **Touching corroboration, story-dedup, or any matching feature** | **`memory/corroboration-feature-hypotheses.md`** — what is confirmed, refuted and untested. The threshold is NOT the lever (primary literature is 20–30% of merges and 0–14% correct); shared-number features are refuted; time is confirmed at AUC 0.809 and still switched off |
| Planning across repos, or asking "what should I work on" | `memory/cross-repo-prioritization.md` — issue landscape, chains, and the two standing traps (the decision list drifts faster than the issue list; a findings list is a sample, not an inventory) |
| Running anything long, or told "the GPU is free" | `memory/b650-gpu.md` — the non-production 3090 Ti. `ssh b650-gpu` works from the workstation, NOT from sadalsuud |
| Checking which lens/tab a filter feeds | `memory/ovr-lens-set-current.md` — current lens→filter→tab mapping |
| Writing docs for a deployed filter | `memory/filter-doc-standard.md` — the required documentation set |
| Building a filter on a DeepSeek oracle, or citing cultural_discovery v5 as a reference | `memory/cd-v5-reference-status.md` — why v5 is the DeepSeek-oracle reference example, and the ADR-020 methodology it demonstrates |
| Retraining uplifting, or touching the obituary/violence gates | `memory/uplifting-v7-training.md`, `memory/obituary-v4-hypotheses.md`, `memory/violence-promotion-v1-hypotheses.md` |
| **Wanting the whole chain in one place, or the live pipeline state** | **`veen-systems/pipeline-atlas`** — the four repos as one signal path, plus an ops snapshot regenerated every 20 min. Served from sadalsuud on Tailscale (`http://100.78.93.76:8099/`), not GitHub Pages. It states mechanisms only; every number is in the snapshot or carries a verify command. **It replaced ovr.news `/ops/architecture`, deleted 2026-08-07.** |
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

*Last updated: 2026-08-11 (evening). **Framework current at v1.21.0** — v1.22.0 is an unreleased candidate branch in another session's checkout; do not pin it. **`solutions v6`'s `community_practice_strength` is NOT dead, just rare** — see `memory/solutions-v6-dimension-hypotheses.md` before touching any dimension weight. Four open owner rulings: **#106** (re-scoped, not closed), **#107**, **#109** (costed, four gaps), and *should ovr.news enrich* (deferred behind ovr#312 — wait for the number). **Next actions and full decision state: `docs/TODO.md` top block.** Session records: `memory/project_session_2026_08_11_evening.md` (+ `_afternoon`, `_midday`).*
