# Which tab for a multi-lens article? RESULT (2026-09-26)

**R1, "narrow lens first" (Nature recovery > Discovery > Belonging > Solutions > Thriving), matches the benchmark
best: 78% N-weighted vs 66% for today's rule** (highest normalized score, `ovr.news/src/lib/data/canonical-lens.ts`).
Unweighted, 46/63 = 0.73 [0.61, 0.82] vs 29/63 = 0.46 [0.34, 0.58]: the intervals do not overlap.

⚠️ **The benchmark is the JUDGES' consensus, not the owner** (owner delegated: "keep it simple for me, i think you
know what i want"; amendment in PREREGISTRATION.md, made before any scoring). The judges' reading diverged from the
owner's today on Nature recovery (3/10) and Thriving (14–16/20). This is a recommendation to confirm on examples.

## Per stratum (judge passes agreed on 88/100; 25 of those were "none"; 63 scored)
| stratum (N/week) | R0 today | **R1 narrow first** | R3 margin | R3b |
|---|---|---|---|---|
| Nature recovery + others (161) | 3/21 | **18/21** | 6/21 | 6/21 |
| Discovery + others (828) | 3/9 | **8/9** | 1/9 | 1/9 |
| Solutions + Thriving (3,022) | 11/15 | **13/15** | 10/15 | 10/15 |
| Belonging + Thriving (881) | 5/5 | 4/5 | 5/5 | 5/5 |
| Belonging + Solutions + Thriving (626) | 4/10 | 2/10 | **7/10** | 4/10 |
| Belonging + Solutions (25) | 3/3 | 1/3 | 3/3 | 3/3 |

R1's weak spot is putting Belonging before Solutions/Thriving. An exploratory hybrid (NR, then Discovery, then R3),
designed AFTER seeing this table and so optimistic, scored 0.764 N-weighted: not better than R1 (`explore_hybrid.py`).

## Also found
**25 of 88 (28%) multi-lens articles were judged junk on EVERY tab they passed.** This is the judges' reading, and
it is a sample share over the strata, not a rate: passing several lenses is no guarantee of quality.

## The change, if the owner confirms
In ovr.news `canonical-lens.ts`, `isBetterPlacement` compares `weighted_average`. Under R1 it compares a fixed lens
priority first (recovery > discovery > belonging > solutions > thriving), with score as the tie-break inside a lens.
That is ovr.news code, so it goes to that repo as a PR; nothing in llm-distillery or NexusMind changes.
