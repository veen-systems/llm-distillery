---
name: project_session_2026_09_26_audit_context
description: Session 2026-09-26 (evening) — /audit-context at v1.49.0, then curate; six auto-memory sessions recovered, memory/archive/ was gitignored, gotcha archive moved into archive/ (TODO item −1 step 1)
metadata:
  type: project
---

# 2026-09-26 (evening) — `/audit-context`, then `/curate` and the first prune step

**$0**, no oracle, no GPU, nothing in `filters/`. **Deploy N/A**: every changed file is
`memory/`, `docs/`, `tests/`, `scripts/maintenance/` or `.gitignore`.

## Arc

The opening ask was `/audit-context`, followed by "fix it all", then "curate, commit, push", then
(mid-curate) *"Large Read surface ?? that means we need to start pruning, thinning,
mechanizing, retiring!"*

| Thread | State |
|---|---|
| Audit report | **closed**: verdict DEFECTS, findings attributed by step in `docs/decisions/2026-09-17-audit-step-attribution.md` |
| Six orphaned auto-memory session files | **closed**: recovered byte-identical to `memory/archive/` (`3f40ee8`) |
| `refcheck.py` doc-relative for docs outside ROOT | **closed**: `rung1b-outside`, seeds 38–40, three mutations caught, 43/43 |
| Stale and duplicated auto-memory rows | **closed** (user layer, not in git; backups in the session scratchpad) |
| `memory/archive/` gitignored | **closed**: root-anchored `/archive/ /tmp/ /temp/` |
| Prune: TODO item −1 step 1 (gotcha archive into `archive/`) | **closed**: read surface 1,944,516 → 1,477,580 chars |
| Prune: item −1 steps 2–4 | **open**: `docs/TODO.md` ▶ item −1 |
| Mid-month retire (`--before 2026-09-17`) | **not yours**: owner call, because it departs from the `<YYYY-MM-01>` convention (dry run: live gotcha log 251,953 → 134,708 chars, 19 session files) |
| `/review-changes` on `3f40ee8` | **open**: not run; the `refcheck.py` change is a loosening |

## Findings worth keeping

- **Stale facts live longest in the layer nobody rotates.** Two auto-memory rows had gone
  false while the repo moved on: NexusMind#338 was "LIVE, not closed" but closed
  2026-08-12, and the harm cap was "3,000, cannot converge" but raised to 6,000 on
  2026-09-26. That was Step 3's first independent catch.
- **Step 7's first catch in its whole record, and the step's own instrument could not
  have made it.** `git ls-files` cannot list an ignored untracked file (*establish what a
  source excludes*, 25th). It is kept, and its retirement candidacy has ended.
- **The gitignore scratch-pattern class recurred a 4th time**, and my first fix negated the
  instance, which is the exact mistake the 2026-09-05 entry names. Anchoring fixes the
  pattern.
- **My mistake**: I undid a mutant with `git checkout --` while the edit under test was
  uncommitted, and lost the edit. Gotcha logged.
