# `max(title, full)` survives a change of seed (#159, H-DET5, EXP-057, 2026-10-21)

Pre-registered (`PREREGISTRATION.md`, `b312f31`, before the run). $0: b650, daytime. The v5 head was retrained at each
seed in `SEED_SET` (EXP-034's protocol). Eval: the leak-free obituary heldout, n = 1,537 (25 leaked rows dropped),
322 positives. Raw output: `result.txt`; lab `experiments/2026-10-21-obituary-maxrule-multiseed/run`.

## Result: both title rules help at EVERY seed. The trade-off #159 names is now measured, not single-seed

| rule (at 0.85) | recall band | specificity band | paired Δrecall vs full | paired Δspecificity | paired ΔFP |
|---|---|---|---|---|---|
| full (as now) | 0.7516–0.8447 | 0.9770–0.9885 | — | — | — |
| `max(title, full)` | 0.8106–0.8789 | 0.9597–0.9819 | **+0.0342 to +0.0590, 5/5 positive** | −0.0173 to −0.0058 | +7 to +21 |
| `max(title@0.99, full)` | 0.7764–0.8602 | 0.9720–0.9885 | **+0.0093 to +0.0248, 5/5 positive** | −0.0049 to 0.0000 | 0 to +6 |

- **The bands overlap, but the pairs do not:** every seed points the same way, for both rules. The overlap is the
  seed's effect on the shared head; the paired difference is the rule's.
- **Plain max:** at every seed it catches 11–19 more obituaries for 7–21 more clean articles blocked.
- **The 0.99 gate:** it catches 3–8 more for 0–6 more blocked.
- **Positive control:** the seed-42 refit against the shipped v5 gives corr 0.9954 with 12 of 1,562 flips at 0.85.
  EXP-034 got 0.9952 with 10 flips: close, NOT identical. The likely cause is the GPU change (3090 Ti → 5090);
  sklearn's MLP is not bit-reproducible across environments.
- `result.txt` is produced by `make_result.py` from the run's JSON.

## Predictions, scored

1. Plain max raises recall at every seed, by +0.03 to +0.07: **HIT** (+0.0342 to +0.0590).
2. Plain max lowers specificity by 0.005–0.02 at every seed: **HIT** (−0.0058 to −0.0173).
3. The 0.99 gate's Δrecall is positive at ≥ 4 of 5 seeds and smaller than plain max's: **HIT** (5/5; smaller at
   every seed).

## What it does NOT decide

Which rule ships is still the owner's call (#159). Recall-first (owner 2026-07-30) points at plain max; ADR-023
(specificity is the budget) points at the 0.99 gate. This removes #159's "one seed" objection only.

⚠️ **Caveats:**
- Seed 101 is the outlier on cost: plain max at +21 FP. Its own full-text baseline is already the most permissive
  (recall 0.8447, spec 0.9770).
- The heldout is all Latin-script (the H-DET register), so this says nothing about non-Latin obituaries.
- Class C (death-as-news, #85) is untouched by either rule.
- Shipping either rule adds one title embedding per article (#89 would make that cheaper).
