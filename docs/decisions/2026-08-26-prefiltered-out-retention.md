# `data/prefiltered_out/` gets a retention policy — 2026-08-26

**Decision:** option 1 of llm-distillery#132 — **archive it on the same path as
`filtered/` and `blocked/`**, then let the cleanup sweep the loose files.
Implemented in NexusMind `7adb615`.

**Status:** shipped, deployed and **VERIFIED LIVE on sadalsuud, 2026-08-26 17:36.**

| | |
|---|---|
| before | 183 loose `flagged_*.jsonl`, 8.9 MB — 100 past the 14-day cutoff, 83 inside it |
| after | **100 archived and removed, 83 untouched**, verifier exit 0 |
| archives | `prefiltered_2026-07.tar.gz` (385 K, 29 members) + `prefiltered_2026-08.tar.gz` (895 K, 71 members) = **100**, every member under `prefiltered_YYYY-MM/violence_promotion/` |
| off-site | 2 files match `prefiltered_*.tar.gz` on the box; first upload at the weekly timer, **Sun 2026-08-30 03:03** |

The member count was confirmed with `tar tzf`, i.e. **independently of the script
that asserted it** — 29 + 71 = 100, matching the 100 the sweep removed.

## What was wrong with doing nothing

`NexusMind/data/prefiltered_out/<gate>/flagged_YYYYMMDD_HHMMSS_<n>.jsonl` — the
violence-promotion gate's shadow log — was in **neither the cleanup path nor the
archive path**. Nothing swept it and nothing preserved it. It survived on the
absence of a matching glob, not on a decision, which made "leave it growing"
(option 2) and "nobody has looked at this" indistinguishable from the outside.

That is the part worth fixing whichever option won: `data/raw/`'s state stores
turned out to be *inside* a deletion path for the same reason in reverse
(`pathlib.Path.glob` matches dotfiles, NexusMind `96b29f3`). A directory whose
fate is set by which globs happen to exist is a directory whose fate is luck.

## Why it was not retired, which was the obvious move

`violence_promotion` now enforces, so its blocked rows land in the block ledger
and the shadow log looks redundant. **It is not.**

Measured over the **12 cycles the two tiers can be joined on** — the ledger only
starts 2026-08-24, so that is the whole observable window, not a sample of a
longer one — **pooled 88.3% of flagged rows never reach the ledger**, per-cycle
range **72.5%–92.9%** (4,801 flagged, 561 blocked, 4,240 kept).
`NexusMind/scripts/research/measure_shadow_kept_share.py`.

The ledger records what a gate *blocked*; by construction it can never hold what
a gate flagged and let through. That population is exactly the evidence any
argument about where the threshold sits has to be made on — a recall/precision
claim about the gate cannot be computed from the ledger alone. ⭐ **The argument
rests on the WORST cycle, not the pooled one**: even at 72.5% the ledger is
missing most of the flagged population.

⛔ **This corrects the 90.6% the issue and my first four documents carried.** That
figure was one file, one cycle, and it sat near the top of the range — I quoted it
in five places before asking what its window was. The decision does not change;
the discipline does. Two things the wider window also exposed:

- **The ledger's first run is a backlog flush, not a cycle** — 239 flagged, 239
  blocked, 0.0% kept. Pooling it in drags the share to 84.1%. It is reported
  separately rather than dropped, because a run excluded without being shown is
  indistinguishable from one that was never there.
- **A flagged run whose ledger file has aged out is not "0 blocked"** — it is
  unobservable, and counting it as zero would have manufactured a 100% kept share
  out of retention.

⚠️ It is also not recoverable from `filtered_*.jsonl`, which is written under an
`if result["passed_prefilter"]` guard, nor from `data/raw/`, which predates the
stamp. **A flagged-but-kept row is persisted nowhere else.**

## Cost

Identity + score only, no content: `id`, `title`, `url`, `source`,
`_violence_promotion_score`, `pipeline_run_id`. **~200 KB per cycle, ~1.2 MB/day,
~36 MB/month** — against `nexusmind_*.tar.gz`'s 18.6 GB. It is the cheapest tier
in the archive and the local retention prune (`temporal.archive_retention_days`,
730) now reaches it like the rest.

## What shipped

| | |
|---|---|
| archive | `data/archived/prefiltered_YYYY-MM.tar.gz`, one directory **per gate** inside the tarball |
| sweep | the same 14-day cleanup, **fail-closed** — nothing is deleted unless the archive step reported `errors == 0` |
| retention | `prefiltered_*.tar.gz` added to `cleanup_old_archives` |
| off-site | added to `sync_backup.sh`'s `BACKUP_PATTERNS`, verified against a stub rclone |

Two traps are worth carrying forward:

- ⛔ **The writer appends the flagged COUNT after the timestamp**
  (`flagged_20260826_031106_485.jsonl`). A date regex copied from `blocked_*`
  without that trailing group matches **nothing**, and the failure is silent —
  "no expiring files to archive" every run, forever, while the directory grows.
  Every real filename on the box carries the suffix.
- ⛔ **The sweep deletes exactly what the archiver reported archiving**
  (`archived_paths`, appended only after the temp tarball is moved into place),
  not what a glob matches. The glob `flagged_*.jsonl` is *wider* than the date
  regex, so a glob-keyed sweep would delete an odd-named file the archiver had
  skipped. **A sweep must not be able to reach further than the thing that
  preserves what it deletes.**

## Verification

`NexusMind/scripts/research/verify_prefiltered_archiving.py` — runs the shipped
`cleanup_old_data()` and then asserts on the filesystem: every file past the
cutoff gone *and* present in a tarball under its own gate with the same row
count; every file inside the cutoff still there; nothing else in the gate
directory touched.

⚠️ **It exits 2, not 0, when nothing is past the cutoff.** A zero from an
instrument that could not have said yes is not a pass.

```
ssh sadalsuud 'cd /home/jeroen/local_dev/NexusMind && \
    venv/bin/python scripts/research/verify_prefiltered_archiving.py'
```
