#!/usr/bin/env bash
# Verify NexusMind#300 stays fixed: `content_length` populated on 100% of rows
# in the newest cycle file, for every deployed filter.
#
# Backs the "VERIFIED FIXED — 17:10 cycle, 2026-08-08" claim in
# memory/stamp-contract-integrity.md. That stamp read 0 of 50,605 rows from
# 2026-08-06 and was fixed through FIVE allowlists in series, with the first
# fix leaving it still at 0/2,170 — so this is a claim that has already
# regressed once after being called fixed.
#
# WHY THIS IS A SCRIPT AND NOT AN INLINE `<!-- verify: -->` COMMENT.
# It used to be inline and spanned twelve lines of embedded Python. The
# framework's curate runner (agent-ready-projects v1.22.0) requires an
# annotation to sit on ONE line: an HTML comment whose `-->` is eleven lines
# below its opener is reported MALFORMED and never runs. It had never run.
#
# Follows the v1.22.0 writing rules: prints the counts as evidence on success
# rather than a bare verdict word, exits non-zero on failure rather than
# echoing FAIL, and reports CANNOT VERIFY when the box is unreachable — which
# is neither a pass nor a failure.

set -uo pipefail

HOST="${1:-sadalsuud}"
BASE="${2:-/home/jeroen/local_dev/NexusMind/data/filtered}"

read -r -d '' REMOTE <<'PY'
import glob, json, os, sys
base = sys.argv[1]
bad = []
for d in sorted(glob.glob(os.path.join(base, "*"))):
    lens = os.path.basename(d)
    files = sorted(glob.glob(os.path.join(d, "filtered_*.jsonl")))
    if not files:
        continue
    tot = pop = 0
    with open(files[-1]) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                attrs = (json.loads(line).get("nexus_mind_attributes") or {})
            except Exception:
                continue
            a = attrs.get(lens) or attrs.get(lens.replace("_", "-")) or {}
            if not a:
                continue
            tot += 1
            if a.get("content_length") is not None:
                pop += 1
    print(f"{lens}: {pop}/{tot} populated ({os.path.basename(files[-1])})")
    if tot == 0 or pop != tot:
        bad.append(lens)
sys.exit(1 if bad else 0)
PY

OUT=$(ssh -o BatchMode=yes -o ConnectTimeout=10 "$HOST" "python3 - '$BASE'" <<<"$REMOTE" 2>/dev/null)
RC=$?

if [ -z "$OUT" ]; then
    echo "CANNOT VERIFY: no output from $HOST (unreachable, or $BASE absent)"
    exit 2
fi

echo "$OUT"
[ "$RC" -eq 0 ] || { echo "content_length is NOT 100% populated — NexusMind#300 has regressed" >&2; exit 1; }
