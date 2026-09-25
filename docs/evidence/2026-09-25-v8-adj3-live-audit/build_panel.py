#!/usr/bin/env python3
"""Build the adj3-vs-v8 live-audit panel exactly as PREREGISTRATION.md fixes it. Writes nothing
it has not checked first; exits 1 on the control stop condition, 3 on plumbing.

Inputs (gitignored, local): datasets/audit/ht_2026-09-25/{chunk_*.jsonl, meta.jsonl,
scores/<model>/<chunk>/scores_calibrated.jsonl} as rsynced from b650.
Outputs (tracked, beside this file): groups.json (sizes + control), datasets/audit/.../key.jsonl (id ->
group; NEVER shown to a judge, copied here only after judging), input_A*.jsonl / input_B*.jsonl (blind batches).
"""
# design-weights: READ. The panel samples groups A, R and B at different rates; every rate the
# analysis publishes is re-weighted by the group sizes N_A, N_R, N_B written to groups.json here.
# No raw pooled share is computed in this file. The production week itself is the population,
# not a design-weighted draw.
import json
import random
import sys
from pathlib import Path

F = Path(__file__).resolve().parent
REPO = F.parents[2]
sys.path.insert(0, str(REPO))
from scripts.gate.ground_truth_gate import load_scores, load_scoring_spec  # noqa: E402

D = REPO / "datasets/audit/ht_2026-09-25"
OP, FLOOR, SEED = 4.5, 0.16, 20260925
CAP = {"A": 150, "R": 150, "B": 60}
BATCH = 28
PILOT = REPO / "docs/evidence/2026-09-24-thriving-adjudication-pilot"


def fatal(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(3)


spec = load_scoring_spec(REPO / "filters/human_thriving/v8/config.yaml")
if spec is None:
    fatal("config spec failed to load -- refusing to fall back to defaults")

meta = {r["id"]: r for r in map(json.loads, open(D / "meta.jsonl"))}
chunks = sorted(D.glob("chunk_*.jsonl"))
if len(chunks) != 7:
    fatal(f"expected 7 chunks, found {len(chunks)}")
sc = {}
for m in ["v8", "v8_adj3"]:
    sc[m] = {}
    for c in chunks:
        p = D / "scores" / m / c.stem / "scores_calibrated.jsonl"
        if not p.exists():
            fatal(f"missing {p}")
        sc[m].update(load_scores(p, spec=spec))
    if set(sc[m]) != set(meta):
        fatal(f"{m}: scored ids != meta ids ({len(sc[m])} vs {len(meta)})")

# Exclusion: every id in any v8/adj* split, and the whole more-positives sample.
excl = set()
for d in ["human_thriving_v8", "human_thriving_v8_adj1", "human_thriving_v8_adj2", "human_thriving_v8_adj3"]:
    for s in ["train", "val", "test"]:
        excl |= {json.loads(l)["id"] for l in open(REPO / f"datasets/training/{d}/{s}.jsonl")}
excl |= {json.loads(l)["id"] for l in open(REPO / "docs/evidence/2026-09-24-thriving-more-positives/sample.jsonl")}
ids = sorted(i for i in meta if i not in excl)
n_excl = len(meta) - len(ids)

# Control: b650-v8 vs production v8, outside the noise band.
prod_pass = {i for i in ids if (meta[i]["prod_v8_raw"] or 0) >= OP}
b650_pass = {i for i in ids if sc["v8"][i] >= OP}
union = prod_pass | b650_pass
disagree = union ^ (prod_pass & b650_pass)
outside = [i for i in disagree if abs(sc["v8"][i] - OP) >= FLOOR and abs((meta[i]["prod_v8_raw"] or 0) - OP) >= FLOOR]
ctrl = {"prod_v8_passers": len(prod_pass), "b650_v8_passers": len(b650_pass), "union": len(union),
        "disagree": len(disagree), "disagree_outside_band": len(outside),
        "share_outside_band": round(len(outside) / len(union), 4) if union else None}

groups = {"A": [], "R": [], "B": []}
for i in ids:
    v, a = sc["v8"][i] >= OP, sc["v8_adj3"][i] >= OP
    if a and not v:
        groups["A"].append(i)
    elif v and not a:
        groups["R"].append(i)
    elif v and a:
        groups["B"].append(i)

out = {"window": "filtered_20260918_145649.jsonl -> filtered_20260925_093350.jsonl", "cycles": 42,
       "stage2_ids": len(meta), "excluded_training_overlap": n_excl, "audit_ids": len(ids),
       "control": ctrl, "N": {g: len(v) for g, v in groups.items()}}
print(json.dumps(out, indent=1))
(F / "groups.json").write_text(json.dumps(out, indent=1) + "\n")
if ctrl["share_outside_band"] is None or ctrl["share_outside_band"] > 0.10:
    print("STOP: the control failed -- b650 re-scoring is not production-faithful (PREREGISTRATION.md)")
    raise SystemExit(1)

rng = random.Random(SEED)
panel = []
for g in ["A", "R", "B"]:
    pool = sorted(groups[g])
    pick = pool if len(pool) <= CAP[g] else sorted(rng.sample(pool, CAP[g]))
    panel += [(i, g) for i in pick]

text = {}
want = {i for i, _ in panel}
for c in chunks:
    for r in map(json.loads, open(c)):
        if r["id"] in want:
            text[r["id"]] = r

controls = []
ctrl_ids = {r["id"]: r["expected"] for r in map(json.loads, open(PILOT / "key.jsonl")) if r.get("stratum") == "control"}
for p in sorted(PILOT.glob("input_A*.jsonl")):
    for r in map(json.loads, open(p)):
        if r["id"] in ctrl_ids and r["id"] not in {c["id"] for c in controls}:
            controls.append(r)
if len(controls) != 4:
    fatal(f"expected 4 pilot controls, found {len(controls)}")


def blind(r):
    m = meta.get(r["id"], {})
    return {"id": r["id"], "title": r.get("title", ""), "url": r.get("url", m.get("url")),
            "source": r.get("source", m.get("source")), "content": r.get("content", "")}


rows_a = [blind(text[i]) for i, _ in panel] + [blind(c) for c in controls]
rng.shuffle(rows_a)
b_ids = set(rng.sample(sorted(want), round(0.2 * len(want))))
rows_b = [blind(text[i]) for i in sorted(b_ids)]
rng.shuffle(rows_b)

for pat in ["input_A*.jsonl", "input_B*.jsonl"]:
    for old in F.glob(pat):
        old.unlink()
for tag, rows in [("A", rows_a), ("B", rows_b)]:
    for k in range(0, len(rows), BATCH):
        with open(F / f"input_{tag}{k // BATCH + 1:02d}.jsonl", "w") as w:
            for r in rows[k:k + BATCH]:
                w.write(json.dumps(r, ensure_ascii=False) + "\n")
# The key lives OUTSIDE the evidence dir until judging is done: a judge in the repo must not be
# able to find which model surfaced what. It is copied beside this file afterwards.
with open(D / "key.jsonl", "w") as w:
    for i, g in panel:
        w.write(json.dumps({"id": i, "group": g, "in_B": i in b_ids,
                            "v8": round(sc["v8"][i], 4), "adj3": round(sc["v8_adj3"][i], 4),
                            "prod_v8": meta[i]["prod_v8_raw"], "content_length": len(text[i].get("content", ""))}) + "\n")
    for c in controls:
        w.write(json.dumps({"id": c["id"], "group": "control", "expected": ctrl_ids[c["id"]]}) + "\n")
print(f"panel {len(panel)} + 4 controls in pass A ({-(-len(rows_a) // BATCH)} batches); pass B {len(rows_b)} rows")
