# llm-distillery data on the four hosts, pulled to situla (2026-10-10)

<!-- lab-check: not-host-data: an inventory of what was on the hosts; the data itself is in ~/ld-lab and each pulled tree carries its own _LAB_MANIFEST.json -->

Owner request (via the NexusMind session, then directly): inventory llm-distillery's experiment data on
b650-gpu, sadalsuud, sadaltager and gpu-server, and propose storage on situla. Ruling and design:
`docs/decisions/2026-10-10-situla-single-source-of-truth.md`.

**Nothing was deleted on any host.** Every item below was copied to `~/ld-lab/inbox/<host>/2026-10-10/` with
`scripts/lab/lab.py pull` and then re-checked against the host with `lab.py adopt` (current manifest format:
kind, links recorded): **identical on both sides**, file by file, by sha256. gpu-server `llm-distillery/` was
pulled with the current tool directly (669 files + 1 link, 6.58 GB; venvs and `.git` excluded). `v8_corpus` was moved to
`~/ld-lab/datasets/v8_corpus/v1` before it was cited; its corpus and cohort hashes match the ones the
2026-08-29 evidence recorded (`5e2cf729…`, `48d740a7…`).

## Method (re-runnable)

```bash
ssh <host> 'cd ~ && ls -la && du -sh */ | sort -h'                       # names and sizes
git grep -l -- <name>                                                    # does LD reference it?
# what b650's checkout held that situla's did not hold identically (5 subdirs; -c also counts files that DIFFER):
for d in datasets filters audit runs staging; do
  rsync -rcn --out-format='%n' --exclude='__pycache__' --exclude='*.pyc' \
    b650-gpu:llm-distillery/$d/ ./$d/ | grep -v '/$' | wc -l; done     # 31 166 64 35 44 = 340
python3 scripts/lab/lab.py verify <dest>                                 # any time later
```

Ownership was decided from the name, the date and whether this repo references the path. **Not by opening
contents**; the NexusMind session agreed the split by message.

## Pulled (LD's)

| Host | Items | Note |
|---|---|---|
| b650-gpu | `llm-distillery/` (checkout minus venvs and `.git`: 3,548 files, 4.3 GB), `v8_corpus/`, `enrich_pilot/`, `belonging_v1_adj1_run1_discarded/`, `belonging_v1_adj1_run2_superseded/`, 15 `belonging_*` logs/gate/leak files, `c2_remote.sh` | the gated belonging candidates' and the v8 adjudication runs' weights existed only here |
| sadalsuud | `belonging_leak_check/` (4.7 GB), `solutions_screen_work/`, `solutions_v6_pool.jsonl`, `solutions_v4_normfit_sample.jsonl`, `ld92_*`, `retired_filters_foresight_sustech_20260803.tar.gz`, scripts `build_pool.py` `sample_designs.py` `gn_trend.py` `shortsrc.py` `stub_lang.py` `volumes.py` `tc_prod.py` `verify_gpuserver.py` `verify_neardup.py` `contract_a_smoke.py` | home-dir work files, outside NexusMind's `local_dev/` |
| sadaltager | `llm-distillery-backup/`, `hf-archive-from-gpu-server/` (an HF cache of cultural-discovery-v4) | |
| gpu-server | `solutions_v4_rescore_corpus.jsonl`, `ab_articles.jsonl`, `ab_results.json`, `run_calibration.sh`, `solutions_screen_work/` (2.6 GB, 58 files, 10 in-tree symlinks), `llm-distillery/` (6.2 GB by the host's `du`) | gpu-server's disk is 91% full (NexusMind's reading) |

## Not LD's (left alone)

b650-gpu `mondriaan/`, `fluxus-lang-exp/`, `nearmiss/` (empty), `e15/` (story-dedup: NexusMind took it),
`augur-*`, the `nm*`/`NexusMind`/`nexusmind-scorer` dirs; sadalsuud `augur-latency/`, `scratch-claude/`
(mostly FluxusSource, flagged to the owner by NexusMind), `fluxus_16h_check*`, `nm*`; sadaltager
`fluxus-lang-exp/`, `torch-test/`, gpu-soak files, `nexusmind-scorer/`; gpu-server's podcast/TTS work
(`ep01_*`, `qwen-*`, `podcast-generator/`, `voice_refs/`), `vmodel-daemon*`, `logo-classifier/` (NexusMind
checking), `retired_2026-09-28/` (likely NexusMind's scorer retirement, NM#395).

## Status and what is NOT done

- **Backed up?** Not yet when written: the restic timer runs daily at 12:00 and `~/ld-lab` was created at
  08:51. A host copy is disposable only after a snapshot contains it (decision record, flow step 5).
- **Host deletion:** none. Each needs the owner's go, item by item.
- **Triage:** everything sits in `inbox/` except `v8_corpus`. Moving an item to `experiments/` or
  `datasets/` means pulling or adopting it again at the new path, not `mv`, once anything cites it.
- **Pending:** nothing; `ls ~/ld-lab/inbox/*/2026-10-10/*/_LAB_MANIFEST.json`
  shows which trees are done.
- **Evidence backlog:** `check_lab_manifests.py` lists the older evidence dirs that name host paths (frozen in
  `scripts/verification/lab_manifest_baseline.json`). Many
  are host `/tmp` paths that no longer exist; this pull cannot recover those.
