#!/usr/bin/env python3
"""adj3 = adj2 + the 439 hard negatives (PLAN.md, "Hard negatives"): oracle k=3 mean per dimension,
each capped at 2.0 whatever the oracle's verdict; oracle in_scope majorities are counted, not obeyed.
Exit 3 on plumbing (ragged k, wrong prompt hash, missing rows)."""
import collections
import json
import os
import random
import statistics
import sys
from pathlib import Path

X = Path(__file__).resolve().parent
REPO = X.parents[2]
sys.path.insert(0, str(REPO / "scripts" / "gate"))
import adverse_suite_gate as G  # noqa: E402

S = {json.loads(l)["id"]: json.loads(l) for l in open(X / "sample.jsonl", encoding="utf-8")}
want = {json.loads(l)["id"] for l in open(X / "oracle_neg_input.jsonl", encoding="utf-8")}
per = collections.defaultdict(list)
for k in (1, 2, 3):
    seen = set()
    for line in open(X / "runs" / f"neg_{k}.jsonl", encoding="utf-8"):
        r = json.loads(line)
        if "human_thriving_analysis" not in r:
            continue
        if r["id"] in seen:
            G.fatal(f"FATAL: neg_{k}: {r['id']} twice")
        seen.add(r["id"])
        a = r["human_thriving_analysis"]
        if a.get("prompt_hash") != "c4705408c477":
            G.fatal(f"FATAL: neg_{k}: prompt hash {a.get('prompt_hash')}")
        per[r["id"]].append(a)
if set(per) != want or any(len(v) != 3 for v in per.values()):
    G.fatal(f"FATAL: {len(per)} ids vs {len(want)} wanted; ragged: "
            f"{[i for i, v in per.items() if len(v) != 3][:3]}")

rows, oracle_in, uncapped_hi = [], 0, 0
for i in sorted(per):
    rs = per[i]
    if collections.Counter(a.get("scope_verdict") for a in rs)["in_scope"] >= 2:
        oracle_in += 1
    dims = [statistics.fmean(float(a[d]["score"]) for a in rs) for d in G.DIMS]
    if G.weighted_average(dict(zip(G.DIMS, dims))) >= 4.5:
        uncapped_hi += 1
    rows.append((i, [min(x, 2.0) for x in dims]))
print(f"hard negatives: {len(rows)}; oracle k=3 majority in_scope on {oracle_in} "
      f"({oracle_in / len(rows):.1%}); uncapped oracle label >= 4.5 on {uncapped_hi} "
      f"— i.e. the oracle itself would have taught the student to surface these")

rng = random.Random(20260928)
rng.shuffle(rows)
n = len(rows)
parts = {"train": rows[:round(0.8 * n)], "val": rows[round(0.8 * n):round(0.9 * n)], "test": rows[round(0.9 * n):]}
src, dst = REPO / "datasets/training/human_thriving_v8_adj2", REPO / "datasets/training/human_thriving_v8_adj3"
os.makedirs(dst, exist_ok=True)
for sp in ("train", "val", "test"):
    base = [json.loads(l) for l in open(src / f"{sp}.jsonl", encoding="utf-8")]
    names = base[0]["dimension_names"]
    for i, labels in parts[sp]:
        s = S[i]
        base.append({"id": i, "url": s.get("url"), "title": s.get("title"), "content": s.get("content"),
                     "labels": labels, "dimension_names": names})
    with open(dst / f"{sp}.jsonl", "w", encoding="utf-8") as f:
        for r in base:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    pos = sum(G.weighted_average(dict(zip(G.DIMS, r["labels"]))) >= 4.5 for r in base)
    print(f"{sp:5} rows {len(base)} (+{len(parts[sp])} hard negatives)  labels >= 4.5: {pos}")
