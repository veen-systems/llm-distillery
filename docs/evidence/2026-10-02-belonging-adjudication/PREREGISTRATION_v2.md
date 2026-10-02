# Belonging adjudication PILOT v2: pre-registration (written before the draw and before any judging)

> ⚠️ **Rubric pointer (2026-10-02 close):** "rubric_belonging_v2.md" below meant **v2.0**, now kept verbatim as `rubric_belonging_v2_0.md`; the path now holds v2.1. **Result:** item 3 (owner) **not met**, 7/10 against ≥ 9/10 (`README.md` § *Review corrections*).


**2026-10-02.** Phase 2R of the revised plan (`docs/TODO.md` ▶ START HERE item 0). The first pilot failed the owner
check at 3/10 (`PREREGISTRATION.md`, `README.md`).

**Definition:** `rubric_belonging_v2.md`, approved by the owner on 2026-10-02.

**Bar:** the same as the first pilot. It is fixed now and will not be loosened after the results.

## Verdicts

`in_scope`, `out_gift_official`, `out_one_moment`, `out_harm_is_story`, `out_culture_topic`, `out_event_spectated`,
`out_other`, `cannot_judge`.

## Sample (seed 20261003)

**v1 strata.** `draw_pilot_v2.py`, run on b650-gpu, with v1's weights and gatekeeper:
- **30 `near`:** v1 weighted average in [3.5, 4.0).
- **40 `above`:** ≥ 4.0.

**Production stratum.** `draw_prod_v2.py`, run on sadalsuud:
- **30 `prod`:** `stage2` belonging passers (raw ≥ 4.0) from files stamped 20260926 or later.
- `news.google.com` and content under 300 characters are excluded, and repeat `content_hash` values are dropped.

**Excluded from every stratum:**
- the first pilot's 100 ids
- the v2 test set
- the 150-row held-out production sample and the 49 probe rows
- every exemplar, v1 and v2
- the 200-row reader sample

The v1 near pool shrinks by the first pilot's 30, so near is drawn from ~35 rows.

**Design weighting:** the strata are not proportional to their pools. Every row carries `n_in_stratum`, and
per-stratum rates are the primary report.

**4 known-answer controls** come from `exemplars_v2.tsv`. They exercise the boundaries the owner just ruled:
- **IN:** `arabic_khaleej_times_96980715085f` (a seniors' club; social clubs ruled in)
- **IN:** `spanish_eldiario_1292add7258e` (a family craft across generations; ruled in)
- **OUT:** `south_american_cuba_headlines_d8011b247ea7` (one barber's free haircuts: a one-off moment)
- **OUT:** `australian_abc_au_fb9f91573d7b` (a car festival: spectated)

⚠️ The rubric describes both IN shapes generically, so these controls test whether the ruling transmits. They do not
test unseen judgement.

## Passes

Pass A and pass B each run as two subagents of 52 rows, on different shuffles. Every judge is blind to the oracle, the
stratum and the scores.

**Every judge gets its own input/output directory AND its own scratch directory.** In the first pilot one judge
overwrote another's temporary script.

## Bar: all must hold before phase 3

1. **Controls:** 4/4 on the binary call in each pass.
2. **Self-consistency:** A vs B binary agreement of at least 0.90 on the 100 sample rows, with κ ≥ 0.75.
3. **Owner spot-check: at least 9 of 10 agree with the A∧B consensus.**
   - **The rows:**
     - 6 consensus-vs-oracle disagreements, at least 2 of them from `prod`
     - 4 consensus `in_scope` rows, so the judges are checked for looseness as well as strictness

     If either group runs short, it is topped up at random from consensus rows.
   - **What "oracle in" means:**
     - for v1 rows, a v1 weighted average ≥ 4.0
     - for `prod` rows, always in, because every row passed the student
   - **The owner reads the article's own title and opening ~600 characters, not Claude's summary.**
4. **Presence:** at least 1 consensus-vs-oracle disagreement.

**If 1 or 2 fails,** the rubric or the instructions are fixed and the pilot re-runs on a fresh sample.
**If 3 fails,** the owner's disagreements are turned into rulings first.

## Predicted (before the draw)

Consensus `in_scope` rate per stratum:
- **`above`:** 15–35%. The strict rubric gave 4/66. v2 is wider, adding intergenerational ties, care, clubs and
  events, but one-off moments still dominate v1's positives.
- **`near`:** 5–25%.
- **`prod`:** 25–50%. The reader snapshot read 16% fits plus 18% borderline under the stricter middle ruling, and v2
  is wider.
- **`cannot_judge`:** under 10% overall.

⚠️ The predictor and the judges are both Claude, so a hit inside a range is not confirmation.
