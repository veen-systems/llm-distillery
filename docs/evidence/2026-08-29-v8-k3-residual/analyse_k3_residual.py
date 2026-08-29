"""H-V8-6 — how much does repeating the oracle actually buy, and what does it cost?

⛔ THIS IS REVISION 2. Revision 1 was reviewed on 2026-08-29 by three lenses and three of
its load-bearing claims did not survive. What changed, so the errors are not re-made:

  1. ⛔⛔ Revision 1's ⭐ headline "out-of-sample check" WAS AN ALGEBRAIC IDENTITY.
     Over 3 draws of a binary, discordant pairs = s(3-s) ∈ {0,2}, so the pairwise
     disagreement rate ≡ (2/3) × non-unanimity, ALWAYS; and on the model side
     2·E[p(1-p)] ≡ (2/3) × fitted(P(s=1)+P(s=2)). "Predicted 5.21% vs measured 5.3%" was
     therefore the IN-SAMPLE fit residual, rescaled by 2/3 and relabelled as validation.
     The sibling Phase A README already warned that §1 and §2 are the same statistic.
     Replaced by a genuine held-out check: LEAVE ONE RUN OUT — fit on two runs, predict the
     third, which the fit never saw.
  2. ⛔ The estimand is computed for the SCOPE GATE and, separately, for the OP-POINT LABEL.
     Revision 1 reported only the gate, then compared it to a plan figure that counts label
     flips on a boundary-weighted panel. Two axes swapped in one sentence.
  3. ⛔ Cost is reported in DOLLARS from the measured per-article rates, per arm. Revision 1
     hardcoded "3x" and "1.67x", which are draw counts and assume no cache discount; the
     measured repeat price makes k=5 ≈ +$3.50 on 6,590 rows, not "1.67x the money".
  4. Grid MLE replaced by a bounded optimiser with an explicit boundary check (revision 1's
     1.25x grid moved one cell's answer by 0.25pp, half its headline effect, and its p=0.5
     control sat exactly ON the grid ceiling — which is where its "1pp resolution" came from).
  5. The residual and the pair rate are now EXACT (incomplete-beta moments), not quadrature:
     revision 1's midpoint rule integrated the Beta(0.039,0.149) density to 0.42, not 1.0.
     It happened not to matter (the integrand vanishes at both ends) and that was luck.
  6. `scope_verdict` has FIVE values, not two. The vocabulary is asserted and printed.
  7. Run exchangeability — assumed by the model, never tested in revision 1 — gets a
     Cochran's Q per cell.

Usage: python3 analyse_k3_residual.py <phaseA-scratch-dir>
"""
import json, math, sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import betaln, betainc
from scipy.stats import chi2

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from filters.uplifting.v7.base_scorer import BaseUpliftingScorer as S

DIMS, W = S.DIMENSION_NAMES, S.DIMENSION_WEIGHTS
OP = dict((n, t) for n, t, _ in S.TIER_THRESHOLDS)["medium"]
GK_DIM, GK_MIN, GK_CAP = S.GATEKEEPER_DIMENSION, S.GATEKEEPER_MIN, S.GATEKEEPER_CAP
SCRATCH = Path(sys.argv[1])
RUNS, ARMS = (1, 2, 3), ("A", "B")

# Measured per-article prices, docs/evidence/2026-08-29-v8-phase-a-k3/results.txt §4f.
# first pass / repeat pass, US$ per article, DeepSeek off-peak.
PRICE = {"A": (0.000519, (0.000267 + 0.000264) / 2),
         "B": (0.002736, (0.000275 + 0.000275) / 2)}
CORPUS_ROWS = 6590

# The full v8 verdict vocabulary. `in_scope` scores normally; every other value zeroes all
# six dimensions (prompt-candidate.md STEP 1). If a future prompt adds a value, this raises
# rather than silently folding it into the exclusion class.
KNOWN_VERDICTS = {"in_scope", "out_of_scope", "harm_is_subject",
                  "response_to_harm", "no_person_benefits"}


def wavg(sc):
    s = {d: max(0.0, min(10.0, float(sc[d]))) for d in DIMS}
    w = sum(s[d] * W[d] for d in DIMS)
    if GK_DIM is not None and s[GK_DIM] < GK_MIN and w > GK_CAP:
        w = GK_CAP
    return w


# ---------------------------------------------------------------- load
cohort = {json.loads(l)["id"]: json.loads(l) for l in open(SCRATCH / "phaseA_cohort200.jsonl")}
gate, label = defaultdict(dict), defaultdict(dict)
verdicts = Counter()
for arm in ARMS:
    for run in RUNS:
        for line in open(SCRATCH / f"phaseA_{arm}{run}.jsonl"):
            r = json.loads(line)
            a = r["uplifting_analysis"]
            v = a["scope_verdict"]
            verdicts[v] += 1
            gate[r["id"]][(arm, run)] = int(v == "in_scope")
            label[r["id"]][(arm, run)] = int(wavg({d: a[d]["score"] for d in DIMS}) >= OP)
ids = sorted(gate)
unknown = set(verdicts) - KNOWN_VERDICTS
if unknown:
    raise SystemExit(f"FATAL: unknown scope_verdict value(s) {unknown} — the binary collapse "
                     f"in this script assumes every non-`in_scope` value is an exclusion.")
assert all(len(gate[i]) == 6 for i in ids), "not all rows carry 6 observations"
STRAT = {i: cohort[i]["stratum"] for i in ids}

print(f"op-point {OP} (imported from filters/uplifting/v7/base_scorer.py)   rows {len(ids)}")
print("scope_verdict vocabulary over 1,200 labels (the gate collapses all but the first):")
for v, c in verdicts.most_common():
    print(f"    {v:<20} {c:>5}   {'IN SCOPE' if v == 'in_scope' else 'exclusion'}")
print()

# ---------------------------------------------------------------- beta-binomial, exactly
def bb_logpmf(s, n, a, b):
    return (math.lgamma(n + 1) - math.lgamma(s + 1) - math.lgamma(n - s + 1)
            + betaln(a + s, b + n - s) - betaln(a, b))


LO, HI = 1e-4, 1e4          # optimiser bounds, checked for contact after every fit


def fit_bb(counts, n=3):
    """MLE by bounded Nelder-Mead on (log a, log b), multi-start. Returns (a, b, logL, on_edge).

    Revision 1 used a 48x48 grid with 1.25x steps. Refitting on a 1.02x grid moved one
    cell's k=3 residual by 0.25pp -- half that revision's headline effect -- so the grid was
    not at the optimum. `on_edge` is returned, never swallowed: a fit that walks into a bound
    is a different object from a fit that converged."""
    def nll(theta):
        a, b = math.exp(theta[0]), math.exp(theta[1])
        if not (LO <= a <= HI and LO <= b <= HI):
            return 1e12
        return -sum(c * bb_logpmf(s, n, a, b) for s, c in counts.items() if c)
    best = None
    for a0 in (0.05, 0.5, 5.0):
        for b0 in (0.05, 0.5, 5.0):
            r = minimize(nll, [math.log(a0), math.log(b0)], method="Nelder-Mead",
                         options={"xatol": 1e-9, "fatol": 1e-11, "maxiter": 8000})
            if best is None or r.fun < best.fun:
                best = r
    a, b = math.exp(best.x[0]), math.exp(best.x[1])
    on_edge = (a <= LO * 1.01 or a >= HI * 0.99 or b <= LO * 1.01 or b >= HI * 0.99)
    return a, b, -best.fun, on_edge


def _seg_moment(a, b, m, n_, upper_half):
    """E[ p^m (1-p)^n_ * 1{p in the chosen half} ] under Beta(a,b), in closed form:
       = B(a+m, b+n_)/B(a,b) * I_{0.5}(a+m, b+n_)   for the lower half,
       and the same with (1 - I) for the upper. Exact -- no quadrature."""
    w = math.exp(betaln(a + m, b + n_) - betaln(a, b))
    inc = float(betainc(a + m, b + n_, 0.5))
    return w * (inc if not upper_half else (1.0 - inc))


def residual(a, b, k):
    """P(the k-majority differs from the limit verdict 1{p>0.5}), exactly.

    maj(p,k) = sum_{j>k/2} C(k,j) p^j (1-p)^(k-j) is a polynomial, so each term integrates
    against the Beta density in closed form over each half of [0,1]."""
    tot = 0.0
    for j in range((k // 2) + 1, k + 1):
        c = math.comb(k, j)
        tot += c * _seg_moment(a, b, j, k - j, upper_half=False)     # p<0.5, majority says yes
    for j in range(0, (k // 2) + 1):
        c = math.comb(k, j)
        tot += c * _seg_moment(a, b, j, k - j, upper_half=True)      # p>0.5, majority says no
    return tot


def pair_disagree(a, b):
    """2E[p(1-p)] in closed form. ⚠️ IDENTICALLY (2/3)x the fitted non-unanimity for n=3 --
    kept only to make that identity checkable, never as a validation."""
    return 2.0 * math.exp(betaln(a + 1, b + 1) - betaln(a, b))


def cochran_q(mat):
    """Cochran's Q over k runs x n rows of 0/1. Tests whether the runs are exchangeable --
    the model's own assumption, untested in revision 1."""
    x = np.asarray(mat, dtype=float)          # rows x runs
    n, k = x.shape
    Cj, Ri = x.sum(0), x.sum(1)
    denom = k * Ri.sum() - (Ri ** 2).sum()
    if denom == 0:
        return float("nan"), float("nan")
    Q = (k - 1) * (k * (Cj ** 2).sum() - Cj.sum() ** 2) / denom
    return Q, float(chi2.sf(Q, k - 1))


def counts_of(binary, rws, arm):
    c = Counter(sum(binary[i][(arm, r)] for r in RUNS) for i in rws)
    return {s: c.get(s, 0) for s in range(4)}


def analyse(binary, name):
    print("=" * 96)
    print(f"ESTIMAND: {name}")
    print("=" * 96)
    out = {}
    for arm, arm_label in (("A", "reordered"), ("B", "as-is")):
        for st in ("R", "B"):
            rws = [i for i in ids if STRAT[i] == st]
            cnts = counts_of(binary, rws, arm)
            n = len(rws)
            a, b, ll, edge = fit_bb(cnts)
            if edge:
                print(f"  ⛔ arm {arm} stratum {st}: MLE ON THE OPTIMISER BOUND "
                      f"(a={a:.5g} b={b:.5g}) — treat every number in this row as unreliable")
            res = {k: residual(a, b, k) for k in (1, 3, 5, 7)}
            # chi-square goodness of fit, df = 4 cells - 1 (sum) - 2 (params) = 1
            exp = {s: n * math.exp(bb_logpmf(s, 3, a, b)) for s in range(4)}
            chi = sum((cnts[s] - exp[s]) ** 2 / exp[s] for s in range(4) if exp[s] > 0)
            q, qp = cochran_q([[binary[i][(arm, r)] for r in RUNS] for i in rws])
            per_run = [sum(binary[i][(arm, r)] for i in rws) for r in RUNS]
            print(f"arm {arm} ({arm_label})  stratum {st}  n={n}")
            print(f"  observed s=0..3 {[cnts[s] for s in range(4)]}   non-unanimous "
                  f"{cnts[1] + cnts[2]}/{n} = {(cnts[1] + cnts[2]) / n:.1%}")
            print(f"  fit Beta({a:.4f}, {b:.4f})  logL {ll:.2f}   expected "
                  f"{[round(exp[s], 1) for s in range(4)]}   chi2(df=1) {chi:.2f} "
                  f"p={chi2.sf(chi, 1):.3f}")
            print(f"  P(k-majority != limit):  k=1 {res[1]:.3%}  k=3 {res[3]:.3%}  "
                  f"k=5 {res[5]:.3%}  k=7 {res[7]:.3%}")
            print(f"  run exchangeability: per-run positives {per_run}  Cochran Q={q:.3f} "
                  f"p={qp:.3f}" + ("   ⚠️ runs differ" if qp < 0.05 else ""))
            out[(arm, st)] = (a, b, res, cnts, n, rws)
    return out


def boot_ci(binary, arm, rws, k, reps=400, seed=991):
    rng = np.random.default_rng(seed)
    vals, edges = [], 0
    idx = np.arange(len(rws))
    for _ in range(reps):
        samp = [rws[j] for j in rng.integers(0, len(rws), len(rws))]
        c = counts_of(binary, samp, arm)
        a, b, _, edge = fit_bb(c)
        edges += edge
        vals.append(residual(a, b, k))
    vals.sort()
    return vals[int(0.025 * reps)], vals[int(0.975 * reps)], edges


def paired_arm_diff(binary, rws, k, reps=400, seed=17):
    """Revision 1 compared two MARGINAL intervals to claim one arm was less stable. The design
    is PAIRED — the same 50 articles under both prompts — so the difference must be
    bootstrapped on the shared rows."""
    rng = np.random.default_rng(seed)
    d = []
    for _ in range(reps):
        samp = [rws[j] for j in rng.integers(0, len(rws), len(rws))]
        aa, ab, _, _ = fit_bb(counts_of(binary, samp, "A"))
        ba, bb_, _, _ = fit_bb(counts_of(binary, samp, "B"))
        d.append(residual(aa, ab, k) - residual(ba, bb_, k))
    d.sort()
    return sum(d) / len(d), d[int(0.025 * reps)], d[int(0.975 * reps)]


def leave_one_run_out(binary, arm, rws):
    """THE GENUINE HELD-OUT CHECK, replacing revision 1's algebraic identity.

    Fit the beta-binomial on TWO runs only (n=2). Then predict, for each held-out run, the
    probability that it comes back `1` given what the other two said:
        P(next = 1 | s of 2) = (a + s) / (a + b + 2)      [posterior predictive mean]
    The held-out run's outcomes are not in the likelihood the parameters came from, and the
    conditioning group (s of 2) is a different partition of the data than the fit's histogram.
    Compare predicted against observed, pooled over the three rotations."""
    pred_by_s, obs_by_s = defaultdict(list), defaultdict(list)
    for held in RUNS:
        keep = [r for r in RUNS if r != held]
        c = Counter(sum(binary[i][(arm, r)] for r in keep) for i in rws)
        a, b, _, _ = fit_bb({s: c.get(s, 0) for s in range(3)}, n=2)
        for i in rws:
            s2 = sum(binary[i][(arm, r)] for r in keep)
            pred_by_s[s2].append((a + s2) / (a + b + 2))
            obs_by_s[s2].append(binary[i][(arm, held)])
    rows = []
    for s2 in (0, 1, 2):
        if not obs_by_s[s2]:
            continue
        rows.append((s2, len(obs_by_s[s2]),
                     sum(pred_by_s[s2]) / len(pred_by_s[s2]),
                     sum(obs_by_s[s2]) / len(obs_by_s[s2])))
    return rows


# ---------------------------------------------------------------- run it
gate_fits = analyse(gate, "SCOPE GATE  (scope_verdict == 'in_scope')")
print()
label_fits = analyse(label, f"OP-POINT LABEL  (weighted average >= {OP})   "
                            f"<- the quantity the plan's ~860 figure counts")

print("\n" + "=" * 96)
print("INTERVALS, PAIRED DIFFERENCES, AND THE HELD-OUT CHECK  (scope gate)")
print("=" * 96)
for (arm, st), (a, b, res, cnts, n, rws) in gate_fits.items():
    lo, hi, edges = boot_ci(gate, arm, rws, 3)
    print(f"arm {arm} stratum {st}: k=3 residual {res[3]:.3%}  95% CI [{lo:.2%}, {hi:.2%}]"
          f"   bootstrap replicates hitting a bound: {edges}/400")
for st in ("R", "B"):
    rws = [i for i in ids if STRAT[i] == st]
    m, lo, hi = paired_arm_diff(gate, rws, 3)
    verdict = "NOT DISTINGUISHABLE" if lo <= 0 <= hi else "differs"
    print(f"paired A-B difference, stratum {st}: {m:+.3%}  95% CI [{lo:+.2%}, {hi:+.2%}]"
          f"  -> {verdict}")
print("\nHELD-OUT: fit on 2 runs, predict the 3rd (pooled over all three rotations)")
for arm in ARMS:
    for st in ("R", "B"):
        rws = [i for i in ids if STRAT[i] == st]
        for s2, nn, pred, obs in leave_one_run_out(gate, arm, rws):
            print(f"  arm {arm} stratum {st}  other two runs said {s2}/2 in_scope  "
                  f"n={nn:>4}   predicted {pred:.1%}   observed {obs:.1%}   "
                  f"|err| {abs(pred - obs):.1%}")

print("\n" + "=" * 96)
print("WHAT k COSTS, IN DOLLARS  (measured per-article prices, Phase A results.txt 4f)")
print("=" * 96)
for arm, (first, repeat) in PRICE.items():
    line = []
    for k in (1, 3, 5, 7):
        line.append(f"k={k} ${CORPUS_ROWS * (first + (k - 1) * repeat):6.2f}")
    print(f"  arm {arm} ({'reordered' if arm == 'A' else 'as-is'}): " + "   ".join(line))
print(f"  On {CORPUS_ROWS:,} rows, going k=3 -> k=5 costs "
      f"+${CORPUS_ROWS * 2 * PRICE['A'][1]:.2f} (arm A) / "
      f"+${CORPUS_ROWS * 2 * PRICE['B'][1]:.2f} (arm B).")
for (arm, st), (a, b, res, cnts, n, rws) in gate_fits.items():
    if st == "R":
        print(f"  arm {arm}: rows it fixes, k=3->k=5: "
              f"{CORPUS_ROWS * (res[3] - res[5]):.0f}  (gate, production-mix rate)")

print("\n" + "=" * 96)
print("CONTROLS -- hand values computed analytically, not simulated")
print("=" * 96)
for true_p in (0.5, 0.2, 0.05):
    # a point mass at p: residual = min(maj(p,3), 1-maj(p,3)); no fit involved in the target
    m3 = 3 * true_p ** 2 * (1 - true_p) + true_p ** 3
    hand = min(m3, 1 - m3)
    N = 200000
    rng = np.random.default_rng(7)
    draws = rng.binomial(3, true_p, N)
    c = Counter(int(x) for x in draws)
    a, b, _, edge = fit_bb({s: c.get(s, 0) for s in range(4)})
    print(f"  point mass p={true_p}: recovered {residual(a, b, 3):.2%}   hand {hand:.2%}   "
          f"fit Beta({a:.3g},{b:.3g}){'  ON BOUND' if edge else ''}")
print("  ⛔ Revision 1 asserted 25% for the fair coin and its estimator printed 48.4%. The")
print("     ESTIMATOR was right (at p=0.5 the limit verdict is a tie, so the answer is 50%),")
print("     and its 1.6pp gap was the GRID CEILING, not resolution: it fitted Beta(717,717),")
print("     exactly the last grid point. This revision has no grid.")

# ------------------------------------------------------------------ machine-readable dump
# The figures read THIS, never the prose: a chart and a paragraph that quote a number
# independently are two hand-maintained copies of it.
dump = {"op_point": OP, "corpus_rows": CORPUS_ROWS, "price": PRICE, "cells": {}}
for estimand, fits, binary in (("gate", gate_fits, gate), ("label", label_fits, label)):
    for (arm, st), (a, b, res, cnts, n, rws) in fits.items():
        lo, hi, edges = boot_ci(binary, arm, rws, 3)
        dump["cells"][f"{estimand}|{arm}|{st}"] = {
            "estimand": estimand, "arm": arm, "stratum": st, "n": n,
            "alpha": a, "beta": b, "observed": [cnts[s] for s in range(4)],
            "expected": [n * math.exp(bb_logpmf(s, 3, a, b)) for s in range(4)],
            "residual": {str(k): res[k] for k in (1, 3, 5, 7)},
            "k3_ci": [lo, hi], "bootstrap_edge_hits": int(edges),
        }
with open(Path(__file__).with_name("figures_data.json"), "w") as f:
    json.dump(dump, f, indent=2)
print(f"\nwrote figures_data.json ({len(dump['cells'])} cells) -- the figures read this file")

print("\n" + "=" * 96)
print("THE IDENTITY revision 1 mistook for a validation")
print("=" * 96)
for (arm, st), (a, b, res, cnts, n, rws) in gate_fits.items():
    nu = (cnts[1] + cnts[2]) / n
    print(f"  arm {arm} stratum {st}: observed non-unanimity {nu:.2%} x 2/3 = {2 * nu / 3:.2%}"
          f"   <- this IS the 'independently measured' pair-disagreement rate")
    print(f"      model 2E[p(1-p)] = {pair_disagree(a, b):.4%}   "
          f"(2/3)x fitted non-unanimity = "
          f"{2 / 3 * (math.exp(bb_logpmf(1, 3, a, b)) + math.exp(bb_logpmf(2, 3, a, b))):.4%}"
          f"   -> identical by construction, not corroboration")
