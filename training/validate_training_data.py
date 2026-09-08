"""
Standardized quality validation for training data.

Usage:
    python training/validate_training_data.py --data-dir datasets/training/uplifting_v4
    python training/validate_training_data.py --data-dir datasets/training/uplifting_v4 --filter filters/uplifting/v4
"""

# Standard library imports
import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Third-party imports
import yaml


class TrainingDataValidator:
    def __init__(self, data_dir: Path, filter_dir: Path = None):
        self.data_dir = data_dir
        self.filter_dir = filter_dir
        self.train_data = []
        self.val_data = []
        self.test_data = []
        self.issues = []
        self.warnings = []
        self.stats = {}

    def load_data(self) -> bool:
        """Load all training data files."""
        try:
            train_file = self.data_dir / 'train.jsonl'
            val_file = self.data_dir / 'val.jsonl'
            test_file = self.data_dir / 'test.jsonl'

            if not train_file.exists():
                self.issues.append(f"Missing train.jsonl")
                return False
            if not val_file.exists():
                self.issues.append(f"Missing val.jsonl")
                return False
            if not test_file.exists():
                self.issues.append(f"Missing test.jsonl")
                return False

            # Load train
            with open(train_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        self.train_data.append(json.loads(line))

            # Load val
            with open(val_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        self.val_data.append(json.loads(line))

            # Load test
            with open(test_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        self.test_data.append(json.loads(line))

            return True
        except json.JSONDecodeError as e:
            self.issues.append(f"JSON parsing error: {e}")
            return False
        except Exception as e:
            self.issues.append(f"Error loading data: {e}")
            return False

    def check_structural_integrity(self):
        """Check structural integrity of the data."""
        all_data = self.train_data + self.val_data + self.test_data

        # Check required fields
        required_fields = ['id', 'title', 'content', 'labels', 'dimension_names']
        for i, example in enumerate(all_data[:10]):  # Check first 10
            missing = [f for f in required_fields if f not in example]
            if missing:
                self.issues.append(f"Example {i}: Missing fields {missing}")

        # oracle_meta coverage -- over EVERY row, not a sample.
        # Nothing inspected the produced split files, which is how #155 survived a
        # whole training cycle: the oracle's non-dimensional output (scope_verdict,
        # dominant_subject, content_type) was dropped at split time in silence.
        # A warning, not an issue: splits built before 2026-09-08 legitimately have
        # none, and those must still validate.
        if all_data:
            with_meta = sum(1 for ex in all_data if ex.get('oracle_meta'))
            self.stats['oracle_meta_coverage'] = (with_meta, len(all_data))
            if with_meta == 0:
                self.warnings.append(
                    f"No oracle_meta on any of {len(all_data)} rows - these splits predate "
                    f"llm-distillery#155. Rebuild with training/prepare_data.py before "
                    f"training anything that needs scope_verdict."
                )
            elif with_meta < len(all_data):
                self.warnings.append(
                    f"oracle_meta on only {with_meta}/{len(all_data)} rows (PARTIAL). A "
                    f"scope_verdict rate read off these splits is a coverage artefact, not "
                    f"a rate - see scripts/merge_training_data.py."
                )

        # Check for duplicate IDs
        all_ids = [ex['id'] for ex in all_data]
        id_counts = Counter(all_ids)
        duplicates = {id_: count for id_, count in id_counts.items() if count > 1}
        if duplicates:
            self.issues.append(f"Found {len(duplicates)} duplicate IDs: {list(duplicates.keys())[:5]}")

        # Check labels array length matches dimension count
        if all_data:
            first_example = all_data[0]
            expected_dims = len(first_example.get('dimension_names', []))

            for i, example in enumerate(all_data[:100]):  # Check first 100
                labels = example.get('labels', [])
                if len(labels) != expected_dims:
                    self.issues.append(f"Example {i} ({example.get('id')}): Expected {expected_dims} labels, got {len(labels)}")

    def check_data_distribution(self):
        """Check data distribution across splits."""
        total = len(self.train_data) + len(self.val_data) + len(self.test_data)

        if total == 0:
            self.issues.append("No data found")
            return

        train_pct = len(self.train_data) / total * 100
        val_pct = len(self.val_data) / total * 100
        test_pct = len(self.test_data) / total * 100

        self.stats['total_examples'] = total
        self.stats['train_count'] = len(self.train_data)
        self.stats['val_count'] = len(self.val_data)
        self.stats['test_count'] = len(self.test_data)
        self.stats['train_pct'] = train_pct
        self.stats['val_pct'] = val_pct
        self.stats['test_pct'] = test_pct

        # Check if ratios are reasonable (within 5% of target)
        if abs(train_pct - 80) > 5:
            self.warnings.append(f"Train split {train_pct:.1f}% (expected ~80%)")
        if abs(val_pct - 10) > 3:
            self.warnings.append(f"Val split {val_pct:.1f}% (expected ~10%)")
        if abs(test_pct - 10) > 3:
            self.warnings.append(f"Test split {test_pct:.1f}% (expected ~10%)")

    def check_label_quality(self):
        """Check quality of labels (scores)."""
        all_data = self.train_data + self.val_data + self.test_data

        if not all_data:
            return

        # Collect all scores
        all_scores = []
        zero_label_count = 0
        out_of_range_count = 0
        out_of_range_examples = []

        for example in all_data:
            labels = example.get('labels', [])

            # Check for all zeros
            if all(score == 0 for score in labels):
                zero_label_count += 1

            # Check for out of range values
            for score in labels:
                if score is None or (isinstance(score, float) and (score != score)):  # NaN check
                    self.issues.append(f"Example {example.get('id')}: Null or NaN score found")
                elif score < 0 or score > 10:
                    out_of_range_count += 1
                    if len(out_of_range_examples) < 5:
                        out_of_range_examples.append({
                            'id': example.get('id'),
                            'title': example.get('title', '')[:50],
                            'scores': labels
                        })

            all_scores.extend(labels)

        if zero_label_count > 0:
            self.warnings.append(f"{zero_label_count} examples with all-zero scores (may indicate scoring failure)")

        if out_of_range_count > 0:
            self.issues.append(f"{out_of_range_count} scores outside valid range [0-10]")
            self.stats['out_of_range_examples'] = out_of_range_examples

        # Calculate score statistics
        if all_scores:
            self.stats['score_min'] = min(all_scores)
            self.stats['score_max'] = max(all_scores)
            self.stats['score_mean'] = statistics.mean(all_scores)
            self.stats['score_stdev'] = statistics.stdev(all_scores) if len(all_scores) > 1 else 0

            # Check for variance (not all identical)
            if self.stats['score_stdev'] < 0.1:
                self.warnings.append("Very low score variance - scores may be too uniform")

    def check_content_quality(self):
        """Check quality of content."""
        all_data = self.train_data + self.val_data + self.test_data

        empty_title_count = 0
        empty_content_count = 0
        content_lengths = []

        for example in all_data:
            title = example.get('title', '')
            content = example.get('content', '')

            if not title or not title.strip():
                empty_title_count += 1

            if not content or not content.strip():
                empty_content_count += 1
            else:
                content_lengths.append(len(content))

        if empty_title_count > 0:
            self.warnings.append(f"{empty_title_count} examples with empty titles")

        if empty_content_count > 0:
            self.issues.append(f"{empty_content_count} examples with empty content")

        if content_lengths:
            self.stats['content_length_min'] = min(content_lengths)
            self.stats['content_length_max'] = max(content_lengths)
            self.stats['content_length_mean'] = statistics.mean(content_lengths)
            self.stats['content_length_median'] = statistics.median(content_lengths)

    def check_consistency(self):
        """Check consistency across splits."""
        if not (self.train_data and self.val_data and self.test_data):
            return

        # Check dimension names consistency
        train_dims = self.train_data[0].get('dimension_names', [])
        val_dims = self.val_data[0].get('dimension_names', [])
        test_dims = self.test_data[0].get('dimension_names', [])

        if train_dims != val_dims or train_dims != test_dims:
            self.issues.append("Dimension names inconsistent across splits")

        self.stats['dimension_names'] = train_dims
        self.stats['dimension_count'] = len(train_dims)

        # If filter config provided, verify dimensions match
        if self.filter_dir:
            config_path = self.filter_dir / 'config.yaml'
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    config_dims = list(config.get('scoring', {}).get('dimensions', {}).keys())

                    if config_dims != train_dims:
                        self.issues.append(f"Dimensions don't match config: {config_dims} vs {train_dims}")

    def calculate_score_distribution(self):
        """Calculate score distribution per dimension."""
        all_data = self.train_data + self.val_data + self.test_data

        if not all_data:
            return

        dimension_names = all_data[0].get('dimension_names', [])

        # Collect scores per dimension
        dimension_scores = {dim: [] for dim in dimension_names}

        for example in all_data:
            labels = example.get('labels', [])
            for i, score in enumerate(labels):
                if i < len(dimension_names):
                    dimension_scores[dimension_names[i]].append(score)

        self.stats['dimension_stats'] = {}
        for dim, scores in dimension_scores.items():
            if scores:
                self.stats['dimension_stats'][dim] = {
                    'min': min(scores),
                    'max': max(scores),
                    'mean': statistics.mean(scores),
                    'stdev': statistics.stdev(scores) if len(scores) > 1 else 0
                }

    def run_all_checks(self):
        """Run all quality checks."""
        print(f"\n{'='*70}")
        print(f"TRAINING DATA QUALITY VALIDATION")
        print(f"Data directory: {self.data_dir}")
        print(f"{'='*70}\n")

        # Load data
        print("Loading data...")
        if not self.load_data():
            self.print_report()
            return False

        print(f"Loaded {len(self.train_data)} train, {len(self.val_data)} val, {len(self.test_data)} test examples\n")

        # Run checks
        print("Running structural integrity checks...")
        self.check_structural_integrity()

        print("Checking data distribution...")
        self.check_data_distribution()

        print("Validating label quality...")
        self.check_label_quality()

        print("Checking content quality...")
        self.check_content_quality()

        print("Verifying consistency...")
        self.check_consistency()

        print("Calculating score distributions...")
        self.calculate_score_distribution()

        # Print report
        self.print_report()

        return len(self.issues) == 0

    def print_report(self):
        """Print validation report."""
        print(f"\n{'='*70}")
        print("VALIDATION REPORT")
        print(f"{'='*70}\n")

        # Issues
        if self.issues:
            print(f"❌ ISSUES FOUND ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  - {issue}")
            print()
        else:
            print("✅ No critical issues found\n")

        # Warnings
        if self.warnings:
            print(f"⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")
            print()
        else:
            print("✅ No warnings\n")

        # Statistics
        if self.stats:
            print(f"📊 STATISTICS:\n")

            # Dataset size
            if 'total_examples' in self.stats:
                print(f"  Dataset Size:")
                print(f"    Total:  {self.stats['total_examples']}")
                print(f"    Train:  {self.stats['train_count']} ({self.stats['train_pct']:.1f}%)")
                print(f"    Val:    {self.stats['val_count']} ({self.stats['val_pct']:.1f}%)")
                print(f"    Test:   {self.stats['test_count']} ({self.stats['test_pct']:.1f}%)")
                print()

            # Dimensions
            if 'dimension_names' in self.stats:
                print(f"  Dimensions ({self.stats['dimension_count']}):")
                for dim in self.stats['dimension_names']:
                    print(f"    - {dim}")
                print()

            # Score statistics
            if 'score_min' in self.stats:
                print(f"  Overall Score Statistics:")
                print(f"    Range:  [{self.stats['score_min']:.2f} - {self.stats['score_max']:.2f}]")
                print(f"    Mean:   {self.stats['score_mean']:.2f}")
                print(f"    StdDev: {self.stats['score_stdev']:.2f}")
                print()

            # Per-dimension statistics
            if 'dimension_stats' in self.stats:
                print(f"  Per-Dimension Score Statistics:")
                for dim, stats in self.stats['dimension_stats'].items():
                    print(f"    {dim:30s}: mean={stats['mean']:.2f}, range=[{stats['min']:.1f}-{stats['max']:.1f}], std={stats['stdev']:.2f}")
                print()

            # Content statistics
            if 'content_length_mean' in self.stats:
                print(f"  Content Length (characters):")
                print(f"    Mean:   {self.stats['content_length_mean']:.0f}")
                print(f"    Median: {self.stats['content_length_median']:.0f}")
                print(f"    Range:  [{self.stats['content_length_min']} - {self.stats['content_length_max']}]")
                print()

            # Out of range examples
            if 'out_of_range_examples' in self.stats:
                print(f"  Examples with out-of-range scores:")
                for ex in self.stats['out_of_range_examples']:
                    print(f"    - {ex['id']}: {ex['title']}")
                    print(f"      Scores: {ex['scores']}")
                print()

        # Recommendation
        print(f"{'='*70}")
        if not self.issues and not self.warnings:
            print("✅ RECOMMENDATION: Data quality is excellent - proceed with training")
        elif not self.issues and self.warnings:
            print("⚠️  RECOMMENDATION: Review warnings, but data is acceptable for training")
        else:
            print("❌ RECOMMENDATION: Fix critical issues before training")
        print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description='Validate training data quality')
    parser.add_argument('--data-dir', type=str, required=True,
                       help='Path to training data directory')
    parser.add_argument('--filter', type=str,
                       help='Path to filter directory (optional, for config validation)')

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    filter_dir = Path(args.filter) if args.filter else None

    validator = TrainingDataValidator(data_dir, filter_dir)
    success = validator.run_all_checks()

    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
