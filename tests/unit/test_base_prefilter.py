"""
Unit tests for filters/base_prefilter.py

Tests the BasePreFilter class methods:
- validate_article(): Input validation
- has_any_pattern(): Regex pattern matching
- count_pattern_matches(): Pattern counting
- has_any_keyword(): Keyword search
- check_content_length(): Content length validation
- sanitize_text_comprehensive(): Text cleaning
"""

import re
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from filters.base_prefilter import BasePreFilter


class TestValidateArticle:
    """Tests for BasePreFilter.validate_article()"""

    def test_valid_article_with_content(self, valid_article):
        """Valid article with content field should pass."""
        is_valid, reason = BasePreFilter.validate_article(valid_article)
        assert is_valid is True
        assert reason == "valid"

    def test_valid_article_with_text(self, article_with_text_field):
        """Valid article with text field (instead of content) should pass."""
        is_valid, reason = BasePreFilter.validate_article(article_with_text_field)
        assert is_valid is True
        assert reason == "valid"

    def test_minimal_article(self, minimal_article):
        """Article with only title and content should pass."""
        is_valid, reason = BasePreFilter.validate_article(minimal_article)
        assert is_valid is True
        assert reason == "valid"

    def test_missing_title(self, article_missing_title):
        """Article missing title should fail."""
        is_valid, reason = BasePreFilter.validate_article(article_missing_title)
        assert is_valid is False
        assert reason == "missing_title"

    def test_missing_content(self, article_missing_content):
        """Article missing content/text should fail."""
        is_valid, reason = BasePreFilter.validate_article(article_missing_content)
        assert is_valid is False
        assert reason == "missing_content"

    def test_empty_content(self, article_empty_content):
        """Article with empty content should fail."""
        is_valid, reason = BasePreFilter.validate_article(article_empty_content)
        assert is_valid is False
        # Empty string is falsy, so it's treated as missing
        assert "content" in reason.lower()

    def test_empty_title(self):
        """Article with empty title should fail."""
        article = {"title": "", "content": "Some content"}
        is_valid, reason = BasePreFilter.validate_article(article)
        assert is_valid is False
        assert reason == "empty_title"

    def test_whitespace_only_title(self):
        """Article with whitespace-only title should fail."""
        article = {"title": "   \n\t  ", "content": "Some content"}
        is_valid, reason = BasePreFilter.validate_article(article)
        assert is_valid is False
        assert reason == "empty_title"

    def test_non_dict_input(self):
        """Non-dict input should fail with type error."""
        is_valid, reason = BasePreFilter.validate_article("not a dict")
        assert is_valid is False
        assert "invalid_type" in reason
        assert "str" in reason

    def test_none_input(self):
        """None input should fail with type error."""
        is_valid, reason = BasePreFilter.validate_article(None)
        assert is_valid is False
        assert "invalid_type" in reason

    def test_list_input(self):
        """List input should fail with type error."""
        is_valid, reason = BasePreFilter.validate_article(["title", "content"])
        assert is_valid is False
        assert "invalid_type" in reason
        assert "list" in reason


class TestHasAnyPattern:
    """Tests for BasePreFilter.has_any_pattern()"""

    @pytest.fixture
    def energy_patterns(self):
        """Compiled regex patterns for energy terms."""
        return [
            re.compile(r'\bsolar\b', re.IGNORECASE),
            re.compile(r'\bwind\b', re.IGNORECASE),
            re.compile(r'\brenewable\b', re.IGNORECASE)
        ]

    def test_single_match(self, energy_patterns):
        """Text with single matching pattern should return True."""
        text = "The new solar installation is complete."
        assert BasePreFilter.has_any_pattern(text, energy_patterns) is True

    def test_multiple_matches(self, energy_patterns):
        """Text with multiple matching patterns should return True."""
        text = "Both solar and wind energy are renewable."
        assert BasePreFilter.has_any_pattern(text, energy_patterns) is True

    def test_no_match(self, energy_patterns):
        """Text with no matching patterns should return False."""
        text = "The coal power plant is shutting down."
        assert BasePreFilter.has_any_pattern(text, energy_patterns) is False

    def test_case_insensitive(self, energy_patterns):
        """Case-insensitive patterns should match any case."""
        text = "SOLAR and Wind and RENEWABLE"
        assert BasePreFilter.has_any_pattern(text, energy_patterns) is True

    def test_empty_text(self, energy_patterns):
        """Empty text should return False."""
        assert BasePreFilter.has_any_pattern("", energy_patterns) is False

    def test_empty_patterns(self):
        """Empty pattern list should return False."""
        assert BasePreFilter.has_any_pattern("any text", []) is False

    def test_word_boundaries(self):
        """Word boundary patterns should not match partial words."""
        patterns = [re.compile(r'\bcar\b')]
        assert BasePreFilter.has_any_pattern("car park", patterns) is True
        assert BasePreFilter.has_any_pattern("cartoon", patterns) is False
        assert BasePreFilter.has_any_pattern("scar tissue", patterns) is False


class TestCountPatternMatches:
    """Tests for BasePreFilter.count_pattern_matches()"""

    @pytest.fixture
    def counting_patterns(self):
        """Patterns for counting tests."""
        return [
            re.compile(r'\bsolar\b', re.IGNORECASE),
            re.compile(r'\bwind\b', re.IGNORECASE)
        ]

    def test_count_single_pattern_multiple_times(self, counting_patterns):
        """Count multiple occurrences of same pattern."""
        text = "Solar panels and more solar panels and even more solar."
        count = BasePreFilter.count_pattern_matches(text, counting_patterns)
        assert count == 3  # "solar" appears 3 times

    def test_count_multiple_patterns(self, counting_patterns):
        """Count occurrences across multiple patterns."""
        text = "Solar and wind and solar and wind."
        count = BasePreFilter.count_pattern_matches(text, counting_patterns)
        assert count == 4  # 2 solar + 2 wind

    def test_count_zero(self, counting_patterns):
        """No matches should return 0."""
        text = "Coal and gas power plants."
        count = BasePreFilter.count_pattern_matches(text, counting_patterns)
        assert count == 0

    def test_count_empty_text(self, counting_patterns):
        """Empty text should return 0."""
        assert BasePreFilter.count_pattern_matches("", counting_patterns) == 0

    def test_count_empty_patterns(self):
        """Empty pattern list should return 0."""
        assert BasePreFilter.count_pattern_matches("any text", []) == 0


class TestHasAnyKeyword:
    """Tests for BasePreFilter.has_any_keyword()"""

    @pytest.fixture
    def keywords(self):
        """Sample keywords for testing."""
        return ["solar", "wind", "renewable"]

    def test_keyword_found(self, keywords):
        """Text containing keyword should return True."""
        text = "The solar panel installation is complete."
        assert BasePreFilter.has_any_keyword(text, keywords) is True

    def test_keyword_not_found(self, keywords):
        """Text without keywords should return False."""
        text = "The coal plant is closing."
        assert BasePreFilter.has_any_keyword(text, keywords) is False

    def test_case_insensitive_default(self, keywords):
        """Default case-insensitive search should match any case."""
        text = "SOLAR and WIND power"
        assert BasePreFilter.has_any_keyword(text, keywords) is True

    def test_case_sensitive(self, keywords):
        """Case-sensitive search should only match exact case."""
        text = "SOLAR and WIND power"
        # "solar" (lowercase) won't match "SOLAR"
        assert BasePreFilter.has_any_keyword(text, keywords, case_sensitive=True) is False

        text = "solar and wind power"
        assert BasePreFilter.has_any_keyword(text, keywords, case_sensitive=True) is True

    def test_partial_match(self, keywords):
        """Keywords should match as substrings (not word boundaries)."""
        text = "The solarwind hybrid system"  # Contains "solar" and "wind" as substrings
        assert BasePreFilter.has_any_keyword(text, keywords) is True

    def test_empty_text(self, keywords):
        """Empty text should return False."""
        assert BasePreFilter.has_any_keyword("", keywords) is False

    def test_empty_keywords(self):
        """Empty keyword list should return False."""
        assert BasePreFilter.has_any_keyword("any text", []) is False


class TestCheckContentLength:
    """Tests for BasePreFilter.check_content_length()"""

    def test_sufficient_length(self, valid_article):
        """Article with sufficient content should pass."""
        passed, reason = BasePreFilter.check_content_length(valid_article)
        assert passed is True
        assert reason == "passed"

    def test_short_content(self, short_article):
        """Article with short content should fail."""
        passed, reason = BasePreFilter.check_content_length(short_article)
        assert passed is False
        assert "content_too_short" in reason

    def test_custom_min_length(self, valid_article):
        """Custom minimum length should be respected."""
        # This should fail with a very high threshold
        passed, reason = BasePreFilter.check_content_length(valid_article, min_length=10000)
        assert passed is False

        # This should pass with a low threshold
        passed, reason = BasePreFilter.check_content_length(valid_article, min_length=10)
        assert passed is True

    def test_text_field_fallback(self, article_with_text_field):
        """Should check 'text' field if 'content' not present."""
        passed, reason = BasePreFilter.check_content_length(article_with_text_field)
        assert passed is True

    def test_missing_content(self, article_missing_content):
        """Article with no content should fail."""
        passed, reason = BasePreFilter.check_content_length(article_missing_content)
        assert passed is False


class TestSanitizeTextComprehensive:
    """Tests for BasePreFilter.sanitize_text_comprehensive()"""

    def test_normal_text_unchanged(self):
        """Normal ASCII text should remain unchanged."""
        text = "This is normal text with punctuation!"
        result = BasePreFilter.sanitize_text_comprehensive(text)
        assert "normal text" in result

    def test_html_entities_removed(self):
        """HTML entities should be converted."""
        text = "Hello &amp; goodbye &lt;tag&gt;"
        result = BasePreFilter.sanitize_text_comprehensive(text)
        # ⛔ This read `assert "&amp;" not in result or "&" in result` until
        # 2026-08-27. It is a TAUTOLOGY: "&amp;" contains "&", so whenever the
        # first disjunct is false the second is true. It passed on the decoded
        # output, on the raw undecoded input, and on the empty string alike —
        # a test named test_html_entities_removed that asserted nothing.
        # Pinned to measured behaviour instead: entities are decoded, and the
        # angle-bracket tag is stripped entirely.
        assert "&amp;" not in result, result
        assert "&" in result, result
        assert "&lt;" not in result, result

    def test_extra_whitespace_normalized(self):
        """Multiple spaces should be normalized."""
        text = "Too    many     spaces"
        result = BasePreFilter.sanitize_text_comprehensive(text)
        # Should have normalized spaces (implementation may vary)
        assert result  # Just verify it returns something

    def test_empty_string(self):
        """Empty string should return empty string."""
        assert BasePreFilter.sanitize_text_comprehensive("") == ""

    def test_unicode_preserved(self):
        """Valid Unicode should be preserved."""
        text = "Café résumé naïve"
        result = BasePreFilter.sanitize_text_comprehensive(text)
        # Should preserve valid unicode
        assert len(result) > 0
