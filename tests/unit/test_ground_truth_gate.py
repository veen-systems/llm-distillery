"""
Unit tests for scripts/gate/ground_truth_gate.py pure functions.

Backs the corrected deploy-gate methodology (judge each model against held-out
oracle ground truth, not against the prior generous model). Covers the
confusion-matrix metrics, the gatekeepered label WA, and spearman.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
_spec = importlib.util.spec_from_file_location(
    "ground_truth_gate", ROOT / "scripts" / "gate" / "ground_truth_gate.py")
gt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gt)


def test_label_wa_weights_sum_to_one():
    assert abs(sum(gt.WEIGHTS.values()) - 1.0) < 1e-9


def test_label_wa_gatekeeper_caps_low_evidence():
    # recovery_evidence=0, everything else 10 -> capped at 3.5
    assert gt.label_wa([0, 10, 10, 10, 10, 10]) == pytest.approx(3.5)


def test_label_wa_no_cap_when_evidence_present():
    assert gt.label_wa([3, 10, 10, 10, 10, 10]) > 3.5


def test_evaluate_perfect_prediction():
    truth = {"a": 6.0, "b": 5.0, "c": 1.0, "d": 0.5}
    pred = dict(truth)
    m = gt.evaluate(truth, pred)
    assert m["recall"] == 1.0 and m["precision"] == 1.0
    assert m["specificity"] == 1.0 and m["f1"] == 1.0


def test_evaluate_confusion_counts():
    truth = {"a": 6.0, "b": 5.0, "c": 1.0, "d": 4.5}   # 3 positives (a,b,d), 1 neg (c)
    pred = {"a": 6.0, "b": 2.0, "c": 5.0, "d": 4.5}    # a TP, b FN, c FP, d TP
    m = gt.evaluate(truth, pred)
    assert (m["tp"], m["fn"], m["fp"], m["tn"]) == (2, 1, 1, 0)
    assert m["recall"] == pytest.approx(2 / 3)
    assert m["precision"] == pytest.approx(2 / 3)


def test_evaluate_only_scores_common_ids():
    truth = {"a": 6.0, "b": 5.0}
    pred = {"a": 6.0}  # b missing from predictions
    m = gt.evaluate(truth, pred)
    assert m["n"] == 1


def test_evaluate_threshold_boundary_is_inclusive():
    # exactly 4.0 counts as surfaced/positive (>=)
    truth = {"a": 4.0}
    pred = {"a": 4.0}
    m = gt.evaluate(truth, pred)
    assert m["tp"] == 1 and m["fn"] == 0


def test_spearman_monotonic():
    assert gt.spearman([1, 2, 3, 4], [2, 4, 6, 8]) == pytest.approx(1.0)
    assert gt.spearman([1, 2, 3, 4], [8, 6, 4, 2]) == pytest.approx(-1.0)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
