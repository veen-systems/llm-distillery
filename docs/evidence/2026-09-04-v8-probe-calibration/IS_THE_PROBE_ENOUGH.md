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
