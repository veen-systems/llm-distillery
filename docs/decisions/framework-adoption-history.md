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

## v1.24.0 + v1.25.0 (both released 2026-08-12) — triaged and adopted 2026-08-12 via `/update-drift`

**3 adopted, 0 declined, 1 not applicable, 3 already in force.**

Clone checked at `889b038`, in sync with its origin. Two releases behind, both
shipped the same day we adopted v1.23.0 — upstream velocity, not neglect.

| From | What | Outcome |
|---|---|---|
| v1.24.0 | `curate` Step 0 reads metadata, not documents | **Already in force** — global `curate` verified byte-identical to the framework's tracked copy by `diff`, not by reading its description |
| v1.24.0 | `[RESOLVED]` + recurrence count belong in an entry's **heading** | **Adopted** → `memory/gotcha-log.md`. Measured before acting: 5 resolution markers were already in headings but in **3 incompatible formats**, and recurrence was **7 in bodies, 0 in headings**. Normalised all five to a `[RESOLVED…` prefix findable by one grep, tagged 5 headings (`[5x verify-the-call-path]`, `[4x verify-the-call-path]`, `[3x restated-set drift]`, two `[2x]`), and documented the forms in the file's template comment |
| v1.24.0 | lint rule 8 — ratchet adopter-facing template sizes | **Not applicable** — no `templates/` dir; we ship no templates upstream |
| v1.25.0 | adversarial lens: one rule — a claim needing a measurement gets one, gets hedged, or is not ready | **Adopted** → `.claude/skills/review-changes/SKILL.md`. We already had the negatives half (v1.22.0); the **absolutes-in-descriptions** half is new. Grounded in the same day's own failure rather than upstream's example — see below |
| v1.25.0 | `hypothesis-log` gains a trigger in the working path | **Adopted, adapted** — we have no `templates/hypothesis-log.md`; we have per-topic `memory/*-hypotheses.md`. Landed as a lens clause: report an unmeasurable claim as a finding **at the moment it is made**, register during `/curate`, home is the topic file. This was the exact gap hit hours earlier — a hypothesis noticed while writing results up, not when the claim was made |
| v1.25.0 | shape rule: never end a bolded phrase with a `**`-suffixed glob | **Already in force — nothing to fix.** 0 hits across 451 markdown files. **Verified by execution with a seeded control**: my first two sweep patterns were wrong (one covered only the single-glob shape; the second had the backticks in the wrong order and matched **0 of 2** known positives). Only the third — 2/2 positives, 0/2 safe lines — makes "0 hits" mean anything |
| v1.25.0 | gotcha-log "2–3 lines" rule **withdrawn** | **No action, and it vindicates this log.** llm-distillery IS the cited evidence upstream: 203 entries, median ~1,200 chars, 35% >1,500. Recorded the withdrawal and the real signal (>3,000 chars) in the file's template comment |

### Why the absolutes rule was adopted on our own evidence, not upstream's

Upstream's gate for shipping it was that it catch something in a repo other than
its own. It did — and independently, on the same day, this repo produced a
textbook instance without knowing the rule existed. A measured claim
("NexusMind's `pre_enrich` attempted 35,229 Google News rows and replaced zero")
was written up with an unmeasured absolute attached: *"a property of the URL
scheme, so no fetcher change moves it."* The measurement was scoped to one
fetcher; the absolute was stated of the scheme. It propagated into
`ovr.news#312` as a premise about a **different** resolver — one that
demonstrably works, 74 of 103 — and licensed a "do not fix the GN resolver"
recommendation that would have retired a capability carrying 22 of 38 published
articles. Refuted by a peer re-measuring against their own source.

That is the rule's whole thesis: the number was right, the absolute rode along
unmeasured, and nothing in the previous lens asked for it. Hence the extra clause
we added beyond upstream's text — **name the population, not just the number.**

### Finding sent upstream

v1.24.0's Step 0.3 reconciles its heading count against
`grep -c '^\*\*Problem\*\*'` as ground truth. On this log that reads **203**
against **206** both-level headings. Three orphans: one real section
(`## The unreachable-mechanism catalogue`) and **two real entries that do not use
the `**Problem**` shape**. So the reconcile under-counts this log by 2 and will
report a mismatch every run — the same class as the level-blind grep v1.24.0
itself shipped to fix.

## v1.22.0 + v1.23.0 (both released 2026-08-11) — triaged 2026-08-12 via `/update-drift`

**2 adopted, 0 declined, 1 not applicable, 2 already in force, 1 deferred.**

| From | What | Outcome |
|------|------|---------|
| v1.22.0 | `curate` Step-0 verify runner | **Already in force** — global skill byte-identical to the v1.23.0 tag. But its *adopter action* was real work here, below |
| v1.22.0 | `review-changes` adversarial lens: state the check before the claim, on any negative | **Adopted** → `.claude/skills/review-changes/SKILL.md`, adapted to this repo's terser lens style and grounded in its own three catalogued instances |
| v1.22.0 | `templates/project-file.md` "Active work" section | **Not applicable** — by the template's own instruction: delete it where the tool has auto-memory (Claude Code) |
| v1.23.0 | `audit-context` Step 4 placeholder skip | **Already in force** — global skill current |
| v1.23.0 | Adopter action: mark placeholders with `<!-- placeholder -->` | **Deferred** to the next `audit-context` run. 0 paths marked here today, and a marker is only meaningful against a live findings list — marking speculatively is how a real break gets labelled intentional |

### The v1.22.0 adopter action was the substance, and it was not a no-op

The framework's own changelog measured **this repo** as
`26 ran: 12 pass, 9 fail, 5 error, 3 malformed`. Re-measured 2026-08-12 after
commit `6a96271`'s repairs plus today's:

```
ran 25 of 38 annotations — 25 pass, 0 fail, 0 error, 0 cannot-verify; 6 manual, 0 malformed
exit 0
```

**All 38 accounted for**, as the runner's reconciliation rule demands: 25 ran,
6 manual, 7 prose mentions inside code spans (6 in `memory/gotcha-log.md`, 1 in
`memory/project_session_2026_07_26.md`) — those are documentation of the syntax
and are correctly not extracted.

Three defects were real and are fixed:

- **Two multi-line annotations in `memory/stamp-contract-integrity.md`** — one of
  them twelve lines of embedded Python. An HTML comment whose `-->` sits eleven
  lines below its opener is MALFORMED and **had never run**. Replaced by
  `scripts/verification/check_content_length_populated.sh`, which follows the
  v1.22.0 writing rules (evidence not a verdict word, non-zero exit, explicit
  `CANNOT VERIFY` when the box is unreachable). First run: all six filters
  2,802/2,802 — NexusMind#300 still fixed.
- **One multi-line annotation** in `memory/corroboration-feature-hypotheses.md`,
  collapsed to one line.
- **One ERROR that was not a defect**: the LD#92 DiD check is a source-clustered
  bootstrap taking ~50s against the runner's 30s default. Verified correct
  (exit 0, `D3_pct2.3 80 80 -1.119 [-1.61, -0.61]`) and annotated in place with
  its `VERIFY_TIMEOUT=120` requirement, so a future default run does not read a
  timeout as a broken claim.

### Also folded in: v1.21.0

Triaged 2026-08-11, nothing adopter-facing — the `install-global-skills.sh`
release guard (maintainer tool), `templates/release.md` Step 1 (we publish no
package), `templates/coordination.md` (we have none), one `docs/GUIDE.md`
sentence, and two stamp bumps. Recorded here so the frontmatter can carry only
the current reconciliation.

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
