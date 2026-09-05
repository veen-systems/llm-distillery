# Runbook

Operational how-to for deployment, training, and scoring. For project identity and hard constraints, see `CLAUDE.md`. For architectural decisions, see `docs/adr/README.md`.

---

## Deployment to NexusMind

One-time per clone, enable the commit-msg hook that blocks unverified deploy claims
(llm-distillery#44 background):

```bash
git config core.hooksPath .githooks
```

### 1. Preflight: verify the filter package

```bash
PYTHONPATH=. python scripts/deployment/verify_filter_package.py \
    --filter filters/{name}/v{N} --check-hub
```

Eight checks: imports match dir version, `repo_id` matches dir version, `config.yaml`
`filter.version` matches, `base_scorer.FILTER_VERSION` matches, Hub repo exists, Hub
`last_modified` ≥ local `model/adapter_model.safetensors` mtime. Catches the
v_new-config × v_old-weights class (#44).

### 2. Upload to HuggingFace Hub

```bash
PYTHONPATH=. python scripts/deployment/upload_to_huggingface.py \
    --filter filters/{name}/v{N} \
    --repo-name jeergrvgreg/{name}-filter-v{N} \
    --token $HF_TOKEN --private
```

Script does a post-upload `PeftModel.from_pretrained()` verification. If that
fails, check adapter format (must be OLD key format — ADR-007). Re-run step 1 with
`--check-hub` before writing any "deployed" claim in commits or memory.

### 3. Copy to NexusMind checkout + commit

```bash
# ALWAYS --dry-run first and read the file list (see the drift warning below).
# On Linux the two roots must be exported; the defaults are the Windows box.
# HF_TOKEN is required or the Hub freshness gate fails as "repo not found"
# (the Hub returns 404 for a private repo a token cannot see).
export HF_TOKEN=$(python -c "import configparser;c=configparser.ConfigParser();c.read('config/credentials/secrets.ini');print(c['api_keys']['huggingface_token'].strip())")
DISTILLERY_ROOT=$PWD NEXUSMIND_ROOT=/home/jeroen/repos/veen-systems/NexusMind \
  bash scripts/deploy_to_nexusmind.sh {name} v{N} --dry-run

# then without --dry-run, or PowerShell:
.\scripts\deploy_to_nexusmind.ps1 {name} v{N}
```

> **Diff before you sync.** The script overwrites NexusMind's copies and honours
> only `.nexusmind-owns`, which is **empty by design** — so a NexusMind-side
> change that never came upstream is deleted silently, not reported. After the
> `--dry-run`, run `git -C $NEXUSMIND_ROOT diff --stat` and account for every
> file you did not edit. Production-behaviour additions belong back in
> llm-distillery *first*, so the sync preserves them; cosmetic drift can be let
> go. On 2026-08-03 this caught three `investment_risk v6` source blocks
> (`arxiv`/`mastodon_`/`bluesky`) that had been production-only since
> 2026-05-18 — see llm-distillery#93.

> ⚠️ **`--dry-run` still writes.** It copies the files and skips only the
> `git add`/`commit`/`push`, so it dirties the NexusMind working tree. That matters
> when a parallel session shares that checkout: revert with **explicit paths**
> (`git -C $NEXUSMIND_ROOT checkout -- <path> <path>`), never a bare
> `git checkout .` (2026-08-13).

> ⚠️ **Since 2026-08-13 the deploy needs ssh reachability to `gpu-server`.**
> Pre-flight guard D probes it for
> `filters/{name}/v{N}/model/adapter_model.safetensors` and **fails closed** if it
> cannot ask — because `deploy_filters.sh` excludes `model/` from both rsync passes,
> so the code never carries weights and a weightless *highest* version stops the
> scorer **starting**, which costs the whole cycle for all six filters. Pre-place the
> adapter first (checklist item 5 / #67), or pass `--weights-preplaced` once you have
> confirmed it by hand:
> `ssh gpu-server 'ls -l ~/NexusMind/filters/{name}/v{N}/model/adapter_model.safetensors'`.

Then `cd $NEXUSMIND_ROOT && git push origin main` — **on a `chore/` branch and a PR
if the target repo uses them**; NexusMind does, and two commits went straight to its
`main` on 2026-08-13 for want of checking.

### 4. Deploy to gpu-server (via sadalsuud)

```bash
# Wrapper that SSHes to sadalsuud, pulls, and runs deploy_filters.sh there.
# Refuses if your local NexusMind has unpushed filter commits.
bash scripts/remote_deploy.sh
```

The wrapped `NexusMind/scripts/deploy_filters.sh` (Fix B, 2026-07-17: ships the
`git archive` of HEAD, never the working tree):
- Verifies local HEAD matches `origin/$CURRENT_BRANCH` for the full `SCORER_PATHS` set (fails closed on origin-unreachable; set `SKIP_ORIGIN_CHECK=1` to override).
- Blocks on uncommitted OR untracked files under `SCORER_PATHS` (untracked `*/model/` configs exempt — out-of-band channel).
- rsyncs a git-archive staging tree of HEAD to gpu-server (model/ directories deliberately excluded — weights live out-of-band).
- Restarts `nexusmind-scorer` systemd service.
- Round-trips a CODE_REVISION hash via `/health`, then asserts push-completeness (every `SCORER_PATHS` entry shipped).
- Runs a post-deploy smoke test (`deploy/smoke_test_articles.jsonl`) — POSTs known positives, asserts per-fixture `weighted_average` bounds. Catches "weights loaded but nonsense."

**⚠ Committed-only deploys (Fix B).** A filter package that is file-copied onto
sadalsuud but not committed+pushed no longer ships silently — it BLOCKS the
every-4h pipeline cycle (fail-closed by design) until committed or removed.
Deploy flow is now strictly: commit → push → pull on sadalsuud → deploy. A
blocked gate fires the `nexusmind-alert@` EMAIL alert (sent via the chain's
existing Gmail sender — FluxusSource `[email_credentials]` on sadalsuud; 3h
burst guard; alerts also append to `data/alerts.log`).

**Why not run `deploy_filters.sh` directly from the workstation?** Its rsync fails
intermittently from Windows Git Bash with `dup() in/out/err failed`. `remote_deploy.sh`
sidesteps by running it on sadalsuud (Linux) instead.

### 5. Monitor

```bash
ssh gpu-server "journalctl -u nexusmind-scorer -f"
# In NexusMind
python scripts/run_filters.py --filter {name} --hub --max-items 50
```

---

## Oracle Scoring

⛔ **`--llm` DEFAULTS TO `claude`, AND THERE ARE TWO ORACLE PATHS, NOT ONE.** Corrected
2026-08-29: this section documented neither fact for months.

- `ground_truth.batch_scorer` takes `--llm`, whose choices are
  **`claude` | `gemini` | `gemini-pro` | `gemini-flash` | `gpt4`**, defaulting to
  **`claude`**. ⚠️ **DeepSeek is not among them** — `grep -rln -i deepseek ground_truth/`
  hits only `text_cleaning.py`. Omitting the flag does not give you the filter's oracle;
  it gives you Claude.
- **DeepSeek runs through a different script entirely**, `scripts/score_deepseek_production.py`,
  written for the `cultural_discovery` v5 retrain (ADR-020 methodology). It is not a flag on
  the command above and it does not share its resume/sampling behaviour.

⚠️ **So "the oracle" is a per-filter fact, not a default.** `memory/cd-v5-reference-status.md`
covers the DeepSeek path; the cost arithmetic and why the comparison is not a rate-card lookup
is `memory/oracle-pricing-scheduling.md`. ⚠️ **For `human_thriving` v8 the oracle choice is
still OPEN** — §9 question 1 of `docs/HUMAN_THRIVING_V8_PLAN.md`: measured on n=3 Gemini is the
**stricter** arm on class A (caps 3/10 vs DeepSeek 1/10), against DeepSeek being ~7× cheaper.
Do not resolve it by reading a default out of this file.

```bash
# Validation run (~100 articles, Phase 3). NAME THE PROVIDER — the default is claude.
python -m ground_truth.batch_scorer \
    --filter filters/{name}/v{N} --llm gemini-flash \
    --source datasets/raw/master_dataset.jsonl --target-count 100
#                      ^^^^^^^^^^^^ THIS FILTER's oracle, not a house default

# Score articles (full run, Phase 5)
python -m ground_truth.batch_scorer \
    --filter filters/{name}/v{N} --llm gemini-flash \
    --source datasets/raw/master_dataset.jsonl

# The DeepSeek oracle — a separate script, not a --llm value
PYTHONPATH=. python scripts/score_deepseek_production.py \
    --input datasets/scored/{name}_v{N}_articles.jsonl \
    --output datasets/scored/{name}_v{N}_deepseek.jsonl --concurrency 15

# Multi-run averaging (for prompt-sensitive filters)
# ⛔ --runs takes DIRECTORIES, not files, and it joins on `url`. The file-list form
#    documented here until 2026-09-01 exits 1 with "Run directory not found".
python scripts/oracle/average_oracle_runs.py \
    --runs datasets/scored/{name}_v{N}_run1/ datasets/scored/{name}_v{N}_run2/ datasets/scored/{name}_v{N}_run3/ \
    --output datasets/scored/{name}_v{N}/ --filter-name {name}

# ⛔ For a SCOPE-GATED prompt (human_thriving v8), use this instead. It joins on `id`,
#    KEEPS the per-run scope verdicts, and prints the flip rate the runbook demands below.
PYTHONPATH=. python3 scripts/oracle/aggregate_k_runs.py \
    --runs run1.jsonl run2.jsonl run3.jsonl \
    --config filters/{name}/v{N}/config.yaml --out datasets/scored/{name}_v{N}.jsonl
```

⛔ **AVERAGING DOES NOT REDUCE EVERY KIND OF ORACLE VARIANCE, AND ON A SCOPE-GATED PROMPT IT
HIDES THE VARIANCE THAT MATTERS (#135).** A prompt whose scope verdict is a **binary that
zeroes every dimension** is a step function, not a noisy continuum: `1/√k` cannot touch a
Bernoulli. Measured on the `human_thriving` v8 prompt — **13% of identical re-runs flip the
gate, median |Δ| 3.750, while gate-stable rows move 0.100**. Gate A missed it precisely
*because* it averaged k=3. **Before averaging, check whether the prompt has a binary gate;
if it does, report the flip RATE, not the mean.**

⛔ **And `average_oracle_runs.py` cannot report it, because it DELETES the evidence.** It
replaces the analysis object with six averaged numbers, so `scope_verdict`,
`dominant_subject`, `content_type` and every evidence quote are gone — after it runs, the
flip rate is unmeasurable. It also joins on `url` (the scorer's own resume key is `id`) and
silently keeps only rows present in every run. `scripts/oracle/aggregate_k_runs.py` fixes all
three and writes **both** aggregates: `weighted_mean_all` and `weighted_mean_major` (the mean
over only the runs agreeing with the majority verdict). ⚠️ **They are not close on a flipping
row** — measured 2026-09-01 on 8 class-A rows, they differ by a median of **1.30** weighted
points, enough to move a row across the operating point. Choose `--aggregate` on the flip
rate the tool prints, and keep the per-run files.

---

## Training

### Prepare data

```bash
# ⛔ --input / --output-dir. There is NO --data-source flag (0 occurrences in the script);
#    the form documented here until 2026-09-01 dies on argparse.
# ⛔ --filter's config.yaml `filter.name` decides which analysis field is read. Point it at a
#    filter whose name does not match the labels and it writes 0 examples to every split,
#    prints "TRAINING DATA PREPARATION COMPLETE", and exits 0 (measured 2026-09-01). Its own
#    docstring: "Articles without analysis are silently skipped; missing dimensions default
#    to score 0" -- so a RENAMED dimension becomes a silent column of zeros.
python training/prepare_data.py \
    --filter filters/{name}/v{N} \
    --input datasets/scored/{name}_v{N}.jsonl \
    --output-dir datasets/training/{name}_v{N}

# Validate splits
python training/validate_training_data.py \
    --data-dir datasets/training/{name}_v{N}
```

### Train on GPU

Two hosts. **`b650-gpu` is the training node** (RTX 3090 Ti 24 GB, ~1.26 s/it at batch 8;
`memory/b650-gpu.md`) and ends Ollama-vs-training contention on gpu-server. It is NOT a
production box — ⛔ never diff a b650 replay against stored production scores without
matching production's device first (CPU→CUDA is worth 3 flips at 4.5).

```bash
# 1. Ship code + data. b650's ~/llm-distillery is NOT a git checkout, so send tracked
#    files only -- then what runs there is exactly what is committed. Verify by md5.
git ls-files training filters/common filters/{name}/v{N}/config.yaml requirements.txt \
  > /tmp/shiplist.txt
rsync -az --files-from=/tmp/shiplist.txt ./ b650-gpu:~/llm-distillery/
rsync -az datasets/training/{name}_v{N}/ b650-gpu:~/llm-distillery/datasets/training/{name}_v{N}/

# 2. Train. venv-prodparity, NOT venv -- the latter is CPU-only (triton cannot build).
ssh b650-gpu
cd ~/llm-distillery
export PYTHONPATH=.
export HF_HUB_OFFLINE=1        # google/gemma-3-1b-pt is already cached there

venv-prodparity/bin/python training/train.py \
    --filter filters/{name}/v{N} \
    --data-dir datasets/training/{name}_v{N} \
    --output-dir filters/{name}/v{N} \
    --epochs 6 --batch-size 8 --seed 42 \
    --select-metric recall_medium
```

⛔ **`--output-dir` has its trailing `/model` STRIPPED** — pass the filter dir; the script
appends `model/` itself.

**Checkpoint selection — read this before choosing flags.**

- `--select-metric` is `recall_at_20` (top-k ranking) or `recall_medium` (recall on MEDIUM+,
  i.e. `1 - FN-rate`). ⛔ **Never select on aggregate MAE**: on an 85–95% floor a
  floor-predictor wins it (ADR-023). It was the *silent* fallback until `1878e7b`, when
  `--select-metric` was inert because the metrics weights were gated on `--sample-weight-scale`
  — four deployed filters were selected on MAE as a result.
- ⚠️ **`recall_medium`'s resolution is `1 / n_positives` in val.** With a thin positive count it
  saturates and the strict `>` tie-break silently keeps the earliest tied epoch
  (llm-distillery#144). Check `training_history.json` per epoch rather than trusting the
  selected one.
- `--medium-threshold` overrides the MEDIUM+ boundary. It is resolved from `base_scorer.py`
  `TIER_THRESHOLDS` first, then `config.yaml` (both `scoring.tiers` and
  `scoring.tier_thresholds`, `threshold` or `min_score`). ⛔ **It RAISES rather than
  defaulting** — a plausible-but-wrong boundary decides which checkpoint ships and is
  indistinguishable afterwards from a correct one. If it raises, pass the flag.
- `--sample-weight-scale` (default 0) weights the LOSS by oracle score. It no longer has any
  effect on which metrics are computed.

**Seed 42 is not bit-reproducible on CUDA** — measured 0.5601 vs 0.5605 val MAE for the same
epoch across two identical runs. Do not read a 4th-decimal difference as an effect (#95 family).

**Pull the provenance back and commit it.** The weights are gitignored as large model
checkpoints (`.gitignore` § *Model checkpoints (large files)*; ⚠️ **not** #97, the TDM assessment) and live only on
the training host, so `training_history.json` + `training_metadata.json` ARE the traceability:

```bash
rsync -az b650-gpu:'~/llm-distillery/filters/{name}/v{N}/training_*.json' filters/{name}/v{N}/
```

Then register the run in `experiments/registry.jsonl` and run
`python3 scripts/verification/check_experiment_registry.py` — it rejects any metric whose
string does not appear verbatim in a cited artifact.

## Deriving an operating point (phase 8)

⛔ **Do not pick an op-point by looking for the "best" number.** Sweep it and read the
SHAPE of the trade, because the shape is what decides. The method, from
`human_thriving v8` (`docs/decisions/2026-09-05-v8-op-point.md`, `EXP-017`/`EXP-025`):

1. Partition the rows the PREVIOUS filter surfaced by what the new oracle says about them:
   **junk** (old ≥ op, new < op) and **good** (both ≥ op). `phase_c_outcome.py` is the
   worked example. ⛔ Never judge a new filter by aggregate recall against the fleet's —
   two filters with different positive classes give two quantities with one name (v7 vs v8
   Jaccard **0.246** on identical rows).
2. Sweep the bar and print the STEP between rows: how many good articles each step costs
   and how many junk ones it removes.
3. ⭐ **Find where the curve bends.** v8's bends at 3.50 (−3 good buys −11 junk); from 3.75
   up every step is ~1 good per 1 junk. In the 1:1 region only the loss function decides,
   and ADR-023 sends a 1:1 trade to specificity. **The bars just above the bend are the
   worst place to spend** — they buy volume at exactly par.
4. Decide on the arm that SHIPS. If the filter has a `calibration.json`, that is the
   calibrated arm — `filter_base_scorer._process_raw_scores` calibrates BEFORE computing
   the weighted average that `_assign_tier` sees. **4.5 calibrated is a stricter bar than
   4.5 raw** (17 rows vs 26 on v8's split); carrying a number across arms silently tightens it.
5. ⛔ **An op-point cannot exceed `MAX_NORMALIZATION_RAW_MIN` (4.5).** Strict `>`, so 4.5 is
   accepted with zero margin and the fitter refuses anything above it.
6. Verify by EXECUTING `_assign_tier` either side of the boundary, never by re-reading
   `config.yaml` — that block is documentation and editing it alone is a no-op (NM#161, NM#205).

⚠️ **A design-weighted split needs a weighted arm before any share is quoted.** v8's is
25.1×; weighting moved junk-removed at most +2.44 pp but specificity +2.65 pp and recall
−8.51 pp, so which quantity you quote decides how much the weighting appears to matter.

## Smoke-testing a filter package before the deploy gate

`scripts/gate/v8_smoke_test.py` is the pattern: **does an article go in and a well-formed,
calibrated, tiered result come out?** It is much cheaper than the ADR-021 gate and answers a
different question — mechanism, not accuracy. Run it on the host that has the weights; on
any other host it exits **2 as CANNOT VERIFY**, because a missing artifact is not a broken
scorer and reporting it as one is how a red suite gets ignored.

⚠️ **Two false alarms it converts into checked facts, so nobody re-diagnoses them:**
loading a base model for sequence classification prints `score.weight | MISSING ... newly
initialized` — that is the BASE checkpoint, and PEFT supplies the trained head from the
adapter a moment later; and the LoRA keys must be OLD format (`.lora_A.weight`).
⛔ **Assert against the object that HOLDS the thing.** The first version of that script
checked `scorer.calibration` and failed — calibration lives on `scorer.stage2_scorer`, so
the check was pointed where it could never succeed.

## The Stage-1 probe threshold is NOT the operating point

⛔ **Two different numbers, opposite loss functions, and they get confused.** The op-point is
on the STUDENT's weighted score and decides visibility; ADR-023 optimises **specificity**
there. The Stage-1 threshold decides ROUTING, and ADR-023 explicitly **does not apply** — the
probe is a recall-safe screen where the false negative is the expensive error
(`train_probe.py --objective recall`).

⛔ **On every filter except `human_thriving v8`, `hybrid_inference.stage1.threshold` in
`config.yaml` is INERT** (verified 2026-08-21). The runtime value is a module-level
`DEFAULT_THRESHOLD` in each `inference_hybrid.py`, and on two filters the config disagrees
with it — `nature_recovery v4` ships 3.225 against a runtime **0.75**, `thriving v1` ships
null against 2.25. Do not cite the config value as the operating threshold and do not "fix"
production by editing it. v8 wires config to runtime and raises if the block is missing.

⚠️ **Tightening the screen is not a free compute win.** Measured: at the adopted ~89%
routing the two-stage design saves **1.52%** (`2.345 + 0.89 × 24.740 = 24.36` against
24.740), break-even is ~53–57% routing, and `EXP-021` found no Stage-2 cost constraint at
all — the pipeline runs at a **5.57% duty cycle** and `score` is 53.5% of blocking wall
time against story dedup's 42.4%. And the non-compute cost is unwritten elsewhere: the
probe's own numbers become the published scores for every screened-out row, and a
recall-objective probe is biased high. **If it is ever tightened, pair it with a
regression-objective probe.**

⚠️ **Verbatim-present is not the same as correct, and the registry checker cannot tell them
apart.** It traces `metrics` only, never `population`, so a wrong count in `population` passes
forever — that happened on 2026-09-05 (`sites_examined.quantified_orderings: 3` where the tool
reported 2). Also run
**`python3 scripts/verification/check_claim_shapes.py`**, which reads the evidence and decision
records for four defect SHAPES: a no-difference-over-a-grid claim with no reachable range, a
zero-width interval, a quantified ordering with no band, and an analysis reading a
design-weighted population without its weights. Both run automatically from
`memory/MEMORY.md`'s `<!-- verify: -->` annotations via
`python3 scripts/verification/run_verify_annotations.py`.

<details><summary>Legacy: training on gpu-server</summary>

```bash
scp -r datasets/training/{name}_v{N}/ gpu-server:~/llm-distillery/datasets/training/
ssh gpu-server
cd ~/llm-distillery
source ~/gpu-server/nexusmind-scorer/venv/bin/activate
export PYTHONPATH=.
export HF_HUB_OFFLINE=1
python training/train.py --filter filters/{name}/v{N} \
    --data-dir datasets/training/{name}_v{N} --output-dir filters/{name}/v{N}
```

gpu-server has 16 GB and also serves Ollama; prefer b650 for training.
</details>

### Fit calibration (after training)

```bash
PYTHONPATH=. python scripts/calibration/fit_calibration.py \
    --filter filters/{name}/v{N} \
    --data-dir datasets/training/{name}_v{N} \
    --test-data datasets/training/{name}_v{N}/test.jsonl \
    --no-config-update
```

Writes `calibration.json`. Commit it with the filter package.

⛔ **PASS `--no-config-update` UNLESS `normalization.json` ALREADY EXISTS.** By default this
script also computes `10.0 / weighted_max` and **edits `config.yaml`'s
`score_scale_factor`** as a side effect. `score_scale_factor` is superseded by percentile
normalization (ADR-014), and a filter shipping a factor ≠ 1.0 with **no** `normalization.json`
silently stretches every score and defeats the gatekeeper design (FILTER_PLAYBOOK §8).
Measured on `human_thriving v8`, 2026-09-04: it computed **1.3787** — a 1.38× stretch on a
filter with no normalization fitted. The flag is **opt-in**, so a run that omits it gets the
edit. ⚠️ The log line prints `(10.0 / 7.25 …)`, which is not an equation — that `7.25` is a
2-decimal rendering of 7.2532.

⛔ **Judge the result on recall + specificity, never on MAE (ADR-023), and expect the
op-point to move.** Isotonic calibration is close to a monotone rescale: on v8 the raw and
calibrated arms were the *same ranker* (Spearman 0.9977, AUC 0.9474 → 0.9488) yet the
inherited 4.5 bar flagged **17** rows calibrated where it flagged **26** raw. **Re-derive the
op-point on the calibrated scale at phase 8** — carrying a raw-scale threshold across
silently tightens the filter. Worked example:
`docs/evidence/2026-09-04-v8-probe-calibration/`.

### Fit normalization (cross-filter comparability, ADR-014)

A fresh version ships with **no** `normalization.json` and emits RAW `weighted_average`, while every other lens emits *normalized* scores — so the new version is under-ranked/under-shown in the shared feed until normalization is fitted (see FILTER_PLAYBOOK §6). Fit it **at deploy time** by rescoring a *production-representative historical* corpus rather than waiting weeks for live production to accumulate:

```bash
# Fit from production filtered output (sadalsuud). --min-score = this filter's
# MEDIUM tier threshold (e.g. 3.75 for nature_recovery v4, 4.0 for most).
# --filter-version isolates the current version's rows from older leftovers.
PYTHONPATH=. python3 scripts/normalization/fit_normalization.py \
    --filter filters/{name}/v{N} --ssh sadalsuud \
    --remote-dir /home/jeroen/local_dev/NexusMind/data/filtered/{name} \
    --min-score {medium_threshold} --filter-version {N}.0
```

Requirements (enforced by `production_scorer.py` guards — a fit that violates them is silently ignored and the filter stays raw):
- **≥200 MEDIUM+ articles** (`MIN_NORMALIZATION_ARTICLES`). A needle filter at ~0.3% base rate needs ~145K rescored articles to reach 200 — rescore a large historical harvest (FluxusSource `~/local_dev/FluxusSource/data`) with the deployed model to get there without waiting.
- **At the production base rate**, NOT the enriched training/val set (enrichment skews the CDF harsh; `raw_min > 4.5` is also rejected, `MAX_NORMALIZATION_RAW_MIN`).

Writes `normalization.json` to the filter dir; commit it and deploy to both servers. Refit per version.

---

## Filter Development Lifecycle

The phases below, in order — `6b` is lettered rather than numbered because other documents cite these numbers (the v8 plan and `CLAUDE.md` both say "phase 5"), so renumbering costs more than it buys. See `docs/agents/filter-development-guide.md` for detailed checklists, or `docs/guides/filter-creation-workflow.md` for quick steps.

| Phase | Goal | Key Action |
|-------|------|------------|
| 1. Planning | Define dimensions, tiers, gatekeepers | Create `filters/{name}/v1/config.yaml` |
| 2. Architecture | Write oracle prompt with scope check + inline critical filters | Create `prompt-compressed.md` |
| 3. Validation | Calibrate oracle on ~100 articles | Small batch scoring run |
| 4. Prefilter | ⛔ **NEW FILTERS SHIP NO PER-LENS PREFILTER** — owner ruling, ADR-018 and ADR-019 *Amendment 2026-08-21*. Keyword screening is Latin-script only; the multilingual e5 probe (phase 6b) replaces it. For an EXISTING filter's prefilter it still saves oracle spend in phases 3/5 and is **NOT enforced in production scoring** (NM#284) | Nothing. If you believe this filter is the exception, read the amendment first |
| 5. Training Data | Score 5K-10K articles | Full batch scoring run |
| 6. Training | Distill to Gemma-3-1B + LoRA | Train on gpu-server |
| 6b. Probe | Stage-1 e5 screen (ADR-006/011) — replaces keyword screening | `scripts/train_probe.py`. ⚠️ `--objective` defaults to `regression`; a needle filter wants `recall` (ADR-023 does **not** apply to the probe — there the FN is the expensive error). ⚠️ **Pass `--seed` and record it** — probes were unseeded before 2026-09-04, and ⛔ **the selected threshold belongs to the PROBE, not the recipe**: on v8, `--seed 7` moved Stage-2 routing 14 pp at the *same* threshold with FN unchanged, and Stage 1 is silent so nothing surfaces it. Train on **CPU** (CUDA reductions are not deterministic under a seed) |
| 7. Calibration | Fit isotonic calibration | `fit_calibration.py` on val set, **with `--no-config-update`** unless `normalization.json` already exists — see "Fit calibration" above. ⛔ It may not improve held-out MAE and is close to a monotone rescale, so **re-derive the op-point on the calibrated scale at phase 8** |
| 8. Testing | Judge against held-out ORACLE ground truth, **never against the prior deployed model** (ADR-021) | `scripts/gate/ground_truth_gate.py --labels ... --model name=path`. ⛔ Rank on **recall + specificity, never MAE** (ADR-023), and read `--noise-floor` (#95, default 0.16) before calling any difference an effect. Plus `pytest tests/` and manual review of 30 articles |
| 9. Deployment | Upload to Hub, copy to NexusMind; fit normalization from a production-representative historical rescore to avoid the cold-start | See deployment + "Fit normalization" sections above |

---

## Dataset Conventions

- **Raw**: `datasets/raw/master_dataset.jsonl` — consolidated article corpus
- **Scored**: `datasets/scored/{filter}_{version}.jsonl` — oracle-labeled articles
- **Training**: `datasets/training/{filter}_{version}/` — train.jsonl, val.jsonl, test.jsonl (80/10/10)
- **Naming**: Training data dirs use underscores (`sustainability_technology_v3`), but hyphenated filter names keep hyphens (`cultural-discovery_v3`)
- **Active learning** (ADR-005): Run production filter on new articles → collect high-scoring candidates → oracle score → add to training data → retrain
- **Scored JSONL keys**: Use `analysis_field_name()` from `ground_truth/__init__.py` for consistent field naming

---

*⛔ **No "last updated" date here.** The one that stood until 2026-08-29 read 2026-04-19
while `git log -1 -- docs/RUNBOOK.md` said 2026-08-13 — a hand-maintained copy of something
git already knows, wrong by four months, in the file people consult before spending money.
Run `git log -1 --format=%ci -- docs/RUNBOOK.md` instead.*
