# #102 step 2 — `uplifting v7` operating point, through the ADR-021 gate

**Measured 2026-08-10. Machine-readable: `docs/evidence/2026-08-10-uplifting-v7-threshold-sweep.json`.**

*(It lives here, not in the filter package. `deploy_to_nexusmind.sh:137` is an unfiltered `cp -r`, so a research artifact inside `filters/uplifting/v7/` ships to NexusMind and on to the GPU box — changing the scorer's `CODE_REVISION` hash for an evidence file. Worse, a `--dry-run` copies without committing, leaving it UNTRACKED under `filters/`, and `deploy_filters.sh`'s `scorer_untracked_blocking()` runs in the every-4h `ExecStartPre` — the scorer would refuse to start. Found by the review battery. **`ground_truth_gate.json` still sits in the package and carries the same hazard** — pre-existing, not changed here.)*

## One-line answer

**Moving `uplifting v7` from 4.0 to 4.5 cuts FPR from 8.11% to 2.70% and recall
from 0.736 to 0.611 — 24 fewer false positives for 27 more false negatives.**
Under ADR-023 that trade is the right direction. **Nothing was changed; this is
the evidence, not the flip.**

> **Correction, 2026-08-10 (review battery).** The first version of this document
> argued the specificity gain was "real, not noise" because the #95 bands at 4.0
> and 4.5 are **disjoint**. That argument was **vacuous** and has been removed —
> see [4.0 vs 4.5](#40-vs-45-what-the-numbers-do-and-do-not-establish) below. It
> was the **third** misuse of the #95 band in one day, in the section directly
> above the one apologising for the second. The *numbers* are unchanged and were
> reproduced independently; only the argument for them was wrong.

## What was run, and why it is cheap now

`scripts/gate/ground_truth_gate.py` against the 660-row held-out oracle test
split, on **production's own predictions** — the committed
`datasets/parity/uplifting_v7_test660_gpuserver-serving-venv_2026-08-09.jsonl`,
calibrated with the deployed `calibration.json`. No re-scoring: the serving box
is only free between pipeline cycles and a 660-row run costs ~30 min of CPU there.
The conversion is `scripts/verification/parity_dump_to_gate_input.py` (new).

**Control, passed:** at threshold 4.0 this pipeline reproduces the committed
`ground_truth_gate.json` **exactly** — tp=159 fn=57 fp=36 tn=408, indeterminate
37/660. The sweep's 4.0 row is a known-answer test, which is the only reason the
other rows are worth reading.

## Three gaps in the gate, closed to make this measurable

The gate could not answer #102's question as it stood.

1. **Specificity had no band.** Every other metric carried a #95 uncertainty
   range; the one ADR-023 makes the objective was a bare point estimate. Added,
   and the overlap check now runs on **specificity first**, separately from F1 —
   two models can be indistinguishable on one and distinguishable on the other,
   and reporting only F1 hides both cases.
2. **The truth cut moved with the threshold.** Sweeping `--threshold` also moved
   what "on-lens" *means*, so the positive set changed underneath the sweep (216
   → 193 positives between 4.0 and 4.5) and recall at one threshold was not
   comparable to recall at another. New `--truth-threshold` pins the oracle cut.
   Default is unchanged: every prior run reproduces **numerically** (proven by
   running both versions of the script over the same inputs — all pre-existing
   report keys bit-identical), and the suite is at 273 passing. The *stdout* is
   not identical: two-model runs now emit the extra lines described below.
3. **The overlap check only ever said "OVERLAP".** It now also prints the
   non-overlapping case with both bands — worded to say exactly what it excludes
   (batch composition) and nothing more. It does **not** say the difference is
   real: a review measurement on 2026-08-10 compared one model against an 80-row
   subsample of *its own* predictions — a guaranteed zero effect — and got
   disjoint specificity bands in **71 of 300 seeds (23.7%)**. The check also now
   covers **recall** (ADR-023 makes it the floor) and warns when two models were
   evaluated on different populations.

   **Note this check played no part in #102's own conclusion**: the reproduce
   block below passes a single `--model` per threshold, so the pair loop is
   empty and neither line prints. The 4.0-vs-4.5 comparison was read off the
   sweep table by hand — and, as the next section explains, should not have been
   framed as a band test at all.

## The sweep

On-lens pinned at oracle ≥ 4.0 (216 positives of 660, 32.7%) at every row; only
the student's bar moves.

| student thr | tp | fn | fp | tn | recall | **specificity** | FPR | spec band (#95) | recall band | indet. |
|---|---|---|---|---|---|---|---|---|---|---|
| **4.00** (deployed) | 159 | 57 | 36 | 408 | 0.7361 | **0.9189** | **8.11%** | [0.901, 0.941] | [0.685, 0.773] | 37 |
| 4.25 | 144 | 72 | 24 | 420 | 0.6667 | 0.9459 | 5.41% | [0.932, 0.962] | [0.630, 0.713] | 31 |
| **4.50** | 132 | 84 | 12 | 432 | 0.6111 | **0.9730** | **2.70%** | [0.957, 0.982] | [0.583, 0.644] | 24 |
| 4.75 | 121 | 95 | 7 | 437 | 0.5602 | 0.9842 | 1.58% | [0.978, 0.989] | [0.519, 0.593] | 21 |
| 5.00 | 103 | 113 | 5 | 439 | 0.4769 | 0.9887 | 1.13% | [0.987, 0.993] | [0.417, 0.542] | 30 |

The point estimates match yesterday's hand-rolled sweep exactly. What is new is
that they now come out of the ADR-021 gate with bands attached, which is what
step 2 asked for.

## 4.0 vs 4.5: what the numbers do and do not establish

**The #95 band cannot adjudicate this comparison, and the first version of this
document wrongly used it to.** Here is why, because the reasoning generalises.

With the truth cut **pinned** and the predictions **fixed**, raising the student's
bar can only move articles from predicted-positive to predicted-negative. So
specificity is **monotone non-decreasing** in the threshold and recall
**monotone non-increasing** — by construction, for every possible batch
realisation. "The specificity went up when I raised the bar" is arithmetic, not a
finding, and a disjointness test on it answers a question nobody asked.

The instrument even contradicts itself on this data: **4.0 vs 4.25 bands
overlap** ([0.901, 0.941] vs [0.932, 0.962]), so by the rule the first draft
applied, a provably-signed improvement would read as "not distinguishable".

**What is actually established is the magnitude and the trade**, which need no
band at all:

| | 4.0 (deployed) | 4.5 |
|---|---|---|
| false positives | 36 | **12** |
| false negatives | 57 | **84** |
| FPR | 8.11% | **2.70%** |
| recall | 0.7361 | 0.6111 |

**24 fewer false positives for 27 more false negatives.** Under ADR-023 —
*"letting junk through is way worse than not catching positives"* — those are not
equal-weight units, and 4.5 puts uplifting's FPR between `solutions v6` (2.8%)
and `nature_recovery v4` (2.1%) instead of 3–4× above both.

**Both rates transfer to production, and that is the reason to trust them**:
recall and specificity are conditional on the true class, so the split's 32.7%
enrichment does not distort them. Precision, MAE and F1 on this split do not
transfer, which is why they are excluded from the argument. F1 in particular is
symmetric and this problem is not — it nets a real specificity gain against a
real recall loss and reports nothing.

**What the bands ARE good for here** is the honest uncertainty on each single
point estimate: at 4.0 specificity could sit anywhere in [0.901, 0.941] depending
on batch composition, and at 4.5 in [0.957, 0.982]. Quote those ranges, not the
third decimal.

## The cross-box question, and a correction I made and then had to withdraw

Running both boxes through the gate:

| student thr | prod spec | b650 spec | gap | prod #95 band width | bands |
|---|---|---|---|---|---|
| 4.00 | 0.9189 | 0.9189 | 0.0000 | 0.0405 | overlap |
| 4.25 | 0.9459 | 0.9459 | 0.0000 | 0.0293 | overlap |
| **4.50** | 0.9730 | 0.9662 | **0.0068** | **0.0248** | overlap |
| 4.75 | 0.9842 | 0.9865 | 0.0023 | 0.0113 | overlap |
| 5.00 | 0.9887 | 0.9910 | 0.0023 | 0.0068 | overlap |

**On the strength of that overlap I retracted the 2026-08-09 conclusion that
"b650 is not cleared at 4.5". The retraction was wrong and has been withdrawn.**

The #95 band answers *"how much could this metric move if batch composition
changed?"*. The parity runs hold batch composition **fixed** — same rows, same
order, same batch size — so batch noise is not the source of variation between
them and a band built from it cannot license "indistinguishable". Wrong
instrument, applied because it is the caveat this repo reaches for most.

A third run the same afternoon settled it: b650 rebuilt on production's exact
frozen stack and run on **CUDA** flips **the same three articles** at 4.5, same
direction, same 0.9662. A proximity control rules out "whatever is nearest the
cut" — of 18 production rows in [4.30, 4.50) only those 3 flip, while one at
4.4870, *closer* to the threshold, does not.
[`2026-08-10-b650-gpu-production-stack-parity.md`](2026-08-10-b650-gpu-production-stack-parity.md).

**Where that leaves #102: nowhere, and that is the point.** The box effect is
0.0068 specificity. The 4.0 → 4.5 gain is **0.054** — an order of magnitude
larger, and larger than the band. The box question governs *which machine may
produce a number*, never *what the number implies*. The sweep above is on
production's own predictions regardless.

*(Two revisions in one day on the same claim. Both are recorded rather than
quietly fixed, because the failure mode — grabbing a familiar caveat without
checking its premise holds — is the reusable part.)*

## The constraint that decides the option set

**`MAX_NORMALIZATION_RAW_MIN = 4.5` bounds the op-point from above.**

`tests/unit/test_normalization_invariant.py` requires `normalization.json`'s
`stats.raw_min` to equal the filter's tier threshold, and
`NexusMind/src/scoring/production_scorer.py:513` **rejects** a fit with
`raw_min > 4.5`, falling through to `score_scale_factor` with a log warning and
no other symptom. The boundary is strict-greater-than and documented as such
("a fit with raw_min exactly equal to 4.5 is accepted", NM#205).

`uplifting v7`'s committed fit is `raw_min: 4.0`, n=18,130, fitted 2026-07-31.

Therefore:

- **4.5 is reachable, and sits exactly ON the bound with zero margin.**
- **4.75 and 5.0 are NOT reachable** without raising the constant in *both*
  repos — attempting either silently disables normalization.
- **Any op-point move must refit `normalization.json` at the new anchor in the
  same change**, or the invariant test fails and production quietly loses
  percentile normalization.

That was not visible before this run and it removes two of the five sweep rows
from consideration.

## What 4.5 does to the production feed

**Correction to this document's first version, which said 4.5 "would remove
roughly two-thirds of uplifting's current surfacing volume". That was wrong** —
two-thirds is the **false-positive** reduction (36 → 12). Surfacing volume falls
about a quarter. The two were conflated.

Measured on the test split: predicted-positives **195 → 144, −26.2%**.

Estimated on the production feed from the 2026-08-09 oracle batch's band table
(the 4.5 cut lands exactly on a band boundary, so nothing is interpolated):

| | at 4.0 | at 4.5 |
|---|---|---|
| surfacing / 6 cycles | 1,193 (≈199 per cycle) | 870 (≈145 per cycle) |
| **off-lens reaching readers** | 302 (**25.3%**) | 164 (**18.8%**) |
| on-lens surfaced | 891 | 706 |

4.5 buys **46% fewer off-lens articles reaching readers** and costs **21% of the
on-lens articles that currently surface** — a 27% smaller feed. Under ADR-023's
asymmetry that is a good trade; whether a ~145-article feed is enough is a
product judgement, not a metrics one.

**Caveat inherited from the source:** the band table's precision figures are
computed on the *long* articles in each band — 26 of 170 sampled rows were never
graded because the oracle prefilter's 300-char floor rejected them, 11 of those
in the marginal band. 25.3% is more likely an underestimate than an over.

## Which true positives are lost

The 27 articles moving TP → FN between 4.0 and 4.5, by oracle score: median
**5.00**, range 4.20–6.25, **none above 6.5**. The loss comes entirely from the
weakest quarter of the positive set, not from the lens's best material.

**They are enriched in academic/preprint sources — 22.2% (6 of 27), against
12.2% of the other 189 oracle-positives and 7.9% of the whole split.** The six
are **arXiv ×3**, PubMed (the perioperative-probiotics trial), Frontiers
Pharmacology, and a genetic-engineering-news piece on mRNA in *mice*. *(An
earlier draft listed "arXiv ×2 … and a probiotics trial", double-counting the
PubMed row and undercounting arXiv; the total 6 was right, the breakdown was
not. "189 surviving positives" was also loose — 189 = 216 − 27 includes the 57
already missed at 4.0; only **132** survive as true positives at 4.5, where the
academic share is 10.6%, a smaller contrast than stated.)* Fisher two-sided
**p = 0.22**. That is the same class the
2026-08-10 adverse adjudication found to be the dominant off-lens failure — so
part of the measured "recall cost" is the oracle and the student sharing a blind
spot, exactly the effect CLAUDE.md warns about. **n=6: directionally consistent,
not established.**

Reading the other 21 titles — judgement, not measurement — many are also not the
community-scale stories the lens exists for: corporate/industrial (Olam Agri
plant, Bybit's fraud system, Azerbaijani gas, a bank's
protect-yourself-from-fraud notice), a headline roundup (*"Czech news in brief
for March 6"*), a Shakira concert. The genuinely on-lens losses are the ones to
weigh: young single women gaining ground in the Dutch housing market, gender
integration in Paralympic curling, a high-court ruling on VAT powers, a physician
on women's health literacy.

## Is there a cheaper, better-targeted fix than moving the threshold? No.

**Tested and refuted, 2026-08-10.** The 2026-08-09 adverse batch found that the
dominant off-lens class at the margin was **academic-abstract register** (9 of 21
candidates). The obvious cheaper fix is therefore a source/register rule rather
than a 27% cut to the feed. It does not work, and the direction is the opposite
of what was hypothesised.

On the held-out split at 4.0 — an **out-of-sample** test, since the hypothesis was
formed on production rows, not on this split:

| policy | tp | fn | fp | tn | recall | spec | FPR |
|---|---|---|---|---|---|---|---|
| **A. current, 4.0** | 159 | 57 | 36 | 408 | 0.736 | 0.919 | 8.1% |
| **B. move to 4.5** | 132 | 84 | **12** | 432 | 0.611 | 0.973 | **2.7%** |
| C. 4.0, drop academic/preprint sources | 138 | 78 | 34 | 410 | 0.639 | 0.923 | 7.7% |
| D. 4.0, academic sources need ≥ 4.5 | 153 | 63 | 34 | 410 | 0.708 | 0.923 | 7.7% |

**Only 2 of the 36 false positives are academic-register, while 21 of the 159
true positives are.** The rule destroys genuine positives to remove almost
nothing. Even the softest form (D) buys 2 false positives for 6 true ones — a
worse exchange rate than the threshold move.

**Why the adverse batch pointed the wrong way**: it sampled *production* rows
above the op-point; this is the *training-corpus* test split, where the oracle
scores academic content across the whole range (the 21 academic true positives
carry oracle scores 4.2–6.0). Source register does not separate on-lens from
off-lens — it separates one *population* from another. A population difference
read as a class difference.

## What the 36 false positives actually are

Heterogeneous, with no usable rule: an AI-for-governance aspiration piece
(predicted **6.63**, oracle 1.80), a drug-addiction statistic (5.50 / 1.00), a
prison-abuse testimony (4.85 / 1.80), disease-awareness features, a Google–Epic
settlement, a stranded sperm whale. Several are the **#91 "about vs contains"**
shape — harm stories carrying a positive fragment.

Two things worth carrying forward:

- **10 of the 36 have an oracle score ≥ 3.5**, i.e. the oracle nearly called them
  on-lens too. About a quarter of this filter's "false positives" are borderline
  oracle calls rather than clear model errors.
- **4.5 removes 8 of the 13 clearly-junk articles (oracle ≤ 2.0), 62%** — close
  to its 67% removal rate over all false positives. So the threshold move is
  **roughly neutral with respect to how bad a false positive is**: it does not
  preferentially catch the worst, and it does not preferentially spare them. Five
  clearly-junk articles survive at 4.5, including the 6.63/1.80 one.

**Consequence for #102**: the threshold move is the best available option, and it
is *partial*. The highest-scoring junk — predicted 5–6.6 against an oracle of
1.0–1.8 — is untouched by any op-point in this range, and is the same shape as
llm-distillery#91 (a child-trafficking investigation ranked 6th of 3,530). That
needs training-time work — the adverse probe suite grown today from 4 rows to 11 —
not an operating point.

## Not done

- **Nothing was deployed or changed.** No config edit, no refit.
- **The oracle labels for those 27 were not re-examined.** If the academic ones
  are mislabelled positives, 4.5's true recall cost is smaller than 0.611 implies.
- **No production A/B.** Everything here is retrospective scoring.

## Reproduce

```bash
PYTHONPATH=. python scripts/verification/parity_dump_to_gate_input.py \
    --dump datasets/parity/uplifting_v7_test660_gpuserver-serving-venv_2026-08-09.jsonl \
    --calibration filters/uplifting/v7/calibration.json --out /tmp/upl_prod.jsonl

# control first -- must print tp=159 fn=57 fp=36 tn=408
PYTHONPATH=. python scripts/gate/ground_truth_gate.py \
    --labels datasets/training/uplifting_v7/test.jsonl \
    --config filters/uplifting/v7/config.yaml --recompute-model-wa \
    --model v7=/tmp/upl_prod.jsonl --report /tmp/control.json

# then the sweep, with on-lens PINNED
for T in 4.0 4.25 4.5 4.75 5.0; do
  PYTHONPATH=. python scripts/gate/ground_truth_gate.py \
      --labels datasets/training/uplifting_v7/test.jsonl \
      --config filters/uplifting/v7/config.yaml --recompute-model-wa \
      --threshold $T --truth-threshold 4.0 \
      --model prod=/tmp/upl_prod.jsonl --report /tmp/sweep_$T.json
done
```

`datasets/training/uplifting_v7/test.jsonl` is gitignored and lives on b650 and
gpu-server (md5 `904ad059fe27157a297ac74c960adad3`); copy it from
`b650-gpu:~/llm-distillery/datasets/training/uplifting_v7/`.
