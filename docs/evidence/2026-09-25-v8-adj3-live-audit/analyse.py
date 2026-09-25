#!/usr/bin/env python3
"""Apply PREREGISTRATION.md's audit bar to the judged panel. Prints the verdict; decides nothing else.

Reads (beside this file unless --dir is given): groups.json, key.jsonl, out_A*.jsonl, out_B*.jsonl.
Order is the pre-registration's: controls 4/4 -> drift >= 0.90 -> rates -> bootstrap -> verdict.
Exit 0 verdict printed, 1 a stop condition fired, 3 plumbing.
"""
# design-weights: READ. The panel samples groups A, R and B at different rates; junk(v8) and
# junk(adj3) are re-weighted by the group sizes N_A, N_R, N_B from groups.json, and the bootstrap
# resamples within each judged group. No raw pooled share is computed.
import argparse
import json
import random
import sys
from pathlib import Path

VERDICTS = {"in_scope", "out_of_scope", "harm_is_subject", "response_to_harm",
            "no_person_benefits", "cannot_judge"}
SEED, DRAWS = 20260925, 10000

ap = argparse.ArgumentParser()
ap.add_argument("--dir", type=Path, default=Path(__file__).resolve().parent)
args = ap.parse_args()
F = args.dir


def fatal(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(3)


def read_outs(pattern):
    out = {}
    files = sorted(F.glob(pattern))
    if not files:
        fatal(f"no {pattern} in {F}")
    for p in files:
        for r in map(json.loads, open(p)):
            if r.get("verdict") not in VERDICTS:
                fatal(f"{p.name}: bad verdict {r.get('verdict')!r} for {r.get('id')}")
            if r["id"] in out:
                fatal(f"{p.name}: duplicate id {r['id']}")
            out[r["id"]] = r["verdict"]
    return out


N = json.loads((F / "groups.json").read_text())["N"]
key = [json.loads(l) for l in open(F / "key.jsonl")]
A = read_outs("out_A*.jsonl")
B = read_outs("out_B*.jsonl")
panel = [k for k in key if k["group"] in ("A", "R", "B")]
missing = [k["id"] for k in key if k["id"] not in A]
if missing:
    fatal(f"pass A is missing {len(missing)} ids, e.g. {missing[:3]}")

# 1. Known-answer controls.
ctrl = [k for k in key if k["group"] == "control"]
ok = sum(A[k["id"]] == k["expected"] for k in ctrl)
print(f"controls: {ok}/{len(ctrl)} as ruled")
if len(ctrl) != 4 or ok != 4:
    print("STOP: controls not 4/4 (PREREGISTRATION.md amendment)")
    raise SystemExit(1)


# 2. Drift check.
def isin(v):
    return v == "in_scope"


b_ids = [k["id"] for k in panel if k["in_B"]]
if set(b_ids) != set(B):
    fatal(f"pass B ids != key's in_B ids ({len(B)} vs {len(b_ids)})")
agree = sum(isin(A[i]) == isin(B[i]) for i in b_ids) / len(b_ids)
print(f"drift: A vs B binary agreement {agree:.3f} on {len(b_ids)} rows (stop below 0.90)")
if agree < 0.90:
    print("STOP: drift check failed -- the run is not used (PREREGISTRATION.md)")
    raise SystemExit(1)


# 3. Final verdict per row: A, except an A/B in/out split counts as NOT in scope (tie rule).
def final(i):
    if i in B and isin(A[i]) != isin(B[i]):
        return "tie_out"
    return A[i]


judged = {"A": [], "R": [], "B": []}
cannot = {"A": 0, "R": 0, "B": 0}
for k in panel:
    v = final(k["id"])
    if v == "cannot_judge":
        cannot[k["group"]] += 1
        continue
    judged[k["group"]].append(0 if v == "in_scope" else 1)  # 1 = junk

for g in "ARB":
    xs = judged[g]
    print(f"group {g}: N={N[g]}, judged {len(xs)}, cannot_judge {cannot[g]}, "
          f"junk {sum(xs)}/{len(xs)} = {sum(xs) / len(xs):.3f}" if xs else f"group {g}: N={N[g]}, none judged")
    if not xs and N[g]:
        fatal(f"group {g} has N={N[g]} but no judged rows")


def rate(xs):
    return sum(xs) / len(xs) if xs else 0.0


def junk_shares(jA, jR, jB):
    v8 = (N["B"] * jB + N["R"] * jR) / (N["B"] + N["R"])
    a3 = (N["B"] * jB + N["A"] * jA) / (N["B"] + N["A"])
    return v8, a3


v8, a3 = junk_shares(rate(judged["A"]), rate(judged["R"]), rate(judged["B"]))
D = v8 - a3
rng = random.Random(SEED)
ds = []
for _ in range(DRAWS):
    r = {g: rate([rng.choice(judged[g]) for _ in judged[g]]) for g in "ARB"}
    x, y = junk_shares(r["A"], r["R"], r["B"])
    ds.append(x - y)
ds.sort()
lo, hi = ds[int(0.025 * DRAWS)], ds[int(0.975 * DRAWS) - 1]
print(f"\njunk share of what each model publishes (re-weighted by N): v8 {v8:.3f}, adj3 {a3:.3f}")
print(f"D = v8 - adj3 = {D:+.3f}, 95% bootstrap CI [{lo:+.3f}, {hi:+.3f}]")
verdict = "WIN" if lo > 0 else "LOSE" if hi < 0 else "NOT DISTINGUISHABLE"
print(f"VERDICT (PREREGISTRATION.md): {verdict}")

# Reported, not gating (ADR-023: a missed positive costs nothing visible).
cycles = 42
good_v8 = N["B"] * (1 - rate(judged["B"])) + N["R"] * (1 - rate(judged["R"]))
good_a3 = N["B"] * (1 - rate(judged["B"])) + N["A"] * (1 - rate(judged["A"]))
junk_v8 = N["B"] * rate(judged["B"]) + N["R"] * rate(judged["R"])
junk_a3 = N["B"] * rate(judged["B"]) + N["A"] * rate(judged["A"])
print(f"\nper cycle, over the audit population ({cycles} cycles): "
      f"v8 publishes {(N['B'] + N['R']) / cycles:.1f} (~{junk_v8 / cycles:.1f} junk, ~{good_v8 / cycles:.1f} in scope); "
      f"adj3 publishes {(N['B'] + N['A']) / cycles:.1f} (~{junk_a3 / cycles:.1f} junk, ~{good_a3 / cycles:.1f} in scope)")
print(f"in-scope articles lost ~{N['R'] * (1 - rate(judged['R'])):.0f}, gained ~{N['A'] * (1 - rate(judged['A'])):.0f} over the week")
if good_v8 and good_a3 < 0.5 * good_v8:
    print("FLAG for the owner: adj3's estimated in-scope output is below 50% of v8's (volume question, not a fail)")
