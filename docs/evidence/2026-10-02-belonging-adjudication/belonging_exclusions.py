#!/usr/bin/env python3
"""Belonging: every article id that must NEVER enter a training draw or a fresh evaluation set.

Mechanizes the exclusion rule that was prose-only (review 2026-10-02: "the phase-4 builder must RAISE on overlap").
Phase 3/4/5 builders import it:

    from belonging_exclusions import assert_disjoint
    assert_disjoint(candidate_ids, purpose="phase-4 harvest")     # raises SystemExit on any overlap

    python3 docs/evidence/2026-10-02-belonging-adjudication/belonging_exclusions.py   # prints the sources and counts

NOT covered here: v1's training splits (b650 `~/llm-distillery/datasets/training/belonging_v1/`). Phase 3 draws
FROM them, and the phase-4 harvest must exclude them separately on b650.

A missing source file RAISES (it is never treated as empty): a draw made on a machine without the gitignored
files must fail, not silently exclude less.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EV = ROOT / "docs" / "evidence"


def _jsonl_ids(path, field="id"):
    return {json.loads(line)[field] for line in open(path) if line.strip()}


def _tsv_col(path, col):
    rows = list(open(path))[1:]
    return {r.rstrip("\n").split("\t")[col] for r in rows if r.strip()}


# (name, path, loader). Every id set that has been read, judged, ruled on, or written about.
SOURCES = [
    ("v2 test set", EV / "2026-10-01-belonging-v2-test-set" / "test_set.jsonl", _jsonl_ids),
    ("150-row held-out production sample", ROOT / "datasets" / "belonging_v2_test" / "prod_heldout_20261001.jsonl", _jsonl_ids),
    ("49 probe rows", ROOT / "datasets" / "belonging_v2_test" / "oracle_probe_49.jsonl", _jsonl_ids),
    ("200-row reader sample", EV / "2026-10-02-belonging-reader-snapshot" / "reader_sample_200.tsv", lambda p: _tsv_col(p, 2)),
    ("exemplars v1", HERE / "exemplars.tsv", lambda p: _tsv_col(p, 2)),
    ("exemplars v2", HERE / "exemplars_v2.tsv", lambda p: _tsv_col(p, 2)),
    ("pilot 1 key", HERE / "key.jsonl", _jsonl_ids),
    ("pilot v2 key", HERE / "key_v2.jsonl", _jsonl_ids),
    ("pilot v3 key", HERE / "key_v3.jsonl", _jsonl_ids),
    ("calibration set", HERE / "calib_key.jsonl", _jsonl_ids),
    ("held-out screen set 2026-10-03", ROOT / "datasets" / "belonging_heldout" / "heldout_rows.jsonl", _jsonl_ids),
]


def load():
    out = {}
    for name, path, loader in SOURCES:
        if not path.exists():
            raise SystemExit(f"exclusion source missing: {name} ({path}); refusing to draw without it")
        ids = loader(path)
        if not ids:
            raise SystemExit(f"exclusion source empty: {name} ({path})")
        out[name] = ids
    return out


def excluded_ids():
    return set().union(*load().values())


def assert_disjoint(ids, purpose, except_sources=()):
    """except_sources: source names NOT checked (only the held-out set's own check of itself uses it)."""
    srcs = load()
    unknown = set(except_sources) - set(srcs)
    if unknown:
        raise SystemExit(f"unknown exclusion source(s): {sorted(unknown)}")
    hit = set(ids) & set().union(*(v for k, v in srcs.items() if k not in except_sources))
    if hit:
        raise SystemExit(f"{purpose}: {len(hit)} ids are excluded (pilot/exemplar/test/calibration), e.g. {sorted(hit)[:3]}")


if __name__ == "__main__":
    srcs = load()
    for name, ids in srcs.items():
        print(f"{len(ids):6d}  {name}")
    print(f"{len(set().union(*srcs.values())):6d}  distinct excluded ids")
