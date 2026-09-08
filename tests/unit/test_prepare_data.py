"""
Unit tests for training/prepare_data.py

Tests the training data preparation functions:
- load_labels(): JSONL loading
- stratified_split(): Data splitting with stratification
- convert_to_training_format(): Format conversion
- calculate_overall_score(): Score calculation
- assign_tier(): Tier assignment
"""

import json
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from training.prepare_data import (
    load_labels,
    stratified_split,
    convert_to_training_format,
    calculate_overall_score,
    assign_tier,
    assign_score_bin,
    get_analysis_field_name,
)


class TestLoadLabels:
    """Tests for load_labels()"""

    def test_load_single_file(self, temp_jsonl_file):
        """Should load all articles from single JSONL file."""
        labels = load_labels(temp_jsonl_file)
        assert len(labels) == 8  # Based on labeled_articles fixture
        assert all("id" in label for label in labels)

    def test_load_nonexistent_file(self, temp_dir):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_labels(temp_dir / "nonexistent.jsonl")

    def test_load_empty_file(self, temp_dir):
        """Should return empty list for empty file."""
        empty_file = temp_dir / "empty.jsonl"
        empty_file.touch()
        labels = load_labels(empty_file)
        assert labels == []

    def test_load_with_blank_lines(self, temp_dir):
        """Should skip blank lines in JSONL."""
        file_path = temp_dir / "with_blanks.jsonl"
        with open(file_path, 'w') as f:
            f.write('{"id": "1", "title": "Test", "content": "Content"}\n')
            f.write('\n')  # Blank line
            f.write('{"id": "2", "title": "Test2", "content": "Content2"}\n')
            f.write('   \n')  # Whitespace line
        labels = load_labels(file_path)
        assert len(labels) == 2


class TestCalculateOverallScore:
    """Tests for calculate_overall_score()"""

    def test_explicit_overall_score(self, sample_oracle_analysis):
        """Should use explicit overall_score if present."""
        score = calculate_overall_score(sample_oracle_analysis)
        assert score == 6.5

    def test_calculate_from_dimensions_nested(self, sample_oracle_analysis):
        """Should calculate from nested dimensions if no overall_score."""
        analysis = sample_oracle_analysis.copy()
        del analysis["overall_score"]
        # Get dimension names (excluding overall_score which we just deleted)
        dimension_names = [k for k in analysis.keys()]
        score = calculate_overall_score(analysis, dimension_names)
        # Scores: 7, 6, 5, 8, 6, 7 = 39/6 = 6.5
        assert abs(score - 6.5) < 0.1  # Allow some tolerance

    def test_calculate_from_dimensions_flat(self, sample_oracle_analysis_flat):
        """Should calculate from flat dimensions if no overall_score."""
        analysis = sample_oracle_analysis_flat.copy()
        del analysis["overall_score"]
        dimension_names = [k for k in analysis.keys()]
        score = calculate_overall_score(analysis, dimension_names)
        assert score > 0

    def test_empty_analysis(self):
        """Should return 0 for empty analysis."""
        score = calculate_overall_score({})
        assert score == 0.0


class TestAssignTier:
    """Tests for assign_tier()"""

    def test_high_tier(self, uplifting_tier_boundaries):
        """Score >= 7.0 should be high_impact."""
        tier = assign_tier(8.5, uplifting_tier_boundaries)
        assert tier == "high_impact"

        tier = assign_tier(7.0, uplifting_tier_boundaries)
        assert tier == "high_impact"

    def test_medium_tier(self, uplifting_tier_boundaries):
        """Score >= 4.0 and < 7.0 should be moderate_uplift."""
        tier = assign_tier(6.9, uplifting_tier_boundaries)
        assert tier == "moderate_uplift"

        tier = assign_tier(4.0, uplifting_tier_boundaries)
        assert tier == "moderate_uplift"

    def test_low_tier(self, uplifting_tier_boundaries):
        """Score < 4.0 should be not_uplifting."""
        tier = assign_tier(3.9, uplifting_tier_boundaries)
        assert tier == "not_uplifting"

        tier = assign_tier(0.0, uplifting_tier_boundaries)
        assert tier == "not_uplifting"

    def test_boundary_values(self, uplifting_tier_boundaries):
        """Boundary values should go to higher tier."""
        assert assign_tier(7.0, uplifting_tier_boundaries) == "high_impact"
        assert assign_tier(4.0, uplifting_tier_boundaries) == "moderate_uplift"
        assert assign_tier(0.0, uplifting_tier_boundaries) == "not_uplifting"


class TestAssignScoreBin:
    """Tests for assign_score_bin()"""

    def test_very_high_bin(self):
        """Score >= 8.0 should be very_high."""
        assert assign_score_bin(10.0) == "very_high"
        assert assign_score_bin(8.0) == "very_high"
        assert assign_score_bin(8.5) == "very_high"

    def test_high_bin(self):
        """Score >= 6.0 and < 8.0 should be high."""
        assert assign_score_bin(7.9) == "high"
        assert assign_score_bin(6.0) == "high"

    def test_medium_bin(self):
        """Score >= 4.0 and < 6.0 should be medium."""
        assert assign_score_bin(5.9) == "medium"
        assert assign_score_bin(4.0) == "medium"

    def test_low_bin(self):
        """Score >= 2.0 and < 4.0 should be low."""
        assert assign_score_bin(3.9) == "low"
        assert assign_score_bin(2.0) == "low"

    def test_very_low_bin(self):
        """Score < 2.0 should be very_low."""
        assert assign_score_bin(1.9) == "very_low"
        assert assign_score_bin(0.0) == "very_low"


class TestStratifiedSplit:
    """Tests for stratified_split()"""

    def test_split_ratios(self, labeled_articles, uplifting_tier_boundaries, uplifting_dimension_names):
        """Split should approximately match requested ratios."""
        train, val, test = stratified_split(
            labeled_articles,
            analysis_field="uplifting_analysis",
            tier_boundaries=uplifting_tier_boundaries,
            dimension_names=uplifting_dimension_names,
            train_ratio=0.8,
            val_ratio=0.1,
            test_ratio=0.1,
            seed=42
        )

        total = len(labeled_articles)
        # Allow some variance due to small sample size
        assert len(train) >= int(total * 0.6)  # At least 60%
        assert len(train) + len(val) + len(test) == total

    def test_no_data_leakage(self, labeled_articles, uplifting_tier_boundaries, uplifting_dimension_names):
        """Same article should not appear in multiple splits."""
        train, val, test = stratified_split(
            labeled_articles,
            analysis_field="uplifting_analysis",
            tier_boundaries=uplifting_tier_boundaries,
            dimension_names=uplifting_dimension_names
        )

        train_ids = {a["id"] for a in train}
        val_ids = {a["id"] for a in val}
        test_ids = {a["id"] for a in test}

        # No overlap between sets
        assert len(train_ids & val_ids) == 0
        assert len(train_ids & test_ids) == 0
        assert len(val_ids & test_ids) == 0

    def test_reproducible_with_seed(self, labeled_articles, uplifting_tier_boundaries, uplifting_dimension_names):
        """Same seed should produce same split."""
        split1 = stratified_split(
            labeled_articles,
            analysis_field="uplifting_analysis",
            tier_boundaries=uplifting_tier_boundaries,
            seed=42
        )
        split2 = stratified_split(
            labeled_articles,
            analysis_field="uplifting_analysis",
            tier_boundaries=uplifting_tier_boundaries,
            seed=42
        )

        # Same articles in each split
        train1_ids = {a["id"] for a in split1[0]}
        train2_ids = {a["id"] for a in split2[0]}
        assert train1_ids == train2_ids

    def test_different_seed_different_split(self, labeled_articles, uplifting_tier_boundaries):
        """Different seeds should produce different splits."""
        split1 = stratified_split(
            labeled_articles,
            analysis_field="uplifting_analysis",
            tier_boundaries=uplifting_tier_boundaries,
            seed=42
        )
        split2 = stratified_split(
            labeled_articles,
            analysis_field="uplifting_analysis",
            tier_boundaries=uplifting_tier_boundaries,
            seed=123
        )

        train1_ids = {a["id"] for a in split1[0]}
        train2_ids = {a["id"] for a in split2[0]}
        # Very likely different (could be same by chance but unlikely)
        # Just check they're not obviously broken
        assert len(train1_ids) > 0
        assert len(train2_ids) > 0

    def test_empty_tier_boundaries_uses_score_bins(self, labeled_articles, uplifting_dimension_names):
        """Empty tier_boundaries should use score bin stratification."""
        train, val, test = stratified_split(
            labeled_articles,
            analysis_field="uplifting_analysis",
            tier_boundaries={},  # Empty = use score bins
            dimension_names=uplifting_dimension_names
        )
        assert len(train) + len(val) + len(test) == len(labeled_articles)


class TestConvertToTrainingFormat:
    """Tests for convert_to_training_format()"""

    def test_basic_conversion(self, labeled_articles, uplifting_dimension_names):
        """Should convert articles to training format."""
        training_data = convert_to_training_format(
            labeled_articles,
            analysis_field="uplifting_analysis",
            dimension_names=uplifting_dimension_names
        )

        assert len(training_data) == len(labeled_articles)
        for item in training_data:
            assert "id" in item
            assert "title" in item
            assert "content" in item
            assert "labels" in item
            assert "dimension_names" in item
            assert len(item["labels"]) == len(uplifting_dimension_names)

    def test_labels_are_numeric_array(self, labeled_articles, uplifting_dimension_names):
        """Labels should be a list of numbers."""
        training_data = convert_to_training_format(
            labeled_articles,
            analysis_field="uplifting_analysis",
            dimension_names=uplifting_dimension_names
        )

        for item in training_data:
            assert isinstance(item["labels"], list)
            assert all(isinstance(score, (int, float)) for score in item["labels"])

    def test_dimension_order_preserved(self, labeled_articles, uplifting_dimension_names):
        """Dimension order in labels should match dimension_names."""
        training_data = convert_to_training_format(
            labeled_articles,
            analysis_field="uplifting_analysis",
            dimension_names=uplifting_dimension_names
        )

        # The dimension_names field should match input
        assert training_data[0]["dimension_names"] == uplifting_dimension_names

    def test_skips_articles_without_analysis(self, valid_article, uplifting_dimension_names):
        """Articles without analysis should be skipped."""
        articles = [
            valid_article,  # No analysis
            {**valid_article, "id": "with-analysis", "uplifting_analysis": {"dimensions": {}}}
        ]

        training_data = convert_to_training_format(
            articles,
            analysis_field="uplifting_analysis",
            dimension_names=uplifting_dimension_names
        )

        # Only the article with analysis should be included
        assert len(training_data) == 1
        assert training_data[0]["id"] == "with-analysis"

    def test_handles_nested_dimension_format(self, uplifting_dimension_names):
        """Should handle nested dimension format (score + reasoning)."""
        article = {
            "id": "nested-test",
            "title": "Test",
            "content": "Content",
            "uplifting_analysis": {
                "dimensions": {
                    dim: {"score": 5 + i, "reasoning": "test"}
                    for i, dim in enumerate(uplifting_dimension_names)
                }
            }
        }

        training_data = convert_to_training_format(
            [article],
            analysis_field="uplifting_analysis",
            dimension_names=uplifting_dimension_names
        )

        assert len(training_data) == 1
        # First dimension should have score 5, second 6, etc.
        assert training_data[0]["labels"][0] == 5
        assert training_data[0]["labels"][1] == 6


class TestGetAnalysisFieldName:
    """Tests for get_analysis_field_name()"""

    def test_simple_filter_name(self):
        """Simple filter name should get _analysis suffix."""
        assert get_analysis_field_name("uplifting") == "uplifting_analysis"

    def test_compound_filter_name(self):
        """Compound filter name should get _analysis suffix."""
        assert get_analysis_field_name("investment_risk") == "investment_risk_analysis"
        assert get_analysis_field_name("sustainability_tech") == "sustainability_tech_analysis"


class TestNoSilentFieldDrop:
    """The oracle's non-dimensional output must survive the split (#155).

    `scope_verdict` was produced at label time and destroyed at split time for
    the whole of human_thriving v8 -- present on all 6,586 label rows, absent
    from every split file, with nothing printed. These tests fail if any field
    the oracle emitted stops reaching the training records, whatever it is
    called: they enumerate the input rather than an allowlist, so a new oracle
    field is covered the day it appears.
    """

    # The real label file carries TWO analysis shapes, measured 2026-09-08 over
    # all 6,586 rows of datasets/scored/human_thriving_v8/labels_v84_merged.jsonl:
    #   6,130 rows -- 20 keys, dimensions are float,          runs is a LIST
    #     456 rows -- 19 keys, dimensions are {"score": ...},  runs is an INT
    # An earlier version of this fixture carried 12 scalar keys and called itself
    # "shaped like" that file. It was not: it omitted every non-scalar value, so a
    # type-conditional drop (`if not isinstance(v, list)`) passed all six tests
    # while losing scope_verdicts_per_run on 6,586/6,586 real rows -- #155's own
    # failure mode one level up, the check unable to see the fields most at risk.
    # Both shapes are reproduced below, and test_real_corpus_row_survives reads
    # the actual file when it is present.

    @staticmethod
    def _v8_shaped_label():
        """The MAJORITY real shape: 20 analysis keys, float dimensions, runs a list."""
        return {
            "id": "ht-1",
            "title": "Flood response in Bihar",
            "url": "https://example.org/a",
            "content": "Community kitchens and boat ambulances.",
            "source": "example.org",
            "published_date": "2026-09-01",
            "language": "en",
            "human_thriving_analysis": {
                "human_wellbeing_impact": 8.0,
                "social_cohesion_impact": 7.0,
                "justice_rights_impact": 6.0,
                "evidence_level": 5.0,
                "benefit_distribution": 4.0,
                "change_durability": 3.0,
                "scope_verdict": "harm_is_subject",
                "scope_flipped": False,
                "scope_verdicts_per_run": ["harm_is_subject"] * 3,
                "dominant_subject": "a flood",
                "content_type": "news",
                "weighted_mean_all": 5.5,
                "weighted_mean_major": 5.5,
                "aggregate_used": "all",
                "k": 3,
                "runs": [{"scope_verdict": "harm_is_subject"} for _ in range(3)],
                "filter_version": "8.0-deepseek",
                "analyzed_by": "deepseek-deepseek-chat",
                "prompt_hash": "003cd35a5122",
                "prompt_file": "filters/human_thriving/v8/prompt-v8-4.md",
            },
        }

    @staticmethod
    def _v8_minority_shape_label():
        """The 456-row real shape: dimensions are {"score": ...}, runs is an INT.

        `runs` means two different things across one file, which is why
        oracle_meta is documented as heterogeneous rather than as a schema.
        """
        return {
            "id": "ht-2",
            "title": "Edge-AI framework for agricultural support",
            "url": "https://example.org/b",
            "content": "A research paper.",
            "source": "example.org",
            "published_date": "2026-09-02",
            "language": "en",
            "human_thriving_analysis": {
                "human_wellbeing_impact": {"score": 5.0},
                "social_cohesion_impact": {"score": 2.1667},
                "justice_rights_impact": {"score": 1.8333},
                "evidence_level": {"score": 4.5},
                "benefit_distribution": {"score": 4.3333},
                "change_durability": {"score": 4.0},
                "scope_verdict": "in_scope",
                "scope_flipped": True,
                "scope_verdicts_per_run": ["in_scope"] * 4 + ["out_of_scope"] * 2,
                "dominant_subject": "a research paper",
                "content_type": "solutions_story",
                "weighted_mean_all": 3.6917,
                "aggregate_used": "all",
                "k": 6,
                "runs": 6,
                "filter_version": "8.0-deepseek",
                "analyzed_by": "deepseek-deepseek-chat",
                "prompt_hash": "c4705408c477",
                "prompt_file": "filters/human_thriving/v8/prompt-v8-4.md",
            },
        }

    @property
    def _dims(self):
        return [
            "human_wellbeing_impact",
            "social_cohesion_impact",
            "justice_rights_impact",
            "evidence_level",
            "benefit_distribution",
            "change_durability",
        ]

    def _convert(self):
        label = self._v8_shaped_label()
        record = convert_to_training_format(
            [label],
            analysis_field="human_thriving_analysis",
            dimension_names=self._dims,
        )[0]
        return label, record

    def test_scope_verdict_reaches_the_split(self):
        """The specific field #155 is about, read the way a gate trainer would."""
        _, record = self._convert()
        assert record["oracle_meta"]["scope_verdict"] == "harm_is_subject"

    def test_every_analysis_field_reaches_the_split(self):
        """No key of the analysis block may be dropped -- enumerated, not allowlisted."""
        label, record = self._convert()
        analysis = label["human_thriving_analysis"]
        missing = [k for k in analysis if k not in record["oracle_meta"]]
        assert missing == [], f"analysis fields dropped at split time: {missing}"
        for key, value in analysis.items():
            assert record["oracle_meta"][key] == value

    def test_every_source_field_reaches_the_split(self):
        """Non-oracle metadata (source, published_date, language) survives too."""
        label, record = self._convert()
        missing = [
            k for k in label
            if k != "human_thriving_analysis" and k not in record
        ]
        assert missing == [], f"source fields dropped at split time: {missing}"
        assert record["language"] == "en"
        assert record["published_date"] == "2026-09-01"

    def test_training_contract_is_unchanged(self):
        """Trainers still see exactly the labels array they saw before."""
        _, record = self._convert()
        assert record["labels"] == [8.0, 7.0, 6.0, 5.0, 4.0, 3.0]
        assert record["dimension_names"] == self._dims
        assert record["id"] == "ht-1"
        assert record["content"] == "Community kitchens and boat ambulances."

    def test_analysis_block_is_not_duplicated(self):
        """The passthrough EXCLUDES the analysis key; it lives under oracle_meta only.

        Without this, `record = dict(label)` passes every other test and writes
        the whole block twice -- measured 41.0 MB vs 31.7 MB on v8's train.jsonl.
        """
        _, record = self._convert()
        assert "human_thriving_analysis" not in record

    def test_minority_real_shape_survives(self):
        """The 456-row shape: dict-valued dimensions and an int-valued `runs`."""
        label = self._v8_minority_shape_label()
        record = convert_to_training_format(
            [label],
            analysis_field="human_thriving_analysis",
            dimension_names=self._dims,
        )[0]
        assert record["labels"] == [5.0, 2.1667, 1.8333, 4.5, 4.3333, 4.0]
        assert record["oracle_meta"]["scope_verdict"] == "in_scope"
        # Carried verbatim, both meanings, no coercion.
        assert record["oracle_meta"]["runs"] == 6
        assert record["oracle_meta"]["scope_verdicts_per_run"].count("out_of_scope") == 2
        missing = [
            k for k in label["human_thriving_analysis"]
            if k not in record["oracle_meta"]
        ]
        assert missing == [], f"analysis fields dropped on the minority shape: {missing}"

    def test_skipped_rows_are_counted_out_loud(self, capsys):
        """A dropped row must never be silent -- that is the whole of #155.

        Articles with no analysis block are still skipped, which is correct, but
        the count is printed so the split total can be reconciled against the
        input total instead of quietly diverging.
        """
        labels = [
            self._v8_shaped_label(),
            {"id": "no-analysis-1", "title": "t", "content": "c"},
            {"id": "no-analysis-2", "title": "t", "content": "c"},
        ]
        records = convert_to_training_format(
            labels,
            analysis_field="human_thriving_analysis",
            dimension_names=self._dims,
        )
        assert len(records) == 1
        out = capsys.readouterr().out
        assert "Skipped 2 of 3 articles" in out
        assert "human_thriving_analysis" in out

    def test_nothing_is_printed_when_nothing_is_skipped(self, capsys):
        """The counter is a signal, not noise -- silence means zero drops."""
        self._convert()
        assert "Skipped" not in capsys.readouterr().out

    def test_real_corpus_row_survives(self):
        """Read a real row off disk -- the fixtures are a model of it, not proof.

        Skips where the corpus is absent (datasets/ is gitignored, so a fresh
        clone has none). It is the fixtures that must hold in CI; this is the
        check that the fixtures still describe reality.
        """
        import json
        from pathlib import Path

        corpus = (
            Path(__file__).resolve().parents[2]
            / "datasets/scored/human_thriving_v8/labels_v84_merged.jsonl"
        )
        if not corpus.exists():
            pytest.skip(f"corpus not on disk: {corpus}")

        with open(corpus, encoding="utf-8") as f:
            labels = [json.loads(line) for _, line in zip(range(500), f) if line.strip()]

        records = convert_to_training_format(
            labels,
            analysis_field="human_thriving_analysis",
            dimension_names=self._dims,
        )
        assert len(records) == len(labels)
        for label, record in zip(labels, records):
            analysis = label["human_thriving_analysis"]
            missing = [k for k in analysis if k not in record["oracle_meta"]]
            assert missing == [], f"{record['id']}: analysis fields dropped: {missing}"
            assert record["oracle_meta"]["scope_verdict"] == analysis["scope_verdict"]
            assert "human_thriving_analysis" not in record

    def test_derived_keys_win_over_source_keys(self):
        """A source row carrying its own 'labels' must not shadow the scores."""
        label = self._v8_shaped_label()
        label["labels"] = "not-a-score-array"
        label["oracle_meta"] = "stale"
        record = convert_to_training_format(
            [label],
            analysis_field="human_thriving_analysis",
            dimension_names=self._dims,
        )[0]
        assert record["labels"] == [8.0, 7.0, 6.0, 5.0, 4.0, 3.0]
        assert record["oracle_meta"]["scope_verdict"] == "harm_is_subject"

    def test_nested_dimension_format_keeps_siblings(self):
        """The nested {score, reasoning} shape must not lose the sibling fields."""
        label = {
            "id": "nested-1",
            "content": "x",
            "uplifting_analysis": {
                "dimensions": {d: {"score": 5, "reasoning": "r"} for d in self._dims},
                "scope_verdict": "in_scope",
            },
        }
        record = convert_to_training_format(
            [label], analysis_field="uplifting_analysis", dimension_names=self._dims
        )[0]
        assert record["labels"] == [5] * 6
        assert record["oracle_meta"]["scope_verdict"] == "in_scope"
