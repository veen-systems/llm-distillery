"""Per-day top-30 personal counts for each tagger, weekly mean vs the bar (<= 6), pairwise agreement on the 101 unique ids.
usage: python3 compare_taggers.py <lab experiments/2026-10-21-belonging-onsite-h>"""
import json, sys, os, itertools
E = sys.argv[1]
sel = json.load(open(os.path.join(E, "selection/selection.json")))
def load(p): return {json.loads(l)["id"]: json.loads(l)["focus"] for l in open(p)} if os.path.exists(p) else {}
qwen = {k: v["focus"] for k, v in json.load(open(os.path.join(E, "selection/reused.json"))).items()}
qwen.update(load(os.path.join(E, "run/tag/out.jsonl")))
tags = {"qwen": qwen, "fable": load(os.path.join(E, "run/tag-fable/out.jsonl")), "mistral": load(os.path.join(E, "run/tag-mistral/out.jsonl"))}
ids = sorted({i for v in sel.values() for i in v["top30"]})
print(f"{'day':10}" + "".join(f"{m:>10}" for m in tags))
means = {m: [] for m in tags}
for day, v in sorted(sel.items()):
    row = f"{day:10}"
    for m, t in tags.items():
        got = [t.get(i) for i in v["top30"]]
        miss = sum(g not in ("personal", "group") for g in got)
        c = sum(g == "personal" for g in got)
        means[m].append(c if not miss else None)
        row += f"{c:>7}" + (f"?{miss:<2}" if miss else "   ")
    print(row)
print(f"{'mean':10}" + "".join(f"{(sum(x)/len(x) if None not in x else float('nan')):>10.2f}" for x in means.values()))
for a, b in itertools.combinations(tags, 2):
    both = [i for i in ids if tags[a].get(i) in ("personal", "group") and tags[b].get(i) in ("personal", "group")]
    agree = sum(tags[a][i] == tags[b][i] for i in both)
    pp = sum(tags[a][i] == tags[b][i] == "personal" for i in both)
    print(f"{a} vs {b}: agree {agree}/{len(both)}; both personal {pp}; {a}-only personal {sum(tags[a][i]=='personal' and tags[b][i]!='personal' for i in both)}; {b}-only personal {sum(tags[b][i]=='personal' and tags[a][i]!='personal' for i in both)}")
