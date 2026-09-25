# Nature recovery: re-judge the v4 training labels under NR-1, then retrain (PLAN, not run)

**2026-09-25. The assistant's proposal; nothing here has run and nothing runs without the owner's yes.**
It follows the route that produced `human_thriving v9` (adjudicate labels, retrain, gate, live audit)
instead of a new oracle prompt first (the owner: "let's wait for the re-judge first"; the re-judge is in).

## Why (`../2026-09-25-nature-recovery-miss-audit-2/README.md`, owner check 18/20)
- nr misses ~0.9 good stories per cycle that other lenses published, mostly scored too low by the MODEL
  (22/week in 2.0–3.0) or just under the cut-off (13/week); none observed via the probe.
- And only ~47% (30–64%) of what nr publishes is Nature recovery by the same definition. By ADR-023 this is
  the bigger problem: half of the tab is junk. A relabel fixes both directions at once.

## The labels (nature_recovery_v4 splits, gate's own weighting)
| band | train | val | test | total |
|---|---|---|---|---|
| ≥ 3.75 (the op-point) | 468 | 58 | 60 | **586** |
| [2.0, 3.75) | 187 | 23 | 27 | **237** |
| < 2.0 | 2,457 | 308 | 304 | 3,069 |

## Steps
1. **Pilot, $0:** 50 rows (25 ≥ 3.75, 25 in [2.0, 3.75)), plus the first audit's 4 known-answer controls. Two
   blind Claude passes under the v4 scope rubric + NR-1; the owner checks 10. Same bar as the Thriving pilot:
   controls 4/4, A-vs-B ≥ 0.90, owner ≥ 9/10.
2. **Full adjudication, $0:** all 823 rows ≥ 2.0; pass B on a seeded 20%, stop below 0.90, a split counts OUT.
   A 200-row seeded sample of the < 2.0 band as a presence check (the audit found 0/59 there in production).
3. **Label rules (a gap to close before any training):**
   - moved OUT → all dimensions capped at 2.0 (v9's rule; the v4 prompt's own out-of-scope convention).
   - moved IN (mostly NR-1's completed steps) → the row needs real dimension scores, and a cap cannot
     invent them. ⏸️ **Owner decision, priced before any call:** oracle re-score of ONLY the moved-in rows,
     with NR-1 added to the prompt, at k=3. Or leave them out of training.
4. **Retrain** on b650 with v4's settings, into a separate `runs/` dir; own calibration.
5. **Gate** on v4's 391 test ids against BOTH label sets, specificity first (ADR-023), noise band; the bar is
   pre-registered before training finishes.
6. **Live week audit**, as for v9, before any deploy.

## Not decided here
Whether Nature recovery v5's PROMPT also carries NR-1 (#71). It should eventually, so that future labels
match; this plan does not need it first.
