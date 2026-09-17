# 2026-09-17 — b650's GPU was swapped, and a term below the noise floor flipped two verdicts

**$0 spend, no oracle calls, nothing in `filters/`, deploy N/A — inapplicable, not skipped**
(no filter package, model, calibration, threshold or config changed; this session produced
measurement and documentation). Commits `70555e2`, `81e1498`, `40d5235` + the curate commit.

## What happened

The owner reported b650 back up "with a brand new GPU". It is an **RTX 5090 32 GB**
(Blackwell, `sm_120`, driver 580.173.02 / CUDA 13.0) in place of the **RTX 3090 Ti 24 GB**
(Ampere, `sm_86`, driver 580.95 / CUDA 12.0). Only the GPU changed — same Ryzen 7 9700X,
30 GB RAM, Ubuntu 24.04.3, same checkout at `b1e945b` with 0 tracked-file drift.

That mattered beyond housekeeping: **run G of the 2026-08-10 decomposition is labelled
`b650 | CUDA | production's pins`, so the device term it produced was measured on hardware
that no longer exists**, and roughly forty surfaces in this repo cite it.

## The measurement (EXP-038)

`uplifting v7`, its 660-row held-out split, `venv-prodparity` (production's pins),
`--batch-size 16`. Full record: `docs/evidence/2026-09-17-b650-gpu-swap-parity/`.

| term | max \|Δ\| | rows > 0.16 | flips @4.0 | flips @4.5 |
|---|---|---|---|---|
| CPU→CUDA, **Ampere** (dead hardware) | 0.1956 | 3 | 1 | 3 |
| CPU→CUDA, **Blackwell** (current) | **0.1572** | **0** | 1 | **2** |
| **Ampere→Blackwell — the swap itself** | **0.2357** | 3 | **2** | 1 |

⭐⭐ **The keeper: a term with ZERO rows above the #95 0.16 floor still changed two verdicts
at 4.5.** The flipping rows moved **0.0467** and **0.1421**. A flip is a *small* delta *near
the bar*, so a max-|Δ| comparison against a floor is **structurally blind** to flips. **Read
the flip count at the op-point; the magnitude answers a different question.** This
invalidates a shortcut already in the repo — `human_thriving v8`'s device delta was partly
dismissed as *"0.1428, below the floor"*, when its **0 flips** is the load-bearing half.

## What made the attribution trustworthy

- **The control, not the md5 list.** The 2026-09-17 CPU arm reproduces the 2026-08-10 CPU
  dump **byte-identically, 660/660**, five weeks and a hardware swap apart, `_meta` stack
  fingerprints identical. So the GPU is the only free variable. The md5s were taken too
  (11 files matching situla↔b650, including the gitignored adapter weights and the split) —
  but that list is **a population I chose by hand**, and a full byte-identical re-run does
  not depend on it being complete.
- **The second confound, ruled out rather than assumed.** The 5090 repeats itself
  byte-identically run to run, so none of the 0.2357 is the GPU failing to repeat. ⚠️ That is
  one process shape on one box — **not** stability across batch size or composition.
- **Pre-registration written before any diff**, including the 0.1–0.3 band expected. 0.2357
  landed inside it.

## Where I was wrong, and what caught it

`check_claim_shapes.py` **rejected the write-up three times** — an ordering with no paired
band, and two sameness claims with no reachability bound. Each was fixed in substance:

- *"0.1572 against 0.1956"* is now stated as **two single measurements**, because both are a
  max over 660 rows and **the Ampere arm can never be replicated**. Occurrence **two** of the
  2026-09-05 "ordering published as a finding, with no band" entry.
- *"recall is identical on all three"* now carries its reachable range (**0.0046 per flip**
  on 216 positives, so ≈0.6065–0.6157, of which it used none — every flip landed in the
  fp/tn cells).

⭐ **The guard failing was the control working.** The tempting move was to add the word
"band" until it went green, leaving the claim as wrong as it was.

## Also this session

- **`sadalsuud → b650` ssh was broken by one word** — sadalsuud's `~/.ssh/config` said
  `User jwasys`, the box owner's account. The **key was correct all along** (fingerprint
  matches b650's `jeroen@sadalsuud-to-b650` entry). Fixed and **proved by outcome**; backup
  at `sadalsuud:~/.ssh/config.bak-20260917-b650user`. `memory/b650-gpu.md` and `CLAUDE.md`
  had contradicted each other about this, and `CLAUDE.md` was right about the outcome for the
  wrong reason — which is why it survived as a "known limitation".
- The old `venv` is **no longer CPU-only**: the triton JIT that could not build now compiles.
  `/usr/include/python3.12` is still absent, so the unblocker is the newer stack.
- Ollama on b650 has gained `gemma3:27b`; `phi4` is still absent (blocks #109 Arm B's
  4-model panel).
- **`--amend` invalidated a commit hash the same commit had just recorded** (gotcha log).
- 822 tests pass, 25 skipped.

## Open, and needing the owner

- **`H-DEV-1` (new): training across the swap is UNMEASURED.** Everything above is inference
  on fixed weights. Gates **#85** (obituary v6 retrain) and **#158** (single-seed metrics),
  both of which propose retraining on b650 and comparing against pre-swap checkpoints.
  ⛔ Do not call b650 "cleared for training" — it is cleared for *probe* work, a different
  claim. Cheap first step is same-box, same-seed, twice.
- **`H-V8-21` can no longer be falsified as written** — both its readings are 3090 Ti numbers
  and its ≥8-point method would now cross the swap. Close as unmeasurable or re-raise.
- **`H-V8-23`'s method has the same confound** — re-dump its bf16 baseline on the 5090 before
  varying dtype against it.
- **Budgets crossed into WARN**: `CLAUDE.md` 37,496 B (2,504 under the 40,000 hard cap) and
  the always-loaded layer 55,155 B of 60,000. Pre-existing and this session added ~480 B.

Issues commented: **#104**, **#95**, **#158**, **#85**, **#81**.
