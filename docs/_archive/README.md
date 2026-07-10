# Archive — retired docs (kept a while, then safe to delete)

Docs moved here are **superseded or deprecated** but retained temporarily in case a lost
detail surfaces. Nothing live points into this folder. **Safe to delete after ~2026-10**
(≥3 months) if nothing needed them.

Before archiving each, its unique value was checked against the live docs (see below).

| Archived file | Why retired | Live equivalent | Salvaged? |
|---------------|-------------|-----------------|-----------|
| `guides/getting-started.md` | Qwen-era 5-step overview | `docs/FILTER_PLAYBOOK.md` + `filter-development-guide.md` | nothing unique |
| `guides/ground-truth-generation.md` | Gemini-only labeling workflow | `filter-development-guide.md` Phase 3 + `docs/RUNBOOK.md` (batch_scorer: `--random-sample`, monitor, resume) | nothing unique |
| `guides/gpu-training-guide.md` | 2025-11 Qwen/tmux training | `docs/RUNBOOK.md` + `memory/gpu-server.md` | ✅ long-job/OOM/nvidia-smi/CPU-fallback tips → `memory/gpu-server.md` |
| `guides/remote-sync-guide.md` | FreeFileSync remote dev (abandoned) | `memory/gpu-server.md` (scp/rsync) + `deploy_filters.sh` | nothing (FreeFileSync-specific) |
| `guides/qwen-finetuning-guide.md` | Qwen 2.5 fine-tuning (we use Gemma-3-1B) | `filter-development-guide.md` + `filters/common/model_loading.py` | nothing unique |

To restore one: `git mv docs/_archive/guides/<f> docs/guides/<f>`.
