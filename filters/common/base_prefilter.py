"""
Base PreFilter Class

Provides common functionality for all semantic prefilters:
- Comprehensive text cleaning (Unicode, HTML, invisible chars, security)
- Article structure validation
- Standard interface for apply_filter()
- Shared utilities for pattern matching

Commerce detection is handled globally by NexusMind's CommercePreprocessor
before articles reach per-filter prefilters. See deployment-boundary memory.

All filter prefilters should inherit from this base class.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, TypedDict

from filters.common.text_cleaning import sanitize_text_comprehensive, clean_article as clean_article_comprehensive

logger = logging.getLogger(__name__)


class CategoryOverrideCfg(TypedDict, total=False):
    """ADR-019 per-category override entry. All fields optional.

    keywords: substring matches (case-insensitive) that bypass the category.
    threshold: POSITIVE_PATTERNS match count needed to bypass the category.
    """
    keywords: List[str]
    threshold: int


class BasePreFilter:
    """
    Base class for semantic prefilters.

    Two ways to use this class (ADR-018):

    1. **Declarative form (preferred)**: Override the class attributes
       EXCLUSION_PATTERNS, OVERRIDE_KEYWORDS, POSITIVE_PATTERNS, POSITIVE_THRESHOLD.
       The default apply_filter() drives the standard pipeline:
            validate -> exclusions-with-override
            -> _filter_specific_final_check (optional hook) -> passed

       Subclasses can override _filter_specific_final_check() for filter-specific
       logic that runs after exclusions pass (e.g. "is this article actually about
       climate?"). Patterns compile once in __init__.

    2. **Custom form (legacy / unusual flows)**: Override apply_filter() directly.
       The pre-#52 filters use this. Migration to the declarative form is tracked
       per-filter as part of llm-distillery#52.
    """

    VERSION = "0.0"  # Override in subclass
    # Labelling-time floor only — prevents oracle framework leakage. NOT applied
    # by apply_filter() (#93); see check_content_length().
    MIN_CONTENT_LENGTH = 300
    MAX_PREFILTER_CONTENT = 2000  # Content chars to analyze in prefilter (for efficiency)

    # --- ADR-018 declarative pattern registry (subclasses override these) ---

    # Category -> raw regex patterns. Compiled once in __init__ with re.IGNORECASE.
    # Note: per-pattern case sensitivity can still be requested via inline
    # `(?-i:...)` (see memory/feedback-regex-ignorecase-trap.md for why this matters).
    EXCLUSION_PATTERNS: Dict[str, List[str]] = {}

    # Substring keywords. If any appears (case-insensitive) in title+text, exclusions
    # are bypassed. Matches `kw.lower() in combined_lower` — substring, not word boundary.
    OVERRIDE_KEYWORDS: List[str] = []

    # Optional: regex patterns whose total match count is checked against
    # POSITIVE_THRESHOLD. If POSITIVE_THRESHOLD > 0 and the count meets it, exclusions
    # are bypassed (e.g. foresight v1's "needs >= 3 positive matches" rule).
    POSITIVE_PATTERNS: List[str] = []
    POSITIVE_THRESHOLD: int = 0

    # Optional URL-based domain blocking. Keys are reason strings (typically
    # `excluded_domain_<category>`), values are lists of domain substrings —
    # `domain in url_lower` semantics, no anchoring. Iteration is in declared
    # order; first match wins. Use via `_check_domain_exclusions(url)`.
    # Subclasses can either declare the dict directly or build it from
    # per-category lists for stats-friendly access.
    DOMAIN_EXCLUSIONS: Dict[str, List[str]] = {}

    # ADR-019 per-category override registry. Keys are category names from
    # EXCLUSION_PATTERNS; values are CategoryOverrideCfg dicts (TypedDict —
    # `keywords` and `threshold` only). Typo'd keys are caught by mypy.
    # Categories not listed fall back to global OVERRIDE_KEYWORDS /
    # POSITIVE_THRESHOLD via _has_override (current ADR-018 semantics).
    # Compound rules that don't fit the dict shape go via the
    # _compound_override_applies() hook instead — see that method's docstring.
    CATEGORY_OVERRIDES: Dict[str, CategoryOverrideCfg] = {}

    def __init__(self):
        """Compile EXCLUSION_PATTERNS and POSITIVE_PATTERNS once, upfront.

        Subclasses that override __init__ should call super().__init__() so the
        compiled patterns are available. Subclasses still using the legacy
        custom-apply_filter shape are unaffected — their EXCLUSION_PATTERNS/etc.
        class attrs are empty, so the compiled dicts come out empty and unused.
        """
        self._compiled_exclusions: Dict[str, List[re.Pattern]] = {
            cat: [re.compile(p, re.IGNORECASE) for p in patterns]
            for cat, patterns in self.EXCLUSION_PATTERNS.items()
        }
        self._compiled_positives: List[re.Pattern] = [
            re.compile(p, re.IGNORECASE) for p in self.POSITIVE_PATTERNS
        ]

    @staticmethod
    def validate_article(article) -> Tuple[bool, str]:
        """
        Validate article structure before processing.

        Checks:
        - Article is a dict
        - Has required fields (title, content/text)
        - Fields are non-empty strings

        Args:
            article: Object to validate

        Returns:
            (is_valid, reason)
            - (True, "valid"): Article structure is valid
            - (False, "reason"): Why validation failed
        """
        if not isinstance(article, dict):
            return (False, f"invalid_type_{type(article).__name__}")

        if 'title' not in article:
            return (False, "missing_title")

        title = article.get('title')
        if not isinstance(title, str) or not title.strip():
            return (False, "empty_title")

        content = article.get('content') or article.get('text')
        if content is None:
            return (False, "missing_content")

        if not isinstance(content, str) or not content.strip():
            return (False, "empty_content")

        return (True, "valid")

    @staticmethod
    def has_any_pattern(text: str, patterns: List[re.Pattern]) -> bool:
        """
        Check if text matches any regex pattern in the list.

        Args:
            text: Text to search
            patterns: List of compiled regex patterns

        Returns:
            True if any pattern matches
        """
        return any(pattern.search(text) for pattern in patterns)

    @staticmethod
    def count_pattern_matches(text: str, patterns: List[re.Pattern]) -> int:
        """
        Count total matches across all patterns.

        Args:
            text: Text to search
            patterns: List of compiled regex patterns

        Returns:
            Total number of matches across all patterns
        """
        return sum(len(pattern.findall(text)) for pattern in patterns)

    @staticmethod
    def has_any_keyword(
        text: str,
        keywords: List[str],
        case_sensitive: bool = False
    ) -> bool:
        """
        Check if text contains any keyword from the list.

        Args:
            text: Text to search
            keywords: List of keywords to find
            case_sensitive: Whether to match case (default: False)

        Returns:
            True if any keyword found
        """
        if not case_sensitive:
            text = text.lower()
            keywords = [k.lower() for k in keywords]
        return any(kw in text for kw in keywords)

    @staticmethod
    def sanitize_text_comprehensive(text: str) -> str:
        """
        Comprehensively clean text for LLM processing.

        Removes:
        - Invalid Unicode (surrogates)
        - HTML entities and tags
        - Zero-width characters (invisible text)
        - Bidirectional marks (security issue)
        - Normalizes whitespace

        This is the RECOMMENDED method for cleaning text.

        Args:
            text: String to clean

        Returns:
            Comprehensively cleaned string
        """
        return sanitize_text_comprehensive(text)

    @staticmethod
    def clean_article(article: Dict) -> Dict:
        """
        Recursively clean all text fields in an article.

        Applies comprehensive text cleaning to all strings:
        - Invalid Unicode removal
        - HTML cleaning
        - Invisible character removal
        - Security (BiDi marks)
        - Whitespace normalization

        Safe to call on already-clean articles (idempotent).

        Args:
            article: Article dict with potentially problematic text

        Returns:
            New dict with all text fields comprehensively cleaned
        """
        return clean_article_comprehensive(article)

    @staticmethod
    def content_length(article: Dict) -> int:
        """Length in characters of the article's content field.

        The stamp half of the #93 split: every scoring path records this so a
        short-content decision can be made (or reversed) downstream without
        re-deriving it. See `check_content_length` for the labelling-time gate.

        Null-safe on purpose: `check_content_length` inherited the bare
        `get('text', get('content'))` expression, which raises on an explicit
        `text: None` alongside a valid `content`. That was harmless while the
        expression only ran on the oracle path; since #93 it runs on every
        scored article, so a malformed row must stamp 0 rather than kill a batch.
        """
        content = article.get('text') or article.get('content') or ''
        return len(content)

    @staticmethod
    def check_content_length(article: Dict, min_length: int = None) -> Tuple[bool, str]:
        """
        LABELLING-TIME precondition: is this article long enough to *oracle-score*?

        Short articles (<300 chars) often cause LLMs to analyze the evaluation
        framework/prompt instead of the article content itself (framework leakage).
        That hazard exists only where a prompt does — i.e. in the oracle path
        (`ground_truth/batch_scorer.py`), which calls this directly.

        **Not a scoring gate (#93).** It is deliberately NOT part of
        `apply_filter()`: the student sees no prompt, and measurement showed a
        length gate discards as much genuine content as bad (uplifting: 67% of
        sub-300 articles above the op-point are oracle-validated vs 65% of long
        ones). The scoring-path treatment is stamp + one config-gated cap —
        see `FilterBaseScorer` `short_content` config.

        Args:
            article: Dict with 'title' and 'text'/'content' keys
            min_length: Minimum content length in characters (defaults to MIN_CONTENT_LENGTH)

        Returns:
            (should_label, reason)
            - (True, "passed"): Content is long enough to send to the oracle
            - (False, "content_too_short_<n>chars"): Below minimum threshold
        """
        if min_length is None:
            min_length = BasePreFilter.MIN_CONTENT_LENGTH

        content_length = BasePreFilter.content_length(article)

        if content_length < min_length:
            return (False, f"content_too_short_{content_length}chars")

        return (True, "passed")

    def _check_domain_exclusions(self, url: str) -> str:
        """Check if URL belongs to a domain in DOMAIN_EXCLUSIONS.

        Returns the matching reason string (the dict key — typically
        `excluded_domain_<category>`), or empty string if no match. Iterates
        in declared order; first match wins. Empty/missing url returns "".

        Hoisted from per-filter implementations under llm-distillery#52
        review-battery cleanup. Filters with no domain rules can leave the
        DOMAIN_EXCLUSIONS class attr empty (the default) — this method
        becomes a no-op returning "".
        """
        if not url:
            return ""
        url_lower = url.lower()
        for reason, domains in self.DOMAIN_EXCLUSIONS.items():
            for domain in domains:
                if domain in url_lower:
                    return reason
        return ""

    def apply_filter(self, article: Dict) -> Tuple[bool, str]:
        """
        Determine if article should be sent to LLM for scoring.

        Default implementation drives the ADR-018 standard pipeline:
            validate -> _pre_exclusion_check -> exclusions-with-override
            -> _filter_specific_final_check -> passed

        There is deliberately NO length check here (#93). The 300-char floor is
        a labelling-time precondition, enforced by the oracle path via
        `check_content_length()`; the scoring path stamps length and applies at
        most one config-gated cap. `validate_article` still rejects genuinely
        empty content — empty is a different case from short.

        Subclasses with custom flow can override this entirely (legacy shape).

        Args:
            article: Dict with 'title' and 'text'/'content' keys

        Returns:
            (should_score, reason)
            - (True, "passed"): Send to LLM
            - (False, "reason"): Block with reason string
        """
        valid, validation_reason = self.validate_article(article)
        if not valid:
            return (False, validation_reason)

        text = self._get_combined_clean_text(article)
        title = article.get('title', '').lower()

        passed_pre, pre_reason = self._pre_exclusion_check(title, text)
        if not passed_pre:
            return (False, pre_reason)

        excluded, exc_reason = self._is_excluded(title, text)
        if excluded:
            return (False, exc_reason)

        passed_specific, specific_reason = self._filter_specific_final_check(title, text)
        if not passed_specific:
            return (False, specific_reason)

        return (True, "passed")

    def _is_excluded(self, title: str, text: str) -> Tuple[bool, str]:
        """
        Check title+text against EXCLUSION_PATTERNS, with OVERRIDE_KEYWORDS /
        POSITIVE_THRESHOLD bypass.

        Returns (excluded, reason). reason is "excluded_<category>" on block,
        empty string on pass.

        No-op (returns (False, "")) if EXCLUSION_PATTERNS is empty — lets legacy
        filters that override apply_filter() inherit this base method without
        side effects.
        """
        if not self._compiled_exclusions:
            return (False, "")

        # Lowercase combined text once for both pattern search and override check.
        # Patterns are compiled case-insensitively, so searching against the
        # lowercased string is equivalent and avoids redundant work.
        combined = f"{title} {text[:1000]}".lower()

        for category, compiled in self._compiled_exclusions.items():
            for pattern in compiled:
                if pattern.search(combined):
                    if self._category_override_applies(category, combined):
                        # Override applies — skip this category entirely (not just
                        # this pattern; legacy sustech behavior).
                        break
                    return (True, f"excluded_{category}")

        return (False, "")

    def _has_override(self, combined_lower: str) -> bool:
        """
        Decide whether the *global* OVERRIDE_KEYWORDS or POSITIVE_THRESHOLD lets
        the article bypass exclusions.

        OVERRIDE_KEYWORDS are substring matches (case-insensitive). POSITIVE_PATTERNS
        require a total match count >= POSITIVE_THRESHOLD (only consulted when
        POSITIVE_THRESHOLD > 0).

        Per-category overrides live in `_category_override_applies()` (ADR-019).
        """
        if self.OVERRIDE_KEYWORDS:
            if any(kw.lower() in combined_lower for kw in self.OVERRIDE_KEYWORDS):
                return True
        if self.POSITIVE_THRESHOLD > 0 and self._compiled_positives:
            count = sum(len(p.findall(combined_lower)) for p in self._compiled_positives)
            if count >= self.POSITIVE_THRESHOLD:
                return True
        return False

    def _category_override_applies(self, category: str, combined_lower: str) -> bool:
        """
        Final arbitration on whether the exclusion for `category` is bypassed.

        DO NOT OVERRIDE THIS METHOD. Subclasses with compound rules override
        `_compound_override_applies` instead — that hook returns Optional[bool],
        with `None` meaning "I don't handle this category, defer to defaults".
        This base implementation owns the fallback chain so subclasses cannot
        accidentally lose the dict + global checks by forgetting `super()`
        (Template Method pattern).

        ADR-019 precedence:
          1. _compound_override_applies(category, combined_lower) — subclass
             hook for compound rules. Returns True/False to short-circuit, or
             None to defer.
          2. CATEGORY_OVERRIDES[category]["keywords"] — substring match.
          3. CATEGORY_OVERRIDES[category]["threshold"] — POSITIVE_PATTERNS
             match count >= threshold.
          4. Global `_has_override` (OVERRIDE_KEYWORDS / POSITIVE_THRESHOLD),
             preserving ADR-018 semantics for filters that declare nothing.
        """
        compound = self._compound_override_applies(category, combined_lower)
        if compound is not None:
            return compound

        cfg = self.CATEGORY_OVERRIDES.get(category)
        if cfg:
            kws = cfg.get("keywords") or []
            if kws and any(kw.lower() in combined_lower for kw in kws):
                return True
            threshold = cfg.get("threshold", 0)
            if threshold > 0 and self._compiled_positives:
                count = sum(
                    len(p.findall(combined_lower)) for p in self._compiled_positives
                )
                if count >= threshold:
                    return True
        return self._has_override(combined_lower)

    def _compound_override_applies(
        self, category: str, combined_lower: str
    ) -> Optional[bool]:
        """
        Hook for compound override rules that don't fit `CATEGORY_OVERRIDES`.

        Returns:
          True  — bypass the exclusion in `category`.
          False — explicitly do NOT bypass (suppress dict + global fallback).
                  Use sparingly; the common case for "don't bypass" is to
                  return None and let the defaults apply.
          None  — subclass doesn't handle this category. The default fallback
                  chain (CATEGORY_OVERRIDES dict, then global _has_override)
                  runs unchanged.

        Subclass shape (cf. belonging v1's obit compound rule — note that
        belonging compiles its positive signals into a renamed attr
        `_compiled_positive_signals`, not the base's `_compiled_positives`,
        to avoid shadowing base's POSITIVE_PATTERNS slot. The example below
        uses base's compiled attr for simplicity; check the actual filter
        for its naming convention):
            def _compound_override_applies(self, category, combined_lower):
                if category == 'obituary_funeral':
                    pos = sum(len(p.findall(combined_lower)) for p in self._compiled_positives)
                    has_exc = any(p.search(combined_lower) for p in self._compiled_exceptions)
                    return pos >= 2 or (has_exc and pos >= 1)
                return None  # defer for every other category

        Note: this hook receives only `combined_lower` — already lowercased
        title + first 1000 chars of text. Compound rules that need the raw
        article (case-sensitive title checks, url, metadata) live outside
        this hook in custom apply_filter() — see ADR-019 Revisit If clause.
        """
        return None

    def _pre_exclusion_check(self, title: str, text: str) -> Tuple[bool, str]:
        """
        Hook for filter-specific logic that runs BEFORE the exclusion loop.

        Symmetric counterpart to `_filter_specific_final_check`. Use this when
        a filter has a *gate-in* check that should short-circuit before any
        exclusion runs — e.g. nature_recovery's "is this article about nature
        at all?" check, where off-topic articles should be tagged
        `not_nature_topic` regardless of which exclusion category their text
        might also trip.

        Default: always pass. Subclasses override and return (False, reason)
        to block at this stage. Reason strings should be bare (no prefix);
        the base pipeline returns them verbatim.

        Args:
            title: Lowercased article title.
            text: Cleaned, lowercased combined title+description+content.

        Returns:
            (passed, reason). reason is empty string on pass.
        """
        return (True, "")

    def _filter_specific_final_check(self, title: str, text: str) -> Tuple[bool, str]:
        """
        Hook for filter-specific logic that runs after exclusions pass.

        Used for things like 'is this article actually about climate?' (sustech)
        or 'does it mention any in-scope cultural region?' (cultural_discovery).

        Default: always pass. Subclasses override and return (False, reason)
        to block at this stage.

        Args:
            title: Lowercased article title.
            text: Cleaned, lowercased combined title+description+content.

        Returns:
            (passed, reason). reason is empty string on pass.
        """
        return (True, "")

    def _get_combined_text(self, article: Dict) -> str:
        """Combine title + description + content/text for analysis"""
        parts = []

        if 'title' in article:
            parts.append(article['title'])

        if 'description' in article:
            parts.append(article['description'])

        content = article.get('content') or article.get('text', '')
        if content:
            # Limit content for pre-filter efficiency
            parts.append(content[:self.MAX_PREFILTER_CONTENT])

        return ' '.join(parts)

    def _get_combined_clean_text(self, article: Dict) -> str:
        """Combine and comprehensively clean title + description + content for analysis"""
        combined_text = self._get_combined_text(article)
        return self.sanitize_text_comprehensive(combined_text.lower())
