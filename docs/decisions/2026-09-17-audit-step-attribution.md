# `/audit-context` Step 8 — what each check has ever caught here

**Date**: 2026-09-17 · **Trigger**: `docs/TODO.md`'s "Run `audit-context` Step 8
(retirement) here", queued by the 2026-09-17 `/update-drift` triage of framework
v1.45.0.

## The standing rule this file exists to enforce

⛔ **Every `/audit-context` close records each finding WITH THE STEP THAT FOUND IT,
and appends it to the table below.** Without attribution an audit cannot tell a check
that works from a check that has never had a subject, and the default becomes keeping
everything. That is not hypothetical: **this table had to be excavated from seven
audit commit messages**, because no prior audit recorded step→finding. The excavation
is the whole reason Step 8 is hard to answer, and it gets harder every audit.

## What each step has caught in this project

Reconstructed 2026-09-17 from `9f28088`, `f272e6d`, `d2d5f24`, `4b5b28a`, `55d0e89`,
`1f78b5b`, `b5d0179` and the session records they name. Where a catch is attributed by
inference rather than by a contemporaneous record, it says so.

| Step | Catches | Verdict |
|---|---|---|
| **1** size | 2026-08-16 `CLAUDE.md` 39,177→34,778; 2026-08-29 38,204→37,445; **two budget-SCOPING defects** (08-16 "the budget governs 71% of it"; 08-29 #138, 19,488 auto-loaded bytes in no target at all); 2026-09-17 the layer over SOFT, **attributed to the auto-memory index at ~370 B/day against `CLAUDE.md`'s ~19** | **Keep.** Highest-yield step here, and its best catches are about its own scope |
| **2** duplication | 2026-08-12 late: "duplicated numbers 7 → 3" | **Keep, with a cadence caveat.** Now largely covered per-session by `scripts/verification/check_doc_claims.py` (5/5 green 2026-09-17), so the monthly prose step is the weaker half of a pair, not the only instrument |
| **3** wrong-layer | **No independent catch found.** The 2026-08-16 relocations were Step 1-driven; Step 3 named the destination | **Keep on the prevention defence** — `CLAUDE.md` has no `## Active work` list and no session narrative (both verified absent 2026-09-17), which is what this step prescribes. Rests on the ⚠️ ambiguity, recorded not decided |
| **4** references | 2026-08-13 three dead auto-memory pointers; 2026-08-27 24→1; 2026-09-11 **`refcheck.py` had no `sys.exit` and could not fail**; 2026-09-17 23 findings, incl. a shape test ruling 3 correct references STALE forever | **Keep** |
| **5** reachability | 2026-08-12 late, 1 orphan; 2026-08-29, 1 orphan homed; 2026-09-17 three unlinked session records, one of them **asserted absent while sitting in the same directory** | **Keep** |
| **6** drift | 2026-08-15 **a premature stamp had silenced its own drift check**; 2026-08-27 a hold with no release condition | **Keep** |
| **7** gitignore | **No catch in its whole recorded history.** The only audit that reports on it (`memory/archive/project_session_2026_08_29_late.md:25`) says "gitignore correct". The one real gitignore finding on record — `.claude/review-profile.md` untracked and unignored, 2026-09-11 evening — came from `/review-changes`, **not from this step** | **Retirement candidate — NOT retired.** See below |

## Step 7: the retirement that was not taken, and why

⚠️ **This rests on the ambiguity Step 8 names and does not resolve it.** A check that
has never fired may be preventing what it checks for, and the record cannot tell you
which.

Step 7 is **kept**, for a reason that is not "it might be useful":

* It **does** have a plausible prevention story. "Do not commit secrets, do track the
  context artifacts" is exactly the class where the prescription changes what an
  author does, so a zero is consistent with the check working.
* The class is **not covered elsewhere**. `.githooks/commit-msg` guards unverified
  deploy claims, not tracking. Retiring would leave it unchecked, which would have to
  be an explicit decision rather than a side effect.
* Its cost is one `git ls-files` per month against an unbounded downside.

⛔ **What would change this**: a Step 7 that has still caught nothing by 2026-12-17,
**and** a mechanised tracking check landing somewhere per-commit. Then it is a
per-session check replacing a monthly one, and the retirement is a gain rather than a
loss. Do not retire it on the zero alone.

## Tombstones

*(none yet — nothing has been retired from `/audit-context` in this project)*
