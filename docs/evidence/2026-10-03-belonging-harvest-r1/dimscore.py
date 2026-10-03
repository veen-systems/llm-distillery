#!/usr/bin/env python3
"""Belonging harvest r1: combine the k=3 Gemini Flash dimension scorings (belonging v1's own prompt, via
ground_truth.batch_scorer, output datasets/belonging_harvest_r1/dimscore/run{1,2,3}/belonging/) into labels.

    .venv/bin/python docs/evidence/2026-10-03-belonging-harvest-r1/dimscore.py

Label per dimension = the mean of the 3 runs. Weighted average = belonging v1's DIMENSION_WEIGHTS with its gatekeeper
(community_fabric < 3.0 caps at 3.42), read from filters/belonging/v1/base_scorer.py, never restated here. A positive
whose label weighted average is < 4.0 (v1's medium threshold) is reported and DROPPED (plan, phase 4).
Every positive must have all 3 runs; a missing one raises.
"""
import ast, json, statistics, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / "datasets" / "belonging_harvest_r1"
src = (ROOT / "filters" / "belonging" / "v1" / "base_scorer.py").read_text()
consts = {}
for node in ast.walk(ast.parse(src)):
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in (
            "DIMENSION_WEIGHTS", "GATEKEEPER_DIMENSION", "GATEKEEPER_MIN", "GATEKEEPER_CAP"):
        consts[node.targets[0].id] = ast.literal_eval(node.value)
W = consts["DIMENSION_WEIGHTS"]
if abs(sum(W.values()) - 1) > 1e-9 or len(consts) != 4:
    raise SystemExit(f"could not read v1 constants: {consts}")


def wavg(s):
    w = sum(W[d] * s[d] for d in W)
    if s[consts["GATEKEEPER_DIMENSION"]] < consts["GATEKEEPER_MIN"]:
        w = min(w, consts["GATEKEEPER_CAP"])
    return w


ids = [json.loads(l)["id"] for l in open(D / "positives_r1_articles.jsonl")]
runs = []
for k in (1, 2, 3):
    r = {}
    for f in sorted((D / "dimscore" / f"run{k}" / "belonging").glob("scored_batch_*.jsonl")):
        for l in open(f):
            x = json.loads(l)
            r[x["id"]] = {d: float(x["belonging_analysis"][d]["score"]) for d in W}
    missing = set(ids) - set(r)
    if missing:
        raise SystemExit(f"run{k}: {len(missing)} positives unscored, e.g. {sorted(missing)[:3]}")
    runs.append(r)
out, kept, dropped = D / "positives_r1_labels.jsonl", 0, []
spread = []
with open(out, "w") as f:
    for i in ids:
        lab = {d: round(statistics.mean(r[i][d] for r in runs), 3) for d in W}
        per_run = [wavg(r[i]) for r in runs]
        spread.append(max(per_run) - min(per_run))
        wa = wavg(lab)
        keep = wa >= 4.0
        kept += keep
        if not keep:
            dropped.append((i, round(wa, 2)))
        f.write(json.dumps(dict(id=i, labels=lab, weighted_average=round(wa, 3), per_run_wavg=[round(x, 3) for x in per_run],
                                keep=keep)) + "\n")
print(f"{len(ids)} positives; kept {kept} (label weighted avg >= 4.0); dropped {len(dropped)}: {dropped}")
was = [json.loads(l)["weighted_average"] for l in open(out)]
print(f"label weighted avg: median {statistics.median(was):.2f}, min {min(was):.2f}, max {max(was):.2f}; "
      f">= 7.0 (v1 high): {sum(w >= 7 for w in was)}")
print(f"run-to-run spread of the weighted avg: median {statistics.median(spread):.2f}, max {max(spread):.2f}")
print("weights read from base_scorer.py:", W, {k: v for k, v in consts.items() if k != 'DIMENSION_WEIGHTS'})
