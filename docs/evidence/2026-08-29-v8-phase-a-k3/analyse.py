"""Phase A k=3 analysis. Estimands and decision rules are fixed in PREREGISTRATION.md.

Deviations from the pre-registration are printed as DEVIATION lines, not silently applied.

The op-point, weights and gatekeeper are IMPORTED from filters/uplifting/v7/base_scorer.py,
never copied: TIER_THRESHOLDS is the sole runtime source of the operating point and a
second copy in an analysis script is how NM#161 and NM#205 happened.
"""
import collections, json, math, random, statistics, sys
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

# ⛔ A BOOTSTRAP BONFERRONI INTERVAL WAS PRINTED HERE AND HAS BEEN REMOVED (review
# 2026-08-29, second pass). At alpha = 0.05/21 on 4,000 draws each bound was a SINGLE
# ORDER STATISTIC -- the 5th of 4,000. Two independent re-runs across seeds put the
# Monte-Carlo sd of that bound at ~0.014 against a reported value of -0.010, and had
# it above zero in 24/30 and 408/500 replications. The published verdict was decided
# by `seed=17`, not by the data: noise printed as a decision, inside the block added
# to fix multiplicity.
#
# `N_INTERVALS = 21` was also simply wrong, and unfixably so: the count is
# DATA-DEPENDENT (section 4 emitted a Bonferroni line only in the non-holding
# branches, so 6-12 of them), and three reviewers counting independently got 15
# nominal / 22 total / 17 on a null fixture. A hand-counted constant governing a
# decision is the shape this repo keeps paying for.
#
# Multiplicity is now handled by the PERMUTATION test in section 4f, which is stable
# to 4 significant figures at 20,000 draws, and by stating the family explicitly
# rather than burying it in a constant. See the FAMILY note printed there.
N_NOMINAL_INTERVALS = 0     # counted as they are emitted, never hand-set


def pctl(vals, lo_q, hi_q):
    """Percentile pair with both indices clamped. The low index had no floor guard:
    at a smaller alpha or fewer draws it degenerates to vals[0] -- the sample
    minimum, reported as a quantile."""
    n = len(vals)
    return vals[max(0, min(int(lo_q * n), n - 1))], vals[max(0, min(int(hi_q * n), n - 1))]


def count_interval(fmt_lo, fmt_hi):
    """Every printed 95% interval increments the family. Derived, not asserted."""
    global N_NOMINAL_INTERVALS
    N_NOMINAL_INTERVALS += 1
    return fmt_lo, fmt_hi
SCRATCH = Path(sys.argv[1])


def wavg(scores):
    """Mirror of _process_raw_scores: clamp, weighted sum, then the gatekeeper cap.
    NO CALIBRATION, and the reason is stronger than "there is no v8 file":
    filters/uplifting/v7/calibration.json DOES exist, and it is a STUDENT-output ->
    oracle-scale isotonic map. These are ORACLE scores -- the calibration target --
    so applying it would be wrong even if a v8 file existed. Do not add the call.
    No short-content cap either: uplifting v7 declares no short_content.cap, so
    _apply_short_content_cap is a pass-through (verified, not assumed)."""
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
    return count_interval(*pctl(vals, 0.025, 0.975))


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
# ⚠️ 0.16 is the #95 batch-composition floor for the STUDENT. These are ORACLE scores,
# whose own decoder floor is 0.436/0.687 -- a different population and a different
# mechanism. It is used here ONLY as a fixed yardstick applied to both sides of a rate
# DIFFERENCE, where it cancels; it is NOT a significance threshold for these scores, and
# inheriting it as one is what memory/score-batch-shape-noise.md forbids.
BAND = 0.16


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
    return count_interval(*pctl(vals, 0.025, 0.975))


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
            (f"share of pairs moving > {BAND} (fixed yardstick, not an oracle floor)", share, w_rows, b_rows),
            ("mean |d|", meanabs, w_rows, b_rows),
            (f"op-point ({OP}) crossing rate", xrate, xw_rows, xb_rows)):
        lo, hi = diff_ci(rw, rb, fn)
        holds = lo <= 0 <= hi
        fmt = (lambda v: f"{v:.1%}") if "share" in label or "crossing" in label else (lambda v: f"{v:.3f}")
        verdict = ("no effect above the null" if holds
                   else "nominal CI excludes 0 — see the FAMILY note in 4f before quoting")
        print(f"    {label:<40} within {fmt(fn(rw)):>7}  between {fmt(fn(rb)):>7}  "
              f"diff 95% CI [{fmt(lo)}, {fmt(hi)}]  -> {verdict}")

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
    lo, hi = count_interval(*pctl(boot, 0.025, 0.975))   # was hardcoded boot[100]/boot[3900]
                                                          # beside a literal 4000: change the
                                                          # draw count and the quantile moved
    down = sum(1 for d in signed if d < -0.01)
    up = sum(1 for d in signed if d > 0.01)
    same = len(signed) - down - up
    print(f"  stratum {st} (n={len(rws)}): mean(A-B) on k=3 means = {statistics.mean(signed):+.3f}"
          f"  95% CI [{lo:+.3f}, {hi:+.3f}]  -> "
          f"{'directional at 95%' if not (lo <= 0 <= hi) else 'no net shift'}")
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
print("4c. THE GATE-STABLE SUBGROUP -- reported PER STRATUM, and it is not clean")
print("=" * 78)
print("⛔ READ THE CAVEATS BEFORE THE NUMBER. `scope_verdict` is an OUTCOME THE")
print("   TREATMENT CHANGES, so conditioning on 'both arms in_scope on all 3 runs'")
print("   is post-treatment (collider) selection, not a subgroup. And the strata")
print("   must not be pooled -- stratum B is oversampled ~4.4x by design.")
POOLED = "__pooled__"   # an explicit sentinel: the old code branched on the LABEL
                        # STRING, so renaming the label silently printed "0 rows",
                        # and adding a stratum "C" would have silently pooled all 200
for st in ("R", "B", POOLED):
    rws = list(ids) if st is POOLED else [i for i in ids if STRAT[i] == st]
    stable = [i for i in rws
              if all(data[i][(a, r)]["verdict"] == "in_scope" for a in ARMS for r in RUNS)]
    if not stable:
        print(f"  stratum {st}: 0 gate-stable rows")
        continue
    k3 = {a: {i: statistics.mean(data[i][(a, r)]["w"] for r in RUNS) for i in stable}
          for a in ARMS}
    d = [k3["A"][i] - k3["B"][i] for i in stable]
    rng = random.Random(29)
    bt = sorted(statistics.mean([d[rng.randrange(len(d))] for _ in d]) for _ in range(4000))
    lo, hi = pctl(bt, 0.025, 0.975)
    if st is not POOLED:                 # POOLED prints no interval, so it counts none
        lo, hi = count_interval(lo, hi)
    if st is POOLED:
        # No CI, no verdict, on purpose. The pre-registration forbids pooling these
        # strata, and a "do not quote" label is a premise that reads as an instruction
        # and gets stripped the moment the number is copied. The point estimate is
        # shown only so the withdrawn -0.235 is traceable to its source.
        print(f"  POOLED n={len(stable)}  mean(A-B) {statistics.mean(d):+.3f}  "
              f"— ⛔ WITHDRAWN FIGURE, no interval and no verdict: the strata cross "
              f"and B is ~4.4x oversampled. Shown for traceability only.")
        continue
    print(f"  stratum {st}: n={len(stable)}  mean(A-B) {statistics.mean(d):+.3f}  "
          f"95% CI [{lo:+.3f}, {hi:+.3f}]  -> "
          f"{'excludes 0' if not (lo <= 0 <= hi) else 'INCLUDES 0'}")
    if st == "R":
        for dim in DIMS:
            va = statistics.mean(statistics.mean(data[i][("A", r)]["dims"][dim] for r in RUNS) for i in stable)
            vb = statistics.mean(statistics.mean(data[i][("B", r)]["dims"][dim] for r in RUNS) for i in stable)
            print(f"      {dim:<26}{va:>6.2f} vs {vb:>6.2f}   {va - vb:+.3f}")
# How asymmetric is the selection? This is the collider, quantified.
only_b = sum(1 for i in ids
             if all(data[i][("B", r)]["verdict"] == "in_scope" for r in RUNS)
             and not all(data[i][("A", r)]["verdict"] == "in_scope" for r in RUNS))
only_a = sum(1 for i in ids
             if all(data[i][("A", r)]["verdict"] == "in_scope" for r in RUNS)
             and not all(data[i][("B", r)]["verdict"] == "in_scope" for r in RUNS))
print(f"  selection asymmetry: {only_b} rows unanimous in_scope under AS-IS only, "
      f"{only_a} under REORDERED only. The dropped rows are treatment-dependent.")

print()
print("=" * 78)
print("4d. THE TWO CONTROLS, computed here instead of by hand")
print("=" * 78)
for arm in ARMS:
    means = [statistics.mean(data[i][(arm, r)]["w"] for i in ids) for r in RUNS]
    print(f"  arm {arm} per-run cohort mean: " + " / ".join(f"{m:.3f}" for m in means)
          + f"   (spread {max(means) - min(means):.3f})")
print("  Time drift would show as a TREND within an arm; the between-arm gap is")
print("  present in every round and no within-arm spread approaches it.")
# Cache state is collinear with run order, so the run-1 step cannot bound both.
# The cache-MATCHED comparison can: runs 2 and 3 of both arms were ~99.4% cached.
for label, runs in (("all runs (k=3)", RUNS), ("cache-matched (runs 2,3 only)", (2, 3))):
    ma = statistics.mean(data[i][("A", r)]["w"] for i in ids for r in runs)
    mb = statistics.mean(data[i][("B", r)]["w"] for i in ids for r in runs)
    print(f"  {label:<30} A {ma:.4f}  B {mb:.4f}  gap {ma - mb:+.4f}")
print("  ⚠️ Arm A ran cache-WARM throughout (89.2% on run 1); arm B's run 1 was COLD")
print("     (0.0%). Cache state and run order are COLLINEAR in this design, so the")
print("     run1->run2 step cannot bound both nuisances. The cache-matched row can,")
print("     and it does not shrink the gap.")

print()
print("=" * 78)
print("4e. DESIGN WEIGHTS -- carried in the cohort file, so they must be READ")
print("=" * 78)
for st in ("R", "B"):
    w = {cohort[i].get("draw_weight") for i in ids if STRAT[i] == st}
    print(f"  stratum {st}: draw_weight {w}  (n={sum(1 for i in ids if STRAT[i] == st)})")
print("  ⛔ Every rate above is WITHIN-STRATUM and unweighted, which is correct for")
print("     'what is the rate in this population'. A POOLED 200-row figure would be")
print("     ~4.4x over-weighted toward the boundary and the pre-registration forbids")
print("     it. If a production-wide total is ever needed, weight by these.")

print()
print("=" * 78)
print("4f. PERMUTATION + COST -- both were computed by hand for the first write-up")
print("=" * 78)
print("Neither appeared in this file, so neither could be re-derived from the evidence")
print("directory. That is the defect the review named; this block is the fix.")
for st in ("R", "B"):
    rws = [i for i in ids if STRAT[i] == st]
    k3 = {a: {i: statistics.mean(data[i][(a, r)]["w"] for r in RUNS) for i in rws}
          for a in ARMS}
    d = [k3["A"][i] - k3["B"][i] for i in rws]
    obs = abs(statistics.mean(d))
    rng = random.Random(31)
    # Sign-flip permutation: under the null the arm label is exchangeable WITHIN a
    # row, so flipping the sign of a paired difference is an exact null draw.
    hits = sum(1 for _ in range(20000)
               if abs(statistics.mean([x if rng.random() < 0.5 else -x for x in d])) >= obs)
    print(f"  stratum {st}: |mean(A-B)| = {obs:.3f}  sign-flip permutation p = "
          f"{(hits + 1) / 20001:.4f}  (20,000 draws)")

RATE_MISS, RATE_HIT, RATE_OUT = 0.22, 0.007, 0.66     # DeepSeek V4 off-peak, $/1M
print("\n  Cost, re-derived from the per-row `usage` blocks -- NOT from the run log's")
print("  $0.02f display, which is what the first write-up divided by 200.")
tot = 0.0
per_run = {}
for arm in ARMS:
    for r in RUNS:
        ti = to = tc = 0
        for line in open(SCRATCH / f"phaseA_{arm}{r}.jsonl"):
            u = json.loads(line).get("usage") or {}
            ti += u.get("prompt_tokens", 0)
            to += u.get("completion_tokens", 0)
            tc += u.get("prompt_cache_hit_tokens", 0)
        c = ((ti - tc) * RATE_MISS + tc * RATE_HIT + to * RATE_OUT) / 1e6
        tot += c
        per_run[(arm, r)] = c / len(ids)
        print(f"    {arm}{r}  ${c:.6f}   per-article ${c / len(ids):.6f}   "
              f"cache {100 * tc / max(ti, 1):.1f}%")
print(f"    TOTAL ${tot:.4f}")
a1, b1 = per_run[("A", 1)], per_run[("B", 1)]
rep_a = (per_run[("A", 2)] + per_run[("A", 3)]) / 2
rep_b = (per_run[("B", 2)] + per_run[("B", 3)]) / 2
print(f"    run-1 per-article: A ${a1:.6f}  B ${b1:.6f}   ratio {b1 / a1:.2f}x")
print(f"    corpus k=3, 6,590 rows, WITH the unproven repeat discount: "
      f"A ${6590 * (a1 + 2 * rep_a):.2f}  B ${6590 * (b1 + 2 * rep_b):.2f}")
print(f"    corpus k=3, 6,590 rows, WITHOUT it:                        "
      f"A ${6590 * 3 * a1:.2f}  B ${6590 * 3 * b1:.2f}")
print("    ⛔ Only run 1 of each arm is a quotable CACHE figure -- runs 2-3 re-send")
print("       byte-identical prompts, so their 99.4% is an artifact of the design.")

print()
print("=" * 78)
print("4g. THE ESTIMATORS THE WRITE-UP QUOTED AND THIS SCRIPT DID NOT COMPUTE")
print("=" * 78)
print("Five numbers were hand-run for the first two write-ups and cited on five")
print("surfaces. Correct, and un-derivable from this directory -- which is the exact")
print("defect 4f was added to close, left half-closed. They are computed here now.")


def clopper_pearson(k, n, alpha=0.05):
    """Exact binomial interval via the Beta quantiles, without scipy."""
    def beta_ppf(q, a, b, lo=0.0, hi=1.0):
        for _ in range(200):                       # bisection on the regularised
            mid = (lo + hi) / 2                    # incomplete beta, 200 halvings
            if betainc(a, b, mid) < q: lo = mid
            else: hi = mid
        return (lo + hi) / 2

    def betainc(a, b, x, terms=4000):              # series expansion, adequate here
        if x <= 0: return 0.0
        if x >= 1: return 1.0
        lbeta = (math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b))
        front = math.exp(a * math.log(x) + b * math.log(1 - x) - lbeta) / a
        f, c, d = 1.0, 1.0, 0.0
        for i in range(terms):
            m, num = i // 2, 0.0
            if i == 0: num = 1.0
            elif i % 2 == 0: num = (m * (b - m) * x) / ((a + 2 * m - 1) * (a + 2 * m))
            else: num = -((a + m) * (a + b + m) * x) / ((a + 2 * m) * (a + 2 * m + 1))
            d = 1.0 + num * d
            if abs(d) < 1e-30: d = 1e-30
            d = 1.0 / d
            c = 1.0 + num / c
            if abs(c) < 1e-30: c = 1e-30
            f *= c * d
            if abs(1.0 - c * d) < 1e-12: break
        return front * (f - 1.0)

    lo = 0.0 if k == 0 else beta_ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta_ppf(1 - alpha / 2, k + 1, n - k)
    return lo, hi


def fisher_exact_2x2(a, b, c, d):
    """Two-sided Fisher, summing tables no more probable than the observed."""
    def logp(x, y, z, w):
        return (math.lgamma(x + y + 1) + math.lgamma(z + w + 1)
                + math.lgamma(x + z + 1) + math.lgamma(y + w + 1)
                - math.lgamma(x + y + z + w + 1)
                - math.lgamma(x + 1) - math.lgamma(y + 1)
                - math.lgamma(z + 1) - math.lgamma(w + 1))
    obs = logp(a, b, c, d)
    n1, n2, k = a + b, c + d, a + c
    tot = 0.0
    for i in range(max(0, k - n2), min(n1, k) + 1):
        lp = logp(i, n1 - i, k - i, n2 - k + i)
        if lp <= obs + 1e-9:
            tot += math.exp(lp)
    return min(1.0, tot)


PROBE_K, PROBE_N = 4, 30          # 2026-08-28 probe: 4 gate flips in 30 rows
cp = clopper_pearson(PROBE_K, PROBE_N)
print(f"\n  Clopper-Pearson on the probe's {PROBE_K}/{PROBE_N}: "
      f"[{cp[0]:.4%}, {cp[1]:.4%}]")

# Like-for-like cells: the probe was ONE pair of runs of the AS-IS prompt, so the
# comparable cell is arm B, runs 1&2. Naming the cell is the point -- the first
# write-up quoted p=0.722 without naming it, and BOTH readings that produce 0.722
# pick a cell that is not like-for-like AND give the larger p.
for st in ("R", "B"):
    rws = [i for i in ids if STRAT[i] == st]
    k = sum(1 for i in rws
            if ing(data[i][("B", 1)]["verdict"]) != ing(data[i][("B", 2)]["verdict"]))
    pv = fisher_exact_2x2(PROBE_K, PROBE_N - PROBE_K, k, len(rws) - k)
    print(f"  Fisher, probe {PROBE_K}/{PROBE_N} vs AS-IS arm runs 1&2, stratum {st} "
          f"({k}/{len(rws)}): p = {pv:.4f}")
print("  ⛔ The probe used the AS-IS prompt, so only arm B is like-for-like. A")
print("     reordered-arm cell would compare two different prompts.")

# Source-clustered CI -- cited on five surfaces, computed nowhere until now.
print()
for st in ("R", "B"):
    rws = [i for i in ids if STRAT[i] == st]
    k3 = {a: {i: statistics.mean(data[i][(a, r)]["w"] for r in RUNS) for i in rws}
          for a in ARMS}
    by_src = defaultdict(list)
    for i in rws:
        by_src[cohort[i].get("source") or "?"].append(k3["A"][i] - k3["B"][i])
    srcs = list(by_src)
    rng = random.Random(37)
    boot = sorted(statistics.mean([x for _ in srcs
                                   for x in by_src[srcs[rng.randrange(len(srcs))]]])
                  for _ in range(4000))
    lo, hi = count_interval(*pctl(boot, 0.025, 0.975))
    print(f"  stratum {st}: SOURCE-clustered 95% CI [{lo:+.3f}, {hi:+.3f}]  "
          f"({len(srcs)} sources, largest {max(len(v) for v in by_src.values())} rows)")

# The medians section 6 of the README quotes.
print()
for st in ("R", "B"):
    rws = [i for i in ids if STRAT[i] == st]
    within = [abs(data[i][(a, p_)]["w"] - data[i][(a, q_)]["w"])
              for i in rws for a in ARMS for p_, q_ in PAIRS]
    k3 = {a: {i: statistics.mean(data[i][(a, r)]["w"] for r in RUNS) for i in rws}
          for a in ARMS}
    between = [abs(k3["A"][i] - k3["B"][i]) for i in rws]
    print(f"  stratum {st}: median within-arm |d| {statistics.median(within):.3f}   "
          f"median between-arm |d| (k=3 means) {statistics.median(between):.3f}")

# Prompt identity -- the third control, also hand-run until now.
print()
pa = (Path(__file__).resolve().parents[3] / "filters/human_thriving/v8/prompt-candidate.md")
pb = (Path(__file__).resolve().parents[3] / "filters/human_thriving/v8/prompt-candidate-tail.md")
if pa.exists() and pb.exists():
    ta, tb = pa.read_text(encoding="utf-8"), pb.read_text(encoding="utf-8")
    MARK = "[Paste the summary of the article here]"
    la = collections.Counter(l for l in ta.splitlines() if l.strip())
    lb = collections.Counter(l for l in tb.splitlines() if l.strip())
    print(f"  prompt identity: {len(ta):,} -> {len(tb):,} chars; article offset "
          f"{ta.index(MARK):,} -> {tb.index(MARK):,}; non-blank line multiset differs by "
          f"{list((lb - la).elements()) or 'nothing'} / {list((la - lb).elements()) or 'nothing'}")
else:
    print("  prompt identity: NOT CHECKED — prompt files not found from this path")

print()
print("=" * 78)
print("4h. FAMILY / MULTIPLICITY -- stated, not buried in a constant")
print("=" * 78)
print(f"  This run printed {N_NOMINAL_INTERVALS} nominal 95% intervals.")
for st, pv in (("R", None), ("B", None)):
    pass
print("  ⛔ NO FAMILY WAS PRE-REGISTERED. That is the defect, and no arithmetic")
print("     repairs it after the fact. Read the two permutation p-values in 4f")
print("     against whichever family you consider honest, and note that the answer")
print("     CHANGES: p(R)=0.0049 clears 0.05 and 0.05/2 (the two pre-registered")
print("     direction tests) but NOT 0.05/%d = %.5f. The headline is significant"
      % (N_NOMINAL_INTERVALS, 0.05 / max(N_NOMINAL_INTERVALS, 1)))
print("     nominally and is NOT multiplicity-robust across the full family.")
print("  ⛔ Do not resolve this by picking the family that keeps the result.")

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
