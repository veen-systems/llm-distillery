# GPU Server (gpu-server)

Proxmox LXC container on HCL edge server, accessed via Tailscale.

## Access

Tailscale key expiry is **disabled** for this node (2026-07-30, verified
`Self.KeyExpiry: null`) — no periodic re-auth needed.

```bash
ssh gpu-server   # direct, headless, passphrase-less from situla — just works
```

**FIXED 2026-07-22 — situla now has direct headless access; the two-agent /
passphrase saga below is SUPERSEDED (kept for history).** Root fix: copied the
dedicated **`~/.ssh/nexusmind_gpu`** key (passphrase-less — the same key sadalsuud
uses) from sadalsuud → situla, and rewrote the `gpu-server` block in `~/.ssh/config`
to `HostName 100.84.103.16` + `IdentityFile ~/.ssh/nexusmind_gpu` + `IdentitiesOnly
yes`, dropping the empty-`openssh_agent` pin that offered no key. A non-interactive
`ssh gpu-server` now authenticates as `hcl@gpu-server` with no prompt — no more
`ssh sadalsuud "ssh gpu-server …"` hop needed. Everything below is historical.

The pre-fix two-agent / passphrase history (agents, why `ssh-add -l` lies, the sadalsuud hop) is in
`memory/archive/gpu-server-archive.md`, verbatim.

## Environment

- **venv**: `~/gpu-server/nexusmind-scorer/venv/bin/python` — torch 2.10, sentence-transformers, scikit-learn
- ⚠️ **System `python3` is NOT production, and it is not a near-copy either.**
  It carries *a* GPU stack (confirmed 2026-07-19, re-verified 2026-08-09):
  torch **2.5.1+cu124**, sentence-transformers **5.2.3**, numpy, **no peft**.
  What systemd actually starts is a different stack — read it off the unit, don't
  guess: `systemctl cat nexusmind-scorer` → `ExecStart=` and `Environment=PATH`
  both point at `/home/hcl/gpu-server/nexusmind-scorer/venv/bin`, which holds
  torch **2.11.0+cu130**, ST **5.2.2**, peft **0.18.1**, sklearn **1.8.0**,
  transformers **5.0.0**. `which python3` answers a question nobody asked.
  Numbers were published off the system interpreter on 2026-08-09 and had to be
  redone. Use it only for a *self-contained* embedding script whose result you
  are not going to compare against production; anything touching `filters.*` /
  `src.*` / PEFT adapters must use the venv above. Same shape on sadalsuud: the
  pipeline runs `~/local_dev/NexusMind/venv`; system python has nothing installed.
- **Working dir**: `~/llm-distillery/` — scripts, training data, embeddings (SCP'd, not git cloned)
- **NexusMind filters**: `~/NexusMind/filters/` — deployed filter packages
- **PYTHONPATH**: Must set `PYTHONPATH=.` or `PYTHONPATH=/home/hcl/NexusMind` for imports
- **HF_HUB_OFFLINE=1**: Can't resolve huggingface.co. Base model must be pre-cached.
- **Model cache**: `~/.cache/huggingface/hub/` — contains `google/gemma-3-1b-pt`
  **and `intfloat/multilingual-e5-small`** (so GPU e5 screening/embedding needs no network).
- **GPU**: 16 GB (16376 MiB). Shared with ollama (see long-jobs section). e5-small
  embedding of ~166K articles is a few minutes on GPU vs ~4 h on the CPU host
  (sadalsuud, 8 cores) — for any embedding-heavy screening pass, use gpu-server.

## File Transfers

Use **scp**, not rsync. rsync fails with dup() errors on this server when invoked from Windows Git Bash. (Linux→Linux rsync from sadalsuud works — that's why NexusMind's `scripts/deploy_filters.sh` runs on sadalsuud, not on the workstation.)

```bash
# Copy training data for training runs (workstation → gpu-server)
scp -r datasets/training/{name}_v{N}/ gpu-server:~/llm-distillery/datasets/training/

# Copy training output back (gpu-server → workstation)
scp -r gpu-server:~/llm-distillery/datasets/training/{name}_v{N}/model/ filters/{name}/v{N}/
```

### Deploy path (DO NOT direct-scp filters to NexusMind)

As of 2026-05-23 the canonical deploy is `scripts/deploy_to_nexusmind.{sh,ps1}` from the workstation. The script (a) verifies the filter package via `verify_filter_package.py`, (b) refuses if the NexusMind target is dirty (escape: `--force-dirty`), and (c) commits via explicit-staged `git add $FILTER_PATH filters/common/` instead of blanket `git add -A`. From there sadalsuud pulls and runs `bash scripts/deploy_filters.sh`, which rsyncs to gpu-server and restarts the scorer service. Don't bypass with direct `scp -r filters/.../v.../ gpu-server:~/NexusMind/...` — that skips the verify gate (#44) and the origin-contamination guard (#71 / 2026-05-22 incident, see gotcha-log).

## NexusMind Scorer Service

**The scorer is DOWN between pipeline cycles BY DESIGN** (learned 2026-07-31 after
chasing a phantom outage): `nexusmind-scorer.service` is a *static* unit that
sadalsuud starts per pipeline cycle and stops afterward — `ExecStopPost`
restarts ollama, handing the GPU back. `curl gpu-server:8000/health` refusing
connections mid-day is normal; check `journalctl -u nexusmind-scorer` for the
last run's load lines instead. Also: **gpu-server logs are UTC; sadalsuud logs
are local (UTC+2)** — a "02:10" scorer run IS the "04:14" pipeline cycle.

```bash
# Restart after deploying new filters
ssh gpu-server "sudo systemctl restart nexusmind-scorer"

# Check status
ssh gpu-server "sudo systemctl status nexusmind-scorer"

# Logs
ssh gpu-server "journalctl -u nexusmind-scorer -f"
```

Canonical scorer source is `deploy/gpu-server/main.py` in NexusMind repo (not llm-distillery).

## Long-running jobs + monitoring (salvaged from the retired gpu-training-guide, 2026-07-10)

- **Long jobs (training/scoring) must survive SSH drops** — the Tailscale link to gpu-server is
  intermittently flaky. Preferred: `setsid nohup … </dev/null >~/llm-distillery/<job>.log 2>&1 &`
  then poll the log (grep the job's own first real output line to confirm it launched — do NOT
  trust `pgrep -f "<script>"`, which matches your own ssh command line; verify by GPU memory /
  large RSS / log growth). `tmux new -s train` / `tmux attach -t train` also works if you prefer
  an interactive session.
- **OOM → reduce `--batch-size`** (e.g. 8 → 4) and/or check what else holds VRAM first:
  `nvidia-smi --query-gpu=memory.free --format=csv,noheader`. **ollama shares this GPU** and can
  hold 15+ GB (`ollama ps` shows loaded models + keep-alive expiry) — a job that OOMs at launch
  may just need to wait for ollama's idle model to unload, or run on CPU (`CUDA_VISIBLE_DEVICES=`).
- **Monitor:** `watch -n 1 nvidia-smi`, or one-shot
  `nvidia-smi --query-gpu=memory.used,memory.free,utilization.gpu --format=csv,noheader`.
- **CPU fallback** for small scoring jobs (a few hundred articles): set `CUDA_VISIBLE_DEVICES=`
  to dodge GPU contention entirely — ~1 s/article, reliable.

## Tailscale DNS Limitation

DNS resolution to external hosts (huggingface.co) may fail. This is why `HF_HUB_OFFLINE=1` is required and models must be pre-cached.
