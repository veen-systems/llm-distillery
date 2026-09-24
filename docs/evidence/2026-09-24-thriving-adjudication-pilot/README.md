# Thriving adjudication PILOT — PASSES all four pre-registered bar items

**2026-09-24.** Pre-registered in `PREREGISTRATION.md`. Result from `analyse.py`, output in `result.txt`.

| bar item | result |
|---|---|
| 1. known-answer controls | **4/4 on both passes** (Houston OUT, Mentawai OUT, Madras OUT, Bombay custody IN) |
| 2. self-consistency A vs B (n=50) | **0.960 agreement, κ 0.908** (bar 0.90 / 0.75) |
| 3. owner spot-check | **10 of 10 agreed** (owner, in session: *"all agree"*). All 10 rows were consensus-vs-oracle disagreements (`spot_check.md`) |
| 4. presence | consensus disagrees with the oracle on 33 of 48 consensus rows |

## ⚠️ Far above the prediction — and read before believing it

Predicted: 10–25% disagreement in the above stratum. **Measured:** above (label ≥ 4.5) **10 of 23
= 43.5%**; near ([3.5, 4.5)) **23 of 25 = 92.0%**. Every disagreement is in → out; none is out → in.
All 48 rows were read by hand (the assistant) before item 3 went to the owner.

The shape: the oracle marks the article `in_scope` and keeps it down with a middling score. The
articles are research abstracts, product and corporate launches, and money, MoUs or events
announced but not delivered. By the rubric's own §5 these are out of scope. Their labels sit
next to the 4.5 op-point, which is where a regression student learns to leak.

⚠️ **Design weighting:** the strata are equal-sized (25/25), not proportional (562:316). Pooled
rates must be reweighted. Only the per-stratum figures above are reported.
⚠️ **Self-consistency is not independence:** both passes are Claude. The owner check (10/10) is
the independent check, and n=10 is small.
