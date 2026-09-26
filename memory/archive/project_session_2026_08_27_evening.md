---
name: project_session_2026_08_27_evening
description: Two trims of CLAUDE.md that found three stale claims, and a six-release framework adoption where the globals turned out to be current already.
metadata:
  type: project
---

# 2026-08-27 evening — the pin caught up, and the treadmill under it got measured

*No spend, no model, no filter, no scoring-path change, **nothing deployed**.* Every
changed file is `CLAUDE.md`, `docs/`, `memory/`, `.claude/skills/` and one evidence doc.
Nothing touches a path that reaches NexusMind — **deploy is N/A, not skipped.**

## What was asked

Started at *"where were we?"*. Then: recommend a next move, do the `CLAUDE.md` size fix,
recommend again, do a second pass, run `/update-drift`, apply what it found, send the
framework feedback to the peer session, wrap up.

## ⛔⛔ THE KEEPER — the audit-time headroom figure is not a growth rate

I was one sentence from recommending we skip the second trim, on the reasoning that
`CLAUDE.md` had moved "one byte in a full cycle" — a figure from the morning's own
write-up. Measuring it first refuted that:

| date | size |
|---|---|
| 2026-08-16 (post-audit trim) | 35,094 |
| 2026-08-26 | 39,955 |

**~486 bytes/day.** The morning figure was *headroom at audit time* — the file is trimmed
to the wall and refills. A stable-looking number and a stable file are different things,
and the number is measured at exactly the moment that hides the growth. Filed as **#133**
with the options; owner decision pending.

⭐ The stronger argument for the routing rule is not size. **All three stale claims found
today were in the always-loaded layer**, and each restated a number or state that lives
elsewhere. The pointer table is the part that *rots*.

## Three stale claims, all found by trimming rather than by reading

1. **"109 owned fields"** — the register was regenerated and reads **125** for its window
   (NexusMind `20b1898`). Two hand-maintained copies of a number.
2. **"the six deployed filters were never assessed"** — assessed under **#97** (closed
   08-07); the publication defect *that* found was remedied 08-06. I verified the remedy
   held rather than trusting the record: 126 rows still carry >500 chars, reconciling
   **exactly** as 115 deliberately-retained (`commerce_prefilter/test.jsonl`, live gate
   input) + 11 documented `datasets/adverse/` rows.
3. **`docs/BLOCK_LEDGER_SPEC.md` headed "NOT yet deployed"** — three days after it went
   live, while entries below it dated 08-25/08-26 already assumed it was.

⭐ **The third surfaced only because I chased a −1.** Resolved-unique went 401 → 400 after
the trim; the dropped path was the qualified pointer to `verify_block_ledger.py`, which is
what exposed the *unqualified* one underneath — and this repo has no such path, so it
resolved to the wrong repo and read as correct.

## The trims

**117 → 2,538 bytes of headroom** across two passes, and **nothing was deleted that
lacked a home**: seven of the eight fat rows were already fully homed, checked atom by
atom. Only one write was needed — the GN undercount *mechanism*, derived from the file's
own table rather than carried: a `gn_` prefix is **5.1×** low on feeds but **1.73×** low
on items, so the item-share sanity check reads roughly-right while the feed population is
off five-fold.

## `/update-drift` — six releases, and the globals were already current

**3 adopt / 1 decline / 4 n/a / 9 already in force.** Stamp bumped `v1.26.0` → **v1.31.0**
in both places; the 08-26 hold is discharged with every item named.

⭐ **`audit-context`, `update-drift` and `curate` were already at v1.31.0** — each differs
from upstream's template by *only* the installer's SAVE-AS → frontmatter conversion.
⛔ **Method, because the naive one is wrong:** diff the installed file against **every
tag** and read which one minimises. Diffing against latest returns "differs" for both
*behind by four* and *current plus installer*, and the wrong reading is the one that makes
an adopter re-copy a re-mapped skill.

The three adopts all landed in `review-changes` (RE-MAPPED, 461 vs 413 lines — surgical
patches, never a re-copy): #52 frontmatter, #50 emphasis spans, #89 hypothesis routing.

⭐ **The controls mattered more than the positives.** The #52 fix sits directly above the
table check, so the run asserted a genuinely lossy table **still fires** afterwards. A fix
that silences its neighbour is indistinguishable from one that works.

**Declined with a reason:** v1.29.0's exit-2 third state for the local `refcheck.py` fork —
no `sys.exit` anywhere in it, `run.sh` exits on its own count, no CI, nothing calls it.
A mechanism with no caller.

## My own errors this session

1. **A verification command that errored and printed the reassuring branch.** Checking the
   evidence-doc fix, my `$( ... )` had escaped quotes; awk failed to open the file and the
   `[ -z ]` test read the empty output as success — `silent (FIXED)` on a broken run.
   Re-run properly with a positive control: file clean, control fires, repo sweep 1 → 0.
2. **`cp -al` across filesystems, with a `|| cp -a` fallback.** /tmp is tmpfs, hardlinks
   cannot cross devices, and the fallback copied the repo *into* the half-made directory.
3. **`git archive HEAD` as a baseline tree** — it excludes gitignored paths, so it reported
   240 fake findings. The clean-clone trap, again.
4. **A predicted +5 that was never mine.** Resolved-unique read 401 against the morning's
   recorded 396; HEAD gives 401 too. The morning figure was recorded mid-session.

## Verification battery

| check | result |
|---|---|
| reference integrity | **1 finding**, 400 resolved — the deliberate `nm188_*` break |
| `tests/unit` | 350 passed, 4 skipped |
| adopted awk, 4 cases | #52 fixed · lossy-table control fires · #50 positive fires · #50 negative silent |
| repo-wide table/emphasis sweep | **1 → 0** after escaping the pipes at `cd-v5-op-point-band-followup.md:99` |
| budgets | `CLAUDE.md` 37,462 (2,538 free) · index 18,893 |

## Next session

1. **#133 — the routing-rule decision.** Owner's; three options, recommendation is option 1
   with a carve-out for money/wrong-number prohibitions.
2. **Reply from the `agent-ready-projects` peer session** on the three feedback items;
   offered to file them as issues.
3. `nm188_mojibake_derived.py` — someone who remembers the experiment.
