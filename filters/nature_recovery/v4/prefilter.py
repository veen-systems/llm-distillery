"""
Nature Recovery Pre-Filter v2 (file) / V1 class — passes recovery/nature
stories, blocks non-environmental content.

ADR-018 declarative shape (data-only): the single text-pattern exclusion
category (disaster_no_recovery, with a recovery-pattern exception) lives in
EXCLUSION_PATTERNS / EXCEPTION_PATTERNS_PER_CATEGORY dicts compiled by
BasePreFilter.__init__. apply_filter stays custom because:

- The nature-relatedness check (`_is_nature_related`) runs FIRST in the
  current flow — block reason "not_nature_topic" precedes the disaster
  check. Base's standard pipeline runs `_filter_specific_final_check`
  LAST, which would change reason ordering on articles that are both
  off-topic and disaster-themed.
- Reason strings are bare category names ("disaster_no_recovery"), not
  "excluded_<category>" — the base pipeline's prefix would be a behavior
  change in this commit.
- This filter intentionally does not call `check_content_length` (gap is
  documented separately under Prefilter Quality, like CD v4's similar
  regression). Base pipeline would add that check.

Class-name drift (V1 in the v2 directory, VERSION="1.0") is intentional —
deferred to the cleanup-batch rename per the #52 plan, because NexusMind
imports the V1 name. Will fix together with sustech V2→V3 once the cross-
repo coordination is done.

History:
- v2.0 (2026-04-29): migrated to declarative BasePreFilter shape (#52,
  ADR-018). No behavior change — pattern set, override semantics, and
  iteration order preserved verbatim. Self-test 6/6 passes.
- v2.0 prior: identical logic, lists declared inline in apply_filter and
  _is_nature_related; class kept the V1 name from the file move.
"""

import re
from typing import Dict, List, Tuple

from filters.common.base_prefilter import BasePreFilter


class NatureRecoveryPreFilterV4(BasePreFilter):
    """Fast rule-based pre-filter for nature recovery content.

    Class-name drift retained intentionally — see module docstring.
    """

    VERSION = "1.0"

    # === ADR-018 EXCLUSION_PATTERNS ===
    # Single category — block when disaster framing fires WITHOUT any recovery
    # framing also present. Category key matches the (False, "disaster_no_recovery")
    # tuple this filter emits — no "excluded_" prefix because callers match
    # the bare reason string.
    EXCLUSION_PATTERNS = {
        # Pure disaster/decline language. Note: these are partial-word stems
        # (e.g. `catastroph` matches catastrophe / catastrophic) intentionally.
        'disaster_no_recovery': [
            r'\b(extinction|collapse|dying|destroyed|devastating|catastroph|irreversible)\b',
        ],
    }

    # Per-category exceptions — recovery framing within the disaster category
    # bypasses the block. Same parallel-dict pattern as CD v4 / uplifting v7,
    # but only one category here.
    EXCEPTION_PATTERNS_PER_CATEGORY = {
        # Recovery framing — partial-word stems (`recover` matches recovery /
        # recovered, `thriv` matches thriving, etc.) — preserved verbatim from
        # the inline regex in v2's prior apply_filter.
        'disaster_no_recovery': [
            r'\b(recover|restor|rebound|return|improv|increas|grow|thriv|heal|reintroduc|rewild)\b',
        ],
    }

    # Nature-related keywords — substring match (preserved semantics:
    # `kw in text_lower` works on the partial stems below). Used by the
    # initial gate-check; off-topic articles short-circuit before the
    # exclusion loop even runs.
    NATURE_KEYWORDS = [
        'ecosystem', 'biodiversity', 'habitat', 'deforestation', 'reforestation',
        'coral', 'reef', 'ocean', 'marine', 'wildlife', 'species', 'extinction',
        'pollution', 'air quality', 'water quality', 'environment', 'climate',
        'carbon', 'wetland', 'mangrove', 'conservation', 'restoration', 'recovery',
        'rewilding', 'endangered', 'protected area', 'national park', 'nature reserve',
        'emission', 'ozone', 'deforestation', 'afforestation', 'fish stock',
    ]

    def __init__(self):
        """Compile per-category exceptions; base compiles EXCLUSION_PATTERNS
        into self._compiled_exclusions."""
        super().__init__()
        self.filter_name = "nature_recovery"
        self.version = self.VERSION
        self._compiled_exceptions_per_category: Dict[str, List[re.Pattern]] = {
            cat: [re.compile(p, re.IGNORECASE) for p in patterns]
            for cat, patterns in self.EXCEPTION_PATTERNS_PER_CATEGORY.items()
        }

    def apply_filter(self, article: Dict) -> Tuple[bool, str]:
        """
        Determine if article should be sent to oracle for scoring.

        Custom flow (not BasePreFilter.apply_filter): preserves the original
        v2 order — nature-relatedness check FIRST, disaster check SECOND.
        Base's pipeline runs the final-check hook LAST, which would change
        reason precedence for articles that are both off-topic and disaster-
        themed.

        Returns:
            (should_score, reason)
            - (True, "passed"): Send to oracle
            - (False, "not_nature_topic"): Article isn't environmental at all
            - (False, "disaster_no_recovery"): Disaster framing without
                  recovery framing (no exception keyword found)
        """
        title = article.get('title', '')
        content = article.get('content', '') or article.get('text', '')
        text_lower = (title + ' ' + content[:self.MAX_PREFILTER_CONTENT]).lower()

        # Gate: must be about nature/ecosystem/environment first.
        if not self._is_nature_related(text_lower):
            return (False, "not_nature_topic")

        # Iterate exclusions; first blocking category wins (only one category
        # here today, but kept generic for shape consistency with the other
        # #52-migrated filters).
        for category, compiled_patterns in self._compiled_exclusions.items():
            if not self.has_any_pattern(text_lower, compiled_patterns):
                continue
            exceptions = self._compiled_exceptions_per_category.get(category, [])
            if self.has_any_pattern(text_lower, exceptions):
                continue
            return (False, category)

        return (True, "passed")

    def _is_nature_related(self, text_lower: str) -> bool:
        """Check if article is about nature/ecosystem/environmental issues
        (PERMISSIVE — any keyword hit lets it through)."""
        return any(kw in text_lower for kw in self.NATURE_KEYWORDS)

    def get_statistics(self) -> Dict:
        """Return filter statistics."""
        stats = {
            'version': self.VERSION,
            'nature_keywords': len(self.NATURE_KEYWORDS),
        }
        for category, patterns in self.EXCLUSION_PATTERNS.items():
            stats[f'{category}_patterns'] = len(patterns)
            stats[f'{category}_exceptions'] = len(
                self.EXCEPTION_PATTERNS_PER_CATEGORY.get(category, [])
            )
        return stats


def test_prefilter():
    """Self-test — hand-crafted cases covering each branch of the flow.
    Lifted from the #52 baseline probe."""

    prefilter = NatureRecoveryPreFilterV4()

    pad = ' Lorem ipsum filler text to extend article length. ' * 8

    test_cases = [
        # PASS - nature recovery
        {
            'title': 'Coral Reef Recovery After Decade of Restoration',
            'text': 'Marine biologists report significant biodiversity recovery in protected reef areas.' + pad,
            'expected': (True, 'passed'),
            'description': 'Nature recovery (reef)',
        },
        # BLOCK - not nature topic
        {
            'title': 'Stock Market Soars to New Highs',
            'text': 'Wall Street traders celebrated record gains today as the index hit a new milestone.' + pad,
            'expected': (False, 'not_nature_topic'),
            'description': 'Off-topic (markets)',
        },
        # BLOCK - disaster without recovery framing
        {
            'title': 'Devastating Forest Collapse Threatens Wildlife',
            'text': 'The ecosystem is dying. Habitat destruction has been catastrophic. Extinction is irreversible for several species.' + pad,
            'expected': (False, 'disaster_no_recovery'),
            'description': 'Disaster framing without recovery',
        },
        # PASS - disaster WITH recovery framing (exception bypass)
        {
            'title': 'Ecosystem Recovery Strategy After Devastating Wildfire',
            'text': 'Despite catastrophic devastation, biodiversity is rebounding. Wildlife is returning, vegetation is regrowing, and conservation efforts have helped the habitat heal.' + pad,
            'expected': (True, 'passed'),
            'description': 'Disaster + recovery framing (exception)',
        },
        # PASS - generic conservation story
        {
            'title': 'Wetland Conservation Project Expands',
            'text': 'The mangrove restoration program is improving water quality and protecting endangered species along the coast.' + pad,
            'expected': (True, 'passed'),
            'description': 'Generic conservation',
        },
        # BLOCK - off-topic with no environmental context
        {
            'title': 'Best Hotels in Paris for 2026',
            'text': 'Travelers will find luxury accommodation, fine dining, and museums in this guide to the French capital.' + pad,
            'expected': (False, 'not_nature_topic'),
            'description': 'Off-topic (travel)',
        },
    ]

    print("Testing Nature Recovery Pre-Filter v2 (class V1)")
    print("=" * 60)

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        result = prefilter.apply_filter(test)
        expected = test['expected']
        match = (result[0] == expected[0] and result[1] == expected[1])

        status = "[PASS]" if match else "[FAIL]"
        if match:
            passed += 1
        else:
            failed += 1

        print(f"\nTest {i}: {status} - {test['description']}")
        print(f"  Title: {test['title'][:60]}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{passed + failed} tests passed")
    print("\nPre-filter Statistics:")
    for key, value in prefilter.get_statistics().items():
        print(f"  {key}: {value}")


if __name__ == '__main__':
    test_prefilter()
