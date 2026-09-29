# Screening Filter Template

**Purpose:** Template for creating screening filters that enrich training data distribution with signal-bearing content before oracle scoring.

**When to use:** Any filter where random corpus is >80% low-scoring (needle-in-haystack problem).

**Related:** See [ADR-003: Screening Filter for Training Data Enrichment](../adr/003-screening-filter-for-training-data.md) for rationale.

---

## Template Code

```python
"""
Screening Filter: {filter_name} v{version}

Purpose: Enrich training data distribution before oracle scoring.
NOT for inference - use prefilter.py for that.

Target: ~20-40% of screened articles should score >= 4.0 (vs ~6% in random)
"""

import re
from typing import Dict, Any, Tuple


# =============================================================================
# CONFIGURATION
# =============================================================================

# Minimum requirements (ANY ONE must match for article to pass)
SIGNAL_PATTERNS = [
    # Pattern 1: Topic indicators
    (
        r'\b(keyword1|keyword2|keyword3)\b',
        re.IGNORECASE,
        "Topic relevance"
    ),
    # Pattern 2: Quality indicators
    (
        r'\b(research|study|analysis|data|evidence)\b',
        re.IGNORECASE,
        "Quality signals"
    ),
    # Pattern 3: Domain-specific signals
    (
        r'\b(domain_specific_term1|domain_specific_term2)\b',
        re.IGNORECASE,
        "Domain signals"
    ),
]

# Patterns that suggest high-signal content (boost confidence)
BOOST_PATTERNS = [
    (r'\b(breakthrough|milestone|pioneering)\b', re.IGNORECASE, "Impact language"),
    (r'\d+%|\d+\s*(percent|million|billion)', re.IGNORECASE, "Quantitative evidence"),
]

# Patterns that suggest low-signal content (reduce confidence)
PENALTY_PATTERNS = [
    (r'\b(rumor|speculation|might|could|may)\b', re.IGNORECASE, "Speculative language"),
    (r'\b(advertisement|sponsored|affiliate)\b', re.IGNORECASE, "Commercial content"),
]

# Source domain preferences (optional - set to None to ignore)
PREFERRED_SOURCES = [
    # "academic.journal.com",
    # "research.org",
    # "quality-news.com",
]

PENALIZED_SOURCES = [
    # "clickbait-site.com",
    # "tabloid.com",
]

# Thresholds
MIN_WORD_COUNT = 200  # Skip very short articles
MAX_WORD_COUNT = 10000  # Skip overly long content
MIN_TITLE_LENGTH = 10  # Skip articles with minimal titles
SIGNAL_THRESHOLD = 1  # Minimum signal patterns required


# =============================================================================
# SCREENING LOGIC
# =============================================================================

def screen_article(article: Dict[str, Any]) -> Tuple[bool, str, float]:
    """
    Screen an article for training data enrichment.

    Args:
        article: Dict with 'title', 'content', 'source' (optional)

    Returns:
        Tuple of (passes: bool, reason: str, confidence: float)
        - passes: Whether article passes screening
        - reason: Human-readable explanation
        - confidence: 0.0-1.0 confidence that article has signal
    """
    title = article.get('title', '') or ''
    content = article.get('content', '') or ''
    source = article.get('source', '') or ''

    full_text = f"{title} {content}"
    word_count = len(full_text.split())

    # Basic filters
    if word_count < MIN_WORD_COUNT:
        return False, f"Too short ({word_count} words < {MIN_WORD_COUNT})", 0.0

    if word_count > MAX_WORD_COUNT:
        return False, f"Too long ({word_count} words > {MAX_WORD_COUNT})", 0.0

    if len(title) < MIN_TITLE_LENGTH:
        return False, f"Title too short ({len(title)} chars)", 0.0

    # Count signal patterns
    signal_count = 0
    matched_signals = []

    for pattern, flags, description in SIGNAL_PATTERNS:
        if re.search(pattern, full_text, flags):
            signal_count += 1
            matched_signals.append(description)

    # Check minimum signal threshold
    if signal_count < SIGNAL_THRESHOLD:
        return False, f"Insufficient signal ({signal_count}/{SIGNAL_THRESHOLD})", 0.1

    # Calculate confidence with boosts and penalties
    confidence = 0.5 + (signal_count * 0.1)  # Base from signals

    # Apply boosts
    for pattern, flags, description in BOOST_PATTERNS:
        if re.search(pattern, full_text, flags):
            confidence += 0.1
            matched_signals.append(f"+{description}")

    # Apply penalties
    for pattern, flags, description in PENALTY_PATTERNS:
        if re.search(pattern, full_text, flags):
            confidence -= 0.15
            matched_signals.append(f"-{description}")

    # Source preferences
    if PREFERRED_SOURCES and any(s in source.lower() for s in PREFERRED_SOURCES):
        confidence += 0.1
        matched_signals.append("+Preferred source")

    if PENALIZED_SOURCES and any(s in source.lower() for s in PENALIZED_SOURCES):
        confidence -= 0.2
        matched_signals.append("-Penalized source")

    # Clamp confidence
    confidence = max(0.1, min(1.0, confidence))

    # Marginal cases - be inclusive for training diversity
    if confidence >= 0.3:
        return True, f"Pass: {', '.join(matched_signals)}", confidence
    else:
        return False, f"Low confidence ({confidence:.2f}): {', '.join(matched_signals)}", confidence


def screen_batch(articles: list, target_count: int = None) -> list:
    """
    Screen a batch of articles, optionally limiting to target count.

    Args:
        articles: List of article dicts
        target_count: Optional max number to return (highest confidence first)

    Returns:
        List of (article, reason, confidence) tuples that pass screening
    """
    results = []

    for article in articles:
        passes, reason, confidence = screen_article(article)
        if passes:
            results.append((article, reason, confidence))

    # Sort by confidence (highest first)
    results.sort(key=lambda x: x[2], reverse=True)

    if target_count and len(results) > target_count:
        results = results[:target_count]

    return results


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Screen articles for training data")
    parser.add_argument("--input", required=True, help="Input JSONL file")
    parser.add_argument("--output", required=True, help="Output JSONL file")
    parser.add_argument("--target", type=int, help="Target number of articles")
    parser.add_argument("--stats", help="Output stats file")
    args = parser.parse_args()

    # Load articles
    articles = []
    with open(args.input, 'r', encoding='utf-8') as f:
        for line in f:
            articles.append(json.loads(line))

    print(f"Loaded {len(articles)} articles")

    # Screen
    passed = screen_batch(articles, args.target)

    # Write output
    with open(args.output, 'w', encoding='utf-8') as f:
        for article, reason, confidence in passed:
            article['_screening_reason'] = reason
            article['_screening_confidence'] = confidence
            f.write(json.dumps(article) + '\n')

    print(f"Screened: {len(passed)}/{len(articles)} passed ({100*len(passed)/len(articles):.1f}%)")

    # Stats
    if args.stats:
        stats = {
            "total_input": len(articles),
            "total_passed": len(passed),
            "pass_rate": len(passed) / len(articles) if articles else 0,
            "avg_confidence": sum(c for _, _, c in passed) / len(passed) if passed else 0,
        }
        with open(args.stats, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"Stats written to {args.stats}")
```

---

## Configuration Guide

### Signal Patterns

**Goal:** Identify articles likely to have content relevant to your filter's dimensions.

**Tips:**
- Start with the most discriminative terms from your filter's scope definition
- Include quality indicators (research, study, data, evidence)
- Include domain-specific jargon that suggests depth
- Test patterns on a sample to verify they're not too broad/narrow

**Example for cultural-discovery filter:**
```python
SIGNAL_PATTERNS = [
    (r'\b(archaeological|excavation|ancient|heritage|artifact)\b', re.IGNORECASE, "Archaeology"),
    (r'\b(tradition|ritual|ceremony|cultural)\b', re.IGNORECASE, "Cultural practices"),
    (r'\b(discovery|uncovered|revealed|found)\b', re.IGNORECASE, "Discovery language"),
    (r'\b(museum|preservation|unesco|heritage)\b', re.IGNORECASE, "Heritage institutions"),
]
```

### Boost and Penalty Patterns

**Boost patterns** indicate high-quality, substantive content:
- Quantitative evidence (numbers, percentages, statistics)
- Research methodology language
- Impact language (breakthrough, pioneering, first)

**Penalty patterns** indicate low-quality or off-topic content:
- Speculative language (might, could, rumored)
- Commercial indicators (sponsored, affiliate)
- Clickbait patterns

### Thresholds

| Parameter | Default | Guidance |
|-----------|---------|----------|
| `SIGNAL_THRESHOLD` | 1 | Start at 1, increase if pass rate > 40% |
| `MIN_WORD_COUNT` | 200 | Filters out stubs and snippets |
| `confidence >= 0.3` | 0.3 | Lower to be more inclusive, raise for higher quality |

---

## Validation Checklist

Before using a screening filter for training data collection:

### 1. Pass Rate Test

```bash
python screening_filter.py --input sample_1000.jsonl --output screened.jsonl --stats stats.json
```

**Target pass rate:** 15-30%
- < 10%: Too aggressive, may miss relevant content
- > 40%: Too permissive, not enriching enough

### 2. Signal Validation

Score a sample of screened articles with the oracle:

```bash
python -m ground_truth.batch_scorer \
    --filter filters/{filter_name}/v{version} \
    --source screened_sample_100.jsonl \
    --output-dir sandbox/screening_validation
```

**Target distribution:**
- 30-40% scoring >= 4.0 (vs ~6% in random)
- 10-20% scoring >= 6.0 (vs ~2% in random)

### 3. False Negative Check

Sample 100 articles that FAILED screening, score with oracle:

```bash
python -m ground_truth.batch_scorer \
    --filter filters/{filter_name}/v{version} \
    --source rejected_sample_100.jsonl \
    --output-dir sandbox/screening_fn_check
```

**Acceptable:** < 5% of rejected articles score >= 6.0
**If higher:** Screening is too aggressive, loosen criteria

### 4. Diversity Check

Verify screened articles aren't all from one pattern/source:

```bash
python scripts/analyze_screening_diversity.py \
    --input screened.jsonl \
    --field source
```

**Look for:** No single source/pattern > 50% of passed articles

---

## Difference from Prefilter

| Aspect | Screening Filter | Prefilter |
|--------|------------------|-----------|
| **Purpose** | Training data enrichment | Inference noise reduction |
| **When used** | Before oracle scoring | Before model inference |
| **Aggressiveness** | Aggressive (reject 60-85%) | Conservative (pass 50-80%) |
| **False negatives** | Acceptable (10-20%) | Critical failure (< 10%) |
| **False positives** | Critical failure | Acceptable (oracle catches) |
| **Goal** | Enrich signal in training distribution | Block obvious noise |

**Key insight:** A good prefilter is NOT a good screening filter, and vice versa. They optimize for opposite goals.

---

## Usage in Training Workflow

```bash
# 1. Screen raw articles (25K → ~5K passed)
python filters/{filter}/v{version}/screening_filter.py \
    --input datasets/raw/master_dataset.jsonl \
    --output sandbox/screened_articles.jsonl \
    --target 10000

# 2. Score screened articles with oracle
python -m ground_truth.batch_scorer \
    --filter filters/{filter}/v{version} \
    --source sandbox/screened_articles.jsonl \
    --output-dir datasets/scored/{filter}_v{version}

# 3. Proceed with training as normal
python training/prepare_data.py ...
python training/train.py ...
```

---

## Examples

See implemented screening filters:
- `filters/cultural_discovery/v2/screening_filter.py` (when available)

---

**Last updated:** 2026-01-29
