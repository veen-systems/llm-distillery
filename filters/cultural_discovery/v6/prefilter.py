"""
Cultural Discovery Pre-Filter v6 — commerce-only pass-through.

WHAT CHANGED, AND ON WHAT EVIDENCE (#98 criterion 4, owner decision 2026-08-06)
------------------------------------------------------------------------------
v6 deletes the keyword screen v5 carried — 453 topic-gate stems across ~25
languages, four exclusion categories with their parallel per-category exception
lists, three domain blocklists, and the custom `apply_filter` that drove them.
800 lines to ~90. Screening moves to the multilingual e5 probe
(`probe/embedding_probe_e5small.pkl`), which screens on meaning rather than
word-stems and therefore cannot have a per-language coverage gap by
construction — the defect #86 spent 2026-08-06 patching stem-by-stem.

This was NOT a tidy-up on faith. Per ADR-021 the gate was only removed after the
probe beat it on held-out ORACLE ground truth, same rows, same measurement:

    held-out oracle false negatives   probe 0/75   keyword gate 10/75

The gate's 10 misses are the per-language gap made concrete. Criteria 1-3 of #98
(recall cost, screen-out fraction, FN rate on MEDIUM+) were all cleared before
this file was touched; criterion 4 is this commit.

WHAT NOW BLOCKS AN ARTICLE HERE: essentially nothing
----------------------------------------------------
Inheriting `BasePreFilter.apply_filter` unchanged, the pipeline is
`validate -> exclusions[none] -> passed`. With EXCLUSION_PATTERNS empty the
only rejection left is `validate_article` (missing or empty title/body). There
is no length check — the 300-char floor is a labelling-time rule enforced in
`ground_truth.batch_scorer.make_oracle_prefilter`, not here (#93). Empty is not
short.

That emptiness is not looseness; it is what remains after the probe took the
job over. It is the same shape as `nature_recovery v4` and `solutions v6`, both
of which declare `EXCLUSION_PATTERNS = {}` for exactly this reason, and it is
what ADR-004 means by "commerce is the only universal prefilter" — commerce runs
UPSTREAM in NexusMind's CommercePreprocessor, not here.

    commerce (upstream) + this pass-through prefilter
      -> multilingual e5 probe (Stage 1, recall-first, threshold 2.50)
      -> Gemma-3-1B student (Stage 2)

THREE THINGS A READER OF THIS FILE WILL GET WRONG
-------------------------------------------------
1. **The screening this replaces never ran in production.** The per-lens rule
   prefilter has not executed in NexusMind's scoring path since 2026-02-10 —
   the GPU scorer builds every scorer with `use_prefilter=False` and calls
   `score_batch(skip_prefilter=True)` (ducroq/NexusMind#284). It DID run in
   this repo's oracle/training path, which is the path this change affects:
   what the oracle gets asked to label.
2. **The probe is not a like-for-like swap of two dormant mechanisms — it runs.**
   So this turns cultural_discovery's screening on for readers for the first
   time. Per ADR-022 the probe ships stamping-only; enforcement is a separate
   config flip, and must not ride along with this commit.
3. **v6 cannot score yet.** The package has a `hybrid_inference` config block
   and a trained probe but NO inference module and NO `calibration.json`, and
   `_load_calibration` fails silent. Nothing here fixes that; it is tracked
   separately and is deliberately out of scope.

DELETED WITH THE GATE, AND WHY IT WAS SAFE
------------------------------------------
- `classify_content_type()` — oracle pre-classification helper. Grepped before
  deletion: its only callers across the whole repo were the self-tests inside
  each cultural_discovery version's own prefilter.py. No pipeline consumed it.
- `DISCOVERY_PATTERNS` — 13 English-only stems that fed `classify_content_type`
  and doubled as an OR-branch of the topic gate. #99 measured them as an
  English-only escape hatch: 66/516 English rows, 0/265 non-English. Deleting
  the gate deletes the escape hatch, which closes #99 by removal rather than by
  translation.
- `DOMAIN_EXCLUSIONS` (VC/startup, defense, code-hosting) — dropped so this
  filter matches the declarative reference shape, which declares none. NOTE:
  these were never part of the #98 probe-vs-gate measurement, so their removal
  is a judgement call, not a measured one. If oracle spend on tech-wire copy
  rises, they are the first thing to reinstate — as a declarative
  `DOMAIN_EXCLUSIONS` dict, no custom `apply_filter` needed.

History:
- v6.0 (2026-08-06): strip topic gate + exclusion categories + domain lists ->
  commerce-only pass-through on the pure ADR-018/019 declarative shape (#98
  criterion 4). Closes #99 by removal.
- v6.0 prior (2026-08-06): carried v5's rules byte-identical so the probe could
  be A/B'd against them on identical rows.
- v5.0 / v4.0 (2026-04-29): declarative BasePreFilter migration of the exclusion
  data (#52, ADR-018); custom apply_filter retained for per-category exceptions.
"""

from typing import Dict, List

from filters.common.base_prefilter import BasePreFilter


class CulturalDiscoveryPreFilterV6(BasePreFilter):
    """Commerce-only pass-through pre-filter for cultural discovery content.

    Inherits `BasePreFilter.apply_filter` unchanged (validate -> exclusions
    [none] -> passed). Topic judgment is delegated to the e5 probe + student,
    not done here — see the module docstring and #98.
    """

    VERSION = "6.0"

    # Empty ON PURPOSE, not by omission. Commerce runs upstream (ADR-004) and
    # topic screening is the probe's job (#98). With this empty, base's
    # `_is_excluded` short-circuits and `apply_filter` reduces to
    # validate + pass. Anything added here re-creates the per-language coverage
    # gap the probe exists to remove — measure against held-out oracle ground
    # truth first (ADR-021).
    EXCLUSION_PATTERNS: Dict[str, List[str]] = {}

    # No force-pass list. nature_recovery v4 keeps POSITIVE_PATTERNS as
    # insurance, but base's override bypasses only EXCLUSION_PATTERNS — with
    # none declared it is inert there, and would be inert here too. Declaring an
    # inert mechanism is the failure mode this repo keeps re-learning
    # (ducroq/NexusMind#284, #94), so it is left out rather than shipped dark.

    def get_statistics(self) -> Dict:
        """Return filter statistics."""
        return {
            'version': self.VERSION,
            'mode': 'commerce_only_passthrough',
            'exclusion_categories': len(self.EXCLUSION_PATTERNS),
            'domain_exclusions': len(self.DOMAIN_EXCLUSIONS),
            'screening_delegated_to': 'e5 probe (stage 1) + student (stage 2)',
        }


def test_prefilter():
    """Self-test — v6 pass-through behavior.

    The four cases below are the ones v5's gate BLOCKED. They pass now by
    design: judging them is the probe's job and then the student's. The last
    case is the only structural block left.
    """
    prefilter = CulturalDiscoveryPreFilterV6()

    pad = ' Lorem ipsum filler text to extend article length. ' * 8

    test_cases = [
        {
            'title': 'The Culture War Over Museum Collections',
            'text': "Critics slammed the museum's decision in a viral backlash. "
                    "The controversy sparked debate about identity politics in arts institutions." + pad,
            'expected': (True, 'passed'),
            'description': 'v5 blocked as political_conflict — the student demotes it now',
        },
        {
            'title': 'Top 10 Must-See Hidden Gems in Kyoto',
            'text': 'Bucket list destinations with breathtaking views. Book now for an '
                    'unforgettable experience; here is where to stay and how to get there.' + pad,
            'expected': (True, 'passed'),
            'description': 'v5 blocked as tourism_fluff',
        },
        {
            'title': 'Sungrow to supply 125 MWh of grid battery storage',
            'text': 'The utility announced a supply agreement for grid-supporting '
                    'battery storage across four project sites.' + pad,
            'expected': (True, 'passed'),
            'description': 'Off-lens: v5 blocked as no_cultural_topic_signal, probe screens it now',
        },
        {
            # The class the keyword gate structurally could not cover: a genuine
            # cultural-discovery article in a language with no stems in the list.
            # 10 of these were the gate's held-out oracle false negatives.
            'title': 'Kaevamistel leiti muinasaegne matmispaik',
            'text': 'Arheoloogid leidsid põllult muinasaegse matmispaiga, kust tuli välja '
                    'mitukümmend eset ja luustikku, mis pärinevad rauaajast.' + pad,
            'expected': (True, 'passed'),
            'description': 'Non-English positive — the gap the probe removes (#98)',
        },
        {
            'title': '',
            'text': '',
            'expected': (False, 'empty_title'),
            'description': 'Structural block: validate_article rejects empty',
        },
    ]

    print("Testing Cultural Discovery Pre-Filter v6 (commerce-only pass-through)")
    print("=" * 68)

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

    # Regression guard: the whole point of v6 is that no lens rules survive here.
    # A future edit that re-adds a category must fail loudly, not quietly reduce
    # recall on languages nobody tests in.
    assert not prefilter.EXCLUSION_PATTERNS, (
        "v6 must declare no lens exclusion rules — screening belongs to the e5 probe (#98)"
    )
    assert not prefilter.DOMAIN_EXCLUSIONS, (
        "v6 must declare no domain blocklists — see the module docstring before re-adding"
    )
    print("\nDeclarative-shape guard: PASS (no exclusion categories, no domain lists)")

    print("\n" + "=" * 68)
    print(f"Results: {passed}/{passed + failed} tests passed")
    print("\nStatistics:")
    for key, value in prefilter.get_statistics().items():
        print(f"  {key}: {value}")

    assert failed == 0, f"{failed} prefilter self-test case(s) failed"


if __name__ == '__main__':
    test_prefilter()
