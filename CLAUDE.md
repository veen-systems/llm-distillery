---
stack: Python 3.12, PyTorch, Transformers, PEFT/LoRA
status: Production
repo: github.com/ducroq/llm-distillery
framework: agent-ready-projects v1.36.1   # a NUMBER, not a status — never write "current" here; the framework's release cadence falsifies the adjective, not the pin
framework_reconciliation: |
  v1.26.1+v1.27.0+v1.28.0 triaged 2026-08-26: 3 adopt, 0 decline. STAMP HELD at
  v1.26.0 until 2 unlanded adopt items ship — held, NOT unreviewed. Every release,
  and which adopt items landed: `docs/decisions/framework-adoption-history.md`.
  v1.23.0's placeholder markers were DEFERRED there and are now DONE — 14 paths
  marked, counted by `refcheck.py` (2026-08-16).
  Stamp = which framework surfaces were reconciled. It does NOT assert that any
  behaviour changed, nor that a skill has since been run.
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

**Downstream consumer (2026-08-01):** `veen-systems/persuasion-scorer` — the #78/#79 persuasion-technique scorer. It **depends on** this repo's distillation machinery; **it must never vendor a copy.** #78/#79 stay open here as definition/origin. **#116 (activation/arousal) is scoped THERE, not here** (its DR-007); #116 stays open here as the ethics decision.

## Tech Stack

- **Oracle**: Gemini Flash 2.5 (real-time — **there is no Batch API call site**, so Batch
  pricing is not an option we can pick); DeepSeek V4 Flash is **1.74× cheaper than the
  Gemini path that exists** even after the 2026-08-16 hike, so the cd v5 default stands.
  ⛔ **Never quote a $/article figure without naming the prompt** — cost is set by the
  input/output ratio (measured 20–43) and by the prompt's own **cache ceiling**
  (1.5%–35.7%, #131). Rates, measured shapes and the arithmetic:
  `memory/oracle-pricing-scheduling.md`; recompute with `scripts/analysis/oracle_cost.py`.
- **Student**: Gemma-3-1B (`google/gemma-3-1b-pt`) with PEFT/LoRA adapters
- **Calibration**: Per-dimension isotonic regression (ADR-008)
- **Hybrid inference**: e5-small embedding probe (Stage 1) + fine-tuned model (Stage 2, ADR-006)
- **Training data**: 5K-10K oracle-scored articles per filter, 80/10/10 splits

## Hard Constraints

- **Oracle outputs scores only.** Dimensional scores (0-10), never tier/stage classifications. Tier assignment is postprocessing. Changing thresholds must never require re-labeling.
- **Use `load_base_model_for_seq_cls()`** from `filters/common/model_loading.py`. Never use `AutoModelForSequenceClassification` directly — Gemma-3-1B's `gemma3_text` config isn't in the Auto mapping.
- **Keep PEFT adapters in OLD key format.** `.lora_A.weight` / `score.weight`, not `.lora_A.default.weight`. Never run `resave_adapter.py` before Hub upload — it breaks `PeftModel.from_pretrained()`.
- **The 300-char length floor is a labelling-time rule only (#93, 2026-08-03).** No `prefilter.apply_filter()` checks content length. The floor lives in `ground_truth.batch_scorer.make_oracle_prefilter` — its rationale is LLM framework leakage, which is a property of the oracle *prompt*, and the student sees no prompt. The scoring path stamps `content_length` on every result and applies at most one config-gated `short_content.cap` (off on every filter; the only candidate defect, solutions v6, is still confounded — #92). That stamp is **populated on 100% of rows in all six filters** since the 2026-08-08 17:10 cycle. ⚠️ **Rows written before `filtered_20260808_17*` still have it absent or null** — historical analysis must use `len(content)` on the persisted row (pre-enrichment runs *before* scoring, so it is the post-enrich length) plus `pre_enriched` / `original_content_length`. Adding `check_content_length` to a prefilter re-creates what #93 removed. `validate_article` still rejects empty content — **empty is not short**. Why it read 0 for two days, the five-allowlists-in-series diagnosis and *code-proven is not outcome-proven*: `memory/stamp-contract-integrity.md`.
- **Most per-filter prefilters have no lens rules at all — and a matching pass rate does not mean a gate is safe to enforce.** Measured 2026-08-02 over 8,283 production articles (NM#285), length's share of all blocking ran from **100%** (`nature_recovery v4`, `solutions v6`) to **0%** (`cultural_discovery`), so "enforce the prefilter" mostly meant "enforce a 300-char length floor" — which is why `expected_pass_rate` was **deleted** from nr/solutions rather than corrected. ⚠️ **cd's observed rate *matches* its declared 0.25 and enforcing it still costs 15.5% of surfacing articles** (19.9% non-English vs 13.0% English). **Rate agreement and safety-to-enforce are independent properties — measure recall before any flip (ADR-021).** Per-filter shares and the pre-/post-#93 caveat: `docs/FILTER_PLAYBOOK.md` §0b, `memory/prefilter-length-floor-hypotheses.md`.
- **A filter's `prefilter` config does NOT mean the prefilter runs in production.** The per-lens *rule* prefilter (`filters/{name}/v{N}/prefilter.py`, ADR-018/019) has never executed in the production scoring path — dead since 2026-02-10, found 2026-08-01 (NM#284). It *does* run in the llm-distillery oracle/training path, which is why it survived six months. **Never check prefilter state from `data/filtered/*/filtered_*.jsonl`** — written only under an `if result["passed_prefilter"]:` guard, so it is 100% passers by construction; use the pipeline's `N scored, M prefiltered` line or the shadow log. **Don't infer runtime behavior from config keys** (`memory/calibration-history.md` Dead Ends). What is unaffected, and the shadow-log biases: `docs/FILTER_PLAYBOOK.md` §0b.

- **A score is not a function of the article alone — there is a measured `|Δ| ≤ 0.16` noise floor under every comparison (#95, 2026-08-03).** Batch composition alone; it changes decisions, not just digits. **A run-to-run difference below ~0.1 near an op-point is indistinguishable from noise; never report one as an effect.** **Owner decision 2026-08-06: budget for the floor, don't try to remove it** — every metric at the threshold carries a band, and **two models whose bands overlap are NOT DISTINGUISHABLE** whatever their point estimates say. `scripts/gate/ground_truth_gate.py` prints it (`--noise-floor`, default 0.16). ⚠️ **Its sibling is NOT the box** (corrected 2026-08-29): with pins and device matched **on CPU**, two machines were **bit-identical, 660/660** — CUDA-to-CUDA is **UNMEASURED**, so that is an extrapolation, not a rule. Real terms: **stack 0.2008**, **CPU→CUDA 0.1956** — MAX |Δ| over 660 rows (1 and 3 rows exceed 0.16), not typical magnitudes. Dump with `box_parity.py`, then **`diff_box_parity.py --threshold`** — the threshold lives there, not on the dump. Flip rates, the run-seed mechanism, *replay is not stability*, and the corpus-wide share: `memory/score-batch-shape-noise.md`, `docs/FILTER_PLAYBOOK.md` §7.
- **A false positive costs a reader; a false negative costs nothing visible. Optimise SPECIFICITY, and NEVER rank filters on MAE (ADR-023, owner 2026-08-09).** Owner, verbatim: *"letting junk through is way worse than not catching positives. Junk kills readers; positives they don't know about don't hurt them."* **Precision and MAE are base-rate dependent — only recall and specificity are conditional on the true class and comparable across splits.** Report both, always with the split's positive rate. Consequences: **active-learning batches sample ABOVE the op-point** (where junk reaches readers), not below it (which hunts the cheap error); ties inside the #95 band go to specificity. **Does NOT apply to the Stage-1 e5 probe**, a recall-safe screen by design — there the FN is the expensive error, hence `train_probe.py --objective recall`. The retracted 2026-08-09 MAE ranking, why MAE is wrong twice over, and the ~27% composition arithmetic that stops the retraction being overstated: `memory/filter-status.md`.
- **Fit `calibration.json` after every training run.** Isotonic regression on the val set. Commit with the filter package. The base scorer auto-loads it.
- **`.nexusmind-owns` must stay empty.** Entries only with a tracked issue and a resolution deadline — the escape-hatch rationale and the 18-day normalization-drift incident are in the file's own header comment. `filters/common/filter_base_scorer.py` and `filters/common/hybrid_scorer.py` are pure shared math; sync freely.

- **An operating point lives in FOUR places, and `config.yaml` is NOT the runtime one.** `base_scorer.py`'s `TIER_THRESHOLDS` is what scores; `config.yaml scoring.tiers` is documentation. Changing the config alone is a **no-op in production**. The other two are `normalization.json` `stats.raw_min` (which `tests/unit/test_normalization_invariant.py` requires to equal the tier threshold) and the expectation in `tests/unit/test_normalization_op_point.py`. **Any op-point move changes all four in one commit and refits normalization**, and `MAX_NORMALIZATION_RAW_MIN = 4.5` caps how high it can go (strict `>`, so 4.5 is accepted with zero margin; above that the production loader silently falls back to `score_scale_factor`). Both NM#161 and NM#205 were `raw_min` drifting off the threshold — the incidents with numbers are in `docs/NORMALIZATION_METHOD.md`. Verify by **executing** the tier assignment, not by re-reading the config. **A FIFTH place holds the same number and is NOT a tier boundary: NexusMind's `pipeline.enrichment.min_score` (`NexusMind/config/app.yaml`), which gates post-scoring enrichment at 4.0.** It is an independent constant that happens to share the value — moving a filter's op-point does **not** move it, and a filter whose distribution sits below 4.0 goes silently un-enriched (NM#319). Raising an op-point cannot starve it further; **lowering one, or shipping a filter that scores low, can.** ⚠️ **That gate reads the NORMALIZED score**, so a rescale cannot move a filter across it — a percentile CDF maps it straight back (`memory/solutions-v6-dimension-hypotheses.md` R3).

### Working rules — non-negotiable, not tips

**Full text, evidence and occurrence catalogue: `memory/working-rules.md`.** The
imperatives stay here because they are needed every session; the war stories moved
out on 2026-08-12 for the size budget. **Read the evidence before weakening any of
them** — each exists because something shipped broken.

- **Before shipping any gate, cap, threshold, config key or stamp — or comparing
  against an option, price or quota — name the caller that would load it, then
  PROVE THE OUTCOME CHANGED at the end of the run.** *(16th
  occurrence 2026-08-25 — the `investment_risk` pause shipped with a green suite and
  nobody watched a service start; a fail-closed deploy gate caught its THIRD file three
  hours later and cost a production cycle. 15th — #103 chose an oracle against a Gemini
  Batch rate card with no call site.)* An annotation, a test and a check are mechanisms too.
  Naming the caller is **not sufficient**: guards have shipped with correct callers
  on the right paths and still done nothing. A green test on the predicate proves
  only the predicate. Never infer runtime behaviour from a config key's presence.
  → **count and numbering: `memory/working-rules.md` (canonical)**; shape-by-shape
  evidence: `memory/gotcha-log.md` § *The unreachable-mechanism catalogue*.
- **A failing check may be the CONTROL WORKING — never "fix" it before asking what
  it proves.** *(⭐⭐ promoted 2026-08-15; the imperative did not arrive in this file
  until 2026-08-16.)* Before repairing a thing that is failing, dead or disabled,
  establish what its failure is currently buying you: 788/788 violations was the
  control firing, and the archive survived only because the purge was broken.
  → `memory/working-rules.md`.
- **`raw_weighted_average` is NOT always a model output — condition on `stage_used`
  first.** A `stage1_low` row's score is an **e5 probe estimate**, not a Gemma score
  (23% of rows measured). Same shape as the length-field trap: the field exists, is
  populated, and means different things per row.
- **Before using any source as evidence, establish what it EXCLUDES.** *(14th
  occurrence 2026-08-29 — a nine-surface correction announced as "finished properly" was
  still live in the AUTO-MEMORY: every sweep was rooted at the repo, and this project's
  always-loaded layer spans TWO trees. 13th
  occurrence 2026-08-28 — a 99.4% cache hit measured on a run that RE-SENT THE SAME
  ARTICLES, so it could not have returned a low one — the mirror, and the seductive
  half: a *positive* that carried no information; 12th 2026-08-28 — a corpus target
  measured over a census that INCLUDED the 22.1% the draw forbids; 11th
  2026-08-27 — a `git archive HEAD` baseline tree, which ships tracked files
  only, so every gitignored path read as a broken reference: 240 findings against a real
  1; 10th 2026-08-26 — a "do not trim, only surviving record" marker whose
  refuting files sat in its own directory, past a load truncation; 9th 2026-08-23
  — every adverse row on disk was a 300-char EXCERPT of a 620–28,905-char
  article, and a paid run against them was one command away.)* Applies to data, to nested
  structures, to prior work, to literature, to hosts, and to **time**. A wrong path
  and a dead field both read as zero, and the wrong one is the more exciting finding.
  ⚠️ **A window is part of a source.** If it is a denominator, a baseline, or a claim
  of absence — enumerate the source first. ⭐ **One root, and it covers the
  INSTRUMENT too: IT WAS POINTED SOMEWHERE THAT CANNOT PRODUCE A POSITIVE, SO THE
  NEGATIVE CARRIED NO INFORMATION. Before believing a negative, prove the instrument
  could have said yes** — and, since that is only the broken-instrument half, **also
  ask what would have made the "before" different**: an instrument can be sound, its
  number correct, and still not be a function of the thing under test.
- **Every measurement error this project has made was a HAND-BUILT POPULATION.**
  *(2026-08-12, across four repos.)* Prefer a population the pipeline already
  computes to one you construct. Make the missing case raise, never return `None`.
- **A parallel agent session may be in the same checkout, so no git verb may take
  the whole tree as its argument.** Never `git add -A`, bare `git stash`,
  `git checkout .`, `git clean`. Always pass explicit paths; `git status --porcelain`
  before committing and stage only what you recognise.
- **`pgrep -f "<pattern>"` cannot answer "is it running?" — and neither can
  `systemctl is-active <one-unit>`.** *(6th occurrence 2026-08-26 — the service
  manager answers for the unit you NAME: `nexusmind.service` read `inactive`
  while the **chained** `nexusmind-cleanup.service` ran the very code the deploy
  was replacing. 5th 2026-08-25 — a wait-loop matched ITSELF via its own echo and
  waited forever.)* **Enumerate the units, then ask all of them**
  (`systemctl list-units 'nexusmind*' --all`); `OnSuccess=`/`Requires=` chains are
  part of what "is it running?" means. `pgrep`/`pkill -f` additionally match the
  shell carrying the pattern — use `ps -eo pid,etime,args | grep -v grep` or the
  log's last timestamp. **If a process check decides whether you act, print the
  matching line before believing it.**

## Production Filters

Full details in `memory/filter-status.md`. Summary:

| Filter | Version | MAE | Status |
|--------|---------|-----|--------|
| **uplifting** | v7 | recall 0.61 / spec 0.97 | Deployed (NO_HUB, hybrid inference). **Op-point 4.5 since 2026-08-11 (#102)**. ⚠️ **Its consumer lens (Thriving) carries a NARROWER predicate than this scorer's name implies** — #107, scoped not reversed, and it **binds the v8 `human_thriving` prompt**. What the lens excludes, and why ADR-012's rename is load-bearing: `memory/filter-status.md` |
| **investment-risk** | v6 | recall 0.72 / spec 0.97 | **PAUSED 2026-08-25** (owner: Aegis is dormant), never an ovr.news lens. **PAUSED ≠ REMOVED** — package, Hub repo, Contract C and the archives all stay. ⛔ **Un-pause is THREE files, not two**: the third, a smoke-test fixture row, failed the deploy gate closed and cost a production cycle. Procedure, recovery command and the unit test that now guards it: `docs/decisions/2026-08-25-pause-investment-risk.md` |
| **cultural-discovery** | v5 | recall 0.59 / spec 0.98 | **LIVE.** v6's cutover failed on 2026-08-13 and was reverted, so v5 is still what scores |
| **cultural-discovery** | v6 | (v5's) | **NOT DEPLOYED** — fixed and verified offline (`dcf2860`), never redeployed. ⚠️ **v5 ALREADY runs two-stage**, so v6 does **not** introduce probe screening — it changes the probe and threshold. The failed cutover, the rollback and the probe numbers: `memory/filter-status.md`, `memory/cd-v6-probe-hypotheses.md` |
| **belonging** | v1 | recall 0.60 / spec 0.985 | Deployed (HF Hub) |
| **nature_recovery** | v4 | recall 0.65 / prec 0.85 | Deployed (recall-first probe, v5 planned #71) |
| **solutions** | v6 | recall 0.67 / spec 0.97 | **LIVE** — gate passed 2026-07-27, normalization fitted 2026-07-28 |
| **sustainability_technology** v3, **foresight** v1 | — | — | **BOTH REMOVED 2026-08-03**, merged into solutions (#43, closes #64); packages deleted, recover from git history |
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
- **Lens-aligned filter naming — the backlog is CLOSED, don't re-open it at a version bump.** Settled 2026-08-06: `cultural_discovery`, `nature_recovery` and `solutions` all keep their names; the only rename left is `uplifting` → **`human_thriving` at v8** (not bare `thriving`, an existing parked directory). Reasoning: `docs/adr/README.md`, ADR-012 as amended
- **Oracle consistency over data volume** — prompt precision predicts MAE better than dataset size; use belonging v1 as template (ADR-010)
- **Embedding screening for needle filters** — use Phase 3 positives as e5-small seeds to screen corpora; replaces keyword screening (ADR-011)
- **English lens names** — all lens/tab names in English, no Dutch (ADR-013)
- **Cross-filter percentile normalization** — non-linear mapping from production CDF; supersedes score_scale_factor (ADR-014)
- **Lenses as perspectives, not partitions** — overlap between lenses is correct; never exclude adjacent lens content in oracle prompts (ADR-015)
- **Drop tier assignments** — filters output pass/block + continuous score only; tiers add no value over the score itself (ADR-016)
- **Declarative prefilter shape** — extend `BasePreFilter` with `EXCLUSION_PATTERNS` / `OVERRIDE_KEYWORDS` / `POSITIVE_PATTERNS` / `POSITIVE_THRESHOLD` class attrs; standard `apply_filter()` pipeline lives on the base (ADR-018, #52). ⚠️ **Amended 2026-08-21: new filters ship NO per-lens prefilter** — keyword screening is Latin-script only; the multilingual e5 probe replaces it (ADR-011). Governs shape where one exists, not whether to have one
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

⛔ **A POINTER ROW IS CAPPED AT 250 CHARS AND A NEW LESSON GOES IN THE TARGET, NOT HERE
(#133).** This file refilled at **~486 bytes/day** while every audit trimmed it back to
the wall — a budget loses that race, a per-row cap cannot. State the trigger, name the
file, stop. ⚠️ **The carve-out is the honest part, not a loophole:** a pointer does not
fire without opening the target, so four rows whose prohibition prevents *spending money*
or *publishing a wrong number* may reach 400. Enforced, with the exemption list itself
bounded: `python3 scripts/verification/check_index_budget.py --target pointers`.

| When you're... | Read... |
|----------------|---------|
| Starting a new session | `memory/MEMORY.md` — project memory index, current work status |
| Resuming thriving v1 work | `memory/thriving-v1-scoring.md` — scoring status, resume commands, full pipeline |
| Starting calibration / scorer-training / oracle-prompt work | `memory/calibration-history.md` — Dead Ends section: which approaches are already known dead (#69) |
| **Touching a prefilter, or considering an enforcement flip** | **`memory/prefilter-length-floor-hypotheses.md`** — what each prefilter actually blocks (measured), and why a matching pass rate is **not** a safety argument. Then #93. |
| **A legal/compliance question, or the training-data source** | `docs/decisions/2026-08-05-tdm-opt-out-training-data.md` — ⚠️ **one carve-out is open**: the oracle ships article text to the vendor. It names the ovr.news companion register. |
| **Anything about the pipeline CONTRACTS — schemas, validators, what a row carries between repos** | **`docs/decisions/2026-08-14-contract-a-envelope.md`**, then **`docs/CONTRACTS_PLAN.md` § *Round 3*** + **`memory/stamp-contract-integrity.md`**. ⛔ **Never quote a Contract A version from here** — read it off a delivered row (`scripts/contracts/contract_a_smoke.py`). |
| **Asking what an article field IS, or where a blocked article went** | **`NexusMind/contracts/article-record.schema.json`** — prescriptive and composed. Human half `NexusMind/docs/ARTICLE_RECORD.md`; per-field answer **`NexusMind/docs/ARTICLE_RECORD_REGISTER.md`**. ⛔ **Never quote a field count — this table included**; every count is a WINDOW. Blocked: `docs/BLOCK_LEDGER_SPEC.md`. |
| **Adding a stamp / config key, or trusting a stamped field in an analysis** | **`memory/stamp-contract-integrity.md`** — the schemas check SHAPE only. ⛔ **Run `NexusMind/scripts/stamp_census.py` for population before quoting any stamped field.** |
| **Reading a number off NexusMind production data** | **`memory/nexusmind-data-sources.md`** — reconcile denominators before diffing two sources. ⛔ **`live_articles` is NOT the reader population** — legacy, off the build path, and nothing can reconverge it; use `getArticlesForBuild`. `weighted_average` there is NORMALIZED, not raw. |
| **Quoting any Google News number, or touching the GN population** | **`memory/google-news-corpus-hypotheses.md`** — ⛔ **Never oracle-re-score a GN row** (sub-300-char headline echoes), and **never match GN on a `gn_` key prefix** (feeds and items undercount by different factors). ⚠️ **Always name the fetcher** (NM#310). |
| **Touching normalization (fitting, debugging a score/tier that looks wrong, ovr ranking)** | **`docs/NORMALIZATION_METHOD.md`** — method and guards; ADR-014, playbook §6. ⚠️ `raw >= threshold` with `tier: low` is **expected, not a bug**. |
| **Reading a date, a recency boost, or anything about `published_date`** | **`memory/date-error-recency-boost-hypotheses.md`** — a flat **1.3× boost under 24h** means any date error landing inside 24h wins it, invisibly. |
| **Measuring anything near an operating point, or comparing two runs' scores** | **`memory/score-batch-shape-noise.md`** — #95, and the Hard Constraint above. |
| **Touching enrichment, or citing a pre/post-enrichment score delta** | **`memory/enrichment-delta-hypotheses.md`** — H-E1 RESOLVED. ⚠️ Condition on `stage_used` before reading `raw_weighted_average` as a model output. |
| **Changing a dimension WEIGHT, or calling any dimension "dead"** | **`memory/solutions-v6-dimension-hypotheses.md`** — ⛔ **A dimension's zero rate is base rate, not breakage.** Re-weighting measured inert. |
| **Quoting any #121 number, or building an opinion/editorial genre stamp** | **`memory/opinion-genre-hypotheses.md`** — the within-source control **dissolves it in 5 of 6 lenses**. ⛔ **#121's issue body uses a wrong op-point for `solutions`.** |
| **Touching cultural_discovery v6, or citing its probe numbers** | **`memory/cd-v6-probe-hypotheses.md`** — #98's confirmed / refuted / traps. ⚠️ **v6 cannot score at all** — no inference module, no `calibration.json`. |
| **Anything obituary/grief-related, or reading the junk-gate state** | `memory/project-obituary-detector.md` — enforcement is ON at v5@0.85; carryover, the two live v5 false negatives, and the four SSH verify assertions live here. |
| **Creating OR retraining ANY filter (START HERE)** | **`docs/FILTER_PLAYBOOK.md`** — the single source of truth: every compiled lesson plus the canonical reference (`nature_recovery v4`). Read before touching filter code. |
| Deploying to NexusMind or gpu-server | `docs/RUNBOOK.md` — deployment, training, scoring how-to |
| Training on GPU server | `memory/gpu-server.md` — venv, PYTHONPATH, HF_HUB_OFFLINE |
| Debugging model loading or PEFT issues | `memory/gemma3-model.md` — Auto mapping fix, key format details |
| Making architectural decisions | `docs/adr/README.md` — 22 settled ADRs (001–019, 021–023; 020 is a draft) |
| Checking priorities or planning work | `docs/TODO.md` and `docs/ROADMAP.md` |
| Understanding system design | `docs/ARCHITECTURE.md` |
| Reviewing work quality | `docs/checklists/` — architect, test, implement, QA gates |
| Stuck on tooling or infra | `memory/gotcha-log.md` — problem/fix archive |
| **About to weaken, delete or argue with a working rule** | **`memory/working-rules.md`** — the full text of each rule plus the evidence and occurrence catalogue behind it. Every one exists because something shipped broken. |
| **Touching corroboration, story-dedup, or any matching feature** | **`memory/corroboration-feature-hypotheses.md`** — confirmed, refuted and untested. ⚠️ **The threshold is NOT the lever.** |
| Planning across repos, or asking "what should I work on" | `memory/cross-repo-prioritization.md` — issue landscape, chains, and the two standing traps it names |
| Running anything long, or told "the GPU is free" | `memory/b650-gpu.md` — the non-production 3090 Ti. `ssh b650-gpu` works from the workstation, NOT from sadalsuud |
| Checking which lens/tab a filter feeds | `memory/ovr-lens-set-current.md` — current lens→filter→tab mapping |
| Writing docs for a deployed filter | `memory/filter-doc-standard.md` — the required documentation set |
| Building a filter on a DeepSeek oracle, or citing cultural_discovery v5 as a reference | `memory/cd-v5-reference-status.md` — why v5 is the DeepSeek-oracle reference example, and the ADR-020 methodology it demonstrates |
| Retraining uplifting, Thriving false positives (#125), or the junk gates | `memory/uplifting-v7-training.md`, `memory/uplifting-oracle-genre-hypotheses.md`, `memory/obituary-v4-hypotheses.md`, `memory/violence-promotion-v1-hypotheses.md` |
| **Wanting the whole chain in one place, or the live pipeline state** | **`veen-systems/pipeline-atlas`** — the four repos as one signal path plus an ops snapshot every 20 min, on Tailscale (`http://100.78.93.76:8099/`), not GitHub Pages. |
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

This project is a source project for [augmented-engineering](https://github.com/ducroq/augmented-engineering) — a proposition about what's new when engineers work with AI agents. When you find evidence for its four patterns (verification findings, context-architecture lessons, reproduce-don't-assess examples, LLM behavioural properties), file an issue there with the pattern name, quantified results, and which claims it supports.

---

*Last updated: 2026-08-29. **Framework: agent-ready-projects v1.36.1 — triaged through v1.36.1, 0 releases behind (checked 2026-08-29 against the REMOTE, not the clone).** The three user-global skills are **byte-identical to the v1.36.1 reference install, 0 differing lines** — diff against `.claude/skills/<name>/SKILL.md` at the tag, never against `templates/`, because there is no install-time transform. ⛔ **Never write "current" here** — upstream moved twice within hours of this line being written, and a state claim in an always-loaded file decays silently. ⛔ **A stamp bump requires the adopt items in the tree first** — ahead of its content it silences the check that would catch the gap. ⛔ **Do not name an upstream section's contents here** — this sentence named v1.26.1's while calling it *unreleased*; it shipped 2026-08-25. Read the changelog, don't quote it. ⚠️ **Do not re-add a self-referential size claim** ("cut to the size you see"): the 08-16 wording was falsified by the next edit to this file. Per-tag triage: `docs/decisions/framework-adoption-history.md`. Structural state, open decisions and every number that moves live in `docs/TODO.md` (top block) and the memory index — deliberately NOT restated here, because two hand-maintained copies of a number disagree the moment one is updated. Session records: the memory index.*

