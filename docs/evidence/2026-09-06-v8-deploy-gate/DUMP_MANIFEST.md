# human_thriving v8 — test-split score dumps (CUDA and CPU)

The inputs to the ADR-021 deploy gate, `filters/human_thriving/v8/ground_truth_gate.json`.

⛔ **The dumps themselves are NOT in git** — `datasets/*` is gitignored (`.gitignore:83`).
This manifest is the committed half: it names where each file lives, what produced it, and
its sha256, so a report can be matched to the pass that produced it.

## Why a second pass existed at all

Every v8 accuracy number before 2026-09-06 was measured on **CPU** while production serves
on **GPU** (#104). The device is not free: on `uplifting v7`'s 660 rows CPU→CUDA is worth
**max |Δ| 0.1956 with 3 verdict flips at 4.5**
(`docs/evidence/2026-08-10-b650-gpu-production-stack-parity.md`), and `EXP-015` measured
CUDA giving 18 TP against CPU's 17 at the same bar. A deploy gate is the one artifact that
must not inherit that caveat, so the split was re-scored on CUDA before the gate was run.

## Provenance, both passes

| | CUDA pass (the gate's input) | CPU pass (2026-09-04, kept for comparison) |
|---|---|---|
| Directory on b650 | `~/llm-distillery/ht_v8_test_dump_cuda/` | `~/llm-distillery/ht_v8_test_dump/` |
| Copied to (gitignored) | `datasets/gate/ht_v8_test_cuda/` | `datasets/gate/ht_v8_test_cpu/` |
| Date | 2026-09-06 | 2026-09-04 |
| Device | **CUDA**, `parameters=cuda:0` read off the loaded model | CPU |
| Box | b650-gpu (`jwasys-B650-EAGLE-AX`), RTX 3090 Ti 24 GB, driver 580.95.05 | same |
| venv | `venv-prodparity` — py 3.11.15, torch 2.11.0+cu130, transformers 5.0.0, peft 0.18.1, CUDA 13.0 (gpu-server's production pins) | same |
| Weights | `filters/human_thriving/v8/model/`, epoch 4 of 6, `adapter_model.safetensors` sha256 `363fc63d2a622b29bee4ac44fa444650dcca554c0a64a874e46a183d64f9291b` | same |
| Split | `datasets/training/human_thriving_v8/test.jsonl`, 660 rows, sha256 `e361b5175c66252582c395bf256eb253bfa9b35f780f2479907231fc4d58d726` | same |
| Calibration | the deployed `filters/human_thriving/v8/calibration.json`, sha256 `23c40f41cffe30da…` (isotonic, n=658, fitted on val) | same |

### sha256

**CUDA**

```
2465d13192ad20220ee1ced3f7ed3c4257215d80e12998b26d5e787cbb1a8fca  raw_logits.jsonl
fef1a56b00d4448bedfc0dfaf2074ddfe94a0d0e04149c831884771af80ff2fb  scores_calibrated.jsonl
0ead6f6b6e863029083f7bf1ecca3d35f99ea4e560865fbaa33ea6a78d58c7a2  scores_raw.jsonl
```

**CPU**

```
438b0d23609436a52c1b7c50cdb82d03a96e8197e4b3d7adf73bf2963eae05bb  raw_logits.jsonl
ff3444f0295d39dc5a51f430c78e9c74201e739721d132cee3488af28f7e4496  scores_calibrated.jsonl
eccbf8f3c392063c2cefe229f1fc8954195a01569b361608c2ec2f52e1d40eb1  scores_raw.jsonl
```

## The command

```bash
ssh b650-gpu 'cd ~/llm-distillery && PYTHONPATH=. HF_HUB_OFFLINE=1 \
  venv-prodparity/bin/python scripts/analysis/dump_student_scores.py \
    --filter filters/human_thriving/v8 \
    --split-file datasets/training/human_thriving_v8/test.jsonl \
    --out-dir /home/jeroen/llm-distillery/ht_v8_test_dump_cuda \
    --require-device cuda'
```

Log: `b650-gpu:~/llm-distillery/logs/ht_v8_cuda_dump_20260906.log`.

⚠️ **`--require-device` was added for this run** and reads the device back off
`next(scorer.model.parameters()).device`, not off the flag. Passing a device is not the
same as being on it: a "CPU" arm has already read **2.37 ms against GPU's 2.34** (true CPU
42.41, 18×) because a cache keyed on the model name alone ignored the device it was asked
for (#146). The log line records both — `device: declared=cuda parameters=cuda:0`.

⚠️ **`--out-dir` is under `~/llm-distillery/`, not `/tmp`.** Eleven probes were found one
reboot from gone in b650's `/tmp` on 2026-09-05 after 36 days of uptime.

## ⚠️ The b650 checkout is not a git clone

`~/llm-distillery` on b650 has no `.git`. Four files in this scoring path had drifted from
the repo, so they were **synced from the repo before the CUDA pass** — the dump must be
produced by the shipped program, not by a copy of it:

| File | b650 before | repo (= what ran) |
|---|---|---|
| `filters/human_thriving/v8/base_scorer.py` | `a39b07a2534a` | `c6cd2431eb1d` |
| `filters/human_thriving/v8/inference.py` | `07a53d08c1b8` | `b34dfd9c46f5` |
| `scripts/analysis/dump_student_scores.py` | `ff99065263cb` | `8072c122556f` (this run's, with `--require-device`) |
| `scripts/calibration/fit_calibration.py` | `d028893e2e95` | `d68ded222a16` |

The b650 copies are backed up at `~/llm-distillery/.presync_backup_20260906/`.

⚠️ **This matters for reading the CPU pass, which predates the sync.** The differences were
checked file by file: `base_scorer.py` and `inference.py` differ only in **docstrings**;
`fit_calibration.py` gained `--force-config-update` and a pure decision function, neither on
the inference path; `dump_student_scores.py` moved its write **after** its presence control
and gained `--require-device`. **No difference touches the arithmetic**, which is why the
two passes are comparable as a device measurement. All other 60 modules under
`filters/common/`, `filters/human_thriving/v8/`, `scripts/analysis/` and
`scripts/calibration/` were already byte-identical.
