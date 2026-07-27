#!/usr/bin/env python3
"""
Create a structured data archive with manifests and checksums.

Usage:
    python scripts/create_data_archive.py --output /path/to/archive
    python scripts/create_data_archive.py --output /path/to/archive --tier 1  # Production only
"""

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def get_file_hash(filepath: Path, algorithm: str = 'sha256') -> str:
    """Calculate file hash."""
    h = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def get_dir_size(path: Path) -> int:
    """Get total size of directory."""
    total = 0
    for p in path.rglob('*'):
        if p.is_file():
            total += p.stat().st_size
    return total


def count_jsonl_lines(filepath: Path) -> int:
    """Count lines in a JSONL file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except:
        return 0


def copy_with_manifest(
    src: Path,
    dst: Path,
    description: str = "",
    calculate_hashes: bool = True
) -> Dict:
    """Copy directory and generate manifest."""
    if not src.exists():
        return {"error": f"Source not found: {src}"}

    dst.mkdir(parents=True, exist_ok=True)

    manifest = {
        "source": str(src),
        "description": description,
        "copied_at": datetime.now().isoformat(),
        "files": []
    }

    for src_file in src.rglob('*'):
        if src_file.is_file():
            rel_path = src_file.relative_to(src)
            dst_file = dst / rel_path
            dst_file.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(src_file, dst_file)

            file_info = {
                "path": str(rel_path),
                "size": src_file.stat().st_size,
            }

            if calculate_hashes:
                file_info["sha256"] = get_file_hash(src_file)

            # Count articles for JSONL files
            if src_file.suffix == '.jsonl':
                file_info["lines"] = count_jsonl_lines(src_file)

            manifest["files"].append(file_info)

    manifest["total_files"] = len(manifest["files"])
    manifest["total_size"] = sum(f["size"] for f in manifest["files"])

    return manifest


def create_archive(
    project_root: Path,
    output_dir: Path,
    tier: int = 4,  # 1-4, higher includes more
    calculate_hashes: bool = True
):
    """Create the data archive."""

    archive_date = datetime.now().strftime("%Y-%m-%d")
    archive_name = f"llm-distillery-archive-{archive_date}"
    archive_path = output_dir / archive_name

    print(f"Creating archive at: {archive_path}")
    archive_path.mkdir(parents=True, exist_ok=True)

    master_manifest = {
        "archive_date": archive_date,
        "archive_version": "1.0",
        "project_root": str(project_root),
        "tier_included": tier,
        "created_at": datetime.now().isoformat(),
        "sections": {}
    }

    # Define what to archive per tier
    archive_plan = []

    # TIER 1: Production scored and models (CRITICAL)
    if tier >= 1:
        archive_plan.extend([
            # Production scored datasets
            ("1-production/scored/uplifting-v5",
             project_root / "datasets/scored/uplifting-v5/uplifting",
             "Production: 10,000 Oracle-scored articles"),
            ("1-production/scored/investment-risk-v5",
             project_root / "datasets/scored/investment-risk-v5/investment-risk",
             "Production: 10,248 Oracle-scored articles"),
            ("1-production/scored/sustainability_technology-v1",
             project_root / "datasets/scored/sustainability_technology-v1/sustainability_technology",
             "Production: 10,000 Oracle-scored articles"),
            ("1-production/scored/sustainability_technology-v2",
             project_root / "datasets/scored/sustainability_technology-v2/sustainability_technology",
             "Production: 8,000 Oracle-scored articles"),
            ("1-production/scored/cultural-discovery-v1",
             project_root / "datasets/scored/cultural-discovery-v1/cultural-discovery",
             "Production: 10,000 Oracle-scored articles"),
            ("1-production/scored/cultural-discovery-v2",
             project_root / "datasets/scored/cultural-discovery-v2/cultural-discovery",
             "Production: 2,919 Oracle-scored articles (screening filter)"),

            # Production models
            ("1-production/models/uplifting-v7",
             project_root / "filters/uplifting/v7/model",
             "Trained LoRA adapter"),
            ("1-production/models/investment-risk-v6",
             project_root / "filters/investment_risk/v6/model",
             "Trained LoRA adapter"),
            ("1-production/models/sustainability_technology-v3",
             project_root / "filters/sustainability_technology/v3/model",
             "Trained LoRA adapter"),
            ("1-production/models/cultural-discovery-v1",
             project_root / "filters/cultural-discovery/v1/model",
             "Trained model"),
            ("1-production/models/cultural-discovery-v2",
             project_root / "filters/cultural-discovery/v2/model",
             "Trained LoRA adapter"),
        ])

    # TIER 2: Training splits and calibration
    if tier >= 2:
        archive_plan.extend([
            ("1-production/training/uplifting_v5",
             project_root / "datasets/training/uplifting_v5",
             "Train/val/test splits"),
            ("1-production/training/investment_risk_v5",
             project_root / "datasets/training/investment_risk_v5",
             "Train/val/test splits"),
            ("1-production/training/sustainability_technology_v1",
             project_root / "datasets/training/sustainability_technology_v1",
             "Train/val/test splits"),
            ("1-production/training/sustainability_technology_v2",
             project_root / "datasets/training/sustainability_technology_v2",
             "Train/val/test splits"),
            ("1-production/training/cultural-discovery-v1",
             project_root / "datasets/training/cultural-discovery-v1",
             "Train/val/test splits"),
            ("1-production/training/cultural-discovery_v2",
             project_root / "datasets/training/cultural-discovery_v2",
             "Train/val/test splits"),

            ("1-production/calibration",
             project_root / "datasets/calibration",
             "Calibration and quality assurance data"),
        ])

    # TIER 3: Raw sources
    if tier >= 3:
        archive_plan.extend([
            ("2-raw-sources",
             project_root / "datasets/raw",
             "Raw source articles (Fluxus, master datasets)"),
        ])

    # TIER 4: Historical and research
    if tier >= 4:
        archive_plan.extend([
            ("3-historical/scored/uplifting-v4",
             project_root / "datasets/scored/uplifting-v4/uplifting",
             "Historical: uplifting v4 scored"),
            ("3-historical/scored/investment-risk-v4",
             project_root / "datasets/scored/investment-risk-v4/investment-risk",
             "Historical: investment-risk v4 scored"),

            ("4-research/embedding_vs_finetuning",
             project_root / "research/embedding_vs_finetuning",
             "Research: embedding comparison experiments"),
        ])

    # Execute archive plan
    for dest_rel, src_path, description in archive_plan:
        dest_path = archive_path / dest_rel
        print(f"\nArchiving: {dest_rel}")
        print(f"  Source: {src_path}")

        if src_path.exists():
            manifest = copy_with_manifest(
                src_path, dest_path, description, calculate_hashes
            )
            master_manifest["sections"][dest_rel] = manifest
            print(f"  Files: {manifest.get('total_files', 0)}")
            print(f"  Size: {manifest.get('total_size', 0) / 1024 / 1024:.1f} MB")
        else:
            print(f"  SKIPPED: Source not found")
            master_manifest["sections"][dest_rel] = {"error": "Source not found"}

    # Calculate totals
    total_files = sum(
        s.get("total_files", 0)
        for s in master_manifest["sections"].values()
        if isinstance(s, dict) and "total_files" in s
    )
    total_size = sum(
        s.get("total_size", 0)
        for s in master_manifest["sections"].values()
        if isinstance(s, dict) and "total_size" in s
    )

    master_manifest["total_files"] = total_files
    master_manifest["total_size_bytes"] = total_size
    master_manifest["total_size_human"] = f"{total_size / 1024 / 1024 / 1024:.2f} GB"

    # Write master manifest
    manifest_path = archive_path / "MANIFEST.json"
    with open(manifest_path, 'w') as f:
        json.dump(master_manifest, f, indent=2)
    print(f"\nManifest written to: {manifest_path}")

    # Copy documentation
    readme_src = project_root / "docs/DATA_ARCHIVE_PROPOSAL.md"
    if readme_src.exists():
        shutil.copy2(readme_src, archive_path / "README.md")

    # Summary
    print("\n" + "=" * 60)
    print("ARCHIVE COMPLETE")
    print("=" * 60)
    print(f"Location: {archive_path}")
    print(f"Total files: {total_files}")
    print(f"Total size: {total_size / 1024 / 1024 / 1024:.2f} GB")
    print(f"Tier: {tier}")
    print("=" * 60)

    return archive_path, master_manifest


def main():
    parser = argparse.ArgumentParser(description="Create data archive")
    parser.add_argument(
        "--output", "-o",
        type=Path,
        required=True,
        help="Output directory for archive"
    )
    parser.add_argument(
        "--tier", "-t",
        type=int,
        default=4,
        choices=[1, 2, 3, 4],
        help="Tier level (1=critical only, 4=everything)"
    )
    parser.add_argument(
        "--no-hash",
        action="store_true",
        help="Skip SHA256 calculation (faster)"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Project root directory"
    )

    args = parser.parse_args()

    create_archive(
        project_root=args.project_root.resolve(),
        output_dir=args.output.resolve(),
        tier=args.tier,
        calculate_hashes=not args.no_hash
    )


if __name__ == "__main__":
    main()
