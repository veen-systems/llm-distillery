"""
Solutions Pre-Filter v4 (package: solutions — renamed from sustainability_technology
per ADR-012/013 at the v4 bump; lens: Solutions).

WHY THIS IS COMMERCE-ONLY PASS-THROUGH (the nature_recovery #70 lesson):
nature_recovery v2's prefilter gated on English keywords and silently dropped
21.6% of non-English positives (129/598, mostly es/pt/fr/de/it/nl/…). Solutions
runs on the SAME multilingual production stream — ~29% of it is non-English
(es/it/de/pt/nl/fr/el/ru/…). A topic-INCLUSION gate ("block unless an English
solution keyword is present") would repeat that failure exactly: a Spanish
"el gobierno despliega un programa…" carries no English keyword and would be
dropped before the oracle/student ever saw it.

So this prefilter does NOT judge whether an article is a solution — that is the
job of the multilingual e5 probe (Stage 1) and the Gemma-3-1B student (Stage 2),
trained on dimensional labels. Per ADR-004, commerce is the ONLY universal
prefilter, and it runs UPSTREAM in NexusMind's CommercePreprocessor. This
per-filter prefilter keeps only base's validate + content-length checks and
passes everything else through:

    commerce (upstream) + this pass-through prefilter
      -> multilingual e5 probe (Stage 1)
      -> Gemma-3-1B student (Stage 2, dimensional scoring + Step-1 scope).

MULTILINGUAL FORCE-PASS (POSITIVE_PATTERNS / POSITIVE_THRESHOLD):
The ADR-018 base mechanism — a strong-positive count bypasses *pattern*
exclusions. INSURANCE-ONLY today: base's override bypasses only
EXCLUSION_PATTERNS, and this filter declares none (commerce is upstream), so the
bypass is currently inert. It is kept so (a) the multilingual solution
vocabulary lives in code, and (b) if a cheap local pattern exclusion is ever
added, the multilingual bypass is already in place. The real recall guarantee is
the absence of a topic gate + the multilingual e5 probe — not this list.

Stems are word-START (leading \\b only, NO trailing \\b) so they match inflected
forms across languages (deploy -> deployed/deployment, despleg -> despliega/
desplegado). A trailing boundary would defeat that (\\bdeploy\\b misses
"deployment"). Verified in test_prefilter's inflection regression check.

History:
- v4.0 (2026-07): first prefilter for the Solutions lens (package renamed from
  sustainability_technology to solutions, ADR-012/013). Commerce-only pass-through from the start
  — no English topic/decline gates, per the nature_recovery #70 lesson.
"""

import re
from typing import Dict

from filters.common.base_prefilter import BasePreFilter


class SolutionsPreFilterV4(BasePreFilter):
    """Commerce-only pass-through pre-filter for the Solutions lens.

    Inherits BasePreFilter.apply_filter unchanged (validate -> length ->
    exclusions[none] -> passed). Solution-vs-not judgment is delegated to the
    e5 probe + student, NOT done here (see module docstring / nature_recovery #70).
    """

    VERSION = "4.0"

    # No local EXCLUSION_PATTERNS: commerce runs upstream (ADR-004), and no
    # topic/decline gate is added (the model's job). Left empty on purpose — base's
    # apply_filter then reduces to validate + length + pass.
    EXCLUSION_PATTERNS: Dict[str, list] = {}

    # Multilingual solution signals — the ADR-018 force-pass slot. Insurance only
    # while EXCLUSION_PATTERNS is empty (see module docstring). Broad, partial-word
    # stems across the top production languages (en/es/it/de/nl/pt/fr). These are
    # NECESSARY-not-SUFFICIENT vocabulary (the prompt's KEY PRINCIPLE) — fine for an
    # insurance force-pass, never as an inclusion gate.
    POSITIVE_PATTERNS = [
        # English
        r'\b(deploy|install|launch|retrofit|reform|legislat|policy|program|'
        r'cooperativ|subsid|mandate|pilot|restor|treaty|rollout)',
        # Spanish / Portuguese (despleg|desplieg covers the radical-changing
        # desplegar -> despliega)
        r'\b(despleg|desplieg|instal|reforma|legislac|legislaç|polític|programa|'
        r'cooperativ|subvencion|subsídi|subsidi|piloto|implement)',
        # Italian
        r'\b(distribu|installa|riforma|legislaz|politic|programma|cooperativ|'
        r'sovvenzion|pilota|attuazion)',
        # German / Dutch
        r'\b(einführ|install|reform|gesetz|förder|programm|genossenschaft|'
        r'sanierung|invoer|hervorming|wetgeving|subsidie|coöperatie|cooperatie)',
        # French
        r'\b(déploi|install|réforme|législ|politiqu|programme|coopérativ|'
        r'subvention|pilote|mise en œuvre)',
    ]
    POSITIVE_THRESHOLD = 2

    def get_statistics(self) -> Dict:
        """Return filter statistics."""
        return {
            'version': self.VERSION,
            'mode': 'commerce_only_passthrough',
            'lens': 'solutions',
            'exclusion_categories': len(self.EXCLUSION_PATTERNS),
            'positive_patterns': len(self.POSITIVE_PATTERNS),
            'positive_threshold': self.POSITIVE_THRESHOLD,
        }


def test_prefilter():
    """Self-test — v4 pass-through behavior.

    Confirms the nature_recovery recall bug is NOT repeated: off-topic-but-valid
    and non-English solution content PASS (solution judgment is the model's job).
    Only base's structural checks (empty/short) still block.
    """
    prefilter = SolutionsPreFilterV4()

    pad = ' Lorem ipsum filler text to extend article length. ' * 8

    test_cases = [
        {
            'title': 'City congestion charge cuts traffic 22% over five years',
            'text': 'The scheme, now running for five years, funds public transit from its revenue.' + pad,
            'expected': (True, 'passed'),
            'description': 'English solution',
        },
        {
            # An English-keyword topic gate would drop this (no English keyword).
            # The model, not the prefilter, judges whether it is a solution.
            'title': 'España despliega un programa de bombas de calor para 12.000 hogares',
            'text': 'El gobierno ha instalado bombas de calor en 12.000 viviendas con ahorros verificados de forma independiente.' + pad,
            'expected': (True, 'passed'),
            'description': 'Non-English solution (an English gate would have blocked)',
        },
        {
            # Pure crisis/rhetoric: demotion is the student's job (Step-1 / flags),
            # not a prefilter regex.
            'title': 'Floods devastate region as experts urge policy change',
            'text': 'The damage is catastrophic and officials say something must be done, but no action was announced.' + pad,
            'expected': (True, 'passed'),
            'description': 'Pure crisis now passes (student zeroes/caps it)',
        },
        {
            'title': 'x',
            'text': 'too short',
            'expected': (False, 'content_too_short_9chars'),
            'description': 'Structural block: content too short',
        },
    ]

    print("Testing Solutions Pre-Filter v4 (commerce-only pass-through)")
    print("=" * 60)

    passed = failed = 0
    for i, test in enumerate(test_cases, 1):
        result = prefilter.apply_filter(test)
        expected = test['expected']
        match = (result[0] == expected[0] and result[1] == expected[1])
        status = "[PASS]" if match else "[FAIL]"
        passed += match
        failed += (not match)
        print(f"\nTest {i}: {status} - {test['description']}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")

    # POSITIVE_PATTERNS must match INFLECTED forms across languages — regression
    # guard for the trailing-\b bug that would make stems match only bare words.
    _pos = [re.compile(p, re.IGNORECASE) for p in prefilter.POSITIVE_PATTERNS]
    _inflected = ["deployment", "installed", "reformed", "legislation",
                  "despliega", "instalado", "programa", "riforma",
                  "einführung", "subsidie", "déploiement", "réforme"]
    _missing = [w for w in _inflected if not any(p.search(w) for p in _pos)]
    print(f"\nPOSITIVE_PATTERNS inflection check: "
          f"{'PASS' if not _missing else 'FAIL — unmatched: ' + str(_missing)}")
    assert not _missing, f"POSITIVE_PATTERNS fail to match inflected forms: {_missing}"

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{passed + failed} tests passed")
    print("\nStatistics:")
    for key, value in prefilter.get_statistics().items():
        print(f"  {key}: {value}")

    assert failed == 0, f"{failed} pass-through test(s) failed"


if __name__ == '__main__':
    test_prefilter()
