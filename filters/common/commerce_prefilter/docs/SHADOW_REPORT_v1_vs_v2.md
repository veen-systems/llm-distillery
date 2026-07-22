# Commerce Prefilter — v1 vs v2 Shadow Comparison

**Date:** 2026-07-22
**Status:** This is the **Phase-5 shadow comparison** that `V2_DESIGN.md` required before cutover but that was **never run**. v2 was cut over to production on 190-sample test-set parity alone. This report runs the missing comparison on real production traffic — and finds v2 is **not** at parity in production.

## TL;DR

**v2 (currently live) underperforms the v1 it replaced on both axes:** it blocks less than half the commerce v1 does (2.1% vs 5.2%), misses obvious product listings, *and* generates false positives on multilingual (esp. Greek) news. On the eyeballed disagreements, v1's calls are consistently the correct ones. The 190-sample test-set "parity" (0.978 F1) masked this because it was too small and not representative of production's short, multilingual traffic.

## Method

- **Sample:** 1,000 recent production articles from `content_items_20260722_160954.jsonl` (non-empty content, ≥50 chars).
  - **Languages:** en 460, **el (Greek) 376**, es 117, hu 45, it 1, fr 1
  - **Length:** short RSS snippets — content chars min 50 / median 125 / p90 382 / max 1,429
- **Models, scored fresh:** v1 = `CommercePrefilterSLM` (DistilBERT, 512-token, 541 MB); v2 = `CommercePrefilterV2` (paraphrase-multilingual-mpnet + MLP, 128-token).
- **Threshold:** 0.95 for both (v1 backtest op-point = v2 README recommendation).
- **Environment:** gpu-server, CPU, scorer venv. Script: `docs/compare_commerce.py` (committed alongside this report).
- **Sanity check:** fresh-v2 scores vs the `_commerce_score` already written by production = **mean |Δ| = 0.000** over 1,000 → this report *is* live production behavior, not a re-implementation artifact.

## Results (threshold 0.95, n=1,000)

| Metric | v1 (DistilBERT) | v2 (embedding+MLP, **LIVE**) |
|---|---|---|
| Flagged as commerce | **52 (5.2%)** | **21 (2.1%)** |
| Binary decision agreement | 94.70% (947/1000) | |
| Raw-score correlation | pearson **r = 0.477** (weak) | |
| Mean \|score₁ − score₂\| | 0.124 | |

**53 disagreements, asymmetric and both unfavorable to v2:**

### ① v2 MISSES 42 items v1 flags (v2 under-blocks real commerce)
Median content of v2-misses = **92 chars** (< 125 overall) → **not** a long-article / 128-token effect.
Langs: en 36, el 5, fr 1.

| v1 | v2 | chars | title |
|----|----|-------|-------|
| 0.99 | 0.88 | 1153 | Avalue RIVAR-1539 15.6-inch fanless industrial panel PC |
| 0.99 | 0.74 | 1033 | Raspberry Pi Touch Display 2 – 10″ review, 3D printed VESA |
| 0.99 | 0.47 | 502 | UOB to Upgrade 300,000 Visa Infinite Cardholders Across ASEAN |
| 0.98 | 0.69 | 484 | Bottomline and Amex Simplify Digital Supplier Payments |
| 1.00 | 0.75 | 461 | Fresh Off a $13M Raise, Neon Wants to Hand Game Publishers… |
| 0.99 | 0.94 | 413 | Consumers Don't Want a Treasure Hunt at Checkout |

These are clear product/commerce items v1 catches and v2 leaks into the lens pipeline.

### ② v2 OVER-blocks 11 items v1 passes (v2 false-positives on news — Greek-heavy)
Langs: el 5, en 4, hu 2.

| v1 | v2 | chars | title |
|----|----|-------|-------|
| 0.41 | 0.96 | 64 | Size, price, parking: the priorities for the ideal home |
| 0.01 | 0.96 | 142 | Swiggy-Zomato deliveries 'for anyone who needs', medicine stalls |
| 0.02 | 0.96 | 84 | Mercedes-Maybach GLS revealed with "otherworldly" luxury |
| 0.10 | 0.99 | 120 | Νέο τεύχος Vita αυτή την Κυριακή με το ΒΗΜΑ |
| 0.02 | 1.00 | 161 | Ούτε κλιματιστικό… (electric cooling alternative — news) |
| 0.03 | 0.98 | 108 | Ζαλίζουν τα ποσά… εισιτήρια για την «Οδύσσεια» (ticket-resale news) |

v2 mis-fires on multilingual news containing price/product-adjacent vocabulary.

## Interpretation

1. **Not a context-length problem.** The 512→128-token cut was the suspected risk, but v2-misses are *shorter* than average. v2 is generically **less sensitive to commerce** and **less precise on multilingual news** — an embedder/MLP quality issue, not a truncation issue.
2. **Test-set parity was misleading.** 0.978 F1 on 190 samples hid a real production regression. The production distribution (short, multilingual, Greek-heavy) is not what the small test set measured.
3. **v1 is the better model on this sample** — higher commerce recall *and* higher multilingual precision on the disagreements.
4. **Live impact:** v2 currently (a) lets product listings through into the lens scorers, and (b) wrongly drops some non-English news *before* it reaches any lens. The latter compounds any downstream ranking/calibration concerns (cf. llm-distillery#76).

## Rollback complication

Cannot cleanly fall back to v1: its 541 MB weights are **only on the gpu-server**, not on the NexusMind box, so `commerce.py:271`'s local `CommercePrefilterSLM` fallback would `FileNotFoundError`. Rolling back requires either serving v1 from the scorer or restoring v1 weights to the NexusMind box. (See also the weights-backup gap: v1 is a single copy on the borrowed gpu-server.)

## Recommendation

- **Do not treat v2 as validated.** Either roll back to v1 (see complication) or **retrain v2 on representative production traffic** (multilingual, short snippets) before trusting it — the rework the TODO called for, now with evidence.
- **Back up the weights to HF Hub** (v1 + v2), matching the convention for the other filters, so rollback/retrain isn't gated on the borrowed machine.

## Reproduce

```bash
# 1000 recent articles from the newest raw file on sadalsuud → shadow_1000.jsonl
# then, on gpu-server (CPU):
HF_HUB_OFFLINE=1 CUDA_VISIBLE_DEVICES= PYTHONPATH=/home/hcl/llm-distillery \
  ~/gpu-server/nexusmind-scorer/venv/bin/python compare_commerce.py shadow_1000.jsonl
```
