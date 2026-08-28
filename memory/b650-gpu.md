# b650 GPU (Arian's box)

Commissioned 2026-07-30. RTX 3090 Ti **24 GB** (vs gpu-server's 16), CUDA 12.0
driver 580.95, 699 GB free disk, 30 GB RAM. Reachable via Tailscale:

```bash
ssh b650-gpu        # account is `jeroen` (NOT jwasys); works from situla and sadalsuud
```

- **sudo password**: in owner's Bitwarden (initial photo'd one is dead).
- **venv**: **two now.** `~/llm-distillery/venv-prodparity` (py 3.11.15, torch
  2.11.0+cu130, transformers 5.0.0 — production's pins, **GPU works**) is the one
  to use for anything touching the student; `~/llm-distillery/venv` (py 3.12.3,
  torch 2.13.0, **CPU only** — triton cannot build) is kept because the
  2026-08-09 parity dumps cite it as provenance. Both created with **uv**
  (`~/.local/bin/uv`);
  system `python3 -m venv` is BROKEN (no ensurepip; python3.12-venv needs sudo).
  Stack: torch 2.13.0+cu130, sentence-transformers 5.6.1, **scikit-learn pinned
  1.8.0** (matches obituary pickle version).
- **Ollama**: 100.87.225.76:11434 over tailnet (qwen3:14b, qwen3-coder:30b,
  qwen2.5:14b pulled; NO gemma3:27b/phi4 yet — pull before running 4-model panels here).
- **Data staged**: `~/llm-distillery/filters/common/obituary_detector/` —
  training corpora (131 MB) + v3/v4/v5 model artifacts + train_v1.py/build_v5_seed.py.
- **Benchmark**: 1,562-row mpnet embed in 1.9 s (~830 rows/s) — ~5× gpu-server.
- ⚠️ **Cross-box score skew — NOW SCOPED, do not apply it blanket** (2026-08-09).
  The |0.16| was measured on the **obituary detector: mpnet + sklearn MLP**, ST
  5.6.1 here vs 5.2.2 on gpu-server (gotcha-log 2026-07-30). It does **NOT**
  generalise to the Stage-1 **e5-small + torch MLP** probe path: same 160
  articles, same pickle, the real `filters/common/embedding_stage.py` class,
  b650 vs gpu-server's *serving venv* gave **max |Δ| 4.2e-6, zero screening
  flips at 0.75/1.0/1.25/1.5/2.85/3.25, bit-identical embedding checksums** —
  smaller than the serving venv's own CPU-vs-CUDA difference (5.4e-6). **b650 is
  therefore cleared to train e5 probes for gpu-server.** The harness is
  `scripts/verification/box_parity.py` + `diff_box_parity.py` (written 2026-08-09
  night; before that "the parity harness" was referenced here but did not exist).
- ⚠️ **The Gemma-3-1B student is NOT probe-clean — a box is cleared AT A
  THRESHOLD, never in general** (measured 2026-08-09 night, uplifting v7's 660
  held-out rows, b650 vs gpu-server's serving venv, everything but the
  interpreter md5-identical). At the **4.0** op-point the boxes agree completely:
  **0 verdict flips**, identical confusion matrix, so
  `filters/uplifting/v7/ground_truth_gate.json` is production's number. But only
  **2.3% of rows are bit-identical**, calibrated weighted |Δ| runs p50 0.0000 /
  p90 0.0345 / p99 0.1198 / **max 0.2008 — above the #95 0.16 floor**, and at
  **4.5** three rows flip, splitting specificity 0.9730 (gpu-server) vs 0.9662
  (b650). **Do not measure a threshold on b650 without re-running the harness at
  that threshold.** The p50 of exactly 0.0000 is a trap: raw logits are
  bf16-quantised (~0.03 steps), so most disagreements are hidden, not absent.
  ⛔ **CORRECTED 2026-08-10, and the correction did not reach this bullet until
  2026-08-29: none of the 0.2008 is the BOX.** The 08-09 run had the stacks
  unmatched. The four-run decomposition
  (`docs/evidence/2026-08-10-b650-gpu-production-stack-parity.md`) isolates each
  term: **host alone is 660/660 bit-identical, max |Δ| 0.0000**; the 0.2008 is the
  **library stack**; and **CPU→CUDA — the "still unmeasured" line below — is now
  measured at 0.1956, 1 flip at 4.0 and 3 at 4.5**, making the device the term that
  reaches the deployed op-point. **Pin production's versions and b650 IS
  gpu-server**; the threshold caveat now attaches to the stack and the device, not
  to the machine. Full records:
  `docs/evidence/2026-08-09-cross-box-parity-uplifting-v7.md` (stack, confounded as
  "cross-box") and the 08-10 decomposition (all four terms).
- ✅ **SOLVED 2026-08-10 — b650 runs the student on GPU. Use
  `~/llm-distillery/venv-prodparity`.** ~2 min per 660 rows, vs ~16 min on CPU
  here and ~30 on gpu-server's CPU. **No sudo was needed.** The old venv is built
  on the *system* python (`pyvenv.cfg` <!-- placeholder --> → `home = /usr/bin`), which ships no
  headers; `uv` can download a standalone CPython that does:
  ```bash
  uv python install 3.11                                    # ships include/python3.11/Python.h
  uv venv ~/llm-distillery/venv-prodparity --python 3.11
  # then torch from the cu130 index, then the inference subset -- exact commands
  # in the header of constraints/production-gpu-server.txt
  ```
  Built to production's frozen versions **for the named ML packages** — a full
  freeze still differs in 13 of 58 transitive deps (`fsspec`, `cuda-bindings`,
  `cuda-pathfinder`, …), so do not call it identical. (torch 2.11.0+cu130, transformers
  5.0.0, peft 0.18.1, numpy 2.4.2, sklearn 1.8.0). The old `venv/` is untouched,
  because the 2026-08-09 parity dumps cite it as provenance.
  **On CPU with these pins, b650 is bit-identical to production: 660/660 rows,
  0 verdict flips at every threshold.** It is a production-exact measuring
  instrument — quote its numbers without qualification. **On GPU it is not**: 1
  flip at 4.0 and 3 at 4.5, so use CUDA for speed (~2 min vs ~16) and confirm on
  CPU before quoting an op-point number. Decomposed one variable at a time: host
  contributes **nothing**, the library stack is worth 3 flips at 4.5, CPU→CUDA is
  worth 3 at 4.5 and 1 at 4.0.
  ⛔ **The concrete act to avoid: diffing ANY b650 replay against STORED PRODUCTION
  SCORES without first matching production's device.** **Production serves on GPU**
  (`memory/filter-status.md`, `memory/project_session_2026_08_09_night.md`), so the
  comparable b650 configuration is **CUDA + `venv-prodparity`** — run **G**'s shape,
  not run C's. A b650 **CPU** replay diffed against stored production output crosses
  the device term, the larger of the two and the one that reaches 4.5.
  ⚠️ **And even the CUDA comparison is an EXTRAPOLATION, not a measurement.** The
  host term is 0.0000 — but it was measured with the device held at **CPU** (P→C).
  Nobody has run gpu-server on CUDA against b650 on CUDA. The four runs do not
  contain production's own configuration.
  ⛔ **This bullet said the exact opposite for one commit (`b7b1d6d`, corrected the
  same day) — "production scoring is gpu-server on CPU (run P), so a CPU replay is
  exact and needs no qualification."** It would have licensed precisely the
  comparison the device term forbids. The mechanism is worth more than the fix:
  **run P is labelled `gpu-server | CPU`, and I read an experiment's ARM LABEL as a
  description of production.** P's *venv* is production's; P's *device* is the
  study's control. An arm label describes what was held fixed to isolate a term, and
  says nothing about what production does. Caught by the NexusMind session; confirmed
  here against this repo's own two records, which had said "production serves on GPU"
  all along.
  ⚠️ **"Production parity" names a HOST here, and there is more than one candidate.**
  `venv-prodparity` is built to **gpu-server's** pins — the box that scores the
  student — **not sadalsuud's**, which runs the pipeline. The two are different
  stacks, and the stack is worth 3 flips at 4.5, so parity with one is not parity
  with the other. (Raised 2026-08-29 by the NexusMind session, which found its own
  b650 memory recorded the sadalsuud target; this repo's is gpu-server, per run P.)
  *(An intermediate note here said pinning made agreement WORSE and that the
  residual was hardware-level. That was confounded — it compared a mismatched-stack
  CPU run against a matched-stack CUDA run. The opposite is true.)*
  `docs/evidence/2026-08-10-b650-gpu-production-stack-parity.md`.
  **`sadaltager` is predicted to need the same fix; untested.**
- 🗄️ **Historical — why the GPU was blocked (superseded by the entry above).**
  *(Diagnosis corrected 2026-08-09 evening; the original note below was wrong.)* torch 2.13 JITs a triton kernel,
  triton compiles its `cuda_utils` helper at first use, and that gcc call dies on:
  `cuda_utils.c:9:10: fatal error: Python.h: No such file or directory`.
  **`python3.12-dev` is not installed** (`/usr/include/python3.12` does not
  exist) — same missing-dev-package family as the broken `python3 -m venv`
  noted above. CUDA is fine: `libcuda.so.1` and the dev symlink `libcuda.so` are
  both in `/lib/x86_64-linux-gnu` and in `ldconfig -p`, and
  `gcc -shared -fPIC -l:libcuda.so.1 -L…/triton/backends/nvidia/lib` links a
  trivial object with exit 0. The earlier "gcc cannot link libcuda.so.1" reading
  came from the tail of the `CalledProcessError` (which prints the command line,
  ending in the `-l:libcuda.so.1` flag) rather than from gcc's own stderr — the
  fatal-error line is further up the traceback.
  **Fix as originally proposed (needs sudo, NEVER RUN — the uv route above
  solved it without root):** `sudo apt install python3.12-dev`. Repro in ~10 s:
  ```bash
  ssh b650-gpu '~/llm-distillery/venv/bin/python /tmp/tk.py'   # trivial triton kernel
  ```
  (write `/tmp/tk.py` as a *file* — a `python -c` heredoc fails differently,
  `ValueError: @jit functions should be defined in a Python file`, which is an
  artefact of the test and not this bug.)
  The old CPU workaround (`CUDA_VISIBLE_DEVICES=""`) took ~16 min per 660
  articles, not the ~7 first recorded here. The e5 probe path never JITs a triton kernel, which is
  why probe work runs clean on GPU here regardless.
- ⚠️ **Read the venv, not `which python3`.** gpu-server's *system* python is a
  different stack (torch 2.5.1+cu124, ST 5.2.3, **no peft**) from the one systemd
  starts (`/home/hcl/gpu-server/nexusmind-scorer/venv`: torch 2.11.0+cu130, ST
  5.2.2, peft 0.18.1). Numbers were published off the wrong one on 2026-08-09 and
  had to be redone. Same on sadalsuud — the pipeline runs
  `~/local_dev/NexusMind/venv` (sklearn 1.8.0, ST 5.6.0); system python has
  nothing installed.
- Purpose: training node (ends Ollama-vs-training contention on gpu-server).
  First planned job was obituary v6 (LD#85, now parked).
