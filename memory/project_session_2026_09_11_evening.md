# Session 2026-09-11 (evening) — framework drift adoption and the structural audit

**Spend $0. No oracle calls. No model trained. Nothing in `filters/`. Deploy N/A, not skipped.**
Two commits: `0b5cbe9` (drift), `b5d0179` (audit).

## What this session was

`/update-drift` → fix → `/audit-context` → fix → `/curate`, as instructed by the owner mid-turn.

## `/update-drift`: v1.36.1 → v1.40.0, 4 releases

**2 adopt, 0 decline, 2 not-applicable, 3 already-in-force.** Stamp bumped only after both
adopt items landed. Full per-release record: `docs/decisions/framework-adoption-history.md`.

⭐⭐ **THE LIVE DEFECT: `/review-changes` was BROKEN in this repo, and nothing said so.**
The 546-line project-local fork had been **inert** — Claude Code loads the user-global copy
in preference, so every edit to the local file changed nothing — and the global copy **STOPS**
without `.claude/review-profile.md`, which did not exist. The session-close ritual calls that
skill. The framework's own checker said so in one line:
`FAIL inert local copy: .claude/skills/review-changes/SKILL.md (shadowed by ~/.claude/skills/review-changes)`.

⚠️ **The onset is BOUNDED, not known** — `docs/TODO.md:5711` records an earlier check finding
no shadowing; v1.40.0 (2026-09-10) moved `review-changes` into `GLOBAL_SKILLS`. A window is
part of a source.

⚠️ **"We are not the one in the release note" was true and irrelevant.** v1.40.0 measured an
adopter whose copy had drifted to 768 lines and lost the `"$BASE"...HEAD` term. Ours carries
it. Ours was broken a different way.

## ⛔⛔ The keeper: I claimed an invariant was repaired and the outcome never changed

The PEFT-adapter guarantee named **no path at all** in the fork. I added
`filters/*/v*/model/**` to the HIGH row, named the caller, and stopped — **CLAUDE.md working
rule #1, violated inside the fix for the class of defect the rule exists for.**
`.gitignore:65` is `filters/**/model/`; the only re-include is `!filters/**/training_*.json`,
which does not cover `adapter_config.json`. **Every current production filter has 0 tracked
files under `model/`** (human_thriving v8, uplifting v7, cultural_discovery v5, belonging v1,
nature_recovery v4, solutions v6). Repointed at `scripts/deployment/*`.

⭐ **Both lenses were wrong about it, in OPPOSITE directions, and the truth was neither.**
Adversarial: `git ls-files 'filters/*/v*/model/'` → 0, a broken instrument (trailing slash,
no filename wildcard, matches nothing whatever is tracked). Doc-accuracy: 32 tracked,
counted correctly, concluded the pattern is diff-visible. The 32 all belong to DEAD filters
predating the ignore rule. Right conclusion on wrong evidence; right evidence with the wrong
conclusion. **The disagreement was the finding.**

## The review found more than the fix

Two lenses, 4 blockers + 9 warnings/notes on my own same-day work, all verified against disk
before acting:

- **Hand extraction dropped two tier rules** while the record claimed the tiering moved
  intact — including `docs/evidence/** is HIGH when it ships a .py`, over **58 .py files**.
- **Two tier holes that PRE-DATE the move**: `docs/decisions/**` matched no row at all, and
  `scripts/deploy_to_nexusmind.sh` tiered MEDIUM via `scripts/**`, so **sync-safety could
  never fire on the very script it is about** — carried unnoticed through the fork's life.
- **The depth cells mandated a `claim-verification` lens the same file says does not fire.**
- **"4 already-in-force" restated wrongly in three files, one always-loaded** — in the very
  edit that bumped the footer warning about restated numbers.
- `#149` marker lines quoted as 31/44/55/122; actually **31, 57, 122** (I transcribed line
  numbers from a grep for different terms).
- `.claude/review-profile.md` was untracked and not gitignored: a plain commit would have
  shipped the breakage with none of the fix.

⛔ **KNOWN LOSS, recorded not absorbed**: v1.40.0's Step 2 lens list is CLOSED. `reachability`,
`claim-verification` and `sync-safety` have no slot and **DO NOT FIRE**. Upstream
`ducroq/agent-ready-projects#166` (filed 2026-09-11) is exactly this gap. Prompts preserved
at the foot of the profile; must be invoked BY HAND. `reachability` is CLAUDE.md's #1 rule.

## `/audit-context`: VERDICT DEFECTS

⭐ **`tests/fixtures/reference-integrity/refcheck.py` had NO `sys.exit` anywhere.** It printed
findings and always exited 0 — `refcheck.py && ...` could never fail. Nothing wires it (no
CI), so nothing broke, but a guard structurally incapable of firing is the signature defect.
Added the three-outcome contract (1 defects / **2 coverage-incomplete, NON-ZERO** / 0 clean)
and 6 tests reading the block out of the shipped file.

⭐ **M4 survived**: `len(set(findings))` → `len(findings)` left all six green.
`test_findings_are_deduplicated` asserted the EXIT CODE, and five duplicates and one finding
both exit 1 — the test was named for a property it never touched. Rewritten to read the
printed count; M4 now dies. **A surviving mutation is a NAME that is lying.**

Checker liveness proven first: a seeded local fabrication AND a seeded cross-repo one both
caught, then removed.

**The two checkers are different instruments and neither is authoritative.** Local: 520
lines, 34 auto-discovered docs, ignores CLI args, stale-placeholder detection, 22 findings,
was exit 0. Framework: 1,151 lines, `--sibling-root`, collisions, **218 findings** (115
COLLISION on basenames with 12–34 copies; **39 of the 102 UNRESOLVED are rung-4 naming, not
dead files**). No `SPEC.md` added — the framework's describes a program 1,629 lines different
from ours. **ENGINEER'S CALL.**

Also fixed: CLAUDE.md claimed *"No hypothesis-log.md at either path … `curate` Step 0.6 is a
deliberate no-op here."* `memory/hypothesis-ledger.md` is 121 KB, is the index's designated
"START HERE to recall prior work", and was updated the same day.

## `/curate`

Read surface **2,408,600 chars over 129 files — 8.0× the 300k threshold, so the corpus was
NOT read**; metadata and runners only. Dead refs **0 dead / 6 unresolvable / 3 skipped / 70
resolved** (all 6 correct COLLISION on per-filter-version basenames). Verify runner **exit 0:
52 of 87 run — 52 pass, 0 fail, 0 error, 0 cannot-verify, 11 manual, 0 malformed**; of the
35 gap, 11 manual + **23 of 24 accounted as code-span-quoted, 1 unaccounted**. Index
self-consistency: **5 distinct clusters, 0 contradicting pairs**. Always-loaded layer
**53,621 B of 60,000**; `CLAUDE.md` **37,165 chars — over the 35,000 soft cap, 2,835 from
hard**. Gotcha log **454 → 458 headers**; no Promoted table here by recorded decision, so
**0 promoted patterns re-checked, 0 recurred**. Hypothesis ledger 31 rows, **0 past-due**,
3 with no retrievable verdict. **828 passed, 25 skipped.**

## ▶ NEXT

1. **Decide the checker question** — adopt the framework's `refcheck.py`, or keep ours and
   write its own `SPEC.md`. Do not ship the framework's SPEC beside our script.
2. **`memory/gotcha-log.md` is 665 KB / 458 entries = 27% of a 2.4 MB corpus, no rotation
   rule.** This is `#123` one layer down, as `docs/TODO.md` already diagnosed.
3. `CLAUDE.md` 2,835 chars from the hard cap; pointer budget at **4 of 5** carve-outs.
