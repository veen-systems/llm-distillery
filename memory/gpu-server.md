# GPU Server (gpu-server)

Proxmox LXC container on HCL edge server, accessed via Tailscale.

## Access

```bash
ssh gpu-server   # configured in ~/.ssh/config — direct from situla over Tailscale
```

**Direct access works. `Permission denied` means the key is LOCKED, not absent.**

Situla runs **two ssh agents**, and gpu-server deliberately uses the smaller one:

| agent | holds | used by |
|-------|-------|---------|
| `/run/user/1000/gcr/ssh` (gnome-keyring, = `$SSH_AUTH_SOCK`) | the unattended fleet keys (`situla-to-sadalsuud-admin`, `situla-bots-admin`, `restic-storagebox@situla`, `veen-demo-admin@situla`) | sadalsuud, bots, storagebox, veen-demo |
| `/run/user/1000/openssh_agent` | **only** `situla@veen` (= `~/.ssh/id_ed25519`, passphrase-protected) | **gpu-server and github.com** — both pin `IdentityAgent` in `~/.ssh/config` |

This split is intentional: the fleet automation keys are passphrase-less, while
the two highest-value targets (gpu-server, GitHub) sit behind the passphrase.
`AddKeysToAgent yes` caches the key into `openssh_agent` after one interactive
unlock, so gpu-server works for the rest of the session and looks unattended.

On a cold agent, a non-interactive shell instead gets:

```
ssh_askpass: exec(/usr/bin/ssh-askpass): No such file or directory
hcl@gpu-server: Permission denied (publickey,password).
```

That is a locked key, NOT a missing link. Do **not** conclude "there's no
gpu-server access from this box" and do **not** route around it via a
`ssh sadalsuud "ssh gpu-server ..."` hop — the hop works only because
sadalsuud's key is unattended, so the workaround succeeds and the wrong
diagnosis never gets falsified.

- **Diagnose with the agent gpu-server actually uses** — `ssh-add -l` reads
  `$SSH_AUTH_SOCK` (gcr), which lists `situla@veen` even when `openssh_agent` is
  empty and gpu-server is failing. That reading is a false positive. Use:
  ```bash
  SSH_AUTH_SOCK=/run/user/1000/openssh_agent ssh-add -l   # must list situla@veen
  ssh -o BatchMode=yes -o ConnectTimeout=10 gpu-server true
  ```
- **Fix**: run `ssh gpu-server` once interactively and type the passphrase.
- **In scripts/assertions**: `-o BatchMode=yes -o ConnectTimeout=10` so a locked
  key fails fast instead of hanging on a prompt, and report transport failure as
  ERROR — never as a FAIL of whatever you were checking (2026-07-14: three
  MEMORY.md verify assertions reported FAIL on true claims for exactly this).
- **Nothing in production depends on this link.** The pipeline reaches gpu-server
  from sadalsuud using `nexusmind-scorer@sadalsuud`, an unattended key on the
  machine that needs it. Situla→gpu-server is ad-hoc/human only, so the
  passphrase costs nothing operationally — don't "fix" it by stripping it.

*Recorded 2026-07-14 — the agent hit this, inferred "no key from situla, must hop
via sadalsuud", and stated it twice as fact before the engineer corrected it. The
first version of this note then documented the wrong agent (gcr instead of
openssh_agent), which would have made `ssh-add -l` report a key that gpu-server
cannot see.*

## Environment

- **venv**: `~/gpu-server/nexusmind-scorer/venv/bin/python` — torch 2.10, sentence-transformers, scikit-learn
- **Working dir**: `~/llm-distillery/` — scripts, training data, embeddings (SCP'd, not git cloned)
- **NexusMind filters**: `~/NexusMind/filters/` — deployed filter packages
- **PYTHONPATH**: Must set `PYTHONPATH=.` or `PYTHONPATH=/home/hcl/NexusMind` for imports
- **HF_HUB_OFFLINE=1**: Can't resolve huggingface.co. Base model must be pre-cached.
- **Model cache**: `~/.cache/huggingface/hub/` — contains `google/gemma-3-1b-pt`

## File Transfers

Use **scp**, not rsync. rsync fails with dup() errors on this server when invoked from Windows Git Bash. (Linux→Linux rsync from sadalsuud works — that's why `deploy_filters.sh` runs on sadalsuud, not on the workstation.)

```bash
# Copy training data for training runs (workstation → gpu-server)
scp -r datasets/training/{name}_v{N}/ gpu-server:~/llm-distillery/datasets/training/

# Copy training output back (gpu-server → workstation)
scp -r gpu-server:~/llm-distillery/datasets/training/{name}_v{N}/model/ filters/{name}/v{N}/
```

### Deploy path (DO NOT direct-scp filters to NexusMind)

As of 2026-05-23 the canonical deploy is `scripts/deploy_to_nexusmind.{sh,ps1}` from the workstation. The script (a) verifies the filter package via `verify_filter_package.py`, (b) refuses if the NexusMind target is dirty (escape: `--force-dirty`), and (c) commits via explicit-staged `git add $FILTER_PATH filters/common/` instead of blanket `git add -A`. From there sadalsuud pulls and runs `bash scripts/deploy_filters.sh`, which rsyncs to gpu-server and restarts the scorer service. Don't bypass with direct `scp -r filters/.../v.../ gpu-server:~/NexusMind/...` — that skips the verify gate (#44) and the origin-contamination guard (#71 / 2026-05-22 incident, see gotcha-log).

## NexusMind Scorer Service

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
