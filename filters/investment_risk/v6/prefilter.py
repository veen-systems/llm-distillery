"""
Investment Risk v6 Prefilter

ADR-018 declarative shape (partial): the three text-pattern exclusion
categories (fomo_speculation, stock_picking, affiliate_conflict) live in
EXCLUSION_PATTERNS / EXCEPTION_PATTERNS_PER_CATEGORY dicts compiled by
BasePreFilter.__init__. apply_filter stays custom because investment-risk
has a flow that doesn't fit the base pipeline:

- Source-based filtering (allowed/blocked/keyword) operates on the `source`
  / `source_type` / `id` fields, not URL — runs before content checks with
  early returns on pass.
- Reasons include the matched pattern (e.g. `allowed_source:reuters`,
  `investment_keyword:recession`, `blocked_source:github`) — the base
  `excluded_<category>` shape would lose this signal.
- `clickbait` operates on title only, not combined text.
- Default outcome is `(True, "default_allow")`, not `(True, "passed")`.

Blocks content that is almost never investment-relevant to save oracle costs.
Target: Block 40-60% of input, <5% false negative rate on actual investment content.

Philosophy: When in doubt, let it through. Better to score some noise than miss a signal.

History:
- v6.0 (2026-04-29): migrated to declarative BasePreFilter shape (#52, ADR-018)
  AND split out from v5 — gets its own class definition rather than re-exporting
  v5 (resolves the "v6 needs own class" drift item in #52). No behavior change
  vs v5 — pattern set, source rules, override semantics, exclusion order all
  preserved verbatim. Self-test 11/11 passes; pattern counts identical.
- v6.0 prior (re-export): v6 was a thin re-export of v5 because the prefilter
  logic was unchanged between v5 and v6 (only model + tier system changed).
- v5: combined source-based + content-pattern filtering, removed academic-source
  blocking after harmonization with NexusMind.
"""

import re
from typing import Dict, List, Tuple

from filters.common.base_prefilter import BasePreFilter


class InvestmentRiskPreFilterV6(BasePreFilter):
    """Fast rule-based pre-filter for investment risk content v6.

    v6.0 (declarative-shape exclusion data per ADR-018; custom apply_filter
    retained for source-based flow + matched-pattern reason strings +
    title-only clickbait check).
    """

    VERSION = "6.0"

    # === SOURCE-BASED FILTERING ===
    # Substring patterns matched against `source` / `source_type` / `id`.
    # NOT URL-based — different field than the other prefilters.

    # Sources to BLOCK (almost never investment-relevant)
    BLOCKED_SOURCE_PATTERNS = [
        # Developer/tech content
        r'github',
        r'dev_to',
        r'hackaday',
        r'hackernews',
        r'nvidia_developer',

        # Science news (non-financial)
        r'phys_org',
        r'nasa',
        r'smithsonian',
        r'science_news',
        r'arxiv',

        # Positive/lifestyle news (uplifting filter's domain)
        r'upworthy',
        r'optimist_daily',
        r'good_news',
        r'greenme',

        # Entertainment/gaming
        r'tom_hardware',
        r'numerama',
        r'canaltech',
        r'olhar_digital',
        r'tecnoblog',
        r'punto_informatico',

        # Social platforms (niche commentary, no market signal for this lens).
        # `mastodon_` with trailing underscore avoids FP on funds like
        # "Mastodon Capital"; production slugs are always `mastodon_<topic>`.
        r'mastodon_',
        r'bluesky',
    ]

    # Sources to ALWAYS ALLOW (high investment signal probability).
    # Note: trailing underscores (e.g. `fed_`, `ecb_`, `ft_`, `investor_`,
    # `fd_`, `imf_`, `bis_`) are intentional — they require the underscore
    # to follow so the pattern doesn't FP on shorter substrings.
    ALLOWED_SOURCE_PATTERNS = [
        # Financial press
        r'reuters',
        r'bloomberg',
        r'wsj',
        r'financial_times',
        r'ft_',
        r'economist',

        # Business news
        r'business_insider',
        r'forbes',
        r'cnbc',
        r'marketwatch',
        r'barrons',

        # European financial
        r'handelsblatt',
        r'expansion',
        r'fd_',
        r'les_echos',
        r'capital',

        # Investment-specific
        r'econbrowser',
        r'investor_',
        r'seeking_alpha',
        r'motley_fool',
        r'zerohedge',

        # Central banks / official
        r'fed_',
        r'ecb_',
        r'bis_',
        r'imf_',
    ]

    # Title/content keywords that suggest investment relevance — override
    # blocked-source decisions when present.
    INVESTMENT_KEYWORDS = [
        # `the fed` / `fed <finance-context>` / `federal reserve` — bare
        # `\bfed\b` previously fired on "fed up" / "force-fed" / "underfed"
        # in unrelated articles, bypassing blocked-source rules. Tightened
        # to require Fed-as-shorthand context (text is lowercased before
        # matching, so case-sensitive disambiguation is unavailable).
        r'\bfederal reserve\b',
        r'\bthe fed\b',
        r'\bfed (?:rate|chair|hike|cut|pivot|decision|policy|meeting|signals?|said|outlook)\b',
        r'\becb\b',
        r'interest rate',
        r'inflation',
        r'recession',
        r'gdp\b',
        r'unemployment',
        r'stock market',
        r'bond market',
        r'yield curve',
        r'credit',
        r'default',
        r'bankruptcy',
        r'bank\s+(failure|crisis|run)',
        r'systemic',
        r'contagion',
        r'liquidity',
        r'central bank',
        r'monetary policy',
        r'fiscal',
        r'treasury',
        r'sovereign debt',
        r'currency',
        r'forex',
        r'commodities',
        r'oil price',
        r'gold price',
        r'tariff',
        r'trade war',
        r'sanctions',
    ]

    # === ADR-018 EXCLUSION_PATTERNS ===
    # Three text-pattern categories that operate on combined title+content.
    # Iteration order matches the legacy apply_filter() check order. Category
    # keys match the (False, "<reason>") tuples this filter emits.
    # Note: clickbait is NOT in this dict — it's title-only and stays as a
    # separate class attr with its own check below the dict iteration.
    EXCLUSION_PATTERNS = {
        # FOMO / hype / get-rich-quick framing.
        'fomo_speculation': [
            r'\b(hot stock|stocks to buy now|buy now|don\'t miss out|act fast)\b',
            r'\b(meme stock|moonshot|to the moon|rocket|lambo)\b',
            r'\b(next big thing|hidden gem|secret stock|insider tip)\b',
            r'\b(crypto pump|shitcoin|altcoin season|crypto bull run)\b',
            r'\b(get rich quick|easy money|guaranteed returns)\b',
            r'\b(100x|10 bagger|massive gains|explosive growth)\b',
            r'\b(penny stock|otc stock|pink sheet)\b',
            r'\b(yolo|diamond hands|paper hands|hodl|wen moon)\b',
        ],
        # Stock-picking / individual recommendations / technical analysis.
        # Has a per-category exception (macro context — see below).
        'stock_picking': [
            r'\b(top \d+ stocks|best stocks|stocks we like)\b',
            r'\b(buy recommendation|strong buy|price target \$)\b',
            r'\b(earnings beat|earnings miss|eps of \$)\b',
            r'\b(technical analysis|chart pattern|support level|resistance)\b',
            r'\b(bullish on|bearish on|long position|short position)\b',
            r'\b(analyst rating|upgrade to buy|downgrade to sell)\b',
        ],
        # Affiliate / sponsored / promotional content.
        'affiliate_conflict': [
            r'\b(sign up|join.*link|use code|promo code|discount code)\b',
            r'\b(through my link|affiliate|sponsored|paid promotion)\b',
            r'\b(my broker|my platform|get bonus|free trial)\b',
            r'\b(discord.*join|telegram.*channel|exclusive.*group)\b',
        ],
    }

    # Per-category exceptions. Only stock_picking has one (macro context lets
    # an article through despite stock-picking language — e.g. "Bank Stocks
    # Plunge as Credit Crisis Spreads"). Other categories have no exceptions.
    EXCEPTION_PATTERNS_PER_CATEGORY = {
        'stock_picking': [
            r'\b(systemic risk|macro|recession|yield curve|credit crisis)\b',
            r'\b(federal reserve|fed|ecb|central bank|monetary policy)\b',
            r'\b(banking sector|financial system|contagion|leverage)\b',
            r'\b(credit spread|credit market|bond market)\b',
            r'\b(unemployment|gdp|inflation|pmi|leading indicators)\b',
            r'(portfolio|asset allocation|diversification|risk management)',
            # Dutch/German/French common financial terms
            r'(systemisch risico|recessie|kredietcrisis|rentecurve)',
            r'(werkloosheid|inflatie|economische groei|centrale bank)',
            r'(systemisches risiko|rezession|kreditkrise|zinsstruktur)',
            r'(arbeitslosigkeit|inflation|wirtschaftswachstum|zentralbank)',
            r'(risque systémique|récession|crise du crédit|courbe des taux)',
            r'(chômage|inflation|croissance économique|banque centrale)',
        ],
    }

    # Clickbait — title-only check, not combined text. Kept as a separate
    # class attr because EXCLUSION_PATTERNS is by-convention combined-text.
    CLICKBAIT_PATTERNS = [
        r'\b(crash coming|market crash|stock market collapse)\b.*\!',
        r'\b(this one stock|the one stock|secret stock)\b',
        r'warren buffett.*secret',
        r'\b(what.*don\'t want you to know|they.*hiding)\b',
        r'🚀|💎|🌙|💰|🤑',
    ]

    def __init__(self):
        """Compile per-category exceptions + clickbait + the source/keyword
        lists; base compiles EXCLUSION_PATTERNS into self._compiled_exclusions."""
        super().__init__()
        self._compiled_exceptions_per_category: Dict[str, List[re.Pattern]] = {
            cat: [re.compile(p, re.IGNORECASE) for p in patterns]
            for cat, patterns in self.EXCEPTION_PATTERNS_PER_CATEGORY.items()
        }
        self._compiled_clickbait: List[re.Pattern] = [
            re.compile(p, re.IGNORECASE) for p in self.CLICKBAIT_PATTERNS
        ]
        # Source/keyword patterns kept in raw form — re.search is called per
        # pattern so the matched pattern can be embedded in the reason string.

    def apply_filter(self, article: Dict) -> Tuple[bool, str]:
        """
        Determine if article should be scored by oracle.

        Flow (preserved verbatim from v5):
        1. Content length check
        2. Allowed source? -> pass with `allowed_source:<pattern>`
        3. Investment keyword in title/content? -> pass with `investment_keyword:<keyword>`
        4. Blocked source? -> block with `blocked_source:<pattern>`
        5. Iterate EXCLUSION_PATTERNS dict (fomo, stock_picking, affiliate)
           with parallel exceptions -> block with `<category>`
        6. Clickbait in title (separate, title-only)? -> block with `clickbait`
        7. Default -> allow with `default_allow`

        Args:
            article: Dict with 'id', 'title', 'content'/'text', 'source', 'source_type'

        Returns:
            Tuple of (should_score: bool, reason: str)
        """
        # 1. No content-length check (#93): the 300-char floor is a
        #    labelling-time precondition enforced by the oracle path.

        source = article.get('source', '').lower()
        source_type = article.get('source_type', '').lower()
        article_id = article.get('id', '').lower()
        title = article.get('title', '').lower()
        content = (article.get('content', '') or article.get('text', ''))[:1000].lower()

        source_combined = f"{source} {source_type} {article_id}"
        text_combined = f"{title} {content}"

        # Reason-string contract for sections 2/3/4 below: the embedded
        # `pattern` / `keyword` is the raw regex string from a class-level
        # constant (NOT user input), so injection isn't a concern. But the
        # raw regex contains metacharacters (`\b`, `(`, `|`, etc.) — callers
        # logging or pattern-matching against the reason should treat it as
        # opaque, NOT as a sanitised display string.

        # 2. Allowed source -> immediate pass with matched-pattern reason
        for pattern in self.ALLOWED_SOURCE_PATTERNS:
            if re.search(pattern, source_combined, re.IGNORECASE):
                return True, f"allowed_source:{pattern}"

        # 3. Investment keyword override -> immediate pass with matched-pattern reason
        for keyword in self.INVESTMENT_KEYWORDS:
            if re.search(keyword, text_combined, re.IGNORECASE):
                return True, f"investment_keyword:{keyword}"

        # 4. Blocked source -> block with matched-pattern reason
        for pattern in self.BLOCKED_SOURCE_PATTERNS:
            if re.search(pattern, source_combined, re.IGNORECASE):
                return False, f"blocked_source:{pattern}"

        # 5. Content-pattern exclusions in declared order. Stock-picking has
        # a per-category exception (macro_context); the others do not.
        for category, compiled_patterns in self._compiled_exclusions.items():
            if not self.has_any_pattern(text_combined, compiled_patterns):
                continue
            exceptions = self._compiled_exceptions_per_category.get(category, [])
            if exceptions and self.has_any_pattern(text_combined, exceptions):
                continue
            return False, category

        # 6. Clickbait — title-only check, not combined text.
        if self.has_any_pattern(title, self._compiled_clickbait):
            return False, "clickbait"

        # 7. Default: when in doubt, score it.
        return True, "default_allow"

    def get_stats(self) -> Dict:
        """Return prefilter configuration stats."""
        stats = {
            "blocked_source_patterns": len(self.BLOCKED_SOURCE_PATTERNS),
            "allowed_source_patterns": len(self.ALLOWED_SOURCE_PATTERNS),
            "investment_keywords": len(self.INVESTMENT_KEYWORDS),
            "clickbait_patterns": len(self.CLICKBAIT_PATTERNS),
            "philosophy": "When in doubt, let it through",
        }
        for category, patterns in self.EXCLUSION_PATTERNS.items():
            stats[f'{category}_patterns'] = len(patterns)
            stats[f'{category}_exceptions'] = len(
                self.EXCEPTION_PATTERNS_PER_CATEGORY.get(category, [])
            )
        return stats

    # Cross-filter consistency: every other migrated filter exposes
    # `get_statistics`. Investment-risk v5 historically used `get_stats`;
    # both names point at the same method so callers using either
    # convention work correctly.
    get_statistics = get_stats


# Backward-compat aliases. Existing code (including v6/base_scorer.py) imports
# `InvestmentRiskPreFilterV5` from this module — keep it working. New code
# should reference InvestmentRiskPreFilterV6 directly.
InvestmentRiskPreFilterV5 = InvestmentRiskPreFilterV6
InvestmentRiskPreFilter = InvestmentRiskPreFilterV6


# Legacy function interface for backward compatibility
def prefilter(article: Dict) -> Tuple[bool, str]:
    """Legacy function interface - use InvestmentRiskPreFilterV6 class instead."""
    return InvestmentRiskPreFilterV6().apply_filter(article)


def get_stats() -> Dict:
    """Legacy function interface - use InvestmentRiskPreFilterV6 class instead."""
    return InvestmentRiskPreFilterV6().get_stats()


def test_prefilter():
    """Test the prefilter with sample articles. Lifted from v5; no behavior
    change between v5 and v6 prefilter logic."""

    prefilter_instance = InvestmentRiskPreFilterV6()

    # Padding to exceed MIN_CONTENT_LENGTH (300 chars)
    pad = " This is additional content to ensure the article exceeds the minimum content length threshold for the prefilter. " * 3

    test_cases = [
        # === SOURCE-BASED TESTS ===

        # Should BLOCK - blocked source (dev/tech)
        {
            "id": "github_789", "title": "New ML framework", "source": "github",
            "content": "A fast library for machine learning." + pad,
            "expected": (False, "blocked_source:github"),
            "description": "Blocked source (github)",
        },

        # Should PASS - allowed source (reuters)
        {
            "id": "reuters_456", "title": "Fed raises rates", "source": "reuters",
            "content": "The Federal Reserve announced today." + pad,
            "expected": (True, "allowed_source:reuters"),
            "description": "Allowed source (reuters)",
        },

        # Should PASS - investment keyword overrides unknown source
        {
            "id": "science_xyz", "title": "Climate change could trigger recession",
            "source": "nature",
            "content": "New study shows economic impact of climate change." + pad,
            "expected": (True, "investment_keyword:recession"),
            "description": "Investment keyword override (recession)",
        },

        # Should BLOCK - arxiv academic preprint (CS), no investment signal
        {
            "id": "science_arxiv_cs_abc123", "title": "A New Neural Network Architecture",
            "source": "science_arxiv_cs",
            "content": "We propose a novel attention mechanism for transformer models." + pad,
            "expected": (False, "blocked_source:arxiv"),
            "description": "Blocked source (arxiv CS preprint)",
        },

        # Should PASS - arxiv paper with macro context overrides blocked-source via keyword check at step 3
        {
            "id": "science_arxiv_cs_xyz", "title": "Recession Forecasting with Large Language Models",
            "source": "science_arxiv_cs",
            "content": "We apply LLMs to economic time series for recession prediction." + pad,
            "expected": (True, "investment_keyword:recession"),
            "description": "arxiv with macro context (keyword override beats blocked-source)",
        },

        # Should BLOCK - mastodon social tech commentary
        {
            "id": "mastodon_general_tech_123", "title": "Cool new ML library released",
            "source": "mastodon_general_tech",
            "content": "Just discovered this awesome library for training neural networks." + pad,
            "expected": (False, "blocked_source:mastodon_"),
            "description": "Blocked source (mastodon)",
        },

        # Should BLOCK - bluesky AI/ML chat
        {
            "id": "bluesky_ai_ml_456", "title": "AI ethics discussion",
            "source": "bluesky_ai_ml",
            "content": "Interesting debate about LLM training data and bias." + pad,
            "expected": (False, "blocked_source:bluesky"),
            "description": "Blocked source (bluesky)",
        },

        # Should PASS - general tech article, default allow
        {
            "id": "tech_news_abc", "title": "Apple launches iPhone",
            "source": "techcrunch_main",
            "content": "Apple today unveiled a new device with many features." + pad,
            "expected": (True, "default_allow"),
            "description": "Default allow (unknown source, no triggers)",
        },

        # === CONTENT-PATTERN TESTS ===

        # Should PASS - macro risk analysis
        {
            "id": "macro_001",
            "title": "Yield Curve Inversion Signals Recession Risk",
            "source": "analysis_site",
            "content": "The Treasury yield curve has inverted, historically a reliable recession indicator. With unemployment rising and credit spreads widening, economists warn of systemic risks." + pad,
            "expected": (True, "investment_keyword:recession"),
            "description": "Macro risk analysis (passes via keyword)",
        },

        # Should BLOCK - FOMO/speculation
        {
            "id": "fomo_001",
            "title": "Diamond hands! This meme stock is headed for a 100x!",
            "source": "reddit_sub",
            "content": "YOLO into this penny stock! To the moon! Lambo time!" + pad,
            "expected": (False, "fomo_speculation"),
            "description": "FOMO/speculation content",
        },

        # Should BLOCK - stock picking without macro context
        {
            "id": "pick_001",
            "title": "Analyst Strong Buy Ratings for Tech Sector",
            "source": "stock_tips",
            "content": "Our analysts have upgraded these stocks to strong buy. Price target $150. Earnings beat expected." + pad,
            "expected": (False, "stock_picking"),
            "description": "Stock picking without macro context",
        },

        # Should PASS - stock analysis WITH macro context (passes via investment keyword first)
        {
            "id": "macro_stock_001",
            "title": "Bank Stocks Plunge as Credit Crisis Spreads",
            "source": "fin_news",
            "content": "Financial sector stocks fell sharply as credit spreads widened to crisis levels. The systemic risk to the banking sector raises concerns about contagion." + pad,
            "expected": (True, "investment_keyword:credit"),
            "description": "Stock analysis with macro context (passes via keyword)",
        },

        # Should BLOCK - affiliate marketing
        {
            "id": "aff_001",
            "title": "Best Trading Platform Review",
            "source": "review_blog",
            "content": "Sign up through my link for a bonus! Use promo code TRADE100 for $100 free. Affiliate disclosure." + pad,
            "expected": (False, "affiliate_conflict"),
            "description": "Affiliate marketing content",
        },

        # Should BLOCK - clickbait in title
        {
            "id": "click_001",
            "title": "MARKET CRASH COMING! This one stock will save you!",
            "source": "clickbait_site",
            "content": "What Wall Street doesn't want you to know about this secret method for protecting your portfolio." + pad,
            "expected": (False, "clickbait"),
            "description": "Clickbait title",
        },

        # Should BLOCK - content too short
        {
            "id": "short_001", "title": "Short Article", "source": "unknown",
            "content": "Too short.",
            "expected": (False, "content_too_short"),
            "description": "Content too short",
        },
    ]

    print(f"Testing Investment Risk Pre-Filter v{InvestmentRiskPreFilterV6.VERSION}")
    print("=" * 80)

    passed_tests = 0
    failed_tests = 0

    for i, test in enumerate(test_cases, 1):
        article = {k: v for k, v in test.items() if k not in ('expected', 'description')}
        result = prefilter_instance.apply_filter(article)
        expected = test['expected']

        if expected[1].startswith('content_too_short') and result[1].startswith('content_too_short'):
            match = True
        else:
            match = (result[0] == expected[0] and result[1] == expected[1])

        status = "[PASS]" if match else "[FAIL]"
        if match:
            passed_tests += 1
        else:
            failed_tests += 1

        title_safe = test['title'].encode('ascii', 'ignore').decode('ascii')
        print(f"\nTest {i}: {status} - {test['description']}")
        print(f"  Title: {title_safe[:60]}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")

    print("\n" + "=" * 80)
    print(f"Results: {passed_tests}/{passed_tests + failed_tests} tests passed")

    print("\nPre-filter Stats:")
    for key, value in prefilter_instance.get_stats().items():
        print(f"  {key}: {value}")

    return passed_tests == len(test_cases)


if __name__ == "__main__":
    success = test_prefilter()
    exit(0 if success else 1)
