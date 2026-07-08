"""
Nature Recovery Pre-Filter v4 — commerce-only screening.

WHY v4 REWRITES v2's PREFILTER (llm-distillery #70 / recall bug):
v2's prefilter did two things that are the *model's* job and were both
English-only, costing 21.6% recall (129/598 genuine positives blocked,
mostly non-English — ~34% of nature-recovery content is es/pt/fr/de/it/
nl/id/vi/…, 20+ languages in production):

  1. `_is_nature_related` — a topic-INCLUSION gate: an article was blocked
     ("not_nature_topic") unless it contained an English nature keyword.
     Non-English positives ("se recupera", "wordt hersteld", …) carry no
     English keyword → silently dropped before the oracle ever saw them.
  2. `disaster_no_recovery` — a decline-DETECTION gate (English regex, ~43%
     precision). Deciding decline-vs-recovery is exactly what the v3/v4
     dimensional student is trained to do; doing it again here with brittle
     English regex both leaks recall and duplicates the model.

v4 strips both. Per ADR-004, commerce is the ONLY universal prefilter, and
it runs UPSTREAM in NexusMind's CommercePreprocessor (see base_prefilter
module docstring) — so this per-filter prefilter keeps only base's
validate + content-length checks and otherwise passes everything to the
recall-first e5 probe (Stage 1) + student (Stage 2). Final architecture:

    commerce (upstream) + this pass-through prefilter
      -> multilingual e5 probe (Stage 1, recall-first)
      -> Gemma-3-1B student (Stage 2).

MULTILINGUAL FORCE-PASS (POSITIVE_PATTERNS / POSITIVE_THRESHOLD):
Wired per the plan (§B.2) as the ADR-018 base mechanism — a strong-positive
count bypasses *pattern* exclusions. NOTE: it is INSURANCE-ONLY today. Base's
override bypasses only EXCLUSION_PATTERNS (not domain/source/length), and this
filter declares no local EXCLUSION_PATTERNS (commerce is upstream), so the
bypass is currently inert. It is kept so (a) the multilingual recovery
vocabulary lives in code, and (b) if a cheap local pattern exclusion is ever
added, the multilingual bypass is already in place. The real recall fix is the
gate removal above + the e5 probe — not this list.

History:
- v4.0 (2026-07): strip topic-inclusion + decline-detection gates -> commerce-
  only pass-through; add multilingual POSITIVE_PATTERNS (insurance). Class
  renamed V1->V4 to match this package's base_scorer loader.
- v2.0 (2026-04-29): declarative BasePreFilter migration (#52, ADR-018).
"""

import re
from typing import Dict

from filters.common.base_prefilter import BasePreFilter


class NatureRecoveryPreFilterV4(BasePreFilter):
    """Commerce-only pass-through pre-filter for nature recovery content.

    Inherits BasePreFilter.apply_filter unchanged (validate -> length ->
    exclusions[none] -> passed). Topic/decline gating is delegated to the
    e5 probe + student, not done here (see module docstring / #70).
    """

    VERSION = "4.0"

    # No local EXCLUSION_PATTERNS: commerce runs upstream (ADR-004), and the
    # v2 topic/decline gates are removed (the model's job). Left empty on
    # purpose — base's apply_filter then reduces to validate + length + pass.
    EXCLUSION_PATTERNS: Dict[str, list] = {}

    # Multilingual recovery signals — the ADR-018 force-pass slot. Insurance
    # only while EXCLUSION_PATTERNS is empty (see module docstring). Stems are
    # partial-word (`recuper` matches recupera/recuperación) and intentionally
    # broad; base counts total matches and bypasses pattern exclusions when the
    # count reaches POSITIVE_THRESHOLD.
    # NOTE: leading \b only — NO trailing \b. These are word-START stems meant to
    # match inflected forms (recover->recovery/recovering, recuper->recuperación),
    # so a trailing boundary would defeat the purpose (\brecover\b does NOT match
    # "recovery"). Verified in test_prefilter.
    POSITIVE_PATTERNS = [
        # English
        r'\b(recover|restor|rebound|rewild|reintroduc|bounce back)',
        # Spanish / Portuguese
        r'\b(recuper|restaur|reintroduc|se recupera|rehabilitaç|rehabilitac)',
        # French
        r'\b(rétabli|restaur|réintroduc|se rétablit|renaturation)',
        # German / Dutch
        r'\b(erholung|wiederherstell|renaturierung|herstel|wordt hersteld|terugkeer)',
        # Italian
        r'\b(ripristin|si riprende|reintroduzione)',
    ]
    POSITIVE_THRESHOLD = 2

    def get_statistics(self) -> Dict:
        """Return filter statistics."""
        return {
            'version': self.VERSION,
            'mode': 'commerce_only_passthrough',
            'exclusion_categories': len(self.EXCLUSION_PATTERNS),
            'positive_patterns': len(self.POSITIVE_PATTERNS),
            'positive_threshold': self.POSITIVE_THRESHOLD,
        }


def test_prefilter():
    """Self-test — v4 pass-through behavior.

    Confirms the two v2 recall-bug blocks are GONE: off-topic-but-valid and
    non-English recovery now PASS (topic/decline judgment is the model's job).
    Only base's structural checks (empty/short) still block.
    """
    prefilter = NatureRecoveryPreFilterV4()

    pad = ' Lorem ipsum filler text to extend article length. ' * 8

    test_cases = [
        {
            'title': 'Coral Reef Recovery After Decade of Restoration',
            'text': 'Marine biologists report significant biodiversity recovery in protected reef areas.' + pad,
            'expected': (True, 'passed'),
            'description': 'English nature recovery',
        },
        {
            # v2 blocked this as not_nature_topic (no English nature keyword).
            # The model, not the prefilter, should judge relevance now.
            'title': 'El lince ibérico se recupera en Andalucía',
            'text': 'La población del lince ibérico se recupera tras décadas de conservación; los censos muestran un aumento sostenido.' + pad,
            'expected': (True, 'passed'),
            'description': 'Non-English recovery (v2 would have blocked)',
        },
        {
            # v2 blocked this as disaster_no_recovery. Demotion is the
            # student's job (dimensional scoring), not a prefilter regex.
            'title': 'Devastating Forest Collapse Threatens Wildlife',
            'text': 'The ecosystem is dying. Habitat destruction has been catastrophic. Extinction is irreversible for several species.' + pad,
            'expected': (True, 'passed'),
            'description': 'Pure decline now passes (student demotes it)',
        },
        {
            'title': 'x',
            'text': 'too short',
            'expected': (False, 'content_too_short_9chars'),
            'description': 'Structural block: content too short',
        },
    ]

    print("Testing Nature Recovery Pre-Filter v4 (commerce-only pass-through)")
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
    # guard for the trailing-\b bug that made stems match only bare words.
    _pos = [re.compile(p, re.IGNORECASE) for p in prefilter.POSITIVE_PATTERNS]
    _inflected = ["recovery", "recovering", "restoration", "recuperación",
                  "restauración", "réintroduction", "wiederherstellung", "ripristino"]
    _missing = [w for w in _inflected if not any(p.search(w) for p in _pos)]
    print(f"\nPOSITIVE_PATTERNS inflection check: "
          f"{'PASS' if not _missing else 'FAIL — unmatched: ' + str(_missing)}")
    assert not _missing, f"POSITIVE_PATTERNS fail to match inflected forms: {_missing}"

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{passed + failed} tests passed")
    print("\nStatistics:")
    for key, value in prefilter.get_statistics().items():
        print(f"  {key}: {value}")


if __name__ == '__main__':
    test_prefilter()
