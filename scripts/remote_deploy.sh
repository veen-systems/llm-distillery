#!/bin/bash
# Run the NexusMind deploy on sadalsuud (Linux) rather than the workstation.
#
# Why: NexusMind/scripts/deploy_filters.sh uses rsync to push filters to gpu-server.
# rsync from Windows Git Bash intermittently fails with `dup() in/out/err failed`
# (documented in NexusMind/memory/gotcha-log.md, 2026-02). Running the script on
# sadalsuud (Linux host) sidesteps the issue entirely — Linux->Linux rsync is
# reliable. This wrapper does the SSH hop in one command.
#
# Prerequisites:
#   - Your NexusMind commit is already pushed to origin (otherwise sadalsuud pulls
#     nothing new).
#   - `ssh sadalsuud` works (alias in ~/.ssh/config).
#
# Usage:
#   ./scripts/remote_deploy.sh
set -euo pipefail

SADALSUUD_NEXUSMIND="/home/jeroen/local_dev/NexusMind"

# Local NexusMind checkout. This was hardcoded to the Windows path, so on the
# Linux workstation the directory never existed, the `-d` test below fell to the
# "not a git checkout" branch, and the unpushed-commits pre-flight — the guard
# deployment-review added on 2026-04-19 precisely to stop stale deploys — was
# skipped silently on every run. Same shape as NM#284/NM#281: configured,
# present, and unable to fire. Found 2026-08-02.
#
# Resolve by probing the known layouts, newest first. NEXUSMIND_LOCAL in the
# environment still wins, for checkouts in neither place.
if [ -z "${NEXUSMIND_LOCAL:-}" ]; then
    for _candidate in \
        "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." 2>/dev/null && pwd)/NexusMind" \
        "$HOME/repos/veen-systems/NexusMind" \
        "C:/local_dev/NexusMind"
    do
        if [ -d "$_candidate/.git" ]; then
            NEXUSMIND_LOCAL="$_candidate"
            break
        fi
    done
fi
NEXUSMIND_LOCAL="${NEXUSMIND_LOCAL:-C:/local_dev/NexusMind}"
echo "Local NexusMind checkout: $NEXUSMIND_LOCAL"

echo "=== Remote deploy via sadalsuud ==="
echo ""

# Pre-flight: the workstation's NexusMind must be pushed before SSHing. Otherwise
# sadalsuud's `git pull` silently no-ops, deploy_filters.sh finds sadalsuud's
# origin-diff clean (because sadalsuud==origin, both stale), and deploys stale
# filters without any signal. Deployment-review flagged this 2026-04-19.
if [ -d "$NEXUSMIND_LOCAL/.git" ]; then
    # Fetch so origin/main is fresh locally before the comparison.
    if git -C "$NEXUSMIND_LOCAL" fetch origin main --quiet 2>/dev/null; then
        UNPUSHED=$(git -C "$NEXUSMIND_LOCAL" log origin/main..HEAD --oneline -- filters/ src/filters/ 2>/dev/null || true)
        if [ -n "$UNPUSHED" ]; then
            echo "ERROR: $NEXUSMIND_LOCAL has unpushed filter commits:"
            echo "$UNPUSHED" | sed 's/^/  /'
            echo "  Push these to origin first, then re-run this script."
            exit 1
        fi
    else
        echo "WARNING: could not fetch origin for $NEXUSMIND_LOCAL — cannot verify push state."
        echo "  Continue only if you are certain all NexusMind filter commits are pushed."
        echo "  Set SKIP_LOCAL_PUSH_CHECK=1 to bypass; Ctrl-C to abort."
        if [ "${SKIP_LOCAL_PUSH_CHECK:-0}" != "1" ]; then
            exit 1
        fi
    fi
else
    echo "WARNING: $NEXUSMIND_LOCAL is not a git checkout — skipping unpushed-commits check"
fi

# Sanity: confirm the host is reachable before committing to the work.
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes sadalsuud "true" 2>/dev/null; then
    echo "ERROR: sadalsuud unreachable over SSH. Check Tailscale, SSH config, and network."
    exit 1
fi

# Pull latest on sadalsuud and run deploy_filters.sh there.
# deploy_filters.sh itself verifies sadalsuud's HEAD matches origin before rsyncing
# and does a /health round-trip hash check after restarting the scorer.
ssh sadalsuud "cd \"$SADALSUUD_NEXUSMIND\" && git pull && bash scripts/deploy_filters.sh"

echo ""
echo "=== Done ==="
