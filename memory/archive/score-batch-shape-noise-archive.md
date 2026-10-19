# Batch-shape score noise — archive (verbatim)

*Moved out of `memory/score-batch-shape-noise.md` on 2026-10-19 (#163 round 10, owner: "pruning, thinning, mechanizing, retiring"). Byte-for-byte; the live file carries a one-line pointer where each block stood. Operative rules, measured terms still in force, and ⛔/⭐ rule lines stayed live.*

## Moved 2026-10-19 (#163 round 10)

### From § *The owner decision, 2026-08-06* — the pinning option that was not one (was lines 63–67)

Note the option that was *not* available: "pin a batch size in production."
`DEFAULT_BATCH_SIZE = 16` (`filters/common/filter_base_scorer.py:50`) is already
fixed and never varies in production — the variable is batch *composition*, which
is what the seeding addressed. #95's own "suggested next steps" text offered
pinning as a live option; it was not one.

### § *Does it change a decision? Yes — measured 2026-08-03* (whole section; its table repeats § *The finding*) (was lines 98–115)

## Does it change a decision? Yes — measured 2026-08-03

The first pass (120 articles) found 0 tier flips **and 0 articles within 0.05 of
the op-point**, so it could not have found one. Re-run against the band where a
flip is possible (`scripts/diagnostics/measure_batch_shape_flips.py`):

| filter | op-point | in ±0.30 band | flipped | share of band | share of corpus |
|---|---|---|---|---|---|
| solutions v6 | 2.252 | 28 | 2 | **7.1%** | 0.07% |
| uplifting v7 | 4.0 | 33 | 3 | **9.1%** | 0.32% |

```
solutions [3]  bs1=2.1745(low)  bs4=2.3398(medium)  bs8=2.3080(medium)  bs16=2.1745(low)
uplifting [9]  bs1=4.0390(medium)  bs4=3.9193(low)   bs8=3.9012(low)     bs16=4.0390(medium)
```

Flips occur within 0.077 (solutions) / 0.039 (uplifting) of the op-point.


### From § *Distinguish from its two cousins* — the 2026-08-09 stack-unmatched measurement and its 2026-08-29 correction note (was lines 141–161)

  ⚠️ Everything below was measured 2026-08-09 with the **stack unmatched**, so read
  it as the stack term, not a box term.
  **NOW MEASURED FOR THE GEMMA STUDENT TOO (2026-08-09 night)**, and it is the
  same order as this floor rather than smaller: uplifting v7's 660 held-out rows,
  b650 vs gpu-server's serving venv, model weights + all filter/`common/` code +
  split md5-identical, CPU both sides — **max calibrated |Δ| 0.2008, i.e. ABOVE
  the 0.16 floor**, p99 0.1198, p90 0.0345, p50 0.0000, only 2.3% of rows
  bit-identical, signed mean +0.00018 (noise, not a shift). **Decision impact is
  threshold-dependent: 0 verdict flips at the 4.0 op-point (identical confusion
  matrix — ⚠️ **but 4.0 has not been the op-point since 2026-08-11, #102**, so that
  reassurance no longer describes the deployed cut) and 3 flips at 4.5,
  splitting specificity 0.9730 vs 0.9662.** So the two noise sources *stack*, and
  **a box is cleared at a threshold, never in general**. The e5 probe's clean
  4.2e-6 result does NOT transfer to the student. Beware the p50 of exactly
  0.0000 — raw logits are bf16-quantised (~0.03 steps), so most disagreements are
  hidden, not absent. Harness: `scripts/verification/box_parity.py` +
  `diff_box_parity.py`; record:
  `docs/evidence/2026-08-09-cross-box-parity-uplifting-v7.md`.
  ⛔ *That last line read "still unmeasured for the student: CPU vs CUDA" until
  2026-08-29. It was measured the NEXT DAY at **0.1956**, 1 flip at 4.0 and 3 at
  4.5 — see the correction block above.*

### From the ⭐ device-term block — the two confounds ruled out on the 5090 (2026-09-17) (was lines 180–184)

  ⚠️ Two confounds were ruled out rather than assumed: the 5090 is
  **self-deterministic run-to-run** (byte-identical 660/660, so none of the 0.2357
  is the GPU failing to repeat itself) — though that is one process shape on one
  box, **not** stability across batch size or composition — and the stored
  `_meta` stack fingerprints are identical across all dumps.

### From § *A THIRD cousin* — the 2026-09-11 harm_detector inherited-floor incident (was lines 229–239)

⛔ **AND THE POPULATION TRAVELS WITH IT — a shipped artifact got this wrong on
2026-09-11.** `harm_detector/v1`'s `inference.py` stated the **0.2008** "was taken on
exactly this architecture (mpnet + sklearn MLP, differing sentence-transformers
versions)". It was not: 0.2008 is the **Gemma-3-1B student's**, measured on `uplifting
v7`'s 660 held-out rows, b650 vs gpu-server's serving venv, CPU both sides. The
mpnet + sklearn-MLP architecture's stack term is **UNMEASURED**. The claim had reached
**five** places in the package — two docstrings, a README, a test docstring, and the
`RuntimeWarning` **emitted into production logs on every off-pin load** — and the first
correction pass fixed one of them, because I worked from a list instead of grepping the
files. Corrected in `bb5a52d` (llm-distillery) and NM#474.


### From § *A FIFTH candidate term* — the EXP-026 evidence (exclusions and confounds; open as `H-V8-23`) (was lines 326–348)

⛔ **Not a floor, and not yet a term — a candidate with two rivals excluded.** `EXP-026`
found `human_thriving v8`'s raw recall differing by **one article** between two ways of
scoring the same 660 rows with the same weights: `eval_ht_v8.py` <!-- placeholder --> gives **18 TP**, the
production inference path **17**.

Excluded by measurement:

- **the device** — CPU vs CUDA, same box, same dumps: **0 verdict flips on both arms**,
  max \|Δ\| **0.1428** calibrated / **0.0508** raw, the same 17 and 26 surfaced
  (`docs/evidence/2026-09-06-v8-deploy-gate/device_delta.py`). ⛔ Note that 0.1428 is
  **below** the #95 batch floor of 0.16, so zero flips is the expected outcome here, not a
  surprising one — this measurement bounds the device term for THIS population, it does not
  overturn the 0.1956 measured on `uplifting v7`.
- **the gatekeeper and the clamp** — applying or removing them moves **0 rows** across 4.5
  on either device (`why_18_not_17.py`).

Still confounded, all three at once: **dtype** (production holds 342 bfloat16 parameters
against 364 float32, score head in bf16; the other path forces `torch_dtype=torch.float32`),
**adapter loading** (`load_lora_local` → `get_peft_model` + a hand-rolled remap vs
`PeftModel.from_pretrained`) and **batch size** (16 vs 8 — itself a #95 composition term).
The quantisation signature is real — 3,960 logits taking **1,161 distinct values** — but it
shows bf16 is present, not that it is the cause.


### From the PROMPT POSITION paragraph — the un-numbering note (was lines 400–402)

*(Deliberately un-numbered: this file and the memory index were counting the same list from
two different bases — "a fifth" here against "a sixth" there. A hand-maintained ordinal in
two files disagrees the moment one is edited.)*
