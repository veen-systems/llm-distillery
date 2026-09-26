#!/usr/bin/env python3
"""Score tab-assignment rules R0/R1/R3/R3b against the judges' consensus (PREREGISTRATION.md + amendment)."""
# design-weights: READ. Strata drawn at different rates; hit rates are per stratum and N-weighted (strata.json).
import json, math, glob
from pathlib import Path
F = Path(__file__).resolve().parent
key = {k["id"]: k for k in map(json.loads, open(F / "key.jsonl"))}
N = json.loads((F / "strata.json").read_text())["N"]
ans = {"A": {}, "B": {}}
for p in glob.glob(str(F / "out_*.jsonl")):
    t = Path(p).name[4]
    for r in map(json.loads, open(p)):
        ans[t][r["id"]] = r["answer"]
def tabs(a):
    return set(a[5:].split("+")) if a.startswith("both:") else {a}
def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k / n; d = 1 + z*z/n; c = p + z*z/(2*n); r = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)); return ((c-r)/d, (c+r)/d)
agree = [i for i in key if ans["A"][i] == ans["B"][i]]
print(f"judge passes agree on {len(agree)}/100 rows; disagreements excluded")
none = [i for i in agree if ans["A"][i] == "none"]
print(f"consensus 'none' (junk on every tab it passed): {len(none)}/{len(agree)}")
scored = [i for i in agree if ans["A"][i] != "none"]
rules = ["R0", "R1", "R3", "R3b"]
per = {}
for st in N:
    rows = [i for i in scored if key[i]["stratum"] == st]
    if not rows: continue
    per[st] = {r: (sum(key[i]["picks"][r] in tabs(ans["A"][i]) for i in rows), len(rows)) for r in rules}
print(f"\n{'stratum':8} {'N':>5} {'n':>3} " + " ".join(f"{r:>14}" for r in rules))
for st, d in per.items():
    print(f"{st:8} {N[st]:5} {d['R0'][1]:3} " + " ".join(f"{d[r][0]:3}/{d[r][1]:<3} ({d[r][0]/d[r][1]:.2f})" for r in rules))
tot = sum(N[s] for s in per)
print("\nN-weighted hit rate (share of all multi-lens articles each rule places where the judges would):")
for r in rules:
    w = sum(N[s] * per[s][r][0] / per[s][r][1] for s in per) / tot
    k = sum(per[s][r][0] for s in per); n = sum(per[s][r][1] for s in per)
    lo, hi = wilson(k, n)
    print(f"  {r:4} {w:.3f}   (unweighted {k}/{n} = {k/n:.2f}, Wilson [{lo:.2f}, {hi:.2f}])")
