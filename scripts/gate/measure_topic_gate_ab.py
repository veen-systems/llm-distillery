#!/usr/bin/env python3
"""LD#86 follow-up: baseline vs candidate topic gate, scored in ONE pass.

Two separate runs of the recall script cannot be compared directly — the
production cycle list grows underneath them, so the windows differ. This walks
each row once and applies both prefilters to it, which makes the before/after
exact by construction.

Run from the NexusMind repo root on sadalsuud.
"""
from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import math
import os
import sys
from collections import Counter, defaultdict

NAME, VERSION, OP, HIGH = "cultural_discovery", "v5", 4.0, 7.0


def load(path):
    root = os.getcwd()
    if root not in sys.path:
        sys.path.insert(0, root)
    spec = importlib.util.spec_from_file_location(f"pf_{abs(hash(path))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cls = next(o for o in vars(mod).values()
               if isinstance(o, type) and getattr(o, "__module__", None) == mod.__name__
               and callable(getattr(o, "apply_filter", None)))
    return cls()


ap = argparse.ArgumentParser()
ap.add_argument("--candidate", default="/tmp/cand_prefilter.py")
ap.add_argument("--cycles", type=int, default=20)
ap.add_argument("--offset", type=int, default=0)
args = ap.parse_args()

base = load(f"filters/{NAME}/{VERSION}/prefilter.py")
cand = load(args.candidate)

files = sorted(glob.glob(f"data/filtered/{NAME}/filtered_2026*.jsonl"))
if args.offset:
    files = files[:-args.offset]
files = files[-args.cycles:]

n = 0
pass_n = {"base": 0, "cand": 0}
surf = high = 0
blocked = {"base": 0, "cand": 0}
high_blocked = {"base": 0, "cand": 0}
per_lang = defaultdict(lambda: {"surf": 0, "base": 0, "cand": 0})
reasons = {"base": Counter(), "cand": Counter()}

for fp in files:
    with open(fp, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            a = r.get("nexus_mind_attributes", {}).get(NAME, {})
            raw = a.get("raw_weighted_average")
            if raw is None or str(a.get("version")) != "5.0":
                continue
            n += 1
            bp, br = base.apply_filter(dict(r))
            cp, cr = cand.apply_filter(dict(r))
            pass_n["base"] += bp
            pass_n["cand"] += cp
            if raw < OP:
                continue
            surf += 1
            lang = (r.get("language") or "??").lower()
            per_lang[lang]["surf"] += 1
            is_high = raw >= HIGH
            high += is_high
            for key, p, reason in (("base", bp, br), ("cand", cp, cr)):
                if not p:
                    blocked[key] += 1
                    high_blocked[key] += is_high
                    per_lang[lang][key] += 1
                    reasons[key][str(reason)] += 1

print(f"window: {len(files)} cycles  {files[0][-24:]} .. {files[-1][-24:]}")
print(f"scored rows {n:,}   surfacing (raw>={OP}) {surf:,}   high tier (raw>={HIGH}) {high}")
print()
print(f"{'':<26}{'BASELINE':>12}{'CANDIDATE':>12}")
print(f"{'gate pass rate (all rows)':<26}{pass_n['base']/n:>12.4f}{pass_n['cand']/n:>12.4f}")
print(f"{'surfacing blocked':<26}{blocked['base']:>12}{blocked['cand']:>12}")
print(f"{'  as % of surfacing':<26}{blocked['base']/surf:>11.1%}{blocked['cand']/surf:>12.1%}")
print(f"{'high-tier blocked':<26}{high_blocked['base']:>12}{high_blocked['cand']:>12}")
print()
print(f"{'lang':>6}{'surf':>7}{'base':>7}{'cand':>7}    base%   cand%")
for lang, d in sorted(per_lang.items(), key=lambda kv: -kv[1]["surf"]):
    if d["surf"] < 3:
        continue
    print(f"{lang:>6}{d['surf']:>7}{d['base']:>7}{d['cand']:>7}"
          f"{d['base']/d['surf']:>9.1%}{d['cand']/d['surf']:>8.1%}")


def pooled(key):
    en = per_lang.get("en", {"surf": 0, key: 0})
    ns = sum(d["surf"] for l, d in per_lang.items() if l != "en")
    nb = sum(d[key] for l, d in per_lang.items() if l != "en")
    if not (en["surf"] and ns):
        return None
    p1, p2 = en[key] / en["surf"], nb / ns
    p = (en[key] + nb) / (en["surf"] + ns)
    se = math.sqrt(p * (1 - p) * (1 / en["surf"] + 1 / ns))
    return p1, p2, (p2 / p1 if p1 else float("nan")), ((p2 - p1) / se if se else 0.0)


for key, label in (("base", "BASELINE"), ("cand", "CANDIDATE")):
    r = pooled(key)
    if r:
        print(f"\n{label}: en {r[0]:.1%}  non-en {r[1]:.1%}  ratio {r[2]:.2f}x  naive z {r[3]:.2f}")
print("\n(pooling is the framing the 08-02 comment retracted; the per-language "
      "rows above are the result. The z is naive — the 08-02 pass measured a "
      "source-clustering design effect of 1.41, which divides z by ~1.19.)")
