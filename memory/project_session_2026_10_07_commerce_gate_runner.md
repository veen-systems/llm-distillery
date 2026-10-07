---
name: project-session-2026-10-07-commerce-gate-runner
description: Session 2026-10-06/07 — commerce v1 over-block taken over from NexusMind and approved (0.990 + decide at the gate); belonging gate runner written, reviewed twice, v1 reference scored; the 4,000-char cut found and proven; LD#160 mechanized; two small TODO items closed
metadata:
  type: project
---

# Session 2026-10-06 evening → 2026-10-07 morning

**Spend:** $0 oracle. b650 GPU: ~6 short v1 scoring runs (5 s each, peak VRAM 3,647 MiB; `gemma3:27b` checked
absent before every run). Claude subagents: 5 reviewers (~390k tokens). Nothing deployed.

## The ask and the threads

The opening ask came from the NexusMind session (`nexusmind-2b`): commerce v1 @0.95 over-blocks (NexusMind#527);
would llm-distillery own the retrain/recalibration? The owner confirmed, approved the proposal ("do it"), then said
"continue with the work we have on LD" and left for the night.

| Thread | State |
|---|---|
| Commerce over-block: verify NM's numbers, proposal, owner approval | **closed here.** Proposal NM#527 comment 6025385135 (0.990; 0.995 alternative), approval comment 6032190593. **Implementation is NexusMind's**, queued as its next session's first build (the owner confirms to it directly). |
| Belonging gate runner (START HERE 0.1) | **closed**, `gate.py` + 29 tests; reviewed in 2 rounds (5 lenses), 1 blocker + ~10 should-fix fixed |
| v1 reference scored | **closed** (b650, `6974177`); `evaluate` verdict identical on both hosts |
| The 4,000-char cut | **open — owner call** (TODO 0.1b): gate on cut text (a) or full text (b). Proven: full text reproduces production, 0 flips on all 133 |
| Full text for cut rows | **closed**: all 509 held-out + 2,251 harvest rows (393 from the monthly archive) |
| cd v5 raw_min 4.0006 | **closed**, no change (legacy fit inside `OP_POINT_EPS`) |
| Retracted 19.9%/13.0% framing | **closed** (3 copies annotated; CLAUDE.md copy already gone) |
| LD#160 | **closed as ruled**; follow-up open — owner call on nature_recovery `config.yaml` 'Herstel' (v4 deployed) |
| LD#134 marking pass | **not started** (254 findings; needs judgement) |

## What I got wrong

- **I wrote "lost / expired" about 393 rows** into GATE.md and the TODO before reading
  `memory/nexusmind-data-sources.md`, which says the monthly archives keep them. Found at `/curate`, corrected the
  same session. 17th occurrence of *establish what a source excludes*.
- **The gate's first version counted unscored rows as rejections** (a reviewer forged a PASS). Fixes then had their
  own gaps (syndicated twin, Latin-only titles, query-stripping url merge): `feedback-articulating-is-not-applying`.
- **`8c464cd` was red at its own commit** (the checker scanned its own newly tracked test file).

## Next

`docs/TODO.md` ▶ START HERE item 0: the owner's call on 0.1b (cut vs full text) and step 2 (hard negatives), then the
build, which must write `training_manifest.jsonl` and drop `gate.content_twins(...)` (21 harvest rows) before
training. Commits on main are **not pushed** (owner's call). b650's checkout is **detached at `6974177`**
(was `main` at `8d8c510`); `git -C ~/llm-distillery checkout main` restores the old state.
