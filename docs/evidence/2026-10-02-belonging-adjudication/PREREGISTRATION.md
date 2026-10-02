# Belonging adjudication PILOT: pre-registration (written before any judging)

**2026-10-02.** Phase 2 of `docs/TODO.md` ▶ START HERE item 0. The owner approved the design shape on 2026-10-02 (the
plan: blind judges, hidden controls, a drift check, the owner's 10). The bar numbers are copied from the human_thriving
pilot (`../2026-09-24-thriving-adjudication-pilot/PREREGISTRATION.md`). They are fixed now and will not be loosened
after the results.

## What is adjudicated

Only the **scope verdict** of a belonging v1 training label. Dimension scores are not re-judged. In phase 3, a row
judged out of scope has every dimension capped at 2.0, and an `in_scope` row keeps the oracle's scores.

**Definition:** `rubric_belonging.md`, which holds the owner's rulings including Q1–Q3.

**Verdicts:** `in_scope`, `out_gift_official`, `out_event_crowd`, `out_one_person`, `out_harm_is_story`,
`out_culture_topic`, `out_other`, `cannot_judge`.

## Sample (`draw_pilot.py`, seed 20261002, run on b650-gpu)

- **Pool:** every belonging v1 row (train + val + test, 7,370) with a v1 weighted average ≥ 3.5. Weights and the
  community_fabric gatekeeper are v1's.
  - The 11 v2-test-set rows (`v1_heldout_top`) are excluded. The draw printed `above` 783 = 794 − 11, so the
    exclusion fired.
- **Strata:**
  - **30 near:** drawn from the 65 rows in [3.5, 4.0).
  - **66 above:** drawn from the 783 rows ≥ 4.0.
- ⚠️ **Design weighting:** the strata are not proportional to the pool. Every row carries `n_in_stratum`. A pooled
  rate is reweighted 65:783; per-stratum rates are the primary report.
- **4 known-answer controls, hidden among the 100.** They are production articles from `exemplars.tsv`, and none is
  described in the rubric's text:
  - `british_irish_guardian_uk_3243001d4d87`, volunteers greening stations: **IN**
  - `pan_african_alwihda_info_4f54e2c1d59c`, alumni re-roof their school: **IN**
  - `west_african_punch_ng_09d36ee26016`, the navy inaugurates a water project: **OUT**
  - `east_african_lexpress_madagascar_b156bebd2863`, crowds watch traditional wrestling: **OUT** (the Q1 ruling)

## Passes

Two Claude passes, **A** and **B**. Each pass is two subagents of 50 rows, and each pass sees its own shuffle. Both
passes are blind to the oracle's label and to the stratum. **Every subagent writes into its own directory** (the
thriving v9 overwrite lesson).

This is a deliberate change from the plan's "20% pass B": pass B covers all 100 rows, as the thriving pilot did,
because 20 rows cannot resolve a 0.90 agreement bar.

Both passes are the same model family, so A vs B measures self-consistency, **not** independence. The owner
spot-check is the independence check.

## Bar: all must hold before the full run (phase 3, ~850 rows)

1. **Controls:** both passes return all 4 controls as expected on the binary in/out call (4/4 each).
2. **Self-consistency:** A vs B agree on the binary call (`in_scope` vs anything else) on ≥ 90% of the 96 sample rows,
   with Cohen's κ ≥ 0.75.
3. **Owner spot-check:** the owner reviews 10 rows, blind to the judges' verdicts, and agrees with the A∧B consensus
   on ≥ 9 of 10.
   - The 10 are rows where the consensus disagrees with the oracle. The oracle counts as "in" at ≥ 4.0.
   - If there are fewer than 10 such rows, the list is topped up at random.
4. **Presence:** the consensus disagrees with the oracle on at least 1 row.

**If 1 or 2 fails,** the rubric or the instructions are fixed and the pilot re-runs on a **fresh** sample.

## Also reported (not bar items)

- **`cannot_judge` per stratum.** 44 of the 96 rows carry under 600 characters of content (RSS-snippet length). The
  v1 oracle labelled from that same text.
- **The out-of-scope classes** among the consensus-out rows of the `above` stratum.

## Predicted (before running)

- **`above`:** the consensus calls 15–35% `in_scope`. The anchor: Claude read ~10 of 60 random v1 positives as fits
  under the middle ruling, before the doing test.
- **`near`:** 5–20% `in_scope`.
- **`cannot_judge`:** 5–20% overall.

⚠️ The prediction and the judges share a source (Claude), so a hit inside the range is not confirmation.
