# Phase A k=3 calibration — pre-registration

**Written 2026-08-29, BEFORE the draw and before any call.** Owner approved n=200, both
arms. Everything below is fixed now so that a number cannot be chosen after seeing it.

## What this run has to settle

| id | question | why it is not already answered |
|---|---|---|
| **H-V8-4′** | the per-row rate at which two identical runs disagree on the scope binary | the 2026-08-28 probe measured **4/30 (13%)** on a cohort **stratified across the v7 score range** — that is a rate for a design-weighted sample, not for production |
| **H-V8-6** | does k=3 majority voting fix it | untested; `1/√k` does not apply to a Bernoulli |
| **H-V8-3** | does the article-last reorder change the labels | UNRESOLVED — the treatment sat inside its own null arm, with no within-arm null on the same rows |
| — | a real $/article for sizing the corpus | the plan's ≈$12 is a single k=1 run at the old prompt shape |

## The design flaw this fixes, stated first

The probe drew **30 rows stratified across the v7 score range, weighted to the op-point**.
Its 13% therefore describes *that* panel, not production. Re-using a stratified draw to
quote a production rate is [[feedback-sample-carries-its-design-weighting]] exactly.

So this run draws **two strata, reported separately and never pooled**:

- **Stratum R — n=150, uniform at random over all eligible rows.** Estimates the
  production-mix flip rate. This is the number that says how many of a corpus re-score's
  rows are coin tosses.
- **Stratum B — n=50, uniform at random over eligible rows with v7 `raw_weighted_average`
  in [4.0, 5.0).** Estimates the flip rate *where it costs a decision*. R alone cannot
  resolve this: the band is a small share of production, so an n=150 random draw would
  land too few boundary rows to say anything.

Drawn so R stays unbiased: **R first, uniformly from the whole eligible pool** (band rows
included); **B then, from band rows not already in R**. Every drawn row carries
`stratum` and `draw_weight = pool_size / n_drawn` **as data in the cohort file**, not as a
sentence in a docstring — a weight that does not travel is a weight that gets lost.

⛔ **No pooled 200-row flip rate will be reported.** The two strata answer different
questions and their populations cross.

## Population and exclusions

`sadalsuud:~/local_dev/NexusMind/data/filtered/uplifting/` — **re-enumerated at draw time**;
the window rolls (83 files at 2026-08-28 session start, 84 three hours later, 83 again on
08-29). The manifest records the window, not just the counts.

Exclusions are the plan's, not chosen here — identical to `draw30.py` so the two cohorts
are comparable:

- `news.google.com` — sub-300-char headline echoes; never oracle-re-score (CLAUDE.md)
- `content` < 300 chars — the oracle floor (`ground_truth.batch_scorer`, #93)
- `stage_used != stage2` — a `stage1_low` score is an **e5 probe estimate**, not a Gemma
  score, so it cannot stratify or band a row

⚠️ **What that excludes, stated up front:** the probe routes ~11% of rows to stage 1, so
both strata describe the **stage-2 population**. The flip rate reported here does not
transfer to stage-1 rows, and no claim about them will be made.

## Arms and ordering

Two arms on the **same** rows, k=3 each → 6 calls/row, 1,200 calls total.

| arm | prompt |
|---|---|
| **A (reordered)** | `filters/human_thriving/v8/prompt-candidate-tail.md` |
| **B (as-is)** | `filters/human_thriving/v8/prompt-candidate.md` |

⛔ **Runs are interleaved A1, B1, A2, B2, A3, B3.** Running one arm to completion then the
other confounds arm with wall-clock — vendor load and decoder behaviour drift, and that
drift would land entirely on one arm.

## Estimands, fixed now

1. **Primary (per arm, per stratum):** P(two independent runs of the same prompt disagree
   on the scope binary `in_scope` vs not). Estimated over all 3 within-arm run pairs per
   row, CI clustered by row. ⚠️ Reported **beside** the runs-1-and-2-only pairwise rate,
   which is the quantity the probe's 4/30 actually measured — like for like.
2. **Secondary:** share of rows whose 3 runs are **not unanimous** (this is what a majority
   vote must absorb) and, of those, how often the majority differs from run 1.
3. **Tertiary:** op-point (4.5) crossing rate, k=3 mean vs k=1 (run 1 alone).
4. **Parity (H-V8-3):** per-row |Δ| of the k=3 weighted mean **between** arms, against the
   per-row |Δ| **within** each arm across run pairs. This is the control the probe lacked:
   the null is measured on the same rows in the same run.

## Decision rules, fixed now

- **Parity holds** iff median between-arm |Δ| ≤ 1.5 × median within-arm |Δ| **and** the
  between-arm op-point crossing count falls inside the range of the two within-arm crossing
  counts. Anything else is reported as *not established*, never as "no effect".
- **k=3 is sufficient** iff the non-unanimity rate in stratum B is such that a majority vote
  leaves < 5% of B rows undetermined-by-margin. Otherwise the answer is k=5 or a
  deterministic gate, and that is a finding, not a failure.
- **No interim peeking.** The run goes to completion before any rate is computed. No
  stopping early on a rate that looks decided.

## Predicted ranges — written before the draw

Stated so that a number outside them forces "what did the instrument do?" before "what a
result!" ([[feedback-predict-the-range-first]]). A hit inside a range is **not**
confirmation where the prediction shares a source with the measurement — flagged per row.

| quantity | predicted | shares a source with the measurement? |
|---|---|---|
| stratum B flip rate (boundary) | **15–35%** | partly — the probe's op-point-weighted 13% informs it |
| stratum R flip rate (production mix) | **4–15%** | partly, same |
| rows non-unanimous at k=3, stratum B | **20–45%** | no — nothing has measured this |
| median between-arm \|Δ\| | **< 0.20** | no |
| median within-arm \|Δ\| (the null) | **0.05–0.20** | yes — probe measured 0.100 on gate-stable rows |
| cache hit, arm A **run 1 only** | **85–94%** | yes — 95.8% ceiling, 90.2% measured |
| total spend | **$1.0–2.2 off-peak** | no |

⚠️ **My own quote to the owner was $0.6–1.2 and it was low.** The as-is arm cannot cache its
prefix, so its run 1 costs ~2.7× arm A's. Corrected here before spending, not after.

## Two numbers this run CANNOT produce

- ⛔ **A quotable cache rate from runs 2 and 3 of either arm.** They re-send byte-identical
  prompts, so the *whole* prompt matches, not the prefix — the same artifact that made the
  probe's null arm read 99.4%. **Only run 1 of each arm carries a cache figure that a corpus
  run could reproduce.**
- ⛔ **A $/article for the corpus taken from the run total.** For the same reason: 4 of the 6
  calls per row are cache-inflated. The corpus figure comes from **run 1 of arm A only**.
