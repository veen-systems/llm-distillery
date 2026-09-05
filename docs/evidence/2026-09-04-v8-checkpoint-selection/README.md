# human_thriving v8 — the two checkpoint-selection arms, head to head

**2026-09-04. EXP-015. No spend. No oracle calls — labels were already on disk.**

Two checkpoints from the same corpus, same seed, same hyperparameters, differing
**only** in the metric that chose which epoch to keep. Produced while fixing
`training/train.py`, where `--select-metric` was accepted and inert (commit
`1878e7b`).

⛔ **The weights are NOT in this repo.** `adapter_model.safetensors` is gitignored as a
large model checkpoint (`.gitignore` § *Model checkpoints (large files)*; ⚠️ **not** #97, which is the TDM assessment —
corrected 2026-09-05). Both arms live on `b650-gpu`:

| arm | selected on | epoch | path on b650 |
|---|---|---|---|
| shipped | `recall_medium` @4.5 | **4** | `~/llm-distillery/filters/human_thriving/v8/model/` |
| baseline | aggregate MAE | 6 | `~/llm-distillery/filters/human_thriving/v8/model_baseline_mae/` |

Per-epoch numbers are committed as `filters/human_thriving/v8/training_history.json`
(shipped arm) and `training_history_baseline_mae.json` (baseline arm).

## Verdict: NOT DISTINGUISHABLE

⚠️ **Uncalibrated.** No `calibration.json` exists yet — Phase C is incomplete, so
these are raw student outputs and are **not** comparable to the deployed fleet's
post-calibration figures in `memory/filter-status.md`.

Test split (n=660, 35 positives at 4.5), untouched by selection:

| @4.5 | epoch 4 (shipped) | epoch 6 (baseline) |
|---|---|---|
| recall | 0.514 | 0.457 |
| specificity | 0.9856 | 0.9824 |
| precision | 0.667 | 0.593 |
| TP / FP / FN | 18 / 9 / 17 | 16 / 11 / 19 |

Epoch 4 leads on all three — **by two articles each**, which is not a difference
this project treats as real:

- At **4.25 epoch 6 leads on both** (recall 0.500 vs 0.463, specificity 0.9818 vs
  0.9802), and at 4.0 they split. A model that changes rank under a 0.25 move in
  the threshold is not distinguishable from its rival.
- Epoch 6 ranks better on test NDCG@10 (0.849 vs 0.801).
- **Seed 42 is not bit-reproducible on this box.** Epoch 6's val MAE was
  `0.5601` in the baseline run and `0.5605` in the re-run — identical code, data
  and seed — so some of the gap is run variance, not the checkpoint choice. Same
  family as the #95 noise floor.

Epoch 4 is kept because a criterion the project endorses chose it, **not** because
it measured better.

## Why the selection metric could not settle it

`recall_medium` **saturates**: 0.5806 at epochs 4, 5 and 6 — identical. Selection
uses a strict `>`, so the earliest of the tied epochs won. The tie-break did the
choosing, not the metric (llm-distillery#144).

Its resolution is `1 / n_positives`, and val has **31** positives at 4.5, so the
metric can only move in steps of 3.2%. The per-epoch sequence is non-monotone —
0.000, 0.258, 0.065, then flat — which is a step-function threshold metric on a
thin positive count, not a model improving and regressing.

## Reproducing

```bash
# on b650-gpu, from ~/llm-distillery
export PYTHONPATH=. HF_HUB_OFFLINE=1
MODEL_DIR=model              venv-prodparity/bin/python eval_checkpoint.py
MODEL_DIR=model_baseline_mae venv-prodparity/bin/python eval_checkpoint.py
```

`eval_checkpoint.py` deliberately imports `FilterDataset` and `evaluate` from
`training/train.py` rather than reimplementing them, so it measures what training
measured. **Control that this worked**: it reproduces `train.py`'s own reported val
MAE to four decimals for both arms (0.5814 / 0.5601), and its val `@4.5` recall for
epoch 4 is 18/31 = 0.581, matching `training_history.json`'s `recall_medium` for
that epoch exactly. Two independent computations of the same quantity agree.

Raw output: `head_to_head_raw.txt`.

## What this does NOT establish

- Nothing about calibrated performance, the Stage-1 probe, or the deploy gate.
- Nothing about whether epoch 4 or 6 is better — see the verdict.
- The `@4.0` and `@4.25` rows are diagnostic only. **v8's op-point is 4.5**
  (`config.yaml scoring.tiers.medium.threshold`); it has no `base_scorer.py` yet,
  so the runtime source that CLAUDE.md calls authoritative does not exist for this
  filter and 4.5 is currently a documentation value.
