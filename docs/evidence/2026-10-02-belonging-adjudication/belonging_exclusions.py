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
    ("held-out set 2 2026-10-08", ROOT / "datasets" / "belonging_heldout2" / "heldout2_rows.jsonl", _jsonl_ids),
    ("held-out set 3 2026-10-08", ROOT / "datasets" / "belonging_heldout3" / "heldout3_rows.jsonl", _jsonl_ids),
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


def assert_disjoint(ids, purpose):
    """For a TRAINING build or any draw: raises on any overlap with every source above."""
    hit = set(ids) & excluded_ids()
    if hit:
        raise SystemExit(f"{purpose}: {len(hit)} ids are excluded (pilot/exemplar/test/calibration/held-out), e.g. {sorted(hit)[:3]}")


# v1's train/val/test ids (copied from b650 to the gitignored datasets/belonging_v1_adj/). The phase-5 build DRAWS
# from them, so they are not in SOURCES; a fresh measurement or harvest draw must avoid them (review 2026-10-03:
# this lived only in an uncommitted, hand-built exclude file).
V1_SPLITS = [ROOT / "datasets" / "belonging_v1_adj" / f"{s}.jsonl" for s in ("train", "val", "test")]


def assert_fresh_draw(ids, purpose):
    """For a new held-out or harvest draw: everything assert_disjoint checks, plus v1's splits. A missing split raises."""
    assert_disjoint(ids, purpose)
    v1 = set()
    for p in V1_SPLITS:
        if not p.exists():
            raise SystemExit(f"v1 split missing: {p}; refusing to draw without it")
        v1 |= _jsonl_ids(p)
    hit = set(ids) & v1
    if hit:
        raise SystemExit(f"{purpose}: {len(hit)} ids are in v1's train/val/test splits, e.g. {sorted(hit)[:3]}")


def assert_is_source(ids, name):
    """For a source checking ITSELF (the held-out set's own check): ids must BE that source exactly and be disjoint
    from every other. Replaces the old `except_sources` bypass, which any copied caller would have inherited
    (review 2026-10-03)."""
    srcs = load()
    if name not in srcs:
        raise SystemExit(f"unknown exclusion source: {name!r}")
    if set(ids) != srcs[name]:
        raise SystemExit(f"{name}: ids are not exactly this source ({len(set(ids) ^ srcs[name])} differ)")
    hit = set(ids) & set().union(*(v for k, v in srcs.items() if k != name))
    if hit:
        raise SystemExit(f"{name}: {len(hit)} ids overlap another exclusion source, e.g. {sorted(hit)[:3]}")


if __name__ == "__main__":
    srcs = load()
    for name, ids in srcs.items():
        print(f"{len(ids):6d}  {name}")
    print(f"{len(set().union(*srcs.values())):6d}  distinct excluded ids")
