---
name: project-session-2026-10-10-situla-ssot
description: Session 2026-10-10/12 — belonging v3 top-of-page is mostly single-person (owner); bar RULED ≤ 6 of top 30; experiment protocol extended (prose); situla ruled single source of truth — lab tool + manifest check built, 2 review rounds, all LD host data pulled and verified, 18 host items deleted on sadalsuud/sadaltager
metadata:
  type: project
---

# Session 2026-10-10 → 2026-10-12

**Spend:** $0 oracle. Claude review subagents: 6 (round 1: 4, round 2: 2). No GPU. **Deployed:** nothing (no filter
package changed). Commits `cd34268`, `36afa99`, `f49e1b8`, `a1aebbb`, `18e46ee` + this close, all on main, pushed.

## The ask and the threads

Opening ask: "the new belonging filter … mostly personal stories popping up … coincidence? or did we do something wrong?"
Then: "should we setup proper experimentation"; NexusMind relayed the owner's storage request; owner: "Situla should be
single-source-of-truth. gpu machines are slaves to that"; "look at b650, sadalsuud, sadaltager, gpu-server";
"help me through decisions"; close with "continue" landing on the next step, and prune the read surface.

| Thread | State |
|---|---|
| belonging: personal stories at the top | ⏳ partial: cause narrowed (no `out_one_moment` negatives in v3 by ruling; community_fabric capped at 6.3335), bar RULED ≤ 6/30; the judged count is TODO **0a** |
| proper experimentation | partial: Protocol + PREREGISTRATION template written; NOT enforced (#173) |
| situla as source of truth | ✅ built (`scripts/lab/lab.py`, `check_lab_manifests.py`, 35 tests, suite-wired); all LD host data in `~/ld-lab` (20 GB), snapshot `6b927ccf` holds it |
| host cleanup | ✅ sadalsuud (16) + sadaltager (2) deleted after three checks; ⏳ b650 + gpu-server: owner "stay as they are for now" (#172) |
| NexusMind port of the lab tools | not mine: NexusMind (told `cd34268`; it will `adopt`) |
| oracle vendor terms on training from outputs | not mine: owner (#174) |
| pre-existing suite failure `test_framework_language` on `docs/TODO.md` (`Herstel`) | not mine this session: present at `a1b320d`; still red |

## What I got wrong (all caught; listed so the next session reads them)

- **Two answers to the owner that I had to retract**: "yesterday's batches were mostly community" (those were v1 rows draining —
  community_fabric 7.4 is impossible for v3) and "the personal ones are v3's lowest scorers" (the top story was one).
  Both from reading ovr.db without the version stamp. → the Protocol now says join to NexusMind's stamp.
- **Proposed re-running a rejected experiment** (add the 121 single-person negatives = c2a, EXP-046) until the registry showed it.
- **Two false claims to a peer** (ovr.news) about our own practice: "non-Claude judges" (ours are Claude) and "we pin and
  record model ids" (#157 says nothing stamps the DeepSeek model). Both corrected by message.
- **Round 1 of review refuted my tool** (re-pull overwrote cited copies; symlinks invisible), **round 2 refuted round 1's
  fixes** (wrong origin for single files, dest escape, citation forms still missed, exemption boundary) — the fixes were the
  least-reviewed code, again.
- **Tooling slips:** a `while read` loop lost all but item 1 (ssh ate stdin); a Python edit opened a file for writing before
  reading it (emptied a scratch script); a commit message claimed an edit that an aborted script never applied (`36afa99`,
  fixed in `f49e1b8`); the deletion guard's `restic ls` was not recursive (gotcha-log 2026-10-12).

## Read surface

758,893 chars at close (755,807 on 10-10): +3,086, mostly this session's ledger row, TODO 0a and gotcha entry. The archive
pass is TODO item 2 (#163), next after 0a.
