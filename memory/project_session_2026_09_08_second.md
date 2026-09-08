# Session 2026-09-08 (second) — the cutover is a 7× cut, and Phase E's rows arrived to a guard that refuses them

**Spend: $0.** No oracle calls, no judges, no GPU. Registry **EXP-030**.
Evidence `docs/evidence/2026-09-08-v7-v8-same-articles/`. New issue **#154**.
Commits `b28e456`, `9fb3feb` (not pushed).

## What was picked up

`docs/TODO.md` flagged two things. Both were attempted; one delivered, one turned out to be
blocked by our own code.

## 1. The free comparison (`EXP-030`) — the measurement #151 step 5 was missing

Both lenses are enabled and score every article of every cycle, so this is arithmetic over
output NexusMind had already written. Four consecutive cycles, **15,372 articles**, both lenses.

⛔ **The cutover is not a swap, it is a 7× cut.** v7 surfaces **1,184**, v8 **168**; v8 is nearly
a **subset** (152/168 = 90.5%), so the Thriving tab loses **1,032** and gains **16**.
Jaccard **0.127**; v8 produced **no `high` tier at all** (max raw 6.222 vs v7's 7.560).

⛔ **And lowering v8's op-point does not fix it — tested against a null that could have said so.**
On the clean both-stage2 frame, volume-matching (op-point 2.820) recovers **57.5%** of v7's
passers where a Spearman-matched *"v8 = noisy rescaled v7"* null gives **76.8%**; within-union
Spearman **0.3436** against the null's **0.5630**.

⭐ **Where the dropped rows go, also free:** 44.7% of the 1,032 are already surfaced by another
lens (baseline **7.65%**), so ~55.3% are surfaced by **no** other lens — **242 · 128 · 96 · 105**
per cycle, 110 on the three normal ones. ⛔ That is *surfacing*, not a claim about readers.

⚠️ **None of it says which lens is RIGHT.** No labels. Judging the 1,032 is the unfunded half.

## 2. Phase E: the rows arrived, the fitter refused them (#154)

The 09:30 cycle took the cumulative count to **202 of 200**. `fit_normalization.py` fits cleanly
(n=202, `raw_min` **4.5** exactly, a file both consumer guards accept) and then hard-errors on its
own #205 check: it compares `sample_min` (**4.5069**) against an **absolute**
`MAX_NORMALIZATION_RAW_MIN = 4.5` — which **is** this filter's op-point. Gap to anchor **0.0069**
against the advisory tier's 0.5.

⭐ **At a 4.5 op-point that guard is a sample-DENSITY test, not the bias test it documents.** Its
own comment names the expired premise: *"no false-block possible for any real op-point
(3.75/4.0)"*, written 2026-07-16 before #102. `uplifting v7` passed it in August with a true
`sample_min` of **4.500027** on 15,698 rows — and **a refit of v7 on these four cycles would fail
it** (min 4.5018). Same filter, same op-point, opposite verdict.

⛔ **Not changed** — deploy-path guard, owner ruling. ⛔ **And the fix is two files**:
`tests/unit/test_normalization_invariant.py:190` asserts the same bound on every committed
package, so a fitter-only change leaves the output uncommittable.

⚠️ NM#319 quantified: **60.4%** (122/202) would clear the normalized 4.0 enrichment gate against
100% today, effective raw bar **4.872**. ⛔ **In-sample and near-tautological** — normalized 4.0
*is* those rows' own 40th percentile. A projection, not a measurement.

## ⛔⛔ VERIFICATION IS NOT REVIEW — 8th session running, and this time it changed the answer

762 tests, the registry checker, doc-claims, claim-shapes, both budget guards and the
filter-table check all green. A four-lens `/review-changes` returned **FOUR BLOCKERS, all in this
session's own code**, two of which changed a published conclusion:

1. ⭐⭐ **THE KEEPER — section 2 mixed two instruments, and on the frame I published my own
   headline was not established.** 3,162 rows carry an **e5 probe estimate** in
   `raw_weighted_average`. On that frame the noise null gives within-union rho **0.3654
   [0.3281, 0.4172]** against an actual **0.3463** — *inside the null*. On the clean frame it is
   excluded decisively. **The conclusion was right; the evidence for it was not.** And the
   control written to prevent exactly this was a **`print`, not an `assert`**, in a section headed
   *"they run in `compare.py` and assert"* — with a gloss true in its first clause and false in
   its second.
2. **"Spearman 0.224" was not Spearman** — global ranks correlated inside a subset. It is 0.3463.
3. **"The prompt work is not what separates the lenses"** was a count comparison across a 6-vs-56
   denominator; on rates it points the **other** way (33.3% vs 17.9%, 1.87×, Fisher p = 0.328).
4. **"55% would leave ovr.news entirely, ≈143/cycle"** — a surfacing measurement stated as
   reader-facing, with a per-cycle rate that averaged in the backlog cycle.

Also corrected: the 0.246-vs-0.127 reconciliation named a *population* difference where the two
are different **quantities** (oracle labels vs student surfacing); "5.30% design-weighted" was the
**unweighted** rate (design-weighted is 3.1638%); the 0.16 noise floor was imported unnamed and is
the **smallest** measured term (sensitivity now published); `extract.py` used `.get()` where its
docstring promised a raise; the cross-lens join and the lens set were unasserted; the window was
published as 17h against an actual **11h38m**.

⭐ **What made the keeper findable was mutating the world the code runs in** — building the null
nobody had built — not re-reading the lines. Same lesson as 2026-09-06's detached-HEAD finding.

## Corrections published

Both #151 and #154 had already been commented before the review, so both carry a correcting
follow-up rather than an edit. Four superseded surfaces updated: `CLAUDE.md`,
`memory/filter-status.md`, `filters/human_thriving/v8/STATUS.md` and `docs/TODO.md`'s 09-07
sizing projection (which predicted 2–3 cycles at v7's 5.81%; v8's measured rate is **1.093%** and
it took five).

## State at close

- ⛔ **Phase E is 202/200 and BLOCKED BY #154, not by data.** Do not disable v8 — rows keep
  accumulating unfitted.
- **The cutover ruling (#151 step 5) now has its numbers.** Four options are laid out in the
  evidence README; none is recommended, because which lens is *right* is unmeasured.
- **Nothing was pushed**, and nothing on sadalsuud was touched.
- **Carried from the 09-08 first session:** the `_wa` aggregation control is still not in the test
  suite; an authorship-independent judge is still blocked.
