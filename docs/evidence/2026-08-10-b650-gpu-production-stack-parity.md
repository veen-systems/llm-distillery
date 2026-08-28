# Decomposing cross-box disagreement: host vs library stack vs device

**Measured 2026-08-10. uplifting v7, the same 660-row held-out split, four runs.**

## One-line answer

**Pinning production's library versions clears the box — 660/660 rows bit-identical,
zero verdict flips at every threshold — WITH THE DEVICE HELD AT CPU.** Two different
physical machines, and not one score differs. ⚠️ *"completely" was the wording here
until 2026-08-29 and it overstates: every run below is CPU, production serves on GPU,
and CUDA-to-CUDA across boxes has never been measured. This sentence is the one that
propagated.* The disagreement everyone has been chasing
is **the library stack plus the device**, and **hardware contributes nothing**.

> ### ⚠ This document's first version claimed the opposite, and was wrong
>
> It said *"matching the library stack made agreement WORSE"* and hardened that
> into a rule — *"you cannot clear a box by pinning its library versions"* —
> propagated to five surfaces including `memory/b650-gpu.md` and
> `constraints/production-gpu-server.txt`.
>
> **It was confounded.** The comparison ran b650-CPU-with-mismatched-stack against
> b650-**CUDA**-with-matched-stack, changing the stack *and* the device at once,
> then attributed the whole difference to the stack. A review lens caught it; the
> missing fourth run (b650 **CPU** + production pins, ~16 min on a free box)
> settles it and shows the reverse. **Pinning works. It works perfectly.**

## The four runs

| id | host | device | stack |
|---|---|---|---|
| **P** | gpu-server (production serving venv) | CPU | py 3.11.2, torch 2.11.0+cu130, transformers 5.0.0, peft 0.18.1 |
| **B** | b650 | CPU | py 3.12.3, torch 2.13.0+cu130, transformers 5.14.1, peft 0.19.1 |
| **C** | b650 | CPU | **production's pins** (py 3.11.15) |
| **G** | b650 | **CUDA** | **production's pins** (py 3.11.15) |

Adapter weights, tokenizer, `config.yaml`, `calibration.json`, `inference.py`,
`filters/common/*` and the split are md5-identical everywhere; batch size 16;
same input order.

## The decomposition — one variable at a time

| comparison | isolates | bit-identical | max \|Δ\| | rows > 0.16 | flips @4.0 | flips @4.5 |
|---|---|---|---|---|---|---|
| **P → C** | **host** (device + stack held) | **660/660 = 100%** | **0.0000** | **0** | **0** | **0** |
| B → C | **library stack** (host + device held) | 15/660 = 2.3% | 0.2008 | 1 | 0 | **3** |
| C → G | **device, CPU→CUDA** (host + stack held) | 4/660 = 0.6% | 0.1956 | 3 | **1** | **3** |

**Host contributes exactly nothing.** Two different machines — an LXC container
on one site, a desktop on another, different CPUs — produce **byte-identical
scores on all 660 articles** once the library versions match. Even the python
patch level differs (3.11.2 vs 3.11.15) and it does not matter.

**The library stack is worth 3 verdict flips at 4.5** and 0 at 4.0.
**CUDA is worth 3 flips at 4.5 and 1 at 4.0** — so the device is if anything the
slightly larger term, and it is the one that reaches the *deployed* op-point.

**It is the same three articles every time** — `east_african_fana_bc_…`,
`german_deutschlandfunk_…`, `global_south_global_voices_…` — moving in whichever
direction the perturbation pushes them. They are not merely "the rows nearest the
cut": of 18 production rows in [4.30, 4.50) only these 3 move, while one at
4.4870 — *closer* to the threshold — never does. They are three specifically
fragile articles, and a perturbation of any kind moves them across 4.5.

## What this overturns

1. **"You cannot clear a box by pinning its library versions" — REFUTED, and it
   was my own rule.** You can, completely. It is the single most effective lever
   available: it took a box from 2.3% bit-identical to 100%.
2. **"b650 is cleared at 4.0 and NOT at 4.5" (2026-08-09) — true of the
   configuration measured, and now fixable.** That b650 ran a mismatched stack.
   On production's pins, on CPU, b650 is cleared at **every** threshold, exactly.
3. **The residual is NOT hardware/kernel-level.** It is library versions plus
   CPU-vs-CUDA, and both are under our control.

**What survives unchanged:** *a box is cleared at a threshold, never in general*
— the C→G row is the proof, since CUDA is clean at 4.0 and not at 4.5. The rule
is now sharper: **a box is cleared for a (stack, device, threshold) triple.**

## What it means operationally

> ### ⛔ CORRECTED 2026-08-29 — this section drew the wrong conclusion from its own table
>
> It said b650-on-CPU was *"a production-exact measuring instrument"* whose numbers
> *"can be quoted for production without qualification"*, and told the reader to
> *"confirm on CPU"*. **Run P is labelled `gpu-server | CPU`. Its venv is
> production's; its device is this study's control.** Production serves on GPU
> (`memory/filter-status.md`, `memory/project_session_2026_08_09_night.md`), so what
> P→C establishes is b650-CPU ≡ gpu-server-**CPU**, not ≡ production.
>
> The measurement table above is unaffected and correct. This was an operational
> conclusion read off an **arm label**, and it propagated: it is where
> llm-distillery's `memory/b650-gpu.md` got the same wrong sentence, which stood
> until 2026-08-29.

- **b650 on `venv-prodparity`, CPU, reproduces gpu-server-on-CPU exactly** — 660/660,
  0 flips at every threshold. That is a real result: it removes the "only free between
  pipeline cycles" constraint for any question where the *device* is held fixed on both
  sides.
- **To compare against stored production output, match production's device (GPU).**
  b650-CUDA + `venv-prodparity` is the configuration that matches gpu-server on both
  axes. ⚠️ **Nobody has measured gpu-server-CUDA against b650-CUDA** — the host term is
  0.0000 with the device held at CPU, and these four runs do not contain production's
  own configuration. Treat CUDA-to-CUDA host equivalence as an extrapolation.
- **CPU vs CUDA on the student is now measured**, and it is the axis that matters:
  max |Δ| **0.1956**, 3 rows above the #95 floor, 1 verdict flip at the deployed
  op-point. **Production serves on GPU, while `ground_truth_gate.json` and the
  whole #102 sweep were measured on CPU** — so the deployed numbers carry this
  term. That is a new open question, not answered here.
- **`sadaltager` should need the same `uv python install` fix.** Untested.

## How the venv was built (no sudo needed)

b650's GPU was unusable since commissioning: triton's helper compile dies on
`Python.h: No such file or directory`, and `sudo` needs a password. The venv was
built on the *system* python (`pyvenv.cfg` → `home = /usr/bin`), which ships no
headers — but `uv 0.12.0` was already installed and can fetch a standalone
CPython that does:

```bash
uv python install 3.11          # ships include/python3.11/Python.h
uv venv ~/llm-distillery/venv-prodparity --python 3.11
# torch from the cu130 index, then the inference subset — exact commands in the
# header of constraints/production-gpu-server.txt
```

The old `venv/` is untouched, because the 2026-08-09 dumps cite it as provenance.

**"Production's stack" means the twelve named ML packages**, which match exactly.
A full freeze still differs in **13 of 58** shared packages (`fsspec` 2026.4.0 vs
2026.1.0, `cuda-bindings`, `cuda-pathfinder`, `filelock`, `regex`, `tqdm`,
`certifi`, `hf-xet`, `idna`, `packaging`, `anyio`, `annotated-doc`,
`typer-slim`). Since P→C is bit-identical, **none of those 13 affects the
student** — worth knowing before anyone spends effort closing that gap.

**A defect in the constraints file, found by using it:** its header documented
`pip install -r requirements.txt -c constraints/production-gpu-server.txt`, and
that command **cannot succeed**. `requirements.txt` needs
`datasets>=2.14.0,<3.0.0`, every version of which caps `fsspec<=2024.6.1`, while
the constraints file itself pins `fsspec==2026.1.0` — and a `-c` file is a pin.
Production's serving venv has **no `datasets` at all** (it is a serving
environment; `datasets` is a training dependency), which is why the conflict never
surfaced there. *(An earlier draft blamed torch for the fsspec pin. It does not —
`torch-2.11.0` declares `fsspec>=0.8.5`, verified from the installed wheel
metadata. uv's error text folds the constraint into the torch line, which is what
misled me.)*

## The proximity control (unchanged, and still load-bearing)

Of the **18** production rows in `[4.30, 4.50)`, exactly **3** flip, and the same
3 in every configuration:

| production | b650 CPU / new stack | b650 GPU / prod stack | article |
|---|---|---|---|
| 4.4919 | **4.5386 ↑** | **4.5386 ↑** | `east_african_fana_bc_…` |
| 4.4870 | 4.4870 | 4.4430 | `danish_dr_nyheder_…` — **closer to the cut, does not flip** |
| 4.4840 | 4.4779 | 4.4779 | `biotech_pharma_genetic_engineering_news_…` |
| 4.4667 | 4.4667 | 4.4667 | `south_african_daily_maverick_…` |
| 4.4140 | **4.5427 ↑** | **4.5311 ↑** | `german_deutschlandfunk_…` |
| 4.3919 | **4.5340 ↑** | **4.5394 ↑** | `global_south_global_voices_…` |

**Two overstatements from the first draft, corrected.** (a) The flippers move
**+0.047 to +0.148**, not "+0.13 to +0.15" — `east_african_fana_bc` moves only
+0.047 and flips because it starts at 4.4919, not because it moves far. (b)
*"their immediate neighbours are bit-stable"* is **false**: six of the 15
non-flippers move ≥0.04, and `balkan_index_hr` moves **+0.168 on the GPU run,
more than any flipper**. And `global_south_global_voices` sits below **nine**
non-flippers, not the five first claimed.

At 4.0 the same window is clean: of **17** production rows in `[3.80, 4.00)`,
**0** flip in any configuration.

## Reproduce

```bash
# C (the run that settles it) — CPU, production pins
ssh b650-gpu 'cd ~/llm-distillery && CUDA_VISIBLE_DEVICES="" HF_HUB_OFFLINE=1 \
  PYTHONPATH=$HOME/llm-distillery ~/llm-distillery/venv-prodparity/bin/python \
  /tmp/parity/box_parity.py --fit-calibration /tmp/parity/fit_calibration.py \
  --filter ~/llm-distillery/filters/uplifting/v7 \
  --data ~/llm-distillery/datasets/training/uplifting_v7/test.jsonl \
  --out /tmp/parity/preds-b650-CPU-prodstack.jsonl'

# the decomposition — change ONE thing per comparison
D=datasets/parity/uplifting_v7_test660
for pair in "${D}_gpuserver-serving-venv_2026-08-09.jsonl:${D}_b650-CPU-prodstack_2026-08-10.jsonl" \
            "${D}_b650_2026-08-09.jsonl:${D}_b650-CPU-prodstack_2026-08-10.jsonl" \
            "${D}_b650-CPU-prodstack_2026-08-10.jsonl:${D}_b650-GPU-prodstack_2026-08-10.jsonl"; do
  PYTHONPATH=. python scripts/verification/diff_box_parity.py \
    --a "${pair%%:*}" --b "${pair#*:}" \
    --labels datasets/training/uplifting_v7/test.jsonl \
    --calibration filters/uplifting/v7/calibration.json \
    --repo-root . --threshold 4.0 --alt-threshold 4.5
done
```
