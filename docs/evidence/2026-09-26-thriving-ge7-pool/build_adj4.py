#!/usr/bin/env python3
"""adj4 (v10 candidate) = adj3 (v9's training data) + this pool's 177 oracle-labelled positives
(alias control d=+0.017 -> MIX) + 471 hard negatives (every dimension capped at 2.0). Each added
set is split 80/10/10 separately, seed 20260929. Refuses to run if any new id is already in adj3."""
import json, os, random, sys
from pathlib import Path
X = Path(__file__).resolve().parent
REPO = X.parents[2]
sys.path.insert(0, str(REPO / "scripts" / "gate"))
import adverse_suite_gate as G  # noqa: E402
SRC, DST = REPO / "datasets/training/human_thriving_v8_adj3", REPO / "datasets/training/human_thriving_v8_adj4"
pool = {json.loads(l)["id"]: json.loads(l) for l in open(X / "pool.jsonl", encoding="utf-8")}
base_ids = {json.loads(l)["id"] for sp in ("train", "val", "test") for l in open(SRC / f"{sp}.jsonl", encoding="utf-8")}
sets = {}
for name, fn in (("positives", "new_labels.jsonl"), ("negatives", "neg_labels.jsonl")):
    rows = [json.loads(l) for l in open(X / fn, encoding="utf-8")]
    rows.sort(key=lambda r: r["id"])
    clash = base_ids.intersection(r["id"] for r in rows)
    if clash:
        G.fatal(f"FATAL: {name}: {len(clash)} ids already in adj3, e.g. {sorted(clash)[:3]}")
    if any(r["dimension_names"] != list(G.DIMS) for r in rows):
        G.fatal(f"FATAL: {name}: dimension order differs from the gate's")
    random.Random(20260929).shuffle(rows)
    n = len(rows)
    sets[name] = {"train": rows[:round(0.8 * n)], "val": rows[round(0.8 * n):round(0.9 * n)], "test": rows[round(0.9 * n):]}
os.makedirs(DST, exist_ok=True)
for sp in ("train", "val", "test"):
    out = [json.loads(l) for l in open(SRC / f"{sp}.jsonl", encoding="utf-8")]
    names = out[0]["dimension_names"]
    added = {}
    for name, parts in sets.items():
        for r in parts[sp]:
            p = pool[r["id"]]
            out.append({"id": r["id"], "url": p["url"], "title": p["title"], "content": p["content"],
                        "labels": r["labels"], "dimension_names": names})
        added[name] = len(parts[sp])
    with open(DST / f"{sp}.jsonl", "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    pos = sum(G.weighted_average(dict(zip(G.DIMS, r["labels"]))) >= 4.5 for r in out)
    print(f"{sp:5} rows {len(out)} (+{added['positives']} pos, +{added['negatives']} neg)  labels >= 4.5: {pos}")
