# <filter> <candidate>: pre-registration (<date>)

*Copy into `docs/evidence/<date>-<name>/PREREGISTRATION.md`. Write and commit it BEFORE the draw, before any
oracle call, before any score is seen. Sections 1–3 are `experiments/README.md` § Protocol; delete a section
only by writing why it does not apply (e.g. "changes nothing a reader sees").*

## 0. What is under test, and the decision it feeds

- Candidate, commit it was trained at, and what differs from the live version.
- The decision: switch / do not switch / which of N. Who decides.

## 1. The gate (held-out, one shot)

- Population, window, exclusions, seeds; bands; who labels (oracle, judges, rubric sha).
- The binding pass rule, written out. What happens on FAIL (the set is spent).

## 2. Top-of-page composition

- Fresh production draw: size, window, and why it does not overlap training or section 1's set.
- N = how many top rows, ranked by the score the site ranks on (say which: raw, or normalized).
- Classes the judges assign (the rubric's own, e.g. `out_one_moment`), two blind passes.
- **Bar, as a count:** "≤ k of N in class X". Owner-set where it encodes taste; quote the owner.

## 3. Live check after the switch

- When: 48 h after the switch. Population: what the site shows (ovr.db via the build query, never
  `live_articles`), joined to NexusMind's version stamp so the previous version's draining rows are excluded.
- The same classification as section 2.
- **Rollback bar**, fixed now, and who executes a rollback (and how: the RUNBOOK's current path).

## 4. Data

- Inputs sent to the GPU host from situla (paths). Outputs pulled back with `scripts/lab/lab.py pull` to
  `~/ld-lab/experiments/<date>-<name>/` and cited with `lab.py cite`; `check_lab_manifests.py` must pass.

## 5. Predictions (before looking)

- Each prediction with the range you would believe, so that a hit outside it reads as an instrument signal.
