import json, sys
from collections import defaultdict
from pathlib import Path
REPO = Path("/home/jeroen/repos/veen-systems/llm-distillery")
sys.path.insert(0, str(REPO))
from filters.uplifting.v7.base_scorer import BaseUpliftingScorer as S
DIMS, W = S.DIMENSION_NAMES, S.DIMENSION_WEIGHTS
OP = dict((n, t) for n, t, _ in S.TIER_THRESHOLDS)["medium"]
GK_DIM, GK_MIN, GK_CAP = S.GATEKEEPER_DIMENSION, S.GATEKEEPER_MIN, S.GATEKEEPER_CAP
SCRATCH = Path("/tmp/claude-1000/-home-jeroen-repos-veen-systems-llm-distillery/96c7f831-6b9e-443a-a955-658f6c98dec6/scratchpad")
def wavg(sc):
    s = {d: max(0.0, min(10.0, float(sc[d]))) for d in DIMS}
    w = sum(s[d] * W[d] for d in DIMS)
    if GK_DIM is not None and s[GK_DIM] < GK_MIN and w > GK_CAP: w = GK_CAP
    return w
cohort = {json.loads(l)["id"]: json.loads(l) for l in open(SCRATCH / "phaseA_cohort200.jsonl")}
data = defaultdict(dict)
for arm in ("A", "B"):
    for run in (1, 2, 3):
        for line in open(SCRATCH / f"phaseA_{arm}{run}.jsonl"):
            r = json.loads(line); a = r["uplifting_analysis"]
            data[r["id"]][(arm, run)] = (wavg({d: a[d]["score"] for d in DIMS}), a["scope_verdict"])
mean = lambda i, arm: sum(data[i][(arm, r)][0] for r in (1, 2, 3)) / 3
print(f"op-point {OP}")
tot = {("A",): 0, ("B",): 0}
above = {"A": 0, "B": 0}
for i in data:
    for arm in ("A", "B"):
        above[arm] += mean(i, arm) >= OP
print(f"k=3 rows above op-point: A(reordered) {above['A']}  B(as-is) {above['B']}  net {above['A']-above['B']}")
print(f"{'id':<52}{'str':<4}{'A k3':>7}{'B k3':>7}{'  A verdicts':<28}{'  B verdicts':<28}")
for i in sorted(data, key=lambda i: mean(i, "A") - mean(i, "B")):
    a, b = mean(i, "A"), mean(i, "B")
    if (a >= OP) == (b >= OP): continue
    va = [data[i][("A", r)][1] for r in (1, 2, 3)]
    vb = [data[i][("B", r)][1] for r in (1, 2, 3)]
    print(f"{i[:50]:<52}{cohort[i]['stratum']:<4}{a:>7.3f}{b:>7.3f}  {'/'.join(v[:4] for v in va):<26}  {'/'.join(v[:4] for v in vb):<26}")
