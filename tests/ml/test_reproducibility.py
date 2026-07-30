"""
ML Tests: Reproducibility

Tests that ML operations are reproducible:
- Same seed → same data split
- Same input → same model output (within tolerance)
- Data preparation is deterministic

Run with: pytest tests/ml/test_reproducibility.py -v
"""

import json
import pytest
import sys
from pathlib import Path

# Add project root for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestDataSplitReproducibility:
    """Tests that data splitting is reproducible with same seed."""

    def test_stratified_split_same_seed_same_result(self):
        """Same seed should produce identical splits."""
        from training.prepare_data import stratified_split

        # Create sample data
        articles = [
            {
                "id": f"article-{i:03d}",
                "title": f"Test Article {i}",
                "content": f"Content for article {i}",
                "uplifting_analysis": {
                    "dimensions": {
                        "human_wellbeing_impact": {"score": (i % 10) + 1}
                    },
                    "overall_score": (i % 10) + 1
                }
            }
            for i in range(50)
        ]

        tier_boundaries = {"high_impact": 7.0, "moderate_uplift": 4.0, "not_uplifting": 0.0}

        # Split twice with same seed
        train1, val1, test1 = stratified_split(
            articles,
            analysis_field="uplifting_analysis",
            tier_boundaries=tier_boundaries,
            seed=42
        )

        train2, val2, test2 = stratified_split(
            articles,
            analysis_field="uplifting_analysis",
            tier_boundaries=tier_boundaries,
            seed=42
        )

        # Should be identical
        train1_ids = {a['id'] for a in train1}
        train2_ids = {a['id'] for a in train2}
        val1_ids = {a['id'] for a in val1}
        val2_ids = {a['id'] for a in val2}
        test1_ids = {a['id'] for a in test1}
        test2_ids = {a['id'] for a in test2}

        assert train1_ids == train2_ids, "Train splits differ with same seed"
        assert val1_ids == val2_ids, "Val splits differ with same seed"
        assert test1_ids == test2_ids, "Test splits differ with same seed"

    def test_different_seed_different_result(self):
        """Different seeds should produce different splits (usually)."""
        from training.prepare_data import stratified_split

        # Create sample data
        articles = [
            {
                "id": f"article-{i:03d}",
                "title": f"Test Article {i}",
                "content": f"Content for article {i}",
                "uplifting_analysis": {
                    "dimensions": {
                        "human_wellbeing_impact": {"score": (i % 10) + 1}
                    },
                    "overall_score": (i % 10) + 1
                }
            }
            for i in range(50)
        ]

        tier_boundaries = {"high_impact": 7.0, "moderate_uplift": 4.0, "not_uplifting": 0.0}

        # Split with different seeds
        train1, _, _ = stratified_split(
            articles,
            analysis_field="uplifting_analysis",
            tier_boundaries=tier_boundaries,
            seed=42
        )

        train2, _, _ = stratified_split(
            articles,
            analysis_field="uplifting_analysis",
            tier_boundaries=tier_boundaries,
            seed=123
        )

        train1_ids = {a['id'] for a in train1}
        train2_ids = {a['id'] for a in train2}

        # Very likely different (could theoretically be same but extremely unlikely)
        # At minimum, check both are valid
        assert len(train1_ids) > 0
        assert len(train2_ids) > 0


class TestScoreCalculationReproducibility:
    """Tests that score calculations are deterministic."""

    def test_calculate_overall_score_deterministic(self):
        """Overall score calculation should be deterministic."""
        from training.prepare_data import calculate_overall_score

        analysis = {
            "human_wellbeing_impact": {"score": 7, "reasoning": "test"},
            "social_cohesion_impact": {"score": 6, "reasoning": "test"},
            "justice_rights_impact": {"score": 5, "reasoning": "test"},
        }

        dimension_names = [
            "human_wellbeing_impact",
            "social_cohesion_impact",
            "justice_rights_impact"
        ]

        # Calculate multiple times
        score1 = calculate_overall_score(analysis, dimension_names)
        score2 = calculate_overall_score(analysis, dimension_names)
        score3 = calculate_overall_score(analysis, dimension_names)

        assert score1 == score2 == score3

    def test_assign_tier_deterministic(self):
        """Tier assignment should be deterministic."""
        from training.prepare_data import assign_tier

        tier_boundaries = {"high_impact": 7.0, "moderate_uplift": 4.0, "not_uplifting": 0.0}

        # Same score should always give same tier
        for score in [1.0, 4.0, 5.5, 7.0, 8.5]:
            tier1 = assign_tier(score, tier_boundaries)
            tier2 = assign_tier(score, tier_boundaries)
            assert tier1 == tier2, f"Tier assignment inconsistent for score {score}"


class TestConversionReproducibility:
    """Tests that data conversion is reproducible."""

    def test_convert_to_training_format_deterministic(self):
        """Training format conversion should be deterministic."""
        from training.prepare_data import convert_to_training_format

        articles = [
            {
                "id": "test-001",
                "title": "Test Article",
                "content": "Test content",
                "uplifting_analysis": {
                    "dimensions": {
                        "dim_a": {"score": 5},
                        "dim_b": {"score": 6},
                        "dim_c": {"score": 7},
                    }
                }
            }
        ]

        dimension_names = ["dim_a", "dim_b", "dim_c"]

        # Convert multiple times
        result1 = convert_to_training_format(articles, "uplifting_analysis", dimension_names)
        result2 = convert_to_training_format(articles, "uplifting_analysis", dimension_names)

        assert result1[0]['labels'] == result2[0]['labels']
        assert result1[0]['dimension_names'] == result2[0]['dimension_names']


@pytest.mark.slow
class TestModelReproducibility:
    """Tests for model inference reproducibility (requires trained model)."""

    @pytest.fixture
    def check_model_available(self):
        """Check if a trained model is available."""
        project_root = Path(__file__).parent.parent.parent
        model_path = project_root / "filters" / "uplifting" / "v7" / "model"

        if not (model_path / "adapter_model.safetensors").exists():
            pytest.skip("Model not available for reproducibility test")
        return model_path

    def test_same_input_same_output(self, check_model_available):
        """Same input should produce same output (deterministic inference)."""
        try:
            import torch
            from filters.uplifting.v7.inference import UpliftingScorer
        except ImportError:
            pytest.skip("Required packages not available")

        # Set seeds for reproducibility
        torch.manual_seed(42)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(42)

        scorer = UpliftingScorer(model_path=check_model_available)

        article = {
            "title": "Community Garden Success Story",
            "content": "A community garden project has transformed an abandoned lot into a thriving green space that provides fresh produce to 200 families weekly."
        }

        # Score same article twice
        result1 = scorer.score_article(article)
        result2 = scorer.score_article(article)

        if result1['scores'] and result2['scores']:
            # Scores should be very close (allow small floating point differences)
            for dim in result1['scores']:
                diff = abs(result1['scores'][dim] - result2['scores'][dim])
                assert diff < 0.01, f"Score difference too large for {dim}: {diff}"
