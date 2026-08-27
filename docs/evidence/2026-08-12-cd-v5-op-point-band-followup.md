# `cultural_discovery v5` at the operating point — #109 arm A follow-up

**Date:** 2026-08-12
**Issue:** #109 (arm A follow-up; owner approved the ~$0.40 spend)
**Status:** **COMPLETE — verdict NOT MATERIAL / not interpretable.** Everything
above the Results section was committed in `d79a4be` before any score existed.
**Parent:** `docs/evidence/2026-08-12-cd-v5-cross-oracle-arm-a.md`
**Reproduce (sampling):**
```
PYTHONPATH=. python3 scripts/research/cd_v5_arm_a_sample.py \
  --splits-dir <splits> --meta <merged-scored> --out-dir <scratch> \
  --n 66 --noise-pairs 20 --seed 20260813 --restrict-min 4.0 \
  --bands "4.0:5.0,5.0:6.0,6.0:7.0,7.0:10.01" --exclude-design <arm_a>/design.json
```

## Why this exists

Arm A returned a bounded null corpus-wide (`D` = −0.0045, CI [−0.216, +0.195],
ν = 0.436). Its band table did not:

| band | pairs | `D` |
|---|---|---|
| `[0,0.5)` | 28 | −0.102 |
| `[0.5,1.5)` | 62 | −0.164 |
| `[1.5,2.5)` | 33 | −0.072 |
| `[2.5,4.0)` | 18 | +0.294 |
| **`[4.0,10]`** | **9** | **+1.044** |

Two reasons that is worth $0.40 rather than a footnote. First, **ADR-023 says the
thin band at the operating point is the only place a decision lives**, and arm A's
registered primary is a corpus-wide mean in which that band is 9 of 150 pairs.
Second, the sign flips there: it is the one region pointing toward *less*
defensible refused labels.

**+1.044 on 9 pairs is a hypothesis and is not cited as a result anywhere.** This
run exists to kill it or keep it.

## Design differences from arm A

Same instrument, three changes:

1. **Restricted to stored ≥ 4.0**, the runtime op-point from
   `base_scorer.py TIER_THRESHOLDS`.
2. **Finer matching bands** — `[4,5) [5,6) [6,7) [7,10]` instead of one wide
   `[4,10]` band. The wide band spans 6 points of label, and matching inside it
   would have permitted exactly the imbalance #105 showed dominates an unmatched
   comparison. It costs capacity: 88 pairable pairs at one band, **66** at four.
   Matching bought with capacity is the right trade here, because the effect under
   test is larger than the resolution lost.
3. **The 9 pairs arm A already scored are excluded** (`--exclude-design`), so this
   sample is independent of already-observed data and can carry its own
   pre-registration. Pooling the two is reported as a **secondary**, never as the
   registered primary.

Matching achieved: mean stored label **4.652 refused vs 4.666 passed**; 33 cells;
median content length 1,700 vs 1,966 chars.

## This is a near-census, and that changes what the CI means

Pair capacity at four sub-bands is 66 and `n = 66`. The Horvitz-Thompson weight
is **1.0**: every pairable pair in the op-point band is in the sample.

So there is no selection uncertainty *between* cells. What remains is (a) which
refused row is taken inside a cell where `|refused| > |passed|`, and (b) oracle
sampling noise. The bootstrap CI is therefore reported in the super-population
sense — "what would this measurement give on another draw of comparable articles"
— and **the binding constraint on interpretation is ν, not the CI.** With a
census, a CI that excludes zero is close to guaranteed for any non-zero true
difference; the noise floor is what stops that from being over-read.

**Population:** 100 refused and 649 passed rows at stored ≥ 4.0 and ≥300 chars.
The refused side is 100 rows, so the op-point region of this corpus is *small* —
2.2% of the 4,458 refused rows. Whatever comes back, it is a statement about 100
articles, and no reading may inflate it into a corpus property.

## Decision rule — fixed before any score was seen

Identical in form to arm A's, with ν re-measured for this band:

**Primary:** `D₄ = MAD_refused − MAD_passed` over the 66 pairs, paired within
cell, bootstrapped 10,000×.

**MATERIAL iff** the 95% CI excludes 0 **AND** `|D₄| ≥ ν₄`.

**ν₄ is measured on this band, not inherited from arm A's 0.436.** Arm A's ν was
arm-asymmetric (0.238 off-lens vs 0.634 on-lens) because off-lens rows return
zeros from both runs and agree trivially. Every row here is high-scoring, so ν₄
should be expected *above* 0.436, and using arm A's figure would be the same
wrong-instrument error one level down. 20 pairs are re-scored a second time
(40 rows).

**Pre-registered outcomes:**

| result | reading |
|---|---|
| `D₄` within noise | The +1.044 was small-sample noise. Arm A's null then holds *including* at the op-point, and #105's cd half closes without residue. |
| `D₄` material, refused worse | The corpus-wide null is real but **does not extend to where decisions are made**: at the op-point, refused rows' labels are less defensible. `human_thriving` v8's corpus stopping condition must then be evaluated at the op-point, not corpus-wide — and arm A's headline must never be quoted without this. |
| `D₄` material, refused better | The lens gate is refusing the better-labelled rows in the only band that matters. Would need its own investigation before any retrain. |
| CI excludes 0 but `\|D₄\| < ν₄` | Not interpretable — the same rule that demoted arm A's signed bias. Report and stop. |

**Power, stated in advance.** Arm A's per-pair SD implies a 95% half-width near
0.30 at n=66, and ν₄ is expected in the 0.4–0.8 range. So this design can
separate "≈ +1.0" from "≈ 0", which is the question asked. It **cannot** resolve
a true effect below ~0.4, and a null here therefore means "no effect of the
claimed size", not "no effect".

## Results

**Ran 2026-08-12. 66/66 pairs, 132/132 rows, 0 missing, 0 broken pairs.** One
transient failure — an arXiv physics abstract whose LaTeX backslashes broke JSON
escaping — retried successfully, so the pair is intact; it is counted in the
coverage block rather than hidden. Spend **$0.26**, against the ~$0.40 estimate.

### Primary — NOT MATERIAL

| quantity | value |
|---|---|
| `MAD_refused` | 1.7561 |
| `MAD_passed` | 1.3602 |
| `D₄` | **+0.3958** |
| bootstrap 95% CI | **[+0.056, +0.750]** — excludes 0 |
| `ν₄` (within-oracle, measured on this band, n=40) | **0.6869** (max 3.40) |
| \|D₄\| ≥ ν₄ | **no** |
| **verdict** | **NOT MATERIAL — not interpretable** |

**The +1.044 did not replicate.** At n=9 it was +1.044; at n=66 it is +0.396 —
the shrinkage a small-sample extreme produces when it is re-measured, which is
why it was carried as a hypothesis and not a finding.

The pre-registered reading for this exact cell was *"Not interpretable — the same
rule that demoted arm A's signed bias. Report and stop."* That is the verdict. The
sign is positive and the CI excludes zero, so this is **not** a clean refutation
either; the honest statement is that the effect, if real, is smaller than the
instrument can see.

### The finding that outranks the primary: at the op-point, the instrument cannot resolve the question

`ν₄ = 0.687` — the same oracle, the same article, twice, at temperature 0.3 —
**exceeds the between-arm difference of 0.396.** The floor predicted to be
"0.4–0.8" landed at 0.69, and arm A's 0.436 would indeed have been the wrong
number to reuse.

So **single-shot cross-oracle comparison cannot adjudicate label defensibility at
this operating point at all**, for either arm, at any sample size. More articles
do not help: the floor is per-article and does not shrink with `n`.

What would help is **repeated scoring of the same article**. The arithmetic, and
it is arithmetic rather than measurement — it assumes the per-article noise is
roughly normal, which 40 pairs cannot establish:

- mean \|Δ\| between two single draws = 0.687 ⟹ σ per draw ≈ 0.61
- averaging `k` draws per article scales σ by `1/√k`
- at **k = 4**, the comparable floor falls to ≈ **0.34**, below the observed 0.396

So a 4-draw design at this same n=66 would put the effect above its own floor for
roughly **4× the cost (~$1.05)**. That is the instrument this question needs, and
it is not what #109 specified. **Nothing here licenses acting on +0.396.**

### The number most likely to be misread, stated with its caveat

Every row in this sample has a stored label **at or above the op-point** by
construction. Gemini puts back below it:

| arm | stored ≥ 4.0, Gemini < 4.0 | stored ≥ 4.0, Gemini ≥ 4.0 |
|---|---|---|
| refused | **37 of 66 (56%)** | 29 |
| passed | **27 of 66 (41%)** | 39 |

Read carefully: this is **cross-oracle disagreement, not error**. Neither oracle
is ground truth (`feedback-oracle-not-ground-truth`), and with ν₄ = 0.687 a large
share of these flips are the *same* oracle's own instability rather than a
disagreement between two. It does **not** say "56% of refused surfacing decisions
are wrong". What it does say is that **DeepSeek's above-op-point calls on this
corpus are not reproduced by a second oracle on roughly half of them**, and that
is a fact about how much confidence any single-oracle op-point label deserves.

### Secondary

**Signed bias.** Gemini − stored: **−0.952 refused**, **−0.480 passed**;
difference −0.472, CI **[−1.011, +0.063]** — includes 0. Both arms negative: on
high-scoring rows Gemini is systematically *more conservative* than DeepSeek.
That is the mirror image of arm A's corpus-wide result (+0.030 / +0.353), and
together they say the two oracles differ in **slope**, not offset — DeepSeek
spreads scores wider at both ends. Not registered, not tested, and it is the most
plausible single explanation of both results.

**Per dimension** (MAD refused vs passed): `discovery_novelty` **3.030 / 2.341**
(Δ +0.689), `heritage_significance` 2.136 / 1.902, `cross_cultural_connection`
1.258 / 1.023, `human_resonance` 1.780 / 1.553, `evidence_quality` 0.992 / 1.030
(Δ −0.038). The disagreement concentrates in `discovery_novelty`, the dimension
carrying the filter's defining judgement — and its absolute MAD of ~3 points on a
0–10 scale is large in both arms. `evidence_quality`, the gatekeeper dimension, is
the *most* reproducible and shows no arm difference.

**Sub-band:** `[4,5)` +0.284 (50 pairs), `[5,6)` +0.848 (14), `[6,7)` +0.037 (2).

**Per source, ≥5 pairs:** `sciencedaily` +0.711 (7), `nature.com` +1.037 (6),
`pubmed` +0.050 (5), `reddit` −0.110 (5), `upworthy` −0.400 (5). **Sign agreement
3/5.** Two domains carry the effect and two reverse it, on 5–7 pairs each — the
#108 shape again, and a reminder that a 0.396 corpus-level number over 33 cells is
not a property of any source.

**Per language:** en +0.219 (49), es +1.013 (8), nl +0.275 (3), pt +0.800 (2),
it +3.650 (1). Nothing readable below English.

### What this changes

- **Arm A's null now covers the op-point too**, in the weak sense that the one
  region that contradicted it does not survive re-measurement above the noise
  floor. #105's `cultural_discovery` half closes without a residue that would
  block a retrain.
- **`ν` at the op-point is 0.687, and that is the number to carry forward** — not
  arm A's 0.436, and emphatically not #95's 0.16. A future op-point question on
  this filter needs a repeated-draw design; a single-shot one is unfalsifiable by
  construction.
- **`discovery_novelty` is where the two oracles disagree**, at ~3 points MAD.
  If `human_thriving` v8 or any cd successor wants tighter labels, that dimension
  is where prompt work would pay — a hypothesis, unmeasured, and the natural
  target for the repeated-draw design above.
