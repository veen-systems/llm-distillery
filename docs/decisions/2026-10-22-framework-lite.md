# Framework-lite profile for llm-distillery (2026-10-22)

## Switch point (for agent-ready-projects EXP-004)

- **Date:** 2026-10-22
- **Last pre-switch commit:** `85309b3bff34958afe8678a906ca614c3eb27b28` (2026-10-22 08:18 +0200)
- **Switch commit:** the commit that adds this file (`git log --diff-filter=A --format=%H -- docs/decisions/2026-10-22-framework-lite.md`)
- **Framework stamp at switch:** agent-ready-projects v1.49.2, FROZEN from here

## The ruling (owner, in session)

The owner asked whether the framework is too heavy for this repo now that the harness keeps improving, and
accepted the assistant's suggestion ("I'll take your suggestion"), then "go" after it was negotiated with the
agent-ready-projects session. **What follows is the assistant's implementation; the owner ruled the direction,
not each line.**

## Why (measured 2026-10-22, git, window 2026-09-22 → 2026-10-22)

- 380 of 395 commits touched `memory/`, `docs/` or `CLAUDE.md`.
- ~46K Markdown lines added vs ~24K lines of Python and tests.
- Tracked Markdown 10.2 MB vs Python 4.1 MB.
- `memory/` feedback (`feedback-prose-promotion-does-not-fire`, user auto-memory): six promoted lessons
  recurred in one session; what prevents recurrence here is executable (scripts/verification/, .githooks,
  the PreToolUse hook, unit tests), not more prose.

## What changed

| Item | Before | After |
|---|---|---|
| `CLAUDE.md` | 19,397 B | 15,185 B: Hard Constraints' operative clauses, working rules, the parsed tables, one pointer row per kept topic file (11,994 B at `d8f4ad7`; ~30 dropped clauses restored after review, next commit) |
| User auto-memory `MEMORY.md` | 13,141 B, carrying findings | pointers only |
| Repo `memory/MEMORY.md` | index + 4-entry session log + rotation rules | the project index, pointers only |
| `memory/session-log.md` | rotated by `/curate` | FROZEN; the last four index entries moved in verbatim |
| Lesson promotion | prose into CLAUDE.md / memory | only as a check (test, hook, script); otherwise archived, not loaded |
| Framework stamp | tracked release by release | FROZEN at v1.49.2 (`framework-adoption-history.md`, 2026-10-22 entry) |
| `/review-changes` | default review | only for `.claude/review-profile.md`'s project lenses; built-in `/code-review` otherwise |

Nothing was deleted. Pre-switch copies: `memory/archive/CLAUDE-pre-lite-2026-10-22.md`,
`memory/archive/auto-memory-index-pre-lite-2026-10-22.md`; and git history.

## Negotiated with agent-ready-projects (session reply, 2026-10-22)

Its answers are taken from the v1.49.2 templates. Policy questions are pending its maintainer.

- **P1 amended:** keep the repo `memory/MEMORY.md` as the index (framework ADR-001: auto-memory is invisible in
  the editor, orphans when the path changes, does not travel with a clone); auto-memory holds pointers only.
- **P2:** checks-only promotion is fine as a local rule. Whether it becomes the upstream default is pending.
- **P3 accepted:** `/curate` does not read session files.
- **P4:** keep the stamp, each constraint's operative clause, anything a verify probe reads, one Before-You-Start
  row per kept topic file (`/audit-context` flags orphans).
- **P5 accepted:** a behind stamp with a recorded reason counts as reconciled; `update-drift` still lists the gap.
- **P6 accepted:** review-changes only needs `.claude/review-profile.md` to exist.
- **Unmeasured by both sides:** what breaks when newer global skills run against this frozen repo's older local
  surfaces.

Always-loaded layer at the close: 32,538 → 19,670 B (`check_index_budget.py --target loaded`).

## How to tell whether it worked

Trial ~1 week (to ~2026-10-29). Signal: do failures caught by the checks, or found by review, go up? If not,
the prose was not doing the work. Revert = restore the two archived files and un-freeze the stamp.
