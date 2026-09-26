# Session 2026-08-29 (late) — three checkers repaired; the fourth was a decline I re-adopted

**No spend, no model, no filter, no threshold, no probe touched. Nothing deployed — deploy is
N/A, not skipped.** Skills run: `/update-drift`, `/audit-context`, `/review-changes` (inline,
then two independent review agents). Changed files: `scripts/verification/` ×2,
`.claude/skills/review-changes/SKILL.md`, `docs/decisions/framework-adoption-history.md`,
`docs/TODO.md`, `memory/oracle-pricing-scheduling.md`, `memory/hypothesis-ledger.md`, this file.

## `/update-drift` — 0 releases behind

v1.36.1 pinned, v1.36.1 latest, **checked against the remote** (clone HEAD `9084baf` equals
`git ls-remote origin HEAD`). One commit past the tag touches a framework-side fixture only.
Step 0 reconciliation: **39 mentioned `(file, framework)` pairs, 15 stamped, 24 dispositioned**.
Three user-global skills byte-identical to the v1.36.1 reference install, **0 differing lines**.

**Finding**: `.claude/skills/review-changes/SKILL.md:40` read *"Latest upstream is v1.28.0"* —
false for **eleven** releases, inside a paragraph added specifically to correct an earlier stale
version claim, whose own next clause says *"do not quote a release count from here"*. Fixed by
removing the number rather than updating it. *A state claim does not become safe by being
written inside a warning about state claims.*

## `/audit-context` — verdict: defects, all of them in the instruments

Content checks were clean: 0 orphaned topic files (32, excluding 75 session records), 38 pointer
rows with 0 trigger collisions and 0 passive triggers, gitignore correct, `docs/work-items/`
absent so the work-item half is N/A.

### ⛔ THE KEEPER — a guard printing FAIL for four days, tallied `pass`

`check_prod_filters_table.sh` protects the exact `CLAUDE.md` ↔ `filter-status.md` duplication
`/audit-context` step 2 exists to find. **Three compounding defects hid that it was failing:**

1. **No `LC_ALL=C` on `sort -u`/`comm`** under `LANG=en_US.UTF-8` → `comm: input is not in
   sorted order` and a **wrong difference: 8 entries reported missing vs a correct 2**.
2. **It printed `FAIL:` and exited 0.**
3. **`run_verify_annotations.py:169` classified on `last`** — the final output line — and the
   `FAIL:` header sits three lines above it.

Broke at `4c626fa` (2026-08-25 17:32), when the `PAUSED` annotation entered the name cell.
**Both reported entries were the guard's own artifacts; there was never any real drift.**

### ⛔ A live fail-open, pre-existing

`memory/oracle-pricing-scheduling.md:97` piped `oracle_cost.py` into `grep`, so the pipeline's
status was grep's, and the script's verdict word is `MISMATCH`, not `FAIL`. **Both halves of the
assertion were destroyed** — it `return 1`s on mismatch and that could never be seen. Fixed and
verified against stubs in both directions.

## `/review-changes` — inline found 2 blockers, two agents found 4 more

The inline pass caught a **wrong re-derived number** ("eight releases", actually eleven) and a
**sensitivity regression** in my own classifier fix. Then two agents with deliberately
non-overlapping framings — a fail-open hunter and a claim auditor — found what I could not.

### ⛔⛔ I re-adopted a recorded DECLINE, in the file that records it

`refcheck.py`'s verdict + exit codes are **declined** in `docs/decisions/framework-adoption-history.md`
(*"Adopting it would ship a mechanism with no caller — the rule this repo has broken 16 times"*),
and I appended a new entry to the **top of that same document** without reading three sections
down. Every clause of the premise still holds. **Reverted.** Two measurements taken before the
revert: the exit-2 state was **unreachable in its own motivating scenario** (clearing `SIBS`
drives findings 1 → 181, so the verdict is `defects`), and the verdict was **a function of
unrelated directories** — `clean`/0 with one irrelevant sibling on disk, `coverage incomplete`/2
with none. ⭐ **Neither the code review nor the mutation tests could have caught it. It took a
reader who opened the document rather than the diff.**

### ⭐ My own negative was vacuous, and an agent said so

I justified the classifier change partly with *"0 differences across 33 executable blocks"*.
Today `failed=0`, so **no block emits a FAIL-bearing line at all** — neither classifier could
have said FAIL, and the zero was guaranteed. The repo's own *prove the instrument could say yes*
rule, and I stated the negative as evidence in a session about instruments that cannot fail.
(The 33 is also flag-dependent: 23 run by default.) The comment now forbids citing it.

## ⭐ `H-CX1` — SPLIT VERDICT: the prediction hit, the mechanism did not

Predicted 37,462 ±500 B at the next audit; measured **37,445** (17 B off). But the number is an
artifact of a trim landing the day before. With the cap in force `CLAUDE.md` went
**37,149 → 38,204 B in 29.3 h (~864 B/day, ABOVE the ~486 it was meant to stop)**, then `1f78b5b`
trimmed it back. **Attribution: pointer table +0 B, rest of file +1,055 B.** The cap is confirmed
*within its own scope* and the claim *holds the file at a stable size* is refuted — the growth
relocated one section over. ⚠️ **One day earlier the same audit would have read 38,204 and called
the cap a failure.** The verdict was one commit wide.

## Mine, caught before they shipped

- `bash script | tail -4; echo $?` captured **tail's** status, making four guards look like exit 0.
- A pointer-table parse that swept the **Production Filters** table too, manufacturing a
  `cultural-discovery` "collision" from the v5/v6 rows.
- A case-sensitive `grep -c "emphasis"` returning **0** — reading exactly like *never adopted* —
  against code that says `# Emphasis spans`.
- A "fix" for bolded name cells whose awk was correct but **unreachable**: a `grep -E "^\| [a-z]"`
  upstream dropped the row first. Only re-running the mutation caught it.
- Three false claims in my own new comments, each found by re-derivation, not by reading.

## Issues

**Filed**: #137 (10 reproduced shapes that still defeat the verify classifier), #138 (the budget
guard measures the file that is *not* auto-loaded and misses the one that is).
**Commented**: #134 (refcheck's document-wide strikethrough skip; non-whitelisted extensions
reported nowhere — 7 `ovr.db`, 2 `.npz` unchecked; worktree siblings invisible), #133 (the
H-CX1 attribution above).

## Next session

See `docs/TODO.md` top block. In order: **#138**, then `CLAUDE.md`'s ~2,556 B of runway, then
**#137**, then the `.claude/skills/**` tier row — the last from a session whose diff does not
contain it.
