# ground_truth/text_cleaning.py
"""
Comprehensive text cleaning utilities for LLM distillery.

Ported from content-aggregator to ensure robust text processing
for training data generation. Handles:
- Invalid Unicode (surrogates)
- Zero-width characters (invisible text)
- Bidirectional marks (security issue)
- Whitespace normalization
- HTML content cleaning

Use sanitize_text_comprehensive() for all text before LLM labeling.
"""

import re
import html
from typing import Dict, List, Any, Union


def remove_zero_width_characters(text: str) -> str:
    """
    Remove zero-width characters that can break text matching and hide content.

    Removes:
    - Zero-width space (U+200B)
    - Zero-width non-joiner (U+200C)
    - Zero-width joiner (U+200D)
    - Byte Order Mark (U+FEFF)
    - Word joiner (U+2060)
    - Mongolian vowel separator (U+180E)

    Args:
        text: String that may contain zero-width characters

    Returns:
        Cleaned string with zero-width characters removed
    """
    if not isinstance(text, str):
        return str(text)

    # Remove all zero-width characters
    zero_width_chars = [
        '\u200b',  # Zero-width space
        '\u200c',  # Zero-width non-joiner
        '\u200d',  # Zero-width joiner
        '\ufeff',  # Byte Order Mark (BOM) / Zero-width no-break space
        '\u2060',  # Word joiner
        '\u180e',  # Mongolian vowel separator (deprecated but still used)
    ]

    for char in zero_width_chars:
        text = text.replace(char, '')

    return text


def remove_bidi_marks(text: str) -> str:
    """
    Remove bidirectional text marks that can be used to hide malicious content.

    Removes:
    - Left-to-right mark/embedding/override
    - Right-to-left mark/embedding/override
    - Pop directional formatting

    These can be used to manipulate text display and hide malicious URLs or content.
    Critical for security when processing untrusted web content.

    Args:
        text: String that may contain BiDi marks

    Returns:
        Cleaned string with BiDi marks removed
    """
    if not isinstance(text, str):
        return str(text)

    # Remove bidirectional formatting characters
    bidi_chars = [
        '\u200e',  # Left-to-right mark
        '\u200f',  # Right-to-left mark
        '\u202a',  # Left-to-right embedding
        '\u202b',  # Right-to-left embedding
        '\u202c',  # Pop directional formatting
        '\u202d',  # Left-to-right override
        '\u202e',  # Right-to-left override
        '\u2066',  # Left-to-right isolate
        '\u2067',  # Right-to-left isolate
        '\u2068',  # First strong isolate
        '\u2069',  # Pop directional isolate
    ]

    for char in bidi_chars:
        text = text.replace(char, '')

    return text


def normalize_whitespace(text: str) -> str:
    """
    Normalize excessive whitespace while preserving paragraph breaks.

    - Converts tabs to spaces
    - Reduces multiple spaces to single space
    - Reduces excessive newlines (>2) to double newline
    - Strips leading/trailing whitespace

    Args:
        text: String with potentially excessive whitespace

    Returns:
        String with normalized whitespace
    """
    if not isinstance(text, str):
        return str(text)

    # Replace tabs with spaces
    text = text.replace('\t', ' ')

    # Normalize multiple spaces to single space
    text = re.sub(r' {2,}', ' ', text)

    # Normalize excessive newlines (more than 2) to double newline
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove spaces at start/end of lines
    text = '\n'.join(line.strip() for line in text.split('\n'))

    return text.strip()


def clean_html_entities(text: str) -> str:
    """
    Decode HTML entities to their Unicode equivalents.

    Converts:
    - &nbsp; → space
    - &amp; → &
    - &lt; → <
    - &gt; → >
    - &quot; → "
    - &#39; → '
    - And all other HTML entities

    Args:
        text: String that may contain HTML entities

    Returns:
        String with HTML entities decoded
    """
    if not isinstance(text, str):
        return str(text)

    try:
        # Use html.unescape for comprehensive entity decoding
        text = html.unescape(text)
    except Exception:
        # Fallback to manual replacements
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")

    return text


def remove_html_tags(text: str) -> str:
    """
    Remove HTML tags using regex.

    This is a lightweight alternative to BeautifulSoup for simple HTML removal.
    For complex HTML parsing, use content-aggregator's ContentCleaner instead.

    Args:
        text: String that may contain HTML tags

    Returns:
        String with HTML tags removed
    """
    if not isinstance(text, str):
        return str(text)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Clean up common HTML artifacts
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)  # Named entities we missed
    text = re.sub(r'&#\d+;', ' ', text)  # Numeric entities

    return text


def sanitize_unicode(text: str) -> str:
    """
    Remove surrogate characters and other invalid Unicode sequences.

    Prevents encoding errors when processing articles scraped from the web.
    Invalid Unicode is silently dropped using errors='ignore'.

    Args:
        text: String that may contain invalid Unicode

    Returns:
        Cleaned string with invalid Unicode removed
    """
    if not isinstance(text, str):
        return str(text)

    # Encode with errors='ignore' to drop surrogates, then decode
    return text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')


def sanitize_text_comprehensive(text: str) -> str:
    """
    Apply all text cleaning operations for comprehensive sanitization.

    Removes:
    - Invalid Unicode (surrogates)
    - HTML entities
    - HTML tags
    - Zero-width characters
    - Bidirectional marks (security)
    - Normalizes whitespace

    This is the RECOMMENDED function for cleaning text before LLM labeling.
    Use this for all article text in the distillery pipeline.

    Args:
        text: Text to clean

    Returns:
        Comprehensively cleaned text

    Example:
        >>> text = "Hello&#39;\\ud800\\u200bWorld\\u202e<script>bad</script>"
        >>> sanitize_text_comprehensive(text)
        "Hello'World"
    """
    if not isinstance(text, str):
        text = str(text)

    # Apply all cleaning operations in order
    text = sanitize_unicode(text)
    text = clean_html_entities(text)
    text = remove_html_tags(text)
    text = remove_zero_width_characters(text)
    text = remove_bidi_marks(text)
    text = normalize_whitespace(text)

    return text


# Boilerplate signatures of scrape artifacts that carry no article body.
# Two tiers, because false-positives here silently discard genuine articles:
#   STRONG — pure UI / bot-check / JS-shim text that never forms a real article
#     subject. A single hit in a short body is junk.
#   WEAK — topical phrases a genuine article can legitimately be ABOUT (cookie
#     law, a paywall debate, a 404 postmortem). One hit alone is NOT enough;
#     junk only when the body is boilerplate-dominated (>=2 distinct weak hits,
#     or a single weak hit in an essentially body-less stub).
_SCRAPE_JUNK_STRONG = [
    r'\benable\s+javascript\b',
    r'\bjavascript\s+is\s+(?:disabled|required|not\s+available|turned\s+off)\b',
    r'\bchecking\s+your\s+browser\b',
    r'\b(?:are\s+you\s+a\s+(?:robot|human)|verify\s+you\s+are\s+human)\b',
    r'\benable\s+cookies\s+and\s+reload\b',
    # Non-English UI / bot-check shims (es/it/de/nl/pt/fr) — production is ~29%
    # non-English (Solutions v4); an English-only list is the nature_recovery
    # dropped-non-English gate in embedding form. These never form a real article
    # subject, so a single hit in a short body is junk (STRONG tier).
    r'\bactiv(?:er|ez)\s+(?:le\s+)?javascript\b',                # fr
    r'\bjavascript\s+est\s+d[ée]sactiv[ée]\b',                   # fr
    r'\b(?:bitte\s+)?aktivieren\s+sie\s+javascript\b',           # de
    r'\bjavascript\s+ist\s+deaktiviert\b',                       # de
    r'\bactiv(?:a|e|ar)\s+(?:el\s+)?javascript\b',               # es
    r'\bjavascript\s+est[áa]\s+desactivad[oa]\b',                # es
    r'\babilita(?:re)?\s+(?:il\s+)?javascript\b',                # it
    r'\bjavascript\s+[èe]\s+disabilitato\b',                     # it
    r'\bschakel\s+javascript\s+in\b',                            # nl
    r'\bjavascript\s+is\s+uitgeschakeld\b',                      # nl
    r'\bative\s+o\s+javascript\b',                               # pt
    r'\bjavascript\s+est[áa]\s+desativad[oa]\b',                 # pt
    # Google consent interstitial (the Solutions v4 consent-wall poison, all
    # languages) — the exact "before you continue to Google" wall. Never a body.
    r'\bbefore\s+you\s+continue\s+to\s+google\b',                # en
    r'\bavant\s+d.?acc[ée]der\s+[àa]\s+google\b',                # fr
    r'\bbevor\s+sie\s+zu\s+google\s+weitergehen\b',              # de
    r'\bantes\s+de\s+ir\s+a\s+google\b',                         # es
    r'\bprima\s+di\s+continuare\s+su\s+google\b',                # it
    r'\bvoordat\s+u\s+verdergaat\s+naar\s+google\b',             # nl
    r'\bantes\s+de\s+(?:ir\s+para|continuar\s+no)\s+google\b',   # pt
]
_SCRAPE_JUNK_WEAK = [
    r'\bwe\s+(?:and\s+our\s+partners\s+)?use\s+cookies\b',
    r'\baccept(?:ing)?\s+(?:all\s+)?cookies\b',
    r'\bcookie\s+(?:policy|consent|preferences|settings|notice)\b',
    r'\bconsent\s+to\s+the\s+use\s+of\s+cookies\b',
    r'\bmanage\s+(?:your\s+)?(?:cookie\s+)?preferences\b',
    r'\bsubscribe\s+to\s+(?:continue|read)\b',
    r'\bsign\s+in\s+to\s+(?:continue|read)\b',
    r'\bregister\s+to\s+(?:continue|read)\b',
    r'\bthis\s+(?:content|page|article|video)\s+is\s+(?:not\s+available|unavailable)\b',
    r'\bpage\s+not\s+found\b',
    r'\b40[34]\b[^.]{0,40}\b(?:not\s+found|forbidden|error)\b',
    r'\baccess\s+denied\b',
    # Non-English cookie / consent / paywall / error (es/it/de/nl/pt/fr) — topical
    # phrases a genuine article can be ABOUT, so WEAK: needs >=2 distinct hits or a
    # body-less stub, never a single hit in a real brief (mirrors the English tier).
    r'\b(?:verwenden|utilisons|usamos|utilizamos|utilizziamo|gebruiken)\s+cookies\b',
    r'\bcookie[- ]?(?:richtlinie|einstellungen|einwilligung)\b',          # de
    r'\b(?:politique|param[èe]tres|gestion)\s+(?:des\s+)?cookies\b',      # fr
    r'\b(?:pol[íi]tica|configuraci[óo]n|preferencias)\s+de\s+cookies\b',  # es/pt
    r'\b(?:informativa|impostazioni|preferenze)\s+(?:sui\s+)?cookie\b',   # it
    r'\bcookie(?:beleid|instellingen|voorkeuren)\b',                      # nl
    r'\bacept(?:ar|a|e)\s+(?:todas\s+)?(?:las\s+)?cookies\b',             # es
    r'\baccepter\s+(?:tous\s+)?les\s+cookies\b',                          # fr
    r'\b(?:alle\s+)?cookies\s+akzeptieren\b',                             # de
    r'\baccetta(?:re)?\s+(?:tutti\s+)?i\s+cookie\b',                      # it
    r'\babonn(?:ez[- ]vous|er)\s+pour\s+(?:lire|continuer)\b',            # fr
    r'\bsuscr[íi]b[a-z]*\s+para\s+(?:seguir\s+)?(?:leyendo|continuar)\b', # es
    r'\babonnieren\s+sie[,\s]+um\s+weiterzulesen\b',                      # de
    r'\babbonati\s+per\s+(?:continuare|leggere)\b',                       # it
    r'\bseite\s+nicht\s+gefunden\b',                                      # de
    r'\bpage\s+(?:introuvable|non\s+trouv[ée]e)\b',                       # fr
    r'\bp[áa]gina\s+no\s+encontrada\b',                                   # es
    r'\bpagina\s+non\s+trovata\b',                                        # it
    r'\bpagina\s+niet\s+gevonden\b',                                      # nl
    r'\bp[áa]gina\s+n[ãa]o\s+encontrada\b',                               # pt
]
_SCRAPE_JUNK_STRONG_RE = [re.compile(p, re.IGNORECASE) for p in _SCRAPE_JUNK_STRONG]
_SCRAPE_JUNK_WEAK_RE = [re.compile(p, re.IGNORECASE) for p in _SCRAPE_JUNK_WEAK]

# A body this short (in words) with even one weak signature is a boilerplate
# stub, not an article that happens to mention the topic.
_STUB_WORD_CEIL = 8


def is_scrape_junk(article: Dict, max_words: int = 120) -> tuple:
    """Detect scrape artifacts that have no article body and must NOT be sent to
    the oracle (scoring one from its headline is an anti-hallucination violation —
    see Solutions v4 calibration, DeepSeek defect 3).

    Conservative by design — two guards keep genuine content safe:
    - Emptiness is measured in CHARACTERS, not whitespace tokens, so genuine
      CJK/Thai (non-space-delimited) articles are not mistaken for empty stubs.
    - Only SHORT bodies (<= max_words) are pattern-checked; a long article is
      never dropped for leading with a boilerplate line. A single topical ("weak")
      signature does not flag a real short brief — that needs >=2 distinct weak
      hits, or a single hit in a body-less (<= _STUB_WORD_CEIL words) stub.

    Args:
        article: Article dict with 'content'/'text' and optional 'title'.
        max_words: Upper bound on body length for pattern-based junk. Real news
            briefs run longer than this; boilerplate stubs do not.

    Returns:
        (is_junk: bool, reason: str) — reason is "" when not junk.
    """
    content = sanitize_text_comprehensive(article.get("content") or article.get("text") or "")
    stripped = content.strip()

    # Effectively empty — no body to score. Character-based so CJK/Thai (which
    # split() collapses to ~1 "word") is not falsely dropped.
    if len(stripped) < 25:
        return True, "empty_or_stub_content"

    words = content.split()
    # Only short bodies can be pure boilerplate; long articles are real content.
    # (Word count is an English-boilerplate proxy; a long CJK body has few
    # "words" but matches none of the English signatures below, so it passes.)
    if len(words) > max_words:
        return False, ""

    haystack = f"{article.get('title', '')} {content}"
    for pattern in _SCRAPE_JUNK_STRONG_RE:
        if pattern.search(haystack):
            return True, f"scrape_junk_strong:{pattern.pattern}"

    weak_hits = [p.pattern for p in _SCRAPE_JUNK_WEAK_RE if p.search(haystack)]
    if len(weak_hits) >= 2:
        return True, f"scrape_junk_weak:{len(weak_hits)}:{weak_hits[0]}"
    if weak_hits and len(words) <= _STUB_WORD_CEIL:
        return True, f"scrape_junk_stub:{weak_hits[0]}"

    return False, ""


def clean_article(article: Union[Dict, List, str, Any]) -> Union[Dict, List, str, Any]:
    """
    Recursively sanitize all text fields in an article or data structure.

    Applies comprehensive cleaning to all strings in the data structure.
    Safe to call on already-clean articles (idempotent).

    Args:
        article: Article dict/list/str with potentially problematic text

    Returns:
        New structure with all text fields comprehensively cleaned

    Example:
        >>> article = {
        ...     'title': 'Test\\ud800Article',
        ...     'text': 'Content with <b>HTML</b> and \\u200b invisible chars',
        ...     'metadata': {'author': 'John&#39;s\\ud800'}
        ... }
        >>> cleaned = clean_article(article)
        >>> cleaned['title']
        'TestArticle'
        >>> cleaned['text']
        'Content with HTML and  invisible chars'
    """
    def _clean(obj):
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_clean(item) for item in obj]
        elif isinstance(obj, str):
            return sanitize_text_comprehensive(obj)
        return obj

    return _clean(article)


def clean_article_for_labeling(article: Dict) -> Dict:
    """
    Clean an article specifically for LLM labeling.

    Focuses on cleaning 'title' and 'text'/'content' fields while
    preserving metadata integrity.

    Args:
        article: Article dict with at least 'title' and 'text' or 'content'

    Returns:
        Article dict with cleaned text fields
    """
    cleaned = article.copy()

    # Clean title
    if 'title' in cleaned:
        cleaned['title'] = sanitize_text_comprehensive(cleaned['title'])

    # Clean main content
    if 'text' in cleaned:
        cleaned['text'] = sanitize_text_comprehensive(cleaned['text'])
    elif 'content' in cleaned:
        cleaned['content'] = sanitize_text_comprehensive(cleaned['content'])

    return cleaned


def batch_clean_articles(articles: List[Dict]) -> List[Dict]:
    """
    Clean a batch of articles for LLM labeling.

    Args:
        articles: List of article dictionaries

    Returns:
        List of cleaned article dictionaries
    """
    return [clean_article_for_labeling(article) for article in articles]
