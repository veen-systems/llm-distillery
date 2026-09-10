# Does widening the detector window 128 -> 512 buy anything? — No. Both detectors, five seeds.

**2026-09-10. €0 (local compute, b650-gpu).** Asked because the pre-scorer detectors
(obituary v3/v4/v5, violence_promotion v1, commerce_prefilter v2) run a frozen
`paraphrase-multilingual-mpnet-base-v2` — XLM-RoBERTa-base — configured at
`max_seq_length` **128** by the checkpoint's own `sentence_bert_config.json`, while the
architecture allows 512 (`max_position_embeddings` 514). Widening needs no encoder
training: re-embed, refit the head. So it was the cheapest confound to remove before
anyone argues about fine-tuning.

**Verdict: 512 is not the fix. Every comparison's seed bands overlap, and on
violence_promotion 512 is worse.** Keep 128.

---

## Design

Arms differ in **exactly one thing**: `SentenceTransformer.max_seq_length`. Same box, same
venv (`b650:~/llm-distillery/venv-prodparity`, ST 5.2.2 / sklearn 1.8.0 / torch 2.11.0+cu130),
same 5 seeds, same hyperparameters as the shipped trainers
(`MLPClassifier(hidden_layer_sizes=(256,128), max_iter=400, early_stopping=True,
n_iter_no_change=15)`, `StandardScaler`). So the ST-version skew that CLAUDE.md warns about
on *this exact detector* cancels between arms rather than contaminating them.

Judged on **recall + specificity at the operating point** (ADR-023), never MAE, and across
**5 seeds** so a difference is only claimed if the bands separate.

- **obituary** — train on `v5_train_seed.jsonl` (11,329 rows, 2,694 pos), evaluate on the
  held-out split (n=1,562, 344 pos, **22.0% positive rate**). This is the shipped protocol.
- **violence_promotion** — 5-fold stratified OOF over the 1,957 definitive-label rows
  (211 pos, **10.8% positive rate**). Also the shipped protocol.

## ✅ Two positive controls, both exact

| control | result |
|---|---|
| shipped v5 pickle re-scored @128 vs the recorded `v5_score` (n=1,562) | mean abs delta **4.1e-08**, max **1.7e-06**, **0/1562** verdict flips at 0.85 |
| violence_promotion @128, seed 42, OOF @0.95 | **recall 0.5498 / precision 0.9355** — reproduces `training_config.json` to 4 dp |

The harness is the shipped program, not a lookalike.

## Result — obituary (heldout n=1,562, 22.0% positive)

| threshold | window | recall (mean [min–max]) | specificity | precision |
|---|---|---|---|---|
| **0.85 (live op-point)** | 128 | 0.7721 [0.6599–0.8081] | 0.9870 [0.9819–0.9951] | 0.9452 |
| | 512 | 0.7959 [0.7384–0.8343] | 0.9806 [0.9704–0.9877] | 0.9219 |
| 0.90 | 128 | 0.7424 [0.6017–0.7994] | 0.9890 | 0.9520 |
| | 512 | 0.7773 [0.7122–0.8169] | 0.9834 | 0.9310 |
| 0.95 | 128 | 0.6924 [0.4942–0.7791] | 0.9916 | 0.9619 |
| | 512 | 0.7453 [0.6657–0.7994] | 0.9867 | 0.9428 |

512 gains **+0.0238 recall** and loses **−0.0064 specificity** at 0.85. On this split that is
~8 more obituaries caught against ~8 more clean articles blocked — a one-for-one trade, and
**the seed bands overlap at every threshold.** Not distinguishable.

## Result — violence_promotion (OOF n=1,957, 10.8% positive)

| threshold | window | recall (mean [min–max]) | specificity | precision |
|---|---|---|---|---|
| 0.90 | 128 | 0.6332 [0.6114–0.6635] | 0.9932 | 0.9189 |
| | 512 | 0.5801 [0.5213–0.6777] | 0.9947 | 0.9322 |
| **0.95 (config default)** | 128 | **0.5545** [0.5403–0.5782] | 0.9953 | 0.9350 |
| | 512 | **0.5090** [0.4360–0.6256] | 0.9963 | 0.9461 |

⭐ **512 LOSES 0.0455 recall** at 0.95 for +0.0010 specificity — and this is the corpus where
truncation at 128 is severe (95.0% truncated, median 21.7% of the article seen). The arm that
should have benefited most is the arm that got worse.

## ⭐ The two findings that matter more than the window

### 1. The seed band dwarfs the window effect

With corpus, hyperparameters and window all fixed, **obituary recall at 0.85 ranges 0.6599 to
0.8081 across five seeds** — a 0.148 spread, six times the 0.0238 the window buys. At 0.95 the
spread is 0.285. `early_stopping=True` makes `random_state` pick the validation split, so the
seed moves the model materially.

⛔ **The shipped v5 was trained at a single seed (42).** Its published heldout recall is one
draw from that distribution, not a property of the architecture. Any future detector
comparison that does not average over seeds is measuring the seed.

### 2. The two corpora have completely different truncation profiles

| corpus | median tokens | % over 128 | % over 512 | median share seen @128 |
|---|---|---|---|---|
| obituary heldout | **133** | 50.4% | 30.9% | **96.2%** |
| violence_promotion | **589** | 95.0% | 58.2% | **21.7%** |

⛔ **So "the detectors see ~21% of an article" is a fact about the violence_promotion corpus
and does NOT generalise.** The obituary corpus is mostly lede-length text; at 128 tokens the
median obituary row is already almost entirely visible. Correcting a claim made on 2026-09-09
from the violence corpus alone — a hand-built population, exactly the shape CLAUDE.md warns
about.

### Mechanism (consistent, not proven)

Mean pooling over 512 tokens dilutes a localised signal more than over 128. Three independent
observations line up with it: 512 hurts recall here; adding body text to a strong obituary
title lowered its score (2026-09-09); and on the e5 path truncated rows routed *more* often,
not less (2026-09-04). ⚠️ Consistency is not a causal test. None was run.

## Performance profile

**GPU, RTX 3090 Ti, batched — the primary production path** (`gpu_client` chunks to
gpu-server's `/obituary/predict`, which calls `predict_batch`):

| window | best throughput | ms/article | power | energy |
|---|---|---|---|---|
| 128 | **725 rows/s** (bs=128) | 1.38 | 426 W | 0.588 J/article |
| 512 | **190 rows/s** (bs=32) | 5.27 | 474 W | 2.501 J/article |

**3.82x slower, 4.25x more energy.**

**CPU, b650 Ryzen — the fallback path.** ⚠️ CPU power was NOT measured; the wattage column in
that run is GPU idle draw and must not be read as CPU cost.

| window | best throughput | ms/article |
|---|---|---|
| 128 | 37.8 rows/s (bs=8) | 26.4 |
| 512 | 10.3 rows/s (bs=1) | 97.2 |

**3.68x slower.**

Single-article latency — the **local** fallback in `NexusMind/src/preprocessing/obituary.py`
loops `is_obituary(article)` one row at a time, so it pays this, not the batched rate:

| device | window | p50 | p95 | max |
|---|---|---|---|---|
| GPU | 128 | 4.95 ms | 7.32 ms | 11.55 ms |
| GPU | 512 | 9.51 ms | 12.23 ms | 15.65 ms |
| CPU | 128 | 35.00 ms | 47.47 ms | 99.00 ms |
| CPU | 512 | 117.28 ms | 128.63 ms | 163.10 ms |

Wall-clock at volume (best batch):

| articles | GPU 128 | GPU 512 | CPU 128 | CPU 512 |
|---|---|---|---|---|
| 1,000 | 1.4 s | 5.3 s | 26.4 s | 97.2 s |
| 8,283 | 11.4 s | 43.7 s | 218.9 s | 805.0 s |
| 10,000 | 13.8 s | 52.7 s | 264.2 s | 971.9 s |
| 100,000 | 137.9 s | 527.1 s | 2,642 s | 9,719 s |

⚠️ **8,283 is a WINDOW, not a rate** — it is the production population measured 2026-08-02
(NM#285) and is quoted here only as one anchored batch size. Do not read it as articles/cycle.

**Money cost is not the constraint.** Per 10,000 articles the GPU arm uses 1.63 Wh at 128 vs
6.95 Wh at 512 — a delta of 5.31 Wh, about €0.0016 at an *assumed* €0.30/kWh. The real cost is
wall-clock and GPU occupancy inside a pipeline cycle: trivial on the batched GPU path
(11 s -> 44 s on the 8,283 anchor), material on the CPU fallback (3.6 min -> 13.4 min).

## What this closes and what it does not

✅ **Closed:** the window is not the bottleneck, for either detector, at any threshold tested.
Do not widen it. Any future encoder/fine-tuning comparison can use 128 as the baseline without
the "crippled baseline" objection.

⛔ **NOT tested:** chunk-and-aggregate (embed the whole article in 128-token windows, pool the
chunk vectors). That is a different mechanism from widening the window and the January research
measured it favourably on this exact backbone — but on a 6-dimension REGRESSION task, by MAE,
which ADR-023 says not to rank on. It remains open.

⛔ **NOT tested:** fine-tuning the encoder end-to-end, and head+tail truncation.

⛔ **Not established:** the pooling-dilution mechanism above. Three observations are consistent
with it; no causal test was run.

## Reproduce

```bash
scp scripts/window_experiment.py scripts/profile_window.py b650-gpu:~/
ssh b650-gpu 'cd ~/llm-distillery && ./venv-prodparity/bin/python ~/window_experiment.py'
ssh b650-gpu '~/llm-distillery/venv-prodparity/bin/python ~/profile_window.py cuda'
ssh b650-gpu '~/llm-distillery/venv-prodparity/bin/python ~/profile_window.py cpu'
```

Needs the obituary corpora staged on b650 (`filters/common/obituary_detector/training/data/`,
131 MB, gitignored). `window_experiment.py` caches embeddings in `~/window_emb_cache/`; delete
it to re-embed. Raw logs and result JSONs are in this directory.
