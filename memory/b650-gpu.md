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
- ⚠️ **Cross-box score skew**: ST 5.6.1 here vs 5.2.2 on gpu-server shifts
  frozen-embedder+MLP scores up to |0.16| on identical rows. Evaluate on the box
  that trained; never mix scores across boxes (gotcha-log 2026-07-30).
- Purpose: training node (ends Ollama-vs-training contention on gpu-server).
  First planned job was obituary v6 (LD#85, now parked).
