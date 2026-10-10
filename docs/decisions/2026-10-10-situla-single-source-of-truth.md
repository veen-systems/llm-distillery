# situla is the single source of truth; GPU hosts are scratch (2026-10-10)

## The ruling (owner, in session)

> "make sure we set up proper experiments, and data for that. Situla should be single-source-of-truth.
> gpu machines are slaves to that"

The same principle reached this session from the NexusMind session the same day, as the owner's: *situla
is the single source of truth (its restic backup `~/.local/bin/situla-home-backup.sh` covers all of
`$HOME` except caches/venvs/`__pycache__`). GPU hosts are scratch: bring data and code there, run, pull
results back to situla, then the host copy is disposable.* The owner then asked for the same inventory on
all four hosts: b650-gpu, sadalsuud, sadaltager, gpu-server.

What follows is the assistant's implementation of the ruling. **The ruling is the quote above; the layout,
tool and check below are the assistant's design**, reviewed by four review agents (2026-10-10) but not by
the owner line by line. The NexusMind session said it will port the same tool and field names once
they are committed (`~/nm-lab`, `$NM_LAB`); at writing its pulls were still plain rsync.

## Why it was needed

Measured 2026-10-10; commands and full lists in `docs/evidence/2026-10-10-host-data-inventory/README.md`:
- b650-gpu held the only copy of the three gated belonging candidates' weights (`v1_adj1`, `v1_c2a`,
  `v1_c2b`), the human_thriving v8 adjudication runs, and `v8_corpus/`. Six evidence dirs named
  `b650-gpu:~/v8_corpus/` as their inputs' durable home (five literally, one as "the b650 pool").
- `docs/RUNBOOK.md` § *Train on GPU* said the weights "live only on the training host". That was the
  convention, not an accident.

## Layout

| Where | What | Rule |
|---|---|---|
| `~/ld-lab/inbox/<host>/<date>/<item>` | a clean-up pull of host data whose home is not decided yet | triage it into `experiments/` or `datasets/` BEFORE the host copy is deleted: an uncited tree may simply be moved; a cited one cannot (re-pulling needs the host copy) |
| `~/ld-lab/experiments/<date>-<name>/` | a planned run's off-repo outputs: weights, dumps, logs | a planned run pulls STRAIGHT here (RUNBOOK) |
| `~/ld-lab/datasets/<name>/<vN>/` | immutable corpora too large for the repo and cited by hash (`v8_corpus/v1`) | never edited in place; a change is a new `vN` |
| repo `datasets/` (git-ignored, on situla) | the working inputs that scripts read by path | **unchanged**: it is already under `$HOME` and backed up, and hundreds of paths name it |
| `docs/evidence/<dir>/MANIFEST.json` | which lab files an evidence dir rests on: path, sha256, size, origin host, date | written by `lab.py cite`, checked by `check_lab_manifests.py` |

`$LD_LAB` or `--lab-root` overrides `~/ld-lab`. It is a plain directory, not a git repo. ⛔ **Never move or
rename a tree after citing from it**: `MANIFEST.json` records the lab path, and the check fails the
evidence dir when the path stops resolving.

## The flow

1. **Code to the host by commit** (`git fetch && git checkout` on b650; RUNBOOK § *Train on GPU*).
   **Data to the host from situla** (rsync from the repo's `datasets/` or the lab).
2. Run.
3. **Pull back: `scripts/lab/lab.py pull host:path <dest>`.** dest must be new; the tool lists every
   file and symlink on both sides, hashes them, and exits 1 unless they are identical. A symlink whose
   data would not be in the copy (dangling, absolute, or outside the tree) refuses the pull. A pull that
   did not print `OK` did not happen. A copy made by other means is checked with `lab.py adopt`.
4. Cite what the evidence rests on: `lab.py cite docs/evidence/<dir> <lab path>...`.
5. The host copy becomes disposable once **both**: the pull printed `OK`, **and** a restic snapshot
   taken after the pull contains it. The backup runs daily at 12:00 (`situla-home-backup.timer`), so a
   morning pull is not backed up until that afternoon. Confirm with
   `restic snapshots` / `restic ls latest <path>`. ⛔ **Until the owner rules otherwise, deleting the host
   copy is per item with the owner's go** — no tool here deletes anything on a host.

## The check

`scripts/verification/check_lab_manifests.py`, also run by the test suite against the real evidence tree
(`tests/unit/test_lab_storage.py::RealTree`: the citation half everywhere, the lab half by size only and
only on situla; the full sha256 comparison is a hand run):
- every evidence `MANIFEST.json` entry must exist on situla with its recorded sha256 and agree with the
  pulled tree's own `_LAB_MANIFEST.json` (hash and origin), and no `MANIFEST.json` may be empty;
- an evidence unit that cites a scratch-host path needs a manifest entry covering that path, and one that
  only names a pure scratch host (`ssh b650-gpu`, `on b650-gpu`, `b650 only`) needs a non-empty manifest.
  Scratch hosts by default: b650-gpu, b650, gpu-server, sadaltager, and sadalsuud outside `~/local_dev/`
  (NexusMind's production tree);
- a unit that names hosts without resting on host data (an inventory of the hosts) declares it with a
  line `lab-check: not-host-data: <reason>`; it is reported as EXEMPT with the reason, never silent;
- enforced per citation, not per date: anything not covered fails unless it is in the committed baseline
  `scripts/verification/lab_manifest_baseline.json`, which froze what the evidence already cited on
  2026-10-10 (37 units, many of them host `/tmp` paths that are already gone). So a new citation added
  to an old dir fails too. ⛔ Regenerating the baseline (`--write-baseline`) is a loosening: review the
  diff as one.

Its blind spots are listed in its docstring: prose that names no host, `/home/...` paths with no host,
`experiments/registry.jsonl`, files over 2 MB, and a push TO a host written as `host:path`.

## Experiment protocol additions (the "proper experiments" half)

The registry, pre-registration and held-out gate already existed (`experiments/README.md`). The gap the
2026-10-10 belonging observation exposed: every gate asked *"does this article pass?"*, and none asked
*"what does the reader see at the top?"*. belonging v3 passed its gate, and the owner then reported that the
top stories on ovr.news's Belonging page "show at least half personal stories" (their seven linked stories
are all v3-scored; any share beyond the owner's reading is Claude's read of titles, not a judged count:
`docs/evidence/2026-10-10-belonging-v3-top-of-page/README.md`).

The additions are in `experiments/README.md` § *Protocol* and the skeleton
`experiments/PREREGISTRATION.template.md`. **They are the assistant's proposal, made in session; the
owner's reply was the ruling quoted above, not an approval of each item.** They are not yet enforced by
any checker: `docs/TODO.md` carries the item to add them to the registry schema.
