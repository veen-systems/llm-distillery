# b650 GPU (Arian's box)

Commissioned 2026-07-30. RTX 3090 Ti **24 GB** (vs gpu-server's 16), CUDA 12.0
driver 580.95, 699 GB free disk, 30 GB RAM. Reachable via Tailscale:

```bash
ssh b650-gpu        # account is `jeroen` (NOT jwasys); works from situla and sadalsuud
```

- **sudo password**: in owner's Bitwarden (initial photo'd one is dead).
- **venv**: `~/llm-distillery/venv` — created with **uv** (`~/.local/bin/uv`);
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
  therefore cleared to train e5 probes for gpu-server.** Still unmeasured for
  the Gemma-3-1B student. Re-run the parity harness before trusting any new
  box/version pair rather than assuming either way.
- 🚫 **b650 CANNOT run the Gemma-3-1B student on GPU** (2026-08-09). torch 2.13
  JITs a `bmm_outer_product` triton kernel and triton fails to build its CUDA
  helper — `gcc` cannot link `libcuda.so.1`. Workaround: `CUDA_VISIBLE_DEVICES=""`,
  ~7 min per 660 articles at ~740% CPU. The e5 probe path never touches that
  kernel, which is why probe work runs clean on GPU here.
- ⚠️ **Read the venv, not `which python3`.** gpu-server's *system* python is a
  different stack (torch 2.5.1+cu124, ST 5.2.3, **no peft**) from the one systemd
  starts (`/home/hcl/gpu-server/nexusmind-scorer/venv`: torch 2.11.0+cu130, ST
  5.2.2, peft 0.18.1). Numbers were published off the wrong one on 2026-08-09 and
  had to be redone. Same on sadalsuud — the pipeline runs
  `~/local_dev/NexusMind/venv` (sklearn 1.8.0, ST 5.6.0); system python has
  nothing installed.
- Purpose: training node (ends Ollama-vs-training contention on gpu-server).
  First planned job was obituary v6 (LD#85, now parked).
