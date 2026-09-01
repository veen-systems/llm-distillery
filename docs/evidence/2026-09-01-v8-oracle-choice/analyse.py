"""Does the REORDERED prompt change which oracle applies STEP 1?

Weights, the gatekeeper and the class-A bar are IMPORTED or read off the data file, never
copied. The bar is `max_acceptable_wa` on each row, not a constant typed here: it is an
editorial upper bound recorded with the row, and §1a is explicit that these are editorial
labels, not oracle ground truth — ADR-021 coverage is NOT claimed.
"""
import json, statistics, sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from filters.uplifting.v7.base_scorer import BaseUpliftingScorer as S

DIMS, W = S.DIMENSION_NAMES, S.DIMENSION_WEIGHTS
GK_DIM, GK_MIN, GK_CAP = S.GATEKEEPER_DIMENSION, S.GATEKEEPER_MIN, S.GATEKEEPER_CAP
RUNS = Path(__file__).resolve().parent / "runs"
ADV = {json.loads(l)["id"]: json.loads(l)
       for l in open(REPO / "datasets/adverse/uplifting.jsonl", encoding="utf-8")}
FIELD = "human_thriving_analysis"


def wavg(sc):
    s = {d: max(0.0, min(10.0, float(sc[d]))) for d in DIMS}
    w = sum(s[d] * W[d] for d in DIMS)
    if GK_DIM is not None and s[GK_DIM] < GK_MIN and w > GK_CAP:
        w = GK_CAP
    return w


data = defaultdict(dict)
for arm, pre in (("DeepSeek", "ds"), ("Gemini 2.5 Flash", "gm")):
    for run in (1, 2, 3):
        for line in open(RUNS / f"{pre}_{run}.jsonl", encoding="utf-8"):
            r = json.loads(line)
            a = r[FIELD]
            data[arm].setdefault(r["id"], []).append(
                (wavg({d: a[d]["score"] for d in DIMS}), a.get("scope_verdict", "__absent__")))

ids = sorted(set(ADV) & set(data["DeepSeek"]))
print(f"prompt: prompt-candidate-tail.md (ADOPTED)   rows: {len(ids)} class-A, FULL TEXT   k=3\n")

summary = {}
for arm in data:
    n_off, n_pass, verdicts = 0, 0, Counter()
    print("=" * 100)
    print(arm)
    for i in ids:
        runs = data[arm][i]
        assert len(runs) == 3, f"{arm} {i}: k={len(runs)}, not 3 — a silent k=1 is the 08-23 defect"
        m = statistics.fmean(w for w, _ in runs)
        vs = [v for _, v in runs]
        for v in vs:
            verdicts[v] += 1
        off = sum(1 for v in vs if v != "in_scope")
        n_off += off >= 2                      # majority says the harm is the subject
        bar = float(ADV[i]["max_acceptable_wa"])
        ok = m < bar
        n_pass += ok
        print(f"  {'PASS' if ok else 'FAIL'}  k=3 {m:5.3f} < {bar}   runs {' '.join(f'{w:5.2f}' for w, _ in runs)}"
              f"   {'/'.join(v[:9] for v in vs):32}  {ADV[i]['title'][:44]}")
    summary[arm] = (n_pass, n_off, verdicts)
    print(f"  -> Gate B-A: {n_pass}/{len(ids)} below bar   |   STEP 1 applied (majority "
          f"non-in_scope): {n_off}/{len(ids)}   |   verdicts {dict(verdicts)}")

print("\n" + "=" * 100)
print("HEAD TO HEAD")
for arm, (p, o, _) in summary.items():
    print(f"  {arm:20} Gate B-A {p}/{len(ids)}   STEP 1 applied {o}/{len(ids)}")

MASH = "south_african_herald_zw_5e7a6674c6d4"
if MASH in ids:
    print(f"\nThe row the two oracles were 4.4 points apart on (08-23), '{ADV[MASH]['title'][:48]}':")
    for arm in data:
        runs = data[arm][MASH]
        print(f"  {arm:20} k=3 {statistics.fmean(w for w, _ in runs):5.3f}   "
              f"runs {' '.join(f'{w:5.2f}' for w, _ in runs)}   {'/'.join(v for _, v in runs)}")
