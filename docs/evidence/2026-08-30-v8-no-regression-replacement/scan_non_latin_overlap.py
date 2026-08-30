"""Non-Latin-script cross-lens overlap candidates, native text >= 1000 ch.
Script test is on the article TEXT, not the language tag -- the tag is a
declaration, the glyphs are the fact."""
import json, glob, os, unicodedata
from collections import defaultdict
BASE = os.path.expanduser("~/local_dev/NexusMind/data/filtered")
OP = {"uplifting": 4.5, "solutions": 2.25, "nature_recovery": 3.75, "cultural_discovery": 4.0}

def non_latin_share(t):
    letters = [c for c in t if c.isalpha()]
    if not letters: return 0.0
    nl = sum(1 for c in letters if "LATIN" not in unicodedata.name(c, "LATIN"))
    return nl / len(letters)

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
                txt = d.get("content") or ""
                ocl = a.get("original_content_length")
                native = ocl if (a.get("pre_enriched") and ocl is not None) else a.get("content_length")
                if (native or 0) < 1000: continue
                if non_latin_share(txt[:3000]) < 0.5: continue
                p = best[lens].get(d.get("id"))
                if p is None or raw > p["raw"]:
                    best[lens][d.get("id")] = {"raw": raw, "native": native, "title": d.get("title"),
                        "lang": d.get("language"), "source": d.get("source"), "url": d.get("url"),
                        "nl_share": round(non_latin_share(txt[:3000]), 3)}
up = best["uplifting"]
print(f"non-Latin, native>=1000, uplifting>=4.5: {len(up)}")
for other in ("solutions", "nature_recovery", "cultural_discovery"):
    both = sorted(set(up) & set(best[other]), key=lambda i: -min(up[i]["raw"], best[other][i]["raw"]))
    print(f"\n=== AND {other}>={OP[other]} -> {len(both)}")
    for i in both[:10]:
        u, o = up[i], best[other][i]
        print(f"  up {u['raw']:6.3f} | {other[:4]} {o['raw']:6.3f} | {u['lang']:3s} nl={u['nl_share']:.2f} "
              f"native {u['native']:6d} | {u['source'][:26]:26s} | {u['title'][:60]}")
        print(f"      {i}")
