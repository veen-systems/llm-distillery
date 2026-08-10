# #102 step 2 — `uplifting v7` operating point, through the ADR-021 gate

**Measured 2026-08-10. Machine-readable: `filters/uplifting/v7/threshold_sweep.json`.**

## One-line answer

**Moving `uplifting v7` from 4.0 to 4.5 is a real specificity gain, not noise** —
FPR 8.11% → 2.70%, and the two specificity bands are **disjoint**. It costs a
real amount of recall (0.736 → 0.611, also disjoint). Under ADR-023 that trade is
the right direction. **Nothing was changed; this is the evidence, not the flip.**

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
   Default is unchanged, so every prior run and all 270 unit tests reproduce.
3. **The overlap check only ever said "OVERLAP".** It now also prints DISJOINT
   with the two bands, so "we checked and the difference is real" is a visible
   result rather than the absence of a warning.

## The sweep

On-lens pinned at oracle ≥ 4.0 (216 positives of 660, 32.7%) at every row; only
the student's bar moves.

| student thr | tp | fn | fp | tn | recall | **specificity** | FPR | spec band (#95) | recall band | indet. |
|---|---|---|---|---|---|---|---|---|---|---|
| **4.00** (deployed) | 159 | 57 | 36 | 408 | 0.7361 | **0.9189** | **8.11%** | [0.901, 0.941] | [0.685, 0.773] | 37 |
| 4.25 | 144 | 72 | 24 | 420 | 0.6667 | 0.9459 | 5.41% | [0.932, 0.962] | [0.630, 0.713] | 31 |
| **4.50** | 132 | 84 | 12 | 432 | 0.6111 | **0.9730** | **2.70%** | [0.957, 0.982] | [0.583, 0.644] | 24 |
| 4.75 | 121 | 95 | 7 | 437 | 0.5602 | 0.9842 | 1.58% | [0.977, 0.989] | [0.519, 0.593] | 21 |
| 5.00 | 103 | 113 | 5 | 439 | 0.4769 | 0.9887 | 1.13% | [0.986, 0.993] | [0.417, 0.542] | 30 |

The point estimates match yesterday's hand-rolled sweep exactly. What is new is
that they now come out of the ADR-021 gate with bands attached, which is what
step 2 asked for.

## 4.0 vs 4.5 under the #95 band rule

| metric | band at 4.0 | band at 4.5 | verdict |
|---|---|---|---|
| **specificity** | [0.9009, 0.9414] | [0.9572, 0.9820] | **DISJOINT — real** |
| **recall** | [0.6852, 0.7731] | [0.5833, 0.6435] | **DISJOINT — real** |
| F1 | [0.7255, 0.8166] | [0.6981, 0.7658] | OVERLAP — not distinguishable |

**The F1 overlap is the expected result, not a contradiction.** F1 is symmetric
and this is an asymmetric problem: it nets a real specificity gain against a real
recall loss and reports nothing. That is precisely what ADR-023 says not to
optimise. Read specificity and recall; do not read F1 here.

**The trade: 24 fewer false positives for 27 more false negatives.** Under
ADR-023 — *"letting junk through is way worse than not catching positives"* —
those are not equal-weight units, and 4.5 puts uplifting's FPR (2.70%) between
`solutions v6` (2.8%) and `nature_recovery v4` (2.1%) instead of 3–4× above both.

**Both numbers transfer to production, and this is the reason to trust them at
all**: recall and specificity are conditional on the true class, so the split's
32.7% enrichment does not distort them. Precision, MAE and F1 on this split do
not transfer, which is why they are excluded from the argument.

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
12.2% of the 189 surviving positives and 7.9% of the whole split.** The six are
arXiv (×2), PubMed, Frontiers Pharmacology, a probiotics trial, and a
genetic-engineering-news piece on mRNA in *mice*. That is the same class the
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
