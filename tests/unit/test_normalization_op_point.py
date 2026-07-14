"""Unit tests for the operating-point guard in scripts/normalization/fit_normalization.py.

Why this guard exists: fitting the percentile CDF on articles below the filter's
visibility threshold maps sub-visibility content into the visible band by
construction. nature_recovery v2 was fitted at raw >= 1.5, giving the fit set a
median of 2.19, so correctly-scored doom articles (model said 2.2-3.3) mapped to
normalized 5.2-8.3 and reached the Recovery lens at up to 8.34/10 (NexusMind#161).
The model was never wrong; --min-score was.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_fitter():
    """Load the fitter by path — scripts/ isn't an importable package."""
    path = REPO_ROOT / "scripts" / "normalization" / "fit_normalization.py"
    spec = importlib.util.spec_from_file_location("fit_normalization", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["fit_normalization"] = module
    spec.loader.exec_module(module)
    return module


fitter = _load_fitter()


class TestLowestNonzero:
    def test_picks_lowest_threshold_above_zero(self):
        assert fitter._lowest_nonzero([0.0, 3.75, 7.0]) == 3.75

    def test_ignores_the_zero_floor_tier(self):
        # "low" always sits at 0.0 and is never the operating point.
        assert fitter._lowest_nonzero([7.0, 4.0, 0.0]) == 4.0

    def test_handles_non_standard_tier_counts(self):
        # sustainability_technology v1/v2 use a 4-tier scheme.
        assert fitter._lowest_nonzero([0.0, 3.0, 5.0, 7.0]) == 3.0

    def test_returns_none_when_no_positive_threshold(self):
        assert fitter._lowest_nonzero([0.0]) is None
        assert fitter._lowest_nonzero([]) is None

    def test_ignores_none_entries(self):
        # investment_risk configs carry tier keys with threshold: null.
        assert fitter._lowest_nonzero([None, None]) is None
        assert fitter._lowest_nonzero([None, 4.0, 0.0]) == 4.0


class TestOpPointFromBaseScorer:
    def test_reads_tier_thresholds_without_importing(self, tmp_path):
        # base_scorer.py imports torch transitively; parsing must not need it.
        (tmp_path / "base_scorer.py").write_text(
            "import torch  # would explode on import\n"
            "class S:\n"
            "    TIER_THRESHOLDS = [\n"
            '        ("high", 7.0, "d"),\n'
            '        ("medium", 3.75, "d"),\n'
            '        ("low", 0.0, "d"),\n'
            "    ]\n"
        )
        assert fitter._op_point_from_base_scorer(tmp_path) == 3.75

    def test_returns_none_when_file_absent(self, tmp_path):
        assert fitter._op_point_from_base_scorer(tmp_path) is None

    def test_returns_none_on_unparseable_file(self, tmp_path):
        (tmp_path / "base_scorer.py").write_text("def broken(:\n")
        assert fitter._op_point_from_base_scorer(tmp_path) is None

    def test_returns_none_when_thresholds_not_a_literal(self, tmp_path):
        (tmp_path / "base_scorer.py").write_text(
            "class S:\n    TIER_THRESHOLDS = build_tiers()\n"
        )
        assert fitter._op_point_from_base_scorer(tmp_path) is None

    def test_real_nature_recovery_v4_resolves_to_tuned_op_point(self):
        # The 3.75 operating point is tuned, not incidental (test set n=391,
        # 2026-07-10): it beats 4.0 on both recall and precision for v4.
        assert (
            fitter._op_point_from_base_scorer(
                REPO_ROOT / "filters" / "nature_recovery" / "v4"
            )
            == 3.75
        )


class TestOpPointFromConfig:
    def test_reads_tiers_block(self):
        config = {"scoring": {"tiers": {
            "high": {"threshold": 7.0},
            "medium": {"threshold": 4.0},
            "low": {"threshold": 0.0},
        }}}
        assert fitter._op_point_from_config(config) == 4.0

    def test_reads_tier_thresholds_alias(self):
        # Config shape varies across filters (tiers vs tier_thresholds).
        config = {"scoring": {"tier_thresholds": {"a": {"threshold": 5.0}, "b": {"threshold": 0.0}}}}
        assert fitter._op_point_from_config(config) == 5.0

    def test_returns_none_when_absent(self):
        assert fitter._op_point_from_config({}) is None
        assert fitter._op_point_from_config({"scoring": {}}) is None


class TestResolveOpPoint:
    def test_base_scorer_wins_over_config_on_drift(self, tmp_path, caplog):
        """TIER_THRESHOLDS is the sole runtime source for tier assignment; config
        is documentation that must mirror it. On drift the runtime value wins and
        the mismatch is reported — the two silently disagreed for the whole v4
        deploy (config 3.75, code an inert 4.0)."""
        (tmp_path / "base_scorer.py").write_text(
            'class S:\n    TIER_THRESHOLDS = [("medium", 4.0, "d"), ("low", 0.0, "d")]\n'
        )
        config = {"scoring": {"tiers": {"medium": {"threshold": 3.0}, "low": {"threshold": 0.0}}}}
        with caplog.at_level("WARNING"):
            assert fitter.resolve_op_point(tmp_path, config) == 4.0
        assert "drift" in caplog.text.lower()

    def test_falls_back_to_config_when_no_base_scorer(self, tmp_path):
        config = {"scoring": {"tiers": {"medium": {"threshold": 4.0}, "low": {"threshold": 0.0}}}}
        assert fitter.resolve_op_point(tmp_path, config) == 4.0

    def test_no_warning_when_they_agree(self, tmp_path, caplog):
        (tmp_path / "base_scorer.py").write_text(
            'class S:\n    TIER_THRESHOLDS = [("medium", 4.0, "d"), ("low", 0.0, "d")]\n'
        )
        config = {"scoring": {"tiers": {"medium": {"threshold": 4.0}, "low": {"threshold": 0.0}}}}
        with caplog.at_level("WARNING"):
            assert fitter.resolve_op_point(tmp_path, config) == 4.0
        assert "drift" not in caplog.text.lower()

    def test_returns_none_when_neither_source_available(self, tmp_path):
        assert fitter.resolve_op_point(tmp_path, {}) is None


@pytest.mark.parametrize(
    "filter_dir,expected",
    [
        ("filters/nature_recovery/v4", 3.75),
        ("filters/nature_recovery/v2", 4.0),
        ("filters/cultural_discovery/v5", 4.0),
        ("filters/belonging/v1", 4.0),
        ("filters/uplifting/v7", 4.0),
    ],
)
def test_production_filters_resolve_their_op_point(filter_dir, expected):
    """Every production filter must resolve — an unresolvable op-point makes the
    fitter refuse to run rather than silently fall back to a hardcoded default."""
    assert fitter._op_point_from_base_scorer(REPO_ROOT / filter_dir) == expected
