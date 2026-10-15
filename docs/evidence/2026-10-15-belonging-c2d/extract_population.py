"""Check B population (PREREGISTRATION.md section 3). Runs ON sadalsuud, stdlib only, read-only on NexusMind's files.

    python3 extract_population.py > population.jsonl      (stderr: the counts)

Every id in belonging filtered_*.jsonl from filtered_20260929 on, published 2026-09-29 or later. Per id: the NEWEST
file's text and production stamp, and the FIRST file it appeared in (its availability time). Kept: the screen
(production stage2, raw >= 2.0), plus the safety sample: 1,000 below-screen stage2 ids and 1,000 stage1_low ids, chosen
with random.Random(0) from the sorted ids of each stratum. Rows carry `stratum` = screen | below | stage1_low.
Also written: norm_control.jsonl in the working directory, the normalization control's inputs (every production
v3 stage2 row: id, raw, stamped normalized).
"""
import glob, json, os, random, sys

files = sorted(f for f in glob.glob(os.path.expanduser("~/local_dev/NexusMind/data/filtered/belonging/filtered_*.jsonl"))
               if os.path.basename(f) >= "filtered_20260929")
first, newest = {}, {}
for p in files:                                     # ascending: first sighting is the first file
    for l in open(p, encoding="utf-8"):
        r = json.loads(l)
        if (r.get("published_date") or "")[:10] < "2026-09-29" or not r.get("content"):
            continue
        b = (r.get("nexus_mind_attributes") or {}).get("belonging") or {}
        first.setdefault(r["id"], os.path.basename(p))
        newest[r["id"]] = dict(id=r["id"], title=r.get("title"), content=r["content"], url=r.get("url"),
                               source=r.get("source"), published_date=r.get("published_date"),
                               prod_version=b.get("version"), prod_stage=b.get("stage_used"),
                               prod_raw=b.get("raw_weighted_average"), prod_norm=b.get("weighted_average"),
                               newest_file=os.path.basename(p))
screen, below, low = [], [], []
for i in sorted(newest):
    r = newest[i]
    if r["prod_stage"] == "stage2" and r["prod_raw"] is not None and r["prod_raw"] >= 2.0:
        screen.append(i)
    elif r["prod_stage"] == "stage2":
        below.append(i)
    elif r["prod_stage"] == "stage1_low":
        low.append(i)
sample_below = set(random.Random(0).sample(below, 1000))
sample_low = set(random.Random(0).sample(low, 1000))
keep = [(i, "screen") for i in screen] + [(i, "below") for i in sorted(sample_below)] + [(i, "stage1_low") for i in sorted(sample_low)]
for i, s in keep:
    print(json.dumps(dict(newest[i], first_file=first[i], stratum=s), ensure_ascii=False))
with open("norm_control.jsonl", "w") as f:
    for i in sorted(newest):
        r = newest[i]
        if r["prod_version"] == "3.0" and r["prod_stage"] == "stage2" and r["prod_raw"] is not None:
            f.write(json.dumps(dict(id=i, raw=r["prod_raw"], norm=r["prod_norm"])) + "\n")
print(f"{len(files)} files {files[0][-30:]}..{files[-1][-30:]}; ids {len(newest)}; screen {len(screen)}; "
      f"below {len(below)} (sampled 1000); stage1_low {len(low)} (sampled 1000); other stages "
      f"{len(newest) - len(screen) - len(below) - len(low)}", file=sys.stderr)
