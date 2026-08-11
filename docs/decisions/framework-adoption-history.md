# Framework adoption history — agent-ready-projects

Per-release reconciliation record. Moved out of `CLAUDE.md`'s
`framework_reconciliation` frontmatter on 2026-08-11, where it had grown to
4,931 chars (12.5% of a file 358 chars under Claude Code's 40k warn threshold).

**The frontmatter keeps only what is still operative** — the current stamp, the
standing skill-scope rules, and open decisions. Everything below is the
historical record: correct when written, and kept for provenance rather than for
reading every session.

Current stamp lives in `CLAUDE.md` frontmatter (`framework: agent-ready-projects vX.Y.Z`).
Upstream changelog: https://github.com/ducroq/agent-ready-projects/blob/master/CHANGELOG.md

---

## v1.19.0 + v1.20.0 (both released 2026-08-10) — triaged 2026-08-11 via `/update-drift`

**4 adopted, 1 declined, 3 not applicable, 6 already in force.**

**ADOPTED.** `review-changes` gained v1.19.0's Step 1.5 structural pre-check, the
`Unclassified` naming rule + never-omit report slot, and the guarantee-lens
invariant — every file the guarantee lens names must tier HIGH.
`tests/unit/test_normalization_invariant.py` was MEDIUM under `tests/**`, so a
change weakening the very pin that caught NM#161/#205 would have skipped the lens
that exists to catch it; it is now listed in HIGH.

`test-verify-memory` gained the `CANNOT VERIFY` disposition, its ordering rule,
and an 11th fixture. Load-bearing here because **7 of ~39 verify commands in
`memory/*.md` are host-dependent** and b650-gpu is routinely powered off, so they
read FAIL on every run.

Step 1.5 was **verified by execution** over 382 tracked `.md` files: 2 violations,
0 false positives, both genuine data loss — a `|r|` header in
`filters/cultural_discovery/v5/calibration_report.md`, and a 4-cell row in
`memory/cross-repo-prioritization.md` whose dropped cell was a staleness caveat
that rendered nowhere. Both fixed in the same pass.

**DECLINED** — v1.20.0's gotcha-log Promoted table + `Occurrences` column. This
repo has no Promoted table: promotion targets `CLAUDE.md` § *Working rules*, and
the rate is already carried in prose ("8th occurrence 2026-08-11, four
self-inflicted") plus the per-shape catalogue table in `memory/gotcha-log.md`. A
fourth-column table would be a second counter over the same events — exactly what
the framework itself declined for its own #38 Step 1 tally.

**NOT APPLICABLE** — `physics-tests/` disclosure (no such surface); `.gitignore`
`/memory/` anchoring (`memory/` is tracked here, no ignore pattern);
`tests/lint/skill-sync.sh` (maintainer infra).

**ALREADY IN FORCE** — the v1.20.0 session-start row; the memory-index "not
auto-loaded" correction (this index never claimed it); `audit-context` Step 1,
`curate` Step 2, and both `install-global-skills.sh` fixes — all verified
byte-identical to the **v1.20.0 tag**, not merely to the clone's HEAD, which sat
4 commits ahead on an unreleased #33 installer guard that was deliberately not
triaged.

## v1.18.0 (2026-08-09) — already in force

Stamp bumped to match reality. Its only change is the `update-drift` skill, which
is user-global and was already installed. Nothing in the repo needed to change —
the stamp was understating what was installed. v1.16.x and v1.17.0 reviewed in the
same pass, no adopter action outstanding.

## v1.16.1 / v1.16.2 / v1.17.0 — adopted 2026-08-08, verified by content

Both global skills byte-identical to the upstream tracked copies (`diff`, plus
`install-global-skills.sh --check` clean).

- **v1.16.1** — the `review-changes` adversarial-lens contradiction does **not**
  affect this repo's copy, which is re-mapped and already carries only the
  consistent half plus a concrete-failure requirement; nothing to port. Its
  `curate` Step 0.6 dual-path fix is a **no-op here** — this repo keeps no
  `hypothesis-log.md` at either path; hypotheses live in per-topic memory files.
- **v1.16.2** — example rename only, no action.
- **v1.17.0** — the gotcha-entry length rule. The entry template it added is now
  in `memory/gotcha-log.md`, adapted to that file's `##` heading level and marked
  NEW-ENTRIES-ONLY (the log is ~2,000 lines and predates the rule).

Declined: nothing.

## v1.15.1 (2026-08-06) — adopted 2026-08-07

A patch to the `audit-context` skill only; no template or memory-layout change.
The global skill already carried the new Step 4 rules (three-section output,
extension whitelist, rung ordering), so only the stamp was behind.

## v1.15.0 (2026-08-06) — adopted

Established the skill-scope split that still governs (see `CLAUDE.md`
frontmatter). Declined: nothing.

---

## Standing caveat on the stamp

**The stamp records which surfaces were reconciled — not that any behaviour
changed, and not that a skill has since been run.**
