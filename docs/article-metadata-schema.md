# Article Metadata Schema

**Purpose:** Document all metadata fields available in article JSON for use in post-filter logic.

**Last updated:** 2025-11-13

---

## Core Fields

### Identifiers
```json
{
  "id": "dutch_news_ad_algemeen_19386d93ae12",
  "url": "https://www.ad.nl/voetbal/...",
  "title": "Article title...",
  "content": "Article text..."
}
```

### Source Information
```json
{
  "source": "dutch_news_ad_algemeen",
  "source_type": "rss",  // or "api", "scraper", etc.
  "published_date": "2025-10-10T10:02:00",
  "collected_date": "2025-10-10T12:51:06.971858",
  "language": "nl"
}
```

### Tags
```json
{
  "tags": [
    "regionaal",
    "nederland",
    "dutch_news",
    "commercial",  // ← Useful for content type detection
    "finance",
    "business"
  ]
}
```

**Use in post-filter:**
- Detect corporate finance: `"finance" in tags or "business" in tags`
- Detect commercial content: `"commercial" in tags`
- Source categorization: `"dutch_news" in tags`

---

## Metadata Object

### Basic Metadata
```json
{
  "metadata": {
    "word_count": 56,
    "char_count": 404,
    "reading_time_minutes": 0.28,
    "author": "Daan Hakkenberg",
    "quality_score": 1.0,  // ← Pre-computed quality metric
    "language_detected": "nl"
  }
}
```

**Use in post-filter:**
- Filter short/low-quality articles: `word_count < 100`
- Quality threshold: `quality_score < 0.5`

### Entity Extraction
```json
{
  "metadata": {
    "entities": {
      "organizations": [
        "Arthrex, Inc.",
        "FDA"
      ],
      "persons": [
        "Daan Hakkenberg"
      ],
      "locations": [
        "Noorwegen",
        "Italië"
      ],
      "monetary": [
        "$50M",
        "€2.5 billion"
      ]  // ← Indicates financial content
    }
  }
}
```

**Use in post-filter:**
- **Corporate finance detection**: `len(entities.monetary) > 0` + corporate org names
- **Business content**: Multiple organization names (M&A, partnerships)
- **Geographic scope**: Number of locations → collective_benefit assessment

### Key Concepts
```json
{
  "metadata": {
    "key_concepts": {
      "key_phrases": [
        "kwalificatieduels",
        "peace process",
        "climate technology"
      ],
      "filter_categories": {
        "ai_ml": ["Dat"],
        "climate_tech": ["solar", "wind"],
        "business": ["IPO", "merger"]
      },
      "extraction_method": "spacy",
      "confidence": "high",
      "concept_scores": {
        "kwalificatieduels": 2.0,
        "peace process": 1.5
      }
    }
  }
}
```

**Use in post-filter:**
- **Content type detection**: Check `filter_categories` keys
- **Keyword matching**: Scan `key_phrases` for triggers
- **Confidence gating**: Filter low-confidence extractions

---

## Sentiment & Emotion

### Sentiment Scores
```json
{
  "sentiment_score": 0.5215,  // 0-10 scale
  "sentiment_category": "negative",  // positive/negative/neutral
  "sentiment_confidence": "high",  // high/medium/low
  "sentiment_method": "vader",
  "sentiment_raw_score": -0.8957,  // -1 to +1
  "is_positive": false,
  "is_negative": true,
  "is_neutral": false
}
```

**Use in post-filter:**
- Filter overly negative content (doomism)
- Validate uplifting scores match sentiment
- Cap scores for negative business news

### Emotion Analysis
```json
{
  "raw_emotions": {
    "neutral": 0.188,
    "joy": 0.0068,
    "surprise": 0.5679,
    "sadness": 0.0075,
    "fear": 0.0385,
    "anger": 0.041,
    "disgust": 0.1505
  },
  "emotion_method": "local"
}
```

**Use in post-filter:**
- **High fear/anger**: May indicate military/security content
- **High joy**: Validates uplifting assessment
- **Disgust/sadness**: Potential doomer content to filter

---

## Time & Freshness

### Temporal Metadata
```json
{
  "published_date": "2025-10-10T10:02:00",
  "collected_date": "2025-10-10T12:51:06.971858",
  "age_hours": 2.9126,
  "is_recent": true
}
```

**Use in post-filter:**
- Prioritize recent articles: `is_recent == true`
- Freshness score adjustment: `age_hours < 24`

---

## Quality & Hashing

### Quality Indicators
```json
{
  "quality_score": 1.0,  // 0-1 scale
  "robust_parsing_used": true
}
```

### Deduplication Hashes
```json
{
  "hashes": {
    "content_md5": "a69f5df710e6394a442803c592aaedf3",
    "title_md5": "0cd2b4f4e1b400a3ea931116ef7bf531",
    "url_normalized": "809bdf7feae18ecc2efda8f88e62da4e",
    "combined_hash": "a0f7296f52da920115c18e37f4e8c8cc"
  }
}
```

> **`minhash_signature` was documented here and never existed on the wire
> (corrected 2026-08-07).** No producer and no reader: `compute_minhash` has had
> no production caller in ~8 months, so the field was never emitted. It could not
> have been even if wired up — `compute_minhash` returns `numpy.uint64` elements
> and `json.dumps` raises `TypeError: Object of type uint64 is not JSON
> serializable`, while the code comment beside it claims the opposite.
> **The recommendation on ducroq/FluxusSource#134 is to delete the implementation**
> (measured: 3 cross-source pairs per cycle at Jaccard ≥0.6, one of them a false
> positive, against the ~2 exact hashing already finds; real cross-language
> same-story pairs land at 0.094–0.297, below any usable threshold).
> Two NexusMind docs still assert the same non-existent capability —
> `docs/ARCHITECTURE.md:56` and `docs/downstream-apps/business/pitch-document.md:39`.
> A schema that documents a field nothing writes is the same
> present-configured-unreachable shape as NM#284 and LD#101.

---

## Filter Analysis (Oracle Output)

### Sustainability Tech Deployment
```json
{
  "sustainability_tech_deployment_analysis": {
    "dimensions": {
      "deployment_maturity": 7,
      "technology_performance": 6,
      // ... 8 dimensions
    },
    "overall_score": 3.9,
    "tier": "pilot_stage",
    "primary_technology": "other",
    "deployment_stage": "commercial_proven",
    "confidence": "MEDIUM",
    "analyzed_at": "2025-11-11T11:05:28.001592Z",
    "analyzed_by": "gemini-flash-api-batch",
    "filter_name": "sustainability_tech_deployment"
  }
}
```

### Uplifting
```json
{
  "uplifting_analysis": {
    "content_type": "peace_process",  // ← Useful for content caps
    "dimensions": {
      "agency": 6,
      "progress": 5,
      // ... 8 dimensions
    },
    "overall_uplift_score": 5.7,
    "tier": "connection",
    "key_markers": ["solidarity", "protest"],
    "analyzed_at": "2025-11-02T07:31:00.386931Z",
    "analyzed_by": "gemini-flash-api-batch",
    "filter_name": "uplifting"
  }
}
```

---

## Metadata Fields Useful for Post-Filter

### Content Type Detection (Uplifting Filter)

**Corporate Finance:**
```python
def is_corporate_finance(article):
    # Check tags
    if any(tag in ["finance", "business", "corporate", "commercial"]
           for tag in article.get("tags", [])):
        # Check for monetary values
        if article.get("metadata", {}).get("entities", {}).get("monetary"):
            return True

    # Check key concepts
    filter_cats = article.get("metadata", {}).get("key_concepts", {}).get("filter_categories", {})
    if "business" in filter_cats or "finance" in filter_cats:
        return True

    return False
```

**Military/Security:**
```python
def is_military_security(article):
    # High fear/anger emotions
    emotions = article.get("raw_emotions", {})
    if emotions.get("fear", 0) > 0.3 or emotions.get("anger", 0) > 0.3:
        # Check tags/keywords
        if any(tag in ["military", "defense", "security"]
               for tag in article.get("tags", [])):
            return True

    # Check key phrases
    key_phrases = article.get("metadata", {}).get("key_concepts", {}).get("key_phrases", [])
    military_terms = ["military", "defense", "weapons", "armed forces"]
    if any(term in " ".join(key_phrases).lower() for term in military_terms):
        return True

    return False
```

**Business News (with collective_benefit check):**
```python
def is_business_news(article, collective_benefit_score):
    # Only cap if collective_benefit < 6
    if collective_benefit_score >= 6:
        return False

    # Check for business-related organizations
    orgs = article.get("metadata", {}).get("entities", {}).get("organizations", [])
    if len(orgs) >= 2:  # Multiple orgs suggests business partnerships/deals
        return True

    # Check tags
    if "business" in article.get("tags", []):
        return True

    return False
```

### Sentiment/Emotion Usage

**IMPORTANT:** Sentiment/emotion analysis measures **tone of writing**, not **semantic content**.

**Examples where tone ≠ semantics:**
- "The devastating hurricane destroyed homes..." → Negative tone, but story about community rebuilding (positive semantics)
- "Outrageous! Government FINALLY banned toxic chemical!" → Angry tone, but positive progress semantics
- "Sadly, the old coal plant shut down" → Sad tone, but climate progress semantics

**Valid uses:**

**1. Clickbait/Sensationalism Detection:**
```python
def is_sensationalist(article):
    emotions = article.get("raw_emotions", {})

    # Extreme surprise + fear = clickbait/fearmongering
    if emotions.get("surprise", 0) > 0.4 and emotions.get("fear", 0) > 0.3:
        return True

    return False
```

**2. Corporate PR Detection (combine with tags):**
```python
def is_corporate_pr(article):
    emotions = article.get("raw_emotions", {})

    # Corporate speak: very neutral (0.85+) + emotionless
    if emotions.get("neutral", 0) > 0.85:
        has_business_tags = any(tag in ["business", "finance"]
                               for tag in article.get("tags", []))
        if has_business_tags:
            return True  # Likely corporate PR

    return False
```

**3. Doom Framing Penalty (uplifting filter):**
```python
def apply_doom_framing_penalty(uplifting_score, article):
    """
    Reduce score if doom-framed presentation.
    Even if semantically positive, doom framing reduces uplift.
    """
    emotions = article.get("raw_emotions", {})

    negative_emotions = (
        emotions.get("sadness", 0) +
        emotions.get("fear", 0) +
        emotions.get("disgust", 0)
    )

    # Heavy doom framing (>60% negative emotions)
    if negative_emotions > 0.6 and emotions.get("neutral", 0) < 0.3:
        penalty = min(2.0, negative_emotions * 3)
        return uplifting_score - penalty

    return uplifting_score
```

**4. Quality Signal (balanced journalism):**
```python
def has_balanced_tone(article):
    emotions = article.get("raw_emotions", {})
    neutral = emotions.get("neutral", 0)

    # Good journalism: 40-70% neutral
    # Too neutral (>85%) = boring/corporate
    # Too emotional (<20%) = sensationalist
    return 0.4 <= neutral <= 0.7
```

**❌ DON'T use sentiment/emotion to:**
- Validate uplifting scores (tone ≠ semantics)
- Directly adjust dimensional scores
- Content type detection alone (need tags/entities too)

### Quality Gating

**Filter low-quality articles:**
```python
def passes_quality_threshold(article):
    quality_score = article.get("quality_score", 0)
    word_count = article.get("metadata", {}).get("word_count", 0)

    # Minimum quality
    if quality_score < 0.5:
        return False

    # Minimum length (avoid snippets/headlines)
    if word_count < 50:
        return False

    return True
```

---

## Usage Decision: Content Caps in Oracle, Not Post-Filter

**Decision (2025-11-13):** Content type caps are enforced in **oracle prompts**, NOT in post-filter using metadata.

**Rationale:**
- Oracle understands context/exceptions (worker cooperative vs corporate VC)
- Avoid false positives from noisy tags
- Keep post-filter simple (pure arithmetic)
- See: `docs/decisions/2025-11-13-content-caps-in-oracle-not-postfilter.md`

**What metadata IS used for:**
- ✅ **Optional pre-filter:** Quality gate (clickbait, duplicates, too short) before oracle calls
- ✅ **Documentation:** Understanding article structure
- ✅ **Analysis:** Post-hoc evaluation of filter performance

**What metadata is NOT used for:**
- ❌ Content type detection in post-filter
- ❌ Overriding oracle dimensional scores
- ❌ Required input to post-filter

---

## Optional: Pre-Filter Quality Gate (Not Implemented Yet)

**Purpose:** Filter low-quality articles before oracle calls (save API costs)

### Example Implementation (Optional)

```python
def prefilter_quality_gate(article: Dict[str, Any]) -> tuple[bool, str]:
    """
    Optional: Filter low-quality articles before oracle calls.

    Returns:
        (should_process, reason)
    """
    # Check 1: Minimum length
    word_count = article.get("metadata", {}).get("word_count", 0)
    if word_count < 50:
        return (False, "Too short (< 50 words)")

    # Check 2: Quality score
    quality_score = article.get("quality_score", 1.0)
    if quality_score < 0.3:
        return (False, "Low quality score")

    # Check 3: Clickbait/sensationalism
    emotions = article.get("raw_emotions", {})
    if emotions.get("surprise", 0) > 0.5 and emotions.get("fear", 0) > 0.4:
        return (False, "Likely clickbait (extreme surprise + fear)")

    # Check 4: Duplicate (if hash exists in database)
    # combined_hash = article.get("hashes", {}).get("combined_hash")
    # if combined_hash and is_duplicate(combined_hash):
    #     return (False, "Duplicate article")

    return (True, "Passed quality gate")


# Usage before oracle calls:
for article in articles:
    should_process, reason = prefilter_quality_gate(article)
    if should_process:
        # Call oracle for dimensional scoring
        scores = oracle.score_article(article)
    else:
        logger.info(f"Skipped article {article['id']}: {reason}")
```

**Note:** This is optional. Oracle costs are low (~$0.001/article) and volume is manageable (1000 articles/day).

---

## Example: Full Article with Metadata

**Use case:** Corporate finance article for uplifting filter

```json
{
  "id": "techcrunch_123abc",
  "title": "Startup X raises $50M Series B",
  "tags": ["business", "finance", "startup", "venture_capital"],
  "metadata": {
    "entities": {
      "organizations": ["Startup X", "Sequoia Capital"],
      "monetary": ["$50M", "$250M valuation"]
    },
    "key_concepts": {
      "filter_categories": {
        "business": ["fundraising", "Series B"]
      }
    }
  },
  "sentiment_score": 7.2,
  "raw_emotions": {
    "joy": 0.15,
    "neutral": 0.7
  }
}
```

**Post-filter logic:**
1. Detect corporate finance: ✅ (tags + monetary entities)
2. Check exceptions: ❌ (not worker cooperative, etc.)
3. Apply cap: overall_score capped at 2.0
4. Even if dimensional scores high, tier = "not_uplifting"

---

## Current Use of Metadata

**What we DO use metadata for:**
- ✅ **Documentation:** Understanding article structure and available fields
- ✅ **Analysis:** Post-hoc evaluation of filter performance
- ✅ **Optional pre-filter:** Quality gating (if implemented later)

**What we DON'T use metadata for:**
- ❌ **Content type caps in post-filter** - Enforced in oracle prompt instead (see ADR)
- ❌ **Sentiment validation** - Tone ≠ semantics
- ❌ **Required input to post-filter** - Post-filter only needs dimensional scores

**Why this approach:**
- Oracle understands semantic context better than tag matching
- Avoids false positives from noisy tags (worker cooperative tagged as "business")
- Keeps post-filter simple (pure arithmetic)
- See: `docs/decisions/2025-11-13-content-caps-in-oracle-not-postfilter.md`

---

## Summary

**Metadata schema documented for:**
1. ✅ Reference - understanding what's available in articles
2. ✅ Future use - optional pre-filter quality gate
3. ✅ Analysis - evaluating filter performance

**Not currently used for:**
- Content type detection in post-filter (oracle handles it)
- Overriding oracle dimensional scores
- Required post-filter input
