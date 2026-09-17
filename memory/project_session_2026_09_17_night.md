# Session 2026-09-17 (night) — framework adopt queue closed; a probe built to kill a decaying claim, with no caller

**Cost**: $0 — no oracle calls, no GPU, no training, nothing in `filters/`.
**Deploy**: N/A — **inapplicable, not skipped**. No filter package, model, calibration,
normalization, threshold or scoring-path probe changed.
**Merge**: N/A — worked on `main`, no branch.
**Suite**: `.venv/bin/python -m pytest tests/ -q` → **848 passed, 25 skipped** (822 on
2026-09-11; +26 = 21 new guard tests + the 2026-09-17 audit's 5).

## What this session did

Closed `docs/TODO.md` START HERE item 1, the framework adopt queue, **v1.40.0 → v1.45.1**.
Four work items across three adopt releases, landed in the order the stamp rule requires,
stamp bumped **last**:

1. **`agent-ready-projects#166`** — the three project lenses in `.claude/review-profile.md`
   were annotated `⛔ NOT READ BY THE SKILL`. True when written 2026-09-11; false from
   v1.43.0, which added the section to the profile contract. Heading is now exactly
   `## Project lenses`; the `/review-changes` pointer row in `CLAUDE.md` no longer says they
   are dead.
2. **`agent-ready-projects#136`** — the stamp probe, shipped as
   `scripts/verification/check_framework_stamp.sh` + `tests/unit/test_framework_stamp_guard.py`
   (21 tests). **Four** skills, not upstream's three: its `want` list omits `review-changes`,
   which v1.40.0 moved into the global set.
3. **`## Mechanized`** appended to `memory/gotcha-log.md` — the `/review-changes` Step 3.1
   destination, which until now did not exist here, so every triage it ran was lost.
4. **Stale `curate` sub-step citations** — the triage named three; there were **four**.

## ⛔⛔ THE KEEPER — I replaced a decaying sentence with a command nothing ran

`CLAUDE.md`'s footer asserted the four globals were byte-identical to v1.40.0 "when enumerated
2026-09-11". Six days later that was false and nothing said so. I deleted the sentence and
pointed at the new probe — and the `reachability` lens found the probe had **no caller**: no
hook (`.githooks/` holds only `commit-msg`), no CI (no `.github/`), no skill. The hermetic unit
test cannot see `~/.claude/skills` by design. So the claim still depended on a human
remembering: **the exact dependency the change was made to remove**, in this repo's signature
shape, inside the mechanism built to remove it.

Fixed with a `<!-- verify: -->` block in `memory/MEMORY.md`, run by
`run_verify_annotations.py`. Proven both ways: `pass … 4 global skills byte-identical to
v1.45.1`, and a seeded `FRAMEWORK=/nope` arm made the runner print `CANNOT VERIFY` and exit 1.

⚠️ **`/curate`'s own `stampcheck()` is NOT this probe** — three skills, skipping
`review-changes`. And `check_doc_claims.py:191` defines a third function literally named
`check_framework_stamp()`, which only asks whether two lines of `CLAUDE.md` agree with each
other. Three similar names, three different populations.

## Review: 6 lenses, 24 findings; then a narrow round 2, 5 more

HIGH tier (a new `scripts/**/*.sh`), 377 changed lines → full battery. Four shipped lenses plus
the profile's `reachability` and `claim-verification`; `sync-safety` did not fire (no
`filters/common/` or deployed filter). Structural pre-check: 8 files, 0 problems.

✅ **This run is the outcome proof for `agent-ready-projects#166`** — the two re-enabled project
lenses each returned a finding no shipped lens did. A heading could never have proved that.

**Six false-PASS paths in the probe itself**, every one reproduced by execution: `diff`'s exit
status unchecked, so an unreadable file read as *identical*, exit 0, with `Permission denied`
on stderr beside the success line; `N_WANT=4` hand-written beside a four-name `WANT`; `head -1`
on the version, so a provenance line naming an older release outranked the stamp; `$HOME` unset
aborting with exit **1**, an environment fault reported as DRIFT; `git show TAG:path` failing
for a missing FILE but blaming the TAG; trailing-newline normalization, so "byte-identical" was
not what was measured.

### ⭐ Round 2's keeper: a test of mine passed for the wrong reason

`test_count_is_derived_not_restated` asserted `"N_WANT=$(printf" in src` — a **spelling check** —
and exercised only the happy path, where a literal and a derivation agree by construction. A
mutant deriving the count from an unrelated literal list left all 17 tests green. **A name that
was lying, inside the test written to stop a hand-kept count.**

Round 2 also found the condemned `diff | grep -c` reintroduced **six lines below the comment
condemning it**. Two recurrences of one class → **a CENSUS, not a third round**, which is the
round-cap rule's own remedy: all 21 substitution/pipe sites enumerated at once, every one now
status-checked, value-only or decoration; the last live instance (two `grep`s whose `2>/dev/null`
hides a failure) closed with an invariant. **13 mutations, 13 killed.**

### ⚠️ Nine prose defects about the probe — the code was well-proven, the writing was not

A `## Mechanized` row whose date (2026-09-17 → really **2026-08-27**), test count (4 → **11**)
and citation were all wrong because I copied them from a TODO summary instead of measuring;
"each killed by exactly one test" flattened into three files when one mutation kills two; a
branch list naming a branch that had **no test**; `7,400` against a measured `7,479`; a
`~19 B/day` rate restated with no window, whose sign reverses on a different endpoint pick; a
test baseline left at 822 by the change that made it 848; a re-diff command hardcoding
`v1.45.1` in the same file whose script header forbids hardcoding a tag, in bold.
⭐ **Every one is the shape the table I had just added exists to catch.**

## Also this session

- **Cross-repo issue numbers qualified.** `llm-distillery#136` **exists** and is the commit-msg
  deploy guard — a different issue from `agent-ready-projects#136`. Bare `#136` in this repo's
  docs resolved to the wrong one, alongside `docs/TODO.md:1752` and `memory/gotcha-log.md:5720`
  which already used it for the local issue.
- **#122 caught my own edit.** The `Occurrences` scoping note went into `CLAUDE.md`'s
  `framework_reconciliation` frontmatter — the block #122 says does not reach session context,
  confirmed directly: the `CLAUDE.md` delivered into this session began at `# CLAUDE.md -
  LLM Distillery`. The operative half is safe only because it also lives in the `## Mechanized`
  preamble. Commented on #122 with the evidence.
- **H-MECH-1 opened** — does the new `Occurrences` column get maintained, or is it a second dead
  column? This repo already declined v1.20.0's for exactly that reason. Three-battery falsifier.
- **`CLAUDE.md` grew +647 B**, the wrong direction for the file the previous day's audit
  flagged. Stated once, with its command, in `docs/decisions/framework-adoption-history.md`.

## Issues updated

- **`llm-distillery#122`** — commented: the frontmatter block did not reach session context
  again, observed directly, and it cost a correction this session.
- **`agent-ready-projects#136`** — adopter report: its `want` list is three skills where four
  are installed; `N_WANT=3` beside a three-name list is the same hand-kept duplicate the block
  warns about, reproduced; plus the worktree and missing-file-at-tag cases.
- **`agent-ready-projects#166`** — adoption confirmed, **with a correction to my own first
  justification**: nothing greps the heading, so the contract is social, not lexical, and the
  outcome proof is a report that NAMES the lenses.
- **`augmented-engineering#46`** — filed, per `CLAUDE.md` § Cross-Repo Evidence: the no-caller
  finding (verification findings) and the spelling-check test (LLM behavioural properties).

## Next session

`docs/TODO.md` ▶ START HERE, top down. Item 1 is **LD#134 step 2** (tier `docs/`; 376 findings,
43% frozen). ⚠️ Do not re-do LD#134 step 1 — `docs/evidence/2026-08-28-refcheck-docs/`.
