> **DEPRECATED (Feb 2026):** This guide references early-stage workflows (Qwen fine-tuning, manual conversion scripts). The batch scorer is still accurate, but for the full current workflow see `docs/guides/filter-creation-workflow.md`.

# Ground Truth Generation Guide

**Version:** 3.0
**Last Updated:** October 30, 2025
**Purpose:** Create labeled training data for fine-tuning Qwen agents
**Next Step:** After labeling → See `qwen-finetuning-guide.md`

---

## ⚠️ Important: Run Calibration First!

**Before following this guide**, you should complete the two-phase calibration workflow:

1. **Pre-filter Calibration** (500 articles) - Test blocking patterns
2. **Oracle Calibration** (100 articles) - Compare model quality

See: [ground_truth/README.md](../../ground_truth/README.md) for the complete calibration workflow.

**Why calibrate?** 30 minutes of calibration can save you $10-40+ on large batches and ensure high-quality ground truth.

---

## Overview

This guide shows you how to create labeled training data (ground truth) for fine-tuning semantic classification agents **after you've completed calibration**.

**What you'll do:**
1. Sample 2,500 articles from your master datasets
2. Label them with your chosen LLM (Gemini Flash recommended after calibration)
3. Pre-filter blocks noise automatically (saves 5-30% API calls)
4. Convert to training format for Qwen fine-tuning
5. Validate data quality

**Time required:** 4-6 hours (mostly automated)
**Cost:** ~$0.85-0.90 (Gemini Flash API with pre-filter savings)

---

## Prerequisites

### Required Files

```bash
# Master datasets (should exist)
datasets/raw/master_dataset_20250929_20251008.jsonl  (37K articles)
datasets/raw/master_dataset_20251009_20251025.jsonl  (52K articles)
datasets/raw/master_dataset_20251026_20251029.jsonl  (11K articles)

# Filter packages (should exist - see filters/README.md)
filters/uplifting/v1/             # Complete filter package
  ├── prefilter.py                # Pre-filter (blocks noise)
  ├── prompt-compressed.md        # Prompt for labeling
  └── config.yaml                 # Configuration

filters/sustainability/v1/        # For sustainability filter
filters/investment-risk/v1/       # For investment-risk filter
# ... (create more as needed)
```

### API Keys

You need a Gemini API key configured:

```bash
# Check if configured
python -c "from ground_truth.secrets_manager import get_secrets_manager; sm = get_secrets_manager(); print('Gemini key:', 'FOUND' if sm.get_llm_key('gemini') else 'MISSING')"
```

If missing, add to `ground_truth/secrets.ini`:
```ini
[llm]
gemini_api_key = YOUR_KEY_HERE
```

---

## Step 1: Create Training Sample

### Why 2,500 Articles?

Based on Qwen fine-tuning benchmarks:
- **500 articles**: Quick prototype (2-3 hours training)
- **1,000 articles**: Good quality (3-4 hours training)
- **2,500 articles**: ✅ **RECOMMENDED** - Best quality/time balance (7-10 hours training)
- **5,000+ articles**: Diminishing returns (15+ hours training)

### Sample Your Data

**Simple random sampling** (recommended - matches your production RSS mix):

```python
# create_sample.py
import json
import random
from pathlib import Path

def create_training_sample(sample_size=2500, train_ratio=0.9):
    """
    Create random sample from all master datasets.

    Why random? Your data already reflects production reality:
    - 32% academic papers (ArXiv)
    - 27% news sources
    - 41% other sources

    Training on this mix = model handles production well.
    """

    print(f"Creating sample of {sample_size:,} articles...")

    # Load all articles
    all_articles = []
    raw_dir = Path("datasets/raw")

    for filepath in raw_dir.glob("master_dataset_*.jsonl"):
        print(f"  Loading: {filepath.name}")
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    article = json.loads(line.strip())
                    # Basic quality filter
                    if article.get('metadata', {}).get('quality_score', 0) >= 0.7:
                        all_articles.append(article)
                except:
                    continue

    print(f"  Total articles available: {len(all_articles):,}")

    # Random sample
    random.seed(42)  # Reproducible
    sample = random.sample(all_articles, min(sample_size, len(all_articles)))

    # Shuffle and split
    random.shuffle(sample)
    split_idx = int(len(sample) * train_ratio)

    train = sample[:split_idx]
    val = sample[split_idx:]

    # Save
    output_dir = Path("datasets/training")
    output_dir.mkdir(parents=True, exist_ok=True)

    train_file = output_dir / "sample_train.jsonl"
    val_file = output_dir / "sample_val.jsonl"

    with open(train_file, 'w', encoding='utf-8') as f:
        for article in train:
            f.write(json.dumps(article, ensure_ascii=False, separators=(',', ':')) + '\n')

    with open(val_file, 'w', encoding='utf-8') as f:
        for article in val:
            f.write(json.dumps(article, ensure_ascii=False, separators=(',', ':')) + '\n')

    print(f"\n✅ Created sample:")
    print(f"   Training: {len(train):,} articles → {train_file}")
    print(f"   Validation: {len(val):,} articles → {val_file}")
    print(f"\n   Total: {len(sample):,} articles")
    print(f"   Split: {train_ratio*100:.0f}% train / {(1-train_ratio)*100:.0f}% val")

    # Quick stats
    sources = [a.get('source', 'unknown') for a in sample]
    from collections import Counter

    print(f"\n   Top 5 sources:")
    for source, count in Counter(sources).most_common(5):
        print(f"     - {source}: {count} ({count/len(sample)*100:.1f}%)")

if __name__ == '__main__':
    create_training_sample(sample_size=2500, train_ratio=0.9)
```

**Run it:**

```bash
python create_sample.py
```

**Output:**
```
datasets/training/sample_train.jsonl   (2,250 articles)
datasets/training/sample_val.jsonl     (250 articles)
```

---

## Step 2: Label with Gemini Flash

### Understanding batch_scorer.py

The `batch_scorer.py` script:
- Loads articles from your sample
- Sends them to Gemini Flash API
- Uses your prompt (e.g., `prompts/uplifting.md`)
- Saves labeled results
- Handles retries and errors
- Tracks progress (resume capability)

### Label Training Set

**For Uplifting Filter:**

```bash
python -m ground_truth.batch_scorer \
  --filter filters/uplifting/v1 \
  --source datasets/training/sample_train.jsonl \
  --output-dir datasets/uplifting \
  --llm gemini-flash \
  --batch-size 50 \
  --max-batches 50
```

**What happens:**
1. Loads pre-filter from `filters/uplifting/v1/prefilter.py`
2. Blocks articles matching rage/outrage/decline patterns (~5%)
3. Labels remaining articles with Gemini Flash
4. Saves to `datasets/uplifting/scored_batch_*.jsonl`

**For Sustainability Filter (same articles, different filter package):**

```bash
python -m ground_truth.batch_scorer \
  --filter filters/sustainability/v1 \
  --source datasets/training/sample_train.jsonl \
  --output-dir datasets/sustainability \
  --llm gemini-flash \
  --batch-size 50 \
  --max-batches 50
```

### What Happens

```
Loading existing master dataset: datasets/training/sample_train.jsonl
  Loaded 0 existing article IDs

Finding content files in: datasets/training
  Found 1 main content files

Processing batch 1 (50 articles)
============================================================
  [1/50] Analyzing article_123...
     SUCCESS
  [2/50] Analyzing article_456...
     SUCCESS
  ...

SAVED 50 labeled articles to scored_batch_001.jsonl

Processing batch 2 (50 articles)
...
```

**Time:** ~3-5 seconds per article = 3-4 hours for 2,250 articles
**Cost:** ~$0.003 per article × 2,250 = ~$6.75

### Resume If Interrupted

The batch labeler saves progress automatically. If interrupted:

```bash
# Just run the same command again
python -m ground_truth.batch_scorer \
  --filter filters/uplifting/v1 \
  --source datasets/training/sample_train.jsonl \
  --output-dir datasets/uplifting \
  --llm gemini-flash \
  --batch-size 50
```

It will skip already-labeled articles (tracked in `.labeled_ids.json`).

### Monitor Progress

**In another terminal:**

```bash
# Check how many labeled so far
wc -l datasets/scored/uplifting/scored_batch_*.jsonl

# Watch session summary
watch -n 10 cat datasets/scored/uplifting/session_summary.json
```

---

## Step 3: Validate Labeled Data

### Check Labeling Quality

```python
# validate_labels.py
import json
from pathlib import Path
from collections import Counter

def validate_labeled_data(labeled_dir, filter_type):
    """Validate Gemini-labeled data quality."""

    labeled_dir = Path(labeled_dir)
    print(f"Validating {filter_type} labels in {labeled_dir}...")

    all_articles = []
    error_count = 0

    # Load all labeled batches
    for batch_file in sorted(labeled_dir.glob("scored_batch_*.jsonl")):
        with open(batch_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    article = json.loads(line.strip())
                    all_articles.append(article)
                except:
                    error_count += 1

    print(f"\n  Total articles: {len(all_articles):,}")
    print(f"  Parse errors: {error_count}")

    # Check for analysis field
    analysis_key = f"{filter_type}_analysis"
    with_analysis = sum(1 for a in all_articles if analysis_key in a)

    print(f"  With {filter_type} analysis: {with_analysis:,} ({with_analysis/len(all_articles)*100:.1f}%)")

    # Check score distributions (for uplifting)
    if filter_type == 'uplifting':
        agency_scores = []
        tiers = []

        for article in all_articles:
            analysis = article.get(analysis_key, {})
            if 'agency' in analysis:
                agency_scores.append(analysis['agency'])
            if 'tier' in analysis:
                tiers.append(analysis['tier'])

        print(f"\n  Agency score distribution:")
        for score, count in sorted(Counter(agency_scores).items()):
            print(f"    Score {score}: {count} articles")

        print(f"\n  Tier distribution:")
        for tier, count in Counter(tiers).most_common():
            print(f"    {tier}: {count} articles ({count/len(tiers)*100:.1f}%)")

    # Check for common issues
    print(f"\n  Quality checks:")

    missing_reasoning = sum(1 for a in all_articles
                          if 'reasoning' not in a.get(analysis_key, {}))
    print(f"    Missing reasoning: {missing_reasoning}")

    empty_analysis = sum(1 for a in all_articles
                        if not a.get(analysis_key))
    print(f"    Empty analysis: {empty_analysis}")

    if empty_analysis == 0 and missing_reasoning < len(all_articles) * 0.05:
        print(f"\n  ✅ Data quality looks good!")
    else:
        print(f"\n  ⚠️  Some quality issues detected. Review error logs.")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("Usage: python validate_labels.py <labeled_dir> <filter_type>")
        print("Example: python validate_labels.py datasets/scored/uplifting uplifting")
        sys.exit(1)

    validate_labeled_data(sys.argv[1], sys.argv[2])
```

**Run validation:**

```bash
python validate_labels.py datasets/scored/uplifting uplifting
```

### Check Labeling Statistics

```bash
# View session summary
cat datasets/scored/uplifting/session_summary.json
```

**Example output:**
```json
{
  "started_at": "2025-10-29T10:00:00",
  "ended_at": "2025-10-29T13:45:00",
  "articles_attempted": 2250,
  "articles_succeeded": 2215,
  "articles_failed": 35,
  "total_retries": 12,
  "errors_by_type": {
    "json_parse_error": 18,
    "timeout": 10,
    "llm_api_error": 7
  }
}
```

**Success rate target:** ≥ 95% (2,215/2,250 = 98.4% ✅)

---

## Step 4: Convert to Training Format

### Why Convert?

Gemini outputs structured JSON (scores, reasoning, etc.). Qwen fine-tuning needs a specific format:

```json
{
  "messages": [
    {"role": "system", "content": "Your classification instructions..."},
    {"role": "user", "content": "ARTICLE:\nTitle: ...\nText: ..."},
    {"role": "assistant", "content": "{\"agency\": 9, \"progress\": 8, ...}"}
  ]
}
```

### Conversion Script

```python
# convert_to_training_format.py
import json
from pathlib import Path

def convert_labels_to_training_format(
    labeled_dir: Path,
    system_prompt_file: Path,
    output_file: Path,
    filter_type: str
):
    """
    Convert Gemini-labeled data to Qwen training format.

    Args:
        labeled_dir: Directory with scored_batch_*.jsonl files
        system_prompt_file: Path to markdown file with system prompt (e.g., prompts/uplifting.md)
        output_file: Where to save training data
        filter_type: 'uplifting', 'sustainability', etc.
    """

    # Load system prompt
    with open(system_prompt_file, 'r', encoding='utf-8') as f:
        system_prompt = f.read()

    analysis_key = f"{filter_type}_analysis"
    training_examples = []
    skipped = 0

    print(f"Converting {filter_type} labels to training format...")
    print(f"  System prompt: {system_prompt_file}")
    print(f"  Output: {output_file}")

    # Load all labeled articles
    for batch_file in sorted(labeled_dir.glob("scored_batch_*.jsonl")):
        with open(batch_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    article = json.loads(line.strip())

                    # Skip if no analysis
                    if analysis_key not in article:
                        skipped += 1
                        continue

                    analysis = article[analysis_key]

                    # Create training example
                    example = {
                        "messages": [
                            {
                                "role": "system",
                                "content": system_prompt
                            },
                            {
                                "role": "user",
                                "content": f"ARTICLE:\nTitle: {article.get('title', 'No title')}\nText: {article.get('content', '')}"
                            },
                            {
                                "role": "assistant",
                                "content": json.dumps(analysis, ensure_ascii=False, indent=2)
                            }
                        ]
                    }

                    training_examples.append(example)

                except Exception as e:
                    print(f"  ⚠️  Error processing article: {e}")
                    skipped += 1
                    continue

    # Save
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for example in training_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    print(f"\n  ✅ Converted {len(training_examples):,} examples")
    print(f"  ⚠️  Skipped {skipped} invalid entries")
    print(f"  📁 Saved to {output_file}")

    return len(training_examples)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 5:
        print("Usage: python convert_to_training_format.py <labeled_dir> <prompt_file> <output_file> <filter_type>")
        print("Example: python convert_to_training_format.py datasets/scored/uplifting prompts/uplifting.md datasets/qwen_training/uplifting_train.jsonl uplifting")
        sys.exit(1)

    convert_labels_to_training_format(
        labeled_dir=Path(sys.argv[1]),
        system_prompt_file=Path(sys.argv[2]),
        output_file=Path(sys.argv[3]),
        filter_type=sys.argv[4]
    )
```

### Convert Labeled Data

**For training set:**

```bash
python convert_to_training_format.py \
  datasets/scored/uplifting \
  prompts/uplifting.md \
  datasets/qwen_training/uplifting_train.jsonl \
  uplifting
```

**For validation set** (label it separately, then convert):

```bash
# Label validation set
python -m ground_truth.batch_scorer \
  --filter filters/uplifting/v1 \
  --source datasets/training/sample_val.jsonl \
  --output-dir datasets/uplifting_val \
  --llm gemini-flash

# Convert
python convert_to_training_format.py \
  datasets/uplifting_val \
  filters/uplifting/v1/prompt-compressed.md \
  datasets/qwen_training/uplifting_val.jsonl \
  uplifting
```

---

## Step 5: Final Quality Check

### Inspect Training Data

```python
# inspect_training_data.py
import json

def inspect_training_examples(file_path, num_examples=3):
    """Show sample training examples."""

    print(f"Inspecting: {file_path}\n")

    with open(file_path, 'r', encoding='utf-8') as f:
        examples = [json.loads(line) for line in f]

    print(f"Total examples: {len(examples):,}\n")

    # Show samples
    for i, example in enumerate(examples[:num_examples], 1):
        print(f"{'='*70}")
        print(f"EXAMPLE {i}")
        print(f"{'='*70}")

        for msg in example['messages']:
            role = msg['role'].upper()
            content = msg['content']

            # Truncate long content
            if len(content) > 500:
                content = content[:500] + "..."

            print(f"\n[{role}]")
            print(content)

        print()

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python inspect_training_data.py <training_file>")
        sys.exit(1)

    inspect_training_examples(sys.argv[1])
```

**Run inspection:**

```bash
python inspect_training_data.py datasets/qwen_training/uplifting_train.jsonl
```

### Verify Format

**Expected structure:**
- ✅ Each line is valid JSON
- ✅ Each example has "messages" array
- ✅ Messages have "role" and "content" fields
- ✅ Roles are: "system", "user", "assistant"
- ✅ Assistant content is valid JSON (scores dictionary)

---

## Complete Workflow Summary

### For One Filter (e.g., Uplifting)

```bash
# 0. CALIBRATION (do this first! - see ground_truth/README.md)
python -m ground_truth.calibrate_prefilter \
  --filter filters/uplifting/v1 \
  --source "datasets/raw/master_dataset_*.jsonl" \
  --sample-size 500

python -m ground_truth.calibrate_oracle \
  --filter filters/uplifting/v1 \
  --source "datasets/raw/master_dataset_*.jsonl" \
  --sample-size 100 \
  --models gemini-flash,gemini-pro

# 1. Create sample (once for all filters)
python create_sample.py

# 2. Label training set (with pre-filter)
python -m ground_truth.batch_scorer \
  --filter filters/uplifting/v1 \
  --source datasets/training/sample_train.jsonl \
  --output-dir datasets/uplifting \
  --llm gemini-flash

# 3. Label validation set (with pre-filter)
python -m ground_truth.batch_scorer \
  --filter filters/uplifting/v1 \
  --source datasets/training/sample_val.jsonl \
  --output-dir datasets/uplifting_val \
  --llm gemini-flash

# 4. Validate quality
python validate_labels.py datasets/uplifting uplifting

# 5. Convert to training format
python convert_to_training_format.py \
  datasets/uplifting \
  filters/uplifting/v1/prompt-compressed.md \
  datasets/qwen_training/uplifting_train.jsonl \
  uplifting

python convert_to_training_format.py \
  datasets/uplifting_val \
  filters/uplifting/v1/prompt-compressed.md \
  datasets/qwen_training/uplifting_val.jsonl \
  uplifting

# 6. Inspect results
python inspect_training_data.py datasets/qwen_training/uplifting_train.jsonl
```

### For Multiple Filters

You can label the SAME sample with different filter packages:

```bash
# Same sample, different filters (with pre-filtering)
python -m ground_truth.batch_scorer \
  --filter filters/uplifting/v1 \
  --source datasets/training/sample_train.jsonl \
  --output-dir datasets/uplifting \
  --llm gemini-flash

python -m ground_truth.batch_scorer \
  --filter filters/sustainability/v1 \
  --source datasets/training/sample_train.jsonl \
  --output-dir datasets/sustainability \
  --llm gemini-flash
```

**Note**: Each filter's pre-filter will block different articles, so final labeled counts may differ.

---

## File Structure After Completion

```
llm-distillery/
├── datasets/
│   ├── raw/
│   │   ├── master_dataset_20250929_20251008.jsonl
│   │   ├── master_dataset_20251009_20251025.jsonl
│   │   └── master_dataset_20251026_20251029.jsonl
│   │
│   ├── training/
│   │   ├── sample_train.jsonl                (2,250 articles)
│   │   └── sample_val.jsonl                  (250 articles)
│   │
│   ├── labeled/
│   │   ├── uplifting/
│   │   │   ├── scored_batch_001.jsonl
│   │   │   ├── scored_batch_002.jsonl
│   │   │   ├── ...
│   │   │   ├── session_summary.json
│   │   │   └── .labeled_ids.json
│   │   │
│   │   ├── uplifting_val/
│   │   │   └── scored_batch_001.jsonl
│   │   │
│   │   └── sustainability/
│   │       └── ...
│   │
│   └── qwen_training/
│       ├── uplifting_train.jsonl             (ready for fine-tuning)
│       ├── uplifting_val.jsonl
│       ├── sustainability_train.jsonl
│       └── sustainability_val.jsonl
│
├── prompts/
│   ├── uplifting.md
│   ├── sustainability.md
│   └── seece.md
│
└── ground_truth/
    ├── batch_scorer.py
    └── secrets_manager.py
```

---

## Troubleshooting

### Issue: "Gemini API key not found"

**Solution:**
```bash
# Add to ground_truth/secrets.ini
[llm]
gemini_api_key = YOUR_KEY_HERE
```

### Issue: "429 Resource exhausted"

**Solution:** Rate limiting kicked in. The batch_scorer handles this automatically with:
- Exponential backoff (1s → 2s → 4s)
- 0.5s wait between requests
- 3 retry attempts

Just let it run - it will recover.

### Issue: "JSON parse errors"

The batch_scorer has built-in JSON repair. Check:
```bash
cat datasets/scored/uplifting/session_summary.json
```

If error rate > 5%, check `error_logs/` directory for details.

### Issue: "Out of memory"

Reduce batch size:
```bash
python -m ground_truth.batch_scorer \
  --batch-size 25 \  # Instead of 50
  ...
```

---

## Cost & Time Estimates

### Labeling Costs (Gemini Flash)

| Articles | Cost (est.) | Time (est.) |
|----------|-------------|-------------|
| 2,500 | $7-10 | 3-4 hours |
| 5,000 | $15-20 | 6-8 hours |
| 10,000 | $30-40 | 12-16 hours |

**Recommended:** Start with 2,500 articles

### Per Filter

If you label 2,500 articles for 3 filters (uplifting, sustainability, SEECE):
- **Option A:** Same sample, 3 prompts = $21-30 total
- **Option B:** Different samples per filter = $21-30 per filter

**Recommendation:** Use same sample with different prompts (Option A)

---

## Next Steps

After completing ground truth generation:

1. **✅ You have:**
   - Training data: `datasets/qwen_training/*_train.jsonl`
   - Validation data: `datasets/qwen_training/*_val.jsonl`

2. **➡️ Next:** Fine-tune Qwen agents
   - See: `docs/guides/qwen-finetuning-guide.md`
   - Start with one filter (e.g., uplifting)
   - Expected training time: 7-10 hours

3. **➡️ Then:** Deploy and evaluate
   - Test on validation set
   - Compare with Gemini baseline
   - Deploy to production

---

## Resources

- **batch_scorer.py**: Core labeling script
- **qwen-finetuning-guide.md**: Next step after labeling
- **prompts/**: Prompt templates for each filter

---

**Document Version:** 2.0 (Simplified)
**Created:** October 29, 2025
**Author:** Claude (Anthropic)
