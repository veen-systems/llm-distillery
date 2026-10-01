---
name: project-session-2026-10-01-decision0
description: Session 2026-10-01 — decision 0 executed (per-lens prefilters deleted), owner decision queue cleared, belonging v2 made item 0, memory retired before 2026-10-01
metadata:
  type: project
---

# Session 2026-10-01 — decision 0, the owner decision queue, belonging v2

**Spend:** $0 oracle, no GPU. **Deploy:** none. NexusMind's sync of decision 0 is its own one-commit task.

## Done (commits on origin/main)
- `a86e6a6` **Decision 0**: 28 per-lens `prefilter.py` files and 28 `prefilter:` blocks deleted (ai-engineering-practice keeps its own). `use_prefilter=True` raises in the shared scorers. Packages keep a raising `_load_prefilter` for NexusMind's abstract base. Uplifting v7 `crime_violence` patterns frozen for the v8 draw and census scripts. Outcome proven through batch_scorer's own loader on one pre-enrichment cycle; the evidence and a verified re-run recipe are in `docs/evidence/2026-10-01-decision-0-prefilter-deletion/`. Reviewed with 6 lenses plus a round-2 adversarial pass; all findings fixed. 1213 passed, 24 skipped. LD#52 and LD#86 closed. NexusMind (`nexusmind-52`) has the sync sequence and was told the commit is pushed.
- `f2b307e`, `ae5ceaa`, `a223ebd`, `8624c05` **Owner rulings**:
  - #134 (a): the archive stays untouched. (c): keep the placeholder form.
  - #156 deferred.
  - Belonging harm cap: shadow first. human_thriving v9: no cap.
  - LD#160: a note on ADR-009; rename the script and build the language check.
  - H-V8-26: moot.
  - Drift guard: normalization freshness only, later.
  - Billing: dropped, not verified.
  - H-TV5: "seems all right" mid-drain.
  - augmented-engineering: parked.
- `a065375` **H-HD17 hand-check**: belonging 35/50 junk, v9 4/19. These are Claude's title-only calls, accepted by the owner wholesale.
- `2ba67eb` **Belonging v2 is START HERE item 0.** It follows the #130 ruling plus ovr EXP-025: the harm cap does not reach grievance-framed picks ("San communities…" scores belonging 9.99, harm 0.22). Comment posted on #130.
- `de48444` **Memory retired before 2026-10-01**: 42 gotcha entries and 18 session files moved to the archive. Default refcheck went 5 → 0, but the 5 moved with their entries rather than being fixed.

## Mine (errors)
- **The decision-0 sweep missed callers of the changed VALUE.** Three `use_prefilter=True` callers and ~12 present-tense docs were found only by review. A cross-repo sync trap was found only by the sync-safety lens. See the gotcha log, 2026-10-01.
- **Measured numbers lived only in my scratchpad** until review: two hand copies, no re-run path. The review's first fix to that recipe was itself refuted in round 2.
- **`git add -A memory/` at close**, which the working rules forbid. Checked afterwards: all 25 files were mine.

## Next session
1. `docs/TODO.md` ▶ START HERE item 0: build the **belonging v2 test set**, free and local, BEFORE any prompt change.
2. LD#160: the ADR-009 note, then the language check shown red on `cross_filter_landscape.py`, then the rename.
3. TODO item 2a: unshield the 6 dated `###` entries under the gotcha-log template heading.
