#!/usr/bin/env python3
"""Junk share of everything adj3 would publish, per candidate cut-off (PREREGISTRATION.md).

Reads bands.json, band_key.jsonl, out_A*/out_B* beside this file (or --dir), plus the live audit's
groups.json / key.jsonl / out_* for the >= 4.5 part. Order: controls 4/4 -> drift >= 0.90 -> table.
Exit 0 table printed, 1 a stop condition fired, 3 plumbing.
"""
# design-weights: READ. Every sub-band and live-audit group is re-weighted by its N; the bootstrap
# resamples within each judged group. No raw pooled share is computed.
import argparse
import json
import random
import sys
from pathlib import Path

VERDICTS = {"in_scope", "out_of_scope", "harm_is_subject", "response_to_harm",
            "no_person_benefits", "cannot_judge"}
SEED, DRAWS, V8_POINT = 20260926, 10000, 0.338
CUTS = [("4.5", []), ("4.25", ["b4.25"]), ("4.0", ["b4.25", "b4.0"]),
        ("3.75", ["b4.25", "b4.0", "b3.75"]), ("3.5", ["b4.25", "b4.0", "b3.75", "b3.5"])]

ap = argparse.ArgumentParser()
ap.add_argument("--dir", type=Path, default=Path(__file__).resolve().parent)
ap.add_argument("--live", type=Path,
                default=Path(__file__).resolve().parent.parent / "2026-09-25-v8-adj3-live-audit")
args = ap.parse_args()


def fatal(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(3)


def outs(d, pattern):
    out = {}
    files = sorted(d.glob(pattern))
    if not files:
        fatal(f"no {pattern} in {d}")
    for p in files:
        for r in map(json.loads, open(p)):
            if r.get("verdict") not in VERDICTS or r["id"] in out:
                fatal(f"{p.name}: bad or duplicate row {r.get('id')}")
            out[r["id"]] = r["verdict"]
    return out


def finals(key, A, B, gfield):
    """Per group: list of 1 (junk) / 0 (in scope); A/B in-out split -> junk (tie rule)."""
    res = {}
    for k in key:
        g = k[gfield]
        if g == "control":
            continue
        v = A[k["id"]]
        if k["id"] in B and (B[k["id"]] == "in_scope") != (v == "in_scope"):
            v = "tie_out"
        if v == "cannot_judge":
            continue
        res.setdefault(g, []).append(0 if v == "in_scope" else 1)
    return res


# --- band panel
key = [json.loads(l) for l in open(args.dir / "band_key.jsonl")]
A, B = outs(args.dir, "out_A*.jsonl"), outs(args.dir, "out_B*.jsonl")
if any(k["id"] not in A for k in key):
    fatal("pass A is missing ids")
ctrl = [k for k in key if k["band"] == "control"]
ok = sum(A[k["id"]] == k["expected"] for k in ctrl)
print(f"controls: {ok}/{len(ctrl)} as ruled")
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
band = finals(key, A, B, "band")
bands = json.loads((args.dir / "bands.json").read_text())
Nb = {b: v["N"] for b, v in bands["bands"].items()}

# --- the >= 4.5 part: adj3's live-audit groups A (adds) and B (both publish)
lk = [json.loads(l) for l in open(args.live / "key.jsonl")]
live = finals(lk, outs(args.live, "out_A*.jsonl"), outs(args.live, "out_B*.jsonl"), "group")
NL = json.loads((args.live / "groups.json").read_text())["N"]
if NL["A"] + NL["B"] != bands["N_ge_4.5"]:
    fatal(f"live A+B = {NL['A'] + NL['B']} != N_ge_4.5 {bands['N_ge_4.5']}")

groups = {"LA": live["A"], "LB": live["B"], **band}
N = {"LA": NL["A"], "LB": NL["B"], **Nb}


def rate(xs):
    return sum(xs) / len(xs)


def junk(r, members):
    parts = ["LA", "LB"] + members
    return sum(N[g] * r[g] for g in parts) / sum(N[g] for g in parts)


for b in ["b4.25", "b4.0", "b3.75", "b3.5"]:
    xs = band[b]
    print(f"sub-band {b}: N={Nb[b]}, judged {len(xs)}, junk {sum(xs)}/{len(xs)} = {rate(xs):.3f}")

point = {g: rate(xs) for g, xs in groups.items()}
rng = random.Random(SEED)
boot = []
for _ in range(DRAWS):
    boot.append({g: rate([rng.choice(xs) for _ in xs]) for g, xs in groups.items()})
print(f"\n{'cut':>5} {'per cycle':>9} {'junk share':>10} {'95% CI':>17}  note")
for cut, members in CUTS:
    vals = sorted(junk(r, members) for r in boot)
    lo, hi = vals[int(0.025 * DRAWS)], vals[int(0.975 * DRAWS) - 1]
    vol = (N["LA"] + N["LB"] + sum(N[m] for m in members)) / bands["cycles"]
    note = "not shown to be better than v8 (CI reaches 0.338)" if hi >= V8_POINT else ""
    print(f"{cut:>5} {vol:9.1f} {junk(point, members):10.3f}  [{lo:.3f}, {hi:.3f}]  {note}")
