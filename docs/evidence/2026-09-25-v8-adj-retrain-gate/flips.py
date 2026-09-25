#!/usr/bin/env python3
"""Row-level view behind verdict.py: which of the 660 rows each retrain surfaces differently from v8.

Surfaced := the gate's recomputed calibrated weighted average >= 4.5 (config weights + gatekeeper
cap, via ground_truth_gate's own functions). Labels: adjudicated (primary) and oracle.
"""
# design-weights: NOT READ. Counts over the 660 design-weighted v8 test rows (25.1x span;
# weights in datasets/scored/human_thriving_v8/corpus.jsonl); paired rows, no production rate.
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
F = Path(__file__).resolve().parent
G = REPO / "datasets/gate/ht_v8_adj_2026-09-25"
OP, FLOOR = 4.5, 0.16

from scripts.gate.ground_truth_gate import load_labels, load_scores, load_scoring_spec

# The gate's OWN weighting, gatekeeper and loaders, so this view cannot disagree with gate_*.json.
spec = load_scoring_spec(REPO / "filters/human_thriving/v8/config.yaml")
if spec is None:
    raise SystemExit("config spec failed to load -- refusing to fall back to defaults")
adj_wa = load_labels(REPO / "datasets/training/human_thriving_v8_adj1/test.jsonl", spec=spec)
ora_wa = load_labels(REPO / "datasets/training/human_thriving_v8/test.jsonl", spec=spec)
title = {r["id"]: r.get("title", "")[:70] for r in map(json.loads, open(REPO / "datasets/training/human_thriving_v8/test.jsonl"))}
adj = {k: (v, title[k]) for k, v in adj_wa.items()}
ora = {k: (v, title[k]) for k, v in ora_wa.items()}
sc = {a: load_scores(G / a / "scores_calibrated.jsonl", spec=spec) for a in ["v8", "adj1", "adj3", "adj2"]}
for a, m in json.loads((F / "gate_adjudicated.json").read_text())["models"].items():
    fp = sum(1 for r in sc[a] if sc[a][r] >= OP and adj[r][0] < OP)
    assert fp == m["fp"], f"{a}: this view counts {fp} FPs, the gate {m['fp']}"

for a in ["adj1", "adj3", "adj2"]:
    print(f"\n== {a} vs v8 (paired, 660 rows)")
    for rid in sorted(sc["v8"]):
        s0, s1 = sc["v8"][rid] >= OP, sc[a][rid] >= OP
        if s0 == s1:
            continue
        pos_a, pos_o = adj[rid][0] >= OP, ora[rid][0] >= OP
        near = "indeterminate" if min(abs(sc["v8"][rid] - OP), abs(sc[a][rid] - OP)) < FLOOR else "determinate"
        kind = ("dropped" if s0 else "added") + " a " + ("TRUE POS" if pos_a else "negative")
        tag = " (oracle-pos, adjudicated OUT)" if pos_o and not pos_a else ""
        print(f"  {kind:22} {near:13} v8 {sc['v8'][rid]:.2f} -> {sc[a][rid]:.2f}  {rid[:34]:34} {adj[rid][1]}{tag}")
    fps = [rid for rid in sc[a] if sc[a][rid] >= OP and adj[rid][0] < OP]
    print(f"  remaining FPs (adjudicated): {[(r[:30], round(sc[a][r], 2), round(adj[r][0], 2), adj[r][1]) for r in fps]}")
