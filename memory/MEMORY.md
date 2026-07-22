# LLM Distillery — Memory Index

Loaded every session. Topic files loaded on demand via triggers below.

> **Creating or retraining a filter? START at `docs/FILTER_PLAYBOOK.md`** — the SSoT that compiles every lesson (the pits) + the canonical example (`nature_recovery v4`). It indexes all filter docs so you never scavenge.

## Topic Files

| File | When to load | Key insight |
|------|-------------|-------------|
| `gemma3-model.md` | Model loading, PEFT, or Hub upload issues | Auto mapping fix, OLD vs NEW key format, torch float16 |
| `gpu-server.md` | Training on GPU or deploying to gpu-server | HF_HUB_OFFLINE, scp not rsync, venv path, PYTHONPATH |
| `feedback-scorer-always-rest.md` | Scorer looks "down" / tempted to restart it | ALWAYS let the on-demand scorer rest; never restart or curl /health (2026-07-10 rule) |
| `filter-status.md` | Checking filter versions, MAE, or hybrid probe stats | Per-filter deployment status and in-dev blockers |
| `gotcha-log.md` | Stuck on infra, tooling, or something weird | Problem → Root cause → Fix archive |
| `thriving-v1-scoring.md` | Understanding thriving v1 attempts | PAUSED — bimodal distribution, MAE 0.94, findings and open questions |
| `uplifting-v7-training.md` | Understanding thriving v1 history | v7 prompt evolution → thriving v1 rename (ADR-012) |
| `calibration-history.md` | Starting any calibration / scorer-training / oracle-prompt experiment | Dead Ends section: which approaches are already known dead — don't retry (#69) |
| `oracle-pricing-scheduling.md` | Planning any oracle batch scoring run | DeepSeek V4 peak/valley pricing — run batches off-peak (avoid 08:00–12:00 CEST) for 2x savings |
| `feedback-oracle-selection-criteria.md` | Picking an oracle for a new filter | Multi-oracle calibration + agent judging on a disagreement set (ADR-020 method); don't default to one |
| `feedback-conservative-oracle-better.md` | Choosing/tuning an oracle with penalty flags | Prefer the oracle that under-fires penalties; conservativism > raw consensus |
| `feedback-oracle-not-ground-truth.md` | High-MAE dimension, or optimizing student | Oracle is a consistent labeler, not truth — suspect label noise first, fix the prompt |
| `feedback-claim-requires-verify.md` | Writing any "deployed/shipped/tested/uploaded" claim | A claim is false until a check that probes THAT specific claim runs and its output is captured — grep the artifact exists before "promoted to X" |
| `feedback-oracle-bias-vs-noise.md` | Tempted to switch/pick an oracle on consistency numbers | NOISE (self-consistency) ≠ BIAS (editorial alignment). Never switch oracle to cut noise — bias is primary; average k runs of the correctly-biased oracle instead. Cost the engineer $100-200 before |
| `feedback-probe-training-data.md` | Building a Stage-1 e5 probe | Train it recall-first on the FULL labeled set (not positives-only/seed-only, which misses low-scoring true positives); threshold from the val recall curve, report FN@MEDIUM+ not MAE |
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
| `docs/NORMALIZATION_METHOD.md` | Canonical normalization method reference (anchored CDF, guards, reproduction) + article source material |
| `docs/adr/README.md` | ADR index (001-019) |
| `filters/common/obit_signal.py` | Hoisted regex obit probe — used by belonging v1 prefilter and NexusMind#199 cross-lens leak measurement |

## Cross-Project: NexusMind

- NexusMind's `src/filters/filter_loader.py` auto-discovers from `filters/` directory
- NexusMind's output includes `nexus_mind_attributes` — downstream apps (ovr.news, dashboard, Aegis) depend on field names. Don't rename fields.
- gpu-server runs NexusMind scorer at `~/NexusMind/filters/` (dirs use **underscore** names: `cultural_discovery`, `investment_risk`, …). Deploy new filters with `scp`.
- **`nexusmind-scorer.service` is a `static`, on-demand unit** (FastAPI :8000) — spun up per scoring run in the chain **FluxusSource harvest (sadalsuud) → NexusMind pipeline (sadalsuud) → gpu-server scorer → exits**. **Inactive between runs is the normal resting state, NOT an outage.** A *real* fault shows `Result≠success` (a clean stop is `Result=success`, `NRestarts=0`). Known eviction failure mode: Ollama/vmodel-daemon grabs the GPU via `Conflicts=` (NexusMind#250). Authoritative details: `FluxusSource/memory/nexusmind.md`. **Do not curl `localhost:8000/health` as a health check — it only answers mid-run.**
- Filter changes should be deployed to both gpu-server and sadalsuud.
- **Deploys ship the git-archive of HEAD (Fix B, 2026-07-17)** — filter packages MUST be committed+pushed to deploy; a file-copied-but-uncommitted package BLOCKS the every-4h cycle (fail-closed, fires the email alert). Manual deploys race the 4h timer (see gotcha-log 2026-07-17) — prefer pull-and-let-ExecStartPre-run.
- **Before merging ANY `deploy_filters.sh` change**: run `NexusMind/tests/deploy_dryrun/setup_and_run.sh <branch>` — the 52-assertion dry-run harness (fake remote, real rsync). Born from Fix B; NEVER test deploy-script changes live as ExecStartPre.
- **`nexusmind.service` failures now alert by EMAIL** via `OnFailure=nexusmind-alert@` — sent through the chain's existing Gmail sender (FluxusSource `[email_credentials]` on sadalsuud; engineer explicitly wants NO new notification services), 3h burst guard, plus `data/alerts.log`. Self-tested delivered 2026-07-17.

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
- if [a regex correctness bug is found], then [audit siblings in the same file/author-style — same-shape bugs cluster] — promoted from gotcha-log 2026-04-29 (recurrence of #45 RIP issue → today's multilingual sweep; recurred AGAIN 2026-07-08: POSITIVE_PATTERNS trailing `\b`)
- if [bumping a filter to vN by copying vN-1's package], then [repoint the inference modules' imports to vN and CONSTRUCT the real production scorer class — `load_filter_package` discovers the prefilter by name-substring and masks a stale `vN-1` import that crashes the actual entrypoint] — promoted from gotcha-log 2026-07-08 (3rd in the cluster: #44 v2→v1 imports, #52 class-name drift, v4 inference stack)
- if [writing or auditing a deploy/sync script that runs `git add` (or rsync-then-commit) against a directory it doesn't fully own], then [require fail-closed dirty-check + explicit path staging; blanket `git add -A` is a latent origin-contamination bug that fires on the first multi-author day] — promoted from gotcha-log 2026-05-23
- if [a candidate oracle looks better on self-consistency/agreement], then [STOP — that's noise, not bias; judge the disagreement set editorially before switching, and cut noise by averaging k runs of the correctly-biased oracle, never by switching to a cleaner-but-differently-biased one] — promoted from gotcha-log 2026-07-09 ([[feedback-oracle-bias-vs-noise]]; engineer caught a $100-200-class error)
- if [a deploy gate / eval reports a surprising FAIL or a batch of "model errors"], then [reproduce — read the actual per-item labels the metric was computed from — before retraining/switching; the reference cohort may be labeled by a different oracle/version (check for a `_v2_split`-style provenance field)] — promoted from gotcha-log 2026-07-09 (ground-truth gate vs Gemini-labeled reference)
- if [re-running a training to regenerate clean artifacts], then [do NOT assume same-seed reproduces the evaluated model — CUDA is nondeterministic; re-run the gate on the re-trained weights, or back up the approved model+calibration+metadata together at approval time] — promoted from gotcha-log 2026-07-09
- if [checking whether a remote job is running with `pgrep -f "<pattern>"`], then [it matches your own ssh command line too — verify by footprint (GPU mem / large RSS / log growth), not name-match] — promoted from gotcha-log 2026-07-09 (recurred 2026-07-19 as the DESTRUCTIVE twin: `pkill -f solutions_screen.py` killed its own parent shell and silently aborted a 669 MB transfer — pkill *executes* the false self-match; use a bracket trick `solutions[_]screen` or match by pid)
- if [a comment asserts a property the code depends on], then [TEST the property — a sentence is not a control. "The dirty-check guarantees HEAD == worktree" was false (`git diff --quiet <paths>` is worktree-vs-INDEX; `git add` defeats it) and shipped a deploy that could stamp a revision naming bytes production wasn't running] — promoted from gotcha-log 2026-07-14 (recurred 2026-07-17: two fresh Fix B "by construction"/"nowhere else to update" comments falsified by contract review — one became the runtime push-completeness assertion)
- if [writing a test for a function], then [IMPORT the function, never re-implement it — a private copy in `test_normalization_invariant.py` drifted from its subject *within the same commit*, omitting the ambiguity check added beside it] — promoted from gotcha-log 2026-07-14
- if [a review finding is dramatic], then [treat it as a hypothesis and check it against the ADRs before acting — round 1's top finding was a misread of ADR-014's documented design, and an agent independently reached the same wrong conclusion. Two models agreeing is not evidence] — promoted from gotcha-log 2026-07-14
- if [running a review at all], then [run TWO rounds — round 1 reviews the code, round 2 reviews the fixes, and 4 of round 2's 8 findings were defects inside round 1's fixes (including the test meant to catch them)] — promoted from gotcha-log 2026-07-14 (pattern held an EIGHTH consecutive time 2026-07-17 evening: solutions v4 prompt round-2 found 3 defects inside round-1's fixes — opinion-vs-router contradiction, unpropagated community-gov rule, conflicting proposed-bill anchor; held a NINTH time 2026-07-18: solutions v4 data-setup plan round-2 caught a self-contradictory *unpassable* pre-spend gate created by round-1's own stratification fix)
- if [adding ANY control — hook, gate, cap, assertion, guard, test], then [watch it fail before trusting it; a control never observed failing is decoration. For tests: run against the OLD code and confirm they fail — AND confirm CI actually feeds them an input that exercises the assertion; a guarded `if field is not None:` over a corpus that never carries the field is dead code] — promoted from gotcha-log 2026-07-14 (5 dead controls in one session; recurred 2026-07-17: the sample_min assertion added by Fix A hardening ran on zero inputs; held AGAIN 2026-07-19: a Part-A seed gate was tautologically-true (seeds folded into `cand` before being counted → `seeds_present ≡ 33`) and a Swahili check-script returned false-`0` for every language — the fix is watch-it-fail: the rewritten gate was proven to FAIL on a boilerplate seed, and reproduction-from-disk caught the false-0. Applies to *measurement* scripts, not just runtime gates. Held a 4th time 2026-07-20: the staged `partB_gate.py` keyed positives on `solution_type != "not_a_solution"` but the prompt emits `"none"` → the gate reported **100% positive → PASS** (plus a nested-dim `TypeError` on `solution_concreteness`). Caught only by running the gate on a REAL oracle-scored row and disbelieving the 100%. **Corollary: a scored-gate whose positive-rate reads 0% or 100% is almost always keyed on the wrong sentinel — verify the gate's literal enum strings + field nesting against an actual scored record before trusting any PASS.**)
- if [a check reports FAIL], then [ask whether it FAILED or couldn't RUN — `cmd && echo PASS || echo FAIL` collapses the two, and a check that cries wolf trains you to skim past it. Let the *claim* decide PASS/FAIL and let transport/deps/creds surface ERROR] — promoted from gotcha-log 2026-07-14
- if [a diagnosis is backed by a workaround that works], then [distrust it — an error whose workaround produces green results never falsifies itself. Test the original path directly] — promoted from gotcha-log 2026-07-14 (sadalsuud hop kept "no gpu-server key from situla" alive; engineer caught it)
- if [a model looks like it's scoring badly in production], then [check `normalization.json`'s fit threshold FIRST — #161 was v2 scoring 2.2–3.3 *correctly* and a CDF fitted at raw>=1.5 inflating it to 5.2–8.3] — promoted from gotcha-log 2026-07-14
- if [shipping a fresh filter version that needs cross-filter normalization], then [fit `normalization.json` at deploy from a *production-representative historical* rescore — do NOT ship raw and wait weeks for live accumulation; a raw filter is under-ranked/under-shown against every normalized lens (ovr `canonical-lens.ts` + `displayScoreThreshold`). Must be production base-rate, not the enriched val set; `MIN_NORMALIZATION_ARTICLES=200` rejects thin fits. Playbook §6] — promoted from gotcha-log 2026-07-11
- if [retraining/broadening a filter by re-scoring an OLD-lens corpus under a NEW lens], then [the article population's positive-rate under the new lens is UNKNOWN — measure it with a ~$0.10 scored random sample BEFORE any full re-score. solutions v4's old ST v3 + foresight corpora were 85% not_a_solution under the Solutions lens (median wa 0.00); prompt/oracle validation says nothing about whether the population still has signal. Enrich via e5-seed screening (ADR-011), don't re-score noise] — promoted from gotcha-log 2026-07-18
- if [tempted to add a runtime fail-closed control (raise/halt) to catch a deploy/config mistake], then [FIRST check whether an existing CI/deploy-time guard already covers it, and bound the blast radius. A raise in NexusMind `_resolve_filters` on one enabled-but-missing filter aborted scoring for ALL filters and broke 2 tests — while `tests/unit/test_filter_integrity.py` already asserts every enabled filter is discoverable at CI time. Fail-closed belongs at the CI/deploy layer, not inside runtime scoring; a runtime control that halts everything on one missing item is over-broad. Round 2 of the review caught it as a defect-in-fix] — promoted from gotcha-log 2026-07-22 (3-round battery: R1 fix became R2 critical; the "run 2+ rounds" rule held again — 15 defects-in-fixes in R2 alone)

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
- **sustainability_technology → `solutions` v4 RENAMED 2026-07-18 (ADR-012)** — pkg `filters/solutions/v4/`, `filter.name=solutions`, field `solutions_analysis`, prefilter class `SolutionsPreFilterV4`; v1–v3 stay under the old package. 4 engineer decisions RATIFIED (DeepSeek oracle, thinner tab, go; gate/weight rewrite deferred to eval). 4 calibration fixes + scrape-junk check applied & live-oracle-verified. **Corpus re-score of the old corpora was RETIRED** — a diagnostic showed ST v3 + foresight r2 are ~85% not_a_solution under the Solutions lens; sourcing pivoted to e5-seed screening per `filters/solutions/v4/DATA_SETUP_PLAN.md`. Multilingual `prefilter.py` drafted (nr v4 template). **2026-07-20: corpus SCORED (~$14) + prepped to train 9,265 / val 1,032 / test 1,500** (test=isolated unscreened holdout); train mix 31.5% pos, holdout 11.5% (prod base rate), 90 high-band community/hybrid. Part-B `<50%` gate reframed unachievable-by-design (flat e5 gradient); arXiv contamination excluded; high-band-community pool dry (v2 source-expansion). **2026-07-21: TRAINED + CALIBRATED + GATED, deploy decision pending.** Gemma-3-1B+LoRA val MAE 0.564; Step-8 runtime scorer written (`base_scorer.py`/`inference.py` — was missing, calibration failed on it first); `calibration.json` (marginal); **ADR-021 gate op 3.0: recall 0.45 / prec 0.78 / spec 0.99**. Op-point sweep best F1 ~2.25 (recall 0.56). Gatekeeper cap 3.0≡2.9 (inert→keep 3.0). **Recall ceiling ~0.58 STRUCTURAL** (52/61 misses scored <2.5 = e5-screened training manifold misses unscreened prod = access-bias → v2). `ground_truth_gate.py` **generalized filter-agnostic** (nr-safe, 8/8 tests). **NEXT: compare to other filters' gate metrics → op-point decision (2.25/3.0/hold-for-v2) → deploy.** Model gitignored → gpu-server + local backup. Records: `project_session_2026_07_21.md`, `DATA_SETUP_PLAN.md` (Round 5), `filters/solutions/v4/README.md`. <!-- verify: test -f filters/solutions/v4/inference.py && test -f filters/solutions/v4/calibration.json && test -f filters/solutions/v4/ground_truth_gate.json && echo PASS || echo FAIL -->
- Normalization must be fitted at/above the operating point — enforced 2026-07-14 (`33fba44`). `fit_normalization.py` resolves the op-point from `TIER_THRESHOLDS` (lowest non-zero) and **refuses** `--min-score` below it (escape: `--allow-below-op-point`). Fitting below it maps sub-visibility content into the visible band — the actual root cause of NexusMind#161, not the model. Warns on config/code drift (already found one: sustech v3). Detail: `project_session_2026_07_14.md`. <!-- verify: PYTHONPATH=. python3 scripts/normalization/fit_normalization.py --filter filters/nature_recovery/v4 --data-dir /nonexistent --min-score 1.5 2>&1 | grep -q "is below the operating point 3.75" && echo PASS || echo FAIL -->
- `climate_doom` runtime cap **RETIRED** 2026-07-14 (NexusMind `1dd5e49`) — 3 production bites, 3 false positives, 0 saves. All three were the trigger word in a *non-doom construction* a polarity-blind regex can't see: `evitar su extinción` (prevent), `en peligro crítico de extinción` (IUCN label), `deforestation-free` (`\b` matches across the hyphen). The earlier same-day override-window widening (`8681efa`) rescued two and missed the third entirely. **The `recovery_evidence` gatekeeper (<3 → cap 3.5, below the 3.75 op-point) already does this job semantically** — doom scores recovery_evidence 0.07–1.08, the coffee FP scored 4.58. Registry is empty but the mechanism is retained. Accepted trade: real doom is no longer capped either (model scores it 0.36–1.89, below op-point). <!-- verify: grep -qF 'List[re.Pattern]]]] = {}' ~/repos/veen-systems/NexusMind/src/scoring/cap_triggers.py && ! grep -qF '"nature_recovery": [(' ~/repos/veen-systems/NexusMind/src/scoring/cap_triggers.py && echo PASS || echo FAIL -->
- Deploy freshness gate, hash and dirty-check all derive from ONE list — `SCORER_PATHS` in NexusMind's `deploy_filters.sh` (`4e25934` → `a95c3d6` → `7ef6029`). Three separate bugs from restating the deployed set: (1) the hash covered `src/scoring/` but the gate didn't → scoring-only commits silently never deployed while reporting "already in sync"; (2) `deploy/gpu-server/{main.py,scorer-start.sh}` were hashed AND scp'd but never gated; (3) the dirty-check used `git diff --quiet <paths>` (worktree-vs-INDEX), so `git add` defeated it — the hash then named bytes production wasn't running. The hash is now built by ITERATING `SCORER_PATHS`, so gate/hash/deploy cannot drift apart. **Validated in production 2026-07-14 20:08**: the gate auto-pulled a `src/scoring`-only change — the exact case it used to miss. <!-- verify: D=~/repos/veen-systems/NexusMind/scripts/deploy_filters.sh; grep -qF 'SCORER_PATHS=(' $D && grep -qF 'for scorer_path in "${SCORER_PATHS[@]}"' $D && grep -qF 'deploy/gpu-server/main.py' $D && ! grep -qF 'HASH_FILTERS=' $D && grep -qF 'git diff --quiet HEAD -- "${SCORER_PATHS[@]}"' $D && echo PASS || echo FAIL -->
- **Deploy ships the git-archive of HEAD — Fix B EXECUTED, DEPLOYED, validated live 2026-07-17** (NexusMind `dcf6fc8`, on top of the `SCORER_PATHS` unification below). `git archive HEAD` → staging dir → all rsync/scp from staging: untracked/gitignored/edited files can no longer ship (closes the round-3 untracked + round-4 gitignored-straggler gaps; supersedes+deletes held `7e525ee`). Untracked operator gate (filters only `filters/**/model/`) shared by auto-pull guard + main gate, fail-closed on git error with sentinel-aware diagnostics; runtime push-completeness assertion; smoke fixtures in `SCORER_PATHS`, shipped from staging; component-form rsync excludes; `.gitignore` `models/` scoped to `/models/`. Carve-outs (documented, deliberate): tracked `*/model/` configs are hashed-but-never-shipped (out-of-band weight channel — sha256 diff vs gpu-server came back DIRTY, so shipping repo copies would overwrite Hub-provenance files; settled, don't "fix"); `CODE_REVISION` is shipped-but-not-hashed. Validated by the canonical 4h chain itself (ExecStartPre status=0, hash `6f0458f3…` round-tripped). Harness fixture: `tests/deploy_dryrun/` (52 assertions). OnFailure→email alert live (chain's Gmail sender, no new services). <!-- verify: D=~/repos/veen-systems/NexusMind; grep -qF 'git archive HEAD' $D/scripts/deploy_filters.sh && grep -qF 'PUSHED+=' $D/scripts/deploy_filters.sh && test -x $D/tests/deploy_dryrun/setup_and_run.sh && grep -qF '/models/' $D/.gitignore && ssh -o BatchMode=yes -o ConnectTimeout=10 sadalsuud 'systemctl show nexusmind.service -p OnFailure | grep -q nexusmind-alert' && echo PASS || echo FAIL -->
- The #44 commit-msg gate is live for the first time — fixed 2026-07-14 (`9b6126d`): was mode 100644 (git silently ignores non-executable hooks) and called bare `python`. Enable per clone: `git config core.hooksPath .githooks`. <!-- verify: [ "$(git ls-files -s .githooks/commit-msg | cut -d' ' -f1)" = "100755" ] && echo PASS || echo FAIL -->
- cultural_discovery v5 DEPLOYED 2026-05-31 — resolves #62 discovery-lens leakage. Val MAE 0.697 (v4 was 0.74). Soft-penalty F/G/H/I/K flags (historical_harm_reckoning, commemoration_memorial, perpetrator_biography, decline_loss, launch_announcement). DeepSeek V4 Flash oracle (first non-Gemini lineage in production, ~7x cheaper). End-to-end verified: Pope apology 9.65→2.31, Indus/Sumer 9.12 (gradient preserved). v4 deleted from gpu-server post-verification; still in llm-distillery + git + HF Hub for rollback. **Provisional reference example for ADR-020 methodology** (multi-oracle batch + agent judging) and DeepSeek-as-default-oracle; solutions v4 is the validation case. <!-- verify: ssh -o BatchMode=yes -o ConnectTimeout=10 gpu-server 'test -d ~/NexusMind/filters/cultural_discovery/v5/model && echo PASS || echo FAIL' 2>/dev/null || echo ERROR -->

## Session pointers

Full per-session narratives live below the auto-loading cliff (read on demand). Newest first.

- [2026-07-22](project_session_2026_07_22.md) — **Solutions v4 op-point 2.25, Hub published, 3-round multi-model review, DEPLOY-READY (live cutover HELD).** Op-point **2.25** (gate recall 0.559/prec 0.768/F1 0.647 regenerated); `score_scale_factor`→1.0; `normalization.json` fitted from a 40K non-commerce prod rescore (536≥2.25); Hub `solutions-filter-v4` published+verified (card fixed to DeepSeek). **3 review rounds (15+31+7 confirmed, 15 defects-in-fixes in R2)**: reverted a bad fail-closed `_resolve_filters` raise that **halted the whole pipeline**+broke tests (existing `test_filter_integrity` is the right guard); added `solutions` across the ovr pipeline incl. the **missed `summarize.ts` driver** + v4-dimension display; fixed nr v4 + cd v5 Hub cards (wrong-oracle). llm-distillery pushed; ovr committed (`c279dc4`); NexusMind staged. **Live cutover HELD (unattended) — coordinated go sequence in the session file.** Sibling report-only: **nr v4 runs raw-passthrough in prod (#72)**. Recall caveat: prod surfaces at effective raw ~2.64 (normalized tiering) < gate 0.559 (systemic).
- [2026-07-21](project_session_2026_07_21.md) — **Solutions v4 TRAINED + CALIBRATED + GATED ($0), deploy decision pending.** Trained (val MAE 0.564), then hit 2 gaps the build left: (1) **Step-8 runtime scorer never written** — calibration failed on the missing `filters.solutions.v4.inference`; wrote `base_scorer.py`/`inference.py`/`__init__.py` (copy-from-nr-v4). (2) **`ground_truth_gate.py` was nr-hardcoded** → generalized filter-agnostic (nr-safe, 8/8 tests + regression check). **ADR-021 gate (op 3.0): recall 0.45 / prec 0.78** — precision-strong, recall-weak. Op-point sweep best F1 ~2.25 (recall 0.56). Gatekeeper cap 3.0≡2.9 (inert→keep 3.0). **Recall ceiling ~0.58 STRUCTURAL** (52/61 misses scored <2.5, incl. 13 high-band = e5-screened training manifold misses unscreened prod = access-bias, v2 fix). Model gitignored → gpu-server + local backup. **NEXT: compare to other filters → op-point decision → deploy.**
- [2026-07-20](project_session_2026_07_20.md) — **Solutions v4 corpus SCORED + TRAIN-READY (~$14 DeepSeek), paused at train boundary.** Drove Part-B → full score → prepare_data. Caught 2 bugs in the staged `partB_gate.py` (wrong `"none"` sentinel → false 100%-PASS; dict/scalar concreteness crash). Part-B `<50%` gate FAILED on the literal line but is **unachievable-by-design** (flat e5 gradient, empirically confirmed; 39-40% positive beats the ~15% forecast). arXiv contamination (**18,628 off-lens rows**) excluded via an OFF_LENS screener mask (quality win, didn't move the rate). High-band-community hunt → **pool is dry** (external source-expansion is a v2 item). Full score crashed mid-run on **HTTP 402 Insufficient Balance** ($5.95) → topped up → resumed in valley pricing → **10,297 + 1,500 scored, 0 err**; prepped **train 9,265 / val 1,032 / test 1,500** (test=isolated holdout). **NEXT: train (gpu-server is a non-git file-copy → sync + verify `train.py` currency FIRST).** Non-EN scrape-junk patterns committed (24 tests).
- [2026-07-19](project_session_2026_07_19.md) — **Solutions v4 corpus build EXECUTED (free), 4 poisons caught, turnkey to Part-B.** Enrich-first reframe (mirror production `pre_enrich`); GPU-screened on gpu-server; caught thin-stubs / multilingual-skew / near-dup-over-drop / **consent-wall poison (99% of candidates!)**. 33 community seeds (21 pool + 12 external high-band). 3-reviewer battery → corpus SOUND, 2 control fixes watched-failing, holdout near-dup (42 leakers dropped → 7,433), Part-B tooling staged. Access-bias → **ovr positioning doc + 3 article seeds**. $0 spent. Cross-repo: NexusMind enrichment consent-guard bug.
- [2026-07-18](project_session_2026_07_18.md) — **solutions v4: decisions ratified, corpus trap caught, rename, pipeline scaffolded.** 4 decisions ratified (DeepSeek/thinner-tab/go); 4 calibration fixes + scrape-junk check live-oracle-verified. The re-score-old-corpora plan was caught as a ~85%-noise trap ($0.09 diagnostic) → pivoted to e5-seed screening (`DATA_SETUP_PLAN.md`). Renamed sustainability_technology → **solutions** (ADR-012), pre-corpus-scoring. Multilingual `prefilter.py` drafted (nr #70 lesson). 2 review batteries (round-2 pattern held a 9th time). Corpus-build tooling scaffolded. Zero spend beyond ~$0.20 diagnostics. Blocked on 2 engineer inputs (community seeds + defaults sign-off).
- [2026-07-17 evening](project_session_2026_07_17_evening.md) — **Solutions v4 (#43): scaffold → calibrated in one session.** Foresight/Solutions mixing confirmed+quantified (tab ~91% foresight-fed, 934 vs 88/24h); v4 prompt drafted + 2 review rounds (round-2 pattern held an 8th time); 350-article calibration batch scored by BOTH oracles ($1.00, ADR-020 method); two judges → DeepSeek; pure-tech ≥7.0 gate empirically unsatisfiable. Stopped at engineer sign-off. Record: `filters/solutions/v4/calibration_report.md`.
- [2026-07-17](project_session_2026_07_17.md) — Morning wrap-up: 11-agent multi-model battery over the merged Fix A range → 5 confirmed findings fixed (dead `sample_min` assertion now exercised by synthetic-package tests; `n_bins < 2` fails closed; 3 stale doc facts), 2 refuted. 196 tests green. Framework current (v1.10.6 = latest); uplifting v7 weights flagged as gpu-server-only (NO_HUB, absent locally). Addendum: **sustech v3 op-point drift FIXED** (`65484f4`). Afternoon: **Fix B EXECUTED end-to-end** — git-archive deploy chosen+built+52-assertion-harnessed, 3-model round-5 review (7 verified defects fixed, pattern held a 7th time), merged `dcf6fc8`, deployed, **validated live by the canonical 4h chain itself**; held `7e525ee` deleted; OnFailure alert shipped+tested (ntfy first, swapped same-day to the chain's Gmail sender on engineer feedback); harness preserved as `tests/deploy_dryrun/` fixture (`f6497fa`); model-config carve-out SETTLED by sha256 evidence (keep).
- [2026-07-16](project_session_2026_07_16.md) — Morning: **#62 leakage check DONE (cd v5 holds, 96% suppressed)** + cap retirement behaviorally confirmed; round-4 review found defects in my own round-3 fixes → both HELD; re-enchantment outlets parked. Evening: **Fix A EXECUTED** — CDF lower edge anchored to op-point (prepended breakpoint; `raw_min == op_point` by construction, `stats.sample_min` added for bias audit), invariant back to near-equality ±0.01 single-sourced, round-3 margin deleted. 3-model review battery found 11 findings incl. a regression my own root fix created (biased-sample fits became loadable → restored as `sample_min > 4.5` deploy gate + test assertion); all verified ones fixed. **llm-distillery hold RESOLVED, merged to main.** NexusMind hold (`7e525ee`) remains — Fix B replaces it.
- [2026-07-14](project_session_2026_07_14.md) — health check → **five dead controls**. #161 reframed: v2's model scored the doom articles 2.2–3.3 *correctly*; `normalization.json` fitted at raw>=1.5 inflated them to 5.2–8.3 (reproduced 5/5 exactly). v4 rescore: 0/5 surface → the `climate_doom` cap is dormant, and was 0-for-2 in prod. Fixed: fitter refuses below op-point, cap override window, commit-msg hook (never executable), deploy gate blind to `src/scoring/`, 3 verify assertions FAILing on true claims.
- [2026-07-11](project_session_2026_07_11.md) — "ovr shows no new nature articles" → **not broken**: v2's fuller feed was ~90% normalization inflation; fresh-v4 raw scores are under-ranked vs still-in-window inflated v2 rows (self-corrects ~Jul 19 as v2 ages out). Exposed the **normalization cold-start** doc gap → fit at deploy from a production-representative historical rescore (playbook §6 + RUNBOOK). Doc-only, no deploy.
- [2026-07-10](project_session_2026_07_10.md) — v4 op-point 3.75 fix (was wired to nothing, ran at 4.0) + cd/invR normalization refit (version/filter_version fitter bug), both **validated in production output**; 12-agent adversarial review (F1/F2/F3); framework → v1.10.6.
- [2026-07-09](project_session_2026_07_09.md) — nature_recovery v4 to the deploy boundary: recall-first probe, ground-truth gate (ADR-021), oracle bias-vs-noise ($100-200 catch), Hub-uploaded + staged-not-activated.
- [2026-07-07→09](project_session_2026_07_08.md) — v4 build pre-deploy: v3→v4 pivot (#70), DeepSeek re-label 3892 ($4.81), commerce-only prefilter (recall 21.6%→1.3%), 4-model review battery (caught CRITICAL v2 import), ranking metrics settled.
- [2026-07-04](project_session_2026_07_04.md) — hygiene: DeepSeek peak/valley pricing (off-peak batches), on-demand scorer architecture correction, issue triage (#39/#53 closed), framework v1.9→v1.10.4.
- [2026-05-31](project_session_2026_05_31.md) — cultural_discovery **v5 SHIPPED** (DeepSeek oracle, val MAE 0.697, #62 leakage resolved end-to-end).
- [2026-05-29/30](project_session_2026_05_29.md) — cd v5 hard-negatives cohort (49 articles, 5 buckets) + v5 prompt drafted (flags F/G/H/I/K).

## Next Session Pickup (updated 2026-07-22 evening)

**The 2026-07-22 *evening* session was ops/triage (no filter-building).** Solutions cutover EXECUTED +
live-scoring; a **P1 commerce regression** was found; infra fixed. Full record: `project_session_2026_07_22.md`.
Pick up in this order:

**① VERIFY SOLUTIONS — still pending; the ONLY thing blocking ADR-020 Accepted.**
The cutover fired but first-cycle verification never completed: the 16:09 cron was blocked by a stale
smoke fixture (fixed NexusMind `e2a102e`, fixture repointed to solutions), then the manual re-run spent
3h+ on a one-time new-filter image+enrichment catch-up (backfill→hero→enrichment each fetching ~20k
pages) and had NOT written `filtered/solutions/*.jsonl` by session end.
→ `ssh sadalsuud 'ls -t ~/local_dev/NexusMind/data/filtered/solutions/'` — if solutions output exists
with sane scores (live smoke was **wa 4.43**, method gpu-server) → **ADR-020 PROVISIONAL→Accepted**.
A normal cron cycle will also have run by then (cheaper/cleaner sample than the catch-up run).

**② P1 — COMMERCE v2 IS A LIVE REGRESSION (#80, P1-high/bug).** Shadow run this session proved v2 (live
on the gpu-server scorer) UNDERPERFORMS the v1 it replaced: blocks 2.1% vs 5.2%, misses obvious product
listings AND over-blocks multilingual (Greek) news — NOT the 128-token cut (v2-misses are shorter than
avg). Report: `filters/common/commerce_prefilter/docs/SHADOW_REPORT_v1_vs_v2.md`.
→ DECIDE: roll back to v1 (BLOCKED — v1 weights only on gpu-server, `commerce.py:271` local fallback
would `FileNotFoundError`) OR retrain v2 on representative multilingual traffic. Also: **back up v1+v2
weights to HF Hub** (gitignored; v1 is a single copy on the borrowed gpu-server = unrecoverable if it dies).

**③ Standing filter work (unchanged): #76 calibration crush.** Deployed filters demote good content below
the medium boundary — likely ONE normalization/`raw_min`-drift root cause across #74/#75/#76/#72; start at
#76, cross-ref `calibration-history.md` Dead Ends. (Owner flagged commerce #80 as higher priority.)

**Infra fixed this session (durable):** gpu-server now has **direct headless ssh from situla** (copied the
passphrase-less `nexusmind_gpu` key; `gpu-server.md` updated — no more sadalsuud hop). **git push works
repo-wide** via the gh HTTPS token (`gh auth setup-git` + global `insteadOf`). Idea issues **#78**
(manipulation/propaganda *technique* scorer — new cross-cutting category) + **#79** (calm/ND + media-literacy
outlets) filed. NexusMind **#277** filed-then-closed (hero extraction DOES self-cap at 3600s — I'd misread
the code; runtime disproved it).

**DEPLOYED 2026-07-22 (LIVE-SCORING; first-output verification pending):** op-point **2.25** (gate 0.559/0.768/0.647); `score_scale_factor` 1.0;
`normalization.json` fitted (40K non-commerce rescore, 536≥2.25); Hub `solutions-filter-v4` published
(card=DeepSeek); 3-round review clean. NexusMind `61ecc10` pushed (package + `enabled_filters` +solutions
−sustech −foresight); model pre-placed on gpu-server (`~/NexusMind/filters/solutions/v4/model/`);
smoke-tested (wa 3.95 medium); `test_filter_integrity` 8/8 + 872 unit tests green. ovr + llm-distillery
(merged to main) pushed. **Retirement is config-level; sustech/foresight package dirs KEPT for rollback
(delete post-drain).** Summarization bake-off → `ovr.news/docs/decisions/` + ovr.news issue **#270**.

**Confirmed live bug — #72 nr v4 raw-passthrough.** nature_recovery v4 has NO `normalization.json` in
production (ssf 1.0 → method 'none'; verified 31,852/31,852 records under-ranked vs normalized lenses).
Fit it: same `content_items` rescore as solutions, `--min-score 3.75 --filter-version 4.0` (playbook §6).

**Commerce detector — v2 is ALREADY DEPLOYED & LIVE (verified 2026-07-22), NOT on the v1 fallback.**
`commerce_prefilter` **v2** (embeddings+MLP, 97.8% F1) is loaded on the gpu-server scorer: `models_loaded`
includes `commerce_prefilter_v2`, so `has_model(...)` is TRUE and NexusMind `commerce.py:178` routes to
gpu-server v2 — the v1 import at :271 is never hit. Confirmed *used*, not just loaded: runs log
`Commerce preprocessing complete: … (method: gpu-server)` (12:10 → 67 flagged, 17:58 → 107 flagged) and
commerce articles are flagged + dropped at load. The earlier "deploy v2 first / prod on v1 fallback"
premise was STALE. v2 weights live in the **NexusMind** checkout (`filters/common/commerce_prefilter/v2/
models/*.pkl`); gitignored/absent in llm-distillery. **Open follow-ups (NOT a deploy):** (a) was v2 ever
formally validated per `V2_DESIGN.md` Phases 4–5 (edge cases + shadow-vs-v1)? check `docs/…/BACKTEST_REPORT.md`;
(b) v2 dropped context 512→**128 tokens** + multilingual embedder — docs/TODO flags "redo for multilingual +
context size"; decide if it warrants rework; (c) gpu-server filter *code* is drifted (rev 916588a6 vs local
be3b163e) — resync via `deploy_filters.sh`. **→ SHADOW RUN DONE 2026-07-22 (#80, P1-high): v2
UNDERPERFORMS v1 in production** — blocks 2.1% vs v1's 5.2%, misses obvious product listings AND
over-blocks multilingual (Greek) news; NOT a 128-token issue (v2-misses are *shorter* than avg). v1 is
the better model on the sample. Report: `commerce_prefilter/docs/SHADOW_REPORT_v1_vs_v2.md`. Decide:
roll back to v1 (blocked — v1 weights only on gpu-server, local fallback would FileNotFoundError) or
retrain v2 on representative multilingual traffic. Also: **back up v1+v2 weights to HF Hub** (gitignored;
v1 is a single copy on the borrowed gpu-server). Obituary detector v3 (trained 2026-06-14, #51): **there IS evidence
of false-negatives** — owner flagged many obituaries that sailed through over past months. They're
COLLECTED: reader flags in Cloudflare KV `ovr-news-flags` (pull via ovr `scripts/flag-audit.mjs`; a
2026-06-25 audit is at `ovr.news/data/flag-evidence/`), plus the existing labeled set
`ovr.news/data/obituary-phase1-prelabels.jsonl` (gate-reject/harvest provenance). → **retrain
obituary_detector v4** on the flagged false-negatives as hard negatives. Other thread: **NexusMind#199**
(regex P(obit) probe integration — this side ready via `obit_signal.py`). NB **don't build a second "universal noise" filter** — only commerce is universal
(ADR-004; calibration-history Dead Ends). Training detectors is llm-distillery's job (they live in
`filters/common/`, NexusMind imports them).

**Follow-ups:**
- ✅ **DONE 2026-07-22:** consent-guard bug FILED → **NexusMind #276**; OFF_LENS source-exclusion mask
  UPSTREAMED into `scripts/screening/embedding_screener.py` (opt-in `--exclude-off-lens`, logged, 6/6 tested).
- Sync **`filters/common/score_normalization.py`** — 44-line llm-distillery↔NexusMind divergence
  (fit-side code NexusMind doesn't run at runtime).
- **ovr.news #270** — actually swap `ollamaConfig.model` → `gpt-oss:20b`.
- **Post-drain (~2026-08-01):** delete the retired sustech/foresight package dirs from NexusMind + servers.
- ovr **content pages** (`architecture.astro`, `lenses.astro`) + dev-analysis scripts + `db-articles.ts`
  narrow helper still say sustainability_technology — non-functional doc follow-ups.
- **solutions v2** = external source expansion + active-learning on the recall misses
  (`docs/ideas/access-bias-and-the-haystack.md`); the recall caveat (prod surfaces at effective raw ~2.64,
  so real recall < the raw-gate 0.559 — systemic, doesn't flip the 2.25 decision) is the v2 motivation.

**Your decisions (parked):** #91 sadalsuud `app.yaml healthcheck.enabled` drift (commit or revert);
uplifting v7 NO_HUB weights backup (only gpu-server + old Windows box); cd v5's 5 config-schema exemptions
(ratify or backfill).

**Optional:** file augmented-engineering evidence — the free-diagnostic-pass caught 4 poisons pre-spend +
the 3-round battery caught 15 defects-in-fixes incl. a fail-closed guard that would've halted the whole
pipeline (verification-pattern evidence).

**Standing:** deploys are committed-only (file-copy blocks the 4h cycle + emails you); run
`NexusMind/tests/deploy_dryrun/setup_and_run.sh` before touching `deploy_filters.sh`. Session close:
review battery → cleanup → docs → curate → commit → push → report.

**Reminder — the old "re-score ST v3 + foresight as-is" plan is DEAD** (85% not_a_solution under
the Solutions lens; `scripts/diagnostics/solutions_v4_corpus_noise_check.py`). Do not resurrect it.

**⚠️ Cross-repo follow-up (NexusMind):** file an issue — `ArticleFetcher.should_replace_content`
has no consent/paywall guard, so `pre_enrich` replaces real RSS summaries with Google consent
pages for Google-News articles (~17% of short articles); degrades live scoring input. See
gotcha-log 2026-07-19 + `docs/ideas/access-bias-and-the-haystack.md`.

**Go-live:** wire `SolutionsPreFilterV4` into the NexusMind loader; retire foresight (NexusMind
app.yaml + ovr filters.ts); normalization from a production-base-rate rescore (NOT the enriched
corpus); Hub repo `solutions`. ADR-020 PROVISIONAL→Accepted after the pipeline lands.

**Cutover reminder (when v4 deploys)**: retiring foresight is a TWO-REPO change — NexusMind
`config/app.yaml enabled_filters` + ovr.news `filters.ts FILTER_NAMES/FILTER_TO_TAB` — plus
normalization fitted AT deploy (playbook §6); the 10-day ovr window gives a gradual drain.

**Also unblocked: #72** nature_recovery v4 normalization refit via production-representative
historical rescore (playbook §6) — Fix A anchoring + Fix B deploy gates both done.

**✅ Fix B / deploy-hardening arc CLOSED 2026-07-17 afternoon** — record:
`project_session_2026_07_17.md` + `docs/normalization-deploy-hardening-plan.md` EXECUTED
addendum. Standing rules in "Cross-Project: NexusMind" above.

**⚠️ Engineer action pending (from 2026-07-17 afternoon):**
1. **sadalsuud `config/app.yaml` local drift**: `notifications.healthcheck.enabled: true → false`
   uncommitted on the production host (#91 dead-man's switch disabled locally). Intentional?
   Commit or revert — it's tracked, and it predates today's work.

**Carried flags**: uplifting v7 weights exist ONLY on gpu-server + old Windows box (NO_HUB) —
backup decision pending; #7-on-situla venv (cosmetic); `policy_announcement` cap gap (#161
leftover); vlonder pins agent-ready-papers v1.3.0 vs v2.3.1 (other repo's concern).

---

## Pickup history (2026-07-16 evening — superseded above, kept for context)

**✅ Fix A (normalization anchor) DONE 2026-07-16 evening — llm-distillery hold RESOLVED, merged
to main.** `raw_min == op_point` by construction; review-hardened (3-model battery, 11 findings
fixed); all 194 unit tests green. Full record: `project_session_2026_07_16.md` (evening section)
+ the EXECUTED addendum in `docs/normalization-deploy-hardening-plan.md`.
<!-- verify: PYTHONPATH=. python3 -c "import inspect, filters.common.score_normalization as m; assert 'anchor_min' in inspect.signature(m.fit_normalization).parameters" && echo PASS || echo FAIL -->

**⚠️ ONE HELD FIX remains — NexusMind `fix/deploy-dirty-check-untracked` (`7e525ee`), do NOT
merge.** Production-halt regression: porcelain flags untracked `model/` config files → blocks the
4-hourly ExecStartPre deploy. NexusMind `main` stays at stable `7ef6029`. **Fix B replaces this
branch** — align deploy dirty-check + CODE_REVISION hash + rsync to ONE deployed-set definition.
Plan: `docs/normalization-deploy-hardening-plan.md` Fix B (READY TO EXECUTE; needs the dry-run
harness in a scratch clone — NEVER live-untested as ExecStartPre). Next-session goal alongside
solutions v4 (#43); the #72 nature_recovery v4 normalization refit is now unblocked by Fix A
(sparse fits anchor instead of false-failing).

**✅ #62 leakage check DONE 2026-07-16 — cd v5 holds, no leak.** See the ✅ entry lower in this file.

---


**✅ climate_doom retirement DEPLOYED + VERIFIED 2026-07-14 20:08.** gpu-server `CODE_REVISION=d3c2f8d8…`, `_TRIGGER_REGISTRY` empty on disk, `cap_applied` is now permanently `null`. The auto-pull fired for a `src/scoring`-only change — the exact case the old freshness gate missed — so `4e25934` proved itself in production the same day. **Outstanding: confirm `cap_applied: 0` in the first post-20:08 batch** (any `filtered_2026071*_20*.jsonl` or later); the 16:40 and earlier batches are pre-retirement and legitimately show 1.

**Two decisions are yours, both deliberately left alone:**
1. **cd v5's 5 config exemptions** (`tests/unit/test_filter_config_schema.py`) — ratify the leaner shape or backfill. v5 may be RIGHT: nothing reads `deployment`/`hybrid_inference`/`training`, and `gatekeepers`/`tiers` live in `base_scorer.py`. Tracked debt, not silence.
2. **`MIN_NORMALIZATION_RAW_MIN`** — a symmetric runtime backstop to `MAX_NORMALIZATION_RAW_MIN=4.5` would make #161 impossible even with a bad file on disk, but NR v2's `raw_min=1.5` is the rollback fallback, so it changes what a rollback restores.

**#72 still blocked on data, not code:** the fitter now correctly refuses — only 66 v4 articles reach 3.75 against a 200 floor. Needs the production-representative historical rescore (playbook §6), not live waiting.

**✅ nature_recovery v4 is DEPLOYED + VALIDATED IN PRODUCTION** (2026-07-10). The op-point 3.75 is now actually wired into `TIER_THRESHOLDS` (was inert, ran at 4.0), and the fix is confirmed in real `filtered_*.jsonl` output. cd v5 + invR v6 normalization refit (percentile) also validated in prod. Full detail: **`memory/project_session_2026_07_10.md`**.

**🔧 Cheap follow-ups from 2026-07-14 (do when convenient):**
1. ~~**sustech v3 op-point drift**~~ **DONE 2026-07-17** — config `tiers` now mirrors `TIER_THRESHOLDS` exactly (medium 4.0; phantom `medium_high: 5.0` removed; both stale "3.0" gatekeeper comments fixed). Verified: `resolve_op_point` returns 4.0 with no drift warning. Source-side only — deployed config copies still carry the old block, but nothing reads them; next deploy syncs.
2. **#7 verify assertion reports ERROR on situla** — correct and honest (no project venv here, so `huggingface_hub` is absent). Fix is `pip install -r requirements.txt` in a venv, not touching the assertion. Verified separately with deps+token: 8/8 PASS, so the v2 Hub claim is sound.
3. **`policy_announcement` cap still unimplemented** (deferred by #161). The vizcacha article will now surface at 4.28 → medium, which is arguably wrong on its merits — the land purchase is only *proposed* ("plantearse adquirir"). Not a regression from the window fix; it's the gap #161 left.

**✅ #62 leakage check DONE 2026-07-16 — cd v5 HOLDS in production, no leak.** Ran the generalized version (the 5 original May examples aren't in the live 10-day window, so scanned for their *shape* instead): tight harm-reckoning/apology/restitution/colonial-reckoning detector over all 80 cd v5 batches on sadalsuud (151,210 unique v5 articles). **624 of 649 harm-reckoning-shaped articles (96%) suppressed below raw 3.5; only 9 at raw≥4.5, and 8 of those are false matches** ("commemorat"/"apology" appearing incidentally in legitimate Discovery content — Ulysses-in-isiZulu translation, American-Revolution book roundups, Indigenous arts). Genuine reckoning content scores LOW: forced-adoption apology 1.81, UK-colonies reparations 1.25, Australia-PM apology 0.67, 1619-Project reparations 1.59 — and `gatekeeper_applied: False` on all, so it's the *learned dimension scores* (discovery_novelty + cross_cultural near zero on reckoning) doing the suppression, not a hard cap. TRAJECTORY-OVER-VOCABULARY holding in prod. The one medium-tier edge case (Rijksmuseum Holocaust *displays*, raw 4.73) is a museum-exhibition/heritage piece, legitimately Discovery-adjacent per ADR-015, not reckoning-shaped — defensible, not a leak. **No `cd_v6_leakage_candidates.jsonl` needed; cd v6 (#23 evidence_quality) stays a note, not real work.** Scan scripts in scratchpad (`cd62_tight.py`, `cd62_detail.py`). **NB: cultural_discovery is NOT otherwise a priority — it is the *reference* solutions v4 copies, not a retrain target.**

**🎯 PRIMARY (next): solutions v4 (#43)** — broaden sustech to governance/community solutions; the ADR-020 validation case (follow cd v5's playbook end-to-end; graduates ADR-020 PROVISIONAL → Accepted). Prompt not yet drafted (`filters/solutions/v4/prompt-compressed.md` planned). **Schedule the oracle batch off-peak** (after ~noon CEST) — see `memory/oracle-pricing-scheduling.md`.

**ovr "no new nature articles" (2026-07-11): diagnosed, NOT broken, no action.** v2's fuller feed was ~90% normalization inflation; fresh-v4 raw scores are under-ranked vs still-in-window inflated v2 rows → self-corrects as v2 ages out of the 10-day window (~Jul 19). Fuller Nature tab = #71 recall lever, not a normalization fix. Full detail: `memory/project_session_2026_07_11.md`.

**Tracked follow-ups (no action until triggered):** (1) **#72** — v4 normalization: no longer must wait ~2wk for 200 live MEDIUM+ — fit at deploy/anytime from a *production-representative historical rescore* (`--min-score 3.75 --filter-version 4.0`; playbook §6 + RUNBOOK "Fit normalization"). Buys cross-lens fairness, not volume; (2) **#71** — v5 recall (harvest false-negatives + high-scorers from saved NexusMind output); (3) blog draft `bias-without-a-self.md` ship steps (user's call, in dev.jeroenveen.nl).

**Housekeeping carried from 2026-07-04 (do first, cheap):**
1. ~~Resolve the phantom-memory-files claim.~~ **DONE 2026-07-05** — all 6 reconstructed + indexed, recap corrected, dangling link resolved. (Optional follow-up: sanity-check `ovr-lens-set-current.md`'s tab mapping against the actual ovr.news repo, which is authoritative.)
2. **Reconstruct the June #51 recap gap** — obituary_detector v3 (commits `87e9962`/`9692bcb`/`dd9c3c4`) has no MEMORY.md entry; add a Session Recap from git if the detail matters, else note it's git-only.
3. **Optional framework pattern** — decide whether to adopt agent-ready-projects v1.10.0's `hypothesis-log.md` (`~/repos/agent-ready-projects/templates/hypothesis-log.md`). Not currently used here.
4. **#23 / #52 are re-scoped, not done** — #23 → cd v6 `evidence_quality`; #52 → class-name drift + #66.

---

**cd v5 post-ship cleanup + solutions v4 prompt drafting** (standing backlog from 2026-05-31; still valid). cd v5 ship is complete; first-week monitoring runs in parallel.

Priority TODOs (in order):
1. ~~**First-week #62 leakage monitoring**~~ **DONE 2026-07-16** — cd v5 holds, no leak (96% of harm-reckoning content suppressed <3.5; genuine apology/reparations articles score 0.67–1.81). See the ✅ entry above. No candidates captured; cd v6 stays a note.
2. **Revise `docs/adr/draft-020-extended-oracle-calibration.md`** per 4-reviewer convergent feedback: mark PROVISIONAL, cut 5→3 oracles default, split soft-penalty into separate ADR (extension of ADR-015), replace "Expected outcome: DS wins" with actual results, address Alternative 5, add conservative-oracle vs consensus-alignment precedence rule.
3. ~~**Solutions v4 prompt drafting**~~ **DONE 2026-07-17 evening** — prompt drafted, review-hardened (2 rounds), calibration batch scored + judged (see pickup above). Remaining: engineer decisions → corpus re-score → training. ADR-020 graduation call after the pipeline lands (capture any divergence in the ADR revision — note the batch DID surface one methodology addition worth recording: a claims-verification agent re-deriving every reported number from disk).
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
- **nature_recovery v2** — DEPLOYED to Hub 2026-04-19 after #44 fix (v2 package referenced v1 imports + repo_id before). <!-- verify: T=$(python3 -c "import configparser;c=configparser.ConfigParser();c.read('config/credentials/secrets.ini');print(c.get('api_keys','huggingface_token',fallback=''))" 2>/dev/null); python3 -c 'import huggingface_hub' 2>/dev/null && [ -n "$T" ] && { PYTHONPATH=. python3 scripts/deployment/verify_filter_package.py --filter filters/nature_recovery/v2 --check-hub --token "$T" >/dev/null 2>&1 && echo PASS || echo FAIL; } || echo ERROR -->
- **nature_recovery v1 normalization** — FIXED (#32 closed 2026-04-09). Refit covers full score range (354 articles, x: 0.10–10.0). gpu-server scorer verified producing differentiated scores.
- **nature_recovery v2 normalization** — FITTED 2026-04-29 on 1,397 v2 production articles (filter_version=2.0, weighted_average≥1.5; raw range 1.50–7.08, p95=4.49). Patched `fit_normalization.py` with `--filter-version` to exclude v1 leftovers (#52 follow-up). Deployed to sadalsuud + gpu-server. <!-- verify: test -f filters/nature_recovery/v2/normalization.json && echo PASS || echo FAIL -->
- **prefilter shape harmonization** (#52) — COMPLETE 2026-04-29. All 7 production filters migrated to declarative shape; review-battery follow-ups also landed (8 commits). Remaining work: class-name drift cleanup batch (sustech V2→V3, NR V1→V2 — gated on NexusMind cross-repo coordination) and potential `_is_excluded` extension for per-category exceptions (deferred to ADR-019 design). See `docs/TODO.md` "Post-#52 Review-Battery Followups" for the full punch-list status. <!-- verify: grep -q "ADR-018" filters/common/base_prefilter.py && grep -q "DOMAIN_EXCLUSIONS" filters/common/base_prefilter.py && echo PASS || echo FAIL -->
- **gpu-server filter discovery dedup + canonical alignment** (2026-04-30, NexusMind 2d3c666 + manual weight migration) — #53 STRUCTURALLY FIXED, with bonus canonical alignment. (1) `FilterLoader.discover_filters()` collapses hyphen/underscore variant collisions to one registered entry (winner = most complete artifacts), alias map covers both API name forms. (2) After the structural fix shipped, weights were moved gpu-server-side from `investment_risk/v6/model/` to `investment-risk/v6/model/` so the registered winner is now `investment-risk` — matches llm-distillery's source-of-truth convention. Discovery flipped: `using 'investment-risk' (most complete artifacts), ignoring ['investment_risk']`; alias map: `{'investment_risk': 'investment-risk'}`. Both API name forms still resolve to the same scorer (verified — same wa returned for both). The earlier band-aid symlink loop (which caused two outages in 24h) is fully retired. **2026-07-04 correction:** gpu-server disk now shows **only `investment_risk/v6/model` (underscore) — the hyphen dir + symlink are gone**, i.e. divergence consolidated to *underscore*, the opposite of the hyphen-winner recorded above (a later cleanup or reprovision superseded the discovery-dedup outcome). #53 is effectively resolved on disk; the two-parallel-dirs symptom is not present. <!-- verify: ssh -o BatchMode=yes -o ConnectTimeout=10 gpu-server 'test -d ~/NexusMind/filters/investment_risk/v6/model && ! test -d ~/NexusMind/filters/investment-risk && echo PASS || echo FAIL' 2>/dev/null || echo ERROR -->
- **raw_weighted_average** — Now passed through gpu-server API → sadalsuud pipeline → filtered output (#36 closed 2026-04-09). Normalization fitting script prefers it to avoid double-normalization.
- **thriving v1** — PAUSED. Candidate for two-stage scoring fix. See `memory/thriving-v1-scoring.md`.
- **#24** — ONNX Runtime INT8 or smaller base model retraining
