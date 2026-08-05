#!/usr/bin/env python3
"""LD#92 discriminating analysis: is the solutions v6 -1.13 DiD real or a selection artifact?

Reads the oracle output produced by scripts/score_deepseek_production.py and the
design file from sample_designs.py, and reports for each of the three designs:

  DiD = mean(oracle - student | short) - mean(oracle - student | long)

with a source-clustered bootstrap CI and p, Holm-corrected across the three
designs. (An article-level permutation p is also printed, parenthesised: it
ignores clustering and is anticonservative, so it is shown for continuity with
the first write-up, not to be quoted.) Also reports the two known asymmetries
(scrape-junk skip rate, smart_compress rate) per arm, because both differ
between short and long by construction and both sit inside the DiD.

RESULT, 2026-08-05 (n=80/arm, 456 articles, deepseek-chat, 0 errors, 0 junk):

    design        DiD    cluster 95% CI   cluster p   +Holm    MAE ratio
    D1_op2.25   -0.790   [-1.29, -0.28]     0.0032    0.0032      1.24
    D2_op4.00   -0.861   [-1.34, -0.38]     0.0006    0.0012      1.58
    D3_pct2.3   -1.119   [-1.61, -0.61]     <5e-5     <1.5e-4     1.91

Reproduce from the committed fixture (no API calls, no sadalsuud access):

    PYTHONPATH=. python3 scripts/diagnostics/ld92_analyze_did.py \
        --design tests/fixtures/ld92/design.json \
        --scored tests/fixtures/ld92/deepseek_scored.jsonl

The selection-artifact hypothesis predicted D2 markedly more negative than D1
(arm depth ratio worsens 0.50 -> 0.19) and D3 collapsing toward zero (depth
equalised). Neither happened: D2 moved -0.071, and D3 — the design where the
artifact is largely removed — is the LARGEST effect, not the smallest. The
effect is identified. Unchanged with the gatekeeper off (corroborating LD#94),
and it survives dropping the smart_compress-truncated long rows (D3 -1.024,
p=0.0002).

Residual caveat, stated rather than dismissed: matched-percentile selection
removes *differential severity* but not *differential noise*. The short arm's
1.91x MAE ratio means its selected set regresses further toward the mean, which
contributes some negative DiD even in D3. D2 is the independent check on that,
and it barely moved.
"""
import argparse
import json
import random
import statistics as st

WEIGHTS = {
    "solution_concreteness": 0.20,
    "systemic_impact": 0.20,
    "evidence_strength": 0.15,
    "governance_intervention_strength": 0.15,
    "community_practice_strength": 0.10,
    "equity_access": 0.10,
    "economic_viability": 0.10,
}
GATE_DIM, GATE_THRESH, GATE_MAX = "solution_concreteness", 3, 3.0
ANALYSIS_FIELD = "solutions_analysis"


def oracle_weighted(analysis, apply_gate=True):
    dims = {}
    for d in WEIGHTS:
        v = analysis.get(d)
        if isinstance(v, dict):
            v = v.get("score")
        if v is None:
            return None
        dims[d] = float(v)
    wa = sum(dims[d] * w for d, w in WEIGHTS.items())
    if apply_gate and dims[GATE_DIM] < GATE_THRESH:
        wa = min(wa, GATE_MAX)
    return wa


def did(pairs_short, pairs_long):
    """pairs_* are lists of (oracle - student) deltas."""
    return st.mean(pairs_short) - st.mean(pairs_long)


def perm_test(short, lon, n=200000, seed=7):
    obs = did(short, lon)
    pool = short + lon
    k = len(short)
    rng = random.Random(seed)
    hits = 0
    for _ in range(n):
        rng.shuffle(pool)
        if abs(did(pool[:k], pool[k:])) >= abs(obs) - 1e-12:
            hits += 1
    return obs, (hits + 1) / (n + 1)


def cluster_boot(short_rows, long_rows, n=20000, seed=11):
    """Resample SOURCES with replacement, not articles — a single feed can
    supply a large share of one arm (nature_recovery's CI was understated ~2x
    for exactly this reason).

    n and seed are pinned here and matched in ld92_crosscheck.py. They were
    10000 vs 20000, which made the two scripts report D3 as [-1.62,-0.60] and
    [-1.61,-0.61] for the same quantity — a discrepancy with no meaning.
    """
    by_src = {}
    for r, arm in [(r, "s") for r in short_rows] + [(r, "l") for r in long_rows]:
        by_src.setdefault(r["source"], []).append((arm, r["delta"]))
    srcs = list(by_src)
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        s, l = [], []
        for _ in range(len(srcs)):
            for arm, d in by_src[srcs[rng.randrange(len(srcs))]]:
                (s if arm == "s" else l).append(d)
        if s and l:
            out.append(did(s, l))
    out.sort()
    m = len(out)
    # Cluster-aware two-sided bootstrap p, consistent with the CI beside it.
    # The article-level permutation below ignores clustering and is therefore
    # anticonservative; this is the number to quote.
    p = min(1.0, 2 * min(sum(1 for v in out if v >= 0) / m,
                         sum(1 for v in out if v <= 0) / m))
    return out[int(0.025 * m)], out[int(0.975 * m)], p


def holm(pvals):
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m = len(pvals)
    adj = [0.0] * m
    prev = 0.0
    for rank, i in enumerate(idx):
        val = min(1.0, (m - rank) * pvals[i])
        prev = max(prev, val)
        adj[i] = prev
    return adj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", required=True)
    ap.add_argument("--scored", required=True)
    ap.add_argument("--no-gate", action="store_true", help="omit the deployed gatekeeper")
    ap.add_argument("--out", help="optional path to dump the per-design results as JSON")
    args = ap.parse_args()

    design = json.load(open(args.design))
    meta = design["meta"]

    oracle, skipped, errored = {}, {}, {}
    for line in open(args.scored):
        r = json.loads(line)
        if "skipped" in r:
            skipped[r["id"]] = r["skipped"]
            continue
        if "error" in r:
            errored[r["id"]] = r["error"]
            continue
        a = r.get(ANALYSIS_FIELD)
        if not a:
            continue
        wa = oracle_weighted(a, apply_gate=not args.no_gate)
        if wa is not None:
            # Raw scorer output carries `content`; the committed fixture carries
            # a precomputed `words` instead, so article bodies stay out of git.
            words = r.get("words")
            if words is None:
                words = len((r.get("content") or "").split())
            oracle[r["id"]] = {"wa": wa, "words": words}

    print(f"oracle scored={len(oracle)}  scrape-junk skipped={len(skipped)}  errors={len(errored)}")
    print(f"gatekeeper: {'OFF' if args.no_gate else 'ON'}\n")

    results = []
    for dname in ["D1_op2.25", "D2_op4.00", "D3_pct2.3"]:
        arms = {}
        for arm in ("short", "long"):
            rows = []
            n_skip = n_err = 0
            for aid in design["membership"][dname][arm]:
                if aid in skipped:
                    n_skip += 1
                    continue
                if aid in errored:
                    n_err += 1
                    continue
                if aid not in oracle:
                    continue
                m = meta[aid]
                rows.append({
                    "id": aid, "source": m["source"], "student": m["raw"],
                    "oracle": oracle[aid]["wa"],
                    "delta": oracle[aid]["wa"] - m["raw"],
                    "len": m["content_length"],
                    "compressed": oracle[aid]["words"] > 800,
                })
            arms[arm] = {"rows": rows, "n_skip": n_skip, "n_err": n_err,
                         "n_drawn": len(design["membership"][dname][arm])}
        s, l = arms["short"]["rows"], arms["long"]["rows"]
        ds = [r["delta"] for r in s]
        dl = [r["delta"] for r in l]
        obs, p = perm_test(ds, dl)
        lo, hi, p_clust = cluster_boot(s, l)
        mae_s = st.mean(abs(x) for x in ds)
        mae_l = st.mean(abs(x) for x in dl)
        results.append({
            "design": dname, "did": obs, "p": p, "p_clust": p_clust, "ci": (lo, hi),
            "n_s": len(s), "n_l": len(l),
            "mae_ratio": mae_s / mae_l if mae_l else float("nan"),
            "student_s": st.mean(r["student"] for r in s),
            "student_l": st.mean(r["student"] for r in l),
            "oracle_s": st.mean(r["oracle"] for r in s),
            "oracle_l": st.mean(r["oracle"] for r in l),
            "junk_s": arms["short"]["n_skip"], "junk_l": arms["long"]["n_skip"],
            "drawn_s": arms["short"]["n_drawn"], "drawn_l": arms["long"]["n_drawn"],
            "comp_s": sum(r["compressed"] for r in s),
            "comp_l": sum(r["compressed"] for r in l),
            "err_s": arms["short"]["n_err"], "err_l": arms["long"]["n_err"],
        })

    for r, pa in zip(results, holm([r["p"] for r in results])):
        r["p_holm"] = pa
    for r, pa in zip(results, holm([r["p_clust"] for r in results])):
        r["p_clust_holm"] = pa

    print(f"{'design':11} {'n_s':>4} {'n_l':>4} {'DiD':>7} {'cluster 95% CI':>18} "
          f"{'p_clust':>8} {'+Holm':>8} {'MAEratio':>9} {'(p_perm)':>9}")
    for r in results:
        print(f"{r['design']:11} {r['n_s']:4} {r['n_l']:4} {r['did']:+7.3f} "
              f"[{r['ci'][0]:+6.2f},{r['ci'][1]:+6.2f}] {r['p_clust']:8.5f} "
              f"{r['p_clust_holm']:8.5f} {r['mae_ratio']:9.2f} {r['p']:9.4f}")
    print("  quote p_clust/+Holm. (p_perm) is article-level and ignores source "
          "clustering, so it is anticonservative — shown only for continuity.")

    print(f"\n{'design':11} {'stu_s':>6} {'stu_l':>6} {'ora_s':>6} {'ora_l':>6} "
          f"{'junk s/l':>10} {'compr s/l':>10} {'err s/l':>8}")
    for r in results:
        print(f"{r['design']:11} {r['student_s']:6.2f} {r['student_l']:6.2f} "
              f"{r['oracle_s']:6.2f} {r['oracle_l']:6.2f} "
              f"{str(r['junk_s'])+'/'+str(r['junk_l']):>10} "
              f"{str(r['comp_s'])+'/'+str(r['comp_l']):>10} "
              f"{str(r['err_s'])+'/'+str(r['err_l']):>8}")

    print("\nPRE-REGISTERED READING")
    d1, d2, d3 = (r["did"] for r in results)
    print(f"  artifact predicts: D2 more negative than D1, D3 -> 0")
    print(f"  real effect predicts: D1 ~ D2 ~ D3")
    print(f"  observed: D1={d1:+.3f}  D2={d2:+.3f}  D3={d3:+.3f}")
    print(f"  D2-D1 = {d2-d1:+.3f}   D3 magnitude vs D1 = {abs(d3)/abs(d1) if d1 else float('nan'):.2f}x")

    # Opt-in: this used to write ld92_results.json into the CWD unconditionally,
    # which drops an untracked file in the repo root every time it is run.
    if args.out:
        json.dump(results, open(args.out, "w"), indent=2)
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
