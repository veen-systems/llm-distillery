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
- if [checking whether a remote job is running with `pgrep -f "<pattern>"`], then [it matches your own ssh command line too — verify by footprint (GPU mem / large RSS / log growth), not name-match] — promoted from gotcha-log 2026-07-09
- if [a comment asserts a property the code depends on], then [TEST the property — a sentence is not a control. "The dirty-check guarantees HEAD == worktree" was false (`git diff --quiet <paths>` is worktree-vs-INDEX; `git add` defeats it) and shipped a deploy that could stamp a revision naming bytes production wasn't running] — promoted from gotcha-log 2026-07-14 (recurred 2026-07-17: two fresh Fix B "by construction"/"nowhere else to update" comments falsified by contract review — one became the runtime push-completeness assertion)
- if [writing a test for a function], then [IMPORT the function, never re-implement it — a private copy in `test_normalization_invariant.py` drifted from its subject *within the same commit*, omitting the ambiguity check added beside it] — promoted from gotcha-log 2026-07-14
- if [a review finding is dramatic], then [treat it as a hypothesis and check it against the ADRs before acting — round 1's top finding was a misread of ADR-014's documented design, and an agent independently reached the same wrong conclusion. Two models agreeing is not evidence] — promoted from gotcha-log 2026-07-14
- if [running a review at all], then [run TWO rounds — round 1 reviews the code, round 2 reviews the fixes, and 4 of round 2's 8 findings were defects inside round 1's fixes (including the test meant to catch them)] — promoted from gotcha-log 2026-07-14 (pattern held an EIGHTH consecutive time 2026-07-17 evening: solutions v4 prompt round-2 found 3 defects inside round-1's fixes — opinion-vs-router contradiction, unpropagated community-gov rule, conflicting proposed-bill anchor)
- if [adding ANY control — hook, gate, cap, assertion, guard, test], then [watch it fail before trusting it; a control never observed failing is decoration. For tests: run against the OLD code and confirm they fail — AND confirm CI actually feeds them an input that exercises the assertion; a guarded `if field is not None:` over a corpus that never carries the field is dead code] — promoted from gotcha-log 2026-07-14 (5 dead controls in one session; recurred 2026-07-17: the sample_min assertion added by Fix A hardening ran on zero inputs)
- if [a check reports FAIL], then [ask whether it FAILED or couldn't RUN — `cmd && echo PASS || echo FAIL` collapses the two, and a check that cries wolf trains you to skim past it. Let the *claim* decide PASS/FAIL and let transport/deps/creds surface ERROR] — promoted from gotcha-log 2026-07-14
- if [a diagnosis is backed by a workaround that works], then [distrust it — an error whose workaround produces green results never falsifies itself. Test the original path directly] — promoted from gotcha-log 2026-07-14 (sadalsuud hop kept "no gpu-server key from situla" alive; engineer caught it)
- if [a model looks like it's scoring badly in production], then [check `normalization.json`'s fit threshold FIRST — #161 was v2 scoring 2.2–3.3 *correctly* and a CDF fitted at raw>=1.5 inflating it to 5.2–8.3] — promoted from gotcha-log 2026-07-14
- if [shipping a fresh filter version that needs cross-filter normalization], then [fit `normalization.json` at deploy from a *production-representative historical* rescore — do NOT ship raw and wait weeks for live accumulation; a raw filter is under-ranked/under-shown against every normalized lens (ovr `canonical-lens.ts` + `displayScoreThreshold`). Must be production base-rate, not the enriched val set; `MIN_NORMALIZATION_ARTICLES=200` rejects thin fits. Playbook §6] — promoted from gotcha-log 2026-07-11

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
- Solutions broadening v4 — CALIBRATION BATCH DONE 2026-07-17 evening. Forks signed off (2026-05-05): C (broaden ST v3 in place), combine ST v3 + foresight v1 corpora, foresight retired when v4 supersedes ST v3. Prompt drafted + review-hardened (2 rounds); 350-article batch scored by DeepSeek + Gemini (ADR-020 method, $1.00); both judges → DeepSeek. Awaiting engineer sign-off on 4 decisions (see `filters/sustainability_technology/v4/calibration_report.md`) before the ~$10-15 corpus re-score. <!-- verify: test -f filters/sustainability_technology/v4/prompt-compressed.md && test -f filters/sustainability_technology/v4/calibration_report.md && echo PASS || echo FAIL -->
- Normalization must be fitted at/above the operating point — enforced 2026-07-14 (`33fba44`). `fit_normalization.py` resolves the op-point from `TIER_THRESHOLDS` (lowest non-zero) and **refuses** `--min-score` below it (escape: `--allow-below-op-point`). Fitting below it maps sub-visibility content into the visible band — the actual root cause of NexusMind#161, not the model. Warns on config/code drift (already found one: sustech v3). Detail: `project_session_2026_07_14.md`. <!-- verify: PYTHONPATH=. python3 scripts/normalization/fit_normalization.py --filter filters/nature_recovery/v4 --data-dir /nonexistent --min-score 1.5 2>&1 | grep -q "is below the operating point 3.75" && echo PASS || echo FAIL -->
- `climate_doom` runtime cap **RETIRED** 2026-07-14 (NexusMind `1dd5e49`) — 3 production bites, 3 false positives, 0 saves. All three were the trigger word in a *non-doom construction* a polarity-blind regex can't see: `evitar su extinción` (prevent), `en peligro crítico de extinción` (IUCN label), `deforestation-free` (`\b` matches across the hyphen). The earlier same-day override-window widening (`8681efa`) rescued two and missed the third entirely. **The `recovery_evidence` gatekeeper (<3 → cap 3.5, below the 3.75 op-point) already does this job semantically** — doom scores recovery_evidence 0.07–1.08, the coffee FP scored 4.58. Registry is empty but the mechanism is retained. Accepted trade: real doom is no longer capped either (model scores it 0.36–1.89, below op-point). <!-- verify: grep -qF 'List[re.Pattern]]]] = {}' ~/repos/veen-systems/NexusMind/src/scoring/cap_triggers.py && ! grep -qF '"nature_recovery": [(' ~/repos/veen-systems/NexusMind/src/scoring/cap_triggers.py && echo PASS || echo FAIL -->
- Deploy freshness gate, hash and dirty-check all derive from ONE list — `SCORER_PATHS` in NexusMind's `deploy_filters.sh` (`4e25934` → `a95c3d6` → `7ef6029`). Three separate bugs from restating the deployed set: (1) the hash covered `src/scoring/` but the gate didn't → scoring-only commits silently never deployed while reporting "already in sync"; (2) `deploy/gpu-server/{main.py,scorer-start.sh}` were hashed AND scp'd but never gated; (3) the dirty-check used `git diff --quiet <paths>` (worktree-vs-INDEX), so `git add` defeated it — the hash then named bytes production wasn't running. The hash is now built by ITERATING `SCORER_PATHS`, so gate/hash/deploy cannot drift apart. **Validated in production 2026-07-14 20:08**: the gate auto-pulled a `src/scoring`-only change — the exact case it used to miss. <!-- verify: D=~/repos/veen-systems/NexusMind/scripts/deploy_filters.sh; grep -qF 'SCORER_PATHS=(' $D && grep -qF 'for scorer_path in "${SCORER_PATHS[@]}"' $D && grep -qF 'deploy/gpu-server/main.py' $D && ! grep -qF 'HASH_FILTERS=' $D && grep -qF 'git diff --quiet HEAD -- "${SCORER_PATHS[@]}"' $D && echo PASS || echo FAIL -->
- **Deploy ships the git-archive of HEAD — Fix B EXECUTED, DEPLOYED, validated live 2026-07-17** (NexusMind `dcf6fc8`, on top of the `SCORER_PATHS` unification below). `git archive HEAD` → staging dir → all rsync/scp from staging: untracked/gitignored/edited files can no longer ship (closes the round-3 untracked + round-4 gitignored-straggler gaps; supersedes+deletes held `7e525ee`). Untracked operator gate (filters only `filters/**/model/`) shared by auto-pull guard + main gate, fail-closed on git error with sentinel-aware diagnostics; runtime push-completeness assertion; smoke fixtures in `SCORER_PATHS`, shipped from staging; component-form rsync excludes; `.gitignore` `models/` scoped to `/models/`. Carve-outs (documented, deliberate): tracked `*/model/` configs are hashed-but-never-shipped (out-of-band weight channel — sha256 diff vs gpu-server came back DIRTY, so shipping repo copies would overwrite Hub-provenance files; settled, don't "fix"); `CODE_REVISION` is shipped-but-not-hashed. Validated by the canonical 4h chain itself (ExecStartPre status=0, hash `6f0458f3…` round-tripped). Harness fixture: `tests/deploy_dryrun/` (52 assertions). OnFailure→email alert live (chain's Gmail sender, no new services). <!-- verify: D=~/repos/veen-systems/NexusMind; grep -qF 'git archive HEAD' $D/scripts/deploy_filters.sh && grep -qF 'PUSHED+=' $D/scripts/deploy_filters.sh && test -x $D/tests/deploy_dryrun/setup_and_run.sh && grep -qF '/models/' $D/.gitignore && ssh -o BatchMode=yes -o ConnectTimeout=10 sadalsuud 'systemctl show nexusmind.service -p OnFailure | grep -q nexusmind-alert' && echo PASS || echo FAIL -->
- The #44 commit-msg gate is live for the first time — fixed 2026-07-14 (`9b6126d`): was mode 100644 (git silently ignores non-executable hooks) and called bare `python`. Enable per clone: `git config core.hooksPath .githooks`. <!-- verify: [ "$(git ls-files -s .githooks/commit-msg | cut -d' ' -f1)" = "100755" ] && echo PASS || echo FAIL -->
- cultural_discovery v5 DEPLOYED 2026-05-31 — resolves #62 discovery-lens leakage. Val MAE 0.697 (v4 was 0.74). Soft-penalty F/G/H/I/K flags (historical_harm_reckoning, commemoration_memorial, perpetrator_biography, decline_loss, launch_announcement). DeepSeek V4 Flash oracle (first non-Gemini lineage in production, ~7x cheaper). End-to-end verified: Pope apology 9.65→2.31, Indus/Sumer 9.12 (gradient preserved). v4 deleted from gpu-server post-verification; still in llm-distillery + git + HF Hub for rollback. **Provisional reference example for ADR-020 methodology** (multi-oracle batch + agent judging) and DeepSeek-as-default-oracle; solutions v4 is the validation case. <!-- verify: ssh -o BatchMode=yes -o ConnectTimeout=10 gpu-server 'test -d ~/NexusMind/filters/cultural_discovery/v5/model && echo PASS || echo FAIL' 2>/dev/null || echo ERROR -->

## Session pointers

Full per-session narratives live below the auto-loading cliff (read on demand). Newest first.

- [2026-07-17 evening](project_session_2026_07_17_evening.md) — **Solutions v4 (#43): scaffold → calibrated in one session.** Foresight/Solutions mixing confirmed+quantified (tab ~91% foresight-fed, 934 vs 88/24h); v4 prompt drafted + 2 review rounds (round-2 pattern held an 8th time); 350-article calibration batch scored by BOTH oracles ($1.00, ADR-020 method); two judges → DeepSeek; pure-tech ≥7.0 gate empirically unsatisfiable. Stopped at engineer sign-off. Record: `filters/sustainability_technology/v4/calibration_report.md`.
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

## Next Session Pickup (updated 2026-07-17 evening)

**🎯 solutions v4 (#43): calibration DONE, waiting on 4 ENGINEER DECISIONS** — all listed in
`filters/sustainability_technology/v4/calibration_report.md` "Open engineer decisions":
(1) ratify DeepSeek as v4 oracle (both ADR-020 judges recommend it, 19-7-4 editorial verdict);
(2) accept the thinner-but-cleaner Solutions tab (foresight currently feeds ~91% of the tab —
934 vs 88 visible/24h — but judges found the Step-1 kills are mostly correct lens-bleed
rejection); (3) rewrite the empirically-unsatisfiable pure-tech ≥7.0 gate (rank-based
suggested) + pick weighting (post-hoc — labels are per-dim, weights are runtime, does NOT
block re-score); (4) then apply the 4 small prompt/pipeline fixes in the report (router-crisis
reinforcement, governance-recall line, corporate_pr encouragement, scrape-junk ingestion check)
and run the **full corpus re-score**: ST v3 (10.6K) + foresight v1 (3.5K), DeepSeek,
**off-peak after ~noon CEST** (`memory/oracle-pricing-scheduling.md`), ~$10-15. Then training
per the playbook. ADR-020 PROVISIONAL→Accepted graduation call comes after the pipeline lands.

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

**🎯 PRIMARY (next): solutions v4 (#43)** — broaden sustech to governance/community solutions; the ADR-020 validation case (follow cd v5's playbook end-to-end; graduates ADR-020 PROVISIONAL → Accepted). Prompt not yet drafted (`filters/sustainability_technology/v4/prompt-compressed.md` planned). **Schedule the oracle batch off-peak** (after ~noon CEST) — see `memory/oracle-pricing-scheduling.md`.

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
