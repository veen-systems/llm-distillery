"""Census `collected.clock_source` over EVERY collection retained on the collection host,
and check whether the `api` stamp is TRUTHFUL rather than merely present.

Two questions, deliberately separate:

 1. What does the stamp SAY? (the pair table, per source_type)
 2. Is it TRUE? — `collected_date` is compared against the collection directory's own UTC
    start. A host-local clock on this host reads +120 minutes; a UTC one reads ~0. A stamp
    that says `utc` on a host-local timestamp is the failure mode nothing else here can see,
    because every consumer downstream trusts the stamp instead of the number.

⚠️ The retention window is part of this source. `data/current` holds ~8 days; this script
prints its span so that a claim derived from it cannot be quoted as "always" or used to DATE
a change that may predate the oldest directory on disk.

Run ON the collection host:  python3 census_clock_source.py [ROOT]
"""
import collections, datetime, glob, json, os, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/home/jeroen/local_dev/FluxusSource/data/current"
dirs = sorted(glob.glob(os.path.join(ROOT, "collection_*")))
if not dirs:
    raise SystemExit(f"FATAL: no collection_* under {ROOT}")

pairs, types, rows_n, unstamped = collections.Counter(), collections.Counter(), 0, 0
for d in dirs:
    for fn in sorted(glob.glob(os.path.join(d, "content_items_*.jsonl"))):
        for line in open(fn, encoding="utf-8"):
            r = json.loads(line)
            rows_n += 1
            cs = (r.get("collected") or {}).get("clock_source")
            types[r.get("source_type")] += 1
            pairs[(r.get("source_type"), cs)] += 1
            if cs is None:
                unstamped += 1

print(f"window: {len(dirs)} collections, {os.path.basename(dirs[0])} .. {os.path.basename(dirs[-1])}")
print(f"rows: {rows_n:,}   unstamped: {unstamped}")
print(f"source_types: {dict(types)}")
print("pairs: " + str({f"{a}->{b}": n for (a, b), n in sorted(pairs.items(), key=str)}))

print("\nis the stamp truthful? collected_date offset from the collection's own UTC start, minutes")
print("  (host-local on this host would read ~+120; UTC reads ~0)")
for d in (dirs[0], dirs[len(dirs) // 2], dirs[-1]):
    local = datetime.datetime.strptime(os.path.basename(d).split("_", 1)[1], "%Y%m%d_%H%M%S")
    start_utc = local - datetime.timedelta(hours=2)          # CEST; see the DST note below
    rows = [json.loads(l) for fn in sorted(glob.glob(os.path.join(d, "content_items_*.jsonl")))
            for l in open(fn, encoding="utf-8")]
    print(f"  {os.path.basename(d)}  dir-local {local}  -> UTC {start_utc}")
    for st in sorted({r.get("source_type") for r in rows}):
        offs = sorted((datetime.datetime.fromisoformat(r["collected_date"]) - start_utc).total_seconds() / 60
                      for r in rows if r.get("source_type") == st and r.get("collected_date"))
        if offs:
            print(f"    {st:<7} n={len(offs):<6} min {offs[0]:+.1f}  median {offs[len(offs)//2]:+.1f}  max {offs[-1]:+.1f}")
# ⚠️ The -2h is CEST and is correct only until 2026-10-25. After the CET switch this
# script's own arithmetic goes stale — which is the same class of bug it is looking for.
