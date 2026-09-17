# What b650's GPU swap cost: the device term got SMALLER, and still flipped verdicts

**2026-09-17.** b650's RTX 3090 Ti (Ampere, `sm_86`, driver 580.95) was replaced
by an **RTX 5090** (Blackwell, `sm_120`, driver 580.173.02, 32 GB). Pre-registration,
including the band predicted before looking: `PREREGISTRATION.md`.

## One-line answer

**The new GPU agrees with CPU BETTER than the old one did — max |Δ| 0.1572 against
0.1956, though those two are single measurements with no paired band, so the load
is carried by the flip counts and not by the ordering — but it still flips 2
verdicts at 4.5, and the two GPUs disagree with each other at 0.2357, so no stored
b650-CUDA dump may be diffed against a new one.**

⚠️ **That ordering is two single measurements, not a compared pair, and it must not
be read as a band-separated improvement.** Both figures are a **max over 660 rows**
— an extreme-value statistic, which is the least stable thing a sample publishes —
and the Ampere arm **can never be replicated**, because the card is out of the
machine. The only repeatability figure that exists here is within Blackwell
(run-to-run **0.0000**, byte-identical), and a band measured on one arm does not
license an ordering across two. **What is solid is the flip count and the
direction; "0.1572 < 0.1956" is a single-sample comparison and should be quoted as
one.**

⭐ **The finding worth carrying out of here is the third clause.** A term whose
every row is below the noise floor still changed two decisions. Flips are not
produced by large deltas; they are produced by small deltas *near the bar*. The
two rows that flipped moved by **0.0467** and **0.1421** — both comfortably under
0.16. **"Max |Δ| is below the floor" is not "the term is free", and this run is
the counter-example to reach for when someone (including me) argues that it is.**

## The runs

All on b650, `venv-prodparity` (py 3.11.15, torch 2.11.0+cu130, transformers
5.0.0, peft 0.18.1, sklearn 1.8.0, numpy 2.4.2 — production's pins), `uplifting v7`,
its 660-row held-out oracle split, `--batch-size 16`. The `_meta` stack
fingerprint — `host`, `python`, `executable`, `platform`, `torch`, `transformers`,
`peft`, `sentence_transformers`, `sklearn`, `numpy` — is identical in every dump,
including the ones from 2026-08-10. **Each of those 10 fields could have differed
and four of them have**: the B→C library-stack term in the 2026-08-10
decomposition is exactly `python`, `torch`, `transformers` and `peft` moving at
once, and it is worth 3 flips at 4.5. The harness records them for that reason.

| id | device | date |
|---|---|---|
| **C** | CPU | 2026-08-10 |
| **G** | CUDA — 3090 Ti | 2026-08-10 |
| **C_new** | CPU | 2026-09-17 |
| **G_new** | CUDA — 5090 | 2026-09-17 |
| **G_new′** | CUDA — 5090, immediate replicate | 2026-09-17 |

## The decomposition

| comparison | isolates | bit-identical | max \|Δ\| | rows > 0.16 | flips @4.0 | flips @4.5 |
|---|---|---|---|---|---|---|
| **C_new → C** | **nothing — the control** | **660/660 = 100%** | **0.0000** | **0** | **0** | **0** |
| **G_new → G_new′** | **nothing — determinism** | **660/660 = 100%** | **0.0000** | **0** | **0** | **0** |
| C → G | device, CPU→CUDA on **Ampere** | 4/660 = 0.6% | 0.1956 | 3 | 1 | **3** |
| **C_new → G_new** | device, CPU→CUDA on **Blackwell** | 5/660 = 0.8% | **0.1572** | **0** | 1 | **2** |
| **G → G_new** | **the GPU swap itself** | 10/660 = 1.5% | **0.2357** | 3 | **2** | 1 |

Signed means: +0.00073, +0.00120, +0.00047. All three are noise, not a direction —
**the new GPU does not bias scores, it perturbs them.**

Confusion matrices where they differ, at 4.5 (`on-lens := oracle ≥ 4.0`):

| device | tp | fn | fp | tn | recall | **spec** | prec |
|---|---|---|---|---|---|---|---|
| CPU | 132 | 84 | 12 | 432 | 0.6111 | **0.9730** | 0.9167 |
| CUDA — 5090 | 132 | 84 | 14 | 430 | 0.6111 | **0.9685** | 0.9041 |
| CUDA — 3090 Ti | 132 | 84 | 15 | 429 | 0.6111 | **0.9662** | 0.8980 |

Blackwell sits between CPU and Ampere on the axis this project optimises
(ADR-023, specificity).

**Recall is 0.6111 on all three — and that sameness is informative only because it
could have moved.** With 216 true positives, one flip in the tp/fn cells is worth
**0.0046** of recall, and the arms differ by 1–3 flips, so recall had a reachable
range of roughly **0.6065–0.6157** here and used none of it. Every flip in this
table landed in the **fp/tn** cells instead: the rows near the 4.5 bar on this
split are off-lens ones, so the device moves specificity and leaves recall alone.
⚠️ That is a property of *this* split's composition near *this* bar, not a rule.

## Why the attribution is clean, and what would have made it dirty

**The control carries this, not the md5 list.** `C_new` vs `C` is
**byte-identical, 660/660** — md5 `3b68c3b47749a41a38e3731df04b3477` on both row
sets, and the `_meta` blocks diff empty too. Five weeks, a reboot and a hardware
swap apart, the CPU arm reproduces bit for bit. So the weights, the split, the
code, the stack, the CPU and the interpreter are all provably unmoved, and the
**only** free variable in `G → G_new` is the GPU and its driver.

The md5s were taken as well (11 files, matching between situla and b650,
including the gitignored `adapter_model.safetensors` `eb0bf841…` and the split
`904ad059…`), but that list is **a population I chose by hand**. A byte-identical
re-run of the whole pipeline does not depend on my list being complete. Had the
control failed, nothing in this directory could have been attributed to the GPU
and the first job would have been finding what else moved.

**The other confound ruled out: run-to-run nondeterminism.** `G_new` was run
twice back to back and the dumps are **byte-identical, 660/660** (md5
`9dc730bb45560bb0a5bb8d6d3d965b48`). Without this, an unknown share of the 0.2357
would be the 5090 simply not repeating itself. ⚠️ This is **self-determinism in
one process shape on one box**, not stability: it says nothing about a different
batch size, a different composition (#95) or a different driver.

## Operational consequences

1. ⛔ **Stored b650-CUDA dumps are not comparable to new b650-CUDA runs.** The
   `G → G_new` term is **0.2357, above the #95 floor, 3 rows over, 2 flips at the
   deployed 4.0**. Anything in `datasets/parity/*GPU-prodstack_2026-08-10*` is an
   Ampere artefact. Re-dump rather than diff across the swap.
2. ✅ **b650-CUDA is now a slightly better stand-in for b650-CPU than it was** —
   0.1572 with zero rows over the floor. **This does NOT make it free**: 1 flip at
   4.0 and 2 at 4.5 survive. See the ⭐ above.
3. ✅ **Everything CPU-side is untouched.** `P→C` (host, 660/660 bit-identical,
   0.0000) and `B→C` (library stack, 0.2008) were measured with the device held at
   CPU. The control re-proves the CPU arm today. Those numbers stand.
4. ⛔ **The gpu-server extrapolation got worse, not better.** CUDA-to-CUDA across
   the two boxes was already unmeasured; it is now a comparison across two GPU
   *architectures*. Treat "the box is free" as strictly weaker than it was.
5. **Speed: 12 s for 660 rows on the 5090**, against ~2 min recorded for the
   3090 Ti and ~9 min 13 s for CPU on the same box today (07:38:39 → 07:47:52).
   The CUDA dump was checked for completeness (661 lines = 1 `_meta` + 660 rows,
   `device: cuda`, production pins in the header) before the figure was believed.
6. ⚠️ **None of this transfers to another filter.** `human_thriving v8`'s own
   device term was 0.1428 with 0 flips; v7's was 0.1956 with 3. A floor belongs to
   a population and a mechanism.

## Reproduce

```bash
# both arms, on b650
ssh b650-gpu 'cd ~/llm-distillery && HF_HUB_OFFLINE=1 PYTHONPATH=$HOME/llm-distillery \
  ./venv-prodparity/bin/python scripts/verification/box_parity.py \
    --fit-calibration $HOME/llm-distillery/scripts/calibration/fit_calibration.py \
    --filter $HOME/llm-distillery/filters/uplifting/v7 \
    --data $HOME/llm-distillery/datasets/training/uplifting_v7/test.jsonl \
    --batch-size 16 --out /tmp/parity/gpu.jsonl'        # prepend CUDA_VISIBLE_DEVICES="" for the CPU arm

# the control -- run this FIRST and stop if it is not byte-identical
D=datasets/parity/uplifting_v7_test660
cmp <(tail -n +2 ${D}_b650-CPU-prodstack_2026-09-17.jsonl) \
    <(tail -n +2 ${D}_b650-CPU-prodstack_2026-08-10.jsonl) && echo "control OK"

# the three terms
for pair in "${D}_b650-CPU-prodstack_2026-08-10.jsonl:${D}_b650-GPU-prodstack_2026-08-10.jsonl" \
            "${D}_b650-CPU-prodstack_2026-09-17.jsonl:${D}_b650-GPU5090-prodstack_2026-09-17.jsonl" \
            "${D}_b650-GPU-prodstack_2026-08-10.jsonl:${D}_b650-GPU5090-prodstack_2026-09-17.jsonl"; do
  PYTHONPATH=. python3 scripts/verification/diff_box_parity.py \
    --a "${pair%%:*}" --b "${pair#*:}" \
    --labels datasets/training/uplifting_v7/test.jsonl \
    --calibration filters/uplifting/v7/calibration.json \
    --repo-root . --threshold 4.0 --alt-threshold 4.5
done
```

## What this does NOT establish

- **Nothing about gpu-server or about production's scores.** gpu-server was not
  re-run. This is b650 against b650.
- **Nothing about training.** Every number here is inference. Whether the swap
  changes a *trained* adapter is a separate, unmeasured question — and a louder
  one, since training is nondeterministic across architectures in ways inference
  is not.
- **Nothing about any filter but `uplifting v7`.**
