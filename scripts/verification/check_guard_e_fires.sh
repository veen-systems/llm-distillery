#!/usr/bin/env bash
# Guard E must refuse a version whose weights are not in the backed-up tree.
#
# Exists as a script rather than an inline `<!-- verify: -->` because the check
# needs more than one line, and a multi-line annotation is reported MALFORMED
# and silently skipped — which is worse than no annotation, since the file then
# looks checked. (Learned twice: 2026-08-12's twelve-line annotation, and this
# one's first draft.)
#
# Prints evidence, exits non-zero on refutation. No verdict words.
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET="$REPO/filters/cultural_discovery/v4"

if [ ! -d "$TARGET" ]; then
    echo "CANNOT VERIFY: $TARGET is gone — pick another version with no model/ dir"
    exit 2
fi
if [ -f "$TARGET/model/adapter_model.safetensors" ]; then
    echo "CANNOT VERIFY: $TARGET now HAS weights, so it no longer tests the guard"
    exit 2
fi

PYTHONPATH="$REPO" python3 - "$TARGET" <<'PY'
import sys
from pathlib import Path
from scripts.deployment.preflight_deploy_guards import check_weights_backed_up, GuardFailure
target = Path(sys.argv[1])
try:
    notes = check_weights_backed_up(target)
except GuardFailure:
    print(f"guard E fired on {target.name} (no local adapter) — as designed")
    sys.exit(0)
print(f"CLAIM REFUTED: guard E did NOT fire on a weightless version: {notes}")
sys.exit(1)
PY
