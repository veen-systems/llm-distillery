# Session 2026-09-27 (evening) — H-DP3 confirmed; retired detectors stop shipping; TODO retire

**Ask:** "continue" (TODO item 0: close H-DP3), then owner "both yes" (stop shipping + delete the retired
detectors; delete the stale Hub repo), then the close ritual with an explicit push to prune the read surface.
**Cost:** $0 oracle, no GPU. **Deploy:** llm-distillery side live on push (deploy-script input only);
NexusMind side = PR ducroq/NexusMind#553, OPEN at close.

## Threads
- ✅ **H-DP3 CONFIRMED** (closed). NexusMind PR #550 (`dafbbc9`) pulled on sadalsuud at 16:08:55 CEST, before
  `deploy_filters.sh` finished 16:08:58; `verify_detector_package.py verify --all --target
  sadalsuud:~/local_dev/NexusMind --strict` → 4× OK, exit 0; served commit `80bf318` has no `.pkl`/`.safetensors`
  (`git show --stat`). Wider than predicted: it also carried the retired detectors' #158 blocks. Recorded in the
  ledger, ADR-024, llm-distillery#165 comment. Reproduced independently by the adversarial reviewer.
- ✅ **Retired detectors stop shipping** (ours closed): `3e7f565` + review fixes `5590f88`,
  `common_runtime_files.RETIRED_DIRS` = obituary v3/v4, commerce v2. Evidence nothing loads them (NexusMind `main`
  `1d724a9`): `commerce.py` pins v1 and discards the gpu client (LD#80), `obituary.py` pins v5, gpu-server's
  `CommercePrefilter` is defined in `main.py` and reads `deploy/gpu-server/models`; grep for the three paths finds
  nothing, control grep for v5/v1 finds 7 files. Mutants: exclusion removed → 5 tests red; any-segment match → 2
  red. Dry-run control: exclusion removed → deploy re-creates all three dirs; present → none.
- ⏳ **NexusMind deletion** (partial): PR #553, 25 files, branch off `1d724a9` from a fresh clone; nexusmind-b2
  told. Commerce v2 pickles were NexusMind-only (recovery: `git show c9b0fb2^:<path>`, commented on the PR).
  gpu-server keeps orphan `{v3,v4,v2}/models/*.pkl` (rsync excludes `models/` from `--delete`) — theirs.
- ✅ **Hub repo `jeergrvgreg/commerce-prefilter-v1` DELETED** (irreversible, owner yes). Checked first: private,
  0 downloads, last modified 2026-07-28, `model.safetensors` sha256 `ac899bbc…` = `commerce-detector`'s pinned
  copy; unique content was only a model card and the non-production tokenizer files. 404 confirmed (authenticated).
- ✅ **Read surface**: `docs/TODO.md` 80,441 → 57,999 B (258-line START HERE block moved verbatim to
  `docs/TODO-archive.md`; containment check, seeded one-char defect detected). New START HERE written.
- ✅ Review battery: 3 lenses (guarantee+reachability+sync, adversarial+claims, doc-accuracy; opus/sonnet/haiku),
  0 blockers, 1 warning + 3 notes fixed. Suite `1102 passed, 25 skipped` (`.venv`, clean tree, alone).

## Mine
- A grep over a nonexistent path read as a clean negative → 3 stale comments that review found (gotcha-log entry).
- The first background poll piped through `tail -3`, so its interim output was empty and uninformative.
