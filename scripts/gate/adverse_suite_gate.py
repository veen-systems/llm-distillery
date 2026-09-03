#!/usr/bin/env python3
"""Gate B-A / criterion 2, as an EXECUTABLE gate with a three-valued verdict.

Until 2026-09-03 this gate existed only as prose. `docs/HUMAN_THRIVING_V8_PLAN.md` §5 said so
itself — *"nothing enforces either form in code … the stored margins are documentation of a
check that was made, not a check"* — and on 2026-09-03 that cost a day: the nursery row was
reported FAILING criterion 1 at **4.400** against a 3.85 bar, from a k=3 mean on a row whose
own spread is sd 2.560. At k=6 it is 3.608 and at k=12 it is 2.342, both PASSES. Nobody
computed the band the gate's own rule requires.

⛔ **The third verdict is the point.** A gate that can only say PASS or FAIL will answer a
question it cannot resolve. This one returns INDETERMINATE when the margin does not clear the
band, and says how large k would have to be.

The band is computed from each row's OWN observed spread — `t * sd / sqrt(k)` — never from a
project-wide constant. A noise figure belongs to a population and a mechanism, not to a project
(`feedback-noise-floor-per-population`): the #95 0.16 batch floor is the wrong floor here, and
§1f's 0.82/2.25 are a different population again. Both are reported for context and neither is
used to decide.

Bars and assertions are read off each row. Nothing about the suite is typed into this file.

Usage:
    PYTHONPATH=. python3 scripts/gate/adverse_suite_gate.py RUNS_GLOB [--t 2.0] [--json OUT]

    # today's data, all three verdicts reachable:
    ... 'docs/evidence/2026-09-03-v8-1-gate/runs/v81b_*.jsonl'      # k=3
    ... 'docs/evidence/2026-09-03-v8-1-gate/runs/k12_v84_*.jsonl'   # k=12

Exit: 0 every row resolved and satisfied · 1 a row FAILS · 2 a row is INDETERMINATE (the gate
refuses to certify) · 3 input/plumbing error. FAIL outranks INDETERMINATE.
"""
import argparse
import glob
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

EXIT_OK, EXIT_FAIL, EXIT_INDETERMINATE, EXIT_PLUMBING = 0, 1, 2, 3


def fatal(msg):
    """Plumbing errors exit 3, NEVER 1.

    A bare `SystemExit("...")` exits 1, which is this gate's "a row FAILS" code — so a gate
    that never ran would be indistinguishable from a gate that ran and failed. Found by
    checking the exit codes on 2026-09-03, after first checking them through `| tail`, which
    swallowed them and reported 0.
    """
    print(msg, file=sys.stderr)
    raise SystemExit(EXIT_PLUMBING)


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from filters.uplifting.v7.base_scorer import BaseUpliftingScorer as S

DIMS, W = S.DIMENSION_NAMES, S.DIMENSION_WEIGHTS
GK_DIM, GK_MIN, GK_CAP = S.GATEKEEPER_DIMENSION, S.GATEKEEPER_MIN, S.GATEKEEPER_CAP

SUITES = ("datasets/adverse/uplifting.jsonl",
          "datasets/adverse/uplifting_no_regression.jsonl")
# Reported for context only. Neither decides anything here.
CONTEXT_FLOORS = {"#95 batch composition": 0.16, "§1f oracle decoder (mean/max)": (0.82, 2.25)}
ANALYSIS_FIELDS = ("human_thriving_analysis", "uplifting_analysis")


def weighted_average(scores):
    s = {d: max(0.0, min(10.0, float(scores[d]))) for d in DIMS}
    w = sum(s[d] * W[d] for d in DIMS)
    if GK_DIM is not None and s[GK_DIM] < GK_MIN and w > GK_CAP:
        w = GK_CAP
    return w


def analysis_of(row, where):
    for f in ANALYSIS_FIELDS:
        if f in row:
            return row[f]
    fatal(f"FATAL: {where}: row {row.get('id')!r} carries none of {ANALYSIS_FIELDS}. "
                     f"A run scored under a different filter config uses a different key; this "
                     f"must raise, never default to an empty analysis.")


def load_suite():
    rows = {}
    for rel in SUITES:
        p = REPO / rel
        if not p.is_file():
            fatal(f"FATAL: adverse suite missing: {rel}")
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            rows[r["id"]] = r
    if not rows:
        fatal("FATAL: adverse suite is empty — refusing to report a vacuous pass")
    return rows


def load_runs(pattern):
    paths = sorted(glob.glob(pattern))
    if not paths:
        fatal(f"FATAL: no run files matched {pattern!r}")
    runs, hashes = defaultdict(list), set()
    for p in paths:
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            a = analysis_of(r, p)
            hashes.add(a.get("prompt_hash", "__absent__"))
            runs[r["id"]].append(weighted_average({d: a[d]["score"] for d in DIMS}))
    ks = {len(v) for v in runs.values()}
    if len(ks) != 1:
        fatal(f"FATAL: ragged k across rows: {sorted(ks)}. A silent k=1 is the "
                         f"2026-08-23 defect; every row must carry the same k.")
    if len(hashes) != 1:
        fatal(f"FATAL: runs mix prompt hashes {sorted(hashes)} — that is two "
                         f"experiments, not one gate run.")
    return runs, ks.pop(), hashes.pop(), len(paths)


def judge(row, samples, t):
    """(verdict, mean, sd, band, margin, k_needed, rule) — verdict in PASS/FAIL/INDETERMINATE."""
    k = len(samples)
    mean = statistics.fmean(samples)
    sd = statistics.pstdev(samples) if k > 1 else float("nan")
    band = t * sd / math.sqrt(k) if k > 1 else float("inf")

    bar, assertion = row.get("max_acceptable_wa"), row.get("assertion")
    if bar is not None:
        rule, target, want_below = f"raw < {bar}", float(bar), True
    elif assertion and assertion.strip().startswith("raw_weighted_average > "):
        target = float(assertion.split(">")[1].strip())
        rule, want_below = f"raw > {target}", False
    elif assertion and assertion.strip().upper().startswith("DELTA"):
        return ("SKIP", mean, sd, band, float("nan"), 0,
                "DELTA assertion — needs a v7 arm this gate was not given")
    else:
        fatal(f"FATAL: row {row['id']!r} declares neither max_acceptable_wa nor a "
                         f"recognised assertion. An unjudgeable row must not read as a pass.")

    margin = abs(mean - target)
    satisfied = (mean < target) if want_below else (mean > target)
    if margin < band:
        # k to shrink the band under the observed margin, at the same t
        k_needed = math.ceil((t * sd / margin) ** 2) if margin > 0 else None
        return "INDETERMINATE", mean, sd, band, margin, k_needed, rule
    return ("PASS" if satisfied else "FAIL"), mean, sd, band, margin, k, rule


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", help="glob for the k-run score files (quote it)")
    ap.add_argument("--t", type=float, default=2.0,
                    help="band multiplier on the standard error (default 2.0, ~95%%)")
    ap.add_argument("--json", help="write the per-row table here")
    args = ap.parse_args()

    suite = load_suite()
    runs, k, phash, nfiles = load_runs(args.runs)
    scored = sorted(set(suite) & set(runs))
    if not scored:
        fatal("FATAL: no suite row appears in the runs — the gate would report a "
                         "vacuous pass over zero rows.")

    print(f"adverse-suite gate   k={k} over {nfiles} file(s)   prompt_hash {phash}   "
          f"t={args.t} (band = t·sd/√k)")
    print(f"suite {len(suite)} rows · scored {len(scored)} · not scored {len(suite)-len(scored)}")
    print(f"context floors, NOT used to decide: {CONTEXT_FLOORS}\n")

    tally, out = defaultdict(int), {}
    for rid in scored:
        row = suite[rid]
        verdict, mean, sd, band, margin, k_needed, rule = judge(row, runs[rid], args.t)
        tally[verdict] += 1
        out[rid] = dict(verdict=verdict, mean=round(mean, 4), sd=round(sd, 4),
                        band=round(band, 4), margin=None if margin != margin else round(margin, 4),
                        k_needed=k_needed, rule=rule, cls=row.get("class"),
                        title=row.get("title", "")[:70])
        note = ""
        if verdict == "INDETERMINATE":
            note = f"  margin {margin:.3f} < band {band:.3f} → need k≈{k_needed}"
        elif verdict != "SKIP":
            note = f"  margin {margin:.3f} ≥ band {band:.3f}"
        print(f"  {verdict:13} {mean:6.3f}  sd {sd:5.3f}  [{rule:>12}]{note}")
        print(f"                {row.get('title','')[:76]}")

    print(f"\n  {dict(tally)}")
    for rid in sorted(set(suite) - set(scored)):
        print(f"  NOT SCORED    {suite[rid].get('title','')[:70]}")

    if args.json:
        Path(args.json).write_text(json.dumps(
            {"k": k, "prompt_hash": phash, "t": args.t, "tally": dict(tally), "rows": out},
            indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"\nwrote {args.json}")

    if tally["FAIL"]:
        print(f"\n⛔ GATE FAILS — {tally['FAIL']} row(s) violate their own assertion.")
        return EXIT_FAIL
    if tally["INDETERMINATE"]:
        print(f"\n⚠️ GATE REFUSES A VERDICT — {tally['INDETERMINATE']} row(s) do not clear their "
              f"band at k={k}. Raise k to the largest k_needed above and re-run. "
              f"A gate that cannot resolve a row must not certify it.")
        return EXIT_INDETERMINATE
    print(f"\n✅ GATE PASSES — every scored row satisfies its assertion with margin ≥ band.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
