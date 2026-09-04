# Could the e5 probe just do the job on its own?

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

⭐ **The probe barely improves on the filter it would be replacing: 0.7517 against v7's
0.7218.** It recovers about a quarter of the gap the student closes. That is the finding —
the probe is a *topical* instrument, and the class-A distinction is a *scope* judgement about
who benefits and whether a harm was merely answered. Sentence embeddings mostly do not carry
it; a fine-tuned model trained on labels that encode it does.

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

⚠️ This says nothing about whether a *bigger* embedding model would close the gap.
`multilingual-e5-small` is what is deployed; `e5-large` is cached on b650 and untested here.

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
