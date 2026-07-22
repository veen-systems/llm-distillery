# GPU Server (gpu-server)

Proxmox LXC container on HCL edge server, accessed via Tailscale.

## Access

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

Situla runs **two ssh agents**, and gpu-server uses the smaller one:

| agent | advertises | used by |
|-------|-----------|---------|
| `/run/user/1000/gcr/ssh` (gnome-keyring, = `$SSH_AUTH_SOCK`) | the fleet keys (`situla-to-sadalsuud-admin`, `situla-bots-admin`, `restic-storagebox@situla`, `veen-demo-admin@situla`) **plus** `situla@veen` — but see below: it advertises keys it may not have unlocked | sadalsuud, bots, storagebox, veen-demo |
| `/run/user/1000/openssh_agent` | **only** `situla@veen` (= `~/.ssh/id_ed25519`, passphrase-protected), and genuinely holds it | **gpu-server and github.com** — both pin `IdentityAgent` in `~/.ssh/config` |

**Origin unknown** — the engineer doesn't recall setting this up, so don't read
intent into it (an earlier version of this note claimed the split was a
deliberate security posture; that was invention). What is *established*:

- Both agents advertise `situla@veen`, and it is the same key
  (`SHA256:VLV24LZ…` = `~/.ssh/id_ed25519.pub`) — not two credentials.
- **gnome-keyring's gcr agent lists keys it has not unlocked**, reading them from
  `~/.ssh/*.pub`, and only prompts when one is actually used. So a gcr listing
  proves nothing about usability — this is exactly why `ssh-add -l` is a
  false-positive diagnostic here.
- Forcing gpu-server through gcr **hangs** rather than connecting (it tries to
  prompt; `BatchMode=yes` can't suppress the agent's own dialog). The passphrase
  gate is therefore real, not bypassable via gcr.
- Pinning `IdentityAgent` to the real openssh agent is the common, sane
  workaround for gcr's deficiencies — so the config is probably right even if
  nobody remembers writing it. `AddKeysToAgent yes` then caches the key into
  `openssh_agent` after one interactive unlock, and it looks unattended for the
  rest of the session.

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
- **Harness/non-interactive sessions (2026-07-19):** a headless agent *cannot*
  answer the passphrase prompt, so `ssh gpu-server` fails with the locked-key
  error and there is no in-session way to unlock it. The `ssh sadalsuud "ssh
  gpu-server …"` hop is then the only autonomous path (sadalsuud's key is
  unattended) and is a legitimate **operational** fallback — it does *not* revive
  the wrong **diagnosis** above (situla access exists; the key is merely locked).
  Best fix stays the same: ask the engineer to run `ssh gpu-server` once to unlock
  for the session (`AddKeysToAgent yes` then caches it and direct access works).
  **And READ THIS FILE before probing gpu-server** — the access + env are already
  documented here; re-discovering them each session is the miss this note fixes.

*Recorded 2026-07-14. Three corrections were needed to get this note right, which
is itself the lesson: (1) the agent inferred "no key from situla, must hop via
sadalsuud" and stated it twice as fact — the hop worked, so the wrong model kept
being confirmed; (2) the first note documented the wrong agent (gcr instead of
openssh_agent), which would have made `ssh-add -l` report a key gpu-server cannot
see; (3) the second note asserted the two-agent split was a deliberate security
design — the engineer doesn't recall creating it at all. Each claim was plausible,
none was checked before being written down.*

## Environment

- **venv**: `~/gpu-server/nexusmind-scorer/venv/bin/python` — torch 2.10, sentence-transformers, scikit-learn
- **System `python3` also carries the GPU stack** (confirmed 2026-07-19): torch+CUDA
  + `sentence-transformers` 5.2.3 + numpy. Enough to run a *self-contained*
  embedding/screening script with no venv and no PYTHONPATH. The venv above stays
  canonical for training/scorer imports (`filters.*`, `src.*`); use system
  `python3` only for standalone scripts.
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
