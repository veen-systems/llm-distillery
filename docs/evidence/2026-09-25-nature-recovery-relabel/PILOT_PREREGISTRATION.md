# Nature recovery relabel: PILOT pre-registration (written before any adjudication)

**2026-09-25.** Owner: "spend money, it is ok" (the oracle step for moved-in rows is approved; it is priced
before any call). The bar is the assistant's proposal, copied from the Thriving pilot that preceded v9.

## What is judged
Only the SCOPE of a nature_recovery v4 training label, under `../2026-09-25-nature-recovery-miss-audit/rubric_scope_nr-v4.md`
(the v4 prompt's STEP 1, verbatim) + owner ruling NR-1 (`docs/decisions/2026-09-25-nature-recovery-scope-ruling.md`).
Verdicts: `in_scope`, `out_of_scope`, `cannot_judge`. Oracle side: in scope := the label's weighted average
(the gate's own weighting) ≥ 3.75, the v4 op-point.

## Sample (`build_pilot.py`, seed 20260930) — ⚠️ design-weighted
25 drawn from the 586 labels ≥ 3.75, 25 from the 237 in [2.0, 3.75), all three splits pooled. Equal strata, so
per-stratum rates are the report; any pooled rate must be re-weighted 586 : 237.
Plus the miss audit's 4 known-answer controls (2 in, 2 out), hidden among the 50.

## Passes
Two independent blind Claude passes, A and B, each as two subagents over a different shuffle. Same model family,
so A-vs-B measures self-consistency, not independence; the owner check is the independent part.

## Bar: all four must hold before the full run of 823
1. Controls 4/4 in BOTH passes.
2. A vs B binary agreement ≥ 0.90 on the 50.
3. Owner checks 10 rows (the rows where the A∧B consensus disagrees with the oracle, topped up at random),
   shown as faithful translations; agrees with the consensus on ≥ 9/10.
4. Presence: the consensus disagrees with the oracle on at least 1 row (else the relabel adds nothing).

## Predicted before running
≥ 3.75 stratum: consensus OUT on 30–60% (the miss audit measured nr's PUBLISHED precision at ~47%, and training
labels come from the same oracle). [2.0, 3.75): consensus IN on 10–30% (NR-1's completed steps). A guess, stated
so it can be wrong.
