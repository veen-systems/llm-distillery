# b650-gpu — archive (verbatim moves from `memory/b650-gpu.md`; #163)

## Moved 2026-10-19 (#163 round 11). Verbatim.

### From § `~/llm-distillery` IS A GIT CHECKOUT as of 2026-09-06

  Before that it was a **partial rsync**, and **12 tracked files differed**, of which
  four are on the scoring path: `training/train.py` was the **pre-fix** version missing
  176 lines of checkpoint-selection machinery, and `uplifting v7`'s `config.yaml` /
  `normalization.json` / `base_scorer.py` all differed from what sadalsuud serves (main
  and sadalsuud were byte-identical, so b650 was the stale one). The other eight were
  `cultural_discovery v5` ×2, `investment_risk v6` ×3 and three `scripts/analysis/`
  dumpers. Pre-checkout copies + per-file diffs, and the authoritative list:
  `b650:~/b650-pre-checkout-2026-09-06/MODIFIED.txt`.

### From § SOLVED 2026-08-10 — b650 runs the student on GPU (the one-commit reversal)

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

### From § SOLVED 2026-08-10 (the confounded intermediate note)

  *(An intermediate note here said pinning made agreement WORSE and that the
  residual was hardware-level. That was confounded — it compared a mismatched-stack
  CPU run against a matched-stack CUDA run. The opposite is true.)*

### From § Historical — why the GPU was blocked (superseded 2026-08-10)

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
