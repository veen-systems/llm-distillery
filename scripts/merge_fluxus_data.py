#!/usr/bin/env python3
"""
Merge FluxusSource data into a master dataset for model training.

This script reads all content_items_*.jsonl files from FluxusSource,
deduplicates articles by URL, and creates a master dataset.

Usage:
    python scripts/merge_fluxus_data.py
    python scripts/merge_fluxus_data.py --max-files 50  # Limit for testing
    python scripts/merge_fluxus_data.py --output datasets/raw/training_v2.jsonl
"""

import json
import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, List
from collections import defaultdict


def find_fluxus_files(base_path: Path, max_files: int = None) -> List[Path]:
    """Find all content_items_*.jsonl files in FluxusSource."""
    print(f"Scanning {base_path}...")

    files = sorted(base_path.glob("content_items_*.jsonl"), reverse=True)

    if max_files:
        files = files[:max_files]
        print(f"Limited to {max_files} most recent files")

    print(f"Found {len(files)} files")
    return files


def load_and_deduplicate(files: List[Path]) -> tuple[List[Dict], Dict]:
    """
    Load all articles and deduplicate by URL.

    Returns:
        - List of unique articles
        - Statistics about the merge process
    """
    articles_by_url = {}  # Use URL as unique key
    stats = defaultdict(int)

    print("\nProcessing files...")
    for i, file_path in enumerate(files, 1):
        if i % 20 == 0 or i == len(files):
            print(f"  Processed {i}/{len(files)} files, {len(articles_by_url):,} unique articles so far...")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        article = json.loads(line)
                        stats['total_articles'] += 1

                        # Use URL as unique identifier
                        url = article.get('url') or article.get('link')
                        if not url:
                            stats['no_url'] += 1
                            continue

                        # Deduplicate - keep first occurrence (most recent file first)
                        if url not in articles_by_url:
                            articles_by_url[url] = article
                            stats['unique_articles'] += 1
                        else:
                            stats['duplicates'] += 1

                    except json.JSONDecodeError as e:
                        stats['json_errors'] += 1

        except Exception as e:
            stats['file_errors'] += 1
            print(f"    Error reading {file_path.name}: {e}")

    print(f"\nLoaded {len(articles_by_url):,} unique articles")

    return list(articles_by_url.values()), dict(stats)


def sort_articles_by_date(articles: List[Dict]) -> List[Dict]:
    """Sort articles by publication date (newest first)."""
    print("\nSorting articles by date...")

    def get_date(article):
        """Extract publication date from article."""
        for field in ['published', 'pubDate', 'date', 'published_date']:
            if field in article and article[field]:
                try:
                    date_str = article[field]
                    if isinstance(date_str, str):
                        if 'T' in date_str:
                            date_str = date_str.split('T')[0]
                        return date_str
                except (ValueError, TypeError, AttributeError):
                    pass
        return '9999-12-31'

    sorted_articles = sorted(articles, key=get_date, reverse=True)
    print(f"Sorted {len(sorted_articles):,} articles")

    return sorted_articles


def write_master_dataset(articles: List[Dict], output_path: Path, stats: Dict, source_path: str):
    """Write articles to master dataset file and create metadata."""
    print(f"\nWriting master dataset to {output_path}...")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for article in articles:
            f.write(json.dumps(article, ensure_ascii=False) + '\n')

    # Get file size
    file_size_mb = output_path.stat().st_size / (1024 * 1024)

    # Get date range from sorted articles
    dates = []
    for article in articles[:100] + articles[-100:]:  # Sample first and last
        for field in ['published', 'pubDate', 'date', 'published_date']:
            if field in article and article[field]:
                date_str = article[field]
                if isinstance(date_str, str) and 'T' in date_str:
                    date_str = date_str.split('T')[0]
                if date_str and date_str != '9999-12-31':
                    dates.append(date_str)
                break

    date_range = {
        'start': min(dates) if dates else 'unknown',
        'end': max(dates) if dates else 'unknown'
    }

    # Create metadata
    metadata = {
        'created_at': datetime.now().isoformat(),
        'total_articles': len(articles),
        'file_size_mb': round(file_size_mb, 2),
        'date_range': date_range,
        'merge_stats': stats,
        'source': source_path
    }

    # Write metadata
    metadata_path = output_path.with_suffix('.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\nMaster dataset created:")
    print(f"  - File: {output_path.name}")
    print(f"  - Size: {file_size_mb:.2f} MB")
    print(f"  - Articles: {len(articles):,}")
    print(f"  - Date range: {date_range['start']} to {date_range['end']}")
    print(f"  - Metadata: {metadata_path.name}")

    return metadata


def print_summary(stats: Dict, metadata: Dict):
    """Print summary statistics."""
    print("\n" + "="*60)
    print("MERGE SUMMARY")
    print("="*60)
    print(f"Total articles processed:  {stats['total_articles']:,}")
    print(f"Unique articles:           {stats['unique_articles']:,}")
    print(f"Duplicates removed:        {stats['duplicates']:,}")
    print(f"Articles without URL:      {stats.get('no_url', 0):,}")
    print(f"JSON errors:               {stats.get('json_errors', 0):,}")
    print(f"File errors:               {stats.get('file_errors', 0):,}")
    if stats['total_articles'] > 0:
        print(f"\nDeduplication rate: {stats['duplicates'] / stats['total_articles'] * 100:.1f}%")
    print(f"Final dataset size: {metadata['file_size_mb']:.2f} MB")
    print("="*60)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Merge FluxusSource data into a master dataset for training'
    )
    parser.add_argument(
        '--source',
        type=Path,
        default=Path("I:/Mijn Drive/FluxusSource/data"),
        help='Path to FluxusSource data directory'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=None,
        help='Output file path (default: datasets/raw/fluxus_YYYYMMDD.jsonl)'
    )
    parser.add_argument(
        '--max-files',
        type=int,
        default=None,
        help='Maximum number of files to process (for testing)'
    )

    args = parser.parse_args()

    print("="*60)
    print("FluxusSource Data Merge Script")
    print("="*60)

    # Check source path
    if not args.source.exists():
        print(f"Error: Source path not found: {args.source}")
        print("\nNote: This script requires access to Google Drive.")
        print("Make sure the drive is mounted at I:/Mijn Drive/")
        return 1

    # Determine output path
    if args.output:
        output_file = args.output
    else:
        today = datetime.now().strftime("%Y%m%d")
        output_file = Path("datasets/raw") / f"fluxus_{today}.jsonl"

    # Check if output already exists
    if output_file.exists():
        response = input(f"\nWARNING: {output_file.name} already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return 0

    # Step 1: Find all FluxusSource files
    files = find_fluxus_files(args.source, args.max_files)

    if not files:
        print("Error: No FluxusSource files found!")
        return 1

    # Step 2: Load and deduplicate
    articles, stats = load_and_deduplicate(files)

    if not articles:
        print("Error: No articles loaded!")
        return 1

    # Step 3: Sort by date
    sorted_articles = sort_articles_by_date(articles)

    # Step 4: Write master dataset
    metadata = write_master_dataset(sorted_articles, output_file, stats, str(args.source))

    # Step 5: Print summary
    print_summary(stats, metadata)

    print(f"\nDone! Master dataset ready at: {output_file}")
    print(f"\nNext steps:")
    print(f"  1. Copy to llm-distiller: scp {output_file} llm-distiller:~/llm-distillery/datasets/raw/")
    print(f"  2. Run batch scoring with v2 oracle:")
    print(f"     python -m ground_truth.batch_scorer \\")
    print(f"       --filter filters/sustainability_technology/v3 \\")
    print(f"       --source datasets/raw/{output_file.name} \\")
    print(f"       --output-dir datasets/scored/sustainability_technology_v2 \\")
    print(f"       --llm gemini-flash \\")
    print(f"       --target-scored 5000 \\")
    print(f"       --random-sample")

    return 0


if __name__ == "__main__":
    exit(main())
