# Pre-registration — what the DEVICE is worth at each live filter's op-point (`EXP-041`, 2026-09-17)

⛔ **Written and committed BEFORE the first dump.** Issue: llm-distillery**#104** — *every accuracy
number is CPU-measured; production serves on GPU*. This is that issue's **proposed work item 2**
(the device-only comparison with host and stack held) extended from one filter to every live one,
plus the decision its item 3 asks for.

Spend: **$0**. No oracle calls. b650-gpu, `venv-prodparity`, RTX 5090.

## The question, and what is already known

`#104` measured `uplifting v7` on 2026-08-10 (Ampere): **1 verdict flip at 4.0**, 3 at 4.5,
max calibrated |Δ| **0.1956**, 4/660 rows bit-identical. `EXP-038` re-measured it on the swapped
GPU (Blackwell, 2026-09-17): max |Δ| **0.1572**, **0 rows above the #95 floor**, and **1 flip at
4.0 / 2 at 4.5** — ⛔ flips survive even when no row exceeds the floor, which is why this reads the
flip count and not the magnitude.

**Nobody has run the other five.**

⛔ **CORRECTION, same day, before any result was read: the sentence that stood here was wrong.**
It said *"every `ground_truth_gate.json` in the tree is a CPU measurement and none of them says so
— there is no `device` field on any of the six."* I had grepped **top-level keys only**, and the
field lives at `provenance.device`. Measured properly:

| filter | `provenance.device` |
|---|---|
| `uplifting v7` | `cpu` |
| `cultural_discovery v5` | `cpu` |
| `belonging v1` | `cpu` |
| `human_thriving v8` | **CUDA** — *"read back off `next(model.parameters()).device`, not off the flag"* (#146) |
| `nature_recovery v4` | **absent** |
| `solutions v6` | **absent** |

⭐ **And the corrected fact is worse than the one I published, not better.** The tree does not hold
six CPU gates; it holds **four CPU gates, one CUDA gate and two that do not say** — so an
ADR-021 comparison across filters is already mixing devices, which is the exact risk `#104` names
in its third bullet. The stamp deliverable narrows to two files and widens to a CHECK: a hand-written
provenance block is only as good as the hand, and two of six hands forgot.

## Op-points, established by EXECUTION not by reading config

`TIER_THRESHOLDS` in each `base_scorer.py` (the sole runtime source), cross-checked against
`normalization.json` `stats.raw_min` and the gate artifact's own `threshold`:

| filter | op-point | raw_min | gate threshold |
|---|---|---|---|
| `human_thriving v8` | **4.5** | *(no normalization.json — Phase E, #154)* | 4.5 |
| `uplifting v7` | **4.5** | 4.5 | 4.5 |
| `cultural_discovery v5` | **4.0** | 4.0006 | 4.0 |
| `belonging v1` | **4.0** | 4.0 | 4.0 |
| `nature_recovery v4` | **3.75** | 3.75 | 3.75 |
| `solutions v6` | **2.25** | 2.25 | 2.25 |

## Method

Per filter, both arms on the SAME box, SAME venv, SAME split, SAME adapter — only
`CUDA_VISIBLE_DEVICES` differs:

```
box_parity.py --filter filters/<f> --data datasets/training/<f>/test.jsonl --out preds-{cpu,cuda}.jsonl
diff_box_parity.py --a preds-cuda.jsonl --b preds-cpu.jsonl --threshold <op-point> --noise-floor 0.16
```

⭐ **The SERVING arm goes in `--a`**, per that script's own contract: production serves on GPU, so
CUDA is A and CPU — what every published number was measured on — is B.

## Predictions, stated before looking

| quantity | predicted | reasoning |
|---|---|---|
| verdict flips at the op-point, per filter | **0–3** | `uplifting v7` gave 1 at 4.0 and 2 at 4.5 on this exact GPU |
| ⭐ **filters with ≥1 flip** | **at least 1 of 6**, and I expect **3–6** | one is already known to flip; nothing makes the others special |
| max calibrated \|Δ\| per filter | **0.10–0.25** | `uplifting` 0.1572 (Blackwell) / 0.1956 (Ampere) |
| specificity change at the op-point | **≤0.01 on every filter** | a handful of flips over ~660 rows |
| recall change at the op-point | **≤0.02 on every filter** | positives are the smaller class, so the same flip count moves recall more |
| `solutions v6` (op-point **2.25**, far from the others) | flips **≥** the median filter | a lower bar sits deeper in the score mass, where more rows are within |Δ| of it |

⛔ **A prediction I am NOT making: that specificity is safe.** `#104` states the device term is
~0.007 on specificity **for uplifting v7**, where the one flip was TP→FN. A FP→TN or TN→FP flip on
another filter moves specificity directly, and under ADR-023 specificity is the metric that decides.

## Decision rule, fixed in advance

| outcome | what happens to the gate artifacts |
|---|---|
| any filter moves **specificity by >0.01** at its op-point | ⛔ gates must be **re-measured on GPU** before any future ADR-021 comparison; the CPU numbers stop being quotable as production's |
| all filters ≤0.01 specificity, but ≥1 flip anywhere | **stamp `device` into every `ground_truth_gate.json`** and carry the term as a known band — `#104` item 3, option B |
| **0 flips on all six** | the device is free *at these six op-points* — ⛔ still stamp `device`, because the claim is a (stack, device, threshold) triple and the next threshold move re-opens it |

⚠️ **Every branch ends in the same stamp.** That is deliberate: the stamp is the finding either way,
and a result that changes nothing is what an unstamped artifact currently looks like.

## Controls

1. **Bit-identity control.** `diff_box_parity.py` reports rows bit-identical; if an arm comes back
   660/660 identical to the other, the two arms were not actually different — the CUDA arm silently
   fell back to CPU. ⛔ Check `cuda_available` in each dump's env block before reading any number.
2. **Same-input control.** Both arms read the same split file; the dumps carry row ids and the diff
   fails on a mismatch.
3. ⚠️ **NOT controlled: batch composition (#95).** Both arms score the same split in the same order,
   so the |Δ| here is device-only *given that order* — it is not a bound on what a different batch
   would do. `#95`'s 0.16 floor is a separate axis and is used only as the reporting threshold.

## What this CANNOT establish

- **That gpu-server's GPU behaves like b650's.** CUDA-to-CUDA across the two boxes is still
  unmeasured, and they are now different architectures. This measures the device AXIS on one box.
- **Anything about production rows.** These are held-out test splits, not live articles.
- **A better model.** Nothing is retrained; no artifact is replaced.
