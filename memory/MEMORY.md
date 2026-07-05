# LLM Distillery — Memory Index

Loaded every session. Topic files loaded on demand via triggers below.

## Topic Files

| File | When to load | Key insight |
|------|-------------|-------------|
| `gemma3-model.md` | Model loading, PEFT, or Hub upload issues | Auto mapping fix, OLD vs NEW key format, torch float16 |
| `gpu-server.md` | Training on GPU or deploying to gpu-server | HF_HUB_OFFLINE, scp not rsync, venv path, PYTHONPATH |
| `filter-status.md` | Checking filter versions, MAE, or hybrid probe stats | Per-filter deployment status and in-dev blockers |
| `gotcha-log.md` | Stuck on infra, tooling, or something weird | Problem → Root cause → Fix archive |
| `thriving-v1-scoring.md` | Understanding thriving v1 attempts | PAUSED — bimodal distribution, MAE 0.94, findings and open questions |
| `uplifting-v7-training.md` | Understanding thriving v1 history | v7 prompt evolution → thriving v1 rename (ADR-012) |
| `calibration-history.md` | Starting any calibration / scorer-training / oracle-prompt experiment | Dead Ends section: which approaches are already known dead — don't retry (#69) |
| `oracle-pricing-scheduling.md` | Planning any oracle batch scoring run | DeepSeek V4 peak/valley pricing — run batches off-peak (avoid 08:00–12:00 CEST) for 2x savings |
| `feedback-oracle-selection-criteria.md` | Picking an oracle for a new filter | Multi-oracle calibration + agent judging on a disagreement set (ADR-020 method); don't default to one |
| `feedback-conservative-oracle-better.md` | Choosing/tuning an oracle with penalty flags | Prefer the oracle that under-fires penalties; conservativism > raw consensus |
| `feedback-oracle-not-ground-truth.md` | High-MAE dimension, or optimizing student | Oracle is a consistent labeler, not truth — suspect label noise first, fix the prompt |
| `cd-v5-reference-status.md` | DeepSeek-oracle or ADR-020 methodology questions | cd v5 = reference example; solutions v4 = the validation case |
| `filter-doc-standard.md` | Documenting a new/deployed filter | belonging v1's 7-file core + cd v5's 2 optional extensions |
| `ovr-lens-set-current.md` | Which filter powers which ovr.news tab | Lens→filter mapping; authoritative tab config lives in ovr.news |

## Universal Gotchas

- **Gemma-3 Auto mapping**: `AutoModelForSequenceClassification` doesn't support `gemma3_text`. Always use `load_base_model_for_seq_cls()`. See `gemma3-model.md`.
- **PEFT adapter format**: Keep OLD format for Hub. Never run `resave_adapter.py`. See `gemma3-model.md`.
- **PYTHONPATH**: Always set `PYTHONPATH=.` when running scripts that import `filters.*`.
- **scp not rsync**: rsync fails with dup() errors on gpu-server.
- **Windows safetensors**: Can't write to memory-mapped file. Save to temp, then `os.replace()`.
- **Training data dir naming**: Hyphens preserved: `cultural-discovery_v3`. Check actual dir names before scripting.
- **Config format variation**: `tiers:` (uplifting, cultural-discovery, investment-risk v6) vs `tier_thresholds:` (sustainability_tech v5).
- **Hyphenated filter imports**: Use `importlib.import_module()` — Python can't import hyphens.
- **Git Bash path mangling**: Set `MSYS_NO_PATHCONV=1` before any command that passes Unix paths as arguments.

## Key File Paths

| Path | Purpose |
|------|---------|
| `filters/common/model_loading.py` | Gemma-3 model loading + LoRA utilities |
| `filters/common/filter_base_scorer.py` | Base class for all filter scorers |
| `filters/common/score_calibration.py` | Isotonic calibration fit/apply |
| `filters/common/embedding_stage.py` | e5-small probe for hybrid inference |
| `filters/common/hybrid_scorer.py` | Two-stage hybrid inference orchestrator |
| `filters/common/base_prefilter.py` | Base prefilter with commerce detection |
| `ground_truth/batch_scorer.py` | Oracle scoring pipeline |
| `training/train.py` | Model training pipeline |
| `training/prepare_data.py` | Training data preparation |
| `scripts/calibration/fit_calibration.py` | Isotonic calibration fitting |
| `scripts/deployment/upload_to_huggingface.py` | Hub upload + verification |
| `ground_truth/__init__.py` | `analysis_field_name()` — shared convention for scored JSONL keys |
| `scripts/screening/embedding_screener.py` | ADR-011: embedding similarity screener for needle filters |
| `scripts/oracle/average_oracle_runs.py` | Multi-run oracle score averaging |
| `filters/common/score_normalization.py` | Cross-filter percentile normalization (ADR-014) |
| `scripts/normalization/fit_normalization.py` | Fit normalization CDF from production data |
| `docs/adr/README.md` | ADR index (001-019) |
| `filters/common/obit_signal.py` | Hoisted regex obit probe — used by belonging v1 prefilter and NexusMind#199 cross-lens leak measurement |

## Cross-Project: NexusMind

- NexusMind's `src/filters/filter_loader.py` auto-discovers from `filters/` directory
- NexusMind's output includes `nexus_mind_attributes` — downstream apps (ovr.news, dashboard, Aegis) depend on field names. Don't rename fields.
- gpu-server runs NexusMind scorer at `~/NexusMind/filters/` (dirs use **underscore** names: `cultural_discovery`, `investment_risk`, …). Deploy new filters with `scp`.
- **`nexusmind-scorer.service` is a `static`, on-demand unit** (FastAPI :8000) — spun up per scoring run in the chain **FluxusSource harvest (sadalsuud) → NexusMind pipeline (sadalsuud) → gpu-server scorer → exits**. **Inactive between runs is the normal resting state, NOT an outage.** A *real* fault shows `Result≠success` (a clean stop is `Result=success`, `NRestarts=0`). Known eviction failure mode: Ollama/vmodel-daemon grabs the GPU via `Conflicts=` (NexusMind#250). Authoritative details: `FluxusSource/memory/nexusmind.md`. **Do not curl `localhost:8000/health` as a health check — it only answers mid-run.**
- Filter changes should be deployed to both gpu-server and sadalsuud.

## Deployment Targets

- **gpu-server**: `~/NexusMind/filters/` — uses `investment_risk` (underscore, not hyphen)
- **sadalsuud**: `~/local_dev/NexusMind/filters/` — Hub inference (no local model/ needed), venv at `~/local_dev/NexusMind/venv/`
- Deploy config changes to both servers after calibration or config updates

## Experiments

- **Quantization (#24)**: Naive PyTorch INT8 rejected — 2.6x faster but MAE +0.63. FP16 produces NaN on CPU. Next: ONNX Runtime or smaller base models. See `docs/experiments/quantization-benchmark-2026-03-07.md`.
- Benchmark script: `scripts/experiments/quantization_benchmark.py` (reusable for any filter)

## Recently Promoted

<!-- Gotchas promoted to topic files or the project file.
     Format: "if [situation], then [what to do] — promoted from gotcha-log YYYY-MM-DD"
     Retire entries once they appear in their destination. -->

- if [landing a non-trivial migration or refactor], then [fire code-reviewer + refactoring-guide + security-auditor in parallel before considering it shipped — they have non-overlapping blind spots] — promoted from gotcha-log 2026-04-29
- if [a regex correctness bug is found], then [audit siblings in the same file/author-style — same-shape bugs cluster] — promoted from gotcha-log 2026-04-29 (recurrence of #45 RIP issue → today's multilingual sweep)
- if [writing or auditing a deploy/sync script that runs `git add` (or rsync-then-commit) against a directory it doesn't fully own], then [require fail-closed dirty-check + explicit path staging; blanket `git add -A` is a latent origin-contamination bug that fires on the first multi-author day] — promoted from gotcha-log 2026-05-23

## Active Decisions

<!-- One-liners about recent architectural choices, pointing to ADRs.
     If a decision lives here for more than one session without a formal ADR, create one. -->

- English-only lens/tab names — ADR-013 (2026-03-28)
- Lens-aligned filter naming at version bumps — ADR-012
- Cross-filter percentile normalization, supersedes score_scale_factor — ADR-014 (2026-03-30)
- Thriving v1 paused, bimodal distribution problem — uplifting v6 stays (2026-03-30)
- Declarative prefilter shape via BasePreFilter extension — ADR-018 (2026-04-28). Per-filter migration COMPLETE 2026-04-29 (#52, all 7 production filters); review-battery follow-ups also landed (RIP guard repair, POSITIVE_PATTERNS shadow rename, CD v4 truncation, uplifting v7 multilingual `\b` boundary sweep, investment-risk cleanups, CD v4 colonial tightening, `_check_domain_exclusions` hoist, `_pre_exclusion_check` hook). Class-name drift cleanup (sustech V2→V3, NR V1→V2) and per-category exception extension to `_is_excluded` (potential ADR-019) deferred — see `docs/TODO.md` "Post-#52 Review-Battery Followups".
- Cross-repo cleavage rule, post-2026-05-04 manifest-as-anti-pattern incident — production-runtime concerns live in NexusMind wrappers (composition over inheritance), shared math lives in `filters/common/`, `.nexusmind-owns` manifest is the escape hatch (empty by default; entries require tracked issue + deadline). See `memory/gotcha-log.md` "Manifest as Anti-Pattern" entry + closure note for the full lesson and the cross-repo coordination shape that worked.
- Per-category exclusion overrides via Template Method — ADR-019 (2026-05-05). `BasePreFilter` extended with `CATEGORY_OVERRIDES: Dict[str, CategoryOverrideCfg]` (TypedDict-typed) + `_compound_override_applies()` hook. Subclasses override the narrow hook; base owns the fallback chain (compound → dict → global `_has_override`). **First migration shipped 2026-05-22**: belonging v1 hook-only consolidation (commits `ba6b7cb` + `c1ebc98`). Path to fully-declarative for the remaining 4 filters is now scoped under #66 (base `EXCLUSION_REASON_PREFIX` attr + move domain checks into `_pre_exclusion_check`). <!-- verify: grep -q 'CATEGORY_OVERRIDES' filters/common/base_prefilter.py && grep -q '_compound_override_applies' filters/common/base_prefilter.py && grep -q '_compound_override_applies' filters/belonging/v1/prefilter.py && echo PASS || echo FAIL -->
- HF Hub model-card license consistency — fixed 2026-05-22 (#65, commits `fb67d05` + `41d2108`). Source-side template patched (`upload_to_huggingface.py:28` declares `eupl-1.2`); all 14 `jeergrvgreg/*` Hub repos relicensed in place via one-shot script. Repo LICENSE + pyproject + upload template + 14 Hub model cards all carry EUPL-1.2 consistently. <!-- verify: grep -q "license: eupl-1.2" scripts/deployment/upload_to_huggingface.py && echo PASS || echo FAIL -->
- Deploy-script hardening — fail-closed defaults for `deploy_to_nexusmind.{sh,ps1}` (2026-05-23, commits `4cf75dd` + `dd11727`). Refuse-on-dirty pre-flight check + `--force-dirty`/`-ForceDirty` escape hatch; explicit `git add $FILTER_PATH filters/common/` replaces blanket `git add -A`. Closes origin-contamination hazard from 2026-05-22 incident. Printed server-pull instructions also corrected to match real deploy flow (sadalsuud at `~/local_dev/NexusMind` + gpu-server via `deploy_filters.sh` from sadalsuud, no git pull). <!-- verify: grep -q "FORCE_DIRTY" scripts/deploy_to_nexusmind.sh && grep -q 'git add "\$FILTER_PATH" filters/common/' scripts/deploy_to_nexusmind.sh && echo PASS || echo FAIL -->
- Solutions broadening v4 DRAFT scaffolded — `filters/sustainability_technology/v4/` (2026-05-05). Forks signed off: C (broaden ST v3 in place), combine ST v3 + foresight v1 corpora, foresight retired when v4 supersedes ST v3. 7 dims, weight=1.00, calibration batch spec inline (300 articles, ~$0.30). Awaiting prompt drafting before any oracle spend. <!-- verify: test -f filters/sustainability_technology/v4/config.yaml && echo PASS || echo FAIL -->
- cultural_discovery v5 DEPLOYED 2026-05-31 — resolves #62 discovery-lens leakage. Val MAE 0.697 (v4 was 0.74). Soft-penalty F/G/H/I/K flags (historical_harm_reckoning, commemoration_memorial, perpetrator_biography, decline_loss, launch_announcement). DeepSeek V4 Flash oracle (first non-Gemini lineage in production, ~7x cheaper). End-to-end verified: Pope apology 9.65→2.31, Indus/Sumer 9.12 (gradient preserved). v4 deleted from gpu-server post-verification; still in llm-distillery + git + HF Hub for rollback. **Provisional reference example for ADR-020 methodology** (multi-oracle batch + agent judging) and DeepSeek-as-default-oracle; solutions v4 is the validation case. <!-- verify: ssh gpu-server 'test -d ~/NexusMind/filters/cultural_discovery/v5/model' && echo PASS || echo FAIL -->

## Last Session Recap (2026-07-04)

Light hygiene session — no code or filter changes. Memory correction + issue triage + framework adoption.

- **DeepSeek V4 peak/valley pricing** (email 2026-07-04). Mid-July 2026 pricing introduces 2x peak surcharge (peak UTC 01:00–04:00 + 06:00–10:00 = 08:00–12:00 CEST is the trap). Rule: run oracle batches off-peak (noon–midnight CEST). New reference memory `oracle-pricing-scheduling.md`; solutions v4 pickup annotated. Commit `7f5ee4a`.
- **gpu-server scorer architecture correction.** Chased a phantom "scorer down" alarm — it was stale memory, not an outage. `nexusmind-scorer.service` is a `static`, **on-demand** unit fired per run in the FluxusSource → NexusMind (sadalsuud) → gpu-server chain; inactive-between-runs is normal. Confirmed via `FluxusSource/memory/nexusmind.md` + `systemctl show` (`Result=success`). Fixed MEMORY.md prose + replaced two curl-`localhost:8000/health` verify snippets with disk-based checks. New gotcha logged. Commit `ca23efa`.
- **Issue triage** (24 → 22 open). Closed **#39** (dup of #23) and **#53** (hyphen/underscore divergence — resolved on disk to underscore-only + NexusMind `filter_loader` now enforces underscore-only per their ADR-019). Re-scoped **#23** (cd `evidence_quality` 1.31 → ~0.90 in v5, cliff removed via ADR-015 soft-penalty) to a v6 target, and **#52** (residual = class-name drift `sustech/v3`→PreFilterV2 + `NR/v2`→PreFilterV1, + #66 fully-declarative remainder).
- **Framework adoption v1.9.0 → v1.10.4.** Bumped `CLAUDE.md` pin; added the v1.10.0 session-start drift-check row to Before You Start (the change we were missing — which is *why* the drift went unnoticed). curate skill already carried v1.10.0 Step-0 sub-steps 6/7. v1.10.1–v1.10.4 are docs/maintainer-only, no adopter action. Optional not-yet-adopted: `hypothesis-log.md` pattern (v1.10.0).

**Freshness flags raised (not yet fixed):**
- ~~The 2026-05-31 recap claimed "6 new memory entries" that never existed on disk.~~ **RESOLVED 2026-07-05**: verified absent everywhere (repo + user-level), then reconstructed all 6 from the recap description + verifiable repo content (ADR-020 draft, CLAUDE.md, ADR-010/012/013/015). Recap claim corrected; index pointers added; `[[cd-v5-reference-status]]` link now resolves. Each file carries a reconstruction note.
- MEMORY.md recap is a **month behind git** — the June obituary_detector v3 work (#51, commits `87e9962`/`9692bcb`/`dd9c3c4`) has no recap entry here.

## Session Recap (2026-05-31)

Shipped cultural_discovery v5 to production — closes the cd v5 retrain arc (started 2026-05-29). #62 leakage resolved end-to-end: Pope apology 9.65 → 2.31, Indus/Sumer trade discovery 9.12 (gradient preserved). Filter is live on gpu-server scorer, ovr.news Discovery tab picks it up on next pipeline cycle.

- **Oracle pick + 8K batch labeling**. Chose DeepSeek V4 Flash over Gemini after multi-oracle calibration (4 oracles: Gemini Flash 2.5, DeepSeek V4 Flash, Qwen3:14b, Phi4:14b) + Opus/Haiku agent judging on 30-article disagreement set. DeepSeek won 80.8% vs Gemini 19.2%; conservative-oracle principle (under-firing better than over-firing on penalty flags) locked in. Re-scored full 8,029 v4-prompt corpus + merged with 522 calibration cohort → **8,551 training records** at `datasets/scored/cd_v5_deepseek_merged_for_training.jsonl`. Actual cost $10.36, 14% cache hit rate. First non-Gemini lineage in production.
- **Training**. Gemma-3-1B + LoRA on gpu-server. Val MAE 0.834 → 0.736 → **0.697** across 3 epochs (better than v4's 0.74). Hyperparams unchanged from v4 (3 epochs, batch 8, lr 2e-5, head+tail 256+256).
- **Calibration + Hub + NexusMind deploy**. Isotonic regression per dim → `calibration.json` + `score_scale_factor` 1.2829. Hub upload `jeergrvgreg/cultural-discovery-filter-v5` (private). Deploy chain: llm-distillery `6acd013` → HF Hub → NexusMind `f9a3fe9` → sadalsuud → gpu-server. v4 deleted from gpu-server post-verification (provably picked v5 via `_find_latest_version()` + actual response `filter_version: "5.0"`); still recoverable from llm-distillery + git + HF Hub.
- **End-to-end verification** (addressed "things have gone badly wrong before"). Triggered actual `/score` requests on gpu-server: Pope apology (9.65 under v4) → **2.31** (F penalty fires, demoted below 4.5 threshold), Indus/Sumer trade discovery → **9.12** (no penalty, tier "high"). Health endpoint confirms `cultural_discovery_v5.0` loaded.
- **Documentation standard locked in** (`memory: filter-doc-standard.md`). Belonging v1's 7-file core (config + prompt + prefilter + STATUS + DEEP_ROOTS + README + README_MODEL) is the project standard from 2026-05-31. cd v5 adds 2 optional extensions for complex calibrations: `calibration_report.md` + `dimension_analysis/`.
- **6 memory entries described here were never committed in the 2026-05-31 session** (`filter-doc-standard.md`, `feedback-conservative-oracle-better.md`, `feedback-oracle-not-ground-truth.md`, `feedback-oracle-selection-criteria.md`, `ovr-lens-set-current.md`, `cd-v5-reference-status.md`) — the recap over-claimed. **Reconstructed 2026-07-05** from this description + verifiable repo content (see each file's reconstruction note). ADR-020 DRAFT (`docs/adr/draft-020-extended-oracle-calibration.md`) *does* exist and is marked PROVISIONAL pending solutions v4 validation.
- **2 new gotchas** (see `memory/gotcha-log.md`): "deploy_filters.sh rsync Excludes model/ Subdir" + "Hub Upload Fails on Missing per-Dim description Field". Both surfaced during cd v5 deploy; both have a clear fix path for next filter cycle.

Cost this session: ~$10.50 (DeepSeek 8K labeling ~$10.36 + Gemini calibration ~$0.10). v4 → v5 development total: ~$11 (vs v4's ~$25 under Gemini, validating DeepSeek economics).

## Previous Session Recap (2026-05-29 / 30)

Took ducroq/llm-distillery#62 (cultural_discovery v5 hard-negatives) from issue body to oracle-labeled cohort + drafted v5 prompt, ready for tomorrow's gpu-server training.

- **Hard-negative cohort built** at `datasets/raw/cd_v5_hard_negatives_candidates.jsonl` (gitignored). Sourced from sadalsuud `editorial_decisions` table (gemma3:27b in audit-only mode) — 1,376 cultural_discovery rejects since 2026-04-01 bucketed via regex over gate-reason text. After reviewer battery audits + dedup + two backfill passes: **49 articles across 5 buckets** (perpetrator_biography 5, historical_harm_reckoning 16, commemoration_memorial 9, demographic_decline 7, launch_announcement 12). Pure death/grief bucket (originally 8 articles) dropped mid-session because that shape is owned by the universal obit detector (`filters/common/obit_signal.py` today; trained detector per llm-distillery#51).
- **Multi-agent review battery on the candidate cohort** (dataset-qa + data-analyzer + general-purpose, parallel). Non-overlapping findings: structural integrity OK; slavery-topic lock-in in historical_harm bucket (37% slavery → reduced via dedup); 4 Mengele near-duplicate articles in perpetrator_biography (67% → 33% after dedup); 3 confirmed false positives (Estonian peasants ethnographic discovery, 2 anthropologist obits mis-flagged by the gate); 1 reclassification (Modigliani restitution: perpetrator_biography → historical_harm_reckoning). #62's explicit AK-47/weapons-designer gap filled by `mexican_el_financiero` Kalashnikov article.
- **v5 oracle prompt drafted** at `filters/cultural_discovery/v5/prompt-compressed.md` (config at `filters/cultural_discovery/v5/config.yaml`, version 5.0-draft). Five new pre-classification flags F, G, H, I, K. J (death/grief) intentionally omitted per universal-detector-framing rule. New KEY PRINCIPLE block (TRAJECTORY OVER VOCABULARY). 7 new contrastive examples (#13–#19) covering Pope apology, UN slavery vote, Mauthausen commemoration, AK-47 designer, Japan demographic shrinking, festival announcement, Nazi-looted Modigliani restitution (NOT capped). HARD ARITHMETIC RULE for cap enforcement added in scoring-rules section.
- **Two calibration passes on a 10-then-9 article stratified sample**. Run_01 found (a) the v4-style "soft cap" doesn't enforce arithmetically — 6/6 cap tests overshot by 0.18–1.62; (b) F carve-out parsed too narrowly — Modigliani-style wartime restitution mis-classified as historical_harm_reckoning. Run_02 after prompt fixes: 4/5 caps now pass on wavg, Modigliani correctly cultural_discovery (wavg 6.28), both positive controls stable (8.50, 7.38). `evidence_quality` still resists clamping on objectively well-sourced articles (~0.18 wavg slack worst case). Pragmatic accept — labels still 2–5 points below production leak scores.
- **Full 49-article labeling pass** completed via `python -m ground_truth.batch_scorer --filter filters/cultural_discovery/v5 --source datasets/raw/cd_v5_hard_negatives_candidates.jsonl --output-dir datasets/scored/cd_v5_hard_negatives --target-scored 49 --llm gemini-flash`. 49/49 SUCCESS, 0 failures, cost ~$0.05. Production v4 mean **8.27 → v5 oracle mean 4.05** across the cohort. **5 articles legitimately flipped to cultural_discovery** (carve-outs fired: Modigliani repatriation, "Slavenhandel was kinderhandel" book argues new figures, 2x Nazi-looted Masterpieces room/article, Life satisfaction Turkey psych research). Tagged `_v5_oracle_reclassified: cultural_discovery` for downstream traceability — they're calibration-confirmed positives, not hard-negatives.
- **Two new gotchas recorded** (see `memory/gotcha-log.md`): "Oracle Prompt Soft Cap Doesn't Enforce Arithmetically" + "Carve-out Language Gets Parsed Narrowly". Both generalise to any future filter prompt design.

Cost this session: ~$0.07 total (2 calibration runs at $0.01 each + 49-article batch at $0.05).

## Next Session Pickup (updated 2026-07-04 EOD)

**Housekeeping carried from 2026-07-04 (do first, cheap):**
1. ~~Resolve the phantom-memory-files claim.~~ **DONE 2026-07-05** — all 6 reconstructed + indexed, recap corrected, dangling link resolved. (Optional follow-up: sanity-check `ovr-lens-set-current.md`'s tab mapping against the actual ovr.news repo, which is authoritative.)
2. **Reconstruct the June #51 recap gap** — obituary_detector v3 (commits `87e9962`/`9692bcb`/`dd9c3c4`) has no MEMORY.md entry; add a Session Recap from git if the detail matters, else note it's git-only.
3. **Optional framework pattern** — decide whether to adopt agent-ready-projects v1.10.0's `hypothesis-log.md` (`~/repos/agent-ready-projects/templates/hypothesis-log.md`). Not currently used here.
4. **#23 / #52 are re-scoped, not done** — #23 → cd v6 `evidence_quality`; #52 → class-name drift + #66.

---

**cd v5 post-ship cleanup + solutions v4 prompt drafting** (standing backlog from 2026-05-31; still valid). cd v5 ship is complete; first-week monitoring runs in parallel.

Priority TODOs (in order):
1. **First-week #62 leakage monitoring** (2026-05-31 → 2026-06-07). Pull cd v5 scores from ovr.news Discovery tab. Verify the #62 leakage examples (Pope apology, Belgium Congo, Modigliani repatriation, residential schools, Antwerp Congolese memorial) score below 4.5. Any leak → capture in `datasets/raw/cd_v6_leakage_candidates.jsonl`.
2. **Revise `docs/adr/draft-020-extended-oracle-calibration.md`** per 4-reviewer convergent feedback: mark PROVISIONAL, cut 5→3 oracles default, split soft-penalty into separate ADR (extension of ADR-015), replace "Expected outcome: DS wins" with actual results, address Alternative 5, add conservative-oracle vs consensus-alignment precedence rule.
3. **Solutions v4 prompt drafting** (`filters/sustainability_technology/v4/prompt-compressed.md`) — 7 dims encoded, calibration batch ready (~$0.30). **This is the ADR-020 validation case**: follow cd v5's playbook end-to-end. If it lands cleanly, ADR-020 graduates PROVISIONAL → Accepted; if it hits issues, capture divergence in ADR-020 revision. **Schedule the full oracle batch off-peak** (after ~noon CEST) — DeepSeek V4 peak/valley pricing (mid-July 2026) doubles cost during 08:00–12:00 CEST. See `memory/oracle-pricing-scheduling.md`.
4. **Code refactor**: extract `extract_dim_score`, `smart_compress`, `build_prompt`, `pearson`, `spearman`, `wavg` into `ground_truth/oracle_utils.py` (9 scripts have copy-pasted variants). ~1hr work.
5. **OracleClient ABC refactor of `ground_truth/batch_scorer.py`**: currently hardcoded if/elif over `claude/gemini/gemini-pro/gemini-flash/gpt4`. No DeepSeek/Ollama support → caused fork pressure during cd v5. 2-4hr work.
6. **Apply remaining v5 prompt tightenings** per oracle-calibration agent final review (K/G/I anti-triggers) — defer to v6.
7. **Fix v3→v4 prefilter regression** (`check_content_length()` skip) — defer to v6.

Carry-over from earlier pickups (still applicable, lower priority):
- **#66 fully-declarative migration** — base `EXCLUSION_REASON_PREFIX` attr + URL-domain into `_pre_exclusion_check`. Unblocks CD v5 / uplifting v7 / foresight v1 / NR v2.
- **NexusMind#199** — regex P(obit) probe in production scoring (this side ready via `filters/common/obit_signal.py`).
- **`deploy_filters.sh` rsync exclude fix** — model/ excluded on hop to gpu-server, requires manual scp (#67 filed 2026-05-31).
- **`verify_filter_package.py` schema check for per-dim `description`** — catches Hub-upload prerequisite (#68 filed 2026-05-31).

## Next Up (from ROADMAP "Now")

- **foresight v1** — PARKED (#43, 2026-04-16). Captures governance solutions, not foresight; merging into broadened Solutions lens at sustainability_technology v4. <!-- verify: grep -qE "\*\*foresight\*\*.*PARKED" CLAUDE.md && echo PASS || echo FAIL -->
- **nature_recovery v2** — DEPLOYED to Hub 2026-04-19 after #44 fix (v2 package referenced v1 imports + repo_id before). <!-- verify: PYTHONPATH=. python scripts/deployment/verify_filter_package.py --filter filters/nature_recovery/v2 --check-hub > /dev/null && echo PASS || echo FAIL -->
- **nature_recovery v1 normalization** — FIXED (#32 closed 2026-04-09). Refit covers full score range (354 articles, x: 0.10–10.0). gpu-server scorer verified producing differentiated scores.
- **nature_recovery v2 normalization** — FITTED 2026-04-29 on 1,397 v2 production articles (filter_version=2.0, weighted_average≥1.5; raw range 1.50–7.08, p95=4.49). Patched `fit_normalization.py` with `--filter-version` to exclude v1 leftovers (#52 follow-up). Deployed to sadalsuud + gpu-server. <!-- verify: test -f filters/nature_recovery/v2/normalization.json && echo PASS || echo FAIL -->
- **prefilter shape harmonization** (#52) — COMPLETE 2026-04-29. All 7 production filters migrated to declarative shape; review-battery follow-ups also landed (8 commits). Remaining work: class-name drift cleanup batch (sustech V2→V3, NR V1→V2 — gated on NexusMind cross-repo coordination) and potential `_is_excluded` extension for per-category exceptions (deferred to ADR-019 design). See `docs/TODO.md` "Post-#52 Review-Battery Followups" for the full punch-list status. <!-- verify: grep -q "ADR-018" filters/common/base_prefilter.py && grep -q "DOMAIN_EXCLUSIONS" filters/common/base_prefilter.py && echo PASS || echo FAIL -->
- **gpu-server filter discovery dedup + canonical alignment** (2026-04-30, NexusMind 2d3c666 + manual weight migration) — #53 STRUCTURALLY FIXED, with bonus canonical alignment. (1) `FilterLoader.discover_filters()` collapses hyphen/underscore variant collisions to one registered entry (winner = most complete artifacts), alias map covers both API name forms. (2) After the structural fix shipped, weights were moved gpu-server-side from `investment_risk/v6/model/` to `investment-risk/v6/model/` so the registered winner is now `investment-risk` — matches llm-distillery's source-of-truth convention. Discovery flipped: `using 'investment-risk' (most complete artifacts), ignoring ['investment_risk']`; alias map: `{'investment_risk': 'investment-risk'}`. Both API name forms still resolve to the same scorer (verified — same wa returned for both). The earlier band-aid symlink loop (which caused two outages in 24h) is fully retired. **2026-07-04 correction:** gpu-server disk now shows **only `investment_risk/v6/model` (underscore) — the hyphen dir + symlink are gone**, i.e. divergence consolidated to *underscore*, the opposite of the hyphen-winner recorded above (a later cleanup or reprovision superseded the discovery-dedup outcome). #53 is effectively resolved on disk; the two-parallel-dirs symptom is not present. <!-- verify: ssh gpu-server 'test -d ~/NexusMind/filters/investment_risk/v6/model && ! test -d ~/NexusMind/filters/investment-risk' && echo PASS || echo FAIL -->
- **raw_weighted_average** — Now passed through gpu-server API → sadalsuud pipeline → filtered output (#36 closed 2026-04-09). Normalization fitting script prefers it to avoid double-normalization.
- **thriving v1** — PAUSED. Candidate for two-stage scoring fix. See `memory/thriving-v1-scoring.md`.
- **#24** — ONNX Runtime INT8 or smaller base model retraining
