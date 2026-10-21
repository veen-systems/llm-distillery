"""EXP-056 step 4: per-build qwen counts on the live H page, as pre-registered (PREREGISTRATION.md §2-3).

    python3 count.py <run dir>      (reads selection.json, reused.json, tag/out.jsonl, tag-control/out.jsonl)

Unparsed tags (focus None) count as NOT personal (the floor direction). Determinism control: >= 9/10 re-tagged
ids must match their earlier tag, else reuse is abandoned (reported; the counts below would then be invalid).
"""
import json, statistics, sys
d = sys.argv[1]
sel = json.load(open(f"{d}/selection.json"))
reused = json.load(open(f"{d}/reused.json"))
new = {r["id"]: r for r in map(json.loads, open(f"{d}/tag/out.jsonl"))}
ctl = {r["id"]: r for r in map(json.loads, open(f"{d}/tag-control/out.jsonl"))}
match = sum(ctl[i]["focus"] == reused[i]["focus"] for i in ctl)
print(f"determinism control: {match}/{len(ctl)} re-tagged ids match their earlier tag "
      f"({'reuse STANDS' if match >= 9 else 'reuse ABANDONED: re-tag everything'})")
for i in ctl:
    if ctl[i]["focus"] != reused[i]["focus"]:
        print(f"  differs: {i}: earlier {reused[i]['focus']!r} ({reused[i]['_file']}), now {ctl[i]['focus']!r}")
tag = lambda i: (new.get(i) or reused.get(i) or {}).get("focus")
missing = [i for s in sel.values() for i in s["top30"] if i not in new and i not in reused]
if missing:
    raise SystemExit(f"{len(missing)} top-30 ids have no tag at all: {missing[:5]}")
print("\nbuild      N  skipped  personal  group  unparsed  other")
counts = {}
for b, s in sorted(sel.items()):
    t = [tag(i) for i in s["top30"]]
    p, g, u = t.count("personal"), t.count("group"), t.count(None)
    counts[b] = p
    print(f"{b}  {s['N']:2d}  {str(s['skipped'] or '-'):7s}  {p:8d}  {g:5d}  {u:8d}  {len(t) - p - g - u:5d}")
inr = {b: c for b, c in counts.items() if sel[b]["N"] == 30}
m = statistics.fmean(inr.values())
print(f"\nin-range builds {len(inr)}/{len(sel)}; WEEKLY qwen mean {m:.2f}; worst day {max(inr.values())} "
      f"({max(inr, key=inr.get)}); best day {min(inr.values())} ({min(inr, key=inr.get)})")
print("presence control:", "PASS" if any(inr.values()) else "FAIL (a week of zeros is an instrument failure)")
print(f"verdict vs the bar (<= 6 weekly, qwen is a FLOOR): "
      f"{'FAILS the bar (conclusive: a floor above 6)' if m > 6 else 'UNDETERMINED (a floor at or below 6; the owner count decides)'}")
