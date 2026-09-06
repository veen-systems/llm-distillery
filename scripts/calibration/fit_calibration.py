"""
Fit post-hoc score calibration (isotonic regression) for any production filter.

Runs the filter's model on the validation set, collects raw (unclamped)
predictions, and fits per-dimension isotonic regression from student -> oracle.
Saves calibration.json to the filter directory.

Usage:
    PYTHONPATH=. python scripts/calibration/fit_calibration.py \
        --filter filters/uplifting/v6 \
        --data-dir datasets/training/uplifting_v6

    # Also evaluate on test set (unbiased):
    PYTHONPATH=. python scripts/calibration/fit_calibration.py \
        --filter filters/uplifting/v6 \
        --data-dir datasets/training/uplifting_v6 \
        --test-data datasets/training/uplifting_v6/test.jsonl
"""

import argparse
import importlib
import json
import logging
import sys
from pathlib import Path

import numpy as np
import torch
import yaml
from transformers import AutoTokenizer

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Suppress the "should TRAIN this model" warning
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)


def score_scale_factor_decision(filter_dir: Path, no_config_update: bool,
                                force_config_update: bool):
    """Decide whether to write `score_scale_factor` into a filter's config.yaml.

    Returns (write: bool, reason: str). Pure apart from one `.exists()`, so the
    behaviour can be proven in both directions without loading a model --
    `tests/unit/test_fit_calibration_config_write.py`.

    ⛔ WHY THE DEFAULT REFUSES WHEN normalization.json IS ABSENT. `score_scale_factor` is
    superseded by percentile normalization (ADR-014). A factor != 1.0 on a filter with no
    `normalization.json` stretches every NORMALIZED score -- which is what feeds
    cross-filter ranking and NexusMind's `pipeline.enrichment.min_score: 4.0`. Visibility
    is decided on the RAW score (NM#280), so the op-point does not move and the change has
    no symptom. ⚠️ Worse, second-order: NexusMind's `_check_required_artifacts` treats the
    mere PRESENCE of `score_scale_factor` in `scoring` as "uses scale factor" and then
    stops warning about the missing `normalization.json` -- so the write also silences the
    one guard that would flag the absent Phase E artifact.

    Filters that already ship a `normalization.json` are unaffected: they still get the
    write, because there the factor is inert by construction.
    """
    if no_config_update:
        return False, "--no-config-update given"
    if (filter_dir / "normalization.json").exists():
        return True, "normalization.json present, factor is inert"
    if force_config_update:
        return True, "--force-config-update overrides the missing normalization.json"
    return False, ("no normalization.json -- a factor != 1.0 would stretch every "
                   "normalized score (ADR-014, FILTER_PLAYBOOK section 8)")


def load_filter_config(filter_dir: Path) -> dict:
    """Load config.yaml from a filter directory."""
    config_path = filter_dir / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"No config.yaml found in {filter_dir}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_dimension_names(config: dict) -> list:
    """Extract dimension names from config."""
    scoring = config.get("scoring", {})
    dims = scoring.get("dimensions", {})
    return list(dims.keys())


def load_data(path: Path) -> list:
    """Load a JSONL file."""
    articles = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                articles.append(json.loads(line))
    return articles


def load_scorer(filter_dir: Path):
    """
    Dynamically load the scorer from a filter directory.

    """
    filter_dir = filter_dir.resolve()
    parts = filter_dir.parts

    # Find the filter name and version from path: filters/<name>/<version>/
    # Walk backwards to find "filters" marker
    try:
        filters_idx = list(parts).index("filters")
    except ValueError:
        raise ValueError(f"Expected 'filters' in path: {filter_dir}")

    filter_name = parts[filters_idx + 1]
    version_dir = parts[filters_idx + 2]

    # Build module path: filters.<name>.<version>.inference
    module_path = f"filters.{filter_name}.{version_dir}.inference"
    module = importlib.import_module(module_path)

    # Find the scorer class (convention: *Scorer, not *Hub, not *Hybrid)
    scorer_cls = None
    for name in dir(module):
        obj = getattr(module, name)
        if (
            isinstance(obj, type)
            and name.endswith("Scorer")
            and "Hub" not in name
            and "Hybrid" not in name
            and "Base" not in name
        ):
            scorer_cls = obj
            break

    if scorer_cls is None:
        raise ValueError(f"No scorer class found in {module_path}")

    logger.info(f"Loading scorer: {scorer_cls.__name__} from {module_path}")
    return scorer_cls(use_prefilter=False)


def run_inference_raw(scorer, articles, dimension_names, batch_size=16):
    """
    Run inference and collect raw (unclamped) logits.

    Bypasses _process_raw_scores to get the raw model output before
    clamping or calibration.
    """
    model = scorer.model
    tokenizer = scorer.tokenizer
    device = scorer.device
    max_len = scorer.MAX_TOKEN_LENGTH

    # ⛔ READ THE DEVICE OFF THE LOADED MODEL, NOT OFF scorer.device. #146: a "CPU"
    # arm once read 2.37 ms against GPU's 2.34 (true CPU 42.41, 18x) because a cache
    # keyed on the model name ignored the device it was asked for. A calibration
    # fitted on a different device from the one that serves is a silent mismatch, and
    # the fit is the artifact the op-point is defined on — so print both and let the
    # log carry it.
    try:
        param_device = str(next(model.parameters()).device)
    except StopIteration:                     # a model with no parameters cannot serve
        param_device = "unknown (model has no parameters)"
    print(f"  device: declared={device} parameters={param_device}, batch_size={batch_size}")

    all_raw_scores = []

    # Check if head+tail preprocessing is enabled
    use_head_tail = getattr(scorer, "use_head_tail", False)

    for batch_start in range(0, len(articles), batch_size):
        batch = articles[batch_start : batch_start + batch_size]

        texts = [f"{a['title']}\n\n{a['content']}" for a in batch]

        if use_head_tail:
            from filters.common.text_preprocessing import extract_head_tail

            texts = [
                extract_head_tail(
                    t,
                    tokenizer,
                    scorer.head_tokens,
                    scorer.tail_tokens,
                    scorer.head_tail_separator,
                )
                for t in texts
            ]

        inputs = tokenizer(
            texts,
            max_length=max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            batch_scores = outputs.logits.float().cpu().numpy()

        all_raw_scores.append(batch_scores)

        if (batch_start // batch_size + 1) % 10 == 0:
            done = min(batch_start + batch_size, len(articles))
            logger.info(f"  Inference progress: {done}/{len(articles)}")

    return np.concatenate(all_raw_scores, axis=0)


def compute_tier_distribution(scores, weights, dimension_names, tier_thresholds):
    """Compute tier distribution from dimension scores.

    Reads tier names and thresholds from the filter's config.yaml instead of
    hardcoding a 3-tier scheme. Supports any number of tiers.
    """
    # Sort tiers by threshold descending for correct assignment
    sorted_tiers = sorted(tier_thresholds.items(), key=lambda x: x[1], reverse=True)
    tiers = {name: 0 for name, _ in sorted_tiers}

    for i in range(len(scores)):
        weighted_avg = sum(
            float(scores[i, j]) * weights.get(dim, 0)
            for j, dim in enumerate(dimension_names)
        )
        assigned = False
        for tier_name, threshold in sorted_tiers:
            if weighted_avg >= threshold:
                tiers[tier_name] += 1
                assigned = True
                break
        if not assigned:
            # Assign to lowest tier
            tiers[sorted_tiers[-1][0]] += 1

    return tiers


def print_report(cal_data, oracle_scores, student_scores, dimension_names, weights, tier_thresholds, label=""):
    """Print calibration report."""
    dims = cal_data["dimensions"]
    stats = cal_data["stats"]

    header = f"Calibration Report{f' ({label})' if label else ''}"
    print(f"\n{'=' * 60}")
    print(f"  {header}")
    print(f"{'=' * 60}")
    print(f"  Filter: {cal_data['filter_name']} v{cal_data['filter_version']}")
    print(f"  Samples: {cal_data['n_samples']}")
    print(f"  Overall MAE: {stats['mae_before']:.4f} -> {stats['mae_after']:.4f}")
    improvement = stats["mae_before"] - stats["mae_after"]
    pct = (improvement / stats["mae_before"]) * 100 if stats["mae_before"] > 0 else 0
    print(f"  Improvement: {improvement:+.4f} ({pct:+.1f}%)")

    print(f"\n  {'Dimension':<28} {'MAE Before':>10} {'MAE After':>10} {'Change':>10}")
    print(f"  {'-' * 58}")
    for dim in dimension_names:
        ds = stats["per_dimension"][dim]
        change = ds["mae_before"] - ds["mae_after"]
        print(f"  {dim:<28} {ds['mae_before']:>10.4f} {ds['mae_after']:>10.4f} {change:>+10.4f}")

    print(f"\n  Score ranges:")
    print(f"  {'Dimension':<28} {'Student':>16} {'Calibrated':>16} {'Oracle':>16}")
    print(f"  {'-' * 76}")
    for dim in dimension_names:
        ds = stats["per_dimension"][dim]
        student_range = f"[{ds['student_min']:.1f}, {ds['student_max']:.1f}]"
        cal_range = f"[{ds['calibrated_min']:.1f}, {ds['calibrated_max']:.1f}]"
        oracle_range = f"[{ds['oracle_min']:.1f}, {ds['oracle_max']:.1f}]"
        print(f"  {dim:<28} {student_range:>16} {cal_range:>16} {oracle_range:>16}")

    # Tier distribution comparison
    n = oracle_scores.shape[0]

    # Oracle tiers
    oracle_tiers = compute_tier_distribution(oracle_scores, weights, dimension_names, tier_thresholds)

    # Student tiers (clamped)
    student_clamped = np.clip(student_scores, 0, 10)
    student_tiers = compute_tier_distribution(student_clamped, weights, dimension_names, tier_thresholds)

    # Calibrated tiers
    calibrated = student_scores.copy()
    for i, dim in enumerate(dimension_names):
        if dim in dims:
            bp = dims[dim]
            calibrated[:, i] = np.interp(student_scores[:, i], bp["x"], bp["y"])
    calibrated_clamped = np.clip(calibrated, 0, 10)
    cal_tiers = compute_tier_distribution(calibrated_clamped, weights, dimension_names, tier_thresholds)

    print(f"\n  Tier distribution:")
    # Use sorted thresholds (descending) for display order
    sorted_tier_names = sorted(tier_thresholds.keys(), key=lambda t: tier_thresholds[t], reverse=True)
    print(f"  {'Tier':<20} {'Oracle':>10} {'Student':>10} {'Calibrated':>10}")
    print(f"  {'-' * 50}")
    for tier in sorted_tier_names:
        print(f"  {tier:<20} {oracle_tiers.get(tier, 0):>10} {student_tiers.get(tier, 0):>10} {cal_tiers.get(tier, 0):>10}")

    print(f"{'=' * 60}")


def evaluate_on_data(cal_data, data_path, scorer, dimension_names, weights, tier_thresholds, label):
    """Evaluate calibration on an arbitrary data split."""
    articles = load_data(data_path)
    logger.info(f"Running inference on {label} set ({len(articles)} articles)...")

    student_scores = run_inference_raw(scorer, articles, dimension_names)
    oracle_scores = np.array([a["labels"] for a in articles], dtype=np.float32)

    # Compute calibrated MAE
    dims = cal_data["dimensions"]
    calibrated = student_scores.copy()
    for i, dim in enumerate(dimension_names):
        if dim in dims:
            bp = dims[dim]
            calibrated[:, i] = np.interp(student_scores[:, i], bp["x"], bp["y"])

    mae_before = float(np.mean(np.abs(oracle_scores - student_scores)))
    mae_after = float(np.mean(np.abs(oracle_scores - calibrated)))

    # Build a stats dict for the report
    per_dim_stats = {}
    for i, dim in enumerate(dimension_names):
        oracle_col = oracle_scores[:, i]
        student_col = student_scores[:, i]
        cal_col = calibrated[:, i]
        per_dim_stats[dim] = {
            "mae_before": round(float(np.mean(np.abs(oracle_col - student_col))), 4),
            "mae_after": round(float(np.mean(np.abs(oracle_col - cal_col))), 4),
            "student_min": round(float(student_col.min()), 4),
            "student_max": round(float(student_col.max()), 4),
            "student_std": round(float(student_col.std()), 4),
            "calibrated_min": round(float(cal_col.min()), 4),
            "calibrated_max": round(float(cal_col.max()), 4),
            "calibrated_std": round(float(cal_col.std()), 4),
            "oracle_min": round(float(oracle_col.min()), 4),
            "oracle_max": round(float(oracle_col.max()), 4),
            "oracle_std": round(float(oracle_col.std()), 4),
            "n_breakpoints": len(dims.get(dim, {}).get("x", [])),
        }

    eval_data = dict(cal_data)
    eval_data["n_samples"] = len(articles)
    eval_data["stats"] = {
        "mae_before": round(mae_before, 4),
        "mae_after": round(mae_after, 4),
        "per_dimension": per_dim_stats,
    }

    print_report(eval_data, oracle_scores, student_scores, dimension_names, weights, tier_thresholds, label=label)


def _update_score_scale_factor(config_path: Path, factor: float, weighted_max: float):
    """Insert or update score_scale_factor in config.yaml, preserving comments."""
    import re

    text = config_path.read_text(encoding="utf-8")
    factor_line = f"  score_scale_factor: {factor}  # 10.0 / {weighted_max:.2f} (calibrated max)\n"

    # Replace existing score_scale_factor line
    pattern = r"^(\s*)score_scale_factor:.*$"
    if re.search(pattern, text, re.MULTILINE):
        text = re.sub(pattern, factor_line.rstrip(), text, flags=re.MULTILINE)
    else:
        # Insert after "scoring:" line
        scoring_match = re.search(r"^scoring:\s*$", text, re.MULTILINE)
        if scoring_match:
            insert_pos = scoring_match.end()
            text = text[:insert_pos] + "\n" + factor_line + text[insert_pos:]
        else:
            logger.warning("Could not find 'scoring:' section in config.yaml, skipping")
            return

    config_path.write_text(text, encoding="utf-8")
    logger.info(f"Updated {config_path} with score_scale_factor={factor}")


def main():
    parser = argparse.ArgumentParser(
        description="Fit post-hoc score calibration (isotonic regression) for a production filter"
    )
    parser.add_argument(
        "--filter", type=Path, required=True,
        help="Path to filter directory (e.g., filters/uplifting/v6)",
    )
    parser.add_argument(
        "--data-dir", type=Path, required=True,
        help="Path to training data directory containing val.jsonl",
    )
    parser.add_argument(
        "--test-data", type=Path, default=None,
        help="Optional path to test.jsonl for unbiased evaluation",
    )
    parser.add_argument(
        "--batch-size", type=int, default=16,
        help="Batch size for inference (default: 16)",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Output path for calibration.json (default: <filter-dir>/calibration.json)",
    )
    parser.add_argument(
        "--force-config-update", action="store_true",
        help="Write score_scale_factor into config.yaml even when the filter has NO "
             "normalization.json. Added 2026-09-04 alongside the default refusal: that "
             "combination silently stretches every normalized score and additionally "
             "silences NexusMind's missing-normalization warning. Filters that already "
             "have a normalization.json are unaffected and still get the write.",
    )
    parser.add_argument(
        "--no-config-update", action="store_true",
        help="Do NOT write score_scale_factor back into the filter's config.yaml. "
             "Added 2026-09-04: this script's default is to compute 10.0/weighted_max "
             "and edit config.yaml as a side effect, but score_scale_factor is "
             "SUPERSEDED by percentile normalization (ADR-014) and a filter that "
             "ships a factor != 1.0 with no normalization.json silently stretches "
             "every score and defeats the gatekeeper design (FILTER_PLAYBOOK section 8). "
             "The computed value is still logged, so nothing is hidden -- it is just "
             "not applied.",
    )
    args = parser.parse_args()

    filter_dir = args.filter.resolve()
    data_dir = args.data_dir.resolve()
    val_path = data_dir / "val.jsonl"

    if not val_path.exists():
        print(f"ERROR: val.jsonl not found at {val_path}", file=sys.stderr)
        sys.exit(1)

    # Load config
    config = load_filter_config(filter_dir)
    dimension_names = get_dimension_names(config)
    filter_name = config.get("filter", {}).get("name", "")
    filter_version = config.get("filter", {}).get("version", "")

    # Extract weights and tier thresholds
    scoring = config.get("scoring", {})
    weights = {}
    for dim_name, dim_config in scoring.get("dimensions", {}).items():
        weights[dim_name] = dim_config.get("weight", 0)

    tier_thresholds = {}
    tiers_config = scoring.get("tiers", {})
    for tier_name, tier_config in tiers_config.items():
        tier_thresholds[tier_name] = tier_config.get("threshold", 0)
    # Fallback for config formats using tier_thresholds key
    if not tier_thresholds:
        for item in scoring.get("tier_thresholds", []):
            if isinstance(item, dict):
                tier_thresholds[item["name"]] = item["threshold"]

    logger.info(f"Filter: {filter_name} v{filter_version}")
    logger.info(f"Dimensions: {dimension_names}")

    # Load scorer
    logger.info("Loading scorer...")
    scorer = load_scorer(filter_dir)

    # Load validation data
    val_articles = load_data(val_path)
    logger.info(f"Loaded {len(val_articles)} validation articles")

    # Verify dimension alignment
    sample = val_articles[0]
    if "dimension_names" in sample:
        data_dims = sample["dimension_names"]
        if data_dims != dimension_names:
            logger.warning(
                f"Dimension order mismatch!\n"
                f"  Config: {dimension_names}\n"
                f"  Data:   {data_dims}\n"
                f"Using data dimension order."
            )
            dimension_names = data_dims

    # Run inference to collect raw scores
    logger.info("Running inference on validation set...")
    student_scores = run_inference_raw(
        scorer, val_articles, dimension_names, batch_size=args.batch_size
    )

    # Collect oracle labels
    oracle_scores = np.array(
        [a["labels"] for a in val_articles], dtype=np.float32
    )

    if oracle_scores.ndim != 2 or oracle_scores.shape[1] != len(dimension_names):
        print(
            f"ERROR: Expected oracle_scores shape (n, {len(dimension_names)}), "
            f"got {oracle_scores.shape}. Check that val.jsonl matches this filter's dimensions.",
            file=sys.stderr,
        )
        sys.exit(1)

    logger.info(f"Student scores shape: {student_scores.shape}")
    logger.info(f"Oracle scores shape: {oracle_scores.shape}")

    # Fit calibration
    logger.info("Fitting isotonic regression calibration...")
    from filters.common.score_calibration import fit_calibration, save_calibration

    cal_data = fit_calibration(
        oracle_scores=oracle_scores,
        student_scores=student_scores,
        dimension_names=dimension_names,
        filter_name=filter_name,
        filter_version=filter_version,
    )

    # Save
    output_path = args.output or (filter_dir / "calibration.json")
    save_calibration(cal_data, str(output_path))

    # Compute and write score_scale_factor to config.yaml
    cal_stats = cal_data.get("stats", {}).get("per_dimension", {})
    if cal_stats and weights:
        weighted_max = sum(
            weights.get(dim, 0) * cal_stats[dim]["calibrated_max"]
            for dim in dimension_names
            if dim in cal_stats
        )
        if weighted_max > 0:
            score_scale_factor = round(10.0 / weighted_max, 4)
            logger.info(
                f"score_scale_factor: {score_scale_factor} "
                f"(10.0 / {weighted_max:.2f} theoretical max from calibration)"
            )

            write, reason = score_scale_factor_decision(
                filter_dir, args.no_config_update, args.force_config_update
            )
            if write:
                logger.info(f"writing score_scale_factor ({reason})")
                _update_score_scale_factor(filter_dir / "config.yaml",
                                           score_scale_factor, weighted_max)
            else:
                logger.warning(
                    "config.yaml NOT modified (%s). The filter keeps its existing "
                    "score_scale_factor; %s is recorded in this log only.",
                    reason, score_scale_factor,
                )

    # Print report
    print_report(cal_data, oracle_scores, student_scores, dimension_names, weights, tier_thresholds, label="val")

    # Optionally evaluate on test set
    if args.test_data:
        test_path = args.test_data.resolve()
        if not test_path.exists():
            print(f"WARNING: test data not found at {test_path}", file=sys.stderr)
        else:
            evaluate_on_data(
                cal_data, test_path, scorer, dimension_names, weights, tier_thresholds, label="test"
            )


if __name__ == "__main__":
    main()
