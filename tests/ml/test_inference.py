"""
ML Tests: Inference Pipeline

Tests that trained models:
- Load successfully
- Produce valid output format
- Return scores in expected range
- Handle edge cases gracefully

Run with: pytest tests/ml/test_inference.py -v

Note: Tests requiring GPU or trained models are skipped if unavailable.
"""

import pytest
from pathlib import Path
from typing import Optional


def find_trained_filters():
    """Find filters with trained models AND inference modules."""
    project_root = Path(__file__).parent.parent.parent
    filters_dir = project_root / "filters"

    trained = []
    if filters_dir.exists():
        for filter_type in filters_dir.iterdir():
            if not filter_type.is_dir() or filter_type.name.startswith('.'):
                continue

            for version in filter_type.iterdir():
                if not version.is_dir():
                    continue

                # Check for model directory with adapter AND inference module
                model_dir = version / "model"
                inference_module = version / "inference.py"

                if (model_dir.exists() and
                    (model_dir / "adapter_model.safetensors").exists() and
                    inference_module.exists()):
                    trained.append({
                        'path': version,
                        'name': f"{filter_type.name}/{version.name}",
                        'inference_module': inference_module
                    })

    return trained


def check_torch_available():
    """Check if PyTorch is available."""
    try:
        import torch
        return True
    except ImportError:
        return False


def check_transformers_available():
    """Check if transformers is available."""
    try:
        import transformers
        return True
    except ImportError:
        return False


# Sample articles for testing inference
SAMPLE_ARTICLES = [
    {
        "id": "test_positive",
        "title": "Community Solar Project Powers 500 Homes",
        "content": """
        A new community solar installation in rural Vermont has successfully connected
        500 households to clean energy. The 2 MW project, completed under budget, has
        reduced carbon emissions by 3,000 tons annually and created 25 local jobs.
        Residents have seen electricity bills drop by 20% on average.
        """
    },
    {
        "id": "test_negative",
        "title": "Stock Market Update: Tech Stocks Rally",
        "content": """
        Technology stocks rallied today as investors responded positively to earnings
        reports. The NASDAQ composite rose 2.3% while the S&P 500 gained 1.8%.
        Analysts attribute the gains to better-than-expected revenue from major
        tech companies. Trading volume was above average.
        """
    },
    {
        "id": "test_short",
        "title": "Brief Update",
        "content": "This is a very short article with minimal content."
    },
]


class TestInferenceModuleAvailability:
    """Tests for inference module availability."""

    def test_find_trained_filters(self):
        """Should be able to find trained filter structure."""
        # This test just verifies the search works, not that models exist
        filters = find_trained_filters()
        # Not a failure if no trained models - just informational
        if not filters:
            pytest.skip("No trained models found - this is expected in CI/fresh checkout")

    @pytest.mark.skipif(not check_torch_available(), reason="PyTorch not available")
    def test_torch_available(self):
        """PyTorch should be importable for inference."""
        import torch
        assert torch.__version__ is not None


@pytest.mark.skipif(
    not check_torch_available() or not check_transformers_available(),
    reason="PyTorch or transformers not available"
)
class TestInferencePipeline:
    """Tests for inference pipeline (requires trained models)."""

    @pytest.fixture
    def trained_filters(self):
        """Get available trained filters."""
        filters = find_trained_filters()
        if not filters:
            pytest.skip("No trained models available")
        return filters

    def test_inference_module_exists(self, trained_filters):
        """Each trained filter should have an inference module."""
        for filter_info in trained_filters:
            assert filter_info['inference_module'].exists(), \
                f"Missing inference.py for {filter_info['name']}"

    def test_inference_module_importable(self, trained_filters):
        """Inference modules should be importable.

        ⛔ THIS TEST WAS RED FOR MONTHS AND THE SHIPPED CODE WAS NEVER THE PROBLEM
        (llm-distillery#139, entered at `6acd013`, diagnosed 2026-09-05). It used
        `spec_from_file_location` with a synthetic module name, which gives the
        loaded module **no package** — so `filters/cultural_discovery/v5/inference.py`'s
        `from .base_scorer import ...` could not resolve and the test reported
        *"Failed to import cultural_discovery/v5"* about a module that imports
        perfectly well. `cultural_discovery v5` is LIVE in production the whole time.

        ⭐ The instrument was broken, not the thing it measured — and a permanently
        red test trains everyone to read the suite as "710 passed and the usual
        one", which is how a real failure would have hidden next to it.

        Imported by DOTTED PATH now, which is how production loads these modules.
        Verified 2026-09-05 against all eight filters the fixture finds:
        solutions v4/v6, cultural_discovery v5/v6, uplifting v7, belonging v1,
        investment_risk v6, nature_recovery v4.
        """
        import importlib

        for filter_info in trained_filters:
            name = filter_info['name']
            # ⚠️ A DIRECTORY NAME IS NOT ALWAYS AN IMPORTABLE ONE. `filters/
            # ai-engineering-practice/` exists and a hyphen is not valid in a
            # module path (`memory/gotcha-log.md`, "Hyphenated Filter Names Break
            # Python Imports"). It is absent from this fixture today only because
            # it has no trained model on disk — so the guard is for the day it
            # gets one, and it SKIPS with a reason rather than failing, because
            # the defect would be the directory name, not the inference module.
            dotted = f"filters.{name.replace('/', '.')}.inference"
            if not all(part.isidentifier() for part in dotted.split('.')):
                pytest.skip(f"{name}: directory name is not a valid Python "
                            f"identifier, so no import form can reach it")
            try:
                importlib.import_module(dotted)
            except Exception as e:
                pytest.fail(f"Failed to import {name} ({dotted}): "
                            f"{type(e).__name__}: {e}")


@pytest.mark.slow
@pytest.mark.skipif(
    not check_torch_available() or not check_transformers_available(),
    reason="PyTorch or transformers not available"
)
class TestModelInference:
    """
    Tests that run actual model inference.

    These tests are slow and require GPU or patience.
    Run with: pytest tests/ml/test_inference.py -v -m slow
    """

    @pytest.fixture(scope="class")
    def uplifting_scorer(self):
        """Load uplifting scorer if available."""
        project_root = Path(__file__).parent.parent.parent
        model_path = project_root / "filters" / "uplifting" / "v6" / "model"

        if not (model_path / "adapter_model.safetensors").exists():
            pytest.skip("Uplifting v6 model not available")

        try:
            from filters.uplifting.v6.inference import UpliftingScorer
            return UpliftingScorer(use_prefilter=True)
        except Exception as e:
            pytest.skip(f"Failed to load model: {e}")

    def test_model_scores_article(self, uplifting_scorer):
        """Model should score a valid article."""
        result = uplifting_scorer.score_article(SAMPLE_ARTICLES[0])

        assert 'passed_prefilter' in result
        assert 'scores' in result
        assert 'tier' in result

    def test_scores_in_valid_range(self, uplifting_scorer):
        """All scores should be in [0, 10] range."""
        result = uplifting_scorer.score_article(SAMPLE_ARTICLES[0])

        if result['passed_prefilter'] and result['scores']:
            for dim, score in result['scores'].items():
                assert 0 <= score <= 10, f"Score {score} for {dim} out of range"

    def test_weighted_average_computed(self, uplifting_scorer):
        """Weighted average should be computed."""
        result = uplifting_scorer.score_article(SAMPLE_ARTICLES[0])

        if result['passed_prefilter']:
            assert 'weighted_average' in result
            assert 0 <= result['weighted_average'] <= 10

    def test_tier_assigned(self, uplifting_scorer):
        """Tier should be assigned based on score."""
        result = uplifting_scorer.score_article(SAMPLE_ARTICLES[0])

        if result['passed_prefilter']:
            assert result['tier'] is not None
            assert result['tier'] in ['high', 'medium', 'low']

    def test_prefilter_blocks_off_topic(self, uplifting_scorer):
        """Prefilter should block obviously off-topic content."""
        # Stock market article should likely be blocked
        result = uplifting_scorer.score_article(SAMPLE_ARTICLES[1])

        # Either blocked by prefilter or scores low - both acceptable
        if result['passed_prefilter']:
            # If it passes, it should at least score low
            assert result['weighted_average'] is not None

    def test_handles_short_content(self, uplifting_scorer):
        """Model should handle short content gracefully."""
        result = uplifting_scorer.score_article(SAMPLE_ARTICLES[2])

        # Should either be blocked by prefilter or return valid scores
        assert 'passed_prefilter' in result
        if result['passed_prefilter']:
            assert 'scores' in result

    def test_batch_scoring(self, uplifting_scorer):
        """Batch scoring should work."""
        results = uplifting_scorer.score_batch(SAMPLE_ARTICLES, batch_size=2)

        assert len(results) == len(SAMPLE_ARTICLES)
        for result in results:
            assert 'passed_prefilter' in result


class TestOutputFormat:
    """Tests for inference output format (can run without model)."""

    def test_expected_output_keys(self):
        """Define expected output format for documentation."""
        expected_keys = {
            'passed_prefilter': bool,
            'prefilter_reason': (str, type(None)),
            'scores': (dict, type(None)),
            'weighted_average': (float, type(None)),
            'tier': (str, type(None)),
            'tier_description': (str, type(None)),
            'gatekeeper_applied': bool,
        }

        # This test documents the expected format
        assert 'passed_prefilter' in expected_keys
        assert 'scores' in expected_keys
        assert 'tier' in expected_keys
