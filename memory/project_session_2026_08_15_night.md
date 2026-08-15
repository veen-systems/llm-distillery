# Session 2026-08-15 (night) — framework drift adopted, then a structural audit

**Scope: housekeeping only.** No filter package touched, no model trained, no deploy, no
oracle spend, nothing sent to any peer repo. Two skills run end to end: `/update-drift`
then `/audit-context`, and the fixes both produced.

---

## 1. `/update-drift` — v1.25.1 + v1.26.0

**3 adopt, 1 decline, 4 not-applicable, 2 already-in-force.** Per-release detail and the
evidence: `docs/decisions/framework-adoption-history.md`.

### The gap existed because a stamp ran ahead of its content

`CLAUDE.md` carried **two** framework stamps that disagreed — frontmatter `v1.25.0`,
footer `v1.26.0` — and the footer had read v1.26.0 since 2026-08-13 while the adoption
history's last entry was v1.25.0. **Neither v1.25.1 nor v1.26.0 had ever been triaged.**

The stamp is the drift check's only input, so a premature bump does not merely mislead a
reader: it makes every later run report "current" and examine nothing. Filed as the
**13th occurrence** of the unreachable-mechanism rule and added to the Promoted table.
**A stale stamp is safe; a premature one is the only value in this repo that can turn its
own checker off.**

Both stamps now agree at v1.26.0, and a **stamp-agreement probe** sits in `CLAUDE.md`,
seeded against this real disagreement before being believed.

### Adopted

- **v1.25.1's Step 1.5 CRLF strip** into the project-local `review-changes`. Reproduced
  against *our* re-mapped awk first rather than taken on the changelog's word: a seeded
  lossy row in a CRLF file printed **nothing** — byte-identical to a clean run — and the
  one-line `{ sub(/\r$/, "") }` restored it, with the LF result unchanged both sides.
  Live exposure today is nil (`core.autocrlf` unset, 0 tracked `.md` carry CR), but
  `docs/RUNBOOK.md` and `CLAUDE.md`'s `MSYS_NO_PATHCONV=1` document driving this repo
  from Git Bash, where `core.autocrlf=true` is the installer default.
- **v1.25.1's withdrawal of the "every reported hit is a real loss" absolute.** It lived
  here in our own wording — *"A hit is data loss, not a style nit"* — so a phrase-grep for
  upstream's text would have missed it. Refuted locally in **3 of the 4** classes upstream
  names (empty excess cells; frontmatter closing after a piped `description:`; a spaced
  `- - -` break). The setext class **did not reproduce** and is recorded as such.
- **v1.26.0's project-file probe.** It caught a live drift on contact: the file read
  *"10th occurrence"* while `memory/working-rules.md` read **12th**.

### Declined

**Tightening `isdelim()`'s guard** to require a pipe in the delimiter row. Upstream
deliberately left it loose and says so — the cost to pipe-less delimiter rows is
unestablished on both sides, GFM ships no example of one, and framework #52 is open for
the decision. Taking it here would fork our copy on an undecided question.

### Also found, independent of the gap

`.claude/skills/review-changes/SKILL.md` cited **"v1.26.1"**, which upstream has never
released; the fix it describes sits on the unmerged branch `fix/review-changes-scope` at
`e824212`. A citation to a version that does not exist cannot be checked against
anything. Restated as a commit reference.

A third stamp was found and deliberately **not** touched:
`tests/fixtures/reference-integrity/SEED.md:2` reads `v1.23.0` as **fixture data**, frozen
to test frontmatter marker scope.

---

## 2. `/audit-context` — and the instrument was again the thing that broke

| | before | after |
|---|---|---|
| reference findings | 16 | **0** |
| `memory/MEMORY.md` | 54,808 chars | **24,743** (−54.9%) |
| duplicated constants (`CLAUDE.md` ∩ index) | 13 | **7** |
| refcheck harness | 20/20 | **24/24** |

### The finding the audit almost dismissed as residue

`refcheck.py`'s rung 4 has stripped a leading component repeating a **sibling** repo's
name since it was written. Nothing stripped the **local** repo's name — so
`llm-distillery/scripts/remote_deploy.sh` was reported unresolved while
`scripts/remote_deploy.sh` sat in the tree, and a whole class of self-reference was
**never examined**. "Not reported" meant "never checked".

Fixed as `selfstrip()`, ordered before rungs 3–4 so a path this repo owns is explained
here rather than by a neighbour with the same filename. Because the strip is a
**loosening**, the seeds are the failures it newly permits (a fabricated path behind the
prefix, an ambiguous one), not the case it was built for.

### Two bounded class rules, each with its laundering case seeded

- **systemd units** (`.service`/`.timer`/`.socket`) resolve only if the unit file exists
  *somewhere in the estate*. A fabricated unit stays a finding — SEED case 24. Four unit
  names had accounted for 6 of 15 findings across three audits without one ever being a
  real break.
- **`.log` files** moved to rung 3, which is rung 3's own definition of runtime state.

### `MEMORY.md` grew 69% in three days and the line heuristic could not see it

32,397 → 54,808 chars between 2026-08-13 and 2026-08-15, while lines moved only 82 → 91.
It grows by lengthening lines. 54 session-log lines held **42,694 chars — 78% of the
file** — against the file's own older convention of ~110 chars per entry. All 15 oversized
entries were verified to have their full repo session file (4.6k–21.7k) **before** any
trimming. Compressed to that convention; the ⛔ "no repo file" entry was left untouched.

### Zero findings is the result the skill says to distrust

So the check was proven alive on the **real** documents, not just the fixture: seven
seeded breaks, one per class touched (plain, self-prefix, `.service`, `.timer`, sibling,
`.html`, `.png`) — **all seven caught**, and restoring returned it to zero. Same control
for the orphan check.

---

## What went wrong, and what caught it

**The checker caught three of my own document edits.** A `<!-- placeholder -->` on a line
whose backticked span is a *command*, so it covered no path; a marker on
`probe/embedding_probe_e5small.pkl`, which **resolves** (8 copies) and was correctly
flagged STALE rather than skipped; and a *new* broken reference I introduced writing
`deploy/gpu-server/main.py` unqualified.

**Compressing `MEMORY.md` broke a reference by editing its NEIGHBOUR.**
`display_ranking.py` resolved at rung 4, which needs a repo-name token within ±1 line —
and the token lived in the adjacent session entry. **A rung-4 resolution is a property of
a neighbourhood, not of a line.** Fixed by qualifying the path in its own hook.

**I over-wrote the frontmatter and blew the size budget.** The first
`framework_reconciliation` block pushed `CLAUDE.md` to **40,380 chars — over the 40k warn
threshold** — by duplicating the whole triage into the file whose own history doc says the
frontmatter keeps only what is operative. Cut to two lines and a pointer; final 38,856.

**The entry marker and the rule total disagreed.** The new gotcha header was first written
`[11x verify-the-call-path]` while `memory/working-rules.md` read 12. Reconciled to **13**
across all three sites, which the probe now holds.

---

## Verify

<!-- verify: bash tests/fixtures/reference-integrity/run.sh 2>&1 | tail -1 -->
<!-- verify: python3 tests/fixtures/reference-integrity/refcheck.py 2>&1 | grep -m1 '### FINDINGS' -->
<!-- verify: S=$(wc -c < memory/MEMORY.md); if [ "$S" -lt 30000 ]; then echo "PASS memory/MEMORY.md $S chars"; else echo "FAIL memory/MEMORY.md grew back to $S"; exit 1; fi -->

## Carries

- [[feedback-verify-call-path]] — a **stamp** is a mechanism input, so bumping it early
  disables the check that reads it. 13th occurrence.
- [[feedback-hand-built-population]] — the audit's own extractor decided which references
  existed; a class it could not express was silently outside the population.
- [[feedback-check-must-be-specific]] — a run that finds nothing cannot distinguish a
  fixed check from a disabled one. Seed on the real documents, not only the fixture.
