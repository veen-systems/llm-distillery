"""`training/prepare_data.py` must FAIL when it would write 0 examples (2026-10-12).

The 2026-09-01 gotcha: labels written under one package's `filter.name` and a `--filter`
naming another select an analysis field no row carries; every row was skipped and the script
printed "TRAINING DATA PREPARATION COMPLETE" over three empty files, exit 0.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "training" / "prepare_data.py"
FILTER = REPO / "filters" / "belonging" / "v3"
DIMS = ["intergenerational_bonds", "community_fabric", "reciprocal_care", "rootedness",
        "purpose_beyond_self", "slow_presence"]


def _run(tmp_path, field):
    labels = tmp_path / "labels.jsonl"
    with open(labels, "w", encoding="utf-8") as f:
        for i in range(30):
            f.write(json.dumps({"id": f"a{i}", "title": "t", "content": "c",
                                field: {d: float(i % 10) for d in DIMS}}) + "\n")
    out = tmp_path / "out"
    r = subprocess.run([sys.executable, str(SCRIPT), "--filter", str(FILTER), "--input",
                        str(labels), "--output-dir", str(out)],
                       capture_output=True, text=True, cwd=REPO, timeout=120,
                       env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"})
    # ^ NO PYTHONPATH on purpose: this is the call CLAUDE.md and the RUNBOOK document
    return r, out


def test_a_mismatched_analysis_field_fails_and_writes_nothing(tmp_path):
    r, out = _run(tmp_path, "uplifting_analysis")
    assert r.returncode == 1, r.stdout[-500:]
    assert "FATAL: 0 training examples from 30 labels" in r.stderr
    assert "uplifting_analysis" in r.stderr              # names what the rows DO carry
    assert "PREPARATION COMPLETE" not in r.stdout
    assert not (out / "train.jsonl").exists()


def test_the_matching_field_still_writes_all_three_splits(tmp_path):
    """The control: the guard must not fire on a real run."""
    r, out = _run(tmp_path, "belonging_analysis")
    assert r.returncode == 0, r.stderr[-500:]
    assert all((out / f"{s}.jsonl").stat().st_size > 0 for s in ("train", "val", "test"))
