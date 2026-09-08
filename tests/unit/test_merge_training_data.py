"""Unit tests for scripts/merge_training_data.py

The active-learning merge path writes the same train/val/test.jsonl that
training/prepare_data.py does, from its own converter. It carried the identical
#155 defect -- a six-key allowlist that discarded the oracle's non-dimensional
output -- and had no tests at all, so the fix in prepare_data.py would have left
exactly the rows active learning just paid to score without a scope_verdict.

Worse than a plain re-drop: load_existing_training_data() passes pre-existing
rows through whole, so a merged split can be PARTIALLY covered, and a consumer
counting scope_verdict presence would read the gap as a real rate rather than as
a missing field. Hence the coverage tests below.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "merge_training_data", _ROOT / "scripts" / "merge_training_data.py"
)
merge_training_data = importlib.util.module_from_spec(_SPEC)
sys.modules["merge_training_data"] = merge_training_data
_SPEC.loader.exec_module(merge_training_data)

convert_oracle_to_training = merge_training_data.convert_oracle_to_training

DIMS = [
    "human_wellbeing_impact",
    "social_cohesion_impact",
    "justice_rights_impact",
    "evidence_level",
    "benefit_distribution",
    "change_durability",
]


def _oracle_article():
    """An oracle-scored row shaped like the active-learning batch files."""
    return {
        "id": "ht-1",
        "title": "Flood response in Bihar",
        "url": "https://example.org/a",
        "content": "Community kitchens and boat ambulances.",
        "source": "example.org",
        "published_date": "2026-09-01",
        "language": "en",
        "human_thriving_analysis": {
            "human_wellbeing_impact": {"score": 8, "evidence": "e"},
            "social_cohesion_impact": {"score": 7, "evidence": "e"},
            "justice_rights_impact": {"score": 6, "evidence": "e"},
            "evidence_level": {"score": 5, "evidence": "e"},
            "benefit_distribution": {"score": 4, "evidence": "e"},
            "change_durability": {"score": 3, "evidence": "e"},
            "scope_verdict": "harm_is_subject",
            "dominant_subject": "a flood",
            "content_type": "news",
        },
    }


class TestConvertOracleToTraining:
    """The merge path must not re-introduce the #155 drop."""

    def test_labels_are_extracted_in_dimension_order(self):
        record = convert_oracle_to_training(
            _oracle_article(), "human_thriving_analysis", DIMS
        )
        assert record["labels"] == [8.0, 7.0, 6.0, 5.0, 4.0, 3.0]
        assert record["dimension_names"] == DIMS

    def test_scope_verdict_survives_the_merge(self):
        record = convert_oracle_to_training(
            _oracle_article(), "human_thriving_analysis", DIMS
        )
        assert record["oracle_meta"]["scope_verdict"] == "harm_is_subject"

    def test_every_analysis_field_survives(self):
        article = _oracle_article()
        record = convert_oracle_to_training(article, "human_thriving_analysis", DIMS)
        analysis = article["human_thriving_analysis"]
        missing = [k for k in analysis if k not in record["oracle_meta"]]
        assert missing == [], f"analysis fields dropped by the merge: {missing}"

    def test_every_source_field_survives(self):
        article = _oracle_article()
        record = convert_oracle_to_training(article, "human_thriving_analysis", DIMS)
        missing = [
            k for k in article if k != "human_thriving_analysis" and k not in record
        ]
        assert missing == [], f"source fields dropped by the merge: {missing}"

    def test_analysis_field_is_not_duplicated(self):
        """The passthrough excludes the analysis key -- it lives under oracle_meta only."""
        record = convert_oracle_to_training(
            _oracle_article(), "human_thriving_analysis", DIMS
        )
        assert "human_thriving_analysis" not in record

    def test_article_without_analysis_is_skipped(self):
        assert (
            convert_oracle_to_training({"id": "x"}, "human_thriving_analysis", DIMS)
            is None
        )

    def test_flat_dimension_scores_still_work(self):
        article = _oracle_article()
        article["human_thriving_analysis"].update({d: i for i, d in enumerate(DIMS)})
        record = convert_oracle_to_training(article, "human_thriving_analysis", DIMS)
        assert record["labels"] == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        assert record["oracle_meta"]["scope_verdict"] == "harm_is_subject"


class TestPartialCoverageIsVisible:
    """A merge of pre-#155 rows with new ones is partially covered -- say so."""

    def test_coverage_warning_fires_on_a_partial_merge(self, tmp_path, capsys):
        import json

        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        # A pre-#155 split row: six keys, no oracle_meta.
        (existing_dir / "train.jsonl").write_text(
            json.dumps(
                {
                    "id": "old-1",
                    "title": "t",
                    "content": "c",
                    "url": "u",
                    "labels": [1.0] * 6,
                    "dimension_names": DIMS,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        scored = tmp_path / "scored_batch_1.jsonl"
        scored.write_text(
            json.dumps(_oracle_article()) + "\n", encoding="utf-8"
        )
        out_dir = tmp_path / "out"

        argv = [
            "merge_training_data.py",
            "--existing-dir", str(existing_dir),
            "--new-scored", str(scored),
            "--output-dir", str(out_dir),
            "--analysis-field", "human_thriving_analysis",
            "--dimensions", *DIMS,
        ]
        old_argv = sys.argv
        sys.argv = argv
        try:
            merge_training_data.main()
        finally:
            sys.argv = old_argv

        out = capsys.readouterr().out
        assert "oracle_meta coverage: 1/2 (50.0%)" in out
        assert "WARNING" in out
        assert "predate llm-distillery#155" in out

        rows = [
            json.loads(line)
            for name in ("train.jsonl", "val.jsonl", "test.jsonl")
            for line in (out_dir / name).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(rows) == 2
        assert sum(1 for r in rows if "oracle_meta" in r) == 1
