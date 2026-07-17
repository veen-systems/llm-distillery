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
# bash (runs verify_filter_package.py first, aborts on failure + refuses dirty tree)
bash scripts/deploy_to_nexusmind.sh {name} v{N}

# or PowerShell
.\scripts\deploy_to_nexusmind.ps1 {name} v{N}
```

Then `cd C:/local_dev/NexusMind && git push origin main`.

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

```bash
# Validation run (~100 articles, Phase 3)
python -m ground_truth.batch_scorer \
    --filter filters/{name}/v{N} \
    --source datasets/raw/master_dataset.jsonl --target-count 100

# Score articles (full run, Phase 5)
python -m ground_truth.batch_scorer \
    --filter filters/{name}/v{N} \
    --source datasets/raw/master_dataset.jsonl

# Multi-run averaging (for prompt-sensitive filters like thriving)
python scripts/oracle/average_oracle_runs.py \
    --runs datasets/scored/{name}_v{N}_run1.jsonl datasets/scored/{name}_v{N}_run2.jsonl datasets/scored/{name}_v{N}_run3.jsonl \
    --output datasets/scored/{name}_v{N}.jsonl
```

---

## Training

### Prepare data

```bash
python training/prepare_data.py \
    --filter filters/{name}/v{N} \
    --data-source datasets/scored/{name}_v{N}.jsonl

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
    --config filters/{name}/v{N}/config.yaml \
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

9-phase process. See `docs/agents/filter-development-guide.md` for detailed checklists, or `docs/guides/filter-creation-workflow.md` for quick steps.

| Phase | Goal | Key Action |
|-------|------|------------|
| 1. Planning | Define dimensions, tiers, gatekeepers | Create `filters/{name}/v1/config.yaml` |
| 2. Architecture | Write oracle prompt with scope check + inline critical filters | Create `prompt-compressed.md` |
| 3. Validation | Calibrate oracle on ~100 articles | Small batch scoring run |
| 4. Prefilter | Rule-based noise filter | Create `prefilter.py` inheriting `base_prefilter.py` |
| 5. Training Data | Score 5K-10K articles | Full batch scoring run |
| 6. Training | Distill to Gemma-3-1B + LoRA | Train on gpu-server |
| 7. Calibration | Fit isotonic calibration | `fit_calibration.py` on val set |
| 8. Testing | Benchmark vs oracle | `pytest tests/`, manual review of 30 articles |
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

*Last updated: 2026-04-19 (deployment pipeline hardening, #44 follow-up)*
