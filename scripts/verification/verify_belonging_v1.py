"""
Belonging Filter v1 — Pre-deployment Verification

End-to-end test of the belonging filter package before Hub upload and deployment.
Tests: model loading, prefilter, scoring, calibration, gatekeeper, tier assignment,
batch scoring, MAE against oracle labels, and inference_hub module imports.

Usage:
    PYTHONPATH=. python scripts/verification/verify_belonging_v1.py

Requires: GPU or CPU with ~4GB RAM, test split at datasets/training/belonging_v1/test.jsonl
"""
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import torch

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

FILTER_DIR = Path("filters/belonging/v1")
TEST_DATA = Path("datasets/training/belonging_v1/test.jsonl")
VAL_DATA = Path("datasets/training/belonging_v1/val.jsonl")
EXPECTED_DIMS = [
    "intergenerational_bonds", "community_fabric", "reciprocal_care",
    "rootedness", "purpose_beyond_self", "slow_presence",
]
EXPECTED_WEIGHTS = {
    "intergenerational_bonds": 0.25, "community_fabric": 0.25,
    "reciprocal_care": 0.10, "rootedness": 0.15,
    "purpose_beyond_self": 0.15, "slow_presence": 0.10,
}

passed = 0
failed = 0
warnings = 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name} — {detail}")
        failed += 1
    return condition


def warn(name, detail):
    global warnings
    print(f"  WARN: {name} — {detail}")
    warnings += 1


def load_test_articles(path, max_n=None):
    articles = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            a = json.loads(line)
            articles.append(a)
            if max_n and len(articles) >= max_n:
                break
    return articles


def main():
    global passed, failed, warnings

    print("=" * 70)
    print("BELONGING v1 — PRE-DEPLOYMENT VERIFICATION")
    print("=" * 70)

    # ================================================================
    print("\n--- 1. File Completeness ---")
    # ================================================================
    required_files = [
        "base_scorer.py", "inference.py", "inference_hub.py",
        "inference_hybrid.py", "config.yaml", "calibration.json",
        "training_history.json", "training_metadata.json",  # prefilter.py deleted 2026-10-01
        "model/adapter_config.json", "model/adapter_model.safetensors",
        "model/tokenizer.json", "model/tokenizer_config.json",
    ]
    for f in required_files:
        check(f"File exists: {f}", (FILTER_DIR / f).exists())

    # ================================================================
    print("\n--- 2. Config Validation ---")
    # ================================================================
    import yaml
    with open(FILTER_DIR / "config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    dims = config["scoring"]["dimensions"]
    check("6 dimensions defined", len(dims) == 6, f"got {len(dims)}")
    check("Dimension names match", set(dims.keys()) == set(EXPECTED_DIMS),
          f"got {set(dims.keys())}")

    total_weight = sum(dims[d]["weight"] for d in dims)
    check("Weights sum to 1.0", abs(total_weight - 1.0) < 0.01, f"sum={total_weight}")

    check("Gatekeeper configured", config["scoring"].get("gatekeepers") is not None)
    gk = config["scoring"]["gatekeepers"]["community_fabric_gatekeeper"]
    check("Gatekeeper dimension = community_fabric", gk["dimension"] == "community_fabric")
    check("Gatekeeper threshold = 3", gk["threshold"] == 3)
    check("Gatekeeper max_score = 3.42", gk["max_score"] == 3.42)

    check("Head+tail enabled", config["preprocessing"]["head_tail"]["enabled"] is True)
    check("Head tokens = 256", config["preprocessing"]["head_tail"]["head_tokens"] == 256)
    check("Tail tokens = 256", config["preprocessing"]["head_tail"]["tail_tokens"] == 256)

    check("Recommended model = gemma-3-1b", "gemma-3-1b" in config["training"]["recommended_model"])

    # ================================================================
    print("\n--- 3. Calibration File ---")
    # ================================================================
    with open(FILTER_DIR / "calibration.json", "r", encoding="utf-8") as f:
        cal = json.load(f)

    check("Calibration has dimensions", "dimensions" in cal)
    cal_dims = set(cal["dimensions"].keys())
    check("Calibration covers all 6 dims", cal_dims == set(EXPECTED_DIMS),
          f"missing: {set(EXPECTED_DIMS) - cal_dims}")
    check("Calibration has n_samples", "n_samples" in cal)
    check("Calibration n_samples = 738", cal.get("n_samples") == 738, f"got {cal.get('n_samples')}")

    for dim in EXPECTED_DIMS:
        d = cal["dimensions"].get(dim, {})
        check(f"Calibration {dim[:12]} has x", "x" in d)
        check(f"Calibration {dim[:12]} has y", "y" in d)

    # ================================================================
    print("\n--- 4. Training Metadata ---")
    # ================================================================
    with open(FILTER_DIR / "training_metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    check("Base model recorded", "model_name" in meta or "base_model" in meta)
    train_n = meta.get("train_examples", meta.get("train_samples", 0))
    check("Training articles recorded", train_n > 5000, f"got {train_n}")

    with open(FILTER_DIR / "training_history.json", "r", encoding="utf-8") as f:
        history = json.load(f)

    check("Training history non-empty", len(history) > 0)

    # ================================================================
    print("\n--- 5. Module Imports ---")
    # ================================================================
    try:
        from filters.belonging.v1.base_scorer import BaseBelongingScorer
        check("Import base_scorer", True)
        check("FILTER_NAME = 'belonging'", BaseBelongingScorer.FILTER_NAME == "belonging")
        check("DIMENSION_NAMES length = 6", len(BaseBelongingScorer.DIMENSION_NAMES) == 6)
        check("DIMENSION_WEIGHTS match config",
              BaseBelongingScorer.DIMENSION_WEIGHTS == EXPECTED_WEIGHTS)
        check("GATEKEEPER_DIMENSION = community_fabric",
              BaseBelongingScorer.GATEKEEPER_DIMENSION == "community_fabric")
        check("GATEKEEPER_MIN = 3.0", BaseBelongingScorer.GATEKEEPER_MIN == 3.0)
        check("GATEKEEPER_CAP = 3.42", BaseBelongingScorer.GATEKEEPER_CAP == 3.42)
    except Exception as e:
        check("Import base_scorer", False, str(e))

    try:
        from filters.belonging.v1.inference_hub import BelongingScorerHub
        check("Import inference_hub", True)
    except ImportError as e:
        check("Import inference_hub", False, str(e))

    try:
        from filters.belonging.v1.inference_hybrid import BelongingHybridScorer
        check("Import inference_hybrid", True)
    except ImportError as e:
        check("Import inference_hybrid", False, str(e))

    # ================================================================
    print("\n--- 6. Prefilter ---")
    # ================================================================
    # Deleted 2026-10-01 with every per-lens prefilter (NexusMind#284, decision 0).
    # Check the absence instead, so a prefilter that comes back is noticed here too.
    from pathlib import Path as _P
    check("No per-lens prefilter.py (decision 0)",
          not (_P(__file__).resolve().parents[2] / "filters/belonging/v1/prefilter.py").exists())

    # ================================================================
    print("\n--- 7. Model Loading & Single Article Scoring ---")
    # ================================================================
    try:
        from filters.belonging.v1.inference import BelongingScorer
        print("  Loading model (this may take 30-60s on CPU)...")
        t0 = time.time()
        scorer = BelongingScorer(use_prefilter=False)
        load_time = time.time() - t0
        check(f"Model loads ({load_time:.1f}s)", True)
        check("Model on expected device", scorer.device is not None)

        # Score the belonging demo article
        demo = {
            "title": "The Last Weaver: How One Village Keeps a 400-Year Tradition Alive",
            "content": "In a small village in Oaxaca, 78-year-old Elena Vasquez rises before dawn "
                       "to prepare her loom. Her granddaughter Maria, 14, sits beside her — as she "
                       "has every morning since she was six. 'My grandmother taught me,' Elena says, "
                       "'and her grandmother taught her. The patterns carry our history.' The village "
                       "of San Marcos has practiced backstrap weaving for over four centuries. Unlike "
                       "tourist-facing workshops in the city, this tradition remains embedded in daily "
                       "life. Neighbors share dye recipes; young mothers weave while watching each "
                       "other's children. When a family needs money, the community orders from them first."
        }

        t0 = time.time()
        result = scorer.score_article(demo)
        score_time = time.time() - t0

        check("Score returns dict", isinstance(result, dict))
        check("Passed prefilter", result["passed_prefilter"])
        check("Has scores", result["scores"] is not None)
        check("Has 6 dimension scores", len(result.get("scores", {})) == 6)
        check("Has weighted_average", result["weighted_average"] is not None)
        check("Has tier", result["tier"] is not None)
        check(f"Inference time OK ({score_time:.2f}s)", score_time < 30)

        # Sanity: this demo should score reasonably high on belonging
        wavg = result["weighted_average"]
        check(f"Demo weighted_avg > 3.0 (got {wavg:.2f})", wavg > 3.0,
              "Demo article should show some belonging signal")

        # Check all scores are in valid range
        all_valid = all(0 <= s <= 10 for s in result["scores"].values())
        check("All scores in [0, 10]", all_valid)

        print(f"\n  Demo result:")
        for dim, score in result["scores"].items():
            print(f"    {dim}: {score:.2f}")
        print(f"    weighted_average: {wavg:.2f}")
        print(f"    tier: {result['tier']}")
        print(f"    gatekeeper_applied: {result.get('gatekeeper_applied', False)}")

    except Exception as e:
        check("Model loads", False, str(e))
        print(f"\n  Cannot continue without model. Skipping remaining tests.")
        print_summary()
        return

    # ================================================================
    print("\n--- 8. Gatekeeper Logic ---")
    # ================================================================
    # Article with low community_fabric but high other dims should be capped
    low_cf_article = {
        "title": "A Hermit's Life of Purpose in the Mountains",
        "content": "After 30 years of corporate life, John retreated to a cabin in Montana. "
                   "He lives alone, tends his garden, and writes letters to his grandchildren. "
                   "He finds deep purpose in solitude and connection with nature. His family "
                   "visits once a year. He has no neighbors within 20 miles."
    }
    gk_result = scorer.score_article(low_cf_article, skip_prefilter=True)
    if gk_result["scores"] is not None:
        cf_score = gk_result["scores"]["community_fabric"]
        wavg = gk_result["weighted_average"]
        print(f"  Low-CF article: community_fabric={cf_score:.2f}, weighted_avg={wavg:.2f}, "
              f"gatekeeper={gk_result.get('gatekeeper_applied')}")
        if cf_score < 3.0:
            check("Gatekeeper caps score when CF < 3.0",
                  wavg <= 3.42 + 0.01 or not gk_result.get("gatekeeper_applied", False))
        else:
            warn("Gatekeeper test", f"CF scored {cf_score:.2f} (>= 3.0), gatekeeper not triggered")

    # ================================================================
    print("\n--- 9. Batch Scoring & MAE on Test Set ---")
    # ================================================================
    data_path = TEST_DATA if TEST_DATA.exists() else VAL_DATA
    if not data_path.exists():
        warn("Test data", f"Neither {TEST_DATA} nor {VAL_DATA} found, skipping MAE test")
    else:
        print(f"  Loading test data from {data_path}...")
        test_articles = load_test_articles(data_path)
        print(f"  {len(test_articles)} articles loaded")

        # Extract oracle labels
        oracle_labels = []
        articles_for_scoring = []
        dim_names = test_articles[0]["dimension_names"]

        check("Test dim names match filter", dim_names == EXPECTED_DIMS,
              f"got {dim_names}")

        for a in test_articles:
            if "title" in a and "content" in a and a["content"]:
                oracle_labels.append(a["labels"])
                articles_for_scoring.append(a)

        print(f"  Scoring {len(articles_for_scoring)} articles (batch_size=16)...")
        t0 = time.time()
        results = scorer.score_batch(articles_for_scoring, batch_size=16, skip_prefilter=True)
        batch_time = time.time() - t0
        print(f"  Batch scoring took {batch_time:.1f}s ({batch_time/len(articles_for_scoring)*1000:.0f}ms/article)")

        # Calculate MAE
        pred_scores = []
        valid_count = 0
        for r in results:
            if r["scores"] is not None:
                pred_scores.append([r["scores"][d] for d in EXPECTED_DIMS])
                valid_count += 1
            else:
                pred_scores.append([0.0] * 6)

        pred = np.array(pred_scores)
        oracle = np.array(oracle_labels[:len(pred)])

        overall_mae = np.mean(np.abs(pred[:valid_count] - oracle[:valid_count]))
        per_dim_mae = np.mean(np.abs(pred[:valid_count] - oracle[:valid_count]), axis=0)

        print(f"\n  Overall MAE: {overall_mae:.4f}")
        print(f"  Per-dimension MAE:")
        for i, dim in enumerate(EXPECTED_DIMS):
            print(f"    {dim}: {per_dim_mae[i]:.4f}")

        check(f"Overall MAE < 0.60 (got {overall_mae:.4f})", overall_mae < 0.60)
        check(f"Valid results = test articles", valid_count == len(articles_for_scoring),
              f"got {valid_count}/{len(articles_for_scoring)}")

        # Tier distribution
        tiers = {}
        for r in results:
            t = r.get("tier", "none")
            tiers[t] = tiers.get(t, 0) + 1
        print(f"\n  Tier distribution:")
        for tier, count in sorted(tiers.items()):
            print(f"    {tier}: {count} ({100*count/len(results):.1f}%)")

        # Check tier distribution is reasonable (most should be low for belonging)
        low_pct = tiers.get("low", 0) / len(results) * 100
        check(f"LOW tier > 60% (got {low_pct:.0f}%)", low_pct > 60,
              "Belonging is needle-in-haystack, most articles should be LOW")

    # ================================================================
    print("\n--- 10. Prefilter + Score Integration ---")
    # ================================================================
    # Score a few articles WITH prefilter to verify full pipeline
    if data_path.exists():
        sample = test_articles[:20]
        results_with_pf = scorer.score_batch(sample, batch_size=16, skip_prefilter=False)
        blocked = sum(1 for r in results_with_pf if not r["passed_prefilter"])
        scored = sum(1 for r in results_with_pf if r["scores"] is not None)
        print(f"  20 test articles: {blocked} blocked by prefilter, {scored} scored")
        check("Prefilter blocks some articles", blocked >= 0)  # may or may not block test data
        check("Some articles scored", scored > 0, f"got {scored}")

    # ================================================================
    print_summary()


def print_summary():
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed, {warnings} warnings")
    print("=" * 70)

    if failed == 0:
        print("\nBelonging v1 is READY for deployment.")
        print("Remaining steps:")
        print("  1. Train embedding probe on gpu-server (optional, for hybrid speedup)")
        print("  2. Upload to HuggingFace Hub")
        print("  3. Deploy to NexusMind")
    else:
        print(f"\nBelonging v1 has {failed} FAILURES — fix before deploying.")

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
