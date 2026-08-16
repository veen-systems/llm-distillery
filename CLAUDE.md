---
stack: Python 3.12, PyTorch, Transformers, PEFT/LoRA
status: Production
repo: github.com/ducroq/llm-distillery
framework: agent-ready-projects v1.26.0
framework_reconciliation: |
  v1.25.1 + v1.26.0 triaged 2026-08-15: 3 adopt, 1 decline, 4 N/A, 2 in force.
  Per-release detail and the evidence: `docs/decisions/framework-adoption-history.md`.
  Releases before v1.25.1: `docs/decisions/framework-adoption-history.md`.
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

- **Oracle**: Gemini Flash 2.5; DeepSeek V4 Flash proven cheaper alternative (cd v5). Per-article pricing + scheduling levers: `memory/oracle-pricing-scheduling.md`.
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

- **A score is not a function of the article alone — there is a measured `|Δ| ≤ 0.16` noise floor under every comparison (#95, 2026-08-03).** Batch composition alone; it changes decisions, not just digits. **A run-to-run difference below ~0.1 near an op-point is indistinguishable from noise; never report one as an effect.** **Owner decision 2026-08-06: budget for the floor, don't try to remove it** — every metric at the threshold carries a band, and **two models whose bands overlap are NOT DISTINGUISHABLE** whatever their point estimates say. `scripts/gate/ground_truth_gate.py` prints it (`--noise-floor`, default 0.16). ⚠️ Cross-box skew is the same magnitude with a different cause — **never compare scores from different machines.** Flip rates, the run-seed mechanism, *replay is not stability*, and the corpus-wide share: `memory/score-batch-shape-noise.md`, `docs/FILTER_PLAYBOOK.md` §7.
- **A false positive costs a reader; a false negative costs nothing visible. Optimise SPECIFICITY, and NEVER rank filters on MAE (ADR-023, owner 2026-08-09).** Owner, verbatim: *"letting junk through is way worse than not catching positives. Junk kills readers; positives they don't know about don't hurt them."* **Precision and MAE are base-rate dependent — only recall and specificity are conditional on the true class and comparable across splits.** Report both, always with the split's positive rate. Consequences: **active-learning batches sample ABOVE the op-point** (where junk reaches readers), not below it (which hunts the cheap error); ties inside the #95 band go to specificity. **Does NOT apply to the Stage-1 e5 probe**, a recall-safe screen by design — there the FN is the expensive error, hence `train_probe.py --objective recall`. The retracted 2026-08-09 MAE ranking, why MAE is wrong twice over, and the ~27% composition arithmetic that stops the retraction being overstated: `memory/filter-status.md`.
- **Fit `calibration.json` after every training run.** Isotonic regression on the val set. Commit with the filter package. The base scorer auto-loads it.
- **`.nexusmind-owns` must stay empty.** Entries only with a tracked issue and a resolution deadline — the escape-hatch rationale and the 18-day normalization-drift incident are in the file's own header comment. `filters/common/filter_base_scorer.py` and `filters/common/hybrid_scorer.py` are pure shared math; sync freely.

- **An operating point lives in FOUR places, and `config.yaml` is NOT the runtime one.** `base_scorer.py`'s `TIER_THRESHOLDS` is what scores; `config.yaml scoring.tiers` is documentation. Changing the config alone is a **no-op in production**. The other two are `normalization.json` `stats.raw_min` (which `tests/unit/test_normalization_invariant.py` requires to equal the tier threshold) and the expectation in `tests/unit/test_normalization_op_point.py`. **Any op-point move changes all four in one commit and refits normalization**, and `MAX_NORMALIZATION_RAW_MIN = 4.5` caps how high it can go (strict `>`, so 4.5 is accepted with zero margin; above that the production loader silently falls back to `score_scale_factor`). Both NM#161 and NM#205 were `raw_min` drifting off the threshold — the incidents with numbers are in `docs/NORMALIZATION_METHOD.md`. Verify by **executing** the tier assignment, not by re-reading the config. **A FIFTH place holds the same number and is NOT a tier boundary: NexusMind's `pipeline.enrichment.min_score` (`config/app.yaml`), which gates post-scoring enrichment at 4.0.** It is an independent constant that happens to share the value — moving a filter's op-point does **not** move it, and a filter whose distribution sits below 4.0 goes silently un-enriched (NM#319). Raising an op-point cannot starve it further; **lowering one, or shipping a filter that scores low, can.** ⚠️ **That gate reads the NORMALIZED score**, so a rescale cannot move a filter across it — a percentile CDF maps it straight back (`memory/solutions-v6-dimension-hypotheses.md` R3).

### Working rules — non-negotiable, not tips

**Full text, evidence and occurrence catalogue: `memory/working-rules.md`.** The
imperatives stay here because they are needed every session; the war stories moved
out on 2026-08-12 for the size budget. **Read the evidence before weakening any of
them** — each exists because something shipped broken.

- **Before shipping any gate, cap, threshold, config key or stamp, name the caller
  that loads it — then PROVE THE OUTCOME CHANGED at the end of the run.** *(14th
  occurrence 2026-08-16 — a watcher I reported as armed and never started.)* An annotation, a test and a check are mechanisms too.
<!-- verify: WR=$(sed -n '/Before shipping any gate/,+2p' memory/working-rules.md | tr '\n' ' ' | tr -s ' ' | grep -oE '[0-9]+(st|nd|rd|th) occurrence' | grep -oE '^[0-9]+' | sort -n | tail -1); CM=$(sed -n '/Before shipping any gate/,+3p' CLAUDE.md | tr '\n' ' ' | tr -s ' ' | grep -oE '[0-9]+(st|nd|rd|th) occurrence' | grep -oE '^[0-9]+' | sort -n | tail -1); if [ -z "$WR" ]; then echo "CANNOT VERIFY: no ordinal in memory/working-rules.md"; elif [ -z "$CM" ]; then echo "CANNOT VERIFY: no ordinal in CLAUDE.md"; elif [ "$WR" = "$CM" ]; then echo "PASS ($CM)"; else echo "FAIL: CLAUDE.md says $CM, working-rules.md says $WR"; exit 1; fi -->
  Naming the caller is **not sufficient**: guards have shipped with correct callers
  on the right paths and still done nothing. A green test on the predicate proves
  only the predicate. Never infer runtime behaviour from a config key's presence.
  → `memory/gotcha-log.md` § *The unreachable-mechanism catalogue*.
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
- **Before using any source as evidence, establish what it EXCLUDES.** *(8th
  occurrence 2026-08-16 — a population whose window was the same length as the
  mechanism's period, so it could only ever return zero.)* Applies to data, to nested
  structures, to prior work, to literature, to hosts, and to **time**. A wrong path
  and a dead field both read as zero, and the wrong one is the more exciting finding.
  ⚠️ **A window is part of a source.** If it is a denominator, a baseline, or a claim
  of absence — enumerate the source first. ⭐ **One root, and it covers the
  INSTRUMENT too: IT WAS POINTED SOMEWHERE THAT CANNOT PRODUCE A POSITIVE, SO THE
  NEGATIVE CARRIED NO INFORMATION. Before believing a negative, prove the instrument
  could have said yes** — and, since that is only the broken-instrument half, **also
  ask what would have made the "before" different**: an instrument can be sound, its
  number correct, and still not be a function of the thing under test.
<!-- verify: WR=$(grep -i 'establish what it excludes' memory/working-rules.md | grep -oE '[0-9]+(st|nd|rd|th) occurrence' | head -1 | grep -oE '^[0-9]+'); CM=$(grep -A1 'establish what it EXCLUDES' CLAUDE.md | grep -oE '[0-9]+(st|nd|rd|th)' | head -1 | grep -oE '^[0-9]+'); if [ -z "$WR" ] || [ -z "$CM" ]; then echo "CANNOT VERIFY: ordinal not extracted (WR='$WR' CM='$CM')"; elif [ "$WR" = "$CM" ]; then echo "PASS ($CM)"; else echo "FAIL: CLAUDE.md says $CM, working-rules.md says $WR"; exit 1; fi -->
- **Every measurement error this project has made was a HAND-BUILT POPULATION.**
  *(2026-08-12, across four repos.)* Prefer a population the pipeline already
  computes to one you construct. Make the missing case raise, never return `None`.
- **A parallel agent session may be in the same checkout, so no git verb may take
  the whole tree as its argument.** Never `git add -A`, bare `git stash`,
  `git checkout .`, `git clean`. Always pass explicit paths; `git status --porcelain`
  before committing and stage only what you recognise.
- **`pgrep -f "<pattern>"` cannot answer "is it running?"** *(3rd occurrence.)* It
  matches the shell carrying the pattern. Use `ps -eo pid,etime,args | grep -v grep`,
  `systemctl is-active`, or the log's last timestamp. If a process check decides
  whether you act, print the matching line before believing it.

## Production Filters

Full details in `memory/filter-status.md`. Summary:

| Filter | Version | MAE | Status |
|--------|---------|-----|--------|
| **uplifting** | v7 | recall 0.61 / spec 0.97 | Deployed (NO_HUB, hybrid inference). **Op-point 4.5 since 2026-08-11 (#102)**. ⚠️ **Its consumer lens (Thriving) now carries a NARROWER predicate than this scorer's name implies** — ovr.news `BRAND.md` `a70609b`, 2026-08-13: *a process going well **for people***, excluding harm-answered-only and institution-beneficiary. #107 is scoped, not reversed: the scorer is faithfully serving a definition ovr did not publish. Binds the **v8 `human_thriving`** prompt (ADR-012's rename is now load-bearing, not hygiene) |
| **sustainability_technology** | v3 | 0.72 | **REMOVED 2026-08-03** — replaced by solutions; package deleted, recover from git history |
| **investment-risk** | v6 | recall 0.72 / spec 0.97 | Deployed (HF Hub, private). **Op-point 4.25 since 2026-08-11** |
| **cultural-discovery** | v5 | recall 0.59 / spec 0.98 | **LIVE.** v6's cutover failed on 2026-08-13 and was reverted, so v5 is still what scores |
| **cultural-discovery** | v6 | (v5's) | **NOT DEPLOYED** — fixed and verified offline (`dcf2860`), never redeployed. ⚠️ **v5 ALREADY runs two-stage**: `filter_loader.py:148` sets `hybrid_class` from the PRESENCE of `inference_hybrid.py`, not from `config.yaml`, so v6 does **not** introduce probe screening — it changes the probe and threshold. The failed cutover, the rollback move and the probe numbers: `memory/filter-status.md`, `memory/cd-v6-probe-hypotheses.md` |
<!-- verify: CM=$(grep -c 'cultural-discovery\*\* | v6 | (v5.s) | \*\*NOT DEPLOYED\*\*' CLAUDE.md); FS=$(grep -c 'CUTOVER ATTEMPTED, FAILED AND REVERTED' memory/filter-status.md); if [ "$CM" = 1 ] && [ "$FS" = 1 ]; then echo "PASS (both layers say v6 is not deployed)"; else echo "FAIL: CLAUDE.md not-deployed row=$CM, filter-status.md reverted marker=$FS — the two layers disagreed on this once already (2026-08-13 to 08-16)"; exit 1; fi -->
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
- **Lens-aligned filter naming — the backlog is CLOSED, don't re-open it at a version bump.** Settled 2026-08-06: `cultural_discovery`, `nature_recovery` and `solutions` all keep their names; the only rename left is `uplifting` → **`human_thriving` at v8** (not bare `thriving`, an existing parked directory). Reasoning: `docs/adr/README.md`, ADR-012 as amended
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
| **Anything about the pipeline CONTRACTS — schemas, validators, what a row carries between repos** | **`docs/decisions/2026-08-14-contract-a-envelope.md`**, then **`docs/CONTRACTS_PLAN.md` § *Round 3*** + **`memory/stamp-contract-integrity.md` § *The contracts layer***. ⛔ **Never quote a Contract A version from this file** — it moves several times a week; read it off a delivered row (`scripts/contracts/contract_a_smoke.py`). ⛔ **Do NOT quote "four validators"** — counting them was the wrong question. ⚠️ Read the traps before quoting any number: the validator counts **errors, not rows**; `format` is declared and never asserted; don't grep bare field names; a `grep -rIl` that prints nothing is a **broken verify command**. |
| **Adding a stamp / config key, or trusting a stamped field in an analysis** | **`memory/stamp-contract-integrity.md`** — the schemas check SHAPE only and are permissive. ⛔ **Run `NexusMind/scripts/stamp_census.py` for population + consumers before quoting any stamped field** — a stamp can be computed on every row and lost before persistence. |
| **Reading a number off NexusMind production data** | **`memory/nexusmind-data-sources.md`** — reconcile denominators before diffing two sources: `filtered_*.jsonl` also drops source-type-excluded rows, `data/raw/` is pre-enrichment. ⛔ **`live_articles` is NOT the reader population** *(corrected 2026-08-16 — this row asserted it was)*: legacy, off the build path, and drifted from its own source with **no code path that can reconverge them**. Use `getArticlesForBuild`, or the `articles` table as a superset. `weighted_average` there is NORMALIZED, not raw. |
| **Quoting any Google News number, or touching the GN population** | **`memory/google-news-corpus-hypotheses.md`** — ⛔ **Never oracle-re-score a GN row** (they are sub-300-char headline echoes), and **never match GN on a `gn_` key prefix**: it is a strict subset, and feeds, rows and items each undercount by a different factor, so a row-share sanity check reads as roughly-right while the feed population is off five-fold. ⚠️ **Always name the fetcher** — ovr.news resolves these URLs, NexusMind cannot (NM#310). Five claims are already REFUTED there, four of them denominator errors. |
| **Touching normalization (fitting, debugging a score/tier that looks wrong, ovr ranking)** | **`docs/NORMALIZATION_METHOD.md`** — canonical method, guards, reproduction steps; ADR-014 for the decision, `docs/FILTER_PLAYBOOK.md` §6 for the digest. ⚠️ Normalization exists only for ovr.news cross-lens ranking, and tier is reassigned on the *normalized* score by design — so `raw >= threshold` + `tier: low` is **expected**, not a bug. Fit at `raw >= the filter's tier threshold`. |
| **Reading a date, a recency boost, or anything about `published_date`** | **`memory/date-error-recency-boost-hypotheses.md`** — a flat **1.3× boost under 24h** means *any* date error landing a row inside 24h wins it, invisibly. Both hypotheses RESOLVED. ⚠️ **`collected_date − published_date` is NOT a fabrication instrument without a `source` breakdown** — a fixed-publication-moment source (arXiv) walks with the collection timer and impersonates the `now − 2h` signature once per daily cycle. |
| **Measuring anything near an operating point, or comparing two runs' scores** | **`memory/score-batch-shape-noise.md`** — #95, and the Hard Constraint above. |
| **Touching enrichment, or citing a pre/post-enrichment score delta** | **`memory/enrichment-delta-hypotheses.md`** — H-E1 RESOLVED: enrichment's dominant effect is on **evidence-quality-type dimensions**, and a filter without one gains nothing. `nature_recovery`'s flat aggregate is a *cancellation*, not inertness. Also: condition on `stage_used` before reading `raw_weighted_average` as a model output. |
| **Changing a dimension WEIGHT, or calling any dimension "dead"** | **`memory/solutions-v6-dimension-hypotheses.md`** — ⛔ **A dimension's zero rate is base rate, not breakage**: `solutions v6`'s `community_practice_strength` is zero on 83% of on-topic articles and has the *highest* conditional correlation of the seven. Re-weighting measured inert, and its apparent gain at an absolute threshold is an **artifact** — a percentile CDF removes any monotone rescale. |
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
| **About to weaken, delete or argue with a working rule** | **`memory/working-rules.md`** — the full text of each rule plus the evidence and occurrence catalogue behind it. Every one exists because something shipped broken. |
| **Touching corroboration, story-dedup, or any matching feature** | **`memory/corroboration-feature-hypotheses.md`** — what is confirmed, refuted and untested. ⚠️ **The threshold is NOT the lever.** Shared-number features are refuted; time is confirmed and still switched off. |
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

This project is a source project for [augmented-engineering](https://github.com/ducroq/augmented-engineering) — a proposition about what's new when engineers work with AI agents. When you find evidence for its four patterns (verification findings, context-architecture lessons, reproduce-don't-assess examples, LLM behavioural properties), file an issue there with the pattern name, quantified results, and which claims it supports.

---

*Last updated: 2026-08-16. **Framework: agent-ready-projects v1.26.0** — the latest TAG. Upstream's CHANGELOG also carries a `v1.26.1 (candidate, unreleased)` section, and its content is the `review-changes` baseline fix from `e824212`, already ported here, so this repo is current rather than behind. Triage detail: `docs/decisions/framework-adoption-history.md`. Structural state, open decisions and every number that moves live in `docs/TODO.md` (top block) and the memory index — deliberately NOT restated here, because two hand-maintained copies of a number disagree the moment one is updated. **`/audit-context` 2026-08-16 cut this file from 39,177 to the size you see and moved the evidence to topic files; the imperatives stayed.** Session records: `memory/project_session_2026_08_16.md` and the files it links.*

<!-- verify: FM=$(grep -m1 -oE '^framework: agent-ready-projects v[0-9.]+' CLAUDE.md | grep -oE 'v[0-9.]+'); FT=$(grep -m1 -oE 'Framework: agent-ready-projects v[0-9.]+' CLAUDE.md | grep -oE 'v[0-9.]+'); if [ -z "$FM" ]; then echo "CANNOT VERIFY: no frontmatter framework stamp"; elif [ -z "$FT" ]; then echo "CANNOT VERIFY: no footer framework stamp"; elif [ "$FM" = "$FT" ]; then echo "PASS ($FM)"; else echo "FAIL: frontmatter $FM, footer $FT"; fi -->
