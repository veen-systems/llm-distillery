# Scorer throughput by device — and five things this document itself got wrong

**2026-09-05. $0**, GPU time on `b650-gpu` only. Run because the owner asked whether the
CPU/GPU experiments for the scorers had actually been **logged**. They had not, in four
specific ways. Fixing that turned up a defect in shipped code — and then a four-lens review
found five defects in this document, one of which was **losing an artifact that existed**.

⚠️ **Read §6 before quoting anything here.** The first published version of this file
(commit `b94fa01`) is wrong in five places and the corrections are the most useful part.

Reproduce — ⛔ **one arm per process, and that is not tidiness** (§2):

```bash
D=docs/evidence/2026-09-05-scorer-device-throughput
for A in e5small-probe-gpu e5large-probe-gpu e5large-encoder-gpu student-gpu e5small-probe-cpu; do
    PYTHONPATH=. HF_HUB_OFFLINE=1 venv/bin/python $D/benchmark_devices.py \
        --arm $A --out $D/$A.json
done
python $D/benchmark_devices.py --merge $D --out $D/devices.json
```

---

## 1. What was and was not logged before

**Logged:** `EXP-019` carries five device metrics. `EXP-021` carries production's figures.

**Not logged, four ways:** the script was cited by **no** registry entry; **no output was ever
retained**; host/device/batch/load-exclusion lived only in a docstring; and **n = 1 per arm**.

⚠️ **A fifth, which the review corrected:** I also wrote that the e5-large probe head had
*"never been retained"*. **It had.** See §6a.

## 2. ⛔ The first attempt reported CUDA as CPU

Running the GPU and CPU arms in one process gave e5-small **GPU 2.34** and **CPU 2.37**
ms/article. `EmbeddingStage` caches models in a class-level dict keyed on the **model name
alone** (`filters/common/embedding_stage.py:112`, read back at `:214`), so a second
`EmbeddingStage(..., device="cpu")` reuses the CUDA-resident object while `self.device` still
reads `"cpu"` — and `self.device` *is* honoured at `:195` and `:284`, so half the object obeys
the flag and nothing raises. True CPU is **42.5 ms**, 18× slower. Filed **llm-distillery#146**.

Each arm now runs in its own interpreter, the script **reads the device back off the loaded
model**, and — since `b94fa01` — **asserts** it matches the arm and refuses otherwise.

⚠️ **Latent, not live, and my first statement of why was false.** I wrote *"no two current
consumers share a model name"*; **fourteen** filter configs name `multilingual-e5-small`. The
latency is on the **device** axis: no filter passes `device`, so all resolve identically at
`:141-142`. The claim is about `(name, device)` pairs. NexusMind's gpu-server keeps up to
**3** filter scorers in one process, so name-sharing happens every production cycle.

## 3. The measurements

`b650-gpu` (RTX 3090 Ti, 8 threads), 660-row v8 test split, **batch 64**, model load excluded,
one arm per process, device read back off the object and asserted.

| arm | median ms/article | repeats | spread | device |
|---|---|---|---|---|
| e5-small probe, GPU | **2.345** | 15 | 1.13% | `cuda:0` |
| **e5-large probe, GPU** | **16.417** | 5 | 0.72% | `cuda:0` |
| e5-large encoder-only, GPU | 16.514 | 5 | 0.45% | `cuda:0` |
| student, GPU | **24.740** | 3 | 0.01% | `cuda:0` |
| e5-small probe, CPU | **42.541** | 3 | 0.12% | `cpu` |

⭐ **The probe head is free**: full e5-large probe 16.417 against encoder-only 16.514 —
**−0.097 ms** (`-0.097`), i.e. inside the noise. Worth stating because §6a's error was *justified* by an
encoder-only substitution that turns out not to have mattered numerically.

⚠️ Not run: e5-large CPU and the student on CPU (~5.6 and ~16 min per repeat). Neither is a
production configuration — NexusMind's **pipeline** skips a cycle without a GPU
(`config/app.yaml:82` `require_gpu: true`, read by `scripts/main.py`). ⚠️ That is the
pipeline's property, not gpu-server's: the scorer app itself has a CPU path
(`deploy/gpu-server/main.py:761`).

## 4. ⭐⭐ The variance is arm-specific, not a session effect

The first version of this document said the arms were stable to **0.03–0.61%** within a run
and that the between-session difference was a machine-state effect. Both halves were too
confident. Three runs of `e5small-probe-gpu`, same box, same day:

| run | median | spread |
|---|---|---|
| 1 | 2.332 | 0.57% |
| 2 | **4.746** | 1.33% |
| 3 (15 repeats) | 2.345 | 1.13% |

**Runs 1 and 3 agree to 0.6%; run 2 is 2.04× off.** Meanwhile `student, GPU` and
`e5-small probe, CPU` reproduce across the same runs to **0.03%** and **0.31%**.

⭐ **So it is not the box having a slow day — it is the short arm.** The e5-small GPU arm is
~1.5 s of work; the student is ~16 s and the CPU arm ~28 s, and those two are stable. ⚠️ Run 2
was taken while a review agent was independently benchmarking the same GPU, which makes
**contention** the leading candidate. ⛔ **Not established** — I did not log clocks or
utilisation alongside, and I am not claiming a cause. Registered as **H-V8-21** with a method
and a stated falsifier.

⚠️ I also saw within-run spreads of **32%** and **111%** on the e5-large arm in other runs. So
"0.03–0.61%" was a property of four quiet processes, **not of the arms**.

## 5. Ratios, and what they are worth

| quantity | 2026-09-04 | 2026-09-05 | |
|---|---|---|---|
| student ÷ e5-small probe, GPU | 11.68× | **10.55×** | 9.7% apart |
| two-stage break-even routing `r*` | 0.5275 | **0.5688** | 7.8% apart |
| CPU ÷ GPU, e5-small probe | 12.62× | **18.14×** | 44% apart |

⚠️ **Percentages are relative to the 2026-09-04 value.** ⛔ **And the first two rows are not
batch-matched**: 09-04 measured the CPU arm at batch **32** and the student at batch **16**,
today's are all batch **64**. Re-running the original 09-04 scripts unchanged today gives
e5-small GPU 2.33–2.34, student 25.8 (batch 16), CPU probe 38.7 (batch 32) — so **the same
script at the same batch reproduces today's number, not yesterday's**, which eliminates script
shape and batch as the cause of the session difference. Batch-matched, student ÷ probe is
**11.07× vs 11.68×, 5.2% apart** — better than the table shows.

⭐ **`r*` is now a like-for-like comparison** (full e5-large probe on both sides), which it was
not when this file first published it.

### EXP-020's conclusions are unchanged

Two-stage at the adopted 89% routing: `2.345 + 0.89 × 24.740 = 24.36 ms` against **24.740** —
a **1.52%** saving (**2.44%** on the same arithmetic in EXP-019; its prose says 2.5%, computed
off a rounded 42.6 ms). Break-even **56.9%** routing (EXP-020 published 52.7%, a truncation of
0.5275 → 52.8%). Same conclusion: the screen barely earns its keep at the adopted threshold.

⚠️ **b650-gpu is not gpu-server.** Production's figure is **18.08 ms/article of model compute**
and **21.36 ms of wall** (`EXP-021`) — the first version of this file called 18.08 "end-to-end",
which understates production by 15% and mislabels the one number readers are told to trust.

## 6. ⛔⛔ What the review found in this document

Four lenses, run *after* `b94fa01` was committed and pushed. The mechanical battery — 667
tests, refcheck, the registry checker, both budget guards, 21/21 verify annotations, the
structural check — was **green throughout and found none of it.**

### 6a. ⭐⭐ "The e5-large probe was never retained" — it was, and I nearly let it be deleted

The probe head was at `b650-gpu:/tmp/probe_e5large.pkl` (1,211,967 B, `input_dim: 1024`,
`output_dim: 6`) the entire time. My search was `find /home/jeroen -maxdepth 8 -name "*.pkl"`,
which cannot reach `/tmp`. ⛔ **I pointed the instrument somewhere that could not produce a
positive and published the negative** — this repo's first working rule, inside a document
about instruments that cannot say what they claim.

⛔ **And it was not one file. Eleven probes were in that `/tmp`**, including both EXP-019
regression heads (`probe_reg_small`, `probe_reg_large`), the seed-sensitivity pair
(`probe_seed42`, `probe_seed7`) and four per-filter recall probes. On a box with 36 days of
uptime, one reboot from gone. **All copied to `~/llm-distillery/rescued_probes/`** with
sha256s recorded in `rescued_probes_manifest.txt`. ⚠️ **They are still only on b650 and are not
in git — that is a decision for the owner, not something to do silently.**

Consequences: the encoder-only substitution was unnecessary; "not reproducible without
retraining" was false; and `r*` was needlessly confounded. **Numerically it changed almost
nothing** (§3) — which is the uncomfortable part, because a harmless-looking substitution is
exactly what stops anyone re-checking the premise.

### 6b. The encoder arm truncated 27.7% of the corpus

It built `f"query: {title} {content}"[:4000]`; no consumer does that —
`EmbeddingStage._prepare_text` uses `f"{title}\n\n{content}"` untruncated and without the
prefix, and 27.7% of the split exceeds 4000 chars (median 2463, p90 6527, max 76768). Now uses
the consumer's own text. ⚠️ The reviewer measured a **1.70×** effect from this; on the fixed
instrument I measure **~1%** (16.514 untruncated vs 16.32–16.43 truncated). **I have not
reconciled the disagreement** and, given §4, contention is a plausible explanation for either.
Reporting both rather than picking.

### 6c. Three claims that were simply false

- *"The student's 43.70 provenance is unknown."* It is `b650-gpu:~/llm-distillery/bench.py`
  plus `logs/bench.log` — two commands on the box the experiment ran on, in a document whose
  subject is provenance.
- *"The only tell was that the two numbers agreed."* At least three others were available, and
  the first is damning: **`EXP-019` already recorded e5-small CPU at 47.2 ms**, a 20×
  disagreement with the 2.37 reading, written down in the very registry this work was
  repairing. Honest form: *the only tell I used*.
- *"No two current consumers share a model name"* — §2.

### 6d. `device_verified` was recorded and never asserted

It was written into the JSON and never compared against what the arm asked for, so any future
all-arms wrapper would re-create #146 exactly: the CPU arm would record `["cuda:0"]`, print a
number and exit 0. **A field that is written and never checked is a report, not a guard.** Now
raises. Also fixed: `--gpu-repeats`/`--cpu-repeats` were inert for the student and
e5-large-CPU arms (hardcoded 3 and 1) — the same "flag that parsed and did nothing" shape as
`#145`, shipped one commit after logging it.

### 6e. The reproduce command did not run

It named `bench_devices.py` (the working copy's name on b650, not the committed
`benchmark_devices.py`) and wrote to `/tmp/a_$A.json`, matching no committed artifact. And
`devices.json` was a hand-merge no command produced; `--merge` now generates it and refuses to
combine arms measured under different environments.

## 7. What `EXP-022` published, kept verbatim

⛔ **Not tidiness — the registry checker demanded it, and it was right.** Rewriting this file
made nine of `EXP-022`'s metrics untraceable to any artifact, which is precisely the failure an
append-only registry exists to prevent: the entry recording what was believed survived, and the
evidence behind it did not. **A superseded entry needs its numbers to stay readable somewhere.**

Measured 2026-09-05 in the runs `EXP-022` reports, before the instrument was fixed:

| arm | EXP-022 | now (`EXP-023`) | why it moved |
|---|---|---|---|
| e5-small probe, GPU | 2.332 | 2.345 | same arm, more repeats — agrees |
| e5-small probe, CPU | 42.409 | 42.541 | agrees |
| student, GPU | 24.733 | 24.740 | agrees |
| e5-large **encoder-only**, GPU | 16.324 | 16.514 | truncation removed (§6b) |
| e5-large **full probe**, GPU | *not measured* | **16.417** | the probe existed (§6a) |

Derived figures as `EXP-022` published them: student ÷ probe **10.61**, CPU ÷ GPU **18.19**,
break-even **0.5657**, two-stage saving **1.57%**, and the cross-session ratios **1.60** and
**1.11** for e5-small GPU and CPU. ⚠️ **The two cross-session ratios are not batch-matched**
(§5) and the break-even was encoder-only on one side.

---

---

## What to take from this

⭐ **The arm ratios are the durable output; every absolute here needs a band.** student ÷ probe
travels; the CPU/GPU ratio does not; and the same arm can move 2× between two runs an hour
apart. ⛔ **And the document's own error rate is the finding that generalises**: six defects
across two commits, none caught by a green mechanical battery, four of them found only because
a reviewer went and *looked on the machine* instead of reading the code.
