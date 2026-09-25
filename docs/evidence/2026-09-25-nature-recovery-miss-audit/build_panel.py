#!/usr/bin/env python3
"""Blind batches for the Nature recovery miss audit, from build_sample.py's output.

Reads datasets/audit/nr_2026-09-25/sample.jsonl (gitignored). Writes beside this file: strata.json and
input_A*/input_B*.jsonl (blind: id, title, url, source, content). The key (id -> stratum, nr score) goes to
datasets/audit/nr_2026-09-25/key.jsonl, out of the judges' reach, and is copied here only after judging.
"""
# design-weights: READ. Strata are drawn at different rates; analyse.py re-weights every stratum by its N
# from strata.json. No raw pooled share is computed here.
import json
import random
from pathlib import Path

F = Path(__file__).resolve().parent
REPO = F.parents[2]
D = REPO / "datasets/audit/nr_2026-09-25"
SEED, BATCH, B_SHARE = 20260928, 56, 0.3
CONTROLS = {"spanish_la_vanguardia_28c048d44378": "in_scope", "east_african_new_times_rw_07ce2bcd52b6": "in_scope",
            "community_social_hacker_news_6e92bdd16207": "out_of_scope", "semantic_scholar_d6a6f7990cb9": "out_of_scope"}

rows = [json.loads(l) for l in open(D / "sample.jsonl")]
meta = rows.pop()
assert "_strata" in meta, "last line must be the strata record"
(F / "strata.json").write_text(json.dumps(meta, indent=1) + "\n")
ctrl = {r["id"]: r for r in map(json.loads, open(REPO / "datasets/training/nature_recovery_v4/test.jsonl")) if r["id"] in CONTROLS}
assert len(ctrl) == 4, len(ctrl)
assert not set(ctrl) & {r["id"] for r in rows}


def blind(r):
    return {"id": r["id"], "title": r.get("title", ""), "url": r.get("url"), "source": r.get("source"),
            "content": r.get("content", "")}


rng = random.Random(SEED)
rows_a = [blind(r) for r in rows] + [blind(c) for c in ctrl.values()]
rng.shuffle(rows_a)
b_ids = set(rng.sample(sorted(r["id"] for r in rows), round(B_SHARE * len(rows))))
rows_b = [blind(r) for r in rows if r["id"] in b_ids]
rng.shuffle(rows_b)
for pat in ["input_A*.jsonl", "input_B*.jsonl"]:
    for old in F.glob(pat):
        old.unlink()
for tag, rs in [("A", rows_a), ("B", rows_b)]:
    for k in range(0, len(rs), BATCH):
        with open(F / f"input_{tag}{k // BATCH + 1:02d}.jsonl", "w") as w:
            for r in rs[k:k + BATCH]:
                w.write(json.dumps(r, ensure_ascii=False) + "\n")
with open(D / "key.jsonl", "w") as w:
    for r in rows:
        w.write(json.dumps({"id": r["id"], "stratum": r["stratum"], "in_B": r["id"] in b_ids,
                            "nr_stage": r["nr_stage"], "nr_raw": r["nr_raw"], "lenses": r["lenses"]}) + "\n")
    for cid, e in CONTROLS.items():
        w.write(json.dumps({"id": cid, "stratum": "control", "expected": e}) + "\n")
print(f"{len(rows)} + 4 controls in pass A ({-(-len(rows_a) // BATCH)} batches); pass B {len(rows_b)}; strata {meta['_strata']}")
