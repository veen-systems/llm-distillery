# Runbook

Operational how-to for deployment, training, and scoring. For project identity and hard constraints, see `CLAUDE.md`. For architectural decisions, see `docs/adr/README.md`.

---

## Deployment to NexusMind

⛔ **Since 2026-09-29 production scores from a CONTAINER IMAGE, not gpu-server (NexusMind#395).** The scorer
is a `nexusmind-scorer` container on whichever host NexusMind's ordered `pipeline.gpu_scoring.scorers` list
picks that cycle (NexusMind#591; the 2026-10-09 09:36 cycle ran on `hcl-ct102`, an RTX 4080, not sadaltager;
`data/last_run.json` `scorer` names it). ⚠️ Different hosts are different devices: compare production scores
across cycles only after checking `scorer.device_name` (#95, `memory/score-batch-shape-noise.md`). Every host
runs the image built by NexusMind's `deploy/scorer-image/stage.py`. It reads each served version's Hub repo
from that package's `inference_hub.py`; a version's adapter found in the llm-distillery checkout it is given
(`--weights-dir`) is used and **refused if it differs from its Hub copy**; with none there, the Hub copy is
downloaded; a `NO_HUB` version must be local (`stage.py` `fill_weights`, read 2026-10-09). sadalsuud no longer auto-pulls and no longer runs `deploy_filters.sh` per cycle. So:
- **Ours (steps 1–3):** a verified package, an adapter on the Hub byte-identical to this checkout's, and a
  NexusMind PR carrying the package.
- **NexusMind's (step 4):** merge, image rebuild, container swap, manual sadalsuud pull — in that repo's
  `deploy/scorer-image/README.md`. Its "Rolling back a filter version" is the only rollback: deleting
  `filters/<name>/vN` is NOT one (the image holds only the served version's weights).
- belonging v3 went this way on 2026-10-08 (NexusMind PR #627, `4901fb5`). Rewritten 2026-10-09 (TODO item 2b);
  the gpu-server text of step 4 is in git history before that date.

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
`last_modified` ≥ local `model/adapter_model.safetensors` <!-- placeholder --> mtime. Catches the
v_new-config × v_old-weights class (#44).

Then, because staging uses this checkout's adapter when present and compares BYTES with the Hub (the
freshness check above compares only times). The Hub repo comes from the package's `inference_hub.py`:

```bash
.venv/bin/python3 scripts/deployment/check_adapter_matches_hub.py {name} v{N}
# 0 MATCH · 1 MISMATCH or adapter missing here · 2 could not ask the Hub (never a pass)
```

Not for `NO_HUB` versions (uplifting v7): staging records their sha256 and has nothing to compare it to.

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

# then without --dry-run. (The PowerShell twin was deleted 2026-09-26: Linux only.)
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

> **Packaged detectors ship by `MANIFEST.json` (ADR-024 step 3, 2026-09-27).** harm v1, obituary v5,
> violence_promotion v1 and commerce_prefilter v1 (`PACKAGES` in `scripts/deployment/detector_manifest.py`) never
> ship from this working tree. **Step 0.7**, before anything is copied, runs `deploy_detectors.py stage`: every
> file the committed manifest lists is fetched (weights from the Hub at the pinned revision, the rest from this
> repo) and sha256-verified. It refuses an uncommitted manifest or git-origin file, an unpinned `hub`, a sidecar
> that does not carry its pickle's manifest digest, and a `.nexusmind-owns` entry inside a packaged dir. It needs
> Hub access and the token from `config/credentials/secrets.ini` (anonymous only works from the HF cache).
> **Step 2a** (`place`) writes the files, deletes ONLY what the previous NexusMind manifest listed and the new one
> does not (no readable previous manifest = nothing deleted, extras reported), writes `MANIFEST.json` last and
> only on success, and re-hashes the target. Under `--dry-run` it only PLANS. Check any tree afterwards with
> `python3 scripts/deployment/verify_detector_package.py verify --all --target <nexusmind root or host:path> --strict`.
> To change a packaged detector: rebuild, upload (`upload_detector_to_hub.py`), rewrite the manifest
> (`verify_detector_package.py write`), commit, deploy — never edit a manifest by hand.
> ⚠️ Limits (ADR-024 step 5, NexusMind's): NexusMind gitignores `*.safetensors`, so commerce v1's model stays in
> the deploying checkout; `deploy_filters.sh` does not delete under `models/` on gpu-server (pre-#395 path; gpu-server is now a fallback only).

> **Step 2b ships the other `filters/common/` RUNTIME files** (owner ruling, #164, 2026-09-26).
> The selection is one module, `scripts/deployment/common_runtime_files.py --unpackaged`. It excludes
> the packaged detector dirs, `*/training/`, `*/validation/`, `*/docs/`, `*/tests/` and `__pycache__/`, plus
> `oracle.py`, `prompt.md` and `detector_seeds.py`, and ships everything else, including
> files git does not track. Preview it without touching NexusMind:
> `python3 scripts/deployment/common_runtime_files.py --unpackaged`. The count depends on the local
> tree (gitignored weights included), so run it rather than quote one.
> `tests/unit/test_common_runtime_files.py` pins the two facts that decide the rule:
> - **Weights of an UNPACKAGED detector would reach NexusMind only through this copy** (gitignored here, so
>   `git ls-files` would stop shipping them). Retired versions (`RETIRED_DIRS`: obituary v3/v4, commerce v2) never ship (owner, 2026-09-27).
> - **Some "training"-named files are runtime.** `harm_detector/v1/inference.py` reads
>   `filters/common/harm_detector/v1/models/training_config.json` (and, if present, `models/SHA256SUMS.txt`) at load, so never exclude by
>   those names.
>
> Untracked scratch files in `filters/common` outside the packaged dirs ship too, and are then committed in
> NexusMind: keep that tree clean before deploying.
>
> **Step 0.6 stops the deploy if a pickle about to ship would sit next to a stale `.sha256`
> sidecar in NexusMind.** It checks the filter package (step 1, probe pickles) and step 2b's
> unpackaged files; packaged detectors' sidecars ship with their pickles and are checked by step 0.7.
> It runs before step 1, so NexusMind is untouched on failure. Fix: write
> the matching sidecar in llm-distillery next to the pickle (`sha256sum X.pkl > X.pkl.sha256`)
> and commit it, so pickle and sidecar land in ONE NexusMind commit. ⛔ Never delete the NexusMind sidecar:
> `embedding_stage` then loads the pickle unchecked, and `harm_detector` refuses to load
> without a recorded hash. Step 2b never deletes; removing files that dropped out of its selection is NexusMind's job.

> ⚠️ **`--dry-run` still writes.** It copies the files and skips only the
> `git add`/`commit`/`push`, so it dirties the NexusMind working tree. That matters
> when a parallel session shares that checkout: revert with **explicit paths**
> (`git -C $NEXUSMIND_ROOT checkout -- <path> <path>`), never a bare
> `git checkout .` (2026-08-13).

> **Pre-flight guard D compares this checkout's adapter with its Hub copy** (since 2026-10-09; before that it
> ssh'd gpu-server, which no longer serves production). It fails closed if it cannot ask the Hub and skips
> `NO_HUB` versions. `--weights-preplaced` skips it: pass it only offline, and only after
> `check_adapter_matches_hub.py` (step 1) printed MATCH somewhere that could reach the Hub.

Then push the NexusMind change **on a `chore/` branch and open a PR** (NexusMind uses them; two commits went
straight to its `main` on 2026-08-13). ⚠️ The script's `--push` pushes NexusMind `main` directly: do not use it.

### 4. Hand-off: NexusMind builds the image and switches (theirs, not ours)

Nothing in this repo deploys to production any more. Tell the NexusMind session (or the owner) that the PR is
ready, and name: the package path and llm-distillery commit, the Hub repo and adapter sha256 (step 1's output),
whether this is a **new filter name** (then step 4b applies, and `pipeline.enabled_filters` changes) or a
version bump, and the rollback rule if the switch has one. NexusMind then, per its
`deploy/scorer-image/README.md` (Build, Run, Rolling back a filter version):
- merges the PR;
- stages and builds the image (`stage.py --weights-dir <llm-distillery checkout>` and the Hub token; a
  local adapter that differs from the Hub stops the build, a `NO_HUB` one must be local), and swaps the container, **keeping the previous one stopped** — that container is
  the rollback;
- pulls sadalsuud by hand, between the same two cycles as the swap (sadalsuud no longer auto-pulls).

⛔ **The scorer serves the highest `vN` it was built with.** A version bump goes live on the first cycle after
the swap, with nothing in between; there is no per-version switch to flip later.

⛔ **Rollback is the kept previous image plus a sadalsuud revert, both between the same two cycles** — NOT
deleting `filters/{name}/v{N}`. The image carries only the served version's weights, so a deletion on it stops
the scorer and takes every filter down (NexusMind PR #627 review, 2026-10-08).

*`scripts/remote_deploy.sh` and `deploy_filters.sh` push to gpu-server, which is NexusMind's FALLBACK only
(`deploy/scorer-image/README.md` § Rollback to gpu-server). Running them deploys nothing to production.*

### 4b. A NEW filter needs its `processed_ids` seeded BEFORE its first cycle

⛔⛔ **This step does not exist for a version bump and is mandatory for a new filter name.
Skipping it took the whole pipeline down on 2026-09-07.**

NexusMind tracks what each filter has already scored in
`data/raw/.processed_ids_<filter>.json`, and `load_articles()` skips those ids
(`scripts/main.py:1565`). A filter with **no such file** therefore loads **every article inside
`pipeline.max_article_age_days`** — not just the cycle's new ones.

That would be a private cost, except the expensive preprocessing stages are **shared**: story
dedup and image analysis run once on the **union of every enabled filter's pool**
(`scripts/main.py:3555-3567`). So one cold-starting filter inflates them for **all** filters.

Measured on the first cycle after enabling `human_thriving v8` (2026-09-07, 3-day window,
collection every 4h ⇒ ~18 cycles of backlog):

| stage | normal | first cycle | factor |
|---|---|---|---|
| og:image backfill | 2.6k–3.1k | **21,245** | 7.0× |
| hero image extraction | 3.3k–4.0k | **41,435** | 10.2× |
| ML candidates | under the 3,000 cap | **18,206** | 6× over |

⛔ **And it does not self-heal.** `_save_processed_ids` is called at `scripts/main.py:2141`,
**after** the per-filter scoring loop completes. The cycle above was on course to exceed
`TimeoutStartSec=4h` before scoring even started, so the SIGKILL would have left the file
unwritten and the next cycle would have rebuilt the identical pool — **a kill loop every 4h,
zero filtered output for every filter, until someone intervenes.** The thing that would end it
is exactly the thing the kill prevents.

**Do this before enabling a new filter name in `pipeline.enabled_filters`:**

```bash
# 1. Confirm the gap (an established filter for comparison)
ssh sadalsuud 'cd ~/local_dev/NexusMind && ls -la data/raw/.processed_ids_*.json'

# 2. Seed from any established filter — same corpus, same id space
#    (measured 2026-09-07: all five sat at 121,881–121,883 ids)
ssh sadalsuud 'cd ~/local_dev/NexusMind && \
  cp data/raw/.processed_ids_uplifting.json data/raw/.processed_ids_{name}.json'
```

⚠️ **Copy the file WHOLESALE — do not copy only the `ids` map.** It also carries a `versions`
sidecar of `{id, content_hash, collected_date}`, the superseded-rows mechanism
(llm-distillery#119) that re-admits an article edited upstream. That is **filter-agnostic corpus
data** — a content hash is the same whichever filter saw it — so stripping it silently costs the
new filter change detection for the whole retention window.

⚠️ **The seeded file is the MITIGATION, not a stray artifact.** Deleting it restores the
backfill, i.e. restores the outage. Say so wherever the deploy is recorded.

⚠️ **Cost of seeding, stated:** the new filter never scores the retention-window backlog. That
is usually irrelevant — Phase E needs *new* rows above the op-point and gets them at the normal
per-cycle rate (~147/cycle measured on `uplifting`, 5.81% of 2,530). Take the backlog only if
something actually needs it, and then plan for a multi-hour cycle rather than discovering one.

**Verification, after the first real cycle** — and predict it before looking: the shared stages
return to their normal bands (og:image 2.6k–3.1k, hero 3.3k–4.0k). If they stay high, the cold
start is not the whole story; back the filter out of `enabled_filters` and re-diagnose rather
than guessing again.

### 5. Verify the switch from the OUTPUT, after the first cycle on the new image

Predict first (expected share of rows at or above the op-point, from the gate run), then read. Checked this
way for belonging v3 (`filters/belonging/v3/STATUS.md`):

```bash
# Every row of the newest filtered file carries the new version (stage1_low rows too):
ssh sadalsuud 'cd ~/local_dev/NexusMind && f=$(ls -t data/filtered/{name}/filtered_*.jsonl | head -1) && \
  echo $f && jq -r ".nexus_mind_attributes.{name}.version" $f | sort | uniq -c'
# The scorer served the code sadalsuud holds (false = image and checkout disagree):
ssh sadalsuud 'cd ~/local_dev/NexusMind && jq ".scorer" data/last_run.json'
```

⚠️ The newest file must be NEWER than the swap. A file written before it carries the old version and reads as
a failed deploy; a count of 0 rows means the cycle did not run, not that it passed. Then the op-point share
against the prediction; condition on `stage_used` before reading `raw_weighted_average`.

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

# Validate splits AND their fit to production. ⛔ Required before every training run (owner, 2026-10-07):
#    docs/checklists/training-data-fmea.md lists the failure modes; this runs the mechanized ones and FAILS
#    without a production sample unless --no-production-sample "<reason>" says why.
python training/validate_training_data.py \
    --data-dir datasets/training/{name}_v{N} --filter filters/{name}/v{N} \
    --production-sample <uniform random draw of recent production rows, full text> \
    [--language-stamps <id -> language JSON>]
```

⛔ **Read the FM-T1 table before training, not just the exit code.** A positive share that rises with text length
while production articles are long is a shortcut the student will learn (belonging, 2026-10-07: training articles over
2,000 chars were 12-21% positive; production, measured 2026-10-08 on the 798-row production sample (oracle k=1): 5.8% / 10.6% / 12.7% positive at 2–4k / 4–8k / >8k chars, so production ALSO rises with length, and the easy negatives only brought training to 10.7-18.9%, about 1.5-1.8x production per bin. Compare per bin, not against one production rate). Each row of
`docs/checklists/training-data-fmea.md` that is not mechanized needs an owner acceptance in the build's evidence
README.

### Train on GPU

Two hosts. **`b650-gpu` is the training node** (⭐ **RTX 5090 32 GB since 2026-09-17**, was a
3090 Ti 24 GB; the ~1.26 s/it at batch 8 is a 3090 Ti figure and has not been re-timed;
`memory/b650-gpu.md`) and ends Ollama-vs-training contention on gpu-server. It is NOT a
production box — ⛔ never diff a b650 replay against stored production scores without
matching production's device first (CPU→CUDA on the current card is worth 2 flips at 4.5).
⛔ **And never diff a b650-CUDA replay against a b650-CUDA dump taken before 2026-09-17** —
the two GPUs disagree at max |Δ| **0.2357**, 2 flips at 4.0. Re-dump instead.
⚠️ **Training across the swap is UNMEASURED** (`H-DEV-1`): everything in `EXP-038` is
inference on fixed weights. Before a retrain here is compared against a pre-swap baseline,
read `memory/hypothesis-ledger.md` H-DEV-1 — the cheap same-box step comes first.

⛔ **THE TRAINING RUN MUST NAME A COMMIT, AND `train.py` NOW REFUSES WITHOUT ONE.**
`human_thriving v8`'s first adapter was built by a tree that `git commit --amend` then
orphaned, so the sha that produced the shipped weights (`0697f5a`) is reachable from no
branch — and nothing caught it, because `training_metadata.json` recorded no commit at
all. The owner's 2026-09-06 ruling was **no exception**: it was retrained rather than
shipped with a carve-out. `resolve_git_provenance()` runs **before** the ~100-minute run
and refuses on a non-checkout, a dirty tree, or a commit on no branch;
`--allow-missing-git-provenance` is the explicit opt-out and is written into the metadata,
where `scripts/verification/check_training_provenance.py` reports it. **Commit and push
before you train.**

⭐ **`b650`'s `~/llm-distillery` IS a git checkout as of 2026-09-06** — `git init` + a
remote + `git checkout -f main`, which left every gitignored artefact (datasets, venvs,
`model/`) untouched. It had been a partial rsync, and its `training/train.py` was the
**pre-fix** version missing 176 lines of checkpoint-selection machinery, while its
`uplifting v7` config/normalization/base_scorer had drifted from the bytes sadalsuud
actually serves. **Prefer `git fetch && git checkout` over the rsync below**; the
`git ls-files` recipe is kept for a host where a checkout is not possible.

```bash
# 1a. PREFERRED: the box is a checkout, so name a commit instead of copying files.
ssh b650-gpu 'cd ~/llm-distillery && git fetch -q origin main \
  && git checkout -q -f main && git reset -q --hard origin/main \
  && git rev-parse HEAD && git status --porcelain -uno | wc -l'   # expect 0 drift

# 1b. FALLBACK for a non-checkout host: send tracked files only, then what runs there is
#     exactly what is committed. Verify by md5. Training will need
#     --allow-missing-git-provenance, and the check will report the gap.
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

## Running the ADR-021 deploy gate — the dump comes first, and its DEVICE decides

⛔ **Step 1 is not the gate.** The gate is arithmetic over a scored dump; whether its answer
is production's depends entirely on how that dump was made. First run for `human_thriving v8`
on 2026-09-06 (`docs/evidence/2026-09-06-v8-deploy-gate/`, `EXP-026`).

1. **Score the held-out split on the DEVICE production serves on** — GPU. CPU dumps from
   earlier phases are usually already on disk and the gate will happily read them, which is
   the trap (#104). On b650:

   ```bash
   ssh b650-gpu 'cd ~/llm-distillery && PYTHONPATH=. HF_HUB_OFFLINE=1 \
     venv-prodparity/bin/python scripts/analysis/dump_student_scores.py \
       --filter filters/<name>/v<N> \
       --split-file datasets/training/<name>_v<N>/test.jsonl \
       --out-dir ~/llm-distillery/<name>_test_dump_cuda \
       --require-device cuda'
   ```

   ⛔ **`--require-device` reads the device back off `next(scorer.model.parameters())`, not
   off the flag you passed.** Setting `CUDA_VISIBLE_DEVICES` is not the same as being on the
   device — a "CPU" arm once read 2.37 ms against GPU's 2.34 because a cache ignored the
   device it was asked for (#146). ⛔ **`--out-dir` under `~`, never `/tmp`**: eleven probes
   were found one reboot from gone in b650's `/tmp` after 36 days of uptime.

2. ⚠️ **Check the box's checkout against the repo before scoring.** `b650:~/llm-distillery`
   is **not a git clone**. Four files on the scoring path had drifted when v8's gate was run.
   A dump that feeds a deploy gate must be produced by the shipped program:
   `sha256sum` the filter package, `filters/common/*.py` and the two script directories on
   both sides, sync what differs, and keep the pre-sync copies.

3. **Run the gate with `--config`**, so the threshold and gatekeeper come from what deploys
   rather than from the nature_recovery v4 fallback constants:

   ```bash
   PYTHONPATH=. python scripts/gate/ground_truth_gate.py \
     --labels datasets/training/<name>_v<N>/test.jsonl \
     --config filters/<name>/v<N>/config.yaml \
     --model calibrated=<dump>/scores_calibrated.jsonl \
     --recompute-model-wa --report filters/<name>/v<N>/ground_truth_gate.json
   ```

   The report records `inputs` (argv plus the sha256 of the labels, the config and every
   dump) automatically. **A hand-written `provenance` block is what a sha256 cannot say** —
   box, venv, device — so write one; the gate carries it across reruns and **stamps it with
   a fingerprint of the inputs it described**, marking it `⛔ STALE` when they change.

4. **Commit a manifest** naming the dump paths, their sha256, the box, the venv pins, the
   weights' sha256 and the device. The dumps themselves are gitignored (`datasets/*`).

⛔ **Do not compare the resulting recall to another filter's.** Two filters share a positive
class only if their oracles do; `uplifting v7` and `human_thriving v8` score 0.246 Jaccard on
the same 660 rows, so those are two quantities with one name.

⚠️ **Whether the device mattered is a MEASUREMENT, not an assumption in either direction.**
On v8 it did not — CPU vs CUDA gave 0 verdict flips and identical confusion matrices, max
|Δ| 0.1428, *below* the #95 floor. On `uplifting v7` at the same 4.5 bar it was 0.1956 with
3 flips. Dump both and diff before claiming either.
⛔ **AND "BELOW THE FLOOR" IS NOT "NO FLIPS" — that inference is invalid, and 2026-09-17
supplied the counter-example.** After b650's GPU swap, `uplifting v7`'s device term measured
**0.1572 with ZERO rows above 0.16 and still 2 flips at 4.5** (the flipping rows moved 0.0467
and 0.1421). A flip is a small delta near the bar; a max-|Δ| comparison cannot see one.
**So v8's 0 flips above is load-bearing and its 0.1428 is not** — always read the flip count.
⚠️ Both of those numbers are 3090 Ti measurements. `EXP-038`,
`docs/evidence/2026-09-17-b650-gpu-swap-parity/`.

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

✅ **FIXED 2026-09-22 (llm-distillery#154, owner-ruled option 1).** A filter whose op-point IS
4.5 could not be fitted at all: the NexusMind#205 hard guard compared `sample_min` against the
absolute `MAX_NORMALIZATION_RAW_MIN = 4.5`, so at that op-point every honest fit failed it — any
observed score above the bar is above 4.5 unless it rounds to 4.5 at four decimals (a 5e-5
window), making it a sample-**density** test rather than the bias test it documents. It blocked
`human_thriving v8`'s Phase E on 2026-09-08 with the row bar met (202/200); `uplifting v7` had
passed the same guard in August at a true `sample_min` of 4.500027 on 15,698 rows.
The guard now tests the **GAP** (`sample_min - anchor > MAX_SAMPLE_GAP`, 0.5), in the fitter and
in `tests/unit/test_normalization_invariant.py` together. ⛔ **Identical at op-point 4.0 only** —
stricter below it, looser above it; see `docs/NORMALIZATION_METHOD.md` §5.2 for the table.
A span-relative advisory warns when the unobserved band exceeds 5% of the fitted span.
**Do not reach for `--analysis-only`**: it cannot write a file named `normalization.json`, by
design.

⚠️ **Fitting also arms NexusMind#319, and the obvious sanity check on it is a tautology.** After
anchoring, the op-point maps to normalized 0.0 and the enrichment gate sits at normalized 4.0 —
which *is* the 40th percentile of whatever sample you fitted on, so "≈60% of surfaced rows still
clear it" is arithmetic, not a measurement. Quote the **effective raw bar** instead — **4.794**
for v8's shipped 2,976-row fit, against an op-point of 4.50 (it was 4.872 on the 202-row fit) —
or measure the share on cycles the fit did not see.
⛔ **A bigger sample does not repair this and the 2026-09-22 session walked into it anyway**: it
recomputed the share on 2,976 fitted rows, got 60.0%, and reported it as a correction of the
202-row 60.4%. Both are the same identity. `uplifting v7`'s 60.0% IS out-of-sample and therefore
real — 82 cycles 2026-08-23 → 2026-09-06, 251,461 rows, 18,041 surfaced, 10,817 clear
(`docs/evidence/2026-09-06-v8-deploy-gate/README.md` §3) — so setting the two side by side as
"parity" compares a measurement to an identity.

Writes `normalization.json` to the filter dir; commit it and deploy to both servers. Refit per version.

---

## Filter Development Lifecycle

The phases below, in order — `6b` is lettered rather than numbered because other documents cite these numbers (the v8 plan and `CLAUDE.md` both say "phase 5"), so renumbering costs more than it buys. See `docs/agents/filter-development-guide.md` for detailed checklists, or `docs/guides/filter-creation-workflow.md` for quick steps.

| Phase | Goal | Key Action |
|-------|------|------------|
| 1. Planning | Define dimensions, tiers, gatekeepers | Create `filters/{name}/v1/config.yaml` |
| 2. Architecture | Write oracle prompt with scope check + inline critical filters | Create `prompt-compressed.md` |
| 3. Validation | Calibrate oracle on ~100 articles | Small batch scoring run |
| 4. Prefilter | ⛔ **NEW FILTERS SHIP NO PER-LENS PREFILTER** — owner ruling, ADR-018 and ADR-019 *Amendment 2026-08-21*. Keyword screening is Latin-script only; the multilingual e5 probe (phase 6b) replaces it. Since 2026-10-01 no ovr filter has one — every per-lens prefilter was deleted (`ai-engineering-practice`, a separate product, keeps its own) (decision 0, NM#284); the oracle path's only gate is `make_oracle_prefilter` | Nothing. If you believe this filter is the exception, read the amendment first |
| 5. Training Data | Score 5K-10K articles | Full batch scoring run |
| 6. Training | Distill to Gemma-3-1B + LoRA | Train on gpu-server |
| 6b. Probe | Stage-1 e5 screen (ADR-006/011) — replaces keyword screening | `scripts/train_probe.py`. ⚠️ `--objective` defaults to `regression`; a needle filter wants `recall` (ADR-023 does **not** apply to the probe — there the FN is the expensive error). ⚠️ **Pass `--seed` and record it** — probes were unseeded before 2026-09-04, and ⛔ **the selected threshold belongs to the PROBE, not the recipe**: on v8, `--seed 7` moved Stage-2 routing 14 pp at the *same* threshold with FN unchanged, and Stage 1 is silent so nothing surfaces it. Train on **CPU** (CUDA reductions are not deterministic under a seed) |
| 7. Calibration | Fit isotonic calibration | `fit_calibration.py` on val set, **with `--no-config-update`** unless `normalization.json` already exists — see "Fit calibration" above. ⛔ It may not improve held-out MAE and is close to a monotone rescale, so **re-derive the op-point on the calibrated scale at phase 8** |
| 8. Testing | Judge against held-out ORACLE ground truth, **never against the prior deployed model** (ADR-021) | **See *Running the ADR-021 deploy gate* above — step 1 is the DUMP, on production's device (#104), not the gate.** ⛔ **HIGH CERTAINTY OVER HIGH DETECTION**: read specificity first, rank on **recall + specificity, never MAE** (ADR-023), and state the priority beside any recall you publish — a low one here is usually the choice working. Read `--noise-floor` (#95, default 0.16) before calling any difference an effect. Plus `pytest tests/` and manual review of 30 articles |
| 9. Deployment | Upload to Hub, copy to NexusMind; **then** fit normalization | See deployment + "Fit normalization" above. ⛔ **Normalization FOLLOWS deployment and cannot precede it**: `fit_normalization.py` reads NexusMind production output and refuses below `MIN_NORMALIZATION_ARTICLES = 200` above the op-point, so an undeployed filter has no population (v8, 2026-09-06; `solutions v6` went gate → deploy → fit in two days). ⚠️ **Fitting it is also what arms NM#319**: anchoring puts the op-point at normalized **0.0** by construction, and NexusMind's enrichment gate at 4.0 reads the NORMALIZED score — on `uplifting v7` only 60.0% of surfaced rows clear it (out-of-sample, measured after its 2026-08-10 fit) |

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
