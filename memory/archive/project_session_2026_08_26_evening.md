# 2026-08-26 evening — /audit-context + /update-drift: a guarantee on the wrong side of a truncation

*No spend, no model, no filter, no deploy.* All work in `llm-distillery` plus one issue
filed upstream. Three repo files changed, one user-level file trimmed.

## What was asked

`/audit-context`, then act on the top two findings, then `/update-drift`, then file the
bug upstream, fix it here, curate, review, commit.

## ⛔⛔ THE KEEPER — a protection notice that could not report its own violation

The Claude Code auto-memory `MEMORY.md` opened with:

> *Two entries below are marked ⛔ NO REPO FILE and must not be trimmed: they are the
> only surviving record.*

The file was **26,645 bytes against a 24.4KB load limit**. The two protected entries sat
at byte offsets **24,905** and **25,445** — past the cut. The notice was at offset 164
and loaded every session.

**The guarantee loaded; the thing it guaranteed did not.** Nothing could have reported
it from inside: read the file as it actually arrives and you see a well-guarded index.

**And the marker was also stale.** Checked all seven of its claims individually rather
than trusting it:

| Claim | Already in the repo at |
|---|---|
| truncation ≤0.01 REFUTED (NM#285) | `prefilter-length-floor-hypotheses.md:19` |
| LD#92 refuted at n=60, op-point 4.0 not 2.25 | `calibration-history.md:44` (fuller) |
| cd ~40% of oracle input | `prefilter-length-floor-hypotheses.md:475` |
| #95 max \|Δ\| 0.162, 7–9% flips | `score-batch-shape-noise.md:3,28,42` |
| arxiv/mastodon_/bluesky port | `prefilter-length-floor-hypotheses.md:482` |
| `nm286-adr022-gaps` "unpushed" | landed as NexusMind `23a9068` |
| HELD gpu-server deploy | transient, 3 weeks moot |

Nothing was at risk. **10th occurrence of *establish what a source excludes*** — and a
new shape: the source excluded **its own tail**, and the excluded part was what the
loaded part promised.

**Fix**: trimmed 26,645 → **18,977 bytes** at the trim, **19,217** after this session's
own additions to it (5,183 headroom under 24,400 — re-derive, do not quote: `wc -c`). All 38 non-session entries
byte-identical; 11 session entries removed, 6 kept; the repo's `session-log.md` covers
2026-08-06 → 08-25 in more detail, verified before cutting. Backup in the session
scratchpad.

## `CLAUDE.md` had 45 bytes of headroom and no guard

`scripts/verification/check_index_budget.py` watched `memory/MEMORY.md` — a *different
file with the same name*. The file at the wall had nothing.

⛔ **I first reported "449 under the limit". The limit is in BYTES: 45.**
`40,000 − 39,551 chars = 449`; `40,000 − 39,955 bytes = 45`. Both correct, one relevant.
Adopter-side instance of agent-ready-projects **#48**.

**Fix**: `--target project` (hard 40,000 / soft 35,000, the skill's numbers). Registered
as a second `<!-- verify: -->` in `memory/MEMORY.md` — **not** in `CLAUDE.md`, because
the script's own docstring warns a guard inside its own subject spends the budget it
polices, and 45 bytes would not have survived the annotation.

⭐ **Table padding measured before proposing any cut** (curate 0.8 says to): only **244
bytes, 0.6%**. The skill's worked examples are 35–61%; this file's table cells are long
prose, so there is no alignment padding to reclaim. **The 45 bytes is a genuine content
problem** — surfaced, not acted on.

## ⛔ Two defects of mine in that guard, both caught by the existing test file

`tests/unit/test_index_budget_guard.py` went 5 red. **The tests were the control
working** — fixed the code, not the tests.

1. **`main()` read `sys.argv` directly**, so any importing caller got the *host*
   process's arguments; under pytest it answered "unknown argument" to five tests that
   never passed one. Now `main(argv=None)` where `None` means *no arguments*, and only
   `__main__` speaks for the command line.
2. **`TARGETS` froze the paths at import time**, making the tests' `monkeypatch` of
   `INDEX` a silent no-op — the guard measured the *real* repo index while the test
   believed it had redirected it. Now resolves the attribute *name* via `getattr` at
   call time.

Both carry a comment saying what they cost. **8 new tests; 6 of 6 real mutations
killed** (a 7th survived and was an *equivalent* mutant — reading a module global at
call time is what `getattr` does; the actual pre-fix defect kills 7 tests). 349 pass.

**Outcome proven, not assumed**: seeded break → `FAIL`, exit **1**, runner row
`failed=1`; restored, `CLAUDE.md` byte-identical to HEAD.

## /update-drift — pinned v1.26.0, upstream v1.28.0

Step 0 reconciliation: **9 mentioned `(file, framework)` pairs, 4 stamped, 5 in the
difference** — all dispositioned. One is a **second framework**: `agent-ready-papers`,
cloned locally, **already declined** at `docs/TODO.md:4052` (*"not adopted here by
design"*). One is a matcher false positive (`agent-ready-fixture`, inside a test
fixture).

**Triage: 3 adopt, 0 decline, 4 not-applicable, 5 already-in-force.** All three
user-global skills (`audit-context`, `update-drift`, `curate`) are **byte-identical** to
the framework's shipped `.claude/skills/` copies — the 23-line diff is the installer
converting the SAVE-AS comment into real frontmatter.

## The `$0` fix, and why it is not a re-copy

Upstream #77 (v1.27.0): skill **arguments are substituted into the skill body**, so a
bare `$0` in an embedded awk program arrives as the first argument word.

⛔ **My locating grep was not my enumerating grep.** `isdelim(` returned **line 146**. A
scan for bare `$0`–`$9` returned **six lines carrying ten occurrences**. A patch script
that detected the block by its closing `}` stopped at a **nested** one and replaced 1 of
10, reporting success; the next attempt asserted `n==9` from an eyeball count and
**aborted before writing** — the real count was 10.

⚠️ **`review-changes` here is RE-MAPPED, not copied** (`CLAUDE.md:19` — the template's
risk tiers key on paths this repo lacks, so a verbatim install tiers everything LOW and
does nothing). 453 lines local vs 358 upstream, 577 diff lines. So: **surgical patch,
never re-copy.**

Verified by execution, both directions:

| | without args | with args |
|---|---|---|
| old form (`$0`) | finds the lossy row | **SILENT — examined nothing** |
| new form (`$(0)`) | finds the lossy row | finds the lossy row |

## Filed upstream: agent-ready-projects#94

Not a re-report of #77 (correctly fixed). **A fix to a PROJECT-LOCAL skill cannot reach
a re-mapped adopter, and the prescribed remedy ("re-copy by hand") destroys the
re-map.** The CRLF fix (#52/#58) reached this repo; the `$0` fix did not — same file,
and the only difference is that one adoption happened to be done by hand while someone
was reading the changelog. For USER-GLOBAL skills this is solved
(`install-global-skills.sh --check` compares content); for project-local there is no
equivalent. Suggested a marker-string manifest per project-local skill.

## Still open

- **The 15 unmarked cross-repo references** in memory files (real files in NexusMind /
  ovr.news; the prose just does not name the repo, so rung 4 cannot fire).
- **`memory/uplifting-oracle-genre-hypotheses.md` is orphaned** — 29,808 chars, the
  largest topic file, reachable from neither `CLAUDE.md` nor the index.
- **Two possibly-real breaks**: `NexusMind/scripts/research/nm188_mojibake_derived.py`
  and `precision_panel_v3/answer_key.json`, cited in
  `corroboration-feature-hypotheses.md`, absent from every repo.
- **`CLAUDE.md:293` calls v1.26.1 "(candidate, unreleased)"** — it has since shipped.
- **`CLAUDE.md` stamp stays v1.26.0** until adopt items land. A stamp ahead of its
  content silences the check that would catch the gap.
