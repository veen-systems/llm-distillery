# b650 on production's exact stack, on GPU — and a correction to my own correction

**Measured 2026-08-10. uplifting v7, the same 660-row held-out split, third run.**

## One-line answer

**Pinning production's library versions did not make b650 agree with production —
it made it agree slightly *worse*.** The residual disagreement is
hardware/kernel-level, not library-level, and it is **systematic and
article-specific**, not batch noise. `b650` remains usable at 4.0 and not at 4.5,
which is what the 2026-08-09 run said before I incorrectly walked it back this
morning.

## What was built

b650's GPU had been unusable since the box was commissioned: triton's helper
compile dies on `Python.h: No such file or directory`, and `sudo` needs a
password. **The fix needed no sudo.** The venv was built on the *system* python
(`pyvenv.cfg` → `home = /usr/bin`), which ships no headers, but `uv 0.12.0` was
already installed and can download a standalone CPython that does:

```bash
uv python install 3.11          # ships include/python3.11/Python.h
uv venv ~/llm-distillery/venv-prodparity --python 3.11
```

Built to **production's frozen versions**, not to `requirements.txt`'s ranges:
python 3.11.15 (production 3.11.2), torch **2.11.0+cu130**, transformers
**5.0.0**, peft **0.18.1**, numpy **2.4.2**, scikit-learn **1.8.0**,
sentence-transformers **5.2.2** — every one matching
`constraints/production-gpu-server.txt`. triton 3.6.0 now compiles and runs a
kernel. The existing `venv/` was left untouched, because the 2026-08-09 parity
dumps cite it as provenance.

**A defect in the constraints file, found by using it:**
its header documents `pip install -r requirements.txt -c constraints/production-gpu-server.txt`,
and **that command cannot succeed**. `requirements.txt` requires
`datasets>=2.14.0,<3.0.0`, every version of which pins `fsspec<=2024.6.1`, while
production's `torch==2.11.0` requires `fsspec==2026.1.0`. Production's serving
venv **has no `datasets` at all** — it is a serving environment, and `datasets`
is a training dependency. The documented command was written and never run.

## The result

Production (gpu-server serving venv, **CPU**) vs b650 (**production stack,
CUDA**). Adapter weights, tokenizer, `config.yaml`, `calibration.json` and the
split all md5-identical; batch size 16; same input order.

| | vs b650 CPU / *different* stack (2026-08-09) | vs b650 **GPU / production stack** (today) |
|---|---|---|
| bit-identical rows | 15/660 (**2.3%**) | 4/660 (**0.6%**) |
| max per-dim raw \|Δ\| | 0.0625–0.1250 | 0.0938 |
| calibrated \|Δ\| p90 / p99 / max | 0.0345 / 0.1198 / **0.2008** | 0.0442 / 0.1388 / **0.1956** |
| rows over the #95 0.16 floor | 1 (0.15%) | 3 (0.45%) |
| signed mean | +0.00018 | +0.00073 |
| **verdict flips at 4.0** | **0** | **1** |
| **verdict flips at 4.5** | **3** | **3 — the same three articles** |
| specificity at 4.5 | 0.9662 | 0.9662 |

**Matching the library stack made agreement worse on every count that moved.**
Bit-identical fell from 2.3% to 0.6%, rows over the noise floor went 1 → 3, and a
verdict flip appeared at 4.0 where there had been none
(`mexican_la_jornada_0627316503ad`, 4.0371 → 3.9532). The one thing that did not
change is the thing that matters: **the same three articles flip at 4.5, in the
same direction, producing the same specificity 0.9662.**

## The proximity control — this is not "whatever is nearest the threshold"

The obvious deflation is that any perturbation flips whichever rows sit closest
to the cut. It does not hold. Of the **18** production rows in `[4.30, 4.50)`,
exactly **3** flip up, and they are the **same 3** on both b650 configurations:

| production | b650 CPU / new stack | b650 GPU / prod stack | article |
|---|---|---|---|
| 4.4919 | **4.5386 ↑** | **4.5386 ↑** | `east_african_fana_bc_…` |
| 4.4870 | 4.4870 | 4.4430 | `danish_dr_nyheder_…` — **closer to the cut, does not flip** |
| 4.4840 | 4.4779 | 4.4779 | `biotech_pharma_genetic_engineering_news_…` |
| 4.4667 | 4.4667 | 4.4667 | `south_african_daily_maverick_…` |
| 4.4140 | **4.5427 ↑** | **4.5311 ↑** | `german_deutschlandfunk_…` |
| 4.3919 | **4.5340 ↑** | **4.5394 ↑** | `global_south_global_voices_…` — **further from the cut than five non-flippers** |

Three specific articles move **+0.13 to +0.15** on b650 in both configurations
while their immediate neighbours are bit-stable, and one of them (`east_african_fana_bc`)
lands on **exactly the same value, 4.5386, in both b650 runs** despite a
different torch, a different transformers and a different device.

At 4.0 the same window is clean: of **17** production rows in `[3.80, 4.00)`,
**0** flip on either configuration.

So the disagreement is **article-specific and reproducible**, not a random draw.

## The correction — and it is a correction of a correction

Earlier today I put a banner on
`2026-08-09-cross-box-parity-uplifting-v7.md` retracting *"b650 is cleared at 4.0
and NOT cleared at 4.5"*, on the grounds that the two boxes' #95 specificity
bands overlap. **That was the wrong instrument, and the retraction is
withdrawn.**

The #95 band answers *"how much could this metric move if the batch composition
changed?"* These parity runs deliberately hold batch composition **fixed** —
same order, same batch size, same 660 rows. Batch noise is therefore not the
source of variation between them, and a band built from it cannot license
"indistinguishable". I reached for the repo's most-used caveat without checking
that its premise applied.

Stated separately, all three things are true:

- **b650 differs from production systematically at 4.5.** Same 3 articles, same
  direction, across a library-stack change *and* a device change. Yesterday's
  conclusion stands as written.
- **The size of that difference (0.0068 specificity) is smaller than the
  batch-noise band at the same threshold (0.0248).** So it does not change what
  specificity can be *claimed* for production — production's own number moves
  more than that between cycles.
- **Therefore it does not affect #102's conclusion at all.** The 4.0 → 4.5
  specificity gain is 0.054, an order of magnitude larger than the box effect
  and larger than the band. What the box effect governs is *which machine may
  produce the number*, not *what the number implies*.

The general rule survives all three revisions and is the part worth keeping:
**a box is cleared at a threshold, never in general** — and now, additionally,
**you cannot clear a box by pinning its library versions.**

## What this changes operationally

- **b650's GPU works.** `~/llm-distillery/venv-prodparity`, ~2 minutes for 660
  rows versus ~16 (b650 CPU) or ~30 (gpu-server CPU). Experiments no longer need
  to wait for a gap between production cycles.
- **Do not use it to produce a number at an op-point production will deploy**
  without checking flips at that threshold first. Use it freely for everything
  else — sweeps, ablations, ranking, anything measured as a *difference within
  one box*, where the effect cancels.
- **`sadaltager` is predicted to have the same triton failure** and the same
  no-sudo fix (`uv python install`). Untested.

## Still unmeasured

- **Why those three articles.** All three are non-English (Amharic-source
  English, German, and a Global Voices translation). Whether that is the
  mechanism or a coincidence at n=3 has not been checked, and n=3 is too small
  to claim it.
- **b650 GPU vs b650 CPU on the same box**, which would separate device from
  host. Both dumps now exist; only the cross-box diff has been run.

## Reproduce

```bash
ssh b650-gpu 'cd ~/llm-distillery && HF_HUB_OFFLINE=1 PYTHONPATH=$HOME/llm-distillery \
  ~/llm-distillery/venv-prodparity/bin/python /tmp/parity/box_parity.py \
    --fit-calibration /tmp/parity/fit_calibration.py \
    --filter ~/llm-distillery/filters/uplifting/v7 \
    --data ~/llm-distillery/datasets/training/uplifting_v7/test.jsonl \
    --out /tmp/parity/preds-b650-GPU-prodstack.jsonl'

PYTHONPATH=. python scripts/verification/diff_box_parity.py \
    --a datasets/parity/uplifting_v7_test660_gpuserver-serving-venv_2026-08-09.jsonl \
    --b datasets/parity/uplifting_v7_test660_b650-GPU-prodstack_2026-08-10.jsonl \
    --labels datasets/training/uplifting_v7/test.jsonl \
    --calibration filters/uplifting/v7/calibration.json \
    --repo-root . --threshold 4.0 --alt-threshold 4.5
```
