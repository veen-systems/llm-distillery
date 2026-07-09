"""
Unit tests for scripts/gate/agreement_gate.py (nature_recovery v4 deploy gate).

Backs the "written + unit-tested" claim for the gate that blocks deploy. Covers
the statistics (wilson_lower, spearman, surfacing_score) and the run_gate wiring
for the metric-3 SKIP path and the overall PASS/FAIL rule.
"""

import importlib.util
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
# scripts/gate isn't a package; load the module by path.
_spec = importlib.util.spec_from_file_location(
    "agreement_gate", ROOT / "scripts" / "gate" / "agreement_gate.py")
ag = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ag)


# --- surfacing_score ------------------------------------------------------- #

def test_surfacing_score_prefers_precomputed_weighted_average():
    assert ag.surfacing_score({"weighted_average": 4.2}) == pytest.approx(4.2)


def test_surfacing_score_computes_from_analysis_dict():
    dims = {d: {"score": 5.0} for d in ag.WEIGHTS}
    rec = {"nature_recovery_analysis": dims}
    assert ag.surfacing_score(rec) == pytest.approx(5.0)


def test_surfacing_score_applies_gatekeeper():
    dims = {d: {"score": 10.0} for d in ag.WEIGHTS}
    dims["recovery_evidence"] = {"score": 0.0}  # below GATEKEEPER_MIN
    rec = {"nature_recovery_analysis": dims}
    assert ag.surfacing_score(rec) == pytest.approx(ag.GATEKEEPER_CAP)


def test_surfacing_score_accepts_bare_scores():
    dims = {d: 5.0 for d in ag.WEIGHTS}
    assert ag.surfacing_score(dims) == pytest.approx(5.0)


# --- wilson_lower ---------------------------------------------------------- #

def test_wilson_lower_zero_n():
    assert ag.wilson_lower(0, 0) == 0.0


def test_wilson_lower_below_point_estimate():
    # lower bound < observed proportion, and within [0,1]
    lo = ag.wilson_lower(9, 10)
    assert 0.0 <= lo < 0.9


def test_wilson_lower_perfect_is_high_but_not_one():
    lo = ag.wilson_lower(40, 40)
    assert 0.9 < lo < 1.0


# --- spearman -------------------------------------------------------------- #

def test_spearman_perfect_monotonic():
    xs = [1, 2, 3, 4, 5]
    ys = [10, 20, 30, 40, 50]
    assert ag.spearman(xs, ys) == pytest.approx(1.0)


def test_spearman_perfect_inverse():
    xs = [1, 2, 3, 4, 5]
    ys = [50, 40, 30, 20, 10]
    assert ag.spearman(xs, ys) == pytest.approx(-1.0)


def test_spearman_handles_ties():
    xs = [1, 1, 2, 2]
    ys = [1, 1, 2, 2]
    assert ag.spearman(xs, ys) == pytest.approx(1.0)


def test_spearman_too_few_points():
    assert ag.spearman([1], [1]) == 0.0


# --- run_gate wiring ------------------------------------------------------- #

def _write_jsonl(path, rows):
    import json
    path.write_text("\n".join(json.dumps(r) for r in rows))


def test_run_gate_metric3_skips_without_protection_probes(tmp_path):
    gate_dir = tmp_path / "gate"
    gate_dir.mkdir()
    # decline probes (held-out ids) — v4 must NOT surface them
    (gate_dir / "nr_v4_heldout_ids.txt").write_text("d1\nd2\n")
    _write_jsonl(gate_dir / "nr_v4_sourceA_reference.jsonl",
                 [{"id": "a1"}, {"id": "a2"}])
    v4 = {"d1": {"weighted_average": 1.0}, "d2": {"weighted_average": 2.0},
          "a1": {"weighted_average": 5.0}, "a2": {"weighted_average": 1.0}}
    v2 = {"a1": {"weighted_average": 5.0}, "a2": {"weighted_average": 1.0}}
    rep = ag.run_gate(v2, v4, gate_dir, protection_probes=None)
    assert rep["metrics"]["protection_acceptance"]["pass"] is None
    assert rep["metrics"]["protection_acceptance"]["status"].startswith("SKIPPED")
    # A None-pass metric must not count toward overall pass.
    assert any("Metric 3 SKIPPED" in w for w in rep["warnings"])


def test_run_gate_overall_fail_when_decline_probes_surface(tmp_path):
    gate_dir = tmp_path / "gate"
    gate_dir.mkdir()
    (gate_dir / "nr_v4_heldout_ids.txt").write_text("d1\nd2\n")
    _write_jsonl(gate_dir / "nr_v4_sourceA_reference.jsonl", [{"id": "a1"}])
    # both decline probes SURFACE under v4 -> probe_demotion fails
    v4 = {"d1": {"weighted_average": 6.0}, "d2": {"weighted_average": 6.0},
          "a1": {"weighted_average": 5.0}}
    v2 = {"a1": {"weighted_average": 5.0}}
    rep = ag.run_gate(v2, v4, gate_dir)
    assert rep["metrics"]["probe_demotion"]["pass"] is False
    assert rep["overall_pass"] is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
