"""
Fit cross-filter percentile normalization from production data (ADR-014).

Reads raw_weighted_average scores from NexusMind filtered output, filters
by score threshold (default >= 4.0, the MEDIUM threshold), fits a percentile
CDF, and saves normalization.json to the filter directory.

Usage:
    # From local JSONL files (e.g., after scp from sadalsuud)
    PYTHONPATH=. python scripts/normalization/fit_normalization.py \
        --filter filters/nature_recovery/v1 \
        --data-dir /path/to/filtered/nature_recovery

    # From sadalsuud directly via SSH
    PYTHONPATH=. python scripts/normalization/fit_normalization.py \
        --filter filters/nature_recovery/v1 \
        --ssh sadalsuud \
        --remote-dir /home/jeroen/local_dev/NexusMind/data/filtered/nature_recovery
"""

import argparse
import json
import logging
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from filters.common.score_normalization import fit_normalization, save_normalization

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_weighted_averages_local(
    data_dir: Path,
    filter_name: str,
    min_score: float = 4.0,
    filter_version: str | None = None,
) -> list:
    """Load weighted averages from local filtered JSONL files."""
    was = []
    n_raw = 0
    n_fallback = 0
    n_below_threshold = 0
    n_wrong_version = 0

    # Read flat JSONL files (NexusMind#144: flat output, no tier subdirs)
    jsonl_files = sorted(data_dir.glob("filtered_*.jsonl"))

    for jsonl_file in jsonl_files:
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    article = json.loads(line)
                    attrs = article.get("nexus_mind_attributes", {})
                    for key, analysis in attrs.items():
                        if isinstance(analysis, dict) and "weighted_average" in analysis:
                            # Production writes the version as "version" inside the
                            # per-filter nexus_mind_attributes block (e.g. {"version":"5.0"}).
                            # Older code/data used "filter_version"; accept either.
                            # str()-compare so "5.0" (arg) matches "5.0" (data). Bug fixed
                            # 2026-07-10: was reading only "filter_version", excluding ALL
                            # articles when --filter-version was passed (production uses "version").
                            art_ver = analysis.get("version", analysis.get("filter_version"))
                            if filter_version is not None and str(art_ver) != str(filter_version):
                                n_wrong_version += 1
                                continue
                            # Use raw_weighted_average to avoid double-normalization
                            raw = analysis.get("raw_weighted_average")
                            wa = raw if raw is not None else analysis["weighted_average"]
                            if wa < min_score:
                                n_below_threshold += 1
                                continue
                            if raw is not None:
                                n_raw += 1
                            else:
                                n_fallback += 1
                            was.append(wa)
                except (json.JSONDecodeError, KeyError):
                    continue

    if n_wrong_version > 0:
        logger.info(f"Excluded {n_wrong_version} articles not matching filter_version={filter_version}")
    if n_below_threshold > 0:
        logger.info(f"Excluded {n_below_threshold} articles below min_score={min_score}")
    if n_fallback > 0 and n_raw > 0:
        logger.warning(
            f"Mixed fields: {n_raw} articles used raw_weighted_average, "
            f"{n_fallback} used weighted_average (possibly normalized). "
            f"CDF may blend raw and normalized scores."
        )
    elif n_fallback > 0:
        logger.warning(
            f"raw_weighted_average not found in any article — using weighted_average "
            f"for all {n_fallback} articles. Check for double-normalization risk."
        )
    else:
        logger.info(f"Using raw_weighted_average for all {n_raw} articles")

    return was


def load_weighted_averages_ssh(
    ssh_host: str,
    remote_dir: str,
    min_score: float = 4.0,
    filter_version: str | None = None,
) -> list:
    """Load weighted averages from a remote host via SSH."""
    # Write extraction script to temp file, scp to remote, execute, retrieve results
    script_content = """import json, glob, os, sys
remote_dir = sys.argv[1]
min_score = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
filter_version = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None
was = []
n_raw = 0
n_fallback = 0
n_below = 0
n_wrong_version = 0
# Read flat JSONL files (NexusMind#144: flat output, no tier subdirs)
files = sorted(glob.glob(os.path.join(remote_dir, "filtered_*.jsonl")))
for fp in files:
    with open(fp) as f:
        for line in f:
            try:
                d = json.loads(line)
                attrs = d.get("nexus_mind_attributes", {})
                for k, v in attrs.items():
                    if isinstance(v, dict) and "weighted_average" in v:
                        if filter_version is not None and str(v.get("version", v.get("filter_version"))) != str(filter_version):
                            n_wrong_version += 1
                            continue
                        raw = v.get("raw_weighted_average")
                        wa = raw if raw is not None else v["weighted_average"]
                        if wa < min_score:
                            n_below += 1
                            continue
                        if raw is not None:
                            n_raw += 1
                        else:
                            n_fallback += 1
                        was.append(wa)
            except Exception:
                pass
for w in was:
    print(w)
print("META:raw=%d,fallback=%d,below=%d,wrong_version=%d" % (n_raw, n_fallback, n_below, n_wrong_version), file=sys.stderr)
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(script_content)
        local_script = f.name

    remote_script = "/tmp/_extract_wa.py"
    try:
        subprocess.run(["scp", local_script, f"{ssh_host}:{remote_script}"],
                       capture_output=True, timeout=30, check=True)
        ssh_args = ["ssh", ssh_host, "python3", remote_script, remote_dir, str(min_score)]
        if filter_version is not None:
            ssh_args.append(filter_version)
        result = subprocess.run(
            ssh_args,
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            logger.error(f"SSH command failed: {result.stderr}")
            sys.exit(1)
    finally:
        Path(local_script).unlink(missing_ok=True)
        subprocess.run(["ssh", ssh_host, "rm", "-f", remote_script],
                       capture_output=True, timeout=15)

    was = []
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            was.append(float(line))

    # Parse field-usage metadata from remote script stderr
    import re
    meta_match = re.search(r"META:raw=(\d+),fallback=(\d+),below=(\d+),wrong_version=(\d+)", result.stderr or "")
    if meta_match:
        n_raw = int(meta_match.group(1))
        n_fallback = int(meta_match.group(2))
        n_below = int(meta_match.group(3))
        n_wrong_version = int(meta_match.group(4))
        if n_wrong_version > 0:
            logger.info(f"Excluded {n_wrong_version} articles not matching filter_version={filter_version}")
        if n_below > 0:
            logger.info(f"Excluded {n_below} articles below min_score={min_score}")
        if n_fallback > 0 and n_raw > 0:
            logger.warning(
                f"Mixed fields: {n_raw} articles used raw_weighted_average, "
                f"{n_fallback} used weighted_average (possibly normalized). "
                f"CDF may blend raw and normalized scores."
            )
        elif n_fallback > 0:
            logger.warning(
                f"raw_weighted_average not found in any article — using weighted_average "
                f"for all {n_fallback} articles. Check for double-normalization risk."
            )
        else:
            logger.info(f"Using raw_weighted_average for all {n_raw} articles")

    return was


def main():
    parser = argparse.ArgumentParser(
        description="Fit cross-filter percentile normalization from production data (ADR-014)"
    )
    parser.add_argument(
        "--filter", type=Path, required=True,
        help="Path to filter directory (e.g., filters/nature_recovery/v1)",
    )
    parser.add_argument(
        "--data-dir", type=Path, default=None,
        help="Local directory containing flat filtered_*.jsonl files",
    )
    parser.add_argument(
        "--ssh", type=str, default=None,
        help="SSH host to read production data from (e.g., sadalsuud)",
    )
    parser.add_argument(
        "--remote-dir", type=str, default=None,
        help="Remote directory on SSH host (e.g., /home/jeroen/local_dev/NexusMind/data/filtered/nature_recovery)",
    )
    parser.add_argument(
        "--n-bins", type=int, default=200,
        help="Number of breakpoints in the lookup table (default: 200)",
    )
    parser.add_argument(
        "--min-score", type=float, default=4.0,
        help="Minimum raw_weighted_average to include (default: 4.0, the MEDIUM threshold). "
             "Use 0.0 to include all scored articles.",
    )
    parser.add_argument(
        "--filter-version", type=str, default=None,
        help="Only include articles where nexus_mind_attributes.<filter>.filter_version "
             "matches this string (e.g., '2.0'). Required when production has v1 leftovers "
             "mixed with the current version's output.",
    )
    args = parser.parse_args()

    # Validate inputs
    if not args.filter.is_dir():
        logger.error(f"Filter directory not found: {args.filter}")
        sys.exit(1)

    if args.ssh and not args.remote_dir:
        logger.error("--remote-dir is required when using --ssh")
        sys.exit(1)

    if not args.ssh and not args.data_dir:
        logger.error("Either --data-dir or --ssh + --remote-dir is required")
        sys.exit(1)

    # Load config for filter name/version
    config_path = args.filter / "config.yaml"
    filter_name = args.filter.parent.name
    filter_version = args.filter.name

    if config_path.exists():
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        filter_info = config.get("filter", {})
        filter_name = filter_info.get("name", filter_name)
        filter_version = str(filter_info.get("version", filter_version))

    logger.info(f"Filter: {filter_name} v{filter_version}")

    # Load production weighted averages
    score_label = f"raw_weighted_average >= {args.min_score}"
    version_label = f", filter_version={args.filter_version}" if args.filter_version else ""
    if args.ssh:
        logger.info(f"Loading production data ({score_label}{version_label}) from {args.ssh}:{args.remote_dir}")
        source_desc = f"production {score_label}{version_label} from {args.ssh}:{args.remote_dir}"
        was = load_weighted_averages_ssh(
            args.ssh, args.remote_dir, min_score=args.min_score, filter_version=args.filter_version,
        )
    else:
        logger.info(f"Loading production data ({score_label}{version_label}) from {args.data_dir}")
        source_desc = f"production {score_label}{version_label} from {args.data_dir}"
        was = load_weighted_averages_local(
            args.data_dir, filter_name, min_score=args.min_score, filter_version=args.filter_version,
        )

    if len(was) < 10:
        logger.error(f"Only {len(was)} weighted averages found — need at least 10")
        sys.exit(1)

    logger.info(f"Loaded {len(was)} weighted averages")

    # Fit normalization
    wa_array = np.array(was, dtype=np.float64)
    norm_data = fit_normalization(
        wa_array,
        filter_name=filter_name,
        filter_version=filter_version,
        source_description=source_desc,
        n_bins=args.n_bins,
    )

    # Report
    stats = norm_data["stats"]
    pcts = stats["percentiles"]
    logger.info(f"\nNormalization fitted on {norm_data['n_articles']} articles")
    logger.info(f"  Raw WA range: {stats['raw_min']:.2f} - {stats['raw_max']:.2f}")
    logger.info(f"  Raw WA mean:  {stats['raw_mean']:.2f} (std {stats['raw_std']:.2f})")
    logger.info(f"  Percentiles (raw):  p25={pcts['p25']:.2f}  p50={pcts['p50']:.2f}  "
                f"p75={pcts['p75']:.2f}  p90={pcts['p90']:.2f}  p95={pcts['p95']:.2f}")

    # Show what key raw scores map to after normalization
    logger.info(f"\n  Sample mappings (raw -> normalized):")
    for raw in [4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 8.0]:
        norm = float(np.interp(raw, norm_data["x"], norm_data["y"]))
        logger.info(f"    {raw:.1f} -> {norm:.2f}")

    # Save
    output_path = args.filter / "normalization.json"
    save_normalization(norm_data, str(output_path))
    logger.info(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
