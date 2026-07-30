#!/usr/bin/env python3
"""Reconstruct v5_train_seed.jsonl (LD#83 corrective retrain).

v5 seed = v4b_train_seed.jsonl + the 21 panel-majority-obituary FN-delta rows
from the in-corpus heldout, relabeled positive. The 21 ids come from the
committed rollup artifact, so the corpus is reproducible from repo + gpu-server
data even though training/data/ itself is not under git.

Usage (on gpu-server):
    python3 build_v5_seed.py \
        --rollup validation/artifacts/rollup_fn_delta_fp5_2026-07-30.json \
        --base training/data/v4b_train_seed.jsonl \
        --heldout training/data/heldout_corpus.jsonl \
        --out training/data/v5_train_seed.jsonl
"""
import argparse, json

ap = argparse.ArgumentParser()
ap.add_argument("--rollup", required=True)
ap.add_argument("--base", required=True)
ap.add_argument("--heldout", required=True)
ap.add_argument("--out", required=True)
args = ap.parse_args()

rollup = json.load(open(args.rollup, encoding="utf-8"))
hard_pos = [x["id"] for x in rollup["fn_delta"] if x["majority"] == "obituary"]
assert len(hard_pos) == 21, f"expected 21 panel-majority ids, got {len(hard_pos)}"

held = {}
for l in open(args.heldout, encoding="utf-8"):
    if l.strip():
        r = json.loads(l)
        held[r["id"]] = r
missing = [i for i in hard_pos if i not in held]
assert not missing, f"ids missing from heldout corpus: {missing}"

n = pos = 0
with open(args.out, "w", encoding="utf-8") as out:
    for l in open(args.base, encoding="utf-8"):
        if not l.strip():
            continue
        out.write(l if l.endswith("\n") else l + "\n")
        n += 1
        pos += json.loads(l)["label"] == "positive"
    for i in hard_pos:
        r = dict(held[i])
        r["label"] = "positive"
        r["provenance"] = "fn_delta_hard_positive_2026-07-30_panel21"
        out.write(json.dumps(r, ensure_ascii=False) + "\n")
        n += 1
        pos += 1

print(f"{args.out}: {n} rows, {pos} positive")
assert n == 11329 and pos == 2694, "row counts diverge from the trained v5 corpus"
