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

### Train on GPU server

```bash
# 1. Copy training data to gpu-server first
scp -r datasets/training/{name}_v{N}/ gpu-server:~/llm-distillery/datasets/training/

# 2. SSH and train
ssh gpu-server
cd ~/llm-distillery
source ~/gpu-server/nexusmind-scorer/venv/bin/activate
export PYTHONPATH=.
export HF_HUB_OFFLINE=1

python training/train.py \
    --filter filters/{name}/v{N} \
    --data-dir datasets/training/{name}_v{N} \
    --output-dir filters/{name}/v{N}/model
```

### Fit calibration (after training)

```bash
PYTHONPATH=. python scripts/calibration/fit_calibration.py \
    --filter filters/{name}/v{N} \
    --data-dir datasets/training/{name}_v{N} \
    --test-data datasets/training/{name}_v{N}/test.jsonl
```

Calibration writes `calibration.json` and `score_scale_factor` to config.yaml. Commit both with the filter package.

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
| 6b. Probe | Stage-1 e5 screen (ADR-006/011) — replaces keyword screening | `scripts/train_probe.py`. ⚠️ `--objective` defaults to `regression`; a needle filter wants `recall` (ADR-023 does **not** apply to the probe — there the FN is the expensive error) |
| 7. Calibration | Fit isotonic calibration | `fit_calibration.py` on val set |
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
