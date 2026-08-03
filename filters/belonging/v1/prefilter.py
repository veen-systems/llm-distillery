"""
Belonging Pre-Filter v1.0

ADR-018 declarative shape for EXCLUSION_PATTERNS; ADR-019 hook-based
consolidation for per-category override decisions. `apply_filter()` stays
custom for URL-domain exclusions (must run first), bare reason strings
(no `excluded_` prefix — NexusMind tagging matches these directly), and
the case-sensitive `\\bRIP\\b` raw-title force-fire of `obituary_funeral`
(ADR-019 "Revisit If": hook signature doesn't expose the raw article).

Blocks content that commodifies or commercializes belonging:
- Wellness industry (longevity hacks, Blue Zone diet tips, biohacking)
- Professional networking (LinkedIn, conferences, career social capital)
- Tourism (Blue Zone tourism, experiencing "authentic" community)
- Self-help (find your tribe, build community as individual project)
- Corporate (company culture, team building, workplace belonging)

Passes content showing organic community bonds, intergenerational ties, and rootedness.

History:
- v1.0 (2026-05-22): ADR-019 hook-only consolidation. Per-category
  bypass logic (non-obit `has_exc OR pos >= threshold` rule, obit floor
  `pos >= 2 OR (has_exc AND pos >= 1)`) lifted from the apply_filter
  loop body into `_compound_override_applies`. apply_filter shrinks
  from ~65 to ~30 LOC; pos/has_exc precomputes drop from the function
  scope (the hook computes per category). 20/20 self-tests still green.
- v1.0 (2026-04-29 #2): RIP guard repair. Removed dead in-list
  `(?-i:\\bRIP\\b)` pattern (inert because text is lowercased before
  pattern matching) and added `_uppercase_rip_in_title()` — case-sensitive
  check on the raw title, consulted alongside the obituary_funeral
  category. Two new test cases (uppercase RIP obit blocks; lowercase
  rip-current still passes). 20/20 self-tests pass. See gotcha-log
  "[RESOLVED] \\bRIP\\b" entry, fix #2.
- v1.0 (2026-04-29 #1): migrated to declarative BasePreFilter shape
  (#52, ADR-018). No behavior change — pattern set, exception/positive
  lists, and per-category thresholds preserved verbatim. 19/19 self-tests.
- Earlier v1.0 work: obituary tightening + RIP false-positive fix #1
  (#45 / `598fa72` — turned out to also break the obituary signal,
  superseded by the 2026-04-29 #2 repair above), multilingual block +
  positive lists, exception pattern overrides.
"""

import re
from typing import Dict, Optional, Tuple

from filters.common.base_prefilter import BasePreFilter
from filters.common.obit_signal import OBIT_PATTERNS, uppercase_rip_in_title


class BelongingPreFilterV1(BasePreFilter):
    """Fast rule-based pre-filter for belonging content.

    v1.0 (ADR-018 EXCLUSION_PATTERNS shape + ADR-019 hook-based override
    consolidation; custom apply_filter retained for domain-first ordering,
    bare reason strings, and the case-sensitive RIP raw-title force-fire).
    """

    VERSION = "1.0"

    # === DOMAIN EXCLUSIONS (URL-based) ===

    WELLNESS_DOMAINS = [
        'mindbodygreen.com',
        'wellandgood.com',
        'goop.com',
        'healthline.com',
        'verywellmind.com',
        'psychologytoday.com',
        'longevity.technology',
        'lifeextension.com',
    ]

    PROFESSIONAL_NETWORKING_DOMAINS = [
        'linkedin.com',
        'forbes.com/sites/forbescoaches',
        'entrepreneur.com',
        'inc.com',
        'fastcompany.com',
        'hbr.org',
    ]

    TRAVEL_TOURISM_DOMAINS = [
        'lonelyplanet.com',
        'tripadvisor.com',
        'travelandleisure.com',
        'cntraveler.com',
        'afar.com',
        'fodors.com',
    ]

    SELF_HELP_DOMAINS = [
        'tinybuddha.com',
        'marcandangel.com',
        'pickthebrain.com',
        'lifehack.org',
        'zenhabits.net',
    ]

    # Mapping consumed by BasePreFilter._check_domain_exclusions (hoisted
    # from per-filter copies). Iteration order = legacy check order.
    DOMAIN_EXCLUSIONS = {
        "excluded_domain_wellness": WELLNESS_DOMAINS,
        "excluded_domain_networking": PROFESSIONAL_NETWORKING_DOMAINS,
        "excluded_domain_tourism": TRAVEL_TOURISM_DOMAINS,
        "excluded_domain_self_help": SELF_HELP_DOMAINS,
    }

    # === ADR-018 EXCLUSION_PATTERNS ===
    # Iteration order matches the legacy apply_filter() check order. Category
    # keys match the (False, "<reason>") tuples this filter emits — no
    # "excluded_" prefix because callers (NexusMind tagging, prefilter eval)
    # match these strings directly.
    #
    # PHILOSOPHY: When in doubt, let it through — the LLM oracle handles edge
    # cases. Patterns should be specific enough to avoid false negatives.
    EXCLUSION_PATTERNS = {
        # Longevity/biohacking, health optimization (specific phrases, not
        # generic words).
        'wellness_industry': [
            r'\b(longevity hacks?|longevity secrets?|longevity tips?)\b',
            r'\b(biohacks?|biohacking|life extension)\b',
            r'\b(anti-aging|anti aging|reverse aging)\b',
            r'\b(blue zone diet|okinawa diet|mediterranean diet secrets)\b',
            r'\b(centenarian secrets|secrets of the longest-lived|secrets to living longer)\b',
            r'\b(health hack|wellness hack|wellness routine|wellness protocol)\b',
            r'\b(fasting protocol|caloric restriction for longevity)\b',
            r'\b(sleep hack|sleep optimization protocol)\b',
            r'\b(nootropic|peptide therapy|supplement stack)\b',
        ],
        # Career networking + business community framing.
        'networking_professional': [
            r'\b(build your network|networking tips|networking event)\b',
            r'\b(linkedin|professional network|business network)\b',
            r'\b(social capital|career capital|professional connections)\b',
            r'\b(mastermind group|accountability partner|mentor network)\b',
            r'\b(startup ecosystem|founder community|entrepreneur community)\b',
            r'\b(coworking|co-working|wework)\b',
            r'\b(industry conference|networking conference)\b',
        ],
        # Tourism / travel-guide framing. "authentic community" intentionally
        # NOT included — it appears in positive belonging articles too.
        'tourism_consumption': [
            r'\b(visit okinawa|travel to sardinia|nicoya tourism)\b',
            r'\b(blue zone tour|blue zone travel|blue zone destination)\b',
            r'\b(ikaria greece travel|loma linda visit)\b',
            r'\b(cultural tourism|wellness tourism|wellness retreat)\b',
            r'\b(destination wellness|retreat center|wellness resort)\b',
            r'\b(immersive travel experience|experiential travel)\b',
            r'\b(travel guide|travel itinerary|travel tips)\b',
            r'\b(best time to visit|where to stay in)\b',
            r'\b(bucket list destination|must-visit destination)\b',
        ],
        # Find-your-tribe and personal-development framing.
        'self_help': [
            r'\b(find your tribe|build your tribe|create your tribe)\b',
            r'\b(build community|building community|create community)\b',
            r'\b(combat loneliness|overcome loneliness|loneliness epidemic)\b',
            r'\b(make friends|how to make friends|finding friends)\b',
            r'\b(life design|lifestyle design|design your life)\b',
            r'\b(personal development|self-improvement|self-help)\b',
            r'\b(intentional living|intentional community)\b.*\b(tips|guide|how to)\b',
            r'\b(your ikigai|find your ikigai|discover your ikigai)\b',
            r'\b(your purpose|find your purpose|discover your purpose)\b',
        ],
        # Workplace-belonging / HR framing.
        'corporate_belonging': [
            r'\b(company culture|corporate culture|workplace culture)\b',
            r'\b(employee engagement|employee experience|employee belonging)\b',
            r'\b(team building|team bonding|offsite)\b',
            r'\b(psychological safety|workplace community)\b',
            r'\b(hr strategy|people strategy|talent management)\b',
            r'\b(retention strategy|engagement strategy)\b',
            r'\b(dei initiative|diversity initiative|inclusion program)\b',
        ],
        # Online-only "community" framing — virtual / digital tribe etc.
        'online_only': [
            r'\b(discord server|discord community|slack community)\b',
            r'\b(online community|virtual community|digital community)\b',
            r'\b(facebook group|subreddit|reddit community)\b',
            r'\b(online tribe|virtual tribe|digital tribe)\b',
            r'\b(digital nomad community|remote work community)\b',
            r'\b(online membership|virtual membership)\b',
        ],
        # Obituary / funeral framing — patterns hoisted to
        # filters/common/obit_signal.py so belonging and the NexusMind#199
        # cross-lens measurement probe share one canonical pattern source.
        # See that module for per-pattern rationale and the case-sensitive
        # uppercase-RIP-in-title check (consumed below in apply_filter).
        # TODO(#51): if the trained universal obituary detector ships,
        # belonging consumes its `_is_obituary` signal instead.
        'obituary_funeral': OBIT_PATTERNS,
        # Multilingual wellness / self-help / professional-networking framing
        # (Dutch, German, French).
        'multilingual_block': [
            r'\b(levensgeluk tips|zelfhulp|persoonlijke ontwikkeling)\b',
            r'\b(netwerken voor je carrière|zakelijk netwerk)\b',
            r'\b(langlebigkeit|selbsthilfe|persönlichkeitsentwicklung)\b',
            r'\b(netzwerken|karriere netzwerk|berufliches netzwerk)\b',
            r'\b(longévité secrets|développement personnel|aide personnelle)\b',
            r'\b(réseautage professionnel|réseau professionnel)\b',
        ],
    }

    # Per-category positive-signal count needed to bypass that category's block.
    # Belonging uses thresholds rather than the binary OVERRIDE_KEYWORDS bypass
    # because individual positive signals (community/intergenerational/rooted-
    # place) vary in strength — a single keyword isn't enough to override e.g.
    # a corporate-belonging block, but several together are.
    # 'obituary_funeral' uses a custom rule (see apply_filter) and is omitted.
    POSITIVE_COUNT_THRESHOLDS = {
        'wellness_industry': 3,
        'networking_professional': 3,
        'tourism_consumption': 3,
        'self_help': 2,
        'corporate_belonging': 3,
        'online_only': 2,
        'multilingual_block': 2,
    }

    # === EXCEPTION PATTERNS — bypass any exclusion when present ===
    # Distinct from POSITIVE_SIGNAL_PATTERNS: exception detection is binary (any match
    # -> bypass), positive signals are counted.
    EXCEPTION_PATTERNS = [
        # Genuine community organizing
        r'\b(mutual aid|mutual-aid)\b',
        r'\b(community organizing|grassroots)\b',
        r'\b(worker cooperative|worker-owned)\b',
        r'\b(village council|town meeting|parish)\b',
        # Intergenerational
        r'\b(grandparent|grandmother|grandfather|elder)\b',
        r'\b(generation|generational|multigenerational)\b',
        r'\b(traditional knowledge|ancestral|heritage)\b',
        # Place-based
        r'\b(hometown|home village|native village)\b',
        r'\b(family farm|homestead|ancestral home)\b',
        r'\b(decades in|years in the same|generations of)\b',
    ]

    # === POSITIVE SIGNAL PATTERNS — counted, used in threshold checks ===
    # Renamed from POSITIVE_PATTERNS (which shadowed BasePreFilter's slot of
    # the same name) to make the semantic difference explicit. Base's
    # POSITIVE_PATTERNS feeds an "any-match-bypasses-exclusions" count check
    # gated by POSITIVE_THRESHOLD. Belonging's signals feed *per-category*
    # threshold checks in apply_filter — same data shape, different consumption.
    # The shadow was inert (POSITIVE_THRESHOLD stays at 0 so base never read
    # it), but a future maintainer setting POSITIVE_THRESHOLD > 0 would have
    # silently activated base semantics on this list. Renaming closes that
    # trap. Compiled locally into self._compiled_positive_signals.
    POSITIVE_SIGNAL_PATTERNS = [
        # Community bonds
        r'\b(neighbor|neighbours|neighborly|neighbourhood)\b',
        r'\b(piazza|town square|village square|community center)\b',
        r'\b(church community|parish|congregation|mosque|temple|synagogue)\b',
        r'\b(mutual aid|helping each other|look after each other)\b',
        # Intergenerational
        r'\b(grandchildren|grandparents|great-grandmother|great-grandfather)\b',
        r'\b(passed down|handed down|taught me|learned from)\b',
        r'\b(family recipe|traditional craft|elder wisdom)\b',
        # Rootedness
        r'\b(born and raised|grew up here|never left)\b',
        r'\b(same house|same street|same village)\b',
        r'\b(family land|ancestral|for generations)\b',
        # Slow presence
        r'\b(sunday dinner|family meal|shared meal|gathering)\b',
        r'\b(ritual|tradition|every week|every day)\b',
    ]

    MULTILINGUAL_POSITIVE_PATTERNS = [
        # Dutch belonging
        r'\b(gemeenschap|buurt|dorpsleven|buren)\b',
        r'\b(grootouders|oma|opa|generaties)\b',
        r'\b(thuisdorp|geboortedorp|familieboerderij)\b',
        # German belonging
        r'\b(gemeinschaft|nachbarschaft|dorfgemeinschaft|heimat)\b',
        r'\b(großeltern|oma|opa|generationen)\b',
        r'\b(heimatdorf|familienhof|verwurzelt)\b',
        # French belonging
        r'\b(communauté|voisinage|vie de village|quartier)\b',
        r'\b(grands-parents|mamie|papi|générations)\b',
        r'\b(village natal|ferme familiale|enracinement)\b',
    ]

    def __init__(self):
        """Compile belonging-specific patterns; base compiles EXCLUSION_PATTERNS
        into self._compiled_exclusions."""
        super().__init__()
        self._compiled_exceptions = [
            re.compile(p, re.IGNORECASE) for p in self.EXCEPTION_PATTERNS
        ]
        self._compiled_positive_signals = [
            re.compile(p, re.IGNORECASE) for p in self.POSITIVE_SIGNAL_PATTERNS
        ]
        self._compiled_multilingual_positives = [
            re.compile(p, re.IGNORECASE) for p in self.MULTILINGUAL_POSITIVE_PATTERNS
        ]

    def apply_filter(self, article: Dict) -> Tuple[bool, str]:
        """
        Determine if article should be sent to LLM for labeling.

        Custom flow (not BasePreFilter.apply_filter) for three reasons:
        URL-domain exclusions must run before content patterns; reason
        strings are bare (no `excluded_` prefix — NexusMind tagging
        contract); and the `\\bRIP\\b` raw-title force-fire of the
        `obituary_funeral` category needs the case-sensitive raw title
        that ADR-019's hook signature doesn't expose.

        Per-category bypass decisions (non-obit thresholds, obit floor)
        live in `_compound_override_applies` per ADR-019.

        Returns:
            (should_label, reason)
            - (True, "passed"): Send to LLM
            - (False, "<category>"): Block with category as reason
        """
        is_valid, validation_reason = self.validate_article(article)
        if not is_valid:
            return False, validation_reason

        # No content-length check (#93): the 300-char floor is a labelling-time
        # precondition enforced by the oracle path, not a lens rule.

        url = article.get('url', '')
        if url:
            domain_block = self._check_domain_exclusions(url)
            if domain_block:
                return False, domain_block

        combined_text = self._get_combined_clean_text(article)
        rip_in_raw_title = self._uppercase_rip_in_title(article)

        for category, compiled_patterns in self._compiled_exclusions.items():
            category_fired = self.has_any_pattern(combined_text, compiled_patterns)
            if category == 'obituary_funeral' and rip_in_raw_title:
                category_fired = True
            if not category_fired:
                continue
            if not self._category_override_applies(category, combined_text):
                return False, category

        return True, "passed"

    def _compound_override_applies(
        self, category: str, combined_lower: str
    ) -> Optional[bool]:
        """ADR-019 hook. Owns the per-category bypass decision for every
        category belonging declares — `obituary_funeral` uses the floor
        rule; the rest use the standard `has_exc OR pos >= threshold` rule
        sourced from `POSITIVE_COUNT_THRESHOLDS`.

        Positive count combines `POSITIVE_SIGNAL_PATTERNS` (English) and
        `MULTILINGUAL_POSITIVE_PATTERNS` (NL/DE/FR) — both are belonging-
        affirming signals; their counts are pooled, matching the legacy
        apply_filter() behavior.

        Returns True/False to short-circuit base's fallback chain. The
        None-defer path is only reached if a new category is added to
        EXCLUSION_PATTERNS without a corresponding entry here; we keep
        the safety net by returning None so base falls back to the dict
        (empty) and global (also empty) — net effect: block, which is
        the safe default for an unhandled new exclusion.
        """
        pos = (
            sum(len(p.findall(combined_lower)) for p in self._compiled_positive_signals)
            + sum(len(p.findall(combined_lower)) for p in self._compiled_multilingual_positives)
        )
        has_exc = any(p.search(combined_lower) for p in self._compiled_exceptions)
        if category == 'obituary_funeral':
            # Floor: require >= 2 positive signals to bypass, OR an exception
            # word PLUS at least one positive signal. Generic exception keywords
            # ("generation"/"elder") leaking into cultural-figure obits without
            # any positive belonging signal must not bypass (#45).
            return pos >= 2 or (has_exc and pos >= 1)
        threshold = self.POSITIVE_COUNT_THRESHOLDS.get(category)
        if threshold is not None and threshold > 0:
            return has_exc or pos >= threshold
        # Belonging declares POSITIVE_COUNT_THRESHOLDS for every non-obit
        # category in EXCLUSION_PATTERNS today, so this defer path is dead.
        # If a new category is added without a corresponding threshold (or
        # with threshold=0, which the guard above treats as missing), this
        # assert fires loudly instead of silently bypassing via the base
        # global-fallback chain. See review-battery 2026-05-22 retrospective.
        assert False, (
            f"belonging v1: EXCLUSION_PATTERNS category {category!r} has no "
            "POSITIVE_COUNT_THRESHOLDS entry and is not handled by the obit "
            "branch. Add one or extend _compound_override_applies."
        )

    @staticmethod
    def _uppercase_rip_in_title(article: Dict) -> bool:
        """Thin wrapper: case-sensitive `\\bRIP\\b` check on the raw title.

        The actual case-sensitivity rationale lives in
        filters/common/obit_signal.py :: uppercase_rip_in_title — see that
        module's docstring for why this can't live in EXCLUSION_PATTERNS
        with an inline `(?-i:)` flag.

        Kept as a method on this class so existing callers and tests
        continue to work after the 2026-05-05 hoist.
        """
        return uppercase_rip_in_title(article.get('title') or '')

    def get_statistics(self) -> Dict:
        """Return filter statistics"""
        stats = {
            'version': self.VERSION,
            'wellness_domains': len(self.WELLNESS_DOMAINS),
            'networking_domains': len(self.PROFESSIONAL_NETWORKING_DOMAINS),
            'tourism_domains': len(self.TRAVEL_TOURISM_DOMAINS),
            'self_help_domains': len(self.SELF_HELP_DOMAINS),
            'exception_patterns': len(self.EXCEPTION_PATTERNS),
            'positive_patterns': len(self.POSITIVE_SIGNAL_PATTERNS),
            'multilingual_positive_patterns': len(self.MULTILINGUAL_POSITIVE_PATTERNS),
        }
        for category, patterns in self.EXCLUSION_PATTERNS.items():
            stats[f'{category}_patterns'] = len(patterns)
        return stats


def test_prefilter():
    """Test the prefilter with sample articles"""

    prefilter = BelongingPreFilterV1()

    test_cases = [
        # Should BLOCK - Content too short
        {
            'title': 'Short Article',
            'text': 'This is too short.',
            'expected': (False, 'content_too_short')
        },

        # Should BLOCK - Wellness industry
        {
            'title': '5 Longevity Hacks from Blue Zone Centenarians',
            'text': 'Researchers have discovered the longevity secrets of the world\'s longest-lived communities. '
                    'These biohacking tips can help you optimize your lifespan and extend your healthspan significantly. '
                    'Supplements and intermittent fasting are key strategies used by centenarians in Okinawa. '
                    'Learn how to use anti-aging techniques and proven longevity hacks to reach 100. '
                    'The Blue Zone diet research shows remarkable results for those who follow these protocols.',
            'expected': (False, 'wellness_industry')
        },

        # Should BLOCK - Professional networking
        {
            'title': 'How to Build Your Professional Network for Career Success',
            'text': 'Building your network is essential for career growth in today\'s competitive marketplace. '
                    'LinkedIn connections and networking events can help you develop valuable social capital. '
                    'Join a mastermind group or find an accountability partner to accelerate your professional development. '
                    'The startup ecosystem thrives on these connections between founders and investors. '
                    'Strategic networking is the key to unlocking new opportunities and advancing your career.',
            'expected': (False, 'networking_professional')
        },

        # Should BLOCK - Tourism
        {
            'title': 'Visit Okinawa: A Travel Guide to Blue Zone Living',
            'text': 'Planning to visit Okinawa? This comprehensive travel guide covers the best time to visit, '
                    'where to stay, and must-visit destinations in this beautiful island paradise. '
                    'Experience cultural tourism at its finest in this Blue Zone destination known for longevity. '
                    'Our detailed itinerary includes wellness retreats, authentic local experiences, and travel tips '
                    'for making the most of your bucket list destination trip to Japan\'s southern islands.',
            'expected': (False, 'tourism_consumption')
        },

        # Should BLOCK - Self-help
        {
            'title': 'How to Find Your Tribe and Combat Loneliness',
            'text': 'Finding your tribe is essential for personal development and living your best life. '
                    'Learn how to build community and overcome loneliness with these practical tips and strategies. '
                    'Life design experts recommend intentional living and discovering your ikigai for fulfillment. '
                    'Here\'s how to make friends, create your tribe, and build meaningful connections in modern life. '
                    'Personal development starts with surrounding yourself with the right people.',
            'expected': (False, 'self_help')
        },

        # Should BLOCK - Corporate
        {
            'title': 'Building Workplace Belonging: HR Strategy Guide',
            'text': 'Company culture is key to employee engagement and organizational success in modern business. '
                    'This comprehensive guide covers workplace belonging initiatives, team building strategies, '
                    'and psychological safety best practices for creating an inclusive environment. '
                    'Learn how to improve your retention strategy through better employee experience programs. '
                    'DEI initiatives and engagement strategies are essential for building a thriving workplace.',
            'expected': (False, 'corporate_belonging')
        },

        # Should PASS - Genuine intergenerational community
        {
            'title': 'In This Village, Four Generations Share Sunday Dinner',
            'text': 'Every Sunday, Maria\'s family gathers at her grandmother\'s house for the weekly meal. '
                    'Her great-grandmother, now 94, still makes the family recipe pasta she learned from her mother. '
                    'The tradition has passed down through generations. Neighbors often join, as they have for decades. '
                    'The village has remained largely unchanged, with families who have lived here for generations '
                    'still gathering in the town square each evening.',
            'expected': (True, 'passed')
        },

        # Should PASS - Mutual aid
        {
            'title': 'After the Flood, Neighbors Became Family',
            'text': 'When the flood hit, neighbors who had barely spoken began checking on each other daily. '
                    'Rosa organized a mutual aid network for elderly residents. Three months later, the group still '
                    'meets every week for shared meals. The parish church became a gathering point. Grandparents '
                    'who had lived in the area for decades led the organizing efforts.',
            'expected': (True, 'passed')
        },

        # Should PASS - Rooted family
        {
            'title': 'Five Generations on the Same Farm',
            'text': 'The Johansen family has worked this land for five generations. Great-grandmother Elsa, 96, '
                    'still lives in the ancestral home where she was born. Every harvest, the extended family '
                    'gathers to help, a tradition handed down since her grandfather\'s time. The neighboring families '
                    'have known each other for over a century, helping each other through hardship.',
            'expected': (True, 'passed')
        },

        # Should BLOCK - Obituary/funeral
        {
            'title': 'Roy Keane Mourns Mother Marie at Funeral Mass',
            'text': 'Former Manchester United captain Roy Keane was among mourners paying tribute at the funeral '
                    'mass of his mother Marie Keane, who passed away last Tuesday aged 82. Family and friends '
                    'gathered to offer condolences at the service. She is survived by her six children and '
                    'fourteen grandchildren. Marie was laid to rest at the local cemetery following the service.',
            'expected': (False, 'obituary_funeral')
        },

        # Should PASS - Funeral with genuine heritage/elder significance (exception overrides)
        {
            'title': 'Elder\'s Funeral Revives Ancestral Mourning Tradition Lost for Decades',
            'text': 'When elder Nana Yaa passed, the village revived the ancestral mourning ritual that had not '
                    'been performed in three generations. Grandparents taught the younger generation the traditional '
                    'songs passed down through heritage. The multigenerational gathering at the funeral brought '
                    'together families who had scattered, reconnecting them with their ancestral home and traditions.',
            'expected': (True, 'passed')
        },

        # Should BLOCK - Obituary leak cases from issue #45 (NexusMind#156)
        # Each one previously bypassed: dies-with-verb-variant, procession,
        # killed-in-year, two-digit age in dies-at-N, cultural-figure obit
        # tripping bare "generation" exception.
        {
            'title': 'Hong Kong Activist Dies After Decades of Protest',
            'text': 'A prominent pro-democracy figure passed away this week after suffering health complications. '
                    'The activist had been involved in protest movements since the 1980s, organizing demonstrations '
                    'and public campaigns over four decades. Statements have been issued by political groups '
                    'acknowledging the loss. The activist is remembered for sustained advocacy work spanning generations.',
            'expected': (False, 'obituary_funeral')
        },
        {
            'title': 'Silent Procession Held for Stabbed Man',
            'text': 'A silent procession took place in the city center today following the stabbing death of a local '
                    'resident last week. Hundreds gathered to walk in solemn formation along the high street. The '
                    'route ended at the location where the incident occurred. Local officials joined the procession '
                    'alongside family members and friends.',
            'expected': (False, 'obituary_funeral')
        },
        {
            'title': 'Family Killed in 1976 Bombing Remembered',
            'text': 'Half a century after the bombing that killed a family of four, descendants and local historians '
                    'gathered at the memorial site. The event marked the anniversary of the attack which claimed '
                    'lives during the height of the conflict. A wreath was laid at the plaque, and a moment of '
                    'silence observed. Speeches recalled the victims and the broader toll of that period.',
            'expected': (False, 'obituary_funeral')
        },
        {
            'title': 'Mexican Muralist Dies at 99',
            'text': 'Melchor Peredo Garcia, the Mexican muralist whose large-scale public works adorned several state '
                    'government buildings, has died at the age of 99. Born in Veracruz, his career spanned more than '
                    'seven decades. He was a contemporary of figures from the post-Rivera generation and contributed '
                    'to the indigenismo aesthetic. His murals depict pre-Columbian themes and rural life.',
            'expected': (False, 'obituary_funeral')
        },
        {
            'title': 'Moya Brennan of Clannad Dies at 73',
            'text': 'Moya Brennan, the lead singer of Irish folk band Clannad, has died at age 73 after a short '
                    'illness. Brennan was the eldest of nine children from the musical Brennan family, which gave '
                    'rise to both Clannad and her sister Enya\'s solo career. Across five decades the band brought '
                    'traditional Irish music to global audiences. Tributes have come in from across the music world.',
            'expected': (False, 'obituary_funeral')
        },

        # Should BLOCK - uppercase RIP token in title is a strong obit signal.
        # Pre-repair, this would have passed because the in-list `(?-i:\bRIP\b)`
        # pattern was inert (text was lowercased before pattern matching).
        # Repair: title-only case-sensitive `\bRIP\b` check via
        # _uppercase_rip_in_title. Article has no positive belonging signal
        # (positive_count == 0), so the obituary floor blocks.
        {
            'title': 'Tributes Pour In: RIP Hero Of Local Sports Coverage',
            'text': 'Hundreds of messages have appeared on social media following the announcement '
                    'this morning. Industry colleagues have been sharing their reactions throughout '
                    'the day. Officials confirmed the news in a brief statement, with further details '
                    'expected later this week. Several outlets are preparing longer-form remembrances. '
                    'The community gathered to recognise the contribution made over many decades.',
            'expected': (False, 'obituary_funeral')
        },

        # Should PASS - lowercase "rip currents" must NOT match the case-
        # sensitive RIP check (preserved post-repair). Beach safety articles
        # are common; this is the original #45-follow-up regression case.
        {
            'title': 'Lifeguards Warn of Rip Currents at Local Beaches',
            'text': 'Coastal authorities are reminding swimmers about the dangers of rip currents this summer. '
                    'Several beach communities have installed new warning signs explaining how to identify and '
                    'escape a rip current. Local surf clubs are organizing free water-safety workshops for families. '
                    'The lifeguard service has expanded patrol hours along the popular stretches of coastline. '
                    'Many beachgoers may not realize how powerful a rip can be, particularly during high tide.',
            'expected': (True, 'passed')
        },

        # Should BLOCK - Override-logic isolation test. Article matches ONE obit
        # pattern (dies at \d+) and trips the "generation" exception keyword,
        # but carries no actual belonging signal (positive_count = 0). The
        # pos>=1 floor on the obit branch must block this even with the
        # exception. Pre-fix (without the floor), this would have passed.
        {
            'title': 'Op-Ed: How a Generation Lost Its Voice as the Author Dies at 84',
            'text': 'When the columnist died at 84 last week, she carried with her a particular generation\'s '
                    'sensibility. Her work for several decades influenced political writing and rhetorical style. '
                    'Editors at the publication she served for thirty years have issued statements about her '
                    'contribution to journalism. The newsroom plans an editorial retrospective next month. The '
                    'literary world will be poorer without her acid wit and her willingness to call out hypocrisy.',
            'expected': (False, 'obituary_funeral')
        },

        # Should BLOCK - Online only community (may also match self_help due to "build community")
        {
            'title': 'Join Our Thriving Discord Server Community',
            'text': 'Our online community has grown to 5,000 members in the Discord server over the past year. '
                    'We host virtual events every week and have a Slack community for discussions with members. '
                    'Join our Facebook group for daily engagement with like-minded individuals from around the world. '
                    'Our digital community is thriving with members connecting virtually through video calls. '
                    'The virtual community offers courses, webinars, and networking opportunities for all members.',
            'expected': (False, 'online_only')
        },
    ]

    print("Testing Belonging Pre-Filter v1.0")
    print("=" * 60)

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        result = prefilter.apply_filter(test)
        expected = test['expected']

        # Check if result matches expected (handle partial match for reasons)
        result_matches = (
            result[0] == expected[0] and
            (result[1] == expected[1] or result[1].startswith(expected[1]))
        )

        status = "[PASS]" if result_matches else "[FAIL]"
        if result_matches:
            passed += 1
        else:
            failed += 1

        print(f"\nTest {i}: {status}")
        print(f"Title: {test['title'][:50]}...")
        print(f"Expected: {expected}")
        print(f"Got:      {result}")

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("\nPre-filter Statistics:")
    for key, value in prefilter.get_statistics().items():
        print(f"  {key}: {value}")


if __name__ == '__main__':
    test_prefilter()
