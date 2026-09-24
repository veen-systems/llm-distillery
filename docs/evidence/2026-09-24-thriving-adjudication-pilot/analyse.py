#!/usr/bin/env python3
"""Pilot bar items 1, 2 and 4 of PREREGISTRATION.md, plus the owner spot-check list for item 3.

Exit 0 = items 1, 2 and 4 hold (item 3 still needs the owner), 1 = one fails, 3 = plumbing.
"""
import json
import random
import sys
from pathlib import Path

E = Path(__file__).resolve().parent
VERDICTS = {"in_scope", "out_of_scope", "harm_is_subject", "response_to_harm", "no_person_benefits"}


def fatal(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(3)


def load_pass(p):
    out = {}
    for part in (1, 2):
        f = E / f"out_{p}{part}.jsonl"
        if not f.is_file():
            fatal(f"FATAL: {f.name} missing")
        for line in open(f, encoding="utf-8"):
            r = json.loads(line)
            if r["verdict"] not in VERDICTS:
                fatal(f"FATAL: {f.name}: {r['id']} verdict {r['verdict']!r} not a category")
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
    key = {json.loads(l)["id"]: json.loads(l) for l in open(E / "key.jsonl")}
    A, B = load_pass("A"), load_pass("B")
    for name, P in (("A", A), ("B", B)):
        if set(P) != set(key):
            fatal(f"FATAL: pass {name} ids differ from key: missing {sorted(set(key) - set(P))[:3]}, "
                  f"extra {sorted(set(P) - set(key))[:3]}")
    ok = True

    ctrl = [i for i, k in key.items() if k["stratum"] == "control"]
    for name, P in (("A", A), ("B", B)):
        hits = sum((P[i]["verdict"] == "in_scope") == (key[i]["expected"] == "in_scope") for i in ctrl)
        print(f"1. controls, pass {name}: {hits}/4")
        for i in ctrl:
            print(f"     {key[i]['expected']:>12} expected  {P[i]['verdict']:>18}  {i}")
        ok &= hits == 4

    rows = [i for i, k in key.items() if k["stratum"] != "control"]
    a = [A[i]["verdict"] == "in_scope" for i in rows]
    b = [B[i]["verdict"] == "in_scope" for i in rows]
    agree = sum(x == y for x, y in zip(a, b)) / len(rows)
    k = kappa(a, b)
    print(f"2. A vs B binary agreement {agree:.3f} (bar >= 0.90), kappa {k:.3f} (bar >= 0.75), n={len(rows)}")
    ok &= agree >= 0.90 and k >= 0.75

    cons = {i: A[i]["verdict"] == "in_scope" for i in rows if (A[i]["verdict"] == "in_scope") == (B[i]["verdict"] == "in_scope")}
    dis = []
    for s in ("near", "above"):
        ids = [i for i in cons if key[i]["stratum"] == s]
        d = [i for i in ids if cons[i] != (key[i]["oracle_verdict"] == "in_scope")]
        dis += d
        print(f"4. stratum {s}: consensus on {len(ids)}, disagrees with oracle on {len(d)}"
              f" ({(len(d) / len(ids) if ids else 0):.1%}); in->out {sum(not cons[i] for i in d)},"
              f" out->in {sum(cons[i] for i in d)}")
    ok &= len(dis) >= 1

    titles = {}
    for p in E.glob("input_A*.jsonl"):
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            titles[r["id"]] = r.get("title") or ""
    rng = random.Random(20260924)
    spot = rng.sample(sorted(dis), min(10, len(dis)))   # random, not the alphabetically-first sources
    rest = sorted(set(cons) - set(spot))
    spot += rng.sample(rest, max(0, 10 - len(spot)))
    with open(E / "spot_check.md", "w", encoding="utf-8") as f:
        f.write("# Owner spot-check — agree or disagree with the consensus on each row\n\n")
        for n, i in enumerate(spot, 1):
            f.write(f"## {n}. {titles.get(i, '')}\n\n`{i}`\n\n- oracle: **{key[i]['oracle_verdict']}** "
                    f"(label {key[i]['oracle_mean']:.2f})\n- consensus: **{'in_scope' if cons[i] else A[i]['verdict']}**\n"
                    f"- A: {A[i]['verdict']} — \"{A[i]['quote']}\" — {A[i]['reason']}\n"
                    f"- B: {B[i]['verdict']} — \"{B[i]['quote']}\" — {B[i]['reason']}\n\n")
    print(f"3. owner spot-check list written: spot_check.md ({len(spot)} rows, "
          f"{min(len(dis), 10)} from consensus-vs-oracle disagreements)")
    print("\nITEMS 1, 2, 4:", "HOLD" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
