#!/usr/bin/env python3
"""F4 vs F5 on the 12 EXP-029 flips, and bar items 2 and 3 of PREREGISTRATION.md.

Scores are computed with `adverse_suite_gate.py`'s own `weighted_average`, so the two halves of
this test read raw the same way. Exit 0 bar met, 1 not met, 3 plumbing.
"""
import collections
import glob
import json
import math
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "gate"))
import adverse_suite_gate as G  # noqa: E402

E = Path(__file__).resolve().parent
OP = 4.5
TARGETS = {
    "climate_solutions_the_cool_down_8094f43914ed": "Houston AC law",
    "central_asian_24_kg_8351094c86fd": "Kyrgyz water systems",
    "indonesian_mongabay_id_4a03fd01cc36": "Mentawai petition",
    "south_asian_indian_express_9f206d53ba0f": "Madras HC permission",
}


def load(arm, k_expected):
    paths = sorted(glob.glob(str(E / "runs" / f"{arm}_*.jsonl")))
    if len(paths) != k_expected:
        G.fatal(f"FATAL: {arm}: {len(paths)} run files, expected {k_expected}")
    wa, verdict, hashes, titles = (collections.defaultdict(list), collections.defaultdict(list),
                                   set(), {})
    for p in paths:
        seen = set()
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            if "error" in r and not any(f in r for f in G.ANALYSIS_FIELDS):
                continue  # a failed attempt; the resume wrote the scored row after it
            if r["id"] in seen:
                G.fatal(f"FATAL: {p}: {r['id']} scored twice in one run")
            seen.add(r["id"])
            a = G.analysis_of(r, p)
            hashes.add(a.get("prompt_hash"))
            wa[r["id"]].append(G.weighted_average({d: a[d]["score"] for d in G.DIMS}))
            verdict[r["id"]].append(a.get("scope_verdict"))
            titles[r["id"]] = r.get("title", "")
    if len(hashes) != 1:
        G.fatal(f"FATAL: {arm} mixes prompt hashes {sorted(hashes)}")
    ks = {len(v) for v in wa.values()}
    if ks != {k_expected} or len(wa) != 12:
        G.fatal(f"FATAL: {arm}: rows={len(wa)} k={sorted(ks)} — expected 12 rows at k={k_expected}")
    return wa, verdict, hashes.pop(), titles


def stats(xs):
    m, sd = statistics.fmean(xs), statistics.pstdev(xs)
    return m, sd, 2 * sd / math.sqrt(len(xs))


def main():
    f4, v4, h4, titles = load("F4", 6)
    f5, v5, h5, _ = load("F5", 6)
    print(f"F4 prompt {h4}   F5 prompt {h5}   k=6   op-point {OP}\n")
    print(f"{'':2}{'F4 mean±sd':>14} {'F5 mean±sd':>14}  F5 in_scope  title")
    credited = 0
    for i in sorted(f4, key=lambda i: (i not in TARGETS, i)):
        m4, s4, b4 = stats(f4[i])
        m5, s5, b5 = stats(f5[i])
        ins5 = sum(v == "in_scope" for v in v5[i])
        tag = "T " if i in TARGETS else "  "
        print(f"{tag}{m4:8.3f}±{s4:5.3f} {m5:8.3f}±{s5:5.3f}  {ins5}/6        {titles[i][:60]}")
        if i in TARGETS:
            below5 = m5 < OP and (OP - m5) >= b5          # bar item 2
            above4 = m4 > OP or (OP - m4) < b4            # bar item 3: not already clearly below
            ok = below5 and above4
            credited += ok
            print(f"    -> {TARGETS[i]}: F5 below with margin {'yes' if below5 else 'NO'}"
                  f" (band {b5:.3f}); F4 at/over op-point or within band {'yes' if above4 else 'NO'}"
                  f" -> {'CREDITED' if ok else 'not credited'}")
    met = credited >= 3
    print(f"\nTargets credited: {credited} of {len(TARGETS)} (bar: at least 3) -> "
          f"{'MET' if met else 'NOT MET'}")
    return 0 if met else 1


if __name__ == "__main__":
    sys.exit(main())
