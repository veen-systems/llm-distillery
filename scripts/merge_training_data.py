"""
Merge existing training data with new oracle-scored articles.

Handles two input formats:
1. Existing training format: {"id", "title", "content", "url", "labels": [...], "dimension_names": [...]}
2. Oracle-scored format: {"id", "title", "content", ..., "{filter}_analysis": {"dim": {"score": X, "evidence": "..."}}}

Newly-converted rows carry every source field plus the analysis block under
"oracle_meta" (#155). Rows loaded from an --existing-dir built before that fix do
not, so the merge prints its oracle_meta coverage and warns when it is partial.

Deduplicates by article ID, re-splits 80/10/10 with stratification.

Usage:
    python scripts/merge_training_data.py \
        --existing-dir datasets/training/sustainability_technology_v3 \
        --new-scored "datasets/scored/sustainability_technology_active_learning/sustainability_technology/scored_batch_*.jsonl" \
        --output-dir datasets/training/sustainability_technology_v3 \
        --analysis-field sustainability_technology_analysis \
        --dimensions technology_readiness_level technical_performance economic_competitiveness life_cycle_environmental_impact social_equity_impact governance_systemic_impact
"""

import argparse
import glob
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple


DIMENSION_ORDER = [
    "technology_readiness_level",
    "technical_performance",
    "economic_competitiveness",
    "life_cycle_environmental_impact",
    "social_equity_impact",
    "governance_systemic_impact",
]


def load_existing_training_data(data_dir: Path) -> List[Dict[str, Any]]:
    """Load existing train/val/test splits and combine into one pool."""
    articles = []
    for split in ["train.jsonl", "val.jsonl", "test.jsonl"]:
        path = data_dir / split
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        articles.append(json.loads(line))
            print(f"  Loaded {split}: {sum(1 for _ in open(path, encoding='utf-8'))} articles")
    return articles


def load_oracle_scored(pattern: str) -> List[Dict[str, Any]]:
    """Load oracle-scored articles from batch files."""
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files matching: {pattern}")

    articles = []
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    articles.append(json.loads(line))
    print(f"  Loaded {len(articles)} articles from {len(files)} batch files")
    return articles


def convert_oracle_to_training(
    article: Dict[str, Any],
    analysis_field: str,
    dimensions: List[str],
) -> Dict[str, Any]:
    """Convert an oracle-scored article to training format."""
    analysis = article.get(analysis_field, {})
    if not analysis:
        return None

    labels = []
    for dim in dimensions:
        dim_data = analysis.get(dim, {})
        if isinstance(dim_data, dict):
            labels.append(float(dim_data.get("score", 0)))
        elif isinstance(dim_data, (int, float)):
            labels.append(float(dim_data))
        else:
            labels.append(0.0)

    # Same shape as training/prepare_data.py: carry every source field through,
    # then overlay the derived ones, and keep the analysis block whole under the
    # stable key "oracle_meta" (#155). An allowlist here would silently drop the
    # oracle's non-dimensional output -- scope_verdict, dominant_subject,
    # content_type -- on exactly the rows active learning just paid to score.
    record = {k: v for k, v in article.items() if k != analysis_field}
    record.update({
        "id": article.get("id", ""),
        "title": article.get("title", ""),
        "content": article.get("content", ""),
        "url": article.get("url", ""),
        "labels": labels,
        "dimension_names": dimensions,
        "oracle_meta": analysis,
    })
    return record


def assign_score_bin(avg_score: float) -> str:
    """Assign score bin for stratification."""
    if avg_score >= 8.0:
        return "very_high"
    elif avg_score >= 6.0:
        return "high"
    elif avg_score >= 4.0:
        return "medium"
    elif avg_score >= 2.0:
        return "low"
    else:
        return "very_low"


def stratified_split(
    articles: List[Dict[str, Any]],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
) -> Tuple[List, List, List]:
    """Split articles with stratification by score bin."""
    random.seed(seed)

    # Group by score bin
    bins = {}
    for article in articles:
        avg = sum(article["labels"]) / len(article["labels"])
        b = assign_score_bin(avg)
        bins.setdefault(b, []).append(article)

    print(f"\n  Stratification distribution:")
    for b in ["very_low", "low", "medium", "high", "very_high"]:
        count = len(bins.get(b, []))
        pct = count / len(articles) * 100 if articles else 0
        print(f"    {b:12s}: {count:5d} ({pct:5.1f}%)")

    train, val, test = [], [], []
    for b, items in bins.items():
        random.shuffle(items)
        n = len(items)
        t1 = int(n * train_ratio)
        t2 = int(n * (train_ratio + val_ratio))
        train.extend(items[:t1])
        val.extend(items[t1:t2])
        test.extend(items[t2:])

    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)
    return train, val, test


def main():
    parser = argparse.ArgumentParser(description="Merge training data with new oracle-scored articles")
    parser.add_argument("--existing-dir", type=Path, required=True, help="Directory with existing train/val/test.jsonl")
    parser.add_argument("--new-scored", type=str, required=True, help="Glob pattern for new oracle-scored files")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory for merged splits")
    parser.add_argument("--analysis-field", type=str, required=True, help="Analysis field name (e.g. sustainability_technology_analysis)")
    parser.add_argument("--dimensions", nargs="+", default=DIMENSION_ORDER, help="Dimension names in order")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    # 1. Load existing training data
    print(f"Loading existing training data from {args.existing_dir}...")
    existing = load_existing_training_data(args.existing_dir)
    print(f"  Total existing: {len(existing)}")

    # 2. Load new oracle-scored articles
    print(f"\nLoading new oracle-scored articles...")
    new_scored = load_oracle_scored(args.new_scored)

    # 3. Convert new articles to training format
    print(f"\nConverting {len(new_scored)} oracle-scored articles to training format...")
    converted = []
    skipped = 0
    for article in new_scored:
        result = convert_oracle_to_training(article, args.analysis_field, args.dimensions)
        if result:
            converted.append(result)
        else:
            skipped += 1
    print(f"  Converted: {len(converted)}, Skipped (no analysis): {skipped}")

    # 4. Merge and deduplicate by ID
    print(f"\nMerging and deduplicating...")
    seen_ids = {}
    # New data takes priority (more recent oracle scores)
    for article in converted:
        seen_ids[article["id"]] = article
    # Add existing data only if ID not already seen
    existing_dupes = 0
    for article in existing:
        if article["id"] in seen_ids:
            existing_dupes += 1
        else:
            seen_ids[article["id"]] = article
    merged = list(seen_ids.values())
    print(f"  Existing: {len(existing)}")
    print(f"  New: {len(converted)}")
    print(f"  Duplicates (existing articles re-scored): {existing_dupes}")
    print(f"  Merged total: {len(merged)}")

    # Coverage, printed rather than assumed. Rows loaded from an --existing-dir
    # built before #155 carry no oracle_meta, so a merge can be PARTIALLY
    # covered. A consumer counting scope_verdict presence on a partial merge
    # reads the gap as a real rate; say it out loud instead.
    with_meta = sum(1 for a in merged if a.get("oracle_meta"))
    pct = (with_meta / len(merged) * 100) if merged else 0.0
    print(f"  oracle_meta coverage: {with_meta}/{len(merged)} ({pct:.1f}%)")
    if merged and with_meta < len(merged):
        print(f"  WARNING: {len(merged) - with_meta} merged rows carry no oracle_meta "
              f"(splits in {args.existing_dir} predate llm-distillery#155).")
        print(f"           Do NOT read a scope_verdict rate off these splits -- "
              f"rebuild from the label file with training/prepare_data.py instead.")

    # 5. Re-split with stratification
    print(f"\nSplitting 80/10/10 with stratification...")
    train, val, test = stratified_split(merged, seed=args.seed)
    print(f"\n  Train: {len(train)}")
    print(f"  Val:   {len(val)}")
    print(f"  Test:  {len(test)}")

    # 6. Save
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in [("train.jsonl", train), ("val.jsonl", val), ("test.jsonl", test)]:
        path = args.output_dir / name
        with open(path, "w", encoding="utf-8") as f:
            for article in data:
                f.write(json.dumps(article, ensure_ascii=False) + "\n")
        print(f"  Saved {path}: {len(data)} articles")

    print(f"\nDone! Total: {len(merged)} articles -> {len(train)}/{len(val)}/{len(test)} splits")


if __name__ == "__main__":
    main()
