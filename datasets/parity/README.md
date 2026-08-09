# Cross-box parity dumps

Raw per-dimension student predictions for one split, produced on two different
machines with **everything except the interpreter held constant**. They exist so
a claim like "box X may be used to measure specificity at op-point Y" has
evidence behind it instead of an assumption.

Produced by `scripts/verification/box_parity.py`, compared with
`scripts/verification/diff_box_parity.py`. Full record and interpretation:
`docs/evidence/2026-08-09-cross-box-parity-uplifting-v7.md`.

| file | box | stack |
|---|---|---|
| `uplifting_v7_test660_gpuserver-serving-venv_2026-08-09.jsonl` | **gpu-server serving venv (production)** | py 3.11.2, torch 2.11.0+cu130, transformers 5.0.0, peft 0.18.1 |
| `uplifting_v7_test660_b650_2026-08-09.jsonl` | b650 | py 3.12.3, torch 2.13.0+cu130, transformers 5.14.1, peft 0.19.1 |

Both CPU-only, batch size 16, same 660-row `uplifting_v7` held-out oracle test
split, md5-identical adapter weights / tokenizer / `inference.py` /
`base_scorer.py` / `config.yaml` / `calibration.json` / `filters/common/*`.

**They are committed because regenerating them is expensive and constrained**:
~30 min of CPU on the serving box, which is only free between pipeline cycles
(`nexusmind-scorer.service` has `Conflicts=ollama.service`).

## Reading these

`raw` is the **uncalibrated** per-dimension logit — bf16-quantised, so values
land on ~0.03 steps and two boxes are either identical on a row or a whole step
apart. `wavg` is the raw weighted average. **Neither is what production
surfaces**: apply `calibration.json` per dimension, clamp to 0–10, then weight.
`diff_box_parity.py` does this; a hand-rolled comparison on `wavg` will not
reproduce the gate's numbers.
