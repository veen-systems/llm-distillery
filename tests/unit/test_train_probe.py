"""
Unit tests for scripts/train_probe.py pure functions (recall-first probe).

Covers the torch-free helpers that decide the Stage-1 screen threshold:
- gatekeepered_wa / labels_to_binary : the MEDIUM+ target
- screen_wa / screen_wa_batch        : the EXACT deployed screen statistic
- fn_rate / stage2_rate / recall_curve
- select_threshold                   : highest threshold within the FN budget

These mirror the invariants agreement_gate.py relies on and guard the H3
recall bug (a floor-collapsed probe that drops genuine positives at Stage 1).
"""

import numpy as np
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.train_probe import (
    MEDIUM, DIMENSION_NAMES, WEIGHTS,
    gatekeepered_wa, labels_to_binary, screen_wa, screen_wa_batch,
    fn_rate, stage2_rate, recall_curve, select_threshold,
)


# --- target construction --------------------------------------------------- #

def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9
    assert list(WEIGHTS.keys()) == DIMENSION_NAMES


def test_gatekeepered_wa_accepts_dict_and_list_equally():
    vec = [5, 5, 5, 5, 5, 5]
    d = dict(zip(DIMENSION_NAMES, vec))
    assert gatekeepered_wa(vec) == gatekeepered_wa(d) == pytest.approx(5.0)


def test_gatekeeper_caps_when_recovery_evidence_low():
    # High other dims but recovery_evidence < 3 -> capped at 3.5
    vec = [0, 10, 10, 10, 10, 10]  # recovery_evidence=0
    raw = sum(v * WEIGHTS[n] for v, n in zip(vec, DIMENSION_NAMES))
    assert raw > 3.5
    assert gatekeepered_wa(vec) == pytest.approx(3.5)


def test_gatekeeper_not_applied_when_evidence_present():
    vec = [3, 10, 10, 10, 10, 10]  # recovery_evidence=3 (>= MIN)
    assert gatekeepered_wa(vec) > 3.5


def test_labels_to_binary_threshold_at_medium():
    # WA exactly 4.0 counts as positive (>=)
    just_pos = [4, 4, 4, 4, 4, 4]          # wa 4.0, evidence ok
    just_neg = [3.9, 3.9, 3.9, 3.9, 3.9, 3.9]  # wa 3.9
    y = labels_to_binary([just_pos, just_neg])
    assert list(y) == [1.0, 0.0]


def test_gatekeepered_positive_blocked_by_gatekeeper_is_negative():
    # Would be MEDIUM+ on raw weights but recovery_evidence=0 caps to 3.5 -> negative
    vec = [0, 10, 10, 10, 10, 10]
    assert labels_to_binary([vec])[0] == 0.0


# --- deployed screen statistic (must match EmbeddingStage) ----------------- #

def test_screen_wa_clamps_each_dimension():
    # Values outside [0,10] get clamped BEFORE weighting (matches EmbeddingStage)
    pred = [100, -100, 5, 5, 5, 5]
    d = {"recovery_evidence": 10, "measurable_outcomes": 0,
         "ecological_significance": 5, "restoration_scale": 5,
         "human_agency": 5, "protection_durability": 5}
    expected = sum(d[k] * WEIGHTS[k] for k in DIMENSION_NAMES)
    assert screen_wa(pred) == pytest.approx(expected)


def test_screen_wa_has_no_gatekeeper():
    # Stage 1 deliberately skips the gatekeeper (hybrid_scorer.py:241):
    # recovery_evidence=0 but the weighted sum is NOT capped at 3.5.
    pred = [0, 10, 10, 10, 10, 10]
    assert screen_wa(pred) > 3.5


def test_screen_wa_batch_matches_scalar():
    rng = np.random.default_rng(0)
    batch = rng.uniform(-2, 12, size=(20, 6))
    got = screen_wa_batch(batch)
    exp = np.array([screen_wa(row) for row in batch])
    assert np.allclose(got, exp)


# --- FN / stage2 / curve --------------------------------------------------- #

def test_fn_rate_counts_positives_below_threshold():
    pred_wa = np.array([1.0, 5.0, 3.0, 6.0])
    y = np.array([1, 1, 1, 0])  # 3 positives
    # threshold 4.0 -> positives at 1.0 and 3.0 are FN (2 of 3)
    assert fn_rate(pred_wa, y, 4.0) == pytest.approx(2 / 3)


def test_fn_rate_zero_with_no_positives():
    assert fn_rate(np.array([1.0, 2.0]), np.array([0, 0]), 4.0) == 0.0


def test_fn_rate_monotonic_nondecreasing_in_threshold():
    rng = np.random.default_rng(1)
    pred_wa = rng.uniform(0, 8, size=200)
    y = (rng.uniform(size=200) < 0.3).astype(float)
    prev = -1.0
    for t in np.arange(0, 8, 0.1):
        f = fn_rate(pred_wa, y, t)
        assert f >= prev - 1e-12
        prev = f


def test_stage2_rate_fraction_above_threshold():
    pred_wa = np.array([1.0, 5.0, 3.0, 6.0])
    assert stage2_rate(pred_wa, 4.0) == pytest.approx(0.5)  # 5.0, 6.0


def test_recall_curve_shape():
    pred_wa = np.array([1.0, 5.0, 3.0, 6.0])
    y = np.array([1, 1, 1, 0])
    rows = recall_curve(pred_wa, y, [0.0, 4.0])
    assert rows[0]["fn_rate"] == 0.0 and rows[0]["recall"] == 1.0
    assert rows[1]["recall"] == pytest.approx(1 - 2 / 3)


# --- threshold selection --------------------------------------------------- #

def test_select_threshold_respects_fn_budget():
    # positives at 2.0 and 5.0. target_fn=0 -> highest threshold with zero FN
    # must be <= 2.0 (so neither positive drops).
    pred_wa = np.array([2.0, 5.0, 0.5, 1.0])
    y = np.array([1, 1, 0, 0])
    thr, fn, s2 = select_threshold(pred_wa, y, target_fn=0.0)
    assert fn == 0.0
    assert thr <= 2.0


def test_select_threshold_allows_higher_with_budget():
    # target_fn=0.5 permits dropping 1 of 2 positives -> threshold can climb
    # above the lower positive (2.0) up toward the higher (5.0).
    pred_wa = np.array([2.0, 5.0, 0.5, 1.0])
    y = np.array([1, 1, 0, 0])
    thr_strict, _, _ = select_threshold(pred_wa, y, target_fn=0.0)
    thr_loose, fn_loose, _ = select_threshold(pred_wa, y, target_fn=0.5)
    assert thr_loose > thr_strict
    assert fn_loose <= 0.5


def test_select_threshold_floor_collapse_is_caught_by_zero_budget():
    # A floor-collapsed probe predicts ~0 for everything, including positives.
    # With target_fn=0 the only safe threshold is ~0 (route everything to
    # Stage 2) — recall preserved, screening gives up. This is the H3 guard.
    pred_wa = np.full(100, 0.05)
    y = np.zeros(100)
    y[:15] = 1.0
    thr, fn, s2 = select_threshold(pred_wa, y, target_fn=0.0)
    assert fn == 0.0
    assert thr <= 0.05
    assert s2 == pytest.approx(1.0)  # everything still reaches Stage 2


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
