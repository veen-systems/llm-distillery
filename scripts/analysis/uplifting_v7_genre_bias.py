#!/usr/bin/env python3
"""Does the uplifting v7 ORACLE rate research artefacts as on-lens?

Motivation (2026-08-20): production surfaces primary literature into the Thriving
lens at a HIGHER rate than it appears in the corpus, while `belonging` and
`solutions` deplete it. The question this script answers is whether that is the
student drifting from its labels, or the labels themselves.

It reads the held-out oracle test split and re-derives the weighted average with
the deployed DIMENSION_WEIGHTS, so nothing here depends on the model. A source
group is taken from the row `id` prefix, which is the collector's source name --
the same namespace production stamps as `source` -- NOT a hand-built list of
articles.

CAVEAT, stated because it is the weak point: the academic/non-academic SPLIT is
still a pattern list over source names (ACADEMIC_MARKERS below). NexusMind's
`metadata.primary_literature.detected` stamp is the better instrument but is not
present on training rows. On production rows the two disagree -- this list is the
looser of the two (it includes `science_*` / `healthcare_*` source GROUPS, which
contain science journalism, not only papers). Treat the magnitude as approximate
and the DIRECTION as the finding.

Usage:
    PYTHONPATH=. python3 scripts/analysis/uplifting_v7_genre_bias.py
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

DEFAULT_SPLIT = Path("datasets/training/uplifting_v7/test.jsonl")

# Mirrors filters/uplifting/v7/base_scorer.py DIMENSION_WEIGHTS. Asserted below.
WEIGHTS = {
    "human_wellbeing_impact": 0.30,
    "social_cohesion_impact": 0.20,
    "justice_rights_impact": 0.15,
    "evidence_level": 0.10,
    "benefit_distribution": 0.10,
    "change_durability": 0.15,
}

ACADEMIC_MARKERS = (
    "pubmed", "arxiv", "mdpi", "medrxiv", "biorxiv", "chemrxiv",
    "bioengineer", "bioinformatics_", "science_", "healthcare_", "biotech_",
)


def _assert_weights_match_deployed() -> None:
    """Fail loudly if the deployed weights have moved away from this copy."""
    src = Path("filters/uplifting/v7/base_scorer.py").read_text(encoding="utf-8")
    for dim, w in WEIGHTS.items():
        needle = f'"{dim}": {w:.2f}'
        if needle not in src:
            raise SystemExit(
                f"weight drift: base_scorer.py does not contain {needle!r}. "
                "Update WEIGHTS in this script rather than reporting a stale number."
            )


def load(split: Path):
    rows = []
    with split.open(encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            labels = dict(zip(d["dimension_names"], d["labels"]))
            missing = set(WEIGHTS) - set(labels)
            if missing:
                raise SystemExit(f"row {d['id']} is missing dimensions: {sorted(missing)}")
            wa = sum(WEIGHTS[k] * labels[k] for k in WEIGHTS)
            source = d["id"].rsplit("_", 1)[0]
            rows.append({
                "wa": wa,
                "source": source,
                "academic": any(m in source for m in ACADEMIC_MARKERS),
                "labels": labels,
                "title": d.get("title", ""),
            })
    if not rows:
        raise SystemExit(f"{split} is empty")
    return rows


def permutation_p(rows, truth_cut: float, n_iter: int, seed: int) -> tuple[float, float]:
    flags = [r["wa"] >= truth_cut for r in rows]
    k = sum(1 for r in rows if r["academic"])
    if k == 0 or k == len(rows):
        raise SystemExit("degenerate split: one arm is empty, the test cannot say yes")
    a = sum(1 for r in rows if r["academic"] and r["wa"] >= truth_cut) / k
    b = sum(1 for r in rows if not r["academic"] and r["wa"] >= truth_cut) / (len(rows) - k)
    observed = a - b
    rng = random.Random(seed)
    hits = 0
    for _ in range(n_iter):
        shuffled = rng.sample(flags, k)
        diff = sum(shuffled) / k - (sum(flags) - sum(shuffled)) / (len(flags) - k)
        if diff >= observed:
            hits += 1
    return observed, hits / n_iter


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", type=Path, default=DEFAULT_SPLIT)
    ap.add_argument("--truth-cut", type=float, default=4.0,
                    help="oracle weighted average at or above which a row is on-lens")
    ap.add_argument("--iterations", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--min-source-n", type=int, default=8)
    args = ap.parse_args()

    _assert_weights_match_deployed()
    rows = load(args.split)
    cut = args.truth_cut

    n = len(rows)
    on = sum(1 for r in rows if r["wa"] >= cut)
    print(f"split: {args.split}  rows={n}  oracle >= {cut}: {on} ({100*on/n:.1f}%)")

    acad = [r for r in rows if r["academic"]]
    other = [r for r in rows if not r["academic"]]
    oa = sum(1 for r in acad if r["wa"] >= cut)
    ob = sum(1 for r in other if r["wa"] >= cut)
    print(f"\n  academic-source rows  {oa:3d}/{len(acad):3d} = {100*oa/len(acad):5.1f}% on-lens")
    print(f"  everything else       {ob:3d}/{len(other):3d} = {100*ob/len(other):5.1f}% on-lens")

    observed, p = permutation_p(rows, cut, args.iterations, args.seed)
    print(f"  difference {observed:+.3f}   permutation p = {p:.4f} "
          f"(one-sided, N={args.iterations}, seed={args.seed})")

    print("\n  mean ORACLE score per dimension (academic vs other):")
    for dim, w in WEIGHTS.items():
        ma = sum(r["labels"][dim] for r in acad) / len(acad)
        mb = sum(r["labels"][dim] for r in other) / len(other)
        print(f"    {dim:<26} w={w:.2f}  acad {ma:4.2f}   other {mb:4.2f}   delta {ma-mb:+.2f}")

    by = defaultdict(lambda: [0, 0])
    for r in rows:
        by[r["source"]][0] += 1
        by[r["source"]][1] += r["wa"] >= cut
    big = sorted(((s, c, k) for s, (c, k) in by.items() if c >= args.min_source_n),
                 key=lambda x: -x[2] / x[1])
    print(f"\n  on-lens rate by source (n >= {args.min_source_n}):")
    for s, c, k in big:
        print(f"    {100*k/c:5.1f}%  {k:3d}/{c:3d}  {s}")


if __name__ == "__main__":
    main()
