# 2026-08-26 — #132 closed and verified live; the number it rested on was one cycle wide

**No spend, no model, no filter, no scoring-path change.** All code in **NexusMind**
(`7adb615`, `5fce395`, `2a51e9d`), pushed, deployed to sadalsuud and **outcome-verified**.
This repo carries the decision record, the standards updates and the evidence.

## ✅ #132 — `data/prefiltered_out/` has a retention policy instead of luck

The violence-promotion gate's shadow log was in **neither** the cleanup path nor the
archive path. Nothing swept it and nothing preserved it: it survived on the absence of a
matching glob, which made "leave it growing" and "nobody has looked at this"
indistinguishable from outside. Owner picked option 1 — archive it on the
`filtered/`+`blocked/` path.

| | |
|---|---|
| archive | `data/archived/prefiltered_YYYY-MM.tar.gz`, one directory **per gate** inside the tarball |
| sweep | the same 14-day cleanup, **fail-closed** — nothing deleted unless the archive step reported `errors == 0` |
| retention | `prefiltered_*.tar.gz` added to `cleanup_old_archives` |
| off-site | added to `sync_backup.sh`'s `BACKUP_PATTERNS`; **first upload Sun 2026-08-30 03:03** |

**Verified live at 17:36**, via `--snapshot` → the real `nexusmind-cleanup.service` →
`--verify`: 183 loose files → **100 archived and removed, 83 inside the cutoff untouched**,
exit 0. Confirmed **independently of the asserting script**: `tar tzf` gives 29 + 71 =
**100** members. 8.9 MB loose → 1.28 MB of tarballs.

⚠️ The verifier **exits 2, not 0**, when nothing is past the cutoff — a zero from an
instrument that could not have said yes is not a pass.

## ⛔⛔ The keeper: a number that was verified, correct, and one cycle wide

The decision rested on *"90.6% of flagged rows never reach the block ledger, so the shadow
log is not redundant with it."* Real measurement, exact join (39 of 39), checked **before**
the decision rather than after. It was **one file, one cycle** — and it reached a GitHub
issue, a decision record, an ADR index, a spec, four docstrings and three commit messages
before anyone asked what its window was.

| | flagged | in ledger | kept | kept % |
|---|---|---|---|---|
| pooled, **12 joinable cycles** (08-24 .. 08-26) | 4,801 | 561 | 4,240 | **88.3%** |
| per-cycle range | | | | **72.5% – 92.9%** |
| ⛔ ledger seeding flush (excluded) | 239 | 239 | 0 | 0.0% |

**90.6% was the second-highest of twelve.** The conclusion is unchanged — the argument
rests on the **worst** cycle, and even at 72.5% the ledger is missing most of the flagged
population — but every copy now carries the pooled value plus its window and says
**re-measure, do not quote**: `NexusMind/scripts/research/measure_shadow_kept_share.py`.

⭐ **1,497 green tests, 11 of them new, 8 failing against the code they replace, 6 mutations
all killed — and none of that machinery can fire on this defect, because the defect was in
the EVIDENCE, not the code.** The evidence layer has no test suite, and a quantified claim
is the thing most likely to be propagated verbatim and least likely to be re-derived,
precisely because it arrives already labelled *measured*. Filed as
**augmented-engineering#38**.

Two instrument rules the wider window produced, both now in the script:

- **A newly-deployed ledger's first run is a backlog flush, not a cycle.** Pooling it in
  drags the share to 84.1%. It is printed and labelled rather than dropped — a run excluded
  without being shown is indistinguishable from one that was never there.
- **A flagged run whose ledger file has aged out is NOT "0 blocked" — it is unobservable.**
  Counting those as zero manufactures a 100% kept share out of retention alone, in the
  flattering direction.

## ⛔ Second keeper: `systemctl is-active` answered for the WRONG UNIT

The deploy touched `scripts/main.py`, which the pipeline imports, so the rule is "pull when
the service is inactive". `nexusmind.service` read `inactive` at 09:18:55 — **and the box
was not idle.** Cleanup is a **separate unit**, `nexusmind-cleanup.service`, chained by
`OnSuccess=` and running `scripts/main.py --cleanup-only` in its own cgroup (deliberately,
NM#210, so an archive OOM cannot fail the parent). It stayed `activating` another **8
minutes**, executing the exact code path the deploy was about to replace.

⭐ **This is the pgrep rule's own recommended remedy failing.** `working-rules.md` says: do
not use `pgrep`, ask the service manager. Correct, and not enough — **it answers for the
unit you NAME, and a chained unit is a different name.** The instrument was sound, its
answer was true, and it was not a function of the question being asked. 6th occurrence;
`CLAUDE.md` and `memory/working-rules.md` both updated.

The tell was in the output: the main unit's last log line was `--- Step 5: Cleanup ---`,
timestamped at the moment the service reported itself finished. I read a handover as a tail.

## Two defects I shipped and caught before deploying

1. **The writer appends the flagged COUNT after the timestamp**
   (`flagged_20260826_031106_485.jsonl`). A date regex copied from `blocked_*` matches
   **nothing**, and fails silently — "no expiring files to archive" every run, forever,
   while the directory grows. Every real filename on the box carries the suffix.
2. **My first sweep globbed `flagged_*.jsonl` + mtime.** That glob is *wider* than the
   archiver's date regex, so an odd-named file would have been deleted **un-archived**. It
   now deletes exactly the paths the archiver reports putting in a tarball
   (`archived_paths`, appended only after the temp archive is moved into place).
   **A sweep must not reach further than the thing that preserves what it deletes** — the
   `data/raw/` dotfile incident (NM `96b29f3`) one week later, in the other direction.

## Also

- **Q11 opened** (`memory/violence-promotion-v1-hypotheses.md`): flagged volume rose ~66%
  in three days (280 → 495, then a plateau). ⛔ **Not a finding** — the raw count has never
  been divided by the cycle's own scored population. Both numbers are in the pipeline's own
  log lines. Cheap to settle.
- **NM#404 commented, not decided**: its headline 51.4% is, by its own argument, *"a share
  that reflects how long the corpus has been running"* — window-dependent, so re-measure
  before it justifies persisting quality in the saved cluster record.
- `docs/decisions/README.md` had **one** 2026 entry indexed of four; the 08-14, 08-25 and
  08-26 records are now listed.
- CLAUDE.md went over the 40k warn when the pgrep rule grew; two REMOVED-filter rows were
  merged to pay for it (39,955). **That is not a strategy** — the next structural session
  has to move content out, same shape as #123 one layer up.

## Next session

1. **NM#404** — decide whether the stored `other_sources` shape carries real quality.
2. **Q11** — divide flagged count by the cycle's scored population before reading a trend.
3. **Confirm the Sunday 03:03 backup uploaded `prefiltered_*.tar.gz`** (one `rclone lsf`).
   NM#403's `blocked_*` first tarball is due ~09-07 and stays open until then.
4. **CLAUDE.md structural cut** — content out to topic files, not whitespace.
