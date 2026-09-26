#!/usr/bin/env python3
"""EXPLORATORY, NOT PRE-REGISTERED (designed after seeing analyse.py's per-stratum table): hybrid H =
Nature recovery if passed, else Cultural discovery if passed, else R3 (largest margin above own cut-off).
Scored on the same judge consensus. Being fitted to the table it is judged on, it is optimistic by construction."""
# design-weights: READ. Per stratum, N-weighted by strata.json.
import json, glob
from pathlib import Path
F = Path(__file__).resolve().parent
key = {k["id"]: k for k in map(json.loads, open(F / "key.jsonl"))}
N = json.loads((F / "strata.json").read_text())["N"]
OP = {"uplifting": 4.5, "cultural_discovery": 4.0, "belonging": 4.0, "nature_recovery": 3.75, "solutions": 2.25}
ans = {"A": {}, "B": {}}
for p in glob.glob(str(F / "out_*.jsonl")):
    for r in map(json.loads, open(p)):
        ans[Path(p).name[4]][r["id"]] = r["answer"]
tabs = lambda a: set(a[5:].split("+")) if a.startswith("both:") else {a}
def H(k):
    ls = k["lenses"]
    if "nature_recovery" in ls: return "nature_recovery"
    if "cultural_discovery" in ls: return "cultural_discovery"
    return max(ls, key=lambda l: k["scores"][l]["raw"] - OP[l])
rows = [i for i in key if ans["A"][i] == ans["B"][i] and ans["A"][i] != "none"]
per = {}
for i in rows:
    st = key[i]["stratum"]; h = H(key[i]) in tabs(ans["A"][i])
    k, n = per.get(st, (0, 0)); per[st] = (k + h, n + 1)
for st, (k, n) in per.items(): print(f"{st:6} {k}/{n}")
tot = sum(N[s] for s in per)
w = sum(N[s] * k / n for s, (k, n) in per.items()) / tot
print(f"H N-weighted {w:.3f} | unweighted {sum(k for k,_ in per.values())}/{sum(n for _,n in per.values())}  (EXPLORATORY; compare R1 0.781, R0 0.662)")
