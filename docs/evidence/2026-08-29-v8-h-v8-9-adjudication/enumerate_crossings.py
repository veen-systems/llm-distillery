"""H-V8-9 step 1: enumerate the rows whose op-point SIDE differs between arms.

Scoring mirrors docs/evidence/2026-08-29-v8-phase-a-k3/analyse.py exactly: the op-point,
weights and gatekeeper are IMPORTED from filters/uplifting/v7/base_scorer.py, never copied.
No calibration (these are ORACLE scores, the calibration target).
"""
import json, sys
from collections import defaultdict
from pathlib import Path

REPO = Path("/home/jeroen/repos/veen-systems/llm-distillery")
sys.path.insert(0, str(REPO))
from filters.uplifting.v7.base_scorer import BaseUpliftingScorer as S

DIMS, W = S.DIMENSION_NAMES, S.DIMENSION_WEIGHTS
OP = dict((n, t) for n, t, _ in S.TIER_THRESHOLDS)["medium"]
GK_DIM, GK_MIN, GK_CAP = S.GATEKEEPER_DIMENSION, S.GATEKEEPER_MIN, S.GATEKEEPER_CAP
SCRATCH = Path(sys.argv[1])


def wavg(sc):
    s = {d: max(0.0, min(10.0, float(sc[d]))) for d in DIMS}
    w = sum(s[d] * W[d] for d in DIMS)
    if GK_DIM is not None and s[GK_DIM] < GK_MIN and w > GK_CAP:
        w = GK_CAP
    return w


cohort = {json.loads(l)["id"]: json.loads(l) for l in open(SCRATCH / "phaseA_cohort200.jsonl")}
data = defaultdict(dict)
for arm in ("A", "B"):
    for run in (1, 2, 3):
        for line in open(SCRATCH / f"phaseA_{arm}{run}.jsonl"):
            r = json.loads(line)
            a = r["uplifting_analysis"]
            dims = {d: a[d]["score"] for d in DIMS}
            data[r["id"]][(arm, run)] = {"w": wavg(dims), "v": a["scope_verdict"], "dims": dims}

ids = sorted(data)
assert set(ids) == set(cohort), "scored ids != cohort ids"
assert all(len(data[i]) == 6 for i in ids), "not all rows have 6 observations"
print(f"op-point {OP} (imported)  rows {len(ids)}")

mean = lambda i, arm: sum(data[i][(arm, r)]["w"] for r in (1, 2, 3)) / 3
out = []
for i in ids:
    a, b = mean(i, "A"), mean(i, "B")
    if (a >= OP) != (b >= OP):
        # within-arm instability: does either arm's own 3 runs straddle the op-point?
        straddle = {arm: len({data[i][(arm, r)]["w"] >= OP for r in (1, 2, 3)}) > 1
                    for arm in ("A", "B")}
        out.append((i, a, b, straddle))

drop = [o for o in out if o[2] >= OP > o[1]]   # as-is above, reordered below
add = [o for o in out if o[1] >= OP > o[2]]    # reordered above, as-is below
for label, rows in (("DROPPED by the reorder (B>=OP > A)", drop),
                    ("ADDED by the reorder (A>=OP > B)", add)):
    print(f"\n{'='*100}\n{label}: {len(rows)}"
          f"   [R {sum(1 for r in rows if cohort[r[0]]['stratum']=='R')}"
          f" / B {sum(1 for r in rows if cohort[r[0]]['stratum']=='B')}]\n{'='*100}")
    for i, a, b, st in sorted(rows, key=lambda r: r[1] - r[2]):
        c = cohort[i]
        flag = "  ⚠ SELF-STRADDLE " + ",".join(k for k, v in st.items() if v) if any(st.values()) else ""
        print(f"\n{i}  [{c['stratum']}] {c['language']}  {len(c['content'])} chars{flag}")
        print(f"  A(reordered) k3 {a:.3f}  runs " +
              " ".join(f"{data[i][('A',r)]['w']:.2f}/{data[i][('A',r)]['v'][:2]}" for r in (1, 2, 3)))
        print(f"  B(as-is)     k3 {b:.3f}  runs " +
              " ".join(f"{data[i][('B',r)]['w']:.2f}/{data[i][('B',r)]['v'][:2]}" for r in (1, 2, 3)))
        print(f"  v7 {c['v7_raw_weighted_average']:.2f} ({c['v7_stage_used']})  {c['source']}")
        print(f"  {c['title'][:150]}")
        print(f"  {c['url']}")
