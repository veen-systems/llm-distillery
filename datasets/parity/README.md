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
| `uplifting_v7_test660_b650_2026-08-09.jsonl` | b650, **CPU** | py 3.12.3, torch 2.13.0+cu130, transformers 5.14.1, peft 0.19.1 |
| `uplifting_v7_test660_b650-CPU-prodstack_2026-08-10.jsonl` | b650, **CPU** | py 3.11.15 + production's pins — **660/660 bit-identical to production** |
| `uplifting_v7_test660_b650-GPU-prodstack_2026-08-10.jsonl` | b650, **CUDA** | same pins; 1 flip at 4.0, 3 at 4.5 |

The first two are CPU-only; the third is the same box on CUDA with production's
library versions pinned from `constraints/production-gpu-server.txt`, which is
production's pins on CUDA, and the fourth is production's pins on **CPU** — the
run that makes the decomposition possible
(`docs/evidence/2026-08-10-b650-gpu-production-stack-parity.md`). Changing one
variable at a time: **host contributes nothing** (gpu-server CPU vs b650 CPU, same
pins → **660/660 bit-identical, 0 flips at any threshold**), the **library stack**
is worth 3 flips at 4.5, and **CPU→CUDA** is worth 3 flips at 4.5 and 1 at 4.0.
An earlier version of this paragraph said the third dump had separated CPU-vs-CUDA
from the stack (it had not) and that pinning made agreement worse (it does the
opposite). All three: batch size 16, same 660-row `uplifting_v7` held-out oracle test
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
