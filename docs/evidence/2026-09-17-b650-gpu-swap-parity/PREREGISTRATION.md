# Pre-registration — what the b650 GPU swap cost, and what it invalidates

Written **before** the arms were diffed. The CUDA arm had already been dumped
(661 lines, 07:38:27→07:38:39) but not compared; the CPU control was still running.

## The event

b650 came back up on 2026-09-17 with an **RTX 5090 32 GB (Blackwell, `sm_120`,
driver 580.173.02)** in place of the **RTX 3090 Ti 24 GB (Ampere, `sm_86`, driver
580.95)**. Nothing else on the box changed: same Ryzen 7 9700X, same 30 GB, same
Ubuntu 24.04.3, same checkout (`b1e945b`, 0 tracked-file drift), same venvs.

## Why this is not a housekeeping question

`docs/evidence/2026-08-10-b650-gpu-production-stack-parity.md` decomposed b650's
disagreement with gpu-server into three terms. Its **run G** is labelled
`b650 | CUDA | production's pins` — and that CUDA is the 3090 Ti. So the device
term it reports (**CPU→CUDA max |Δ| 0.1956, 1 flip @4.0, 3 @4.5**) describes
hardware that is no longer in the box. Roughly forty surfaces across this repo
cite that number.

⛔ **The 0.1956 does not become WRONG.** It remains a correct measurement of
CPU→CUDA-on-Ampere. What it loses is *transferability to b650 as it now exists*.
The question here is whether the replacement silicon lands in the same place.

## Arms

All arms are b650, `venv-prodparity` (py 3.11.15, torch 2.11.0+cu130,
transformers 5.0.0, peft 0.18.1, sklearn 1.8.0, numpy 2.4.2 — production's pins),
`uplifting v7`, its 660-row held-out split, `--batch-size 16`.

| id | device | date | role |
|---|---|---|---|
| **G** (stored) | CUDA — 3090 Ti | 2026-08-10 | the old device arm |
| **C** (stored) | CPU | 2026-08-10 | the old CPU arm |
| **G_new** | CUDA — 5090 | 2026-09-17 | the new device arm |
| **C_new** | CPU | 2026-09-17 | **the control** |

## The control, and why it carries the whole attribution

**C_new vs stored C is the load-bearing comparison, not a formality.** Every
other diff here crosses five weeks as well as a GPU. If C_new reproduces stored
C **bit-identically, 660/660**, then the weights, the split, the code, the stack
and the CPU are all provably unmoved, and the only free variable left in
G → G_new is the GPU plus its driver.

⛔ **If the control does NOT reproduce, no number in this directory may be
attributed to the GPU** — something else moved, and finding it comes first.

This is the concrete form of the working rule about hand-built populations: the
alternative was to md5 a list of files I chose myself and call that "everything
that matters". The md5s were taken anyway (11 files, all matching between
situla and b650, including the gitignored adapter weights and the split), but a
byte-identical re-run of the whole pipeline is the stronger statement, because
it does not depend on my list being complete.

## Pre-stated expectations

Stated before looking, so a hit cannot be read as confirmation after the fact:

1. **C_new ≡ C, 660/660 bit-identical.** Anything else is a stop-and-investigate.
2. **G_new ≠ G.** bf16 accumulation order differs between GPU architectures; a
   zero here would be the surprise, and would itself need explaining.
3. **The magnitude lands in the same band as the other device/stack terms —
   roughly 0.1 to 0.3 max |Δ|, a handful of rows over the #95 0.16 floor, and
   0–3 verdict flips at 4.0/4.5.** A result far outside that band is more likely
   an instrument fault than a discovery, and gets re-run before it gets written up.
4. **Signed mean ≈ 0.** A device term should be accumulation noise, not a
   direction. A non-zero signed mean would mean the new GPU *biases* scores, which
   is a much more serious claim than "it perturbs them".

## What this cannot answer

- **Nothing about gpu-server.** gpu-server was not re-run. The host term
  (P→C, 0.0000) was measured with the device held at **CPU** and is untouched by
  this; the CUDA-to-CUDA host comparison remains unmeasured and is now a
  comparison across two different GPU architectures, i.e. *further* out of reach
  than it was on 2026-08-16.
- **Nothing about production's scores.** Production serves on gpu-server's GPU.
  This measures b650 against b650.
- **Nothing about any filter but `uplifting v7`.** A floor belongs to a
  population and a mechanism. `human_thriving v8`'s own device term was 0.1428
  with 0 flips on the same split shape — the two disagree already, on Ampere.
