"""H-V8-9 step 2: the §5b no-regression rows under BOTH v8 arms and the v7 prompt,
k=3 each, one judge (deepseek-chat). Weights, op-point and gatekeeper IMPORTED, never copied.

⚠️ This reads the LIVE no-regression set but replays a FIXED 2026-08-29 run, and those two
drift apart the moment the set changes. They did on 2026-08-30: the Rwanda-EU row was dropped
and two rows were added, and this script raised KeyError on the first new id -- found only
because someone ran it, four commits after the change. It now reports the coverage gap in both
directions instead of crashing, because a replay that silently skipped the new rows would be
worse: it would look like a clean pass over a set it never scored.
"""
import json, sys, statistics
from pathlib import Path
REPO = Path("/home/jeroen/repos/veen-systems/llm-distillery")
sys.path.insert(0, str(REPO))
from filters.uplifting.v7.base_scorer import BaseUpliftingScorer as S
DIMS, W = S.DIMENSION_NAMES, S.DIMENSION_WEIGHTS
OP = dict((n, t) for n, t, _ in S.TIER_THRESHOLDS)["medium"]
GK_DIM, GK_MIN, GK_CAP = S.GATEKEEPER_DIMENSION, S.GATEKEEPER_MIN, S.GATEKEEPER_CAP
SP = Path(sys.argv[1])
NR = {json.loads(l)["id"]: json.loads(l) for l in open(REPO / "datasets/adverse/uplifting_no_regression.jsonl")}

def wavg(sc):
    s = {d: max(0.0, min(10.0, float(sc[d]))) for d in DIMS}
    w = sum(s[d] * W[d] for d in DIMS)
    if GK_DIM is not None and s[GK_DIM] < GK_MIN and w > GK_CAP: w = GK_CAP
    return w

ARMS = {"A": "v8 reordered", "B": "v8 as-is", "V": "v7 prompt (baseline, same judge)"}
data = {}
for arm in ARMS:
    for run in (1, 2, 3):
        for line in open(SP / f"nr_{arm}{run}.jsonl"):
            r = json.loads(line); a = r["uplifting_analysis"]
            data[(r["id"], arm, run)] = (wavg({d: a[d]["score"] for d in DIMS}),
                                         a.get("scope_verdict", "-"), a.get("dominant_subject", "-"))
print(f"op-point {OP} (imported)   judge deepseek-chat, one judge across all three arms")

# ⛔ Reconcile the live set against what this fixed run actually scored, BEFORE reporting
# anything. Rows in the run but not in the set are retired rows; rows in the set but not in
# the run have never been scored under these arms and MUST NOT read as a pass.
scored_ids = {k[0] for k in data}
covered = [i for i in NR if i in scored_ids]
unscored = [i for i in NR if i not in scored_ids]
retired = sorted(scored_ids - set(NR))
print(f"no-regression set: {len(NR)} rows   scored by this run: {len(covered)}")
if retired:
    print("  RETIRED since the run (scored here, no longer in the set): " + ", ".join(retired))
if unscored:
    print("  ⛔ NOT SCORED BY THIS RUN -- no verdict below covers them: " + ", ".join(unscored))
    print("  ⛔ This run is a 2026-08-29 replay. Re-score these rows before reading step 2 as "
          "covering the current set.")

for i in covered:
    r = NR[i]
    print("\n" + "=" * 96)
    print(f"{i}\n  {r['title'][:88]}\n  guards: {r['guards']}   assertion: {r['assertion']}")
    means = {}
    for arm, label in ARMS.items():
        ws = [data[(i, arm, run)][0] for run in (1, 2, 3)]
        vs = [data[(i, arm, run)][1] for run in (1, 2, 3)]
        means[arm] = sum(ws) / 3
        print(f"  {label:<34} k=3 {means[arm]:.3f}   runs " + " ".join(f"{w:.2f}" for w in ws)
              + "   verdicts " + "/".join(v[:4] for v in vs))
    if r["assertion"].startswith("raw_weighted_average > 4.5"):
        for arm in ("A", "B"):
            ok = means[arm] > OP
            print(f"  ASSERTION [{ARMS[arm]}]: {means[arm]:.3f} > {OP}  -> {'PASS' if ok else 'FAIL'}")
    else:
        for arm in ("A", "B"):
            d = means[arm] - means["V"]
            print(f"  ASSERTION [{ARMS[arm]}]: delta vs v7 prompt = {d:+.3f}"
                  f"  -> {'PASS (not lower)' if d >= 0 else 'FAIL (scored LOWER than v7)'}")

if unscored:
    sys.exit(2)   # partial coverage is NOT a pass; 2 distinguishes it from a scoring failure
