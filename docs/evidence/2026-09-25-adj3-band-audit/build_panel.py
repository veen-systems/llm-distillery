#!/usr/bin/env python3
"""Build the adj3 band-audit panel as PREREGISTRATION.md fixes it. Exit 3 on any plumbing mismatch.

Writes beside this file: input_A*.jsonl / input_B*.jsonl (blind) and bands.json (sub-band N).
The key (id -> sub-band) goes to datasets/audit/ht_2026-09-25/band_key.jsonl, out of the judges'
reach, and is copied here only after judging.
"""
# design-weights: READ. Sub-bands are sampled at different rates; the analysis re-weights every
# sub-band by its N from bands.json. No raw pooled share is computed here.
import json
import random
import sys
from pathlib import Path

F = Path(__file__).resolve().parent
REPO = F.parents[2]
sys.path.insert(0, str(REPO))
from scripts.gate.ground_truth_gate import load_scores, load_scoring_spec  # noqa: E402

D = REPO / "datasets/audit/ht_2026-09-25"
LIVE = REPO / "docs/evidence/2026-09-25-v8-adj3-live-audit"
PILOT = REPO / "docs/evidence/2026-09-24-thriving-adjudication-pilot"
SEED, BATCH, DRAW = 20260926, 56, 40
BANDS = [("b4.25", 4.25, 4.5, 182), ("b4.0", 4.0, 4.25, 197), ("b3.75", 3.75, 4.0, 245), ("b3.5", 3.5, 3.75, 313)]


def fatal(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(3)


spec = load_scoring_spec(REPO / "filters/human_thriving/v8/config.yaml")
if spec is None:
    fatal("config spec failed to load")
a3 = {}
for p in sorted(D.glob("scores/v8_adj3/*/scores_calibrated.jsonl")):
    a3.update(load_scores(p, spec=spec))

excl = set()
for d in ["human_thriving_v8", "human_thriving_v8_adj1", "human_thriving_v8_adj2", "human_thriving_v8_adj3"]:
    for s in ["train", "val", "test"]:
        excl |= {json.loads(l)["id"] for l in open(REPO / f"datasets/training/{d}/{s}.jsonl")}
excl |= {json.loads(l)["id"] for l in open(REPO / "docs/evidence/2026-09-24-thriving-more-positives/sample.jsonl")}
ids = sorted(i for i in a3 if i not in excl)
live = json.loads((LIVE / "groups.json").read_text())
if len(ids) != live["audit_ids"]:
    fatal(f"audit ids {len(ids)} != live audit's {live['audit_ids']}")

rng = random.Random(SEED)
panel, bands = [], {}
for name, lo, hi, n_expected in BANDS:
    pool = [i for i in ids if lo <= a3[i] < hi]
    if len(pool) != n_expected:
        fatal(f"{name}: N={len(pool)}, the pre-registration says {n_expected}")
    bands[name] = {"lo": lo, "hi": hi, "N": len(pool)}
    panel += [(i, name) for i in sorted(rng.sample(pool, DRAW))]
n_ge45 = sum(a3[i] >= 4.5 for i in ids)
out = {"N_ge_4.5": n_ge45, "bands": bands, "cycles": 42}
(F / "bands.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out))

want = {i for i, _ in panel}
text = {}
for c in sorted(D.glob("chunk_*.jsonl")):
    for r in map(json.loads, open(c)):
        if r["id"] in want:
            text[r["id"]] = r
if len(text) != len(want):
    fatal(f"text found for {len(text)} of {len(want)}")
meta = {r["id"]: r for r in map(json.loads, open(D / "meta.jsonl")) if r["id"] in want}

ctrl_exp = {r["id"]: r["expected"] for r in map(json.loads, open(PILOT / "key.jsonl")) if r.get("stratum") == "control"}
controls = {}
for p in sorted(PILOT.glob("input_A*.jsonl")):
    for r in map(json.loads, open(p)):
        if r["id"] in ctrl_exp:
            controls[r["id"]] = r
if len(controls) != 4:
    fatal(f"expected 4 pilot controls, found {len(controls)}")


def blind(r):
    m = meta.get(r["id"], {})
    return {"id": r["id"], "title": r.get("title", ""), "url": r.get("url", m.get("url")),
            "source": r.get("source", m.get("source")), "content": r.get("content", "")}


rows_a = [blind(text[i]) for i, _ in panel] + [blind(c) for c in controls.values()]
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
with open(D / "band_key.jsonl", "w") as w:
    for i, b in panel:
        w.write(json.dumps({"id": i, "band": b, "in_B": i in b_ids, "adj3": round(a3[i], 4)}) + "\n")
    for cid, e in ctrl_exp.items():
        w.write(json.dumps({"id": cid, "band": "control", "expected": e}) + "\n")
print(f"panel {len(panel)} + 4 controls in pass A ({-(-len(rows_a) // BATCH)} batches); pass B {len(rows_b)} rows")
