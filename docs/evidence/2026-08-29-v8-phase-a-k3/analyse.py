"""Phase A k=3 analysis. Estimands and decision rules are fixed in PREREGISTRATION.md.

Deviations from the pre-registration are printed as DEVIATION lines, not silently applied.

The op-point, weights and gatekeeper are IMPORTED from filters/uplifting/v7/base_scorer.py,
never copied: TIER_THRESHOLDS is the sole runtime source of the operating point and a
second copy in an analysis script is how NM#161 and NM#205 happened.
"""
import json, random, statistics, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from filters.uplifting.v7.base_scorer import BaseUpliftingScorer as S

DIMS = S.DIMENSION_NAMES
W = S.DIMENSION_WEIGHTS
OP = dict((n, t) for n, t, _ in S.TIER_THRESHOLDS)["medium"]
GK_DIM, GK_MIN, GK_CAP = S.GATEKEEPER_DIMENSION, S.GATEKEEPER_MIN, S.GATEKEEPER_CAP
ARMS = ("A", "B")
RUNS = (1, 2, 3)
SCRATCH = Path(sys.argv[1])


def wavg(scores):
    """Mirror of _process_raw_scores: clamp, weighted sum, then the gatekeeper cap.
    No calibration (there is none for a v8 candidate) and no short-content cap
    (uplifting v7 declares no short_content.cap -- verified, not assumed)."""
    s = {d: max(0.0, min(10.0, float(scores[d]))) for d in DIMS}
    w = sum(s[d] * W[d] for d in DIMS)
    if GK_DIM is not None and s[GK_DIM] < GK_MIN and w > GK_CAP:
        w = GK_CAP
    return w


cohort = {json.loads(l)["id"]: json.loads(l) for l in open(SCRATCH / "phaseA_cohort200.jsonl")}
data = defaultdict(dict)          # data[id][(arm, run)] = {"w":.., "verdict":.., "dims":..}
for arm in ARMS:
    for run in RUNS:
        for line in open(SCRATCH / f"phaseA_{arm}{run}.jsonl"):
            r = json.loads(line)
            a = r["uplifting_analysis"]
            dims = {d: a[d]["score"] for d in DIMS}
            data[r["id"]][(arm, run)] = {
                "w": wavg(dims), "verdict": a["scope_verdict"], "dims": dims}

ids = sorted(data)
missing = [i for i in ids if len(data[i]) != 6]
if missing:
    raise SystemExit(f"FATAL: {len(missing)} rows without all 6 observations")
if set(ids) != set(cohort):
    raise SystemExit("FATAL: scored ids != cohort ids")
STRAT = {i: cohort[i]["stratum"] for i in ids}
print(f"rows {len(ids)}  observations {6*len(ids)}  strata "
      f"{ {s: sum(1 for i in ids if STRAT[i]==s) for s in ('R','B')} }")
print(f"op-point {OP} (imported)  gatekeeper {GK_DIM}<{GK_MIN} -> cap {GK_CAP}\n")

ing = lambda v: v == "in_scope"
PAIRS = [(1, 2), (1, 3), (2, 3)]


def boot_ci(rows, stat, n=4000, seed=11):
    """Cluster bootstrap over ROWS -- the 3 pairs inside a row are not independent."""
    rng = random.Random(seed)
    if not rows:
        return (float("nan"), float("nan"))
    vals = []
    for _ in range(n):
        samp = [rows[rng.randrange(len(rows))] for _ in rows]
        vals.append(stat(samp))
    vals.sort()
    return (vals[int(0.025 * n)], vals[int(0.975 * n)])


print("=" * 78)
print("1. PRIMARY -- P(two identical runs disagree on the scope binary)")
print("=" * 78)
print(f"{'arm':<4}{'stratum':<9}{'rows':>5}{'disc/pairs':>13}{'rate':>8}{'  95% CI (row-clustered)':>26}"
      f"{'   runs1&2 only':>16}")
for arm in ARMS:
    for st in ("R", "B"):
        rws = [i for i in ids if STRAT[i] == st]
        per_row = [[ing(data[i][(arm, p)]["verdict"]) != ing(data[i][(arm, q)]["verdict"])
                    for p, q in PAIRS] for i in rws]
        disc, tot = sum(sum(x) for x in per_row), 3 * len(rws)
        lo, hi = boot_ci(per_row, lambda s: sum(sum(x) for x in s) / max(3 * len(s), 1))
        r12 = sum(1 for i in rws
                  if ing(data[i][(arm, 1)]["verdict"]) != ing(data[i][(arm, 2)]["verdict"]))
        print(f"{arm:<4}{st:<9}{len(rws):>5}{disc:>7}/{tot:<5}{disc/tot:>7.1%}"
              f"{'':>6}[{lo:.1%}, {hi:.1%}]{'':>6}{r12}/{len(rws)} = {r12/len(rws):.1%}")

print()
print("=" * 78)
print("2. SECONDARY -- non-unanimity at k=3, and whether a majority vote moves the label")
print("=" * 78)
for arm in ARMS:
    for st in ("R", "B"):
        rws = [i for i in ids if STRAT[i] == st]
        nonun = [i for i in rws
                 if len({ing(data[i][(arm, r)]["verdict"]) for r in RUNS}) > 1]
        maj_ne_r1 = sum(1 for i in nonun
                        if (sum(ing(data[i][(arm, r)]["verdict"]) for r in RUNS) >= 2)
                        != ing(data[i][(arm, 1)]["verdict"]))
        print(f"  arm {arm} stratum {st}: non-unanimous {len(nonun)}/{len(rws)} = "
              f"{len(nonun)/len(rws):.1%}   majority differs from run 1 on "
              f"{maj_ne_r1} of them")

print()
print("=" * 78)
print(f"3. TERTIARY -- op-point ({OP}) crossings, k=3 mean vs k=1 (run 1 alone)")
print("=" * 78)
for arm in ARMS:
    for st in ("R", "B"):
        rws = [i for i in ids if STRAT[i] == st]
        k3 = {i: statistics.mean(data[i][(arm, r)]["w"] for r in RUNS) for i in rws}
        cross = sum(1 for i in rws if (k3[i] >= OP) != (data[i][(arm, 1)]["w"] >= OP))
        above3 = sum(1 for i in rws if k3[i] >= OP)
        above1 = sum(1 for i in rws if data[i][(arm, 1)]["w"] >= OP)
        print(f"  arm {arm} stratum {st}: k=1 above {above1:>3}  k=3 above {above3:>3}  "
              f"rows where k=1 and k=3 disagree: {cross}/{len(rws)} = {cross/len(rws):.1%}")

print()
print("=" * 78)
print("4. PARITY (H-V8-3) -- between-arm effect against the within-arm null, SAME rows")
print("=" * 78)
print("Matched by construction: every quantity below is computed over PAIRS OF SINGLE RUNS.")
print("within = 6 pairs/row (3 within A, 3 within B).  between = 9 pairs/row (Ai vs Bj).")
BAND = 0.16          # the #95 batch-composition band


def diff_ci(rows_w, rows_b, stat, n=4000, seed=13):
    """Row-clustered bootstrap on (between - within). Resamples ROWS, recomputing both
    sides from the same resampled rows, so the pairing survives the bootstrap."""
    rng = random.Random(seed)
    vals = []
    k = len(rows_w)
    for _ in range(n):
        idx = [rng.randrange(k) for _ in range(k)]
        vals.append(stat([rows_b[j] for j in idx]) - stat([rows_w[j] for j in idx]))
    vals.sort()
    return vals[int(0.025 * n)], vals[int(0.975 * n)]


for st in ("R", "B"):
    rws = [i for i in ids if STRAT[i] == st]
    w_rows, b_rows = [], []
    for i in rws:
        w_rows.append([abs(data[i][(a, p)]["w"] - data[i][(a, q)]["w"])
                       for a in ARMS for p, q in PAIRS])
        b_rows.append([abs(data[i][("A", p)]["w"] - data[i][("B", q)]["w"])
                       for p in RUNS for q in RUNS])
    flat = lambda rows: [x for r in rows for x in r]
    share = lambda rows: sum(x > BAND for x in flat(rows)) / len(flat(rows))
    meanabs = lambda rows: statistics.mean(flat(rows))

    xw_rows, xb_rows = [], []
    for i in rws:
        xw_rows.append([(data[i][(a, p)]["w"] >= OP) != (data[i][(a, q)]["w"] >= OP)
                        for a in ARMS for p, q in PAIRS])
        xb_rows.append([(data[i][("A", p)]["w"] >= OP) != (data[i][("B", q)]["w"] >= OP)
                        for p in RUNS for q in RUNS])
    xrate = lambda rows: sum(flat(rows)) / len(flat(rows))

    print(f"  stratum {st} (n={len(rws)})")
    for label, fn, rw, rb in (
            (f"share of pairs moving > {BAND} (#95 band)", share, w_rows, b_rows),
            ("mean |d|", meanabs, w_rows, b_rows),
            (f"op-point ({OP}) crossing rate", xrate, xw_rows, xb_rows)):
        lo, hi = diff_ci(rw, rb, fn)
        holds = lo <= 0 <= hi
        fmt = (lambda v: f"{v:.1%}") if "share" in label or "crossing" in label else (lambda v: f"{v:.3f}")
        print(f"    {label:<40} within {fmt(fn(rw)):>7}  between {fmt(fn(rb)):>7}  "
              f"diff 95% CI [{fmt(lo)}, {fmt(hi)}]  -> "
              f"{'no effect above the null' if holds else 'EFFECT: CI excludes 0'}")

print()
print("DEVIATIONS from PREREGISTRATION.md, reported not substituted:")
print("  1. The pre-registered rule was 'median between-arm |d| (k=3 mean) <= 1.5x median")
print("     within-arm |d| (run pairs)'. It is unusable and biased, two ways. Biased: a k=3")
print("     mean is less noisy by construction, so it favours 'parity holds'. Unusable: the")
print("     within-arm median |d| is 0.000 in stratum R -- most rows are identical run to")
print("     run -- so the ratio divides by zero. A bar that cannot be evaluated is not a")
print("     bar; the fix is the matched pair-level test above, whose null is measured, not")
print("     assumed.")
print("  2. The pre-registered op-point rule ('between-arm count inside the range of the two")
print("     within-arm counts') had no error bar: with counts of 3-8 out of 150, Poisson")
print("     noise alone spans that range. Replaced by the same bootstrap.")

print()
print("=" * 78)
print("4b. DIRECTION -- |d| cannot tell bias from noise, and the answer is bias")
print("=" * 78)
for st in ("R", "B"):
    rws = [i for i in ids if STRAT[i] == st]
    k3 = {a: {i: statistics.mean(data[i][(a, r)]["w"] for r in RUNS) for i in rws}
          for a in ARMS}
    signed = [k3["A"][i] - k3["B"][i] for i in rws]
    rng = random.Random(17)
    boot = sorted(statistics.mean([signed[rng.randrange(len(signed))]
                                   for _ in signed]) for _ in range(4000))
    lo, hi = boot[100], boot[3900]
    down = sum(1 for d in signed if d < -0.01)
    up = sum(1 for d in signed if d > 0.01)
    same = len(signed) - down - up
    print(f"  stratum {st} (n={len(rws)}): mean(A-B) on k=3 means = {statistics.mean(signed):+.3f}"
          f"  95% CI [{lo:+.3f}, {hi:+.3f}]  -> "
          f"{'DIRECTIONAL' if not (lo <= 0 <= hi) else 'no net shift'}")
    print(f"      rows where reordered scores LOWER {down}, higher {up}, unchanged {same}")
    for a in ARMS:
        print(f"      arm {a}: rows >= op-point {OP} at k=3: "
              f"{sum(1 for i in rws if k3[a][i] >= OP)}/{len(rws)}")
    va = {}
    for a in ARMS:
        c = defaultdict(int)
        for i in rws:
            for r in RUNS:
                c[data[i][(a, r)]["verdict"]] += 1
        va[a] = dict(sorted(c.items(), key=lambda kv: -kv[1]))
    print(f"      verdicts A (reordered): {va['A']}")
    print(f"      verdicts B (as-is)    : {va['B']}")

print()
print("=" * 78)
print("5. FREE -- recorded scope_verdict vs the old 'all six dims <= 2' inference")
print("=" * 78)
agree = dis = 0
byv = defaultdict(int)
for i in ids:
    for arm in ARMS:
        for r in RUNS:
            o = data[i][(arm, r)]
            inferred_refusal = all(v <= 2.0 for v in o["dims"].values())
            byv[o["verdict"]] += 1
            if inferred_refusal == (not ing(o["verdict"])):
                agree += 1
            else:
                dis += 1
n = agree + dis
print(f"  {n} labels: inference agrees with the recorded verdict on {agree} = {agree/n:.1%}, "
      f"disagrees on {dis} = {dis/n:.1%}")
print(f"  recorded verdicts: {dict(sorted(byv.items(), key=lambda kv: -kv[1]))}")
