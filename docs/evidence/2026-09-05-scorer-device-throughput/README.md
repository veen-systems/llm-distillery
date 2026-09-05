# Scorer throughput by device — measured properly, and the first attempt measured CUDA twice

**2026-09-05. $0**, GPU time on `b650-gpu` only. Run because the owner asked whether the
CPU/GPU usage experiments for the scorers had actually been **logged**. They had not, in four
specific ways, and fixing that turned up a defect in shipped code.

Reproduce — ⛔ **one arm per process, and that is not tidiness** (see §2):

```bash
for A in e5small-probe-gpu e5small-probe-cpu e5large-encoder-gpu student-gpu; do
    PYTHONPATH=. HF_HUB_OFFLINE=1 venv/bin/python bench_devices.py \
        --arm $A --out /tmp/a_$A.json
done
```

Runs on `b650-gpu` (the split and the v8 weights are there; both are gitignored, #97).

---

## 1. What was and was not logged before

**Logged:** `EXP-019` carries five device metrics (e5-small 3.74 GPU / 47.2 CPU, e5-large
26.79 GPU / 511.2 CPU, student 43.70 GPU); `EXP-021` carries production's 18.08 ms/article on
gpu-server.

**Not logged, four ways:**

1. `benchmark_throughput.py` was cited as an artifact by **no** registry entry.
2. **No output was ever retained.** The figures survived only as prose in a markdown file —
   they passed the registry's greppable-metric check by appearing in a *document*, not by
   having a *run* behind them.
3. Host, device, batch size and load-exclusion lived only in the script's **docstring**, never
   in `EXP-019`'s `population` — against this repo's own *always name the device* rule.
4. **n = 1 per arm.** No spread, on a quantity whose spread turns out to be the whole story.

⛔ **And the e5-large arms cannot be reproduced at all.** Those probes were trained during
EXP-018/019 and never retained: the only `.pkl` for this filter on `b650-gpu` is the shipped
`embedding_probe_e5small.pkl`. e5-large is therefore measured here **encoder-only** and
labelled as such — **not the same quantity** as a full probe pass.

## 2. ⛔⛔ The first attempt reported CUDA as CPU, and the only tell was that it agreed

Running the GPU and CPU arms in one process gave:

| arm | reported |
|---|---|
| e5-small probe, GPU | 2.34 ms/article |
| e5-small probe, CPU | **2.37 ms/article** |

`EmbeddingStage` caches loaded models in a class-level dict keyed on the **model name alone**
(`filters/common/embedding_stage.py:112`, read back at `:213`). A second
`EmbeddingStage(..., device="cpu")` for the same model silently reuses the CUDA-resident
object, while `self.device` still reads `"cpu"`. **The object and its label disagree, and
nothing raises.**

⭐ **The number was not imprecise — it was the wrong device.** Measured properly, CPU is
**42.41 ms/article**, 18× slower. Had the two devices differed by 20% instead of 20×, I would
have published it. Filed as **llm-distillery#146**; the cache is shared across the repo
boundary — `NexusMind/src/preprocessing/story_dedup.py:861` reads and writes the *same* dict —
so two components in two repos each believe they choose the device. ⚠️ **Latent, not live**:
checked, and no two current consumers share a model name (filters e5-small, dedup e5-large,
detectors mpnet).

Each arm now runs in its own interpreter, and the script **reads the device back off the
loaded model** rather than trusting the flag it passed.

## 3. The measurements

`b650-gpu` (RTX 3090 Ti, 8 CPU threads), 660-row v8 test split, batch size 64, **model load
excluded** via a warm-up pass, one arm per process.

| arm | median ms/article | repeats | within-run spread | device, read back |
|---|---|---|---|---|
| e5-small probe, GPU | **2.332** | 5 | 0.57% | `cuda:0` |
| e5-large encoder-only, GPU | **16.324** | 5 | 0.61% | ⚠️ not verified |
| student, GPU | **24.733** | 3 | 0.03% | ⚠️ not verified |
| e5-small probe, CPU | **42.409** | 3 | 0.17% | `cpu` |

⚠️ **The device read-back only covers arms that go through `EmbeddingStage`.** The
encoder-only and student arms construct their models directly, so for those the device is a
*request*, not a verified fact — the same gap that produced §2, disclosed rather than closed.

⚠️ Not run: e5-large on CPU (511 ms/article × 660 ≈ 5.6 min/repeat) and the student on CPU
(~1.5 s/article ≈ 16 min). Neither is a production configuration — gpu-server has
`require_gpu: true` and no CPU fallback.

## 4. ⭐⭐ The finding that matters: the repeats were in the wrong place

Within one process the arms are almost perfectly stable — **0.03% to 0.61%** spread. Between
sessions, on the same box, with the same script shape and the same batch size:

| arm | 2026-09-04 (n=1) | 2026-09-05 (median) | ratio |
|---|---|---|---|
| e5-small probe, GPU | 3.74 | **2.332** | **1.60×** |
| e5-small probe, CPU | 47.2 | **42.409** | 1.11× |

**Within-run spread understates the real uncertainty by two orders of magnitude.** A number
quoted to three significant figures from five repeats inside one process is not precise to
three significant figures — it is precise about one process.

⛔ **So the honest reading of the 2026-09-04 timings is not "wrong", it is "n=1 with no band",
and the band is wide.** What changed between the two sessions was not identified: same box,
same batch, same rows, load 0.00 today. Clocks, thermal state and other users are candidates;
none was measured, and I am not going to name a cause I did not establish.

⚠️ The other two arms are **not** comparable across sessions and are excluded from that table
on purpose: e5-large was a full probe yesterday and is encoder-only today, and the student's
43.70 was not produced by `benchmark_throughput.py` at all — that script only ever built an
`EmbeddingStage` — so its provenance is unknown.

## 5. ⭐ What survives: the ratios, which is what the old evidence actually relied on

`benchmark_throughput.py` asserted *"ratios should travel; absolute numbers may not."* Now
measured rather than asserted:

| quantity | 2026-09-04 | 2026-09-05 | travels? |
|---|---|---|---|
| student ÷ e5-small probe, GPU | 11.68× | **10.61×** | ✅ within 10% |
| two-stage break-even routing `r*` | 0.5275 | **0.5657** | ✅ within 8% |
| CPU ÷ GPU, e5-small probe | 12.62× | **18.19×** | ⛔ **44% apart** |

**The ratio the conclusions rest on travels; the CPU/GPU ratio does not.** The claim *"on GPU
the probe is 11.7× cheaper than the student"* reproduces at 10.6× and is safe. Any statement
of the form *"CPU is N× slower"* is not.

### The EXP-020 conclusions are unchanged

Recomputed on today's numbers: two-stage at the adopted 89% routing costs
`2.332 + 0.89 × 24.733 = 24.34 ms` against `24.733 ms` for student-on-everything — a **1.57%**
saving (2.5% yesterday). Break-even is **56.6%** routing (52.7% yesterday). Same conclusion,
same direction: the screen barely earns its keep at the adopted threshold, and that is a cost
the hold-near-pass-through ruling knowingly accepted.

⚠️ **b650-gpu is not gpu-server**, and this is the point of §5 rather than a footnote:
production's own end-to-end figure is **18.08 ms/article** (`EXP-021`, 146,433 articles). Use
the ratios here; do not quote the absolutes as production.
