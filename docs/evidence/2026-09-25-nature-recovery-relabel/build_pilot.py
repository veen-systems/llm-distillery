#!/usr/bin/env python3
"""Build the Nature recovery relabel PILOT panel (PILOT_PREREGISTRATION.md). Exit 3 on plumbing."""
# design-weights: READ. Two equal strata drawn from unequal pools (586 : 237); the pilot reports per-stratum
# rates and re-weights any pooled rate by those N. No pooled share is computed here.
import json
import random
import sys
from pathlib import Path

F = Path(__file__).resolve().parent
REPO = F.parents[2]
sys.path.insert(0, str(REPO))
from scripts.gate.ground_truth_gate import load_labels, load_scoring_spec  # noqa: E402

AUDIT = REPO / "docs/evidence/2026-09-25-nature-recovery-miss-audit"
KEY = REPO / "datasets/audit/nr_relabel_pilot_key.jsonl"
SEED, OP = 20260930, 3.75
spec = load_scoring_spec(REPO / "filters/nature_recovery/v4/config.yaml")
if spec is None:
    raise SystemExit(3)
rows, wa = {}, {}
for s in ["train", "val", "test"]:
    p = REPO / f"datasets/training/nature_recovery_v4/{s}.jsonl"
    for r in map(json.loads, open(p)):
        rows[r["id"]] = dict(r, split=s)
    wa.update(load_labels(p, spec=spec))
hi = sorted(i for i in wa if wa[i] >= OP)
mid = sorted(i for i in wa if 2.0 <= wa[i] < OP)
if (len(hi), len(mid)) != (586, 237):
    print(f"pools {len(hi)}/{len(mid)} != 586/237", file=sys.stderr)
    raise SystemExit(3)
rng = random.Random(SEED)
panel = [(i, "ge3.75") for i in sorted(rng.sample(hi, 25))] + [(i, "b2.0_3.75") for i in sorted(rng.sample(mid, 25))]
ctrl = {k["id"]: k["expected"] for k in map(json.loads, open(AUDIT / "key.jsonl")) if k.get("stratum") == "control"}
ctrl_rows = {}
for p in sorted(AUDIT.glob("input_A*.jsonl")):
    for r in map(json.loads, open(p)):
        if r["id"] in ctrl:
            ctrl_rows[r["id"]] = r
if len(ctrl_rows) != 4:
    raise SystemExit(3)


def blind(r):
    return {"id": r["id"], "title": r.get("title", ""), "url": r.get("url", ""),
            "source": r.get("source", ""), "content": r.get("content", "")}


items = [blind(rows[i]) for i, _ in panel] + [blind(r) for r in ctrl_rows.values()]
for tag, seed in [("A", SEED + 1), ("B", SEED + 2)]:
    order = list(items)
    random.Random(seed).shuffle(order)
    for k, chunk in enumerate([order[:27], order[27:]], 1):
        with open(F / f"pilot_input_{tag}{k}.jsonl", "w") as w:
            for r in chunk:
                w.write(json.dumps(r, ensure_ascii=False) + "\n")
KEY.parent.mkdir(parents=True, exist_ok=True)
with open(KEY, "w") as w:
    for i, st in panel:
        w.write(json.dumps({"id": i, "stratum": st, "oracle_wa": round(wa[i], 4), "split": rows[i]["split"]}) + "\n")
    for i, e in ctrl.items():
        w.write(json.dumps({"id": i, "stratum": "control", "expected": e}) + "\n")
print(f"pilot: 50 + 4 controls; passes A and B, 2 batches each (27 rows); key -> {KEY}")
