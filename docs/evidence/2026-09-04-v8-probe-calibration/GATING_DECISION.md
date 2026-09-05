# Should the Stage-1 screen gate harder? — the trade, measured

**2026-09-04. `EXP-020`. $0**, GPU time only. Raised by the owner, re-opening their own
2026-08-28 *hold-near-pass-through* ruling: *"this was supposed to be a needle-in-haystack
filter, 89% pass-through does not sound needle to me."*

Reproduce: `scripts/gating_tradeoff.py` → `gating_tradeoff.txt`.

---

## The short answer

**Harder gating is available and it costs about one needle in thirty-five.** Your shipped
probe can screen at **52% weighted routing instead of 89%** — a **38% cut in scoring cost** —
at a price of **1 of 35 test positives**, unrecoverable.

⭐ **But the ruling looks right on its own stated premise, and there is a second cost nobody
had written down.** Both are below.

## 1. How hard can the screen go, at a given FN budget?

Threshold selected on **val**, evaluated on **test** — never both on the same split.

| probe | threshold | test routing | test FN | weighted routing |
|---|---|---|---|---|
| **recall e5-small (shipped)** | 2.825 | 56.5% | **1/35** | **52.1%** |
| recall e5-large | 2.350 | 47.6% | 2/35 | 43.2% |
| regression e5-small | 0.600 | 55.3% | 1/35 | 50.8% |
| regression e5-large | 1.150 | 30.3% | **6/35** | 25.6% |

⭐ **A better ranker does not buy a safer screen.** Regression e5-small ranks above
the shipped probe (AUC 0.9035 vs 0.8710) and lands on essentially the same screen — 55.3%/1FN
against 56.5%/1FN. Ranking quality and screen safety are different properties, and this is
the measurement that shows it rather than assuming it.
⛔ **"far better" was an ordering published without a band, and the band was added on
2026-09-05: ΔAUC = +0.0325, 95% CI [−0.0054, +0.0725], P = 0.094 — the interval INCLUDES ZERO,
so the two are NOT DISTINGUISHABLE on this split** (paired bootstrap, positives and negatives
resampled separately, 10,000 replicates, seed 42, both published AUCs reproduced as a control:
`scripts/auc_ordering_band.py`, `auc_ordering_band.txt`). Found by
`scripts/verification/check_claim_shapes.py --check ordering-needs-band`. ⭐ **The section's
conclusion is unaffected and is in fact strengthened** — if the ranking gap is not even
resolvable, "a better ranker does not buy a safer screen" is the weaker claim to have to
make.

⛔ **And ADR-011 is right where it applies.** Regression e5-large screens hardest and drops
**6 of 35 positives — 17% of the needles.** That is floor-collapse in the screen role, as
written. (I had reported this prediction as "not holding" from the scorer role. Corrected.)

⚠️ **A threshold giving 0% FN on val gave 1–6 FN on test for every probe.** Threshold
selection does not generalise reliably at 31/35 positives. Any tightening is provisional
until there are more positives — llm-distillery#141.

## 2. What tightening buys, in compute

Two-stage cost is linear in the routing rate: `3.74 + r × 43.70` ms/article on GPU.

| routing | two-stage | vs e5-large alone (26.79) |
|---|---|---|
| 100% (no gate) | 47.44 ms | e5-large 1.77× cheaper |
| **89% — adopted** | **42.63 ms** | e5-large 1.59× cheaper |
| 61% | 30.40 ms | e5-large 1.13× cheaper |
| **52.7% — break-even** | **26.79 ms** | tied |
| 40% | 21.22 ms | two-stage 1.26× cheaper |
| 25% | 14.67 ms | two-stage 1.83× cheaper |

⭐ **The adopted 89% sits well above break-even, and that is the only reason
e5-large-alone is competitive at all.** Tighten the screen past ~53% and the two-stage
architecture wins outright on cost *and* on quality.

## 3. ⛔ The cost of tightening that is not compute

A screened-out row does not merely skip the student. **The probe's numbers become the
article's published scores and tier** — `result["scores"] = screen.scores`, then
`_assign_tier` (`hybrid_scorer.py`, Stage-1-LOW branch). The probe is the scorer of record
for everything it screens out.

| routing | share of corpus scored by the probe |
|---|---|
| 89% (adopted) | **11%** |
| 52% | **48%** |

And the shipped recall-objective probe's scores are **inflated +1.98** on the weighted average
and **3.4× worse per-dimension** than the student's (MAE 2.073 vs 0.614), with a mechanism:
`pos_weight ≈ 20` pushes every prediction up and the auxiliary L1 is weighted only 0.1.

**So tightening the screen quadruples how much of the corpus carries the weaker instrument's
scores.** If the screen is ever tightened, it should be paired with a **regression-objective**
probe — not for its ranking, but because regression removes the inflation (per-dim MAE
0.762, bias −0.298).

⚠️ Tier assignment is unaffected today: screened-out rows sit below the Stage-1 threshold,
far below the 4.5 surfacing boundary, so they are tiered `low` either way. This becomes live
when a `normalization.json` maps raw scores to percentiles — Stage-1-LOW and Stage-2 rows
would then be two populations on two different scales sharing one CDF.

## 4. Was the 2026-08-28 ruling right?

**On its stated premise, yes.** The ruling's reasoning was: *no Stage-2 cost constraint was
claimed, so the FN risk is not bought.* Buying a needle for a cost saving nobody needs is a
bad trade under ADR-023, where the false negative is the cheap error only when nothing is
gained by risking it.

⭐ **And "89% doesn't sound needle-like" conflates two things.** The filter's needle-ness is
its **base rate** (4.80% positive). The screen's tightness is set by the **ranker's quality**:
demanding near-zero FN from a probe at AUC 0.87 on a 4.8%-positive corpus *forces* a
permissive threshold. 89% is not slack — it is what recall-safety costs at this ranking
quality. The measurement in §1 is what makes that concrete: even a much better ranker could
not tighten it safely.

## What would change the answer

1. **A Stage-2 cost constraint appearing.** Then 52% is the move: 38% cheaper, ~1 needle in
   35, paired with a regression probe to keep the published scores honest.
2. **More positives (#141).** Everything here rests on 31 val / 35 test positives, and the
   val→test threshold drift shows that is not enough to fix a screen point reliably.
3. **A GPU ratio from gpu-server.** All timings are b650. Ratios should travel; the
   break-even point moves if the production probe/student ratio differs.
