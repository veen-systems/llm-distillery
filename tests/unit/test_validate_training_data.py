"""Unit tests for training/validate_training_data.py's oracle_meta coverage check.

#155 -- the oracle's non-dimensional output being dropped at split time -- survived
a whole training cycle because nothing ever inspected the produced split files. The
unit tests on the converter prove the function; this proves the ARTIFACT is checked.

Three states, because the middle one is the dangerous one: full coverage, none at
all (a legitimate pre-2026-09-08 directory, which must still validate), and PARTIAL
(a merge of old and new rows, where a consumer counting scope_verdict presence reads
the coverage gap as a real rate).
"""

import importlib.util
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "validate_training_data", _ROOT / "training" / "validate_training_data.py"
)
validate_training_data = importlib.util.module_from_spec(_SPEC)
sys.modules["validate_training_data"] = validate_training_data
_SPEC.loader.exec_module(validate_training_data)

TrainingDataValidator = validate_training_data.TrainingDataValidator

DIMS = ["a", "b", "c"]


def _row(idx, with_meta):
    row = {
        "id": f"r-{idx}",
        "title": "t",
        "content": "c",
        "url": "u",
        "labels": [5.0, 5.0, 5.0],
        "dimension_names": DIMS,
    }
    if with_meta:
        row["oracle_meta"] = {"scope_verdict": "in_scope"}
    return row


def _write_splits(tmp_path, n_with_meta, n_without):
    rows = [_row(i, True) for i in range(n_with_meta)]
    rows += [_row(1000 + i, False) for i in range(n_without)]
    # One row per split is enough; the check runs over the union.
    for name, chunk in (
        ("train.jsonl", rows[:-2] or rows),
        ("val.jsonl", rows[-2:-1]),
        ("test.jsonl", rows[-1:]),
    ):
        (tmp_path / name).write_text(
            "".join(json.dumps(r) + "\n" for r in chunk), encoding="utf-8"
        )
    return tmp_path


def _coverage_warnings(tmp_path):
    v = TrainingDataValidator(tmp_path)
    assert v.load_data()
    v.check_structural_integrity()
    return [w for w in v.warnings if "oracle_meta" in w], v


def test_full_coverage_warns_about_nothing(tmp_path):
    _write_splits(tmp_path, n_with_meta=6, n_without=0)
    warnings, v = _coverage_warnings(tmp_path)
    assert warnings == []
    assert v.stats["oracle_meta_coverage"] == (6, 6)


def test_pre_155_directory_warns_but_still_validates(tmp_path):
    """Zero coverage is legitimate for an old directory -- a warning, never an issue."""
    _write_splits(tmp_path, n_with_meta=0, n_without=6)
    warnings, v = _coverage_warnings(tmp_path)
    assert len(warnings) == 1
    assert "predate llm-distillery#155" in warnings[0]
    assert v.issues == []
    assert v.stats["oracle_meta_coverage"] == (0, 6)


def test_partial_coverage_is_called_out_as_partial(tmp_path):
    """The merge case: a rate read off these splits is a coverage artefact."""
    _write_splits(tmp_path, n_with_meta=4, n_without=2)
    warnings, v = _coverage_warnings(tmp_path)
    assert len(warnings) == 1
    assert "PARTIAL" in warnings[0]
    assert "4/6" in warnings[0]
    assert v.stats["oracle_meta_coverage"] == (4, 6)


def test_coverage_counts_every_row_not_a_sample(tmp_path):
    """The required-fields check samples the first 10; coverage must not."""
    _write_splits(tmp_path, n_with_meta=20, n_without=1)
    warnings, v = _coverage_warnings(tmp_path)
    assert v.stats["oracle_meta_coverage"] == (20, 21)
    assert len(warnings) == 1
    assert "PARTIAL" in warnings[0]
