# Cross-box parity: the Gemma-3-1B student is not box-clean

**Measured 2026-08-09 (night session). uplifting v7, 660-row held-out oracle test split.**

> ### ✅ This document stands. A retraction posted against it earlier on 2026-08-10 was itself wrong and has been withdrawn.
>
> **History, because the mistake is more instructive than the result.** On the
> morning of 2026-08-10 I banner-retracted the "not cleared at 4.5" conclusion
> below, on the grounds that the two boxes' **#95 specificity bands overlap**.
> That was **the wrong instrument**. The #95 band answers *"how much could this
> metric move if batch composition changed?"* — and these parity runs hold batch
> composition **fixed** (same rows, same order, same batch size 16). Batch noise
> is not the source of variation between them, so a band built from it cannot
> license "indistinguishable". I reached for the repo's most-used caveat without
> checking that its premise applied.
>
> **A third run the same afternoon settled it.** b650 rebuilt on production's
> frozen ML stack (torch 2.11.0+cu130, transformers 5.0.0, peft 0.18.1 — the
> named packages; 13 of 58 transitive deps still differ) and
> run on **CUDA** flips **the same three articles** at 4.5, in the same
> direction, to the same specificity 0.9662. A proximity control rules out "it's
> just whatever is nearest the cut": of 18 production rows in [4.30, 4.50) only
> those 3 flip, while a row at 4.4870 — *closer* to the threshold — does not.
> **The difference is systematic and article-specific, and this document's
> conclusion is correct as written.**
>
> **And a fourth run reversed the reason.** This document's conclusion is right
> *for the configuration it measured* — b650 on a **mismatched** stack. Pin
> production's library versions and run on CPU and b650 becomes **660/660
> bit-identical to production, 0 flips at every threshold**. The 3 flips at 4.5
> were the **library stack**, not the hardware, and they are removable. Host
> contributes nothing. (An intermediate write-up here claimed pinning made things
> *worse*; that was confounded — it changed the stack and the device at once.)
> The box effect is also an order of magnitude smaller than #102's 4.0→4.5 gain
> (0.0068 vs 0.054), so it governs *which machine may produce a number*, never
> *what that number implies*.
>
> Full record: [`2026-08-10-b650-gpu-production-stack-parity.md`](2026-08-10-b650-gpu-production-stack-parity.md).

## One-line answer

**b650 is cleared at the 4.0 op-point and NOT cleared at 4.5.** Yesterday's
`ground_truth_gate.json` numbers reproduce exactly on production's own
interpreter, so #102's premise stands — but the candidate threshold it wants to
move to sits inside the skew.

## Why this was run

`filters/uplifting/v7/ground_truth_gate.json` recorded its own provenance
honestly: `/provenance/box = b650 (RTX 3090 Ti), CPU-only. NOT the serving box.`
Its caveat 1 flagged "unquantified cross-box uncertainty" on the threshold
metrics. Since **spec 0.9189 is the entire premise of #102**, and the e5 probe's
clean parity (max |Δ| 4.2e-6) had never been shown to extend to the student,
the uncertainty had to be quantified before a threshold move could be argued.

## Controls

Everything except the interpreter was held constant and **verified by md5 on
both boxes**, not assumed: `model/adapter_model.safetensors`,
`adapter_config.json`, `tokenizer.json`, `tokenizer_config.json`,
`inference.py`, `base_scorer.py`, `config.yaml`, `calibration.json`,
`filters/common/{model_loading,filter_base_scorer,text_preprocessing}.py`, and
the 660-row `test.jsonl`. This repo's `scripts/calibration/fit_calibration.py`
was copied to both boxes and md5-checked, so the inference code is provably the
same object rather than "the same file, probably". Batch size 16 both sides,
same input order, CPU both sides.

| | gpu-server serving venv (**production**) | b650 |
|---|---|---|
| python | 3.11.2 | 3.12.3 |
| torch | 2.11.0+cu130 | 2.13.0+cu130 |
| transformers | **5.0.0** | **5.14.1** |
| peft | 0.18.1 | 0.19.1 |
| sentence-transformers | 5.2.2 | 5.6.1 |
| numpy | 2.4.2 | 2.5.1 |

The production interpreter was read off `systemctl cat nexusmind-scorer`
(`ExecStart=/home/hcl/gpu-server/nexusmind-scorer/venv/bin/uvicorn`), **not**
`which python3` — the system python is torch 2.5.1+cu124 with no `peft` at all
and cannot even load the adapter.

## Result

**Agreement at 4.0 is total:**

| | gpu-server | b650 |
|---|---|---|
| tp / fn / fp / tn | 159 / 57 / 36 / 408 | 159 / 57 / 36 / 408 |
| recall / specificity | 0.7361 / 0.9189 | 0.7361 / 0.9189 |
| verdict flips | — | **0 of 660** |

**But the underlying skew is real, and larger than the #95 floor at the tail:**

- ⭐ **the instrument could say no, and did:** three rows flip at 4.5 (below), and
  15/660 rows differ on at least one dimension — so a null on this comparison would be a
  measurement, not a dead instrument
- bit-identical on every dimension: **15/660 (2.3%)**
- max |Δ| per raw dimension: 0.0625 – **0.1250**
- calibrated weighted score |Δ|: p50 **0.0000**, p90 0.0345, p99 0.1198, **max 0.2008**
- **1 row (0.15%) exceeds the #95 |0.16| noise floor** — `south_african_businesslive_2cb1e80cae4f`, 5.8413 vs 5.6405
- signed mean (b650 − gpu-server): **+0.00018** → noise, not a systematic shift

**At 4.5, three rows flip** (`east_african_fana_bc_…`, `german_deutschlandfunk_…`,
`global_south_global_voices_…`), all in the same direction, and specificity
diverges: **0.9730 (production) vs 0.9662 (b650)**. Measuring #102's candidate
threshold on b650 would have understated production's specificity by 0.7 points.

## The consequence

**A box is cleared at a threshold, never in general.** The e5 probe result
(4.2e-6, zero flips) does *not* license using a dev box for student threshold
work, because the student is a different path with ~0.03 bf16 granularity and a
0.2 tail. The median |Δ| of exactly 0.0000 makes this easy to misread: it does
not mean the stacks agree, it means the quantisation hides most disagreements.

## Bonus: the #102 threshold sweep, on production predictions

On-lens fixed at oracle ≥ 4.0; only the student's bar moves.

| student thr | recall | specificity | **FPR** | fp |
|---|---|---|---|---|
| **4.00** (current) | 0.7361 | 0.9189 | **8.11%** | 36 |
| 4.25 | 0.6667 | 0.9459 | 5.41% | 24 |
| **4.50** | 0.6111 | 0.9730 | **2.70%** | 12 |
| 4.75 | 0.5602 | 0.9842 | 1.58% | 7 |
| 5.00 | 0.4769 | 0.9887 | 1.13% | 5 |

4.5 lands uplifting's FPR at 2.70%, between `solutions v6` (2.8%) and
`nature_recovery v4` (2.1%) — exactly what #102 hypothesised. It trades 24 fewer
false positives for 27 more false negatives, which under ADR-023 is the right
direction.

**This is NOT the ADR-021 gate run.** No #95 band was applied to these deltas,
`scripts/gate/ground_truth_gate.py` was not used, and the split is 32.7%
enriched so the rates do not transfer to production. It is pre-work that removes
one confound from #102 step 2, not a decision.

## Still unmeasured

- **CPU vs CUDA on the student.** Today isolated the *library stack*, on CPU
  both sides. Production serves on GPU. The 5.4e-6 CPU-vs-CUDA figure in
  `memory/b650-gpu.md` is the **e5 probe's**, not the student's.
- **The obituary/violence mpnet + sklearn-MLP path**, where the original |0.16|
  cross-box skew was measured (ST 5.6.0 on sadalsuud vs 5.2.2 on gpu-server).
  That is #81, and obituary enforces at 0.85 with a 0.0012 margin.

## Reproduce

```bash
# both boxes (see scripts/verification/box_parity.py docstring for the full form)
ssh <box> 'CUDA_VISIBLE_DEVICES="" ... python box_parity.py --filter ... --out preds-<box>.jsonl'

PYTHONPATH=. python scripts/verification/diff_box_parity.py \
    --a datasets/parity/uplifting_v7_test660_gpuserver-serving-venv_2026-08-09.jsonl \
    --b datasets/parity/uplifting_v7_test660_b650_2026-08-09.jsonl \
    --labels <split>/test.jsonl \
    --calibration filters/uplifting/v7/calibration.json \
    --repo-root . --threshold 4.0 --alt-threshold 4.5
```
