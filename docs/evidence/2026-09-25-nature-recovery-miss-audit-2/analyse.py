#!/usr/bin/env python3
"""Nature recovery miss audit: apply PREREGISTRATION.md. Controls 4/4 -> drift >= 0.90 -> per-stratum rates.

Reads strata.json, key.jsonl, out_A*/out_B* beside this file (or --dir). Exit 0 table printed, 1 stop, 3 plumbing.
"""
# design-weights: READ. Strata are sampled at different rates; per-week estimates are N_s x rate_s with the
# stratum N from strata.json, and the bootstrap resamples within each stratum. No raw pooled share.
import argparse
import json
import math
import random
import sys
from pathlib import Path

VERDICTS = {"in_scope", "out_of_scope", "cannot_judge"}
SEED, DRAWS = 20260928, 10000
ORDER = ["nr_passes", "near_3.0_3.75", "low_2.0_3.0", "very_low_lt2", "probe_screened"]
LEAK = {"near_3.0_3.75": "cut-off", "low_2.0_3.0": "model", "very_low_lt2": "model", "probe_screened": "probe"}

ap = argparse.ArgumentParser()
ap.add_argument("--dir", type=Path, default=Path(__file__).resolve().parent)
F = ap.parse_args().dir


def fatal(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(3)


def outs(pattern):
    out = {}
    files = sorted(F.glob(pattern))
    if not files:
        fatal(f"no {pattern} in {F}")
    for p in files:
        for r in map(json.loads, open(p)):
            if r.get("verdict") not in VERDICTS or r["id"] in out:
                fatal(f"{p.name}: bad or duplicate row {r.get('id')}")
            out[r["id"]] = r["verdict"]
    return out


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


key = [json.loads(l) for l in open(F / "key.jsonl")]
N = json.loads((F / "strata.json").read_text())["_strata"]
A, B = outs("out_A*.jsonl"), outs("out_B*.jsonl")
if any(k["id"] not in A for k in key):
    fatal("pass A is missing ids")

ctrl = [k for k in key if k["stratum"] == "control"]
ok = sum(A[k["id"]] == k["expected"] for k in ctrl)
print(f"controls: {ok}/{len(ctrl)} as expected")
if len(ctrl) != 4 or ok != 4:
    print("STOP: controls not 4/4")
    raise SystemExit(1)
b_ids = [k["id"] for k in key if k.get("in_B")]
if set(b_ids) != set(B):
    fatal("pass B ids != key's in_B ids")
agree = sum((A[i] == "in_scope") == (B[i] == "in_scope") for i in b_ids) / len(b_ids)
print(f"drift: A vs B {agree:.3f} on {len(b_ids)} rows (stop below 0.90)")
if agree < 0.90:
    print("STOP: drift check failed")
    raise SystemExit(1)

judged, cannot = {}, {}
for k in key:
    s = k["stratum"]
    if s == "control":
        continue
    v = A[k["id"]]
    if k["id"] in B and (B[k["id"]] == "in_scope") != (v == "in_scope"):
        v = "tie_out"
    if v == "cannot_judge":
        cannot[s] = cannot.get(s, 0) + 1
        continue
    judged.setdefault(s, []).append(1 if v == "in_scope" else 0)

rng = random.Random(SEED)
boot = [{s: sum(rng.choice(x) for _ in x) / len(x) for s, x in judged.items()} for _ in range(DRAWS)]
print(f"\n{'stratum':16} {'N/week':>7} {'judged':>6} {'in':>4} {'rate':>6} {'Wilson 95%':>15} {'est. in-scope/week':>20}  leak")
tot_miss = []
for s in ORDER:
    x = judged.get(s, [])
    if not x:
        print(f"{s:16} {N.get(s, 0):7} {0:6}  (none judged; cannot_judge {cannot.get(s, 0)})")
        continue
    k, n = sum(x), len(x)
    lo, hi = wilson(k, n)
    vals = sorted(N[s] * b[s] for b in boot)
    print(f"{s:16} {N[s]:7} {n:6} {k:4} {k / n:6.3f}  [{lo:.3f}, {hi:.3f}]  "
          f"{N[s] * k / n:8.0f} [{vals[int(.025 * DRAWS)]:.0f}, {vals[int(.975 * DRAWS) - 1]:.0f}]  "
          f"{LEAK.get(s, 'precision control')}  (cannot_judge {cannot.get(s, 0)})")
miss = sorted(sum(N[s] * b[s] for s in LEAK if s in b) for b in boot)
point = sum(N[s] * sum(judged[s]) / len(judged[s]) for s in LEAK if s in judged)
print(f"\nestimated nature-recovery stories MISSED by nr but published by another lens, per week: "
      f"{point:.0f} [{miss[int(.025 * DRAWS)]:.0f}, {miss[int(.975 * DRAWS) - 1]:.0f}] (~{point / 42:.1f} per cycle)")
for leak in ["probe", "model", "cut-off"]:
    pts = sum(N[s] * sum(judged[s]) / len(judged[s]) for s, l in LEAK.items() if l == leak and s in judged)
    print(f"  via {leak:8}: {pts:6.0f}")
