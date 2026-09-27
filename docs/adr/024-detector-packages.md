---
status: Accepted
date: 2026-09-27
deciders: [Jeroen Veen]
superseded_by:
---

# ADR-024: Detectors as Deploy Packages — Manifest, Hub Record, Required Integrity, Removal by Manifest

✅ **RULED 2026-09-27 by Jeroen Veen, in session** (answering questions the assistant wrote): **Option C
accepted**; open question 2 → **one Hub repo per detector**; open question 1 (in part) → **obituary v3/v4 are
retired, not packaged**. Questions 3–5 were ruled later the same day (see *NexusMind's review*). Nothing is built yet; order step 1 comes first, and the
NexusMind session reviews the cross-repo order before step 4. "ADR-024" is **llm-distillery's**; NexusMind
numbers its own ADRs.

## Context

Detectors live in `filters/common/` (`harm_detector`, `obituary_detector`, `violence_promotion`,
`commerce_prefilter`). Unlike filters, they have no package. Measured 2026-09-26/27: #164, #165 and a
read-only sweep of both repos. File references are to the sweep; re-read them before building.

- **Weights have no home of record.** Every `*.pkl` / `*.safetensors` is gitignored here (`.gitignore:73`,
  `filters/common/obituary_detector/.gitignore:17`). NexusMind tracks the pickles and sidecars in ITS git,
  except commerce v1's `distilbert/model.safetensors` (541,317,368 B), which is untracked there and arrives
  out of band. **commerce_prefilter v2's pickles exist only in NexusMind git** (NexusMind `3864388`). They are
  in neither this checkout nor b650's, so llm-distillery is canonical (#164) for a package it cannot rebuild.
- **Integrity is three different things.**
  - harm v1 raises on a missing or wrong hash (`harm_detector/v1/inference.py:153-180`, `SHA256SUMS.txt` or
    sidecars).
  - obituary v3–v5, violence v1 and commerce v2 raise on a mismatch but only log at DEBUG when the sidecar is
    missing (NexusMind `filters/common/embedding_stage.py:37-58`).
  - commerce v1 has no check at all.
  - gpu-server's own detector copies use baked-in or env hashes and raise when one is missing
    (`deploy/gpu-server/main.py:492-527`).
- **The runtime contract is undeclared.** Nobody knew harm reads `training_config.json` and `SHA256SUMS.txt`
  at load until the code was read (#164).
- **Delivery is a working-tree copy.** `deploy_to_nexusmind.sh` step 2 copies whatever is on disk. Since
  `356cd70` it copies runtime files only; since `675c101` it refuses a stale NexusMind sidecar. It never
  deletes, so files that leave the selection stay in NexusMind (22 did, #164). `NexusMind/scripts/
  deploy_filters.sh:370-389` rsyncs in-git pickles to gpu-server without `--delete`, so they stay there too.
- ⭐ **Filters do not load from the Hub in production either.** gpu-server calls
  `get_production_scorer(..., use_hub=False)` (`deploy/gpu-server/main.py:926-931`), runs with
  `HF_HUB_OFFLINE=1` (`deploy/gpu-server/.env.example`), and refuses to start without a local
  `model/adapter_model.safetensors` (`main.py:~1041-1054`). The Hub is where adapters are RECORDED, not
  where production reads them, and no Hub `revision` is pinned anywhere (`load_lora_hub`,
  `filters/common/model_loading.py:337`). **#165's "weights on the Hub, like the filters" therefore means a
  Hub record plus a local copy, not a Hub fetch at load time.**

Why now: #164 made llm-distillery canonical for `filters/common`, and the copy-based deploy is the only
route detector weights have. A retrained detector today ships whatever the working tree holds.

## Options Considered

### Option A: Keep the interim (runtime-file copy + stale-sidecar guard)

| Pros | Cons |
|------|------|
| Already built and tested (`356cd70`, `675c101`) | No record of which bytes shipped; not reproducible from a commit |
| No cross-repo work | commerce v2 stays unrebuildable here; files are never removed |
| | Integrity stays optional for 4 of 5 detector families |

### Option B: Manifest here, weights stay in NexusMind git

| Pros | Cons |
|------|------|
| Small change; the pickles are 2.8–14 MB and already tracked there | Weights canonical in the CONSUMER, which contradicts the #164 ruling |
| Loaders unchanged | commerce v1's 541 MB model cannot live in git; it still needs another route |
| | Retraining here still has to push bytes into another repo by hand |

### Option C: Manifest here + Hub as the record, fetched at DEPLOY time (recommended)

| Pros | Cons |
|------|------|
| One source of record per version (Hub revision + sha256), matching how filters are recorded | New tooling: manifest writer, package check, Hub upload for non-LoRA dirs (`upload_to_huggingface.py` assumes a LoRA layout, 309-331) |
| Loaders stay offline and unchanged; only the deploy fetches | Deploy host needs Hub access and a token (the deploy already reads `secrets.ini` for `--check-hub`) |
| Removal is safe: only files named in the PREVIOUS manifest are deleted | Backfill: current weights must be uploaded first, and commerce v2's come from NexusMind |
| Works for the 541 MB commerce v1 model | Two copies (Hub + NexusMind git) until NexusMind stops tracking the pickles |

### Option D: NexusMind loaders fetch from the Hub at load time

| Pros | Cons |
|------|------|
| No copy step | Production is offline by design (`HF_HUB_OFFLINE=1`); no filter works this way; a Hub outage becomes a pipeline outage |

## Decision

**Option C (ruled 2026-09-27).** Per detector version (`filters/common/<detector>/<version>/`):

1. **`MANIFEST.json`, committed here**: `detector`, `version`, `source_commit`, `built_utc`, and `files` — each
   `{path, sha256, bytes, origin: "git" | "hub"}`. Plus `hub: {repo_id, revision}` when any file is `hub`.
   **Only listed files ship.** It replaces `SHA256SUMS.txt` and the per-file sidecars as the integrity
   record. It is written by a script, never by hand. The manifest itself is protected only by git review and
   the commit it records; that is the trust root, stated rather than assumed. The writer's file boundary is
   the detector's own `<detector>/<version>/` dir, pinned by a test (as `common_runtime_files.py` is) so a
   refactor cannot pull a shared `filters/common/*.py` module into one detector's manifest.
2. **Weights recorded on the Hub**: one private repo per DETECTOR (ruled), with `revision` = the commit
   that uploaded the version, pinned in the manifest. Code and small JSON stay in git (`origin: "git"`).
3. **Deploy = fetch, verify, place, prune.** The deploy fetches `hub` files at the pinned revision into a
   staging dir. It verifies every file against the manifest, copies them, then deletes exactly the files
   that the PREVIOUS manifest listed and the new one does not. It never deletes an unlisted file. A
   mismatch fails before anything is copied, as step 0.6 does today. **No readable previous manifest**
   (first deploy, deleted or corrupt file) **means no prune**: the deploy places the files and REPORTS every
   file in the target dir that the new manifest does not list. It never infers what to delete.
4. **Integrity required at load, as the END state**: the loaders verify against the manifest, and in the end
   state they raise when an entry is missing or wrong. They get there behind a config flag that defaults to
   log-only and is flipped per detector (Order, step 4). This is the NexusMind change, and it goes last.
5. **`verify_detector_package.py`**: the detector counterpart of `verify_filter_package.py`. It checks that
   the manifest matches disk, versions are consistent (imports, `config.yaml`, directory name), the Hub
   revision exists, and each `hub` file's sha256 matches the Hub's LFS sha256 (the same check
   `verify_filter_package.py` already does for adapters, 206-371).

### Order (cross-repo; each step is independently useful and reversible)

1. **Here:** manifest writer + `verify_detector_package.py`, run in **reporting mode** over the current
   packages. Backfill manifests from the bytes NexusMind actually serves, not from this working tree.
2. **Here:** upload each current detector version's weights to the Hub (commerce v2 from NexusMind's copy)
   and pin the revisions. Verify by downloading and comparing hashes, not by the upload's exit code.
3. **Here:** `deploy_to_nexusmind.sh` step 2 becomes manifest-driven (fetch → verify → place → prune).
   Prove the outcome on one detector with `--dry-run`, then for real, then diff NexusMind's tree against
   the manifest.
4. **NexusMind (their PR, their review):** loaders read `MANIFEST.json` and require it. This is a
   config-flippable enforcement: log first, enforce second. This borrows ADR-022's MECHANIC (one flag, flipped
   deliberately) but not its safety case: ADR-022 was built for score visibility, where a bad flip mis-ranks
   an article, while a bad integrity flip takes a detector DOWN. Flip one detector at a time, and only after
   its log-only run shows zero mismatches. NexusMind may then stop
   tracking the pickles in git.
5. **NexusMind:** `deploy_filters.sh` pushes detector files to gpu-server manifest-driven, with the same
   prune rule.

## Open questions (owner)

1. **Which versions to package vs retire.** ✅ *Ruled in part:* obituary v3/v4 → retire, don't package. Measured 2026-09-27: commerce v1 IS loaded
   (`NexusMind/src/preprocessing/commerce.py:35,286`), so its 541 MB model must be packaged. commerce v2 is
   named by gpu-server (`deploy/gpu-server/main.py:853`, `src/scoring/gpu_client.py:505`), and whether
   anything loads it there was not checked. Obituary v3/v4 have no loader in NexusMind: retire them, don't
   package them?
2. ✅ **RULED: one Hub repo per detector.** *(Was: one Hub repo per detector, or one per detector version?)* Filters use one per version
   (`{name}-filter-v{N}`). Per detector with pinned revisions is fewer repos; per version matches filters.
3. **Does gpu-server keep its own detector copies** (`main.py` loads obituary v5 and commerce from its own
   paths with baked-in hashes), or read the same manifest?
4. **Does enforcement (step 4) wait for all detectors,** or go per detector as each gets a manifest?
5. **Library skew is out of scope as drafted.** The manifest proves the bytes are CORRECT, not LOADABLE: a
   pickle built under one `sklearn_version` can fail or misbehave under another. harm already warns on this
   (`_warn_on_stack_drift`). Record the build stack in the manifest and check it at load (warn), or leave it
   to `training_config.json`?

## NexusMind's review (2026-09-27, session `nexusmind-b2`, relayed; peer ENGINEERING VIEWS, not owner rulings)

- **The order (steps 1–5, NexusMind's as reviewed PRs) is accepted by NexusMind.** Nothing is needed from them before step 4.
- **commerce v2, measured by NexusMind:**
  - The pipeline does NOT load v2. `src/preprocessing/commerce.py:190-197` (LD#80) forces local v1, so
    production commerce stamps come from v1.
  - gpu-server DOES load v2 when `models/mlp_classifier.pkl` exists (`deploy/gpu-server/main.py:1059-1062`).
    Its journal shows it loaded at 10:08:26 and unloaded at 10:08:35 on 2026-09-27; the caller is unidentified.
  - ▶ **Owner question (new): package v2 only if gpu-server's `/commerce/predict` should keep working.**
    Nothing in NexusMind's scoring depends on it.
- **Q3 (their view):** gpu-server reads the same `MANIFEST.json`. Its env-var hashes (`CLASSIFIER_HASH`,
  `main.py:~478`) and baked-in obituary v5 value are a second integrity record that can drift.
- **Q4 (their view):** enforce per detector, so a bad manifest takes out one detector, not all.
- **Q5 (their view):** yes. Record the sklearn/joblib versions and warn on skew at load.

*All three match this ADR's leanings. They become rulings only when the owner rules them.*

✅ **RULED 2026-09-27 by Jeroen Veen, in session** ("ok, let us do it", answering the assistant's question
whether to take all four as rulings):
- **Q3:** gpu-server reads the same `MANIFEST.json`.
- **Q4:** enforce per detector.
- **Q5:** record the sklearn/joblib versions and warn on skew at load.
- **commerce v2 is RETIRED, not packaged.** It lost to v1 on 1,000 production articles (llm-distillery#80:
  under-blocks commerce, over-blocks Greek news), and the pipeline has forced v1 since.
  *Gloss:* gpu-server's `/commerce/predict` then loses its model; retiring the endpoint is NexusMind's
  change to make.

**Package set (ruled): harm v1, obituary v5, violence_promotion v1, commerce_prefilter v1.**

## Consequences

### Positive
- Every shipped detector byte is named, hashed and reproducible from a commit plus a Hub revision.
- Retraining here no longer depends on the working tree at deploy time; stale files are removed safely.
- One integrity format replaces three, and a missing hash stops being a DEBUG line.

### Negative
- Five steps across two repos. Step 4 is NexusMind's, and nothing is enforced until it lands.
- The deploy host needs Hub credentials for detector deploys.

### Risks
- A backfill taken from the wrong copy freezes the wrong bytes as canonical. Backfill from what NexusMind
  serves, and hash-compare against the live files.
- Prune is a deletion in another repo. It is safe only if the previous manifest is correct, so step 1 runs
  in reporting mode until the manifests match NexusMind exactly.
- Required integrity can take a detector down (an availability failure, worse than anything ADR-022's
  staging was calibrated for). Log-only first, then flip per detector after a clean run.

## Revisit if
- NexusMind moves detector inference to gpu-server's REST API entirely (then the placement target changes).
- A detector grows past what the Hub free tier or LFS handles comfortably.
