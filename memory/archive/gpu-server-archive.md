# gpu-server — archived history (verbatim)

Moved verbatim from `memory/gpu-server.md` § *Access* on 2026-10-12 (read-surface pruning, #163). Superseded since 2026-07-22: situla reaches gpu-server headless with `~/.ssh/nexusmind_gpu`.

## The two-agent / passphrase saga (pre-2026-07-22)

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
