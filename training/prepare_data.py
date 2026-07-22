"""
Generic training data preparation script for any filter.

This script:
1. Reads filter configuration to extract dimensions, tiers, analysis field
2. Loads oracle-labeled data
3. Splits into train/val/test sets (stratified by tier)
4. Converts to simplified training format (score arrays only)
5. Exports in JSONL format for Qwen training

Usage:
    python training/prepare_data.py \
        --filter filters/uplifting/v1 \
        --input datasets/labeled/uplifting/labeled_articles.jsonl \
        --output-dir datasets/training/uplifting \
        --train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1
"""

# Standard library imports
import argparse
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Third-party imports
import yaml

# Local imports
from ground_truth import analysis_field_name


def load_filter_config(filter_dir: Path) -> Dict[str, Any]:
    """Load filter configuration from config.yaml."""
    config_file = filter_dir / 'config.yaml'

    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def extract_filter_info(config: Dict[str, Any]) -> Tuple[str, List[str], Dict[str, float]]:
    """Extract filter name, dimension names, and tier boundaries from config.

    Returns:
        (filter_name, dimension_names, tier_boundaries)
    """
    filter_name = config['filter']['name']

    # Extract dimensions in order (maintaining order from config)
    dimensions_config = config['scoring']['dimensions']
    dimension_names = list(dimensions_config.keys())

    # Extract tier boundaries
    tiers_config = config['scoring'].get('tiers', {})
    tier_boundaries = {}

    for tier_name, tier_info in tiers_config.items():
        threshold = tier_info.get('threshold', 0.0)
        tier_boundaries[tier_name] = threshold

    # Sort tiers by threshold (descending) for tier assignment
    tier_boundaries = dict(sorted(tier_boundaries.items(),
                                  key=lambda x: x[1],
                                  reverse=True))

    return filter_name, dimension_names, tier_boundaries


def get_analysis_field_name(filter_name: str) -> str:
    """Infer analysis field name from filter name. Delegates to shared convention."""
    return analysis_field_name(filter_name)


def load_labels(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load oracle-labeled articles from JSONL file(s).

    Supports both single files and glob patterns for loading multiple
    batch files at once.

    Args:
        input_path: Path to JSONL file, or glob pattern (e.g., "scored_batch_*.jsonl")

    Returns:
        List of article dicts with oracle analysis

    Raises:
        FileNotFoundError: If path/pattern matches no files

    Examples:
        >>> # Single file
        >>> labels = load_labels(Path("datasets/labeled/articles.jsonl"))

        >>> # Glob pattern for multiple batch files
        >>> labels = load_labels(Path("datasets/scored/scored_batch_*.jsonl"))
    """
    import glob

    labels = []

    # Check if path contains wildcard
    input_str = str(input_path)
    if '*' in input_str or '?' in input_str:
        # Glob pattern - load all matching files
        files = sorted(glob.glob(input_str))
        if not files:
            raise FileNotFoundError(f"No files matching pattern: {input_path}")

        print(f"Found {len(files)} files matching pattern")
        for file_path in files:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        labels.append(json.loads(line))
    else:
        # Single file
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    labels.append(json.loads(line))

    # Defensive de-dup by id. Merging multiple scored files (or a resumed run
    # that appended) can repeat an article, and the e5 screen can legitimately
    # surface the same id across pool files. Keep the LAST occurrence (newest
    # label) and report the collapse. Records without an "id" are kept as-is.
    # (Review 2026-07-18: prepare_data had no dedup; upstream exact-id exclusion
    # does not protect this stage. Near-duplicate *distinct* ids are handled at
    # pool assembly, not here.)
    by_id: Dict[str, Any] = {}
    no_id: List[Dict[str, Any]] = []
    for rec in labels:
        rid = rec.get("id")
        if rid is None:
            no_id.append(rec)
        else:
            by_id[rid] = rec  # last wins
    deduped = list(by_id.values()) + no_id
    dropped = len(labels) - len(deduped)
    if dropped:
        print(f"  De-duplicated {dropped} repeated id(s): {len(labels)} -> {len(deduped)}")

    return deduped


def calculate_overall_score(
    analysis: Dict[str, Any],
    dimension_names: List[str] = None
) -> float:
    """Calculate overall score from analysis.

    Tries to find overall_score field first, then calculates average from dimensions.
    """
    # Try different field names for overall score
    overall_score = (analysis.get('overall_score') or
                    analysis.get('overall_uplift_score'))

    # If no overall score field, calculate average from dimensions
    if overall_score is None and dimension_names:
        scores = []
        for dim in dimension_names:
            # Handle both nested and flat formats
            dim_data = analysis.get(dim)
            if isinstance(dim_data, dict) and 'score' in dim_data:
                scores.append(dim_data['score'])
            elif isinstance(dim_data, (int, float)):
                scores.append(dim_data)
        overall_score = sum(scores) / len(scores) if scores else 0.0
    elif overall_score is None:
        overall_score = 0.0

    return overall_score


def assign_tier(overall_score: float, tier_boundaries: Dict[str, float]) -> str:
    """Assign tier based on overall score and tier boundaries.

    Args:
        overall_score: The overall score
        tier_boundaries: Dict mapping tier names to minimum thresholds (sorted descending)

    Returns:
        Tier name (metadata only, not used in training)
    """
    for tier_name, threshold in tier_boundaries.items():
        if overall_score >= threshold:
            return tier_name

    # Return lowest tier if no match
    return list(tier_boundaries.keys())[-1]


def assign_score_bin(overall_score: float) -> str:
    """Assign score bin for stratification when tiers are not available.

    Bins:
        0-2: very_low
        2-4: low
        4-6: medium
        6-8: high
        8-10: very_high
    """
    if overall_score >= 8.0:
        return 'very_high'
    elif overall_score >= 6.0:
        return 'high'
    elif overall_score >= 4.0:
        return 'medium'
    elif overall_score >= 2.0:
        return 'low'
    else:
        return 'very_low'


def stratified_split(
    labels: List[Dict[str, Any]],
    analysis_field: str,
    tier_boundaries: Dict[str, float],
    dimension_names: List[str] = None,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Split labeled data into train/validation/test sets with stratification.

    Stratification ensures each split maintains the same distribution of
    quality tiers (or score bins) as the original dataset. This prevents
    train/test skew where one split might have mostly high-quality articles.

    Stratification method:
    - If tier_boundaries provided: Groups by tier (e.g., gold/silver/bronze)
    - Otherwise: Groups by score bins (very_low/low/medium/high/very_high)

    Args:
        labels: List of articles with oracle analysis results
        analysis_field: Key containing analysis (e.g., "uplifting_analysis")
        tier_boundaries: Dict mapping tier names to minimum score thresholds,
                        sorted by threshold descending. Empty dict uses score bins.
        dimension_names: Ordered list of dimension names for score calculation.
                        Required if analysis uses nested dimension format.
        train_ratio: Proportion for training set (default: 0.8 = 80%)
        val_ratio: Proportion for validation set (default: 0.1 = 10%)
        test_ratio: Proportion for test set (default: 0.1 = 10%)
        seed: Random seed for reproducibility (default: 42)

    Returns:
        Tuple of (train_set, val_set, test_set), each a list of article dicts

    Raises:
        AssertionError: If ratios don't sum to approximately 1.0

    Example:
        >>> train, val, test = stratified_split(
        ...     labels=labeled_articles,
        ...     analysis_field="uplifting_analysis",
        ...     tier_boundaries={"gold": 8.0, "silver": 6.0, "bronze": 4.0},
        ...     dimension_names=["agency", "progress", "connection"],
        ...     train_ratio=0.8, val_ratio=0.1, test_ratio=0.1
        ... )
        >>> print(f"Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")

    Notes:
        - Small strata (<10 examples) may not maintain exact ratios
        - Each stratum is shuffled independently before splitting
        - Final sets are shuffled after combining all strata
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.01, "Ratios must sum to 1.0"

    random.seed(seed)

    # Determine stratification method
    use_score_bins = not tier_boundaries or len(tier_boundaries) == 0

    if use_score_bins:
        print("Using score bin stratification (no tiers defined)")
    else:
        print(f"Using tier stratification ({len(tier_boundaries)} tiers)")

    # Group by tier or score bin
    tier_groups = {}
    for label in labels:
        analysis = label.get(analysis_field, {})

        # Calculate overall score
        overall_score = calculate_overall_score(analysis, dimension_names)

        # Assign to stratum (tier or score bin)
        if use_score_bins:
            stratum = assign_score_bin(overall_score)
        else:
            stratum = assign_tier(overall_score, tier_boundaries)

        if stratum not in tier_groups:
            tier_groups[stratum] = []
        tier_groups[stratum].append(label)

    # Print stratification distribution
    print(f"\nStratification distribution:")
    for stratum in sorted(tier_groups.keys()):
        count = len(tier_groups[stratum])
        pct = (count / len(labels) * 100) if len(labels) > 0 else 0
        print(f"  {stratum:20s}: {count:5d} ({pct:5.1f}%)")

    # Split each stratum
    train_set = []
    val_set = []
    test_set = []

    for stratum, items in tier_groups.items():
        random.shuffle(items)

        n = len(items)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        train_set.extend(items[:train_end])
        val_set.extend(items[train_end:val_end])
        test_set.extend(items[val_end:])

    # Shuffle final sets
    random.shuffle(train_set)
    random.shuffle(val_set)
    random.shuffle(test_set)

    return train_set, val_set, test_set


def convert_to_training_format(
    labels: List[Dict[str, Any]],
    analysis_field: str,
    dimension_names: List[str]
) -> List[Dict[str, Any]]:
    """
    Convert oracle-labeled articles to simplified training format.

    Extracts dimensional scores from oracle analysis and creates a format
    suitable for training regression models. The output uses score arrays
    for efficient batch processing during training.

    Input format (oracle labels):
        {
            "id": "article-123",
            "title": "Article Title",
            "content": "Full article text...",
            "uplifting_analysis": {
                "dimensions": {
                    "agency": {"score": 7, "reasoning": "..."},
                    "progress": 8,  # Flat format also supported
                    ...
                }
            }
        }

    Output format (training data):
        {
            "id": "article-123",
            "title": "Article Title",
            "content": "Full article text...",
            "url": "https://...",
            "labels": [7, 8, 6, 5, 7, 4],  # Scores in dimension order
            "dimension_names": ["agency", "progress", ...]
        }

    Args:
        labels: List of articles with oracle analysis
        analysis_field: Key containing analysis (e.g., "uplifting_analysis")
        dimension_names: Ordered list of dimension names. Order determines
                        the position of each score in the labels array.

    Returns:
        List of training examples with score arrays

    Notes:
        - Articles without analysis are silently skipped
        - Missing dimensions default to score 0
        - Supports both nested format (dim: {score, reasoning})
          and flat format (dim: score)
    """
    training_data = []

    for label in labels:
        analysis = label.get(analysis_field, {})

        if not analysis:
            continue  # Skip if no analysis

        # Extract dimension scores in correct order
        # Handle two formats:
        # 1. Nested: analysis['dimensions'][dim_name] = score or {score: X, reasoning: Y}
        # 2. Flat: analysis[dim_name] = score
        dimensions = analysis.get('dimensions', analysis)  # If no 'dimensions' key, use analysis itself

        # Handle nested structure (dimensions can be objects with score/reasoning vs. flat score values)
        score_array = []
        for dim in dimension_names:
            dim_value = dimensions.get(dim, 0)

            # If it's a dict with 'score' field, extract score
            if isinstance(dim_value, dict):
                score_array.append(dim_value.get('score', 0))
            else:
                # Otherwise assume it's the score directly
                score_array.append(dim_value)

        # Get content (handle different field names)
        content = label.get('content', label.get('description', ''))

        training_data.append({
            'id': label.get('id', ''),
            'title': label.get('title', ''),
            'content': content,
            'url': label.get('url', ''),
            'labels': score_array,
            'dimension_names': dimension_names
        })

    return training_data


def save_training_data(
    train_data: List[Dict[str, Any]],
    val_data: List[Dict[str, Any]],
    test_data: List[Dict[str, Any]],
    output_dir: Path
):
    """
    Save training, validation, and test data to JSONL files.

    Creates the output directory if needed and writes:
    - train.jsonl: Training examples
    - val.jsonl: Validation examples
    - test.jsonl: Test examples

    Args:
        train_data: List of training examples
        val_data: List of validation examples
        test_data: List of test examples
        output_dir: Directory to save files (created if needed)

    Example:
        >>> save_training_data(train, val, test, Path("datasets/training/uplifting"))
        # Creates:
        #   datasets/training/uplifting/train.jsonl
        #   datasets/training/uplifting/val.jsonl
        #   datasets/training/uplifting/test.jsonl
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save train set
    train_file = output_dir / 'train.jsonl'
    with open(train_file, 'w', encoding='utf-8') as f:
        for item in train_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    # Save val set
    val_file = output_dir / 'val.jsonl'
    with open(val_file, 'w', encoding='utf-8') as f:
        for item in val_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    # Save test set
    test_file = output_dir / 'test.jsonl'
    with open(test_file, 'w', encoding='utf-8') as f:
        for item in test_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"\nSaved training data:")
    print(f"  Train: {train_file} ({len(train_data)} examples)")
    print(f"  Val:   {val_file} ({len(val_data)} examples)")
    print(f"  Test:  {test_file} ({len(test_data)} examples)")


def print_statistics(
    labels: List[Dict[str, Any]],
    train_set: List[Dict[str, Any]],
    val_set: List[Dict[str, Any]],
    test_set: List[Dict[str, Any]],
    analysis_field: str,
    tier_boundaries: Dict[str, float],
    dimension_names: List[str] = None
):
    """Print dataset statistics."""
    print("\n" + "="*70)
    print("DATASET STATISTICS")
    print("="*70)

    use_score_bins = not tier_boundaries or len(tier_boundaries) == 0

    if use_score_bins:
        print("\nOriginal Dataset (Score bin distribution):")
        strata_order = ['very_low', 'low', 'medium', 'high', 'very_high']
    else:
        print("\nOriginal Dataset (Tier distribution):")
        strata_order = list(tier_boundaries.keys())

    stratum_counts = Counter()
    for label in labels:
        analysis = label.get(analysis_field, {})
        overall_score = calculate_overall_score(analysis, dimension_names)
        if use_score_bins:
            stratum = assign_score_bin(overall_score)
        else:
            stratum = assign_tier(overall_score, tier_boundaries)
        stratum_counts[stratum] += 1

    total = len(labels)
    for stratum_name in strata_order:
        count = stratum_counts.get(stratum_name, 0)
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {stratum_name:20s}: {count:5d} ({pct:5.1f}%)")

    print(f"\nSplit Sizes (Stratified):")
    print(f"  Train: {len(train_set)} labels")
    print(f"  Val:   {len(val_set)} labels")
    print(f"  Test:  {len(test_set)} labels")

    if use_score_bins:
        print(f"\nTrain Score Bin Distribution:")
    else:
        print(f"\nTrain Tier Distribution:")

    train_stratum_counts = Counter()
    for item in train_set:
        analysis = item.get(analysis_field, {})
        overall_score = calculate_overall_score(analysis, dimension_names)
        if use_score_bins:
            stratum = assign_score_bin(overall_score)
        else:
            stratum = assign_tier(overall_score, tier_boundaries)
        train_stratum_counts[stratum] += 1

    train_total = len(train_set)
    for stratum_name in strata_order:
        count = train_stratum_counts.get(stratum_name, 0)
        pct = (count / train_total * 100) if train_total > 0 else 0
        print(f"  {stratum_name:20s}: {count:5d} ({pct:5.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description='Prepare training data for any filter',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Uplifting filter
  python scripts/prepare_training_data.py \\
      --filter filters/uplifting/v1 \\
      --input datasets/labeled/uplifting/labeled_articles.jsonl \\
      --output-dir datasets/training/uplifting

  # Tech deployment filter
  python scripts/prepare_training_data.py \\
      --filter filters/sustainability_tech_deployment/v1 \\
      --input datasets/labeled/sustainability_tech_deployment/labeled_articles.jsonl \\
      --output-dir datasets/training/sustainability_tech_deployment
        """)

    parser.add_argument('--filter', type=str, required=True,
                       help='Path to filter directory (e.g., filters/uplifting/v1)')
    parser.add_argument('--input', type=str, required=True,
                       help='Input JSONL file with oracle labels')
    parser.add_argument('--output-dir', type=str, required=True,
                       help='Output directory for train/val/test splits')
    parser.add_argument('--train-ratio', type=float, default=0.8,
                       help='Training set ratio (default: 0.8)')
    parser.add_argument('--val-ratio', type=float, default=0.1,
                       help='Validation set ratio (default: 0.1)')
    parser.add_argument('--test-ratio', type=float, default=0.1,
                       help='Test set ratio (default: 0.1)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility')

    args = parser.parse_args()

    filter_dir = Path(args.filter)
    input_file = Path(args.input)
    output_dir = Path(args.output_dir)

    # Load filter configuration
    print(f"Loading filter configuration from: {filter_dir}")
    config = load_filter_config(filter_dir)
    filter_name, dimension_names, tier_boundaries = extract_filter_info(config)
    analysis_field = get_analysis_field_name(filter_name)

    print(f"Filter: {filter_name}")
    print(f"Dimensions: {len(dimension_names)} ({', '.join(dimension_names)})")
    print(f"Analysis field: {analysis_field}")
    print(f"Tiers: {len(tier_boundaries)} ({', '.join(tier_boundaries.keys())})")

    # Load labels
    print(f"\nLoading labels from: {input_file}")
    labels = load_labels(input_file)
    print(f"Loaded {len(labels)} labels")

    # Split data
    print(f"\nSplitting into train/val/test ({args.train_ratio}/{args.val_ratio}/{args.test_ratio})...")
    train_set, val_set, test_set = stratified_split(
        labels,
        analysis_field,
        tier_boundaries,
        dimension_names,
        args.train_ratio,
        args.val_ratio,
        args.test_ratio,
        args.seed
    )

    # Convert to training format
    print(f"\nConverting to training format (score arrays only)...")
    train_data = convert_to_training_format(train_set, analysis_field, dimension_names)
    val_data = convert_to_training_format(val_set, analysis_field, dimension_names)
    test_data = convert_to_training_format(test_set, analysis_field, dimension_names)

    # Print statistics
    print_statistics(labels, train_set, val_set, test_set, analysis_field, tier_boundaries, dimension_names)

    # Save data
    save_training_data(train_data, val_data, test_data, output_dir)

    print("\n" + "="*70)
    print("TRAINING DATA PREPARATION COMPLETE")
    print("="*70)
    print(f"\nFilter: {filter_name} ({len(dimension_names)} dimensions)")
    print(f"Output directory: {output_dir}")
    print(f"Format: Simplified score arrays")
    print(f"Stratification: Maintains tier proportions across splits")
    print(f"Note: Tier labels are metadata only, training uses dimensional scores")


if __name__ == '__main__':
    main()
