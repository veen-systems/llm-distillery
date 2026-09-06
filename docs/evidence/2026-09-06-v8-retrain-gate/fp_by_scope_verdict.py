#!/usr/bin/env python3
"""What KIND of false positive is each one? — the harm-weighted view of precision.

⛔ WHY THIS EXISTS. The deploy gate reports one FP count, and it treats every false
positive as equal. They are not. Under this lens an article that is merely adjacent
costs a reader almost nothing (ADR-015: lens overlap is correct), while an article
whose occasion is a crime surfacing in a "human thriving" tab is a category error
that damages trust. Optimising the plain count therefore optimises the wrong object.

The oracle already emits the distinction: `scope_verdict` is the first key of its
JSON output and is present on all 6,586 labelled rows. So this is a MEASUREMENT of
the label set, not an interpretation of the scores.

⚠️ WHAT IT DOES NOT SETTLE. `scope_verdict` is an oracle label, not truth. And the
counts are over 17 and 20 surfaced articles — "1 category error versus 1" compares
two single articles, not two rates. Read the direction, not a percentage.

Usage:
    python3 docs/evidence/2026-09-06-v8-retrain-gate/fp_by_scope_verdict.py \
        --labels datasets/scored/human_thriving_v8/labels_v84_merged.jsonl \
        --dump epoch5=<path>/scores_calibrated.jsonl \
        --dump epoch4=<path>/scores_calibrated.jsonl

Dumps are gitignored and live on b650-gpu; the manifest in this directory names
their paths and sha256.
"""
from __future__ import annotations

# design-weights: NOT READ, and no rate published here is a population estimate.
# The 660 test rows are a 25.1x design-weighted draw (inclusion_probability lives in
# datasets/scored/human_thriving_v8/corpus.jsonl, not in the split). Every figure
# below is a COUNT over surfaced articles plus a share of that count, which is a
# property of this split. The comparison between the two checkpoints is PAIRED on
# identical rows, so weights would move both arms together -- but that is an
# argument, not a measurement, and no weighted arm has been run. Production
# precision must be measured from production output, not from here.

# ⛔ THE BLOCK ABOVE SAT INSIDE THE MODULE DOCSTRING when this file was
# first written, and check_claim_shapes.py correctly refused it: `_declaration`
# reads COMMENT TOKENS, because a regex over file text once exempted a
# declaration written inside a string literal. A declaration that is not a
# comment is not a declaration -- the file documenting that trap is the file
# that caught this one.


import argparse
import collections
import json
import sys

# base_scorer.py DIMENSION_WEIGHTS. Kept here rather than imported so the script
# runs without the package on PATH; test_filter_package_consistency pins the pair.
WEIGHTS = {
    "human_wellbeing_impact": 0.30,
    "social_cohesion_impact": 0.20,
    "justice_rights_impact": 0.15,
    "evidence_level": 0.10,
    "benefit_distribution": 0.10,
    "change_durability": 0.15,
}
DIMS = list(WEIGHTS)
OP_POINT = 4.5
GATEKEEPER_CAP = 3.0

# Ordered most-harmful first. `in_scope` is LAST and is the point of the exercise:
# an `in_scope` false positive is the oracle and the student disagreeing about where
# a thriving story sits, not junk reaching a reader.
VERDICT_ORDER = ["harm_is_subject", "response_to_harm", "no_person_benefits",
                 "out_of_scope", "in_scope"]
OFF_LENS = {"harm_is_subject", "response_to_harm", "no_person_benefits", "out_of_scope"}


def as_number(v):
    """⚠️ labels_v84_merged.jsonl carries TWO SCHEMAS in one file: 6,130 rows with
    scalar dimensions and 456 (the v8.4 re-labelled ones) with {"score": x}. A naive
    `v * weight` raises; a naive `.get(dim, 0)` would silently score those rows ZERO,
    which is the more dangerous failure because it looks like data."""
    if isinstance(v, dict):
        for key in ("score", "value", "mean"):
            if key in v:
                return float(v[key])
        raise ValueError(f"dimension object carries no numeric field: {v!r}")
    return float(v)


def weighted_average(scores):
    """The scoring path's arithmetic: weighted mean, then the evidence gatekeeper."""
    vals = {d: as_number(scores[d]) for d in DIMS}
    wa = sum(vals[d] * WEIGHTS[d] for d in DIMS)
    if vals["evidence_level"] < 3:
        return min(GATEKEEPER_CAP, wa)
    return wa


def load_labels(path):
    truth, verdict = {}, {}
    for line in open(path, encoding="utf-8"):
        row = json.loads(line)
        analysis = row["human_thriving_analysis"]
        truth[row["id"]] = weighted_average(analysis)
        verdict[row["id"]] = analysis.get("scope_verdict")
    if not truth:
        raise SystemExit(f"no labels read from {path} — refusing to report on nothing")
    return truth, verdict


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--dump", action="append", required=True,
                    metavar="NAME=PATH", help="repeatable; NAME=path/to/scores_calibrated.jsonl")
    args = ap.parse_args(argv if argv is not None else sys.argv[1:])

    truth, verdict = load_labels(args.labels)
    print(f"labels: {len(truth)} rows from {args.labels}")
    missing_verdict = sum(1 for v in verdict.values() if v is None)
    if missing_verdict:
        print(f"⚠️ {missing_verdict} label rows carry no scope_verdict")

    for spec in args.dump:
        name, _, path = spec.partition("=")
        pred = {}
        for line in open(path, encoding="utf-8"):
            row = json.loads(line)
            pred[row["id"]] = weighted_average(row["scores"])
        rows = [i for i in pred if i in truth]
        if len(rows) != len(pred):
            raise SystemExit(
                f"{name}: {len(pred) - len(rows)} scored rows have no label — a partial "
                f"join would silently shrink the surfaced set")

        tp = [i for i in rows if pred[i] >= OP_POINT and truth[i] >= OP_POINT]
        fp = [i for i in rows if pred[i] >= OP_POINT and truth[i] < OP_POINT]
        surfaced = len(tp) + len(fp)
        counts = collections.Counter(verdict.get(i) for i in fp)
        off_lens = sum(counts[v] for v in OFF_LENS)
        category_errors = counts["harm_is_subject"]

        print(f"\n=== {name} ===  joined {len(rows)} rows")
        print(f"  surfaced {surfaced}   TP {len(tp)}   FP {len(fp)}")
        print("  false positives by the oracle's own scope_verdict:")
        for v in VERDICT_ORDER:
            if counts[v]:
                flag = "  <- category error" if v == "harm_is_subject" else (
                    "  <- NOT junk: the oracle calls it on-lens" if v == "in_scope" else "")
            else:
                flag = ""
            print(f"      {v:20s} {counts[v]}{flag}")
        print(f"  plain precision      {len(tp)}/{surfaced} = {len(tp)/surfaced:.3f}")
        print(f"  off-lens precision   {surfaced - off_lens}/{surfaced} = "
              f"{(surfaced - off_lens)/surfaced:.3f}   (excludes in_scope boundary cases)")
        print(f"  category errors      {category_errors} of {surfaced}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
