---
name: project-session-2026-10-02-belonging-reshape
description: Session 2026-10-02 (afternoon) — owner rulings on belonging (middle + "doing"), reader snapshot over a month, v2 prompt parked for a v9-style training-data reshape; the curator must never be named publicly
metadata:
  type: project
---

# Session 2026-10-02 (afternoon): belonging, from prompt fixing to reshaping the data

**Spend:** $0. No oracle calls, no GPU, no deploy; belonging v1 stays live. Every read was read-only:
sadalsuud `data/filtered/belonging/`, `ovr.db`, b650 v1 splits, and the curator's public pages.

## Done
- **Owner rulings** (asked with real examples; the cryptic questions were the problem):
  - (a) MIDDLE definition.
  - (b) Robinvale counts as P.
  - (c) Marches after a harm count, so Morwell is P. Charleville is B in the test set only and stays adverse after the
    owner learned it is a reader flag.
  - Later: the ovr.news `docs/BRAND.md:84` "doing, not feeling" test was adopted for the training rubric.
- **Reader snapshot** (`docs/evidence/2026-10-02-belonging-reader-snapshot/`):
  - A month of passer volume.
  - 200 reader-facing articles read against the ruling.
  - v1's training positives.
  - Where an external curator's picks score.
- **The owner redirected the method:** "look way broader" took the work from 150 rows on one day to a month and the
  reader population. "Shape our dataset like human_thriving" turned it from prompt work into data work. The v2 DRAFT
  prompt is PARKED.
- **Plan approved** (plan mode): seven phases with owner checkpoints, in START HERE item 0. The full plan is local at
  `~/.claude/plans/adaptive-tumbling-naur.md`.
- **Owner rule:** never name the external curator in this repo or on GitHub. Its data is in gitignored
  `datasets/external_curator/`. The name is ALREADY public in places; the inventory is in the local plan, and the
  decision is pending.

## Mine (review caught these)
- I described the reader population as "normalized ≥ 4.5". The binding gate is ovr's top-50-per-lens cap (raw ≥ ~5.6).
  This was the same unnamed-population defect as before, and it made "the curator picks pass, mid-pack" wrong: 6 of
  17 could never win a slot.
- Two figures had no committed artifact (raw bands, language mix); `passer_bands.py` now carries them.
- In TODO I wrote the leak locations into the public repo while recording the rule against leaking.

## Next
`docs/TODO.md` ▶ START HERE item 0, phase 1: the rubric plus the exemplar list for the owner. Re-run
`build_test_set.py` first, because the test-set jsonl files still carry the pre-ruling labels.
