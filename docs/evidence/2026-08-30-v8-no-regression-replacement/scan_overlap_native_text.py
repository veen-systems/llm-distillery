"""Same population as scan_overlap.py, but keep only rows whose PRODUCER text
already cleared the 300-char labelling floor -- i.e. the row is reproducible
without the enricher having run.  original_content_length + pre_enriched are
the fields CLAUDE.md names for reading historical length."""
import json, glob, os
from collections import defaultdict
BASE = os.path.expanduser("~/local_dev/NexusMind/data/filtered")
OP = {"uplifting": 4.5, "solutions": 2.25, "nature_recovery": 3.75}
best = defaultdict(dict)
for lens in OP:
    for fp in sorted(glob.glob(os.path.join(BASE, lens, "filtered_*.jsonl"))):
        with open(fp, encoding="utf-8") as fh:
            for line in fh:
                try: d = json.loads(line)
                except Exception: continue
                a = (d.get("nexus_mind_attributes") or {}).get(lens)
                if not a or a.get("stage_used") != "stage2": continue
                raw = a.get("raw_weighted_average")
                if raw is None or raw < OP[lens]: continue
                ocl = a.get("original_content_length")
                native = ocl if (a.get("pre_enriched") and ocl is not None) else a.get("content_length")
                r = {"raw": raw, "native": native, "clen": a.get("content_length"),
                     "pre_enriched": a.get("pre_enriched"), "title": d.get("title"),
                     "url": d.get("url"), "lang": d.get("language"), "source": d.get("source"),
                     "pub": d.get("published_date")}
                p = best[lens].get(d.get("id"))
                if p is None or raw > p["raw"]: best[lens][d.get("id")] = r
up = best["uplifting"]
for other in ("nature_recovery", "solutions"):
    both = [i for i in set(up) & set(best[other])
            if (up[i]["native"] or 0) >= 1000]
    both.sort(key=lambda i: -min(up[i]["raw"], best[other][i]["raw"]))
    print(f"\n=== uplifting>=4.5 AND {other}>={OP[other]}, NATIVE text >=1000 ch -> {len(both)}")
    for i in both[:14]:
        u, o = up[i], best[other][i]
        print(f"  up {u['raw']:6.3f} | {other[:4]} {o['raw']:6.3f} | {u['lang']:3s} "
              f"native {u['native']:6d} enriched {u['clen']:6d} | {u['source'][:26]:26s} | {u['title'][:70]}")
        print(f"      {i}")
