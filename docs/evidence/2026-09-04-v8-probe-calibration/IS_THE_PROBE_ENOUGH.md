# Could the e5 probe just do the job on its own?

> ⛔⛔ **UPDATED 2026-09-04 with EXP-018, which REFUTED MY REASONING BELOW.** I claimed the
> probe/student gap was a *kind-of-signal* limit — that sentence embeddings encode topic and
> the class-A judgement is about scope, so more encoder capacity would not help. **It helps.**
> `multilingual-e5-large` closes **70%** of the gap on the disputed rows (0.7517 → **0.8169**
> against the student's 0.8454) and is **not distinguishable** from the student there by the
> resolution I pre-registered. See §**EXP-018** at the foot of this file.
> ⭐ The operational answer is unchanged — keep the student — but **for cost reasons, not the
> accuracy reasons argued below.** Read this file knowing its central claim did not survive.

**2026-09-04. $0** — the student's scores were already on disk; the probe's took one CPU pass
over the same 660 held-out rows. Reproduce with `scripts/analysis/dump_probe_scores.py`,
then the comparison at the foot of this file.

**Answer: no — and the place it falls down is exactly the distinction `human_thriving v8`
exists to make.** But the probe is better than "not enough" implies, and the reason it comes
up is worth recording: its score is normally **invisible**, because Stage 1 only decides
route-or-not and the number is discarded for every row it forwards. Nothing the pipeline
keeps can answer this, which is why the question keeps returning.

## Whole test split (n=660, 35 positives, 5.30%)

| arm | AUC | average precision |
|---|---|---|
| **probe (e5-small alone)** | **0.8710** | **0.3779** |
| student, raw | 0.9474 | 0.5474 |
| student, calibrated | 0.9488 | 0.5648 |

The probe is genuinely competent — 0.87 AUC from a 384-dim multilingual embedding and a small
MLP is respectable. But **average precision goes 0.378 → 0.565, a 50% relative gain**, and AP
is the metric that tracks what a reader sees at the top of a ranking.

## At matched surfacing volume — the practical version

Flag the k highest-scoring rows in each arm, so all three surface the same amount:

| k | probe alone | student raw | student calibrated |
|---|---|---|---|
| 17 | 0.257 | 0.286 | 0.343 |
| 26 | 0.286 | 0.486 | 0.457 |
| 35 | 0.314 | 0.571 | 0.543 |
| 50 | 0.429 | 0.686 | 0.657 |

**At k=35 the probe finds 11 of the 35 positives where the student finds 20.** Same volume,
roughly half the good content. To match the student's haul you would have to surface far more
— which is the junk a reader then sees.

## ⛔ The decisive test: the rows v7 and v8 disagree about

The 117 test rows `uplifting v7` surfaced, split by the v8 oracle into **30 v8-good** and
**87 v8-junk**. Can each arm tell "v7 was right" from "v7 was wrong"? This is the #107 /
class-A judgement — harm-answered-only and institution-beneficiary content — and it is the
entire reason v8 exists.

| arm | AUC on the disputed rows |
|---|---|
| v7 itself (baseline) | 0.7218 |
| **probe alone** | **0.7517** |
| student, raw | 0.8454 |
| student, calibrated | 0.8521 |

⭐ **The e5-SMALL probe barely improves on the filter it would be replacing: 0.7517 against
v7's 0.7218.** It recovers about a quarter of the gap the student closes.

⛔ **The explanation I gave here was wrong and EXP-018 killed it.** I wrote that the probe is
a *topical* instrument and the class-A distinction is a *scope* judgement that sentence
embeddings do not carry — i.e. a kind-of-signal limit that capacity could not fix. **e5-large
reaches 0.8169 on these same rows**, closing 70% of the gap and landing inside the noise of
the student's 0.8454. It was substantially a **capacity** limit. See EXP-018 below.

## So what IS the probe for, and is it doing it?

Its job is a **recall-safe screen**, not a ranker: route everything that might qualify to
Stage 2, cheaply, and drop only what certainly does not. On that job it succeeds — **0 false
negatives at the adopted 1.75 threshold on both splits**, routing ~89% onward, at ~1.3 ms
against the student's ~19 ms.

⚠️ **And the comparison above is mildly unfair to it, deliberately noted.** The probe was
trained with `--objective recall` — class-weighted BCE on a binary MEDIUM+ target — so it was
optimised *not to miss*, not to order well. AUC and AP judge ordering. A regression-objective
probe might rank better; ADR-011 and the v8 plan say it would also floor-collapse on a 4.7%-
positive corpus and start dropping needles, which is the worse failure for a screen.

## Caveats

⚠️ **35 positives.** The matched-volume gaps are 9 articles at k=35 and 7 at k=26 — real, and
small. The disputed-row comparison rests on 30 v8-good against 87 v8-junk.

⚠️ Both arms were trained on the **same labels and the same corpus**, so the comparison is
fair on that axis; neither has seen this split.

⚠️ ~~This says nothing about whether a *bigger* embedding model would close the gap.~~
**ANSWERED by EXP-018 below: it closes most of it.** `multilingual-e5-small` is what is
deployed; `e5-large` reaches 0.9016 whole-split and 0.8169 on the disputed rows, and is ruled
out on **cost** (11.1× the encode time), not on accuracy.

## Reproduce

```
PYTHONPATH=. python scripts/analysis/dump_probe_scores.py \
    --filter filters/human_thriving/v8 \
    --split-file datasets/training/human_thriving_v8/test.jsonl \
    --out <dump-dir>/probe_scores.jsonl --device cpu
```

then compare against `scores_raw.jsonl` / `scores_calibrated.jsonl` from
`dump_student_scores.py`. ⚠️ The per-row dumps are not committed — they carry ids for corpus
rows whose text is gitignored (#97); they live at `b650-gpu:~/llm-distillery/ht_v8_test_dump/`.


---

# EXP-018 — does a bigger encoder close the gap? (2026-09-04)

**$0, CPU only.** One variable: same corpus, same splits, same `--objective recall`, same
`--seed 42`, same device; only `--embedding-model` changed to
`intfloat/multilingual-e5-large` (1024-dim, ~4.7× the parameters, 2.2 GB).
Prediction registered as **H-V8-16 before the run**.

## Result

| arm | whole-split AUC | AP | **AUC on the 117 disputed rows** |
|---|---|---|---|
| v7 itself (baseline) | — | — | 0.7218 |
| probe, **e5-small** | 0.8710 | 0.3779 | **0.7517** |
| probe, **e5-large** | **0.9016** | **0.4972** | **0.8169** |
| student, raw | 0.9474 | 0.5474 | 0.8454 |
| student, calibrated | 0.9488 | 0.5648 | **0.8521** |

Recall at matched flag count: e5-large closes much of the gap in the middle of the range
(k=35: 0.486 vs e5-small's 0.314 and the student's 0.571) and none of it at the top
(k=17: 0.257, identical to e5-small).

## ⛔ Scoring the prediction honestly

| what I registered | outcome |
|---|---|
| whole-split AUC "~0.89–0.91" | **0.9016 — correct**, inside the band |
| disputed rows "at most ~0.80" | **0.8169 — EXCEEDED. Wrong.** |
| falsifier: "≥0.83 means my reasoning is wrong" | 0.8169, **not reached** |
| my own caveat: "a difference under ~0.05 is not resolvable here" | **e5-large vs student = 0.0285 — NOT RESOLVABLE** |

**It landed between my point estimate and my falsifier.** By the pre-registered criterion my
reasoning was not falsified; by my own point prediction it was wrong. ⛔ **I am not going to
claim the prediction held.** The substantive claim — *capacity will not help, because this is
the wrong kind of signal* — is **substantially wrong**: capacity closes **0.0652 of the
0.0937** gap, about **70%**.

⭐ **And by my own pre-registered resolution, e5-large and the student are NOT
DISTINGUISHABLE on the disputed rows.** That is the sentence that matters, and it is the one
I would have least liked to write.

## So why keep the student anyway — and note the reason changed

**Cost. Measured, same machine, same 5,926 articles, CPU:**

| encoder | encode time | ratio |
|---|---|---|
| e5-small | **4:14** | 1× |
| e5-large | **47:13** | **11.1×** |

That is fatal in **both** roles e5-large could occupy:

- **As a Stage-1 screen** it is disqualified by construction. The screen exists to be cheap:
  ~1.3 ms/article against the student's ~19 ms. At 11× it becomes ~14 ms — the screen would
  cost nearly as much as the thing it exists to avoid, while still routing ~89% onward.
- **As a replacement for the student** it is ~27% cheaper for AUC 0.9016 against 0.9474 and
  AP 0.4972 against 0.5648. Not a trade worth making.

⭐ **Right answer, wrong reasoning.** "Keep the student" survives; the argument I gave for it
did not. The gap was substantially capacity, and what rules e5-large out is the bill.

⚠️ **CPU only.** The 11.1× is a CPU measurement; the GPU ratio is unmeasured, and gpu-server
is where production serves. If the GPU ratio were much smaller the cost argument would weaken
— that is the experiment that would reopen this.

⚠️ 35 positives whole-split, 30 v8-good vs 87 v8-junk on the disputed rows. Every difference
here under ~0.05 AUC is inside the noise I named before running.

⚠️ e5-large selected a **different threshold** (2.350, val stage-2 rate 0.480) against
e5-small's 2.825/0.591, and reached a better val BCE (0.8953 vs 0.9611). Neither was adopted;
the shipped probe is unchanged.

---

# EXP-019 — the fair test: a probe trained AS A SCORER (2026-09-04)

**Raised by the owner, and the framing was the correction.** Everything above compares
probes trained as **screens** (`--objective recall`) — an objective that optimises the
weighted average as a binary MEDIUM+ classifier through class-weighted BCE, and supervises
the six dimensions only through an auxiliary L1 weighted **0.1**. Judging that on AUC and
concluding the student is necessary is close to a strawman. *"Vectorizer + MLP head"*, as
people actually propose it, means a probe trained to **regress the dimensions**.

**$0. GPU.** One variable: same corpus, splits, `--seed 42`; `--objective regression`.

## Result

| arm | AUC | AP | disputed rows | ΔAUC vs student, paired bootstrap |
|---|---|---|---|---|
| probe recall, e5-small | 0.8710 | 0.3779 | 0.7517 | +0.0778 [+0.0281, +0.1416] |
| probe recall, e5-large | 0.9016 | 0.4972 | 0.8169 | +0.0480 [+0.0064, +0.0962] |
| **probe REGRESSION, e5-small** | **0.9035** | 0.4055 | 0.7851 | **+0.0452 [+0.0113, +0.0883]** |
| **probe REGRESSION, e5-large** | 0.9021 | **0.5209** | 0.7962 | +0.0468 [+0.0091, +0.0860] |
| student, calibrated | **0.9488** | **0.5648** | **0.8521** | — |

**The objective mattered more than the encoder.** Regression lifts e5-**small** from 0.8710
to **0.9035** — past e5-large's recall-trained 0.9016, at **1/7th the compute**. And with the
regression objective, e5-large buys **nothing** on AUC (0.9021 vs 0.9035); only AP improves.

⭐ **It also fixes the inflation**, which is what the objective was always going to do:

| | recall e5-small | regression e5-small | regression e5-large | student |
|---|---|---|---|---|
| per-dimension MAE | 2.073 | **0.762** | **0.692** | 0.614 |
| per-dimension bias | **+1.699** | −0.298 | −0.168 | ~0 |

## The verdict, against a decision rule fixed before the run

**H-V8-17 stated: replacing the student requires the paired bootstrap CI on ΔAUC to INCLUDE
ZERO — not merely a small point difference.** In all four probe configurations the CI
**excludes** zero. By the pre-registered rule, **the student is not replaceable on this
evidence.**

⚠️ **But the owner's scepticism was substantially justified, and the honest framing is a
trade rather than a refutation.** What the student buys, at every surfacing volume:

| rows flagged | probe finds | student finds | **lost** |
|---|---|---|---|
| 17 | 6 | 12 | **6** |
| 26 | 12 | 16 | 4 |
| 35 | 13 | 19 | **6** |
| 50 | 17 | 23 | **6** |
| 80 | 23 | 29 | **6** |

**~6 of 35 positives — a consistent 17% of the positive set — for 11.7× the compute**
(GPU: probe 3.74 ms/article, student 43.7 ms). Whether that trade is worth making is an
editorial decision, not a statistical one. The statistics only say the difference is real.

## ⛔ A documented prediction that did NOT hold

`train_probe.py` emits, and ADR-011 asserts: *"Only 4.7% MEDIUM+ positives — this looks like
a needle filter. Regression will likely collapse to a floor predictor and drop positives."*
**It did not collapse.** The regression probe beat the recall probe on AUC by 3.25 points.

⚠️ **This does not refute ADR-011, and the distinction matters.** ADR-011's claim is about
using regression **as a screen**, where floor-collapse means unrecoverable false negatives at
Stage 1. This experiment used it **as a scorer** and never picked a screening threshold. Both
can be true: good at ordering, bad at not-missing. **Testing the screen claim needs an
FN@MEDIUM+ measurement at a selected threshold, which was not done here.**

## Prediction scoring

I predicted regression would beat recall on AUC and AP and still fall short of the student,
and said in advance I would not treat a small shortfall as vindication. **Both halves held**
— unlike EXP-018 the same evening, where my mechanism claim was substantially wrong. ⚠️ The
shortfall is 0.045 AUC and it is resolved, so "falls short" is the correct verb; "the student
is clearly necessary" is not.

## GPU timing, same machine, same 660 articles, model load excluded

| | ms/article |
|---|---|
| e5-small, GPU | **3.74** |
| e5-large, GPU | 26.79 |
| student, GPU | 43.70 |
| e5-small, CPU | 47.2 |
| e5-large, CPU | 511.2 |

⚠️ **This corrects an earlier observation in this file.** I noted that the student on GPU
(43.7 ms) beat the probe on CPU (47.2 ms) and concluded the two-stage design saved nothing.
That was an artefact of running the probe on the wrong device. On GPU the probe is **11.7×**
cheaper than the student.

⚠️ **But the screen still barely earns its keep at the adopted threshold**, for a different
reason: routing is ~89%, so two-stage costs 3.74 + 0.89 × 43.7 ≈ **42.6 ms** against 43.7 ms
for student-on-everything — a **2.5%** saving. At the probe's own selected 2.825 (routing
~52%) it would be ~26.5 ms, a 39% saving. **The hold-near-pass-through ruling is what makes
the screen nearly free of benefit** — a cost the ruling knowingly accepted, since no Stage-2
cost constraint was claimed.

⚠️ b650-gpu, not gpu-server. Ratios should travel; absolute numbers may not.
