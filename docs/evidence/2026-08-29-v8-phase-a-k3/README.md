# Phase A k=3 — the reorder is not label-neutral; the flip rate is not distinguishable from the probe's

**2026-08-29. Spend: $0.867** (DeepSeek off-peak, 1,200 calls, **0 errors**). No model
trained, no threshold moved, nothing in `filters/` changed, nothing deployed.

Design fixed in [`PREREGISTRATION.md`](PREREGISTRATION.md) **before the draw and before any
call** — committed in `ff88b56`, one commit ahead of the results and unchanged between them.
Four of its seven predicted ranges were missed (§6).

⚠️ **This document was rewritten after a five-lens review on the same day.** The first
version overstated four things and the corrections are marked ⛔ **CORRECTED** inline. They
are kept visible rather than silently fixed, because three of the four had already
propagated into `docs/TODO.md`, the v8 plan and the hypothesis ledger.

## Headline

1. ⛔⛔ **H-V8-3 is RESOLVED and it reverses the plan's assumption: moving the article to the
   end of the prompt CHANGES THE LABELS.** On the production-mix stratum,
   mean(reordered − as-is) = **−0.239**, 95% CI [−0.409, −0.080]. It survives a 20,000-draw
   sign-flip permutation (**p = 0.0049**, 20,000 draws), source clustering ([−0.408, −0.083]), and
   and source clustering ([−0.410, −0.078], 120 sources). On the boundary stratum it is
   **−0.443** [−0.764, −0.138] (p = 0.0063), source-clustered [−0.747, −0.150].
   The reordered prompt is a **stricter oracle**, not a cheaper copy.
   ⛔ **It is NOT multiplicity-robust, and the first write-up said the opposite.** A bootstrap Bonferroni interval was printed and has been **removed**: at α=0.05/21 on 4,000 draws each bound was a *single order statistic*, its Monte-Carlo sd ~0.014 against a reported −0.010, and it sat above zero in **408 of 500** replications — the verdict was decided by the seed. The stable instrument is the permutation: **p(R)=0.0049** clears 0.05 and 0.05/2, but **not 0.05/16 = 0.00313**, and 16 is now *derived by the script* rather than hand-counted (21 matched no count of anything). **No family was pre-registered** — that is the defect, and no arithmetic repairs it afterwards.
2. ⛔ **CORRECTED — "the effect is not just the scope gate" is NOT ESTABLISHED on the
   production mix.** The first version reported −0.235 over 41 gate-stable rows. That number
   pooled the two strata, which this run's own pre-registration forbids. Per stratum:
   **R n=21, −0.243, CI [−0.516, +0.036] — includes zero**; B n=20, −0.226, [−0.356, −0.106].
   ⛔ And it is **post-treatment conditioning**: `scope_verdict` is an outcome the treatment
   changes (16 rows are unanimously `in_scope` under as-is only, 8 under reordered only), so
   this is a collider, not a subgroup. The direction is suggestive, but the per-dimension pattern is **not** uniform on the
   production stratum — `evidence_level` is **+0.048** there, against −0.089 in the
   withdrawn pooled set — so *"on all six dimensions"* was a property of the pooled
   figure. The claim as originally written is withdrawn.
3. ⛔ **CORRECTED — the flip rate is NOT "smaller than the probe's 13%".** Measured here:
   **5.3%** production-mix ([2.7%, 8.4%]), **6.7%** (as-is) and **9.3%** (reordered) at the
   boundary, per identical-run pair. But the probe's 4/30 carries a Clopper-Pearson CI of
   **[3.8%, 30.7%]**, which contains every one of those; Fisher's exact against the
   like-for-like cell gives **p = 0.118**, and against the boundary stratum — which is what
   an op-point-weighted panel actually sampled — **p = 0.4648** against the like-for-like boundary cell (arm B — the *as-is* prompt, which is what the probe ran — stratum B, runs 1&2 = 4/50). ⛔ The first write-up quoted **p = 0.722** without naming its cell; both readings that produce 0.722 use a non-comparable cell *and* give the larger p, i.e. the one that supports the conclusion being drawn. The conclusion survives at 0.4648; the number was chosen, not derived. The design-weighting
   explanation is plausible and is *not distinguishable from n=30 sampling noise*. What this
   run adds is a usable interval, not a refutation.
4. **The old "all six dims ≤ 2" inference was 98.8% right** over 1,200 now-recorded labels.

## Why the 2026-08-28 probe could not see finding 1

Its null arm was **a second run of the control**, compared against the treatment as a whole —
one alternative number with no interval. Here the null is measured **on the same rows at the
same pair level**: 6 within-arm pairs and 9 between-arm pairs per row, row-clustered
bootstrap on the difference.

| stratum R (n=150) | within (null) | between | diff, 95% CI |
|---|---|---|---|
| share of pairs moving > 0.16 | 34.9% | **52.4%** | [12.4%, 22.7%] |
| mean \|Δ\| | 0.312 | **0.630** | [0.196, 0.459] |
| op-point crossing rate | 2.4% | 4.2% | [0.2%, 4.0%] |

| stratum B (n=50) | within (null) | between | diff, 95% CI |
|---|---|---|---|
| share of pairs moving > 0.16 | 39.3% | **52.9%** | [6.4%, 21.7%] |
| mean \|Δ\| | 0.421 | **0.767** | [0.141, 0.590] |
| op-point crossing rate | 12.7% | 16.2% | [−0.4%, 8.9%] |

⛔ **The Bonferroni column that stood here has been deleted, not recomputed.** These are
nominal 95% intervals over a family of **16** that no pre-registration named. The
stratum-R op-point cell (lower bound 0.2%) and the stratum-B one are the two nearest
their bound; neither should be read as established. See § *Headline* for why the
bootstrap Bonferroni was seed noise.

⛔ **CORRECTED — the stratum-R op-point crossing cell was labelled "EFFECT: CI excludes 0"
on a lower bound of 0.2%.** It survives no multiplicity correction. Now reported as not
established. `analyse.py` no longer prints a Bonferroni interval at all — see the family note above and §4h of `results.txt`.

⚠️ **A known bias in this test, not disclosed in the first version.** Pooling the two arms'
within-pairs into one null inflates the "between" side whenever the arms differ in noise —
√(a²+b²) > (a+b)/√2 for a ≠ b — and they do differ (9.3% vs 6.7% flip rate). At the observed
noise ratio the inflation is ~1%, far below the measured 2.02×, so the stratum-R conclusions
hold; the two cells nearest their bound are the ones already reported as not established.

⚠️ §1 and §2 of `results.txt` are **algebraically the same statistic** — over three runs a
binary is 3–0 or 2–1, so discordant pairs = 2 × non-unanimous rows, always. They are not two
corroborating findings.

## Three controls, run before believing any of it

- **Time drift.** Arm A ran ~1 minute before arm B in every round. Per-run cohort means:
  **A 1.524 / 1.566 / 1.537** (spread 0.042), **B 1.809 / 1.843 / 1.845** (spread 0.036). The
  ~0.29 gap is present in all three rounds and no within-arm spread approaches it.
- ⛔ **CORRECTED — cache state, which the first version did not name at all.** Arm A ran
  cache-warm throughout (89.2% on run 1); arm B's run 1 was cold (0.0%). Cache state and run
  order are **collinear** in this design, so the run1→run2 step cannot bound both nuisances —
  the same number cannot be the time-drift evidence and the cache-effect bound. The
  cache-matched comparison can: restricting to runs 2 and 3 of both arms (99.4% vs 99.5%
  cached) gives **A 1.5515 − B 1.8440 = −0.2925**, marginally *larger* than the k=3 gap of
  −0.2897. The finding survives; the first version's silence was the defect.
- **Prompt identity.** Re-verified here: **42,406 → 42,411 chars**, non-blank line multiset
  differs by exactly one `---`, article offset **617 → 40,626**.

## The cost picture, re-derived from token counts

⛔ **CORRECTED — every figure in the first version was the `$0.02f` rounded display ÷ 200.**
Re-derived from the per-row `usage` blocks at the script's own off-peak rates:

| | cache hit, run 1 | $/article, run 1 | was published as |
|---|---|---|---|
| arm A, article last | **89.2%** (ceiling 95.8%) | **$0.000519** | $0.00050 |
| arm B, as-is | **0.0%** | **$0.002736** | $0.00275 |
| repeat runs (2–3), **arm A** | 99.4% | **$0.000266** | $0.00025 |
| repeat runs (2–3), **arm B** | 99.5% | **$0.000275** | $0.00025 |

Ratio **5.27×** (published as 5.5×). **Total spend $0.867** (published as $0.85).

⚠️ **The k=3 repeat discount is UNPROVEN at corpus scale.** Runs 2–3 cost that little because
the identical prompt came back ~1 minute later. A 6,590-row pass takes ~30 minutes and
**nothing here measured DeepSeek's cache TTL**. Scheduling k=3 as three back-to-back calls
**per article** rather than three passes removes the assumption.

Corpus k=3 on 6,590 rows — *with* the unproven discount: **reordered ≈$6.92, as-is ≈$21.65**.
Without it: **≈$10.27 / ≈$54.08**.

## What this makes into an owner decision

The reorder is **~5.3× cheaper on the paying call and a different labelling function**, so it
cannot be adopted as a cost optimisation — it has to be chosen as a scoring change:

- It is **stricter**. Per stratum (⛔ **CORRECTED — the first version pooled these**):
  rows above the 4.5 op-point at k=3 are **8/150 vs 11/150** on the production mix and
  **7/50 vs 12/50** at the boundary — **−27%** and **−42%**, not a single "−35%", which was a
  panel figure from a 4.4×-oversampled mix. `in_scope` share was likewise published pooled
  (28.7% vs 32.8%); read it per stratum from `results.txt` §4b.
- ADR-023 wants specificity, so *stricter is not obviously wrong* — but v8 was adjudicated in
  its **as-is** form, and ≈$15 on the corpus is small against the adjudication time the plan
  already calls "the real cost".

**Not adopted here.**

## §6 — predictions vs outcomes

| quantity | predicted | measured | |
|---|---|---|---|
| stratum B flip rate | 15–35% | **6.7–9.3%** | ⛔ miss, low |
| stratum R flip rate | 4–15% | 5.3% | ✅ |
| rows non-unanimous at k=3, stratum B | 20–45% | **10–14%** | ⛔ miss, low |
| median between-arm \|Δ\| | < 0.20 | 0.217 (R) / 0.192 (B) | ⚠️ borderline |
| median within-arm \|Δ\| (null) | 0.05–0.20 | **0.000 (R)** / 0.100 (B) | ⛔ miss, low |
| cache hit, arm A run 1 | 85–94% | 89.2% | ✅ |
| total spend | $1.0–2.2 | **$0.867** | ⛔ miss, low |

⭐ **Four misses, all the same direction: I over-predicted variability and cost**, having
anchored on a 30-row op-point-weighted panel. An anchor drawn from a design-weighted sample
biases the *prediction* too, not only the estimate it came from.

## Deviations from the pre-registration, reported not substituted

1. The pre-registered parity rule — *median between-arm |Δ| on k=3 means ≤ 1.5 × median
   within-arm |Δ|* — is **biased and unusable**: biased because a k=3 mean is less noisy by
   construction, unusable because the within-arm median is **0.000** in stratum R, so the
   ratio divides by zero. **A bar that cannot be evaluated is not a bar.**
2. The pre-registered op-point rule had **no error bar** at counts of 3–8 out of 150.
3. ⛔ **The pre-registration's own ban on pooling was violated by the first version of this
   document** in four places (the 41-row subgroup, "15 vs 23", "~35% fewer", "28.7% vs
   32.8%"). All four are now per-stratum. The rule was right; the write-up ignored it.

## Selection independence

Stratum B selects on v7 `raw_weighted_average ∈ [4.0, 5.0)` — a **pre-treatment** variable
produced by a different model, and the design is paired within row. Selection therefore
cannot depend on the quantity being compared. (Stated explicitly because the review found it
was assumed, not written.)

## Reproduce

```bash
# Draw (on sadalsuud, which holds the archive; window re-enumerated at draw time)
python3 draw200.py > phaseA_cohort200.jsonl 2> cohort_manifest.json

# Six passes, interleaved A1 B1 A2 B2 A3 B3, through the real call site.
# Arm A uses prompt-candidate-tail.md; arm B uses prompt-candidate.md.
PYTHONPATH=. python scripts/score_deepseek_production.py \
  --input phaseA_cohort200.jsonl --output phaseA_A1.jsonl \
  --config filters/uplifting/v7/config.yaml \
  --prompt filters/human_thriving/v8/prompt-candidate-tail.md \
  --concurrency 8

PYTHONPATH=. python docs/evidence/2026-08-29-v8-phase-a-k3/analyse.py <dir-with-the-six-outputs>
```

The analysis expects `phaseA_cohort200.jsonl` and `phaseA_<arm><run>.jsonl` in that
directory. ⛔ The first version of this block wrote the cohort to `cohort200.jsonl`, which
`analyse.py` does not open, and used a shell brace expansion that `argparse` rejects.

⚠️ **Runs of this cohort predate the `prompt_hash` stamp** added the same day
(`scripts/score_deepseek_production.py`). In those six files both arms carry an identical
`filter_version: "7.0-deepseek"`, so **arm identity rests on the filenames**. The per-row
`usage.prompt_cache_hit_tokens` block is the only independent discriminator (89.2% vs 0.0% on
run 1). Any re-run will carry `prompt_hash` and `prompt_file` instead.

⛔ **The cohort is not committed** — full article text at scale is the #97 hazard.
`cohort_manifest.json` records the window, pool sizes and design weights, which is what a
re-draw needs. ⚠️ **It predates `draw200.py`'s `archive` key** (added on review, so the
manifest can name the glob it read) — the committed manifest has no such key, and a re-run
of the documented command produces a manifest with one. Regenerating it requires sadalsuud. `results.txt` is `analyse.py`'s output verbatim.

**Population:** `sadalsuud:~/local_dev/NexusMind/data/filtered/uplifting/`, window
`filtered_20260814_165416` → `filtered_20260828_131614`, **83 files, 232,564 rows**.
Exclusions applied **in this order**: `news.google.com` 53,793 (23.1%), then content < 300
chars 21,345 (short *among non-GN*), then `stage_used != stage2` 15,052, then duplicate id 1
(counted among rows surviving the filters, not corpus-wide) → **142,373 eligible**, of which
**10,738** in the [4.0, 5.0) band. ⚠️ Both strata therefore describe the **stage-2
population**; no claim here transfers to stage-1 rows. The window rolls.
