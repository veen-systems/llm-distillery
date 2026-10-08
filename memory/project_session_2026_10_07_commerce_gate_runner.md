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
| LD#160 | **closed as ruled**; follow-up (nature_recovery `config.yaml` tab label, v4 deployed) ruled 2026-10-07: fixed in v1/v2/v4 |
| LD#134 marking pass | **not started** (254 findings; needs judgement) |

## What I got wrong

- **I wrote "lost / expired" about 393 rows** into GATE.md and the TODO before reading
  `memory/nexusmind-data-sources.md`, which says the monthly archives keep them. Found at `/curate`, corrected the
  same session. 17th occurrence of *establish what a source excludes*.
- **The gate's first version counted unscored rows as rejections** (a reviewer forged a PASS). Fixes then had their
  own gaps (syndicated twin, Latin-only titles, query-stripping url merge): `feedback-articulating-is-not-applying`.
- **`8c464cd` was red at its own commit** (the checker scanned its own newly tracked test file).

## Next

*(Superseded by § Second half below: everything was pushed and b650 is back on `main`.)*

## Owner rulings, 2026-10-07 (after the session, "help me through decisions")

1. **Gate text: FULL text** (not the pre-registered cut text). `gate.py` now scores recovered full text for every
   row cut at 4,000 chars and raises if any is missing; v1 re-scored on full text.
2. **Training text for harvest positives: FULL text** (oracle labels stay as made on the cut text).
3. **Hard negatives: only the 121 harvest rows where BOTH judges said `out_one_moment`** (capped at 2.0), the class
   the owner agreed was out every time on v1's rows; minus any `content_twins` hit.
4. **Push** the session's commits.
5. **Fix the nature_recovery v1/v2/v4 `config.yaml` tab label** (v4 is deployed: one-line diff at the next sync).

## Second half (2026-10-07 afternoon → 10-08 close)

**Spend:** Gemini oracle, k=3 × 121 hard negatives + k=1 × 798 easy negatives (estimates ~$1.25 + ~$2.80, NOT
measured), **plus an unknown amount from ~74k failed calls** in an overnight `batch_scorer` loop (2 rows, fixed; owner to
check billing). b650 GPU: a few 5-second v1 scorings. 4 more reviewer subagents.

| Thread | State |
|---|---|
| Commerce | **closed**: deployed 2026-10-07 21:28 (NM PR #618), verified by outcome (blocks 34,385 → 13,597) |
| Owner rulings | full text (gate + training), hard negatives = 121 one-moment rows, easy negatives k=1, push, nature_recovery tab label |
| Gate | v1 full-text reference scored (spec 0.5248 = production 0.525); two more refusals (model path, v1 clone) |
| Build | script + easy-negative draw written; **NOT run**: 2 unscored easy negatives, and an owner ruling on 61 excluded v1 rows (TODO 0.1b), and the length coupling only partly fixed (TODO 0.1c) |
| Data FMEA | owner: "part of the runbook" → `docs/checklists/training-data-fmea.md` + `training/data_quality.py`, run by `validate_training_data.py --production-sample` (RUNBOOK § Prepare data) |
| Read surface | 857,038 → ~799k chars: session-log entries 09-01..09-17 moved verbatim; `retire_memory.py sessionlog` added |

**Mine:** I answered "are the articles enriched?" only after the owner asked, and first misread v1's short training
text as "consistent"; I wrote "~2–9% in production" without measuring (production also rises with length, review
corrected it); I let a background oracle run go unchecked for 12 hours; one patch deleted most of the build script
(self-caught).

**Next:** `docs/TODO.md` ▶ START HERE item 0, steps 1 → 1b → 1c (owner rulings first), then build, validate, stage,
train, gate.
