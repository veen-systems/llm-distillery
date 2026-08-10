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


def test_noise_floor_is_the_measured_value_not_rounded_up():
    # #95 measured max |delta| 0.1617; the stated floor is 0.16. An earlier draft
    # of the memory file rounded to 0.17 — that was wrong and must not come back.
    assert gt.NOISE_FLOOR == 0.16


def test_indeterminate_counts_articles_within_the_floor_of_the_threshold():
    # d is 0.05 below the op-point, e is 0.10 above it -> both indeterminate.
    # a and c sit well clear -> neither is.
    truth = {"a": 6.0, "c": 1.0, "d": 5.0, "e": 1.0}
    pred = {"a": 6.0, "c": 1.0, "d": 3.95, "e": 4.10}
    m = gt.evaluate(truth, pred)
    assert m["n_indeterminate"] == 2


def test_band_brackets_the_point_estimate():
    truth = {"a": 6.0, "b": 5.0, "c": 1.0, "d": 0.5}
    pred = {"a": 6.0, "b": 4.05, "c": 3.95, "d": 0.5}
    m = gt.evaluate(truth, pred)
    # specificity included deliberately: ADR-023 makes it THE objective, it is
    # what the DISJOINT/OVERLAP verdict is computed from, and it was the one band
    # shipped without a test (found by review battery, 2026-08-10).
    for key in ("recall", "precision", "specificity", "f1"):
        lo, hi = m[f"{key}_band"]
        assert lo <= m[key] <= hi


def test_specificity_band_stays_in_unit_interval_and_denominator_is_invariant():
    """tn+fp cannot move under the flips the band models -- both cells are truth-negatives."""
    truth = {"a": 6.0, "b": 5.0, "c": 1.0, "d": 0.5, "e": 1.0}
    pred = {"a": 6.0, "b": 4.05, "c": 3.95, "d": 0.5, "e": 4.02}
    m = gt.evaluate(truth, pred)
    lo, hi = m["specificity_band"]
    assert 0.0 <= lo <= m["specificity"] <= hi <= 1.0
    cells = m["indeterminate_by_cell"]
    assert sum(cells.values()) == m["n_indeterminate"]
    assert cells["fp"] + cells["tn"] <= m["fp"] + m["tn"]


def test_truth_threshold_pins_the_positive_set_while_the_bar_sweeps():
    """Without pinning, sweeping `medium` changes WHICH articles count as on-lens,
    so recall at one threshold is not comparable to recall at another (#102)."""
    truth = {"a": 6.0, "b": 4.2, "c": 4.6, "d": 1.0}
    pred = {"a": 6.0, "b": 4.2, "c": 4.6, "d": 1.0}
    pinned = [gt.evaluate(truth, pred, medium=t, truth_threshold=4.0) for t in (4.0, 4.5, 5.0)]
    assert {m["positives"] for m in pinned} == {3}, "pinned truth must hold the positive set fixed"
    assert [m["tp"] for m in pinned] == [3, 2, 1], "only the prediction side may move"

    unpinned = [gt.evaluate(truth, pred, medium=t) for t in (4.0, 4.5, 5.0)]
    assert [m["positives"] for m in unpinned] == [3, 2, 1], "unpinned, the positive set moves too"


def test_default_truth_threshold_is_tied_to_medium():
    """Back-compat: omitting truth_threshold must reproduce every pre-2026-08-10 run."""
    truth = {"a": 6.0, "b": 4.2, "c": 1.0}
    pred = {"a": 5.9, "b": 3.0, "c": 4.4}
    assert gt.evaluate(truth, pred, medium=4.5) == gt.evaluate(truth, pred, medium=4.5,
                                                               truth_threshold=4.5)


def test_band_collapses_to_the_point_estimate_when_nothing_is_borderline():
    truth = {"a": 6.0, "b": 5.0, "c": 1.0, "d": 0.5}
    pred = dict(truth)
    m = gt.evaluate(truth, pred)
    assert m["n_indeterminate"] == 0
    assert m["recall_band"] == [m["recall"], m["recall"]]
    assert m["f1_band"] == [m["f1"], m["f1"]]


def test_borderline_true_positive_can_fall_out_of_recall():
    # one positive, predicted 0.05 above the threshold: recall reads 1.0, but the
    # band must admit 0.0 because the batch alone decided it.
    truth = {"a": 5.0}
    pred = {"a": 4.05}
    m = gt.evaluate(truth, pred)
    assert m["recall"] == 1.0
    assert m["recall_band"] == [0.0, 1.0]


def test_noise_floor_zero_reproduces_the_pre_2026_08_06_behaviour():
    truth = {"a": 5.0, "b": 1.0}
    pred = {"a": 4.05, "b": 3.95}
    m = gt.evaluate(truth, pred, noise_floor=0.0)
    assert m["n_indeterminate"] == 0
    assert m["recall_band"] == [m["recall"], m["recall"]]


def test_spearman_monotonic():
    assert gt.spearman([1, 2, 3, 4], [2, 4, 6, 8]) == pytest.approx(1.0)
    assert gt.spearman([1, 2, 3, 4], [8, 6, 4, 2]) == pytest.approx(-1.0)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
