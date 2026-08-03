"""
Unit tests for the #93 length-floor split.

The 300-char floor used to be a scoring gate inside every prefilter's
`apply_filter()`. Measurement (NexusMind#284/#285, llm-distillery#92) showed it
was 87-100% of everything four of six production prefilters block, and that
short content clearing an op-point is as likely to be genuine as long content.
It is now:

  - a LABELLING-time precondition, enforced by the oracle path
    (`make_oracle_prefilter`), where the framework-leakage rationale applies;
  - a STAMP on every scoring result (`content_length`);
  - at most ONE config-gated cap (`short_content.cap`), off by default.

These tests pin all three halves, and pin that the production prefilters no
longer emit `content_too_short`.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from filters.common.base_prefilter import BasePreFilter
from ground_truth.batch_scorer import make_oracle_prefilter


SHORT_CONTENT = "A tiny community garden opened downtown today."
LONG_CONTENT = (
    "A tiny community garden opened downtown today, the result of four years of "
    "organising by residents who wanted a shared growing space. " * 6
)


def _article(content: str, **extra) -> dict:
    article = {"title": "Community garden opens", "content": content}
    article.update(extra)
    return article


class TestLabellingGateIntact:
    """check_content_length() is unchanged — the oracle still needs it."""

    def test_short_content_blocked(self):
        passed, reason = BasePreFilter.check_content_length(_article(SHORT_CONTENT))
        assert passed is False
        assert "content_too_short" in reason

    def test_long_content_passes(self):
        passed, reason = BasePreFilter.check_content_length(_article(LONG_CONTENT))
        assert passed is True
        assert reason == "passed"


class TestApplyFilterNoLongerGatesOnLength:
    """The scoring-path half: apply_filter() must not block on length."""

    def test_base_apply_filter_passes_short_content(self):
        assert BasePreFilter().apply_filter(_article(SHORT_CONTENT)) == (True, "passed")

    @pytest.mark.parametrize(
        "content,expected",
        [
            # "" is falsy, so validate_article's `content or text` fallback reads
            # it as absent rather than empty. Both are blocks; the reason differs.
            ("", "missing_content"),
            ("   ", "empty_content"),
        ],
    )
    def test_empty_content_still_blocked(self, content, expected):
        """Empty is a different case from short — validate_article still owns it."""
        passed, reason = BasePreFilter().apply_filter(_article(content))
        assert passed is False
        assert reason == expected

    @pytest.mark.parametrize(
        "module_path,class_name",
        [
            ("filters/nature_recovery/v4/prefilter.py", None),
            ("filters/solutions/v6/prefilter.py", None),
            ("filters/uplifting/v7/prefilter.py", None),
            ("filters/belonging/v1/prefilter.py", None),
            ("filters/investment_risk/v6/prefilter.py", None),
            ("filters/cultural_discovery/v5/prefilter.py", None),
        ],
    )
    def test_production_prefilters_never_emit_content_too_short(
        self, module_path, class_name
    ):
        """No production prefilter may block on length any more.

        Asserted on the reason string rather than on pass/pass: a filter is free
        to block this article for a lens reason (that is its job), but never for
        being short.
        """
        prefilter = _load_prefilter(module_path, class_name)
        _passed, reason = prefilter.apply_filter(
            _article(SHORT_CONTENT, url="https://example.org/garden", source="local_news")
        )
        assert "content_too_short" not in reason


class TestOraclePrefilterKeepsTheFloor:
    """The labelling half: the oracle wrapper composes floor + lens rules."""

    def test_short_content_blocked_by_wrapper(self):
        gate = make_oracle_prefilter(BasePreFilter())
        assert gate(_article(SHORT_CONTENT)) is False

    def test_long_content_admitted_by_wrapper(self):
        gate = make_oracle_prefilter(BasePreFilter())
        assert gate(_article(LONG_CONTENT)) is True

    def test_no_prefilter_object_yields_none(self):
        assert make_oracle_prefilter(None) is None

    def test_prefilter_obj_attribute_preserved(self):
        """batch_scorer reaches through this attribute for Unicode cleaning."""
        obj = BasePreFilter()
        assert make_oracle_prefilter(obj).prefilter_obj is obj

    def test_lens_block_still_honoured(self):
        """A long article blocked by a lens rule stays blocked."""

        class Blocking(BasePreFilter):
            EXCLUSION_PATTERNS = {"garden": [r"community garden"]}

        gate = make_oracle_prefilter(Blocking())
        assert gate(_article(LONG_CONTENT)) is False

    def test_floor_is_uniform_across_filters(self):
        """cultural_discovery v5 is now floored too — an intended side effect.

        cd v4/v5's custom `apply_filter` never called `check_content_length`
        (a v3 regression its own module docstring records as an open
        follow-up), so before #93 cd was the one filter whose ORACLE path had
        no length floor. Hoisting the floor into the wrapper restores it
        uniformly. Measured on a short-skewed stress corpus this withholds ~40%
        of what cd would otherwise have sent to the oracle, so it must stay a
        pinned decision rather than an accident: if cd should be exempt, exempt
        it here explicitly.
        """
        prefilter = _load_prefilter("filters/cultural_discovery/v5/prefilter.py", None)
        short_but_on_lens = _article(
            "A new museum of textile craft opened in Oaxaca this week.",
            title="Oaxaca opens a museum of Indigenous textile craft",
        )
        assert prefilter.apply_filter(short_but_on_lens)[0] is True
        assert make_oracle_prefilter(prefilter)(short_but_on_lens) is False

    def test_object_without_length_check_is_tolerated(self):
        """Filter packages need not inherit BasePreFilter."""

        class Bare:
            def apply_filter(self, article):
                return (True, "passed")

        gate = make_oracle_prefilter(Bare())
        assert gate(_article(SHORT_CONTENT)) is True


class _FakeScorer:
    """Minimal stand-in exercising the base scorer's short-content methods.

    Avoids loading a 1B-parameter model: the stamp and the cap are pure
    functions of the result dict and the config, so they are bound off
    FilterBaseScorer directly.
    """

    def __init__(self, cap=None, min_chars=300):
        from filters.common.filter_base_scorer import FilterBaseScorer

        self.short_content_cap = cap
        self.short_content_min_chars = min_chars
        self._create_empty_result = FilterBaseScorer._create_empty_result.__get__(self)
        self._stamp_content_length = FilterBaseScorer._stamp_content_length.__get__(self)
        self._apply_short_content_cap = (
            FilterBaseScorer._apply_short_content_cap.__get__(self)
        )


class TestContentLengthIsNullSafe:
    """The stamp runs on every scored article — a malformed row must not raise."""

    def test_null_text_falls_back_to_content(self):
        article = {"title": "t", "text": None, "content": LONG_CONTENT}
        assert BasePreFilter.content_length(article) == len(LONG_CONTENT)

    def test_empty_text_falls_back_to_content(self):
        article = {"title": "t", "text": "", "content": LONG_CONTENT}
        assert BasePreFilter.content_length(article) == len(LONG_CONTENT)

    def test_no_content_fields_stamps_zero(self):
        assert BasePreFilter.content_length({"title": "t"}) == 0


class TestStampAlways:
    def test_length_stamped_on_result(self):
        scorer = _FakeScorer()
        result = scorer._create_empty_result()
        scorer._stamp_content_length(_article(SHORT_CONTENT), result)
        assert result["content_length"] == len(SHORT_CONTENT)

    def test_empty_result_declares_the_fields(self):
        result = _FakeScorer()._create_empty_result()
        assert result["content_length"] is None
        assert result["short_content_cap_applied"] is False


class TestShortContentCap:
    def test_off_by_default(self):
        scorer = _FakeScorer(cap=None)
        result = scorer._create_empty_result()
        scorer._stamp_content_length(_article(SHORT_CONTENT), result)
        assert scorer._apply_short_content_cap(7.5, result) == 7.5
        assert result["short_content_cap_applied"] is False

    def test_caps_short_content_when_configured(self):
        scorer = _FakeScorer(cap=2.0)
        result = scorer._create_empty_result()
        scorer._stamp_content_length(_article(SHORT_CONTENT), result)
        assert scorer._apply_short_content_cap(7.5, result) == 2.0
        assert result["short_content_cap_applied"] is True

    def test_leaves_long_content_alone(self):
        scorer = _FakeScorer(cap=2.0)
        result = scorer._create_empty_result()
        scorer._stamp_content_length(_article(LONG_CONTENT), result)
        assert scorer._apply_short_content_cap(7.5, result) == 7.5
        assert result["short_content_cap_applied"] is False

    def test_cap_does_not_raise_a_low_score(self):
        """A cap is a ceiling, never a floor."""
        scorer = _FakeScorer(cap=2.0)
        result = scorer._create_empty_result()
        scorer._stamp_content_length(_article(SHORT_CONTENT), result)
        assert scorer._apply_short_content_cap(0.4, result) == 0.4
        assert result["short_content_cap_applied"] is False

    def test_unstamped_result_is_never_capped(self):
        """No stamp means no decision — fail open, not on a missing field."""
        scorer = _FakeScorer(cap=2.0)
        result = scorer._create_empty_result()
        assert scorer._apply_short_content_cap(7.5, result) == 7.5
        assert result["short_content_cap_applied"] is False


class TestHybridStage1Branch:
    """HybridScorer's Stage-1 branch builds its own result dict.

    That branch bypasses `score_batch`/`_process_raw_scores` entirely, so it
    needs its own stamp and its own call into the cap — the two lines #93 added
    there. A regression would be silent: scores would simply stop being capped
    for whichever articles the probe resolves early, which on solutions v6 is
    most of them.
    """

    def _hybrid(self, cap=None):
        from filters.common.hybrid_scorer import HybridScorer

        stage2 = _FakeScorer(cap=cap)
        stage2.DIMENSION_NAMES = ["a", "b"]
        stage2.TIER_THRESHOLDS = [("high", 4.0, "high"), ("low", 0.0, "low")]
        stage2.prefilter = None
        stage2._validate_article = lambda article: None
        stage2._assign_tier = lambda avg: (
            ("high", "high") if avg >= 4.0 else ("low", "low")
        )

        class _ConcreteHybrid(HybridScorer):
            # HybridScorer is an ABC; __new__ still refuses the abstract base.
            def _create_stage2_scorer(self):  # pragma: no cover - not reached
                return stage2

            def _get_embedding_stage_config(self):  # pragma: no cover
                return {"threshold": 3.0}

        # __new__ rather than __init__: the real constructor builds an
        # EmbeddingStage, which loads a sentence-transformer. The branch under
        # test is score_batch's, not the probe's.
        hybrid = _ConcreteHybrid.__new__(_ConcreteHybrid)
        hybrid.device_str = "cpu"
        hybrid.use_prefilter = False
        hybrid.stage2_scorer = stage2
        hybrid.threshold = 3.0
        hybrid.embedding_stage = _FakeEmbeddingStage(weighted_avg=6.0)
        return hybrid

    def test_stage1_stamps_content_length(self):
        hybrid = self._hybrid()
        results = hybrid.score_batch([_article(SHORT_CONTENT), _article(LONG_CONTENT)])
        assert [r["content_length"] for r in results] == [
            len(SHORT_CONTENT),
            len(LONG_CONTENT),
        ]

    def test_stage1_uncapped_by_default(self):
        results = self._hybrid().score_batch([_article(SHORT_CONTENT)])
        assert results[0]["weighted_average"] == 6.0
        assert results[0]["short_content_cap_applied"] is False

    def test_stage1_honours_the_cap(self):
        results = self._hybrid(cap=2.0).score_batch(
            [_article(SHORT_CONTENT), _article(LONG_CONTENT)]
        )
        short, long_ = results
        assert short["weighted_average"] == 2.0
        assert short["short_content_cap_applied"] is True
        assert long_["weighted_average"] == 6.0
        assert long_["short_content_cap_applied"] is False

    def test_stage1_tier_follows_the_capped_score(self):
        results = self._hybrid(cap=2.0).score_batch([_article(SHORT_CONTENT)])
        assert results[0]["tier"] == "low"

    def test_stage1_estimate_keeps_the_uncapped_probe_value(self):
        """The probe's own number is provenance — capping must not rewrite it."""
        results = self._hybrid(cap=2.0).score_batch([_article(SHORT_CONTENT)])
        assert results[0]["stage1_estimate"] == 6.0


class _FakeEmbeddingStage:
    """Resolves every article at Stage 1, above any cap under test."""

    def __init__(self, weighted_avg):
        self.weighted_avg = weighted_avg

    def screen_batch(self, articles, batch_size=None):
        from filters.common.embedding_stage import ScreeningResult

        return [
            ScreeningResult(
                needs_stage2=False,
                weighted_avg=self.weighted_avg,
                scores={"a": self.weighted_avg, "b": self.weighted_avg},
            )
            for _ in articles
        ]


def _load_prefilter(module_path: str, class_name):
    """Load a filter-package prefilter the way batch_scorer does."""
    import importlib.util

    root = Path(__file__).parent.parent.parent
    path = root / module_path
    spec = importlib.util.spec_from_file_location("prefilter_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if class_name:
        return getattr(module, class_name)()

    candidates = [
        obj
        for name, obj in vars(module).items()
        if isinstance(obj, type)
        and issubclass(obj, BasePreFilter)
        and obj.__module__ == module.__name__
    ]
    assert candidates, f"no prefilter class found in {module_path}"
    return candidates[0]()
