# human_thriving v8 — the RETRAIN, and its deploy gate (2026-09-06)

**Owner ruling, verbatim: *"no exception, i want this system to be harmonized"*.**

## Why the model was retrained

The v8 adapter shipped until today was built by the tree that became `1878e7b` via
`git commit --amend`. The sha that actually produced it — `0697f5a` — is reachable from
no branch and would not survive `git gc`. Nothing caught it, because
`training_metadata.json` recorded **no commit at all**: the run's provenance lived in a
session note, and a session note cannot be checked.

⭐ **Confirmed independently while preparing the retrain, and it is worse than "unrecorded":**
`b650-gpu:~/llm-distillery` was a partial rsync rather than a checkout, and its
`training/train.py` was the **pre-fix version, missing the 176 lines of checkpoint-selection
machinery** that `main` says trained the shipped artifact. The box did not hold the code the
record named.

The option to record an exception was put to the owner and **rejected**.

## What changed, mechanically

| | before | after |
|---|---|---|
| `training_metadata.json` | no commit field | `git_commit`, `git_dirty`, `git_branches_at_train_time`, `git_provenance` |
| `train.py` on a non-checkout / dirty tree / commit on no branch | trained anyway | **refuses**, before the ~100-minute run; `--allow-missing-git-provenance` is the explicit opt-out and is itself recorded |
| later drift (amend, rebase, gc) | invisible | `scripts/verification/check_training_provenance.py` re-checks **reachability**, which only *now* can measure |
| `b650:~/llm-distillery` | partial rsync, 12 files drifted | real git checkout, 0 tracked-file drift |

⚠️ **This buys traceability, NOT bit-reproducibility.** The training run is not deterministic
at this seed — EXP-015 recorded 0.5601 vs 0.5605 on a same-seed rerun, and epoch 1 here came
in at MAE 0.7728 against the original 0.7773. Re-running `64b469d` yields a near-identical but
different model. What is removed is *"nobody can say what built this"*, not *"anyone can
rebuild it exactly"*.

## The retrained checkpoint

- **Trained under `64b469d935bc34a87c176b8ee2ad86cbafd5bdde` on `main`**, `git_dirty=false`.
- **Epoch 5 of 6**, selected on `recall_medium` @4.5 (val **0.613** = 19/31).
  ⛔ **Not epoch 4**, which is what the first build shipped. In EXP-015 `recall_medium`
  **saturated** at 0.5806 across epochs 4/5/6, so the strict `>` tie-break kept the earliest
  (llm-distillery#144). This run did **not** saturate, so selection chose outright — the
  shipped checkpoint therefore differs from its predecessor by more than run-to-run noise.
- Adapter `074209ff572c4823206569b3c7d89c26b15029263748cf510c9c5b8ce347de08`.
  The superseded epoch-4 adapter (`363fc63d…`) is preserved at
  `b650-gpu:~/llm-distillery/filters/human_thriving/v8/model_exp015_epoch4_prehatch/`.
- Same data, seed, hyperparameters and selection metric as EXP-015 — deliberately, so this is
  a **pure provenance fix** and not a fix bundled with a behaviour change.

Per-epoch: 0.000 → 0.226 → (no new best) → 0.516 → **0.613** → (no new best).

## The gate

Held-out oracle labels, 660 rows, 35 positives (5.30% unweighted), op-point **4.50 calibrated**,
everything on **CUDA**.

| arm | recall | precision | specificity | F1 | surfaced | TP | FP |
|---|---|---|---|---|---|---|---|
| **calibrated** (ships) | 0.314 | 0.550 | 0.9856 | 0.400 | 20 | 11 | 9 |
| raw | 0.486 | 0.586 | 0.981 | 0.531 | 29 | 17 | 12 |

### ⛔ Against the superseded checkpoint: NOT DISTINGUISHABLE

| | epoch 5 (ships) | epoch 4 (superseded) |
|---|---|---|
| recall | 0.314 `[0.286, 0.400]` | 0.343 `[0.314, 0.429]` |
| precision | 0.550 `[0.500, 0.737]` | 0.706 `[0.579, 0.833]` |
| specificity | 0.9856 `[0.984, 0.992]` | 0.9920 `[0.9872, 0.9952]` |
| surfaced / FP | 20 / 9 | 17 / 5 |

**All four #95 bands overlap.** The owner's 2026-08-06 rule: two models whose bands overlap are
not distinguishable whatever their point estimates say. ⛔ **Do not report this as a
regression** — and equally, the consistently adverse direction is not nothing, it is a
direction without an effect behind it.

### ⭐ The precision drop is mostly boundary disagreement, not junk

Every false positive classified by the **oracle's own `scope_verdict`** — a field present on
all 6,586 labelled rows, so this is a measurement and not an interpretation:

| | epoch 5 | epoch 4 |
|---|---|---|
| `in_scope` (oracle calls it a thriving story, scored just under 4.5) | **6** | 3 |
| `out_of_scope` | 1 | 1 |
| `response_to_harm` | 1 | 0 |
| **`harm_is_subject`** (the category error that damages trust) | **1** | **1** |
| plain precision | 0.550 | 0.706 |
| **off-lens precision** (excluding `in_scope`) | **0.850** | 0.882 |

The apparent collapse from 0.706 to 0.550 is mostly the new model surfacing more articles the
oracle scores *just below* the bar. On the reader-facing measure the two are close, with the
**same single category error each**.

⚠️ **Counts of 17 and 20 surfaced articles.** *"1 versus 1"* compares two single articles, not
two rates. `scope_verdict` is an oracle label, not truth. And the 660 rows are a **25.1×
design-weighted** draw, so no figure here is a production rate — production precision has to be
measured from live output after deploy.

## Provenance

| | |
|---|---|
| Training commit | `64b469d` on `main`, `git_dirty=false` |
| Code commit for calibration / dump / gate | `0d7115a` — differs from the training commit only by the `fit_calibration.py` device print and the `filter_completeness` rewrite, neither on the inference path |
| Box | b650-gpu (`jwasys-B650-EAGLE-AX`), RTX 3090 Ti 24 GB, driver 580.95.05 |
| venv | `venv-prodparity` — py 3.11.15, torch 2.11.0+cu130, transformers 5.0.0, peft 0.18.1 |
| Device | **CUDA throughout** — calibration fit, score dump and gate. Read back off `next(model.parameters()).device`: `declared=cuda parameters=cuda:0` in both logs (#146) |
| Split | `datasets/training/human_thriving_v8/test.jsonl`, sha256 `e361b5175c66252582c395bf256eb253bfa9b35f780f2479907231fc4d58d726` |
| Calibration | `calibration.json` sha256 `7665f526e77824df4c9c3dca428e3073931a3d642c489e43566ef6597c61f7c0` — **refitted** on this checkpoint; the previous file described the epoch-4 weights |

### Dumps (gitignored; `b650-gpu:~/llm-distillery/ht_v8_test_dump_cuda_retrain/`)

```
4bc1a7250446212dc2b02f830b2c567f4489c765239b0165711af3c1d3755a16  raw_logits.jsonl
d30f12bcec83f176f0d988cbd30c8a8779750ada5e2a776b71ede3300c7c2cf2  scores_calibrated.jsonl
f370b719f373b85c3bac3606bbc50cc4849f73b66ddae75409794d5a95bf4888  scores_raw.jsonl
```

## Calibration

Test MAE **0.5947 → 0.6066 (−2.0%)** — worse, as on the previous checkpoint (−1.9%). It ships
per ADR-008 and ADR-023's specificity tie-break, **not because it helped**. Val (its own fit
set) improves +4.5%, which is what isotonic regression is defined to do and is not evidence.

⚠️ The fit was run **twice** and produced identical numbers both times (val 0.5717 → 0.5461,
test 0.5947 → 0.6066), which is the only reason to call this path reproducible.

## What is NOT re-derived on this checkpoint

⛔ The Phase C outcome figures (87 disputed rows, 90.8%/94.3% removed, AUC 0.8454/0.8521), the
op-point trade arithmetic, and the CPU-vs-CUDA device delta (0 flips, max |Δ| 0.1428) were all
measured on the **epoch-4** model. They are not restated as figures for the shipped one. The
op-point ruling was not reopened: the shape of the trade is a property of the calibration
curve rather than of one checkpoint. Re-deriving them is owed and untriggered.
