#!/usr/bin/env python3
"""Draw the Nature recovery miss-audit sample ON SADALSUUD (the article text lives there).

Run: ssh sadalsuud 'cd ~/local_dev/NexusMind/data/filtered && python3 -' < build_sample.py > sample.jsonl
Prints one JSON line per drawn article, then a final {"_strata": ...} line with every stratum's N.

Population: articles that passed >= 1 OTHER lens that week (stage2 raw >= that lens's runtime op-point),
same 42-cycle window as the live audits. Strata by what nature_recovery (v4, op-point 3.75) did with them.
"""
# design-weights: READ. Strata are drawn at different rates; every per-week estimate in analyse.py is
# re-weighted by the N printed in the final line. No raw pooled share is computed here.
import glob
import json
import os
import random

OP = {"uplifting": 4.5, "human_thriving": 4.5, "cultural_discovery": 4.0, "belonging": 4.0, "solutions": 2.25}
NR_OP = 3.75
SEED = 20260928
DRAW = {"nr_passes": 30, "near_3.0_3.75": 62, "low_2.0_3.0": 50, "probe_screened": 100, "very_low_lt2": 60}


def in_window(f):
    b = os.path.basename(f)[9:24]
    return "20260918_145649" <= b <= "20260925_093350"


passed = {}
for lens, op in OP.items():
    for f in filter(in_window, sorted(glob.glob(lens + "/filtered_*.jsonl"))):
        for line in open(f):
            r = json.loads(line)
            h = (r.get("nexus_mind_attributes") or {}).get(lens) or {}
            if h.get("stage_used") != "stage1_low" and (h.get("raw_weighted_average") or 0) >= op:
                passed.setdefault(r["id"], set()).add(lens)

nr, text = {}, {}
for f in filter(in_window, sorted(glob.glob("nature_recovery/filtered_*.jsonl"))):
    for line in open(f):
        r = json.loads(line)
        if r["id"] not in passed:
            continue
        h = r["nexus_mind_attributes"].get("nature_recovery") or {}
        nr[r["id"]] = (h.get("stage_used"), h.get("raw_weighted_average") or 0.0)
        text[r["id"]] = {"title": r.get("title", ""), "content": r.get("content", ""),
                         "url": r.get("url"), "source": r.get("source")}


def stratum(stage, raw):
    if stage == "stage1_low":
        return "probe_screened"
    if raw >= NR_OP:
        return "nr_passes"
    if raw >= 3.0:
        return "near_3.0_3.75"
    if raw >= 2.0:
        return "low_2.0_3.0"
    return "very_low_lt2"


pools = {}
for i, (st, raw) in nr.items():
    pools.setdefault(stratum(st, raw), []).append(i)
rng = random.Random(SEED)
for s in sorted(DRAW):
    pool = sorted(pools.get(s, []))
    pick = pool if len(pool) <= DRAW[s] else sorted(rng.sample(pool, DRAW[s]))
    for i in pick:
        print(json.dumps({"id": i, "stratum": s, "lenses": sorted(passed[i]), "nr_stage": nr[i][0],
                          "nr_raw": round(nr[i][1], 4), **text[i]}, ensure_ascii=False))
print(json.dumps({"_strata": {s: len(v) for s, v in sorted(pools.items())}, "other_lens_passers": len(passed),
                  "with_nr_score": len(nr)}))
