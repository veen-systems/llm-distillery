"""Population probe BEFORE any rate is quoted: what window do these files span, and
what fraction of rows actually carry _obituary_score?"""
import json, glob, os, collections, re
files = sorted(glob.glob(os.path.expanduser("~/local_dev/NexusMind/data/raw/content_items_*.jsonl")))
print(f"files: {len(files)}")
ds = sorted(re.search(r"content_items_(\d{8})_", f).group(1) for f in files)
print(f"WINDOW: {ds[0]} .. {ds[-1]}  ({len(set(ds))} distinct days)")
n = 0; stamped = 0; model = collections.Counter(); flagged = 0
for f in files:
    for line in open(f, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        try: r = json.loads(line)
        except Exception: continue
        n += 1
        if r.get("_obituary_score") is not None:
            stamped += 1
            model[r.get("_obituary_model")] += 1
            if r.get("_is_obituary"): flagged += 1
print(f"rows: {n}")
print(f"_obituary_score present: {stamped} ({100*stamped/max(n,1):.2f}%)")
print(f"_obituary_model values: {dict(model)}")
print(f"_is_obituary true: {flagged} ({100*flagged/max(stamped,1):.2f}% of stamped)")
