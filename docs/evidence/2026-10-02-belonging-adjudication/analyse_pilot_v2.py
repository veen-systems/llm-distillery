#!/usr/bin/env python3
"""Belonging pilot v2: bar items 1, 2 and 4 of PREREGISTRATION_v2.md, plus the owner spot-check list for item 3.

    python3 docs/evidence/2026-10-02-belonging-adjudication/analyse_pilot_v2.py

Reads key_v2.jsonl (here) and datasets/belonging_adjudication/pilot2/{A1,A2,B1,B2}/out.jsonl (gitignored).
Writes spot_check_v2_blind.tsv (for the owner: no verdicts) and spot_check_v2_key.tsv (opened after).
Spot-check: 6 consensus-vs-oracle disagreements (>= 2 from prod) + 4 consensus in_scope rows.
Exit 0 = items 1, 2 and 4 hold (item 3 still needs the owner), 1 = one fails, 3 = plumbing.
"""
import collections
import json
import random
import sys
from pathlib import Path

E = Path(__file__).resolve().parent
PILOT = E.parents[2] / "datasets" / "belonging_adjudication" / "pilot2"
VERDICTS = {"in_scope", "out_gift_official", "out_one_moment", "out_harm_is_story", "out_culture_topic",
            "out_event_spectated", "out_other", "cannot_judge"}


def fatal(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(3)


def load_pass(p):
    out = {}
    for part in (1, 2):
        d = PILOT / f"{p}{part}"
        f = d / "out.jsonl"
        if not f.is_file():
            fatal(f"FATAL: {f} missing")
        inp = [json.loads(l)["id"] for l in open(d / "input.jsonl", encoding="utf-8")]
        got = [json.loads(l) for l in open(f, encoding="utf-8")]
        if [r["id"] for r in got] != inp:
            fatal(f"FATAL: {f}: ids are not the input ids in input order")
        content = {json.loads(l)["id"]: json.loads(l)["content"] or "" for l in open(d / "input.jsonl", encoding="utf-8")}
        for r in got:
            if set(r) != {"id", "verdict", "quote", "reason"}:
                fatal(f"FATAL: {f}: {r['id']} keys {sorted(r)}")
            if r["verdict"] not in VERDICTS:
                fatal(f"FATAL: {f}: {r['id']} verdict {r['verdict']!r} not a category")
            if r["verdict"] != "cannot_judge" and r["quote"] and r["quote"] not in content[r["id"]]:
                print(f"   quote not verbatim in content: {p}{part} {r['id']}: {r['quote'][:60]!r}")
            if r["id"] in out:
                fatal(f"FATAL: pass {p}: {r['id']} judged twice")
            out[r["id"]] = r
    return out


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def main():
    key = {json.loads(l)["id"]: json.loads(l) for l in open(E / "key_v2.jsonl")}
    A, B = load_pass("A"), load_pass("B")
    for name, P in (("A", A), ("B", B)):
        if set(P) != set(key):
            fatal(f"FATAL: pass {name} ids differ from key")
    ok = True

    ctrl = [i for i, k in key.items() if k["stratum"] == "control"]
    if len(ctrl) != 4:
        fatal(f"FATAL: {len(ctrl)} controls in key_v2, expected 4")
    for name, P in (("A", A), ("B", B)):
        hits = sum((P[i]["verdict"] == "in_scope") == (key[i]["expected"] == "in_scope") for i in ctrl)
        print(f"1. controls, pass {name}: {hits}/4")
        for i in ctrl:
            print(f"     {key[i]['expected']:>9} expected  {P[i]['verdict']:>18}  {i}")
        ok &= hits == 4

    sample = [i for i, k in key.items() if k["stratum"] != "control"]
    a = [A[i]["verdict"] == "in_scope" for i in sample]
    b = [B[i]["verdict"] == "in_scope" for i in sample]
    agree = sum(x == y for x, y in zip(a, b)) / len(sample)
    k = kappa(a, b)
    item2 = agree >= 0.90 and k >= 0.75
    print(f"2. A vs B binary agreement {agree:.3f} (bar 0.90), kappa {k:.3f} (bar 0.75) on n={len(sample)}: "
          f"{'PASS' if item2 else 'FAIL'}")
    ok &= item2
    exact = sum(A[i]["verdict"] == B[i]["verdict"] for i in sample)
    print(f"   exact-verdict agreement (8 classes): {exact}/{len(sample)}")

    consensus = {i: A[i]["verdict"] == "in_scope" for i in sample if a[sample.index(i)] == b[sample.index(i)]}
    oracle_in = {i: key[i]["oracle_in"] for i in sample}
    disagree = [i for i in consensus if consensus[i] != oracle_in[i]]
    print(f"4. presence: consensus disagrees with the oracle on {len(disagree)} of {len(consensus)} consensus rows: "
          f"{'PASS' if disagree else 'FAIL'}")
    ok &= bool(disagree)

    print("\nPer stratum (consensus rows; NOT pooled — design weighting, PREREGISTRATION.md):")
    for s in ("near", "above", "prod"):
        ids = [i for i in sample if key[i]["stratum"] == s]
        cons = [i for i in ids if i in consensus]
        n_in = sum(consensus[i] for i in cons)
        cj = sum(A[i]["verdict"] == "cannot_judge" or B[i]["verdict"] == "cannot_judge" for i in ids)
        print(f"   {s:>5} (pool {key[ids[0]]['n_in_stratum']}): n={len(ids)}, consensus {len(cons)}, "
              f"consensus in_scope {n_in}/{len(cons)}, cannot_judge in either pass {cj}")
        if s in ("above", "prod"):
            out_cls = collections.Counter(A[i]["verdict"] for i in cons if not consensus[i])
            print(f"   {s}, consensus-out classes (pass A's class): {dict(out_cls.most_common())}")

    rng = random.Random(20261003)
    dis_prod = sorted(i for i in disagree if key[i]["stratum"] == "prod")
    dis_v1 = sorted(i for i in disagree if key[i]["stratum"] != "prod")
    rng.shuffle(dis_prod)
    rng.shuffle(dis_v1)
    spot = dis_prod[:2]
    pool = dis_v1 + dis_prod[2:]
    rng.shuffle(pool)
    spot += pool[:6 - len(spot)]
    cons_in = sorted(i for i in consensus if consensus[i] and i not in spot)
    rng.shuffle(cons_in)
    spot += cons_in[:4]
    if len(spot) < 10:
        rest = sorted(i for i in consensus if i not in spot)
        spot += rng.sample(rest, 10 - len(spot))
    rng.shuffle(spot)
    with open(E / "spot_check_v2_blind.tsv", "w") as f, open(E / "spot_check_v2_key.tsv", "w") as g:
        f.write("n\tid\n")
        g.write("n\tid\tstratum\tscore\toracle_in\tconsensus\tA_verdict\tB_verdict\tA_reason\n")
        for n, i in enumerate(spot, 1):
            f.write(f"{n}\t{i}\n")
            g.write(f"{n}\t{i}\t{key[i]['stratum']}\t{key[i]['score']}\t{key[i]['oracle_in']}\t"
                    f"{'in' if consensus[i] else 'out'}\t{A[i]['verdict']}\t{B[i]['verdict']}\t{A[i]['reason']}\n")
    print(f"\n3. owner spot-check: {len(spot)} rows -> spot_check_v2_blind.tsv ({sum(i in disagree for i in spot)} disagreements, "
          f"{sum(consensus[i] for i in spot)} consensus in_scope)")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
