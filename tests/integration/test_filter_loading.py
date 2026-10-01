"""
Integration tests for filter package loading.

Tests the complete filter loading workflow:
- load_filter_package(): prompt and config, and (since 2026-10-01) NO per-lens
  prefilter object — those were deleted (NexusMind#284, decision 0)
- make_oracle_prefilter(): the oracle-path gate that remains (length floor + validation)
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestFilterPackageLoading:
    """Integration tests for filter package loading."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def uplifting_filter_path(self, project_root):
        """Path to uplifting v7 filter."""
        return project_root / "filters" / "uplifting" / "v7"

    def test_load_uplifting_filter(self, uplifting_filter_path):
        """Should load uplifting v7: prompt and config, no lens prefilter."""
        assert uplifting_filter_path.exists()

        from ground_truth.batch_scorer import load_filter_package

        prefilter, prompt_path, config = load_filter_package(uplifting_filter_path)

        assert prefilter is None
        assert prompt_path.exists()
        assert prompt_path.suffix == ".md"
        assert config["filter"]["name"] == "uplifting"


class TestOracleGateOnALoadedPackage:
    """The gate batch_scorer builds from a loaded package, end to end."""

    @pytest.fixture
    def gate(self):
        from ground_truth.batch_scorer import load_filter_package, make_oracle_prefilter

        filter_path = Path(__file__).parent.parent.parent / "filters" / "uplifting" / "v7"
        prefilter, _, _ = load_filter_package(filter_path)
        return make_oracle_prefilter(prefilter)

    def test_accepts_valid_article(self, gate, valid_article):
        assert gate(valid_article) is True

    def test_rejects_short_content(self, gate):
        assert gate({"title": "Good News", "content": "This is too short."}) is False

    def test_rejects_empty_content(self, gate):
        assert gate({"title": "Test", "content": ""}) is False

    def test_admits_what_the_deleted_lens_rules_blocked(self, gate):
        # uplifting v7's prefilter blocked this as `corporate_finance`; the oracle
        # now labels it (decision 0)
        article = {
            "title": "Company announces quarterly earnings beat and share buyback",
            "content": "The firm reported quarterly earnings above analyst estimates "
                       "and announced a share buyback programme. " * 10,
        }
        assert gate(article) is True
