#!/usr/bin/env python3
"""LD#92 review follow-ups: second-oracle cross-check + cluster-aware p-values.

Two defects in the 2026-08-05 write-up this repairs:

1. ONE ORACLE. DiD cancels a *constant* oracle bias. DeepSeek is not solutions
   v6's teacher (gemini is), and if DeepSeek's bias varies with input length —
   plausible, it sees a bare headline in the short arm — that is confounded with
   the effect being claimed. Re-scores the identification-critical D3 sample with
   gemini-2.5-flash and compares.

2. ARTICLE-LEVEL PERMUTATION with source-clustered CIs. A permutation test that
   ignores clustering is anticonservative, so the reported p-values were
   optimistic. Replaced with a source-clustered bootstrap p-value, consistent
   with the CI it accompanies.
"""
import argparse
import json
import random
import statistics as st

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ld92_analyze_did import oracle_weighted, did


def load_oracle(path, field="solutions_analysis"):
    out = {}
    for line in open(path):
        r = json.loads(line)
        a = r.get(field)
        if not a:
            continue
        wa = oracle_weighted(a)
        if wa is not None:
            out[r["id"]] = wa
    return out


def cluster_boot(short_rows, long_rows, n=20000, seed=11):
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
    lo, hi = out[int(0.025 * m)], out[int(0.975 * m)]
    # Cluster-aware two-sided bootstrap p: how often does the resampled DiD
    # cross zero? Consistent with the CI, unlike an article-level permutation.
    frac_ge = sum(1 for v in out if v >= 0) / m
    frac_le = sum(1 for v in out if v <= 0) / m
    p = min(1.0, 2 * min(frac_ge, frac_le))
    return lo, hi, p, len(srcs)


def build(design, oracle, dname):
    meta = design["meta"]
    arms = {}
    for arm in ("short", "long"):
        rows = []
        for aid in design["membership"][dname][arm]:
            if aid not in oracle:
                continue
            m = meta[aid]
            rows.append({"source": m["source"], "student": m["raw"],
                         "oracle": oracle[aid], "delta": oracle[aid] - m["raw"]})
        arms[arm] = rows
    return arms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", required=True)
    ap.add_argument("--deepseek", required=True)
    ap.add_argument("--gemini", required=True)
    ap.add_argument("--designs", default="D3_pct2.3")
    args = ap.parse_args()

    design = json.load(open(args.design))
    ds = load_oracle(args.deepseek)
    gm = load_oracle(args.gemini)
    print(f"deepseek scored={len(ds)}  gemini scored={len(gm)}\n")

    for dname in args.designs.split(","):
        print(f"===== {dname} =====")
        rows = []
        for label, oracle in (("deepseek-chat", ds), ("gemini-2.5-flash", gm)):
            arms = build(design, oracle, dname)
            s, l = arms["short"], arms["long"]
            if not s or not l:
                print(f"  {label}: no coverage")
                continue
            d = did([r["delta"] for r in s], [r["delta"] for r in l])
            lo, hi, p, nsrc = cluster_boot(s, l)
            rows.append((label, len(s), len(l), d, lo, hi, p, nsrc,
                         st.mean(r["oracle"] for r in s),
                         st.mean(r["oracle"] for r in l),
                         st.mean(r["student"] for r in s),
                         st.mean(r["student"] for r in l)))
        print(f"  {'oracle':18} {'n_s':>4} {'n_l':>4} {'DiD':>7} {'cluster 95% CI':>18} "
              f"{'p_boot':>8} {'srcs':>5}")
        for r in rows:
            print(f"  {r[0]:18} {r[1]:4} {r[2]:4} {r[3]:+7.3f} [{r[4]:+6.2f},{r[5]:+6.2f}] "
                  f"{r[6]:8.4f} {r[7]:5}")
        print(f"\n  {'oracle':18} {'ora_short':>10} {'ora_long':>9} {'stu_short':>10} {'stu_long':>9}")
        for r in rows:
            print(f"  {r[0]:18} {r[8]:10.2f} {r[9]:9.2f} {r[10]:10.2f} {r[11]:9.2f}")

        if len(rows) == 2:
            print(f"\n  cross-oracle: deepseek {rows[0][3]:+.3f} vs gemini {rows[1][3]:+.3f} "
                  f"-> diff {rows[1][3]-rows[0][3]:+.3f}")
            # Per-article agreement on the two oracles, where both scored it.
            both = [(ds[i], gm[i]) for i in ds if i in gm]
            if both:
                md = st.mean(abs(a - b) for a, b in both)
                print(f"  per-article |deepseek - gemini| mean {md:.2f} on n={len(both)} "
                      f"(absolute agreement is NOT the claim; the DiD gap is)")
        print()


if __name__ == "__main__":
    main()
