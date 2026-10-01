# Session — 2026-09-17 (final): LD#134 step 2, and a tier rule I warranted twice with an absolute I had not enumerated

**$0. No oracle calls, no GPU, nothing in `filters/`.** Deploy **N/A — inapplicable, not
skipped**: no filter package, model, calibration, normalization, threshold or scoring probe
changed. Merge **N/A** — worked on `main`, no branch. Commits `34e7b6d` + this one.

## What shipped

**LD#134 step 2** — `docs/` is tiered for `refcheck.py`, the tier is in code, and **`--docs`
does not come off the flag**. Live tier **254 findings in 60 of the 111 files it scans**
against a default run of **0**; promotion would replace the 0 baseline — the thing that
makes a *new* break visible — with a section the reader learns to skip. Precondition is the
marking pass (step 3), not more measurement. Nothing under `docs/` was edited to satisfy the
checker. Record: `docs/decisions/2026-09-17-refcheck-docs-tier.md`.

The tier is **three tests**: live by directory; else live if `CLAUDE.md`/`memory/MEMORY.md`
routes an agent into it (computed, not hand-listed); else frozen if `_archive/` or dated,
with "undated ⇒ live" restricted to a file sitting *directly* in the frozen directory.

## ⛔⛔ The keeper — the same defect twice, which is why this ended in a census

**Draft 1** tiered by directory alone, warranted with *"every frozen entry is dated BY
CONSTRUCTION"*. False: it froze `docs/decisions/framework-adoption-history.md` — undated,
edited that same day, routed into from `CLAUDE.md` twice, largest finding count of any single
frozen file — and declared it *"never to be edited to satisfy this checker"*, along with four
more pointer targets and every undated index.

**Draft 2's fix repeated the shape.** "Undated ⇒ live" at any depth admitted **13 files of
which 10 are frozen accounts** by the tier's own definition — six verbatim copies of *other
repos'* ADRs, two training reports for a filter removed 2026-08-03 — **21 findings, 7.7%** of
the live total the decision rests on.

⭐ **Two instances is a CLASS, and the round cap's own remedy is a CENSUS, not a third
round.** Two ran: every absolute about behaviour in the change's prose (3 more defects — one
of them *"every assertion here is POSITIVE about the scan set"*, in a docstring, where
several assertions are negative), and every count either tool prints against the population
it is over (19 surfaces, both defects already known).

## Also found by review, each reproduced before it was believed

- **The `/audit-context` command ran clean against our fork.** `refcheck.py . CLAUDE.md
  memory/MEMORY.md` — the skill's invocation with its one flag dropped — **exited 0 and
  printed the full default report**, because the new guard rejected only `--`-prefixed
  tokens while its own message asserted there were no positional arguments. `-docs`, `-h`
  and an em-dash `--docs` too.
- **The routing pattern had no left boundary**, so `NexusMind/docs/ARTICLE_RECORD.md`
  registered as routing into a file of ours that does not exist. Routed set 17 → 15, all 15
  now resolve.
- **`_relroot()`** — `os.path.relpath(d, ROOT)` on an *already-relative* path resolves
  against the **CWD**, so every directory-grouped report section was cwd-dependent. Latent,
  unrelated to the tier, found while writing the tests.
- **Both tier guard tests were source-text greps**, one claiming in its docstring to assert
  "against the code". Three behaviour-changing mutants survived them.

## Two numbers retracted from #134's own comments

*"43% frozen, climbing ~8× the live rate"* does not survive its denominator: the `docs/`
corpus went **168 → 242 files** in twenty days, almost all dated evidence directories — the
frozen tier by construction. And *"+4/+34"* was not a re-scoring effect. Re-scored under one
rule by a committed script: live 245 → 254, frozen 93 → 124, both lower bounds.

## Curate found two live claims that had gone false

- ⛔ **`investment_risk` is RETIRED downstream, not paused** — NexusMind ADR-025 (NM#499),
  dated **today**. The pause probe in `memory/filter-status.md` went **FAIL** because the
  `pipeline.aegis_export` block it counted no longer exists. **The check was the control
  working**; it was rewritten to assert the retirement (both arms seeded), not repaired to
  go green. This repo's `filters/investment_risk/v6/` is untouched — the ADR is
  NexusMind-scoped and does not name llm-distillery.
- ⛔ **The DeepSeek V4 Pro shutdown is CANCELLED**, not postponed again (vendor mail
  2026-09-11, surfaced by the owner). `memory/oracle-pricing-scheduling.md` said *"pushed
  back: 04:00 UTC 2026-09-14"* — true when written on 2026-09-10, superseded the next day.
  ⭐ The date moved **twice in 48 hours**; the transferable rule is to schedule oracle work
  against measurement, never a vendor calendar. Nothing of ours calls Pro. → #157.

## H-MECH-1: battery 1 of 3, and the column moved

The `Occurrences` column on a `live` Mechanized row went to **1** — and not by anyone
dutifully incrementing it. The battery's claim-verification lens found a number restated
from prose, which is that row's class exactly. ⛔ **The increment's content refutes the
comfortable reading of a 0**: `check_doc_claims.py` **could not have fired** — four
hand-listed claim pairs against a class of "any number restated" — so the row was live over
the wrong population, which a 0 would have looked identical to. Remedy shipped the same
session: `check_doc_claims.py --check suite-baseline`, red on the real restatement (the
decision record's own copy of the suite count) and `CANNOT VERIFY` when the protected line
is deleted.

## Verification

18 mutants / 18 killed (manual run, listed in the record); `run.sh` **40/40** and shown going
**red** on a seeded regression; 43 new tests across two files; suite **894 passed, 25
skipped**; `--docs` byte-identical to `HEAD` except the new section; the rung-1b refactor
byte-identical; default run still **0 findings**.

## Next session

`docs/TODO.md` ▶ START HERE, top down. Item 1 is now **#134 step 3 — the marking pass over
the live tier**, then promotion in a separate change.
