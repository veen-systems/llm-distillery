#!/usr/bin/env python3
"""Apply PREREGISTRATION.md's bar to the ground_truth_gate.py reports. Prints; decides nothing else.

Inputs: gate_adjudicated.json and gate_oracle.json next to this file, each written by
ground_truth_gate.py with one --model per arm (v8, adj1, adj3, adj2) on v8's 660 test ids.

Rule (adjudicated labels, band = the gate's #95 [lo, hi]):
  WIN  iff retrain spec lo > v8 spec hi  AND  retrain recall hi >= v8 recall lo
  LOSE iff retrain spec hi < v8 spec lo  OR   retrain recall hi <  v8 recall lo
  else NOT DISTINGUISHABLE
adj2 is diagnostic only and gets a verdict line marked as such.
Exit 0 always when the inputs are sound; 3 on missing arms (plumbing).
"""
# design-weights: NOT READ. Every figure is an unweighted SAMPLE quantity over the 660
# design-weighted v8 test rows (25.1x span; weights in datasets/scored/human_thriving_v8/corpus.jsonl),
# as in v8's own 2026-09-06 gate. The comparison is paired on identical rows; nothing here is a
# production rate.
import json
import sys
from pathlib import Path

F = Path(__file__).resolve().parent
ARMS = ["v8", "adj1", "adj3", "adj2"]


def load(name):
    p = F / name
    if not p.exists():
        print(f"missing {p}", file=sys.stderr)
        raise SystemExit(3)
    models = json.loads(p.read_text())["models"]
    missing = [a for a in ARMS if a not in models]
    if missing:
        print(f"{name}: arms missing {missing}", file=sys.stderr)
        raise SystemExit(3)
    return models


def verdict(r, b):
    s_lo, s_hi = r["specificity_band"]
    bs_lo, bs_hi = b["specificity_band"]
    r_hi = r["recall_band"][1]
    b_lo = b["recall_band"][0]
    if s_hi < bs_lo or r_hi < b_lo:
        return "LOSE"
    if s_lo > bs_hi and r_hi >= b_lo:
        return "WIN"
    return "NOT DISTINGUISHABLE"


def table(models, title):
    print(f"\n{title}")
    print(f"{'arm':6} {'pos':>4} {'TP':>3} {'FP':>3} {'spec':>6} {'spec band':>16} {'recall':>6} {'recall band':>14} {'indet':>5}")
    for a in ARMS:
        m = models[a]
        sb, rb = m["specificity_band"], m["recall_band"]
        print(f"{a:6} {m['positives']:4d} {m['tp']:3d} {m['fp']:3d} {m['specificity']:6.4f} "
              f"[{sb[0]:.4f}, {sb[1]:.4f}] {m['recall']:6.3f} [{rb[0]:.3f}, {rb[1]:.3f}] {m['n_indeterminate']:5d}")


adj = load("gate_adjudicated.json")
ora = load("gate_oracle.json")
table(adj, "PRIMARY — adjudicated labels (human_thriving_v8_adj1/test.jsonl), op-point 4.5, calibrated")
table(ora, "SECONDARY — oracle labels (human_thriving_v8/test.jsonl), same rows; not gating")

print("\nVerdicts (PREREGISTRATION.md, adjudicated labels):")
for a in ["adj1", "adj3", "adj2"]:
    tag = "  (diagnostic only — cannot win on its own)" if a == "adj2" else ""
    print(f"  {a}: {verdict(adj[a], adj['v8'])}{tag}")
