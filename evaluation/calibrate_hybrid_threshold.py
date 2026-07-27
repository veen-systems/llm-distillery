"""
Calibrate Stage 1 threshold for the hybrid inference pipeline.

Sweeps thresholds from 1.0 to 5.0 and measures the false negative rate:
articles that the fine-tuned model would classify as MEDIUM or HIGH,
but Stage 1 embedding probe classifies as LOW (below threshold).

Target: <2% false negative rate on MEDIUM+ articles.

Usage:
    python evaluation/calibrate_hybrid_threshold.py \
        --filter uplifting \
        --version v7 \
        --val-data datasets/training/uplifting_v7/val.jsonl \
        --probe-path filters/uplifting/v7/probe/embedding_probe.pkl

    # With ground truth labels (oracle scores) for more accurate calibration:
    python evaluation/calibrate_hybrid_threshold.py \
        --filter uplifting \
        --version v7 \
        --val-data datasets/training/uplifting_v7/val.jsonl \
        --probe-path filters/uplifting/v7/probe/embedding_probe.pkl \
        --use-ground-truth
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_articles(path: Path) -> List[Dict]:
    """Load articles from JSONL file."""
    articles = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                articles.append(json.loads(line))
    return articles


def load_filter_config(filter_name: str, version: str) -> Dict:
    """Load filter config.yaml to get dimension names, weights, and tier thresholds."""
    config_path = Path(f"filters/{filter_name}/{version}/config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def extract_dimension_info(config: Dict) -> Tuple[List[str], Dict[str, float], float]:
    """Extract dimension names, weights, and MEDIUM tier threshold from config.

    Supports both config formats:
    - `tiers:` with simple threshold values (uplifting, cultural-discovery)
    - `tier_thresholds:` with threshold or min_score (sustainability_technology)
    - `tier_thresholds:` with compound conditions (investment-risk)
    """
    dimensions = config["scoring"]["dimensions"]
    dim_names = list(dimensions.keys())
    dim_weights = {name: dim["weight"] for name, dim in dimensions.items()}

    # Support both config key formats
    tiers = config["scoring"].get("tiers") or config["scoring"].get("tier_thresholds", {})

    # Find MEDIUM tier threshold (the cutoff for "interesting" articles)
    medium_threshold = 4.0  # default fallback

    # Try direct "medium" key first (most filters)
    if "medium" in tiers:
        tier_def = tiers["medium"]
        medium_threshold = tier_def.get("threshold", tier_def.get("min_score", 4.0))
    else:
        # For filters without "medium" tier (e.g. investment-risk uses RED/YELLOW/GREEN/BLUE/NOISE),
        # find the lowest min_score among actionable tiers as the "interesting" threshold
        actionable_scores = []
        for tier_name, tier_def in tiers.items():
            if isinstance(tier_def, dict) and "min_score" in tier_def:
                actionable_scores.append(tier_def["min_score"])
        if actionable_scores:
            medium_threshold = min(actionable_scores)

    return dim_names, dim_weights, medium_threshold


def compute_weighted_avg(
    scores: Dict[str, float],
    dim_names: List[str],
    dim_weights: Dict[str, float],
) -> float:
    """Compute weighted average from dimension scores."""
    return sum(scores.get(dim, 0) * dim_weights[dim] for dim in dim_names)


def run_ground_truth_calibration(
    articles: List[Dict],
    dim_names: List[str],
    dim_weights: Dict[str, float],
    medium_threshold: float,
    probe_path: str,
    embedding_model: str,
    device: str,
):
    """Calibrate using ground truth labels from training data."""
    from filters.common.embedding_stage import EmbeddingStage

    # Load Stage 1
    stage1 = EmbeddingStage(
        embedding_model_name=embedding_model,
        probe_path=probe_path,
        threshold=0.0,  # We'll sweep threshold manually
        dimension_weights=dim_weights,
        dimension_names=dim_names,
        device=device,
    )

    # Compute ground truth weighted averages
    gt_weighted_avgs = []
    for article in articles:
        labels = article.get("labels", [])
        if len(labels) != len(dim_names):
            gt_weighted_avgs.append(None)
            continue
        scores = {dim: labels[i] for i, dim in enumerate(dim_names)}
        gt_weighted_avgs.append(compute_weighted_avg(scores, dim_names, dim_weights))

    # Run Stage 1
    logger.info(f"Running Stage 1 on {len(articles)} articles...")
    screening_results = stage1.screen_batch(articles, batch_size=32)

    # Sweep thresholds
    thresholds = np.arange(1.0, 5.1, 0.25)

    print(f"\n{'='*80}")
    print(f"Threshold Calibration Results (Ground Truth)")
    print(f"{'='*80}")
    print(f"MEDIUM+ threshold: >= {medium_threshold}")
    print(f"Total articles: {len(articles)}")
    print()
    print(f"{'Threshold':>10} {'Stage1 LOW':>12} {'Stage2':>8} {'FN (MEDIUM+)':>14} {'FN Rate':>10} {'Speedup':>10}")
    print(f"{'-'*10} {'-'*12} {'-'*8} {'-'*14} {'-'*10} {'-'*10}")

    best_threshold = None
    best_fn_rate = 1.0

    for threshold in thresholds:
        stage1_low = 0
        stage2 = 0
        false_negatives = 0
        medium_plus_total = 0

        for i, screen in enumerate(screening_results):
            gt_avg = gt_weighted_avgs[i]
            if gt_avg is None:
                continue

            is_medium_plus = gt_avg >= medium_threshold
            if is_medium_plus:
                medium_plus_total += 1

            if screen.weighted_avg < threshold:
                # Would be classified as LOW by Stage 1
                stage1_low += 1
                if is_medium_plus:
                    false_negatives += 1
            else:
                stage2 += 1

        total = stage1_low + stage2
        fn_rate = false_negatives / medium_plus_total if medium_plus_total > 0 else 0
        stage1_pct = stage1_low / total if total > 0 else 0
        speedup_estimate = 1 / (1 - stage1_pct * 0.6) if stage1_pct < 1 else 1

        marker = ""
        if fn_rate <= 0.02 and (best_threshold is None or stage1_pct > 0.5):
            best_threshold = threshold
            best_fn_rate = fn_rate
            marker = " <-- recommended"

        print(
            f"{threshold:>10.2f} {stage1_low:>12} {stage2:>8} "
            f"{false_negatives:>14} {fn_rate:>9.1%} {speedup_estimate:>9.2f}x{marker}"
        )

    print()
    if best_threshold is not None:
        print(f"Recommended threshold: {best_threshold:.2f} (FN rate: {best_fn_rate:.1%})")
    else:
        print("WARNING: No threshold achieves <2% FN rate. Consider lowering target.")

    # Show probe accuracy stats
    probe_avgs = [s.weighted_avg for s in screening_results]
    valid_gt = [g for g in gt_weighted_avgs if g is not None]
    if valid_gt:
        errors = [abs(p - g) for p, g in zip(probe_avgs, valid_gt)]
        print(f"\nProbe accuracy:")
        print(f"  MAE vs ground truth: {np.mean(errors):.3f}")
        print(f"  RMSE vs ground truth: {np.sqrt(np.mean([e**2 for e in errors])):.3f}")
        print(f"  Probe mean: {np.mean(probe_avgs):.3f}, GT mean: {np.mean(valid_gt):.3f}")


def run_model_calibration(
    articles: List[Dict],
    filter_name: str,
    version: str,
    dim_names: List[str],
    dim_weights: Dict[str, float],
    medium_threshold: float,
    probe_path: str,
    embedding_model: str,
    device: str,
):
    """Calibrate by comparing Stage 1 probe vs Stage 2 fine-tuned model."""
    from filters.common.embedding_stage import EmbeddingStage

    # Load Stage 1
    stage1 = EmbeddingStage(
        embedding_model_name=embedding_model,
        probe_path=probe_path,
        threshold=0.0,
        dimension_weights=dim_weights,
        dimension_names=dim_names,
        device=device,
    )

    # Load Stage 2 (the fine-tuned model)
    logger.info("Loading Stage 2 model for comparison...")
    scorer_map = {
        "uplifting": ("filters.uplifting.v5.inference", "UpliftingScorer"),
        "sustainability_technology": ("filters.sustainability_technology.v2.inference", "SustainabilityTechnologyScorer"),
        "investment-risk": ("filters.investment-risk.v5.inference", "InvestmentRiskScorer"),
        "cultural-discovery": ("filters.cultural-discovery.v3.inference", "CulturalDiscoveryScorer"),
    }
    if filter_name not in scorer_map:
        raise ValueError(
            f"Unknown filter: {filter_name}. "
            f"Known filters: {list(scorer_map.keys())}"
        )
    module_path, class_name = scorer_map[filter_name]
    import importlib
    module = importlib.import_module(module_path)
    scorer_class = getattr(module, class_name)
    stage2_scorer = scorer_class(device=device, use_prefilter=False)

    # Run Stage 1
    logger.info(f"Running Stage 1 on {len(articles)} articles...")
    screening_results = stage1.screen_batch(articles, batch_size=32)

    # Run Stage 2
    logger.info(f"Running Stage 2 on {len(articles)} articles...")
    stage2_results = stage2_scorer.score_batch(articles, batch_size=16, skip_prefilter=True)

    # Sweep thresholds
    thresholds = np.arange(1.0, 5.1, 0.25)

    print(f"\n{'='*80}")
    print(f"Threshold Calibration Results (vs Fine-Tuned Model)")
    print(f"{'='*80}")
    print(f"MEDIUM+ threshold: >= {medium_threshold}")
    print(f"Total articles: {len(articles)}")
    print()
    print(f"{'Threshold':>10} {'Stage1 LOW':>12} {'Stage2':>8} {'FN (MEDIUM+)':>14} {'FN Rate':>10} {'Speedup':>10}")
    print(f"{'-'*10} {'-'*12} {'-'*8} {'-'*14} {'-'*10} {'-'*10}")

    best_threshold = None

    for threshold in thresholds:
        stage1_low = 0
        stage2_count = 0
        false_negatives = 0
        medium_plus_total = 0

        for i, (screen, s2_result) in enumerate(zip(screening_results, stage2_results)):
            s2_avg = s2_result.get("weighted_average")
            if s2_avg is None:
                continue

            is_medium_plus = s2_avg >= medium_threshold
            if is_medium_plus:
                medium_plus_total += 1

            if screen.weighted_avg < threshold:
                stage1_low += 1
                if is_medium_plus:
                    false_negatives += 1
            else:
                stage2_count += 1

        total = stage1_low + stage2_count
        fn_rate = false_negatives / medium_plus_total if medium_plus_total > 0 else 0
        stage1_pct = stage1_low / total if total > 0 else 0
        speedup_estimate = 1 / (1 - stage1_pct * 0.6) if stage1_pct < 1 else 1

        marker = ""
        if fn_rate <= 0.02 and (best_threshold is None or stage1_pct > 0.5):
            best_threshold = threshold
            marker = " <-- recommended"

        print(
            f"{threshold:>10.2f} {stage1_low:>12} {stage2_count:>8} "
            f"{false_negatives:>14} {fn_rate:>9.1%} {speedup_estimate:>9.2f}x{marker}"
        )

    print()
    if best_threshold is not None:
        print(f"Recommended threshold: {best_threshold:.2f}")
    else:
        print("WARNING: No threshold achieves <2% FN rate.")


def main():
    parser = argparse.ArgumentParser(
        description="Calibrate Stage 1 threshold for hybrid inference pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--filter", type=str, required=True,
        help="Filter name (e.g., uplifting)",
    )
    parser.add_argument(
        "--version", type=str, required=True,
        help="Filter version (e.g., v5)",
    )
    parser.add_argument(
        "--val-data", type=Path, required=True,
        help="Path to validation JSONL file",
    )
    parser.add_argument(
        "--probe-path", type=str, default=None,
        help="Path to MLP probe pickle (default: filters/{filter}/{version}/probe/embedding_probe.pkl)",
    )
    parser.add_argument(
        "--embedding-model", type=str, default="intfloat/multilingual-e5-large",
        help="Embedding model name",
    )
    parser.add_argument(
        "--device", type=str, default=None,
        help="Device (cuda or cpu, default: auto)",
    )
    parser.add_argument(
        "--use-ground-truth", action="store_true",
        help="Use ground truth labels instead of Stage 2 model predictions",
    )

    args = parser.parse_args()

    if args.device is None:
        import torch
        args.device = "cuda" if torch.cuda.is_available() else "cpu"

    if args.probe_path is None:
        args.probe_path = f"filters/{args.filter}/{args.version}/probe/embedding_probe.pkl"

    # Load config
    config = load_filter_config(args.filter, args.version)
    dim_names, dim_weights, medium_threshold = extract_dimension_info(config)

    logger.info(f"Filter: {args.filter} {args.version}")
    logger.info(f"Dimensions: {dim_names}")
    logger.info(f"MEDIUM threshold: {medium_threshold}")

    # Load articles
    articles = load_articles(args.val_data)
    logger.info(f"Loaded {len(articles)} validation articles")

    if args.use_ground_truth:
        run_ground_truth_calibration(
            articles, dim_names, dim_weights, medium_threshold,
            args.probe_path, args.embedding_model, args.device,
        )
    else:
        run_model_calibration(
            articles, args.filter, args.version,
            dim_names, dim_weights, medium_threshold,
            args.probe_path, args.embedding_model, args.device,
        )


if __name__ == "__main__":
    main()
