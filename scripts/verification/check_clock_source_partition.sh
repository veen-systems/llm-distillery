#!/usr/bin/env bash
# Contract A `collected.clock_source` — is every DELIVERED ROW stamped, and is
# every stamp `utc`?
#
# ⚠️ THE ASSERTION CHANGED ON 2026-08-31, and the old one is kept here because a
# guard whose history is erased cannot be audited. Until today this script
# asserted a PARTITION — `api -> host_local`, `rss`/`social` -> `utc`, no mixed
# cases — which is what FS#176 measured on 2026-08-15/16. That partition is now
# obsolete BY SUCCESS: over the 47 collections retained on sadalsuud
# (collection_20260824_040945 .. collection_20260831_200757, 158,656 rows) every
# row is stamped and every stamp is `utc`, `host_local` count zero, and the `api`
# rows' own `collected_date` sits within ~5 minutes of the collection's UTC start
# rather than +120 — so the stamp is TRUTHFUL, not a mislabelled host-local clock.
# ⚠️ The retention window starts 2026-08-24 and therefore CANNOT date the change;
# it only shows the state is a week old at least.
#
# The post-migration invariant is strictly stronger than the partition and stays
# falsifiable in the same way: ONE `host_local` row refutes it.
#
# ⚠️ Deliberately reads emitted rows and NOT the producer's source. A probe that
# counts `datetime.now()` call sites is satisfied by a RENAME: when the 28 sites
# were migrated to `host_local_now()` on 2026-08-16, two sibling probes that
# counted the old spelling reported "#176 SHIPPED — delete this warning" while
# 19 files still stamped host-local and nothing was fixed. **If a refactor can
# make a probe pass, the probe is measuring the wrong thing.**
#
# ⛔ FAIL-OPEN FIXED 2026-08-31. Until today the remote block's `sys.exit(1)` — a
# real violation — landed in the SAME `||` branch as an unreachable host, so the
# script printed "CANNOT VERIFY: remote check did not run" and exited 0 with the
# violation's own evidence on the line above it. A detection was indistinguishable
# from a transport failure, and it read as the harmless one. Exit codes are now
# carried out of the remote block: 0 holds, 2 violation (prints FAIL), 3 cannot
# verify. Same shape as the `| grep` fail-open fixed in
# `memory/oracle-pricing-scheduling.md` on 2026-08-29.
#
# `FS_COLLECTION_ROOT` exists so the FAIL branch can be PROVEN on a seeded fixture
# rather than asserted — see the controls recorded in
# `docs/evidence/2026-08-31-clock-source-fail-open/`. It defaults to production and
# the `<!-- verify: -->` annotation passes no environment, so the shipped path is
# the tested path.
set -u
H=sadalsuud
ROOT=${FS_COLLECTION_ROOT:-/home/jeroen/local_dev/FluxusSource/data/current}
R=$(ssh -o BatchMode=yes -o ConnectTimeout=10 "$H" \
      "ls -dt '$ROOT'/collection_* 2>/dev/null | head -1" 2>/dev/null)
[ -n "$R" ] || { echo "CANNOT VERIFY: $H unreachable, or no collection_* under $ROOT"; exit 0; }

# ⛔ The verdict NAMES the directory it read. `FS_COLLECTION_ROOT` propagates into this
# script through `run_verify_annotations.py` (subprocess inherits the environment — proven
# on 2026-08-31 by seeding a fixture and watching the battery turn red), so without the
# directory on the verdict line a redirected guard is indistinguishable from the real one.
OUT=$(ssh -o BatchMode=yes -o ConnectTimeout=10 "$H" "COLL='$R' python3 -" <<'PY' 2>/dev/null
import collections, glob, json, os, sys
rows = [json.loads(l) for fn in sorted(glob.glob(os.environ["COLL"] + "/content_items_*.jsonl"))
        for l in open(fn)]
if not rows:
    print("CANNOT VERIFY: newest collection has no rows"); sys.exit(3)
pairs = collections.Counter(
    (r.get("source_type"), (r.get("collected") or {}).get("clock_source")) for r in rows)
table = str({f"{a}->{b}": n for (a, b), n in sorted(pairs.items(), key=str)})
unstamped = sum(n for (a, b), n in pairs.items() if not b)
host_local = sum(n for (a, b), n in pairs.items() if b == "host_local")
other = sum(n for (a, b), n in pairs.items() if b and b not in ("utc", "host_local"))
if unstamped == len(rows):
    print("CANNOT VERIFY: no row carries collected.clock_source — pre-deploy data"); sys.exit(3)
if unstamped or host_local or other:
    print(f"FAIL: {unstamped} unstamped, {host_local} host_local, {other} other "
          f"in {os.environ['COLL']} — {table}")
    sys.exit(2)
print(f"PASS every row utc, {len(rows)}/{len(rows)} stamped "
      f"in {os.environ['COLL']}: {table}")
PY
)
RC=$?
echo "$OUT"
case "$RC" in
  0) exit 0 ;;
  2) exit 1 ;;                                   # a real violation — the runner reads the FAIL line
  3) exit 0 ;;                                   # the remote block said why, and it is not a verdict
  *) echo "CANNOT VERIFY: the remote block did not complete (ssh rc=$RC)"; exit 0 ;;
esac
