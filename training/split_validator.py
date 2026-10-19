"""The one validator every reader of a labelled split calls (#179, owner ruling 2026-10-19).

Called by `training/prepare_data.py` (before writing), `training/train.py`, `scripts/calibration/fit_calibration.py`
and `scripts/gate/ground_truth_gate.py`. Before it, each reader checked a different subset -- train.py only the
first row's label count, fit_calibration warned on a dimension-order mismatch and then ADOPTED the file's order
while the model head emits config order, the gate let a duplicate id silently overwrite, and nothing checked the
0-10 range. `training/validate_training_data.py` checked range but nothing called it.

RAISES, for every file, old or new:
  - a row with no id, or an id seen twice (within a file, or across the splits of one directory)
  - a label that is not a finite number in [0, 10]
  - a label count that differs from the row's dimension_names, or dimension_names that differ from the
    filter's own (order included) or from the other rows'
RAISES only for rows labelled on or after PROVENANCE_REQUIRED_FROM (by `analyzed_at`):
  - no served model, or no prompt digest
Rows before it, or with no date and no stamps, are LEGACY: they pass and their provenance is `"unknown"` -- an
explicit value, never an absent one. Every live split predates #155/#157 and is legacy.
"""
import json
import math
from pathlib import Path

PROVENANCE_REQUIRED_FROM = "2026-10-20T00:00:00Z"
PROVENANCE_KEYS = ("prompt_sha256", "prompt_hash", "served_model", "system_fingerprint", "model_digest",
                   "analyzed_by", "analyzed_at", "canary")
UNKNOWN = "unknown"
_ABSENT = "__absent__"          # ground_truth.oracle_provenance.ABSENT: stamped "this provider has none"


class SplitInvalid(ValueError):
    pass


def provenance_of(row):
    """The row's oracle provenance as a dict, or UNKNOWN. Reads a normalised `provenance` field if the split
    already carries one, else the `oracle_meta` block (prepare_data's copy of the analysis block), else the
    row's top level (score_ollama_oracle.py writes its stamps at the record root)."""
    p = row.get("provenance")
    if p == UNKNOWN or isinstance(p, dict):
        return p
    for src in (row.get("oracle_meta"), row):
        if isinstance(src, dict):
            got = {k: src[k] for k in PROVENANCE_KEYS if src.get(k) not in (None, "")}
            if any(k in got for k in ("prompt_sha256", "prompt_hash", "served_model")):
                return got
    return UNKNOWN


def _is_new(prov):
    return isinstance(prov, dict) and str(prov.get("analyzed_at", "")) >= PROVENANCE_REQUIRED_FROM


def _date_of(row):
    for src in (row.get("oracle_meta"), row):
        if isinstance(src, dict) and src.get("analyzed_at"):
            return str(src["analyzed_at"])
    return ""


def validate_rows(rows, dims=None, where="split", seen_ids=None):
    """Check one file's rows. `dims`: the filter's dimension names in config order (None: rows must agree with
    each other only). `seen_ids`: ids already taken by sibling files (mutated). Returns a summary dict."""
    if not rows:
        raise SplitInvalid(f"{where}: no rows")
    seen = set() if seen_ids is None else seen_ids
    want = list(dims) if dims is not None else None
    known = unknown = 0
    for n, row in enumerate(rows, 1):
        at = f"{where} row {n}"
        rid = row.get("id")
        if rid in (None, ""):
            raise SplitInvalid(f"{at}: no id")
        if rid in seen:
            raise SplitInvalid(f"{at}: duplicate id {rid!r}")
        seen.add(rid)
        names = row.get("dimension_names")
        if names is None:
            raise SplitInvalid(f"{at}: no dimension_names")
        if want is None:
            want = list(names)
        elif list(names) != want:
            raise SplitInvalid(f"{at}: dimension_names {list(names)} != {want}")
        labels = row.get("labels")
        if not isinstance(labels, list) or len(labels) != len(want):
            raise SplitInvalid(f"{at}: {len(labels) if isinstance(labels, list) else 'no'} labels for "
                               f"{len(want)} dimensions")
        for d, v in zip(want, labels):
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 10:
                raise SplitInvalid(f"{at}: {d} = {v!r} is not a finite score in [0, 10]")
        prov = provenance_of(row)
        date = _date_of(row)
        if date >= PROVENANCE_REQUIRED_FROM:
            p = prov if isinstance(prov, dict) else {}
            if p.get("served_model") in (None, "", _ABSENT):
                raise SplitInvalid(f"{at}: labelled {date} with no served_model (required from "
                                   f"{PROVENANCE_REQUIRED_FROM}, #179)")
            if not (p.get("prompt_sha256") or p.get("prompt_hash")):
                raise SplitInvalid(f"{at}: labelled {date} with no prompt digest (required from "
                                   f"{PROVENANCE_REQUIRED_FROM}, #179)")
        if prov == UNKNOWN:
            unknown += 1
        else:
            known += 1
    return {"rows": len(rows), "provenance_known": known, "provenance_unknown": unknown, "dims": want}


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def validate_file(path, dims=None, seen_ids=None):
    return validate_rows(read_jsonl(path), dims, where=str(path), seen_ids=seen_ids)


def validate_split_dir(split_dir, dims=None, parts=("train", "val", "test")):
    """Every present part of a split directory, with ids unique ACROSS parts (a shared id is leakage)."""
    seen, out = set(), {}
    for part in parts:
        p = Path(split_dir) / f"{part}.jsonl"
        if p.exists():
            out[part] = validate_file(p, dims, seen_ids=seen)
    if not out:
        raise SplitInvalid(f"{split_dir}: no {'/'.join(parts)}.jsonl")
    return out


def summary_line(result):
    return (f"split validator: {result['rows']} rows OK; provenance known {result['provenance_known']}, "
            f"unknown {result['provenance_unknown']}")
