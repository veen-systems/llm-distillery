# Thriving ground-truth adjudication — PILOT pre-registration (written before any adjudication)

**2026-09-24.** Owner approved the design in session ("sounds good"). The bar numbers below are
the **assistant's proposal**. They are fixed now and will not be loosened after the results.

## What is adjudicated

Only the **scope verdict** of a `human_thriving v8` training label. The categories are the
oracle's own: `in_scope`, `out_of_scope`, `harm_is_subject`, `response_to_harm`,
`no_person_benefits`. Dimension scores are not re-judged. If the corrected verdict is not
`in_scope`, the dimensions later take the oracle's 0–2 out-of-scope convention. If it is
`in_scope`, the oracle's scores are kept.

**Definition used:** `rubric_scope_v8-4.md`, which is STEP 1 of `prompt-v8-4.md` verbatim, plus
the rulings of 2026-09-03 and 2026-09-24 (`docs/decisions/2026-09-24-thriving-scope-rulings.md`).

## Sample (`key.jsonl`; seed 20260924)

- **25 near:** drawn from the 562 labels in [3.5, 4.5).
- **25 above:** drawn from the 316 labels ≥ 4.5.
- ⚠️ **Design weighting:** the strata are equal-sized here, not proportional to the pool. Any
  rate pooled across strata must be reweighted 562:316. Per-stratum rates are the primary
  report.
- **4 known-answer controls, hidden among the 50:** Houston AC law (expected OUT, ruling 2),
  Mentawai petition (OUT, ruling 3), Madras HC permission (OUT, ruling 3), Bombay HC custody
  (IN, ruling 1). These are live articles, not corpus rows. They prove the instrument can say
  both yes and no.

## Passes

Two independent Claude passes, **A** and **B**. Each is split into two subagents of 27 articles
and each pass sees a different shuffle. Both are **blind to the oracle's label**. Same model
family, so A-vs-B measures self-consistency, **not** independence from Claude's own bias. The
owner spot-check is the independence check.

## Bar — all must hold to proceed to the remaining ~830 rows

1. **Controls:** both passes return all 4 controls as ruled (4/4 each).
2. **Self-consistency:** A vs B agree on the binary in/out-of-scope call on ≥ 90% of the 50,
   with Cohen's κ ≥ 0.75.
3. **Owner spot-check:** the owner reviews 10 rows (chosen as the rows where the A∧B consensus
   disagrees with the oracle, topped up at random if fewer than 10) and agrees with the consensus
   on ≥ 9 of 10.
4. **Presence:** the consensus disagrees with the oracle on at least 1 row. If it disagrees on
   none, the pass adds nothing and the full run is not worth doing.

If 1 or 2 fails, the rubric or instructions are fixed and the pilot re-runs on a **fresh**
sample. The same 50 are not re-used.

## Predicted (before running)

A consensus-vs-oracle disagreement rate of **10–25% in the above stratum**. This is a guess: 12
of 62 live passers flipped under the rubric (EXP-029), and ruling 1 moves one of those back.
Lower in the near stratum, where more labels are already mixed.
