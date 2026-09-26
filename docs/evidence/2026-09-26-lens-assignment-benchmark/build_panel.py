#!/usr/bin/env python3
"""Draw the lens-assignment benchmark panel (PREREGISTRATION.md). Exit 3 on plumbing.

Input: datasets/audit/lens_bench_multi.jsonl (every article passing >= 2 reader-facing lenses in the week).
Writes: input_A*.jsonl / input_B*.jsonl (blind, shuffled per pass), strata.json; the key (stratum, lenses passed,
rule picks) to datasets/audit/lens_bench_key.jsonl, copied here only after judging.
"""
# design-weights: READ. Strata are drawn at very different rates; every reported rate is per stratum and
# re-weighted by the stratum N in strata.json. No pooled share is computed here.
import json
import random
import sys
from pathlib import Path

F = Path(__file__).resolve().parent
REPO = F.parents[2]
SRC = REPO / "datasets/audit/lens_bench_multi.jsonl"
KEY = REPO / "datasets/audit/lens_bench_key.jsonl"
SEED, BATCH = 20261001, 50
OP = {"uplifting": 4.5, "cultural_discovery": 4.0, "belonging": 4.0, "nature_recovery": 3.75, "solutions": 2.25}
NARROW = ["nature_recovery", "cultural_discovery", "belonging", "solutions", "uplifting"]
DRAW = {"NR": 25, "CD": 20, "S+U": 20, "B+U": 15, "B+S+U": 15, "B+S": 5}


def stratum(ls):
    s = set(ls)
    if "nature_recovery" in s:
        return "NR"
    if "cultural_discovery" in s:
        return "CD"
    return {frozenset({"solutions", "uplifting"}): "S+U", frozenset({"belonging", "uplifting"}): "B+U",
            frozenset({"belonging", "solutions", "uplifting"}): "B+S+U",
            frozenset({"belonging", "solutions"}): "B+S"}.get(frozenset(s), "other")


rows = [json.loads(l) for l in open(SRC)]
pools = {}
for r in rows:
    pools.setdefault(stratum(r["lenses"]), []).append(r)
N = {k: len(v) for k, v in pools.items()}
print("strata N:", N)
if "other" in N:
    print(f"  'other' ({N['other']}) is outside the pre-registered strata and is not drawn")
rng = random.Random(SEED)
panel = []
for st, k in DRAW.items():
    if len(pools.get(st, [])) < k:
        print(f"stratum {st} too small", file=sys.stderr)
        raise SystemExit(3)
    panel += [(r, st) for r in rng.sample(sorted(pools[st], key=lambda x: x["id"]), k)]


def picks(ls):
    r0 = max(ls, key=lambda l: (ls[l]["norm"] or 0))
    r1 = next(l for l in NARROW if l in ls)
    r3 = max(ls, key=lambda l: ls[l]["raw"] - OP[l])
    r3b = max(ls, key=lambda l: (ls[l]["raw"] - OP[l]) / (10 - OP[l]))
    return {"R0": r0, "R1": r1, "R3": r3, "R3b": r3b}


(F / "strata.json").write_text(json.dumps({"N": N, "drawn": DRAW, "seed": SEED}, indent=1) + "\n")
with open(KEY, "w") as w:
    for r, st in panel:
        w.write(json.dumps({"id": r["id"], "stratum": st, "lenses": sorted(r["lenses"]),
                            "scores": r["lenses"], "picks": picks(r["lenses"])}) + "\n")
blind = [{"id": r["id"], "title": r["title"], "url": r["url"], "source": r["source"], "content": r["content"],
          "passed_lenses": sorted(r["lenses"])} for r, _ in panel]
for tag, seed in [("A", SEED + 1), ("B", SEED + 2)]:
    order = list(blind)
    random.Random(seed).shuffle(order)
    for k in range(0, len(order), BATCH):
        with open(F / f"input_{tag}{k // BATCH + 1}.jsonl", "w") as w:
            for r in order[k:k + BATCH]:
                w.write(json.dumps(r, ensure_ascii=False) + "\n")
owner_order = [r["id"] for r in random.Random(SEED + 3).sample(blind, len(blind))]
(REPO / "datasets/audit/lens_bench_owner_order.json").write_text(json.dumps(owner_order))
print(f"panel {len(panel)}; judge batches of {BATCH}; owner order fixed (seed {SEED + 3})")
