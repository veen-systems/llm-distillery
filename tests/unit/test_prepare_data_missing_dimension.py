"""`training/prepare_data.py` must FAIL on a missing dimension (owner ruling 2026-10-14).

It used to default a missing dimension to 0, so a dimension renamed in the config (or in the data)
trained as a column of zeros with no warning.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from training.prepare_data import convert_to_training_format  # noqa: E402

DIMS = ["a", "b"]


def _row(analysis):
    return {"id": "r1", "title": "t", "content": "c", "x_analysis": analysis}


@pytest.mark.parametrize("analysis", [
    {"a": 3.0, "b": 4.0},                                               # flat
    {"a": {"score": 3.0}, "b": {"score": 4.0, "reasoning": "r"}},      # nested objects
    {"dimensions": {"a": 3.0, "b": 4.0}},                              # under 'dimensions'
    {"a": 0, "b": 0.0},                                                # a real zero is a score
])
def test_present_dimensions_convert(analysis):
    out = convert_to_training_format([_row(analysis)], "x_analysis", DIMS)
    assert [float(v) for v in out[0]["labels"]] == [float(analysis.get("dimensions", analysis)[d]["score"])
                                                    if isinstance(analysis.get("dimensions", analysis)[d], dict)
                                                    else float(analysis.get("dimensions", analysis)[d]) for d in DIMS]


@pytest.mark.parametrize("analysis", [
    {"a": 3.0},                       # b absent (a renamed dimension)
    {"a": 3.0, "b_renamed": 4.0},
    {"a": 3.0, "b": {"reasoning": "no score"}},
    {"a": 3.0, "b": None},
    {"a": 3.0, "b": {"score": None}},
])
def test_missing_dimension_raises_and_names_it(analysis):
    with pytest.raises(ValueError, match=r"'b'.*'x_analysis'"):
        convert_to_training_format([_row(analysis)], "x_analysis", DIMS)


def test_cli_exits_nonzero_on_a_renamed_dimension(tmp_path):
    """End to end: the run fails and writes no train.jsonl."""
    dims = ["intergenerational_bonds", "community_fabric", "reciprocal_care", "rootedness",
            "purpose_beyond_self", "slow_presence"]
    labels = tmp_path / "labels.jsonl"
    with open(labels, "w", encoding="utf-8") as f:
        for i in range(30):
            scores = {d: float(i % 10) for d in dims}
            scores["slow_presence_renamed"] = scores.pop("slow_presence")
            f.write(json.dumps({"id": f"a{i}", "title": "t", "content": "c",
                                "belonging_analysis": scores}) + "\n")
    out = tmp_path / "out"
    r = subprocess.run([sys.executable, str(REPO / "training" / "prepare_data.py"), "--filter",
                        str(REPO / "filters" / "belonging" / "v3"), "--input", str(labels),
                        "--output-dir", str(out)],
                       capture_output=True, text=True, cwd=REPO, timeout=120,
                       env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"})
    assert r.returncode != 0, r.stdout[-500:]
    assert "slow_presence" in r.stderr
    assert not (out / "train.jsonl").exists()
