"""Score mass per bin for the three populations the corpus decision turns on.

⛔⛔ TWO THINGS THIS FILE EXISTS TO GET RIGHT, both found by review on 2026-08-29:

1. **`math.fsum`, never `sum`.** CPython 3.12 changed `sum()` to Neumaier compensated
   summation. The 2026-08-28 census ran on Python 3.11 (naive), this machine runs 3.14
   (compensated), and on the SAME 6,590 rows with the SAME weights **34 rows land in a
   different bin** -- e.g. labels [6,7,7,6,6,7] are exactly 6.5, and naive summation returns
   6.49999999999999911, which bins as 6.0. Neither run is buggy; the histogram is simply
   interpreter-dependent at bin edges. `math.fsum` is correctly rounded, so it is the same
   answer on every interpreter, and it is what this file uses.
2. **The production column must be the population the draw can actually SAMPLE.** The first
   version compared the corpus against all-lengths production while the draw excludes
   sub-300-char rows, which are 6.9x less likely to be positive -- the same
   target-against-an-excluded-population error the 2026-08-28 GN correction was written
   about. Both columns are computed here and both are reported.

Usage: python3 measure_score_mass.py <v7-labels> <pool> <corpus> <out.json>
"""
import json, math, sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from filters.uplifting.v7.base_scorer import BaseUpliftingScorer as S

DIMS, W = S.DIMENSION_NAMES, S.DIMENSION_WEIGHTS
GK, GKMIN, GKCAP = S.GATEKEEPER_DIMENSION, S.GATEKEEPER_MIN, S.GATEKEEPER_CAP
FLOOR = 300


def wavg(vals):
    s = {d: max(0.0, min(10.0, float(v))) for d, v in zip(DIMS, vals)}
    w = math.fsum(s[d] * W[d] for d in DIMS)          # NOT sum() -- see the module docstring
    if GK and s[GK] < GKMIN and w > GKCAP:
        w = GKCAP
    return w


def hist(vals, step=0.5, hi=10.0):
    c = Counter(min(int(v / step) * step, hi - step) for v in vals)
    n = len(vals)
    return {f"{k:.1f}": 100 * c[k] / n for k in sorted(c)}, n


v7_labels, pool_f, corpus_f, out_f = sys.argv[1:5]
v7 = [wavg(json.loads(l)["labels"]) for l in open(v7_labels, encoding="utf-8")]
pool = [json.loads(l) for l in open(pool_f, encoding="utf-8").read().splitlines()[1:]]
corpus_ids = {json.loads(l)["id"] for l in open(corpus_f, encoding="utf-8")}

s2 = lambda rs: [r["v7_score"] for r in rs
                 if r["v7_stage_used"] == "stage2" and r["v7_score"] is not None]
prod_all = s2(pool)
prod_drawable = s2([r for r in pool if r["content_length"] >= FLOOR])
new = s2([r for r in pool if r["id"] in corpus_ids])

out = {}
for name, vals in (("v7", v7), ("production_all_lengths", prod_all),
                   ("production_drawable", prod_drawable), ("new", new)):
    h, n = hist(vals)
    out[name] = h
    out.setdefault("n", {})[name] = n
    print(f"{name:<24} n={n:>7,}")

band = lambda name, lo, hi: sum(v for k, v in out[name].items() if lo <= float(k) < hi)
print(f"\n{'band':<20}{'prod(all)':>11}{'prod(drawable)':>16}{'v7':>9}{'new':>9}"
      f"{'v7 x':>8}{'new x':>8}   <- x is against prod(drawable), the population sampled")
for label, lo, hi in (("low-middle 1.5-3.5", 1.5, 3.5), ("decision 3.5-5.5", 3.5, 5.5),
                      ("visible 5.5-10", 5.5, 10.0)):
    pa, pd = band("production_all_lengths", lo, hi), band("production_drawable", lo, hi)
    v, nw = band("v7", lo, hi), band("new", lo, hi)
    print(f"{label:<20}{pa:>10.2f}%{pd:>15.2f}%{v:>8.2f}%{nw:>8.2f}%{v/pd:>7.2f}x{nw/pd:>7.2f}x")
json.dump(out, open(out_f, "w"), indent=2)
print(f"\nwrote {out_f}")
