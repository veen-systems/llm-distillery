"""Enumerate cross-lens overlap candidates from NexusMind's filtered archive.

Population = every filtered_*.jsonl in data/filtered/{lens}/ at run time. The
archive ROLLS, so the window is printed and must be recorded with any number
taken from here.

raw_weighted_average is a model output ONLY when stage_used == "stage2"
(a stage1_low row's score is an e5 probe estimate). Every row here is
stage-2-conditioned before its score is read.
"""
import json, glob, os, sys
from collections import defaultdict

BASE = os.path.expanduser("~/local_dev/NexusMind/data/filtered")
OP = {"uplifting": 4.5, "solutions": 2.25, "nature_recovery": 3.75,
      "cultural_discovery": 4.0, "belonging": 4.0}

best = defaultdict(dict)   # lens -> id -> row (highest raw seen)
window = defaultdict(list)
skipped_nonstage2 = defaultdict(int)

for lens in OP:
    files = sorted(glob.glob(os.path.join(BASE, lens, "filtered_*.jsonl")))
    window[lens] = [os.path.basename(files[0]), os.path.basename(files[-1]), len(files)]
    for fp in files:
        with open(fp, encoding="utf-8") as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                a = (d.get("nexus_mind_attributes") or {}).get(lens)
                if not a:
                    continue
                if a.get("stage_used") != "stage2":
                    skipped_nonstage2[lens] += 1
                    continue
                raw = a.get("raw_weighted_average")
                if raw is None:
                    continue
                aid = d.get("id")
                prev = best[lens].get(aid)
                if prev is None or raw > prev["raw"]:
                    best[lens][aid] = {
                        "raw": raw, "title": d.get("title"), "url": d.get("url"),
                        "lang": d.get("language"), "published": d.get("published_date"),
                        "len": a.get("content_length"), "tier": a.get("tier"),
                        "source": d.get("source"), "version": a.get("version"),
                        "file": os.path.basename(fp), "runs": 1,
                    }
                else:
                    prev["runs"] += 1

print("WINDOW (rolls — record it):")
for lens, (a, b, n) in window.items():
    print(f"  {lens:20s} {a} .. {b}  ({n} cycle files, {len(best[lens])} distinct stage-2 ids, "
          f"{skipped_nonstage2[lens]} non-stage-2 rows skipped)")

up = {i: r for i, r in best["uplifting"].items() if r["raw"] >= OP["uplifting"]}
print(f"\nuplifting stage-2 rows at or above its 4.5 op-point: {len(up)}")

for other in ("nature_recovery", "solutions", "cultural_discovery", "belonging"):
    ov = {i: r for i, r in best[other].items() if r["raw"] >= OP[other]}
    both = sorted(set(up) & set(ov), key=lambda i: -min(up[i]["raw"], ov[i]["raw"]))
    print(f"\n=== uplifting>=4.5  AND  {other}>={OP[other]}  ->  {len(both)} articles")
    for i in both[:25]:
        u, o = up[i], ov[i]
        print(json.dumps({"id": i, "uplifting_raw": round(u["raw"], 4),
                          other + "_raw": round(o["raw"], 4), "lang": u["lang"],
                          "len": u["len"], "title": u["title"], "url": u["url"],
                          "source": u["source"], "published": u["published"],
                          "up_runs": u["runs"], "other_runs": o["runs"]}, ensure_ascii=False))
