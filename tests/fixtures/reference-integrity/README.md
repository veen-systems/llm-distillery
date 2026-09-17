# Reference integrity — the instrument for `/audit-context` step 4

`refcheck.py` resolves every file reference in `CLAUDE.md`, `memory/MEMORY.md`,
`memory/gotcha-log.md` and the `memory/*.md` topic files, and splits the result
into **findings**, **resolved below rung 1**, **generic artifact names** and
**skipped as asserted-absent**.

    python3 tests/fixtures/reference-integrity/refcheck.py     # the audit
    ./tests/fixtures/reference-integrity/run.sh                # the sensitivity test

## Arguments — four flags, nothing else

⛔ **This fork takes NO positional arguments and no `--sibling-root`.** Upstream's
checker in `~/repos/agent-ready-projects` takes both; a command copied from the
`/audit-context` skill is aimed at a **different program**. Since 2026-09-17 any
unrecognised argument stops the run with a message — before that it scanned exactly
what an unflagged run scans and printed a small, reassuring findings count.

| flag | adds to the scan set |
|---|---|
| *(none)* | `CLAUDE.md`, `memory/MEMORY.md`, `memory/gotcha-log.md`, `memory/*.md` topic files, the user auto-memory index |
| `--sessions` | `memory/project_session_*.md` — frozen accounts of a moment |
| `--docs-live` | the LIVE tier of `docs/` — **the preview of what promotion would put in the default set** (llm-distillery#134 step 2) |
| `--docs-frozen` | the FROZEN tier of `docs/` |
| `--docs` | **all** of `docs/`, i.e. both tiers. Every recorded `--docs` number was measured this way, so it must keep meaning that |

The tier is not a directory list: see `_tier_of_doc` and
`docs/decisions/2026-09-17-refcheck-docs-tier.md`. A `docs/` subdirectory that has
not been tiered stops the run rather than defaulting into a tier.

## Why this is committed

The skill describes an instrument; this project did not have one, so each
monthly audit re-implemented the check and got a different answer. **The first
implementation on 2026-08-09 produced 134 findings of which essentially zero
were real** — the cry-wolf failure the framework exists to catch. Without a
committed instrument the next audit would have repeated it.

## Rungs, in order

1. **as written**, relative to repo root
2. **whole-fragment suffix** in the **working tree** (not `git ls-files` — that
   omits gitignored-but-present files). Two matches is a collision, reported.
3. **runtime state** — a state directory or state-file shape. Data only: a
   *source* file merely named `*_state.py` is still source.
4. **sibling repo**, only when the reference is *marked* cross-repo — either a
   whole-token repo name in the surrounding prose (with the backticked paths
   stripped first, so a reference cannot mark itself) or a **first component
   that is a sibling repo name and not a generic directory** (`docs`, `src`,
   `scripts`, `tests`, `config`, `memory`, `filters`, `data`, `lib`).
5. **assistant auto-memory** — `~/.claude/projects/<slug>/memory/`, a real named
   location outside the repo that `CLAUDE.md` deliberately points at.

## Two local rules that are not in the skill

Both were added on 2026-08-09 because without them the check cried wolf, and
both are covered by the sensitivity fixture so they cannot silently widen:

- **A bare basename matching ≥2 files in-tree is a CLASS of artifact, not a
  locator.** This repo has 33 `config.yaml`, 29 `prefilter.py`, 26 `__init__.py`
  — one per filter version. Prose saying "the filter's `config.yaml`" is not a
  broken reference. **A bare basename matching 0 files is still reported.**
- **A path whose first component is a sibling repo name is qualified**, not a
  self-marking coincidence. `NexusMind/config/app.yaml` names its repo. The
  skill's self-marking hazard is a *generic* first component, so those are
  excluded by the list above and case 3 in the fixture proves it.

## Expect a residue; zero is not the target

A short unresolved list is the healthy result: systemd units that are host state
(`nexusmind.service`), one-off scratch scripts named in a gotcha as things that
were once run, and cross-repo files that have since moved. **A change that
drives the count to zero has disabled the check, not fixed it.**

`run.sh` seeds the failure each loosening newly permits and asserts each
disposition positively. Run it before and after any edit to `refcheck.py`.

⚠️ **It does not reach the docs tier as written** — but not for the reason it looks
like. `SEED` bypasses `_docs_files()`, so no tier is *selected*; the report block,
however, keys off the seed's own path, so a seed placed under `docs/` DOES reach
`_tier_of_doc` and prints a tier line (`SEED=docs/TODO.md ...` was measured doing
exactly that, and would abort on an untiered directory). What keeps the harness clear
of it is simply that its seed lives in `tests/fixtures/`. The tier's guard tests are
`tests/unit/test_refcheck_docs_tier.py`, which runs the checker against fixture trees.
What `run.sh` *does* cover of that change is the argument guard, which runs on `argv`
at module level, above the `SEED` short-circuit.
