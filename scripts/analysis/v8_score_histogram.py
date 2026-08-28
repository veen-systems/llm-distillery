"""Phase 0 (human_thriving v8): where does score mass actually sit, corpus vs production?

The Gate 0 targets say the corpus is "2.9x enriched" over production. That is a single
scalar over a threshold, and it cannot answer the question a draw needs answered: which
REGIONS of the 0-10 range are thin, and by how much. The op-point decision (specificity
at 4.5) and the ranking decision (order among articles readers see) are won in different
places, so the enrichment factor has to be stated per region, not once.

Both sides use the SAME weighted-average function. On production rows that is checkable,
because the row carries both the six dimension scores and the scorer's own stored
raw_weighted_average -- so the script asserts its arithmetic against the scorer's on every
row it reads, and aborts if they diverge. Without that, "corpus vs production" would be
comparing two functions and calling the difference composition.

Population, production side: the DRAWABLE one (distinct articles, stage2, minus
news.google.com) -- see docs/evidence/2026-08-28-v8-phase0-drawable-population.md.

Usage:
  PYTHONPATH=<repo> python3 v8_score_histogram.py corpus     <training-split-dir>
  PYTHONPATH=<repo> python3 v8_score_histogram.py production <archive-dir>
"""
import json, glob, os, sys, re
from collections import Counter

NAMES = ["human_wellbeing_impact", "social_cohesion_impact", "justice_rights_impact",
         "evidence_level", "benefit_distribution", "change_durability"]
W = {"human_wellbeing_impact": 0.3, "social_cohesion_impact": 0.2, "justice_rights_impact": 0.15,
     "evidence_level": 0.1, "benefit_distribution": 0.1, "change_durability": 0.15}
BIN = 0.5
GN_DOMAIN = "news.google.com"
WA_EPS = 1e-4

REGIONS = [("anchor      0.0-3.5", 0.0, 3.5),
           ("decision    3.5-5.5", 3.5, 5.5),
           ("visible     5.5-10.0", 5.5, 10.01)]


def wa(labels, apply_gk=True):
    """Identical to corpus_census.py's wa(). Verified against the scorer's own
    raw_weighted_average on production rows (see check below)."""
    s = dict(zip(NAMES, labels))
    v = sum(s[d] * W[d] for d in NAMES)
    if apply_gk and s["evidence_level"] < 3.0 and v > 3.0:
        v = 3.0
    return v


def control():
    """The WA function must move with its inputs and must fire the gatekeeper."""
    hi = wa([8, 8, 8, 8, 8, 8])
    lo = wa([1, 1, 1, 1, 1, 1])
    gk = wa([9, 9, 9, 1.0, 9, 9])          # evidence_level 1.0 -> capped at 3.0
    ok = hi > lo and abs(gk - 3.0) < 1e-9
    print("  control: wa(8s)=%.2f > wa(1s)=%.2f, gatekeeper caps to %.2f -> %s"
          % (hi, lo, gk, "PASS" if ok else "FAIL"))
    return ok


def collect_corpus(base):
    vals = []
    files = sorted(glob.glob(os.path.join(base, "*.jsonl")))
    if not files:
        sys.exit("ABORT: no *.jsonl under %s -- an empty scan reports clean" % base)
    for f in files:
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            labels = r.get("labels")
            if not labels or len(labels) != 6:
                continue
            vals.append(wa(labels))
    return vals, "corpus: %d files, %d labelled rows" % (len(files), len(vals))


def collect_production(base):
    vals, seen = [], set()
    files = sorted(glob.glob(os.path.join(base, "*.jsonl")))
    if not files:
        sys.exit("ABORT: no *.jsonl under %s -- an empty scan reports clean" % base)
    worst = 0.0
    checked = 0
    for f in files:
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            up = (r.get("nexus_mind_attributes") or {}).get("uplifting") or {}
            v = up.get("raw_weighted_average")
            if v is None or up.get("stage_used") != "stage2":
                continue
            aid = r.get("id")
            if not aid or aid in seen:
                continue
            seen.add(aid)
            m = re.match(r"https?://([^/]+)", r.get("url") or "")
            if m and m.group(1).lower().replace("www.", "") == GN_DOMAIN:
                continue
            sc = up.get("scores") or {}
            if all(k in sc for k in NAMES):
                mine = wa([sc[k] for k in NAMES])
                d = abs(mine - v)
                if d > worst:
                    worst = d
                checked += 1
            vals.append(v)
    print("  cross-instrument check: my wa() vs the scorer's stored raw_weighted_average")
    print("     rows compared %d, max |delta| %.3e" % (checked, worst))
    if checked == 0:
        sys.exit("ABORT: compared 0 rows -- the check could not have failed")
    if worst > WA_EPS:
        sys.exit("ABORT: wa() disagrees with the scorer by %.4f -- the two sides would "
                 "not be on one scale" % worst)
    return vals, "production drawable: %d files, %d distinct non-GN stage2 articles" % (len(files), len(vals))


def histogram(vals):
    h = Counter()
    for v in vals:
        b = min(int(v / BIN) * BIN, 10.0 - BIN)
        h[round(b, 1)] += 1
    return h


def main(mode, base):
    print("== v8 SCORE HISTOGRAM (%s) ==" % mode)
    print("== CONTROL ==")
    if not control():
        sys.exit("ABORT: wa() control failed")
    vals, desc = (collect_corpus if mode == "corpus" else collect_production)(base)
    print(desc)
    h = histogram(vals)
    n = len(vals)
    print("\n  bin        count      share    cumul")
    cum = 0
    b = 0.0
    while b < 10.0:
        k = round(b, 1)
        c = h.get(k, 0)
        cum += c
        print("  %4.1f-%4.1f  %7d  %7.3f%%  %7.3f%%"
              % (k, k + BIN, c, 100.0 * c / n, 100.0 * cum / n))
        b += BIN
    print("\n  region shares")
    for name, lo, hi in REGIONS:
        c = sum(1 for v in vals if lo <= v < hi)
        print("    %-22s %7d  %7.3f%%" % (name, c, 100.0 * c / n))
    print("\n  n=%d  (machine-readable below)" % n)
    print("JSON " + json.dumps({"mode": mode, "n": n,
                                "bins": {("%.1f" % k): h.get(k, 0)
                                         for k in [round(i * BIN, 1) for i in range(20)]}}))


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("corpus", "production"):
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
