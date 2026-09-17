"""Every ADR-021 gate artifact says which DEVICE produced its numbers (llm-distillery#104).

`EXP-041` measured the device at all six live op-points: `uplifting v7` disagrees on 2 rows of 660
between CPU and CUDA, both false-positive side, moving specificity 0.9687 -> 0.9642. Small — but
before this check the tree mixed four `cpu` gates, one CUDA gate and three that said nothing, and a
comparison that does not know which side it is on is not small.

⚠️ These tests check that a gate ANSWERS, never that the answer is true.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CHECKER = REPO / "scripts" / "verification" / "check_gate_device_stamp.py"


def run(root: Path):
    p = subprocess.run([sys.executable, str(CHECKER), "--root", str(root)],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def write_gate(root: Path, gate: dict, name: str = "f/v1"):
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "ground_truth_gate.json").write_text(json.dumps(gate), encoding="utf-8")


def test_the_real_tree_passes():
    rc, out = run(REPO / "filters")
    assert rc == 0, out
    assert "PASS gate-device-stamp" in out


def test_the_real_tree_is_enumerated_by_glob_not_by_a_list():
    """⛔ The population was wrong twice before this test existed: I counted the six LIVE filters
    and the tree holds eight gates — `investment_risk v6` and `solutions v4` are also gates."""
    rc, out = run(REPO / "filters")
    on_disk = sorted((REPO / "filters").glob("**/ground_truth_gate.json"))
    assert rc == 0, out
    assert f"{len(on_disk)} gate(s) examined" in out, out
    for g in on_disk:
        assert str(g.relative_to(REPO)) in out, f"{g} exists and the census does not name it"


def test_a_gate_with_no_provenance_fails(tmp_path):
    write_gate(tmp_path, {"threshold": 4.0, "models": {}})
    rc, out = run(tmp_path)
    assert rc == 1
    assert "no `provenance` object" in out


def test_a_provenance_without_device_fails(tmp_path):
    write_gate(tmp_path, {"provenance": {"box": "somewhere"}})
    rc, out = run(tmp_path)
    assert rc == 1
    assert "`provenance.device` is missing or empty" in out


def test_an_empty_device_string_fails(tmp_path):
    write_gate(tmp_path, {"provenance": {"device": "   "}})
    assert run(tmp_path)[0] == 1


def test_unrecorded_without_a_reason_fails(tmp_path):
    """The honest answer costs a sentence; the dishonest one must not be cheaper."""
    write_gate(tmp_path, {"provenance": {"device": "UNRECORDED"}})
    rc, out = run(tmp_path)
    assert rc == 1
    assert "device_unrecorded_why" in out


def test_unrecorded_with_a_reason_passes(tmp_path):
    write_gate(tmp_path, {"provenance": {"device": "UNRECORDED",
                                         "device_unrecorded_why": "predates #104, cannot be established"}})
    rc, out = run(tmp_path)
    assert rc == 0, out


def test_a_recorded_device_passes(tmp_path):
    write_gate(tmp_path, {"provenance": {"device": "cpu"}})
    assert run(tmp_path)[0] == 0


def test_mixed_devices_are_flagged_even_though_every_gate_answers(tmp_path):
    """⛔ The mixture is the finding. A tree where all gates answer can still be a tree whose
    ADR-021 comparisons cross hardware paths."""
    write_gate(tmp_path, {"provenance": {"device": "cpu"}}, name="a/v1")
    write_gate(tmp_path, {"provenance": {"device": "cuda"}}, name="b/v1")
    rc, out = run(tmp_path)
    assert rc == 0, out
    assert "distinct devices" in out


def test_an_empty_root_cannot_verify(tmp_path):
    rc, out = run(tmp_path)
    assert rc == 1
    assert "CANNOT VERIFY" in out
