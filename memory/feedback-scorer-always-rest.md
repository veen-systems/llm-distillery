---
name: feedback-scorer-always-rest
description: nexusmind-scorer is on-demand — ALWAYS let it rest; never restart it or curl /health to check it
metadata:
  type: feedback
---

The `nexusmind-scorer` systemd unit is `static`/on-demand: the pipeline (FluxusSource harvest → NexusMind on sadalsuud → gpu-server scorer → exits) spins it up per scoring run. **`inactive` between runs is the correct resting state, NOT an outage.** A clean rest = `systemctl show` `Result=success` + `NRestarts=0`. A real fault = `Result≠success`.

**Why:** the scorer shares the 16GB GPU with ollama (`gemma3:27b` ≈ 15GB). A resting scorer hands the GPU back to ollama; manually starting/restarting it holds the GPU and starves ollama. The user's standing instruction (2026-07-10): **always rest** — don't keep it up "just in case."

**How to apply:**
- `systemctl is-active` = `inactive` → **do nothing**, it's normal. Never `systemctl start/restart` it to "fix" it.
- **Never** use `curl localhost:8000/health` as a liveness check — it only answers mid-run, so an empty/failed curl on a resting scorer looks like an outage but isn't.
- Only investigate if `Result≠success` or `NRestarts>0`.

**How I got this wrong (don't repeat):** 2026-07-10 I found the scorer `inactive`, curled `/health` (empty), called it "DOWN," and restarted it — re-running the exact phantom-outage pattern the 2026-07-04 session already fixed. The guidance existed in MEMORY.md; I didn't apply it. This file makes it a behavioral rule, not just a fact. See MEMORY.md on-demand-scorer note + [[gotcha-log]].
