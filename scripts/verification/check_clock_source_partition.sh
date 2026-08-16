#!/usr/bin/env bash
# Contract A `collected.clock_source` — does the clock partition still hold on
# DELIVERED ROWS?  api -> host_local, rss/social -> utc, no mixed cases.
#
# ⚠️ Deliberately reads emitted rows and NOT the producer's source. A probe that
# counts `datetime.now()` call sites is satisfied by a RENAME: when the 28 sites
# were migrated to `host_local_now()` on 2026-08-16, two sibling probes that
# counted the old spelling reported "#176 SHIPPED — delete this warning" while
# 19 files still stamped host-local and nothing was fixed. **If a refactor can
# make a probe pass, the probe is measuring the wrong thing.**
set -u
H=sadalsuud
R=$(ssh -o BatchMode=yes -o ConnectTimeout=10 "$H" \
      'ls -dt /home/jeroen/local_dev/FluxusSource/data/current/collection_* 2>/dev/null | head -1' 2>/dev/null)
[ -n "$R" ] || { echo "CANNOT VERIFY: $H unreachable, or no collections under data/current"; exit 0; }

ssh -o BatchMode=yes -o ConnectTimeout=10 "$H" "COLL='$R' python3 -" <<'PY' 2>/dev/null || { echo "CANNOT VERIFY: remote check did not run"; exit 0; }
import collections, glob, json, os, sys
rows = [json.loads(l) for fn in sorted(glob.glob(os.environ["COLL"] + "/content_items_*.jsonl"))
        for l in open(fn)]
if not rows:
    print("CANNOT VERIFY: newest collection has no rows"); sys.exit(0)
pairs = collections.Counter(
    (r.get("source_type"), (r.get("collected") or {}).get("clock_source")) for r in rows)
expected = {"api": "host_local", "rss": "utc", "social": "utc"}
mixed = [k for k in pairs if k[0] in expected and k[1] != expected[k[0]]]
stamped = sum(v for k, v in pairs.items() if k[1])
if not stamped:
    print("CANNOT VERIFY: no row carries collected.clock_source — pre-deploy data")
    sys.exit(0)
print(("MIXED CASES: " if mixed else "partition holds, %d/%d rows stamped: " % (stamped, len(rows)))
      + str({f"{a}->{b}": n for (a, b), n in sorted(pairs.items(), key=str)}))
sys.exit(1 if mixed else 0)
PY
