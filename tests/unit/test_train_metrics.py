"""Pins the needle-metric plumbing in training/train.py.

Nothing in tests/ referenced training.train before this file, so the 573 passing
tests carried ZERO information about that module: none of them could execute a
changed line. The defect these tests exist for was silent for exactly that reason
-- `--select-metric` was accepted and inert, and selection fell back to aggregate
MAE, which ADR-023 forbids ranking on.
"""
import sys
from pathlib import Path

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from training.train import (  # noqa: E402
    _medium_threshold_from_config,
    compute_metrics,
    resolve_medium_threshold,
)

NAMES = ["a", "b", "c", "d", "e", "f"]
WEIGHTS = [0.3, 0.2, 0.15, 0.1, 0.1, 0.15]
NEEDLE_KEYS = ("recall_at_10", "recall_at_20", "recall_at_50", "ndcg_at_10", "recall_medium")


def _needle_fixture(n=400, seed=0):
    """A thin needle over a floor -- the shape every filter here has."""
    torch.manual_seed(seed)
    labels = torch.zeros(n, 6)
    labels[:20] = torch.rand(20, 6) * 9
    return labels + torch.randn(n, 6) * 0.3, labels


class TestNeedleMetricsArePresent:
    def test_weights_none_emits_no_needle_metrics(self):
        """The pre-fix state. Kept as the NEGATIVE CONTROL: without it, a test
        asserting the keys exist cannot distinguish a working fix from a
        compute_metrics that emits them unconditionally."""
        preds, labels = _needle_fixture()
        m = compute_metrics(preds, labels, NAMES, None)
        for k in NEEDLE_KEYS:
            assert k not in m

    def test_weights_supplied_emits_needle_metrics(self):
        preds, labels = _needle_fixture()
        m = compute_metrics(preds, labels, NAMES, WEIGHTS)
        for k in NEEDLE_KEYS:
            assert k in m


class TestMediumThresholdIsLive:
    def test_threshold_changes_the_positive_count(self):
        """If n_positives is constant the threshold is decorative."""
        preds, labels = _needle_fixture()
        counts = [
            compute_metrics(preds, labels, NAMES, WEIGHTS, medium_threshold=t)["n_positives"]
            for t in (2.25, 3.75, 4.0, 4.25, 4.5)
        ]
        assert counts == [19, 16, 14, 10, 10]
        assert len(set(counts)) > 1

    def test_default_is_backwards_compatible(self):
        preds, labels = _needle_fixture()
        a = compute_metrics(preds, labels, NAMES, WEIGHTS)
        b = compute_metrics(preds, labels, NAMES, WEIGHTS, medium_threshold=4.0)
        assert a["n_positives"] == b["n_positives"] == 14


class TestRecallAtKCannotBeConstant:
    """recall_at_k clamped with min(k, n) is identically 1.0 when n <= k, so a
    poor model scores a perfect metric and the strict `>` pins epoch 1 forever."""

    @pytest.mark.parametrize("n", [8, 15, 20])
    def test_small_split_does_not_emit_a_degenerate_recall_at_20(self, n):
        torch.manual_seed(0)
        labels = torch.rand(n, 6) * 9
        preds = labels + torch.randn(n, 6) * 2.0  # deliberately poor
        m = compute_metrics(preds, labels, NAMES, WEIGHTS)
        assert m.get("recall_at_20") is None

    def test_large_split_still_emits_and_can_fail(self):
        torch.manual_seed(0)
        labels = torch.rand(100, 6) * 9
        preds = labels + torch.randn(100, 6) * 2.0
        m = compute_metrics(preds, labels, NAMES, WEIGHTS)
        assert m["recall_at_20"] < 1.0, "a poor model must be able to score below 1.0"


class TestThresholdResolution:
    def test_reads_the_tiers_schema(self):
        cfg = {"scoring": {"tiers": {"high": {"threshold": 7.0},
                                     "medium": {"threshold": 4.5},
                                     "low": {"threshold": 0.0}}}}
        assert _medium_threshold_from_config(cfg) == 4.5

    def test_reads_the_tier_thresholds_min_score_schema(self):
        """resilience/v1's shape. Reading only scoring.tiers.medium.threshold
        returned 4.0 here while the filter really deploys at 4.5."""
        cfg = {"scoring": {"tier_thresholds": {"medium": {"min_score": 4.5},
                                               "low": {"min_score": 0.0}}}}
        assert _medium_threshold_from_config(cfg) == 4.5

    def test_is_tier_name_agnostic(self):
        """uplifting v1/v4 call it `connection`; todo/v1 calls it `monitoring`."""
        cfg = {"scoring": {"tiers": {"connection": {"threshold": 3.0},
                                     "none": {"threshold": 0.0}}}}
        assert _medium_threshold_from_config(cfg) == 3.0

    @pytest.mark.parametrize("cfg", [
        {}, {"scoring": None}, {"scoring": {"tiers": None}},
        {"scoring": {"tiers": {"medium": None}}},
        {"scoring": {"tiers": {"medium": {"threshold": None}}}},
        {"scoring": {"tiers": {"low": {"threshold": 0.0}}}},
    ])
    def test_unresolvable_shapes_return_none_and_never_crash(self, cfg):
        assert _medium_threshold_from_config(cfg) is None

    def test_unresolvable_config_RAISES_rather_than_defaulting(self, tmp_path):
        """The whole point: a plausible-but-wrong 4.0 silently decides which
        checkpoint ships and is indistinguishable in metadata from a real 4.0."""
        with pytest.raises(RuntimeError, match="Cannot resolve the MEDIUM"):
            resolve_medium_threshold(tmp_path, {"scoring": {}}, None)

    def test_cli_override_wins_and_is_labelled(self, tmp_path):
        val, src = resolve_medium_threshold(tmp_path, {"scoring": {}}, 3.25)
        assert val == 3.25 and "cli" in src

    def test_config_fallback_says_it_is_not_the_runtime_source(self, tmp_path):
        cfg = {"scoring": {"tiers": {"medium": {"threshold": 4.5}}}}
        val, src = resolve_medium_threshold(tmp_path, cfg, None)
        assert val == 4.5
        assert "NOT the runtime source" in src


class TestRealFilterConfigs:
    """The values the code comment asserts, read off disk rather than restated."""

    @pytest.mark.parametrize("rel,expected", [
        ("filters/solutions/v6", 2.25),
        ("filters/nature_recovery/v4", 3.75),
        ("filters/investment_risk/v6", 4.25),
        ("filters/uplifting/v7", 4.5),
        ("filters/human_thriving/v8", 4.5),
        ("filters/resilience/v1", 4.5),  # the tier_thresholds/min_score shape
    ])
    def test_shipped_configs_resolve_to_their_documented_boundary(self, rel, expected):
        import yaml
        root = Path(__file__).resolve().parents[2]
        cfg_path = root / rel / "config.yaml"
        if not cfg_path.exists():
            pytest.skip(f"{rel} not on disk")
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        assert _medium_threshold_from_config(cfg) == expected
