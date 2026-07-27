# Commerce Prefilter SLM Design

**Status**: Design
**Created**: 2026-01-16
**Goal**: Replace brittle regex-based product deal detection with a small language model

## Problem

Current prefilters use regex patterns to detect promotional/commerce content:

```python
'product_deals': [
    r'\b(Black Friday|Prime Day|Cyber Monday|holiday deal)\b',
    r'\bGreen Deals\b',
    r'\$\d[\d,]*\s*(savings|discount|off)\b',
    # ... more patterns
]
```

**Issues:**
- Constant tweaking as new patterns slip through (whack-a-mole)
- Doesn't generalize - misses novel promotional language
- Maintenance burden grows over time
- Case study: Jackery "Green Deals" article passed v2.1 prefilter despite being obvious shopping content

## Solution

A small language model (SLM) trained as a binary classifier:
- **Input**: Article title + content
- **Output**: `commerce` (block) or `not_commerce` (pass)

## Architecture

```
Article Input
      │
      ▼
┌─────────────────────────────────────────┐
│  Commerce Prefilter SLM                 │
│  (DistilBERT or similar, ~60-100MB)     │
│                                         │
│  Binary classification:                 │
│  - commerce → BLOCK                     │
│  - not_commerce → PASS                  │
└─────────────────────────────────────────┘
      │
      ▼ (if passed)
┌─────────────────────────────────────────┐
│  Existing Filter Pipeline               │
│  (sustainability_technology, etc.)      │
└─────────────────────────────────────────┘
```

## Placement

Location: `filters/common/commerce_prefilter/`

```
filters/common/commerce_prefilter/
├── v1/
│   ├── model/                 # Trained model files
│   ├── inference.py           # SLM inference
│   ├── config.yaml            # Threshold, model settings
│   └── README.md
├── training/
│   ├── collect_examples.py    # Gather training data
│   ├── prepare_dataset.py     # Format for training
│   └── train.py               # Training script
└── README.md
```

## Training Data Sources

### Positive (Commerce) Examples
- Electrek "Green Deals" articles
- Product review sites (The Verge reviews, CNET deals)
- Press releases (PR Newswire, Business Wire)
- Affiliate content (Amazon Associates, commission-based)
- Shopping aggregators

### Negative (Journalism) Examples
- Reuters, AP News
- Scientific journals (Nature, Science)
- Government reports (EPA, DOE, IEA)
- NGO reports (IRENA, RMI, BloombergNEF)
- Quality sustainability journalism

### Signals the Model Should Learn

**Commerce indicators:**
- Price mentions in promotional context
- Urgency language ("limited time", "ends tonight")
- Affiliate/deal language ("exclusive", "save $X")
- Product comparison shopping tone
- Call-to-action patterns ("buy now", "check price")

**Journalism indicators:**
- Attribution to sources
- Balanced perspective
- Technical depth
- No commercial call-to-action
- Institutional sources cited

## Model Selection

Options (in order of preference):

1. **DistilBERT** (~66M params, ~250MB)
   - Good balance of speed and accuracy
   - Well-supported, easy to fine-tune
   - Fast inference on CPU

2. **TinyBERT** (~14M params, ~60MB)
   - Smaller, faster
   - May sacrifice some accuracy

3. **MiniLM** (~22M params, ~90MB)
   - Good for sentence-level tasks
   - Efficient inference

## Integration with Existing Filters

The commerce prefilter runs BEFORE existing regex prefilters:

```python
# In filters/common/base_prefilter.py

class BasePreFilter:
    def __init__(self):
        self.commerce_detector = CommercePrefilterSLM()  # NEW

    def apply_filter(self, article):
        # Step 1: Commerce SLM (generalizes well)
        if self.commerce_detector.is_commerce(article):
            return (False, "commerce_content")

        # Step 2: Existing regex patterns (specific edge cases)
        # These can be LOOSENED over time as SLM proves reliable
        ...
```

## Migration Plan

### Phase 1: Shadow Mode
- Deploy commerce SLM alongside existing regex
- Log when SLM would block but regex didn't (and vice versa)
- Measure precision/recall

### Phase 2: SLM Primary
- Commerce SLM becomes primary filter
- Regex patterns kept as backup for edge cases
- Loosen regex patterns (remove redundant ones)

### Phase 3: SLM Only
- Remove most regex patterns
- Keep only specific edge cases regex can't learn
- Minimal maintenance burden

## Success Metrics

- **Recall**: Catch >95% of commerce content (vs ~80% with regex)
- **Precision**: <5% false positives (legitimate journalism blocked)
- **Maintenance**: No pattern updates needed for 6+ months
- **Performance**: <50ms inference per article on CPU

## Training Pipeline

```bash
# 1. Collect examples
python filters/common/commerce_prefilter/training/collect_examples.py \
    --output data/commerce_training/raw/

# 2. Prepare dataset
python filters/common/commerce_prefilter/training/prepare_dataset.py \
    --input data/commerce_training/raw/ \
    --output data/commerce_training/prepared/

# 3. Train model
python filters/common/commerce_prefilter/training/train.py \
    --data data/commerce_training/prepared/ \
    --output filters/common/commerce_prefilter/v1/model/ \
    --base-model distilbert-base-uncased \
    --epochs 3
```

## Open Questions

1. **Threshold tuning**: What confidence threshold for "commerce"? Start with 0.7?
2. **Edge cases**: How to handle legitimate price reporting (e.g., "solar costs hit record low")?
3. **Multi-lingual**: Train on English only or include Dutch/German?
4. **Retraining cadence**: How often to retrain with new examples?

## Timeline Estimate

- Week 1: Collect and label training data (~1000 examples each class)
- Week 2: Train and validate model
- Week 3: Shadow mode deployment
- Week 4: Evaluation and tuning
- Week 5: Production deployment

## References

- [Jackery case study](../filters/sustainability_technology/v3/prefilter.py) - v3 prefilter patterns
- [Prefilter harmonization](./PREFILTER_HARMONIZATION_TASK.md)
- [Filter architecture](./ARCHITECTURE.md)
