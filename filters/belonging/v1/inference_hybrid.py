"""
Belonging Filter v1 - Hybrid Inference Pipeline

Two-stage scorer that uses embedding + MLP probe for fast screening (Stage 1)
and the trained Gemma-3-1B model for precise scoring (Stage 2).

Stage 1 (~1.3ms): Embedding probe estimates scores. Articles with weighted_avg
below threshold are classified as LOW without running the expensive model.

Stage 2 (~19ms): Full fine-tuned model scoring for articles that pass Stage 1.

Usage:
    from filters.belonging.v1.inference_hybrid import BelongingHybridScorer

    scorer = BelongingHybridScorer()
    result = scorer.score_article(article)
    # result["stage_used"] -> "stage1_low" or "stage2"

    # CLI
    python filters/belonging/v1/inference_hybrid.py --input articles.jsonl --output results.jsonl
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from filters.common.hybrid_scorer import HybridScorer
from filters.belonging.v1.inference import BelongingScorer

logger = logging.getLogger(__name__)

# Default Stage 1 threshold: articles below this skip Stage 2
# Calibrated on v1 val data (738 articles):
#   Threshold 1.00 -> 0.0% FN rate on MEDIUM+, ~1.18x speedup
DEFAULT_THRESHOLD = 1.00


class BelongingHybridScorer(HybridScorer):
    """
    Two-stage hybrid scorer for belonging filter v1.

    Combines:
    - Stage 1: multilingual-e5-small embeddings + MLP probe
    - Stage 2: Existing BelongingScorer (Gemma-3-1B fine-tuned)
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        probe_path: Optional[Path] = None,
        threshold: float = DEFAULT_THRESHOLD,
        device: Optional[str] = None,
        use_prefilter: bool = False,
    ):
        """
        Initialize the hybrid belonging scorer.

        Args:
            model_path: Path to Stage 2 model directory (default: ./model)
            probe_path: Path to Stage 1 probe file (default: ./probe/embedding_probe_e5small.pkl)
            threshold: Stage 1 threshold (articles below skip Stage 2)
            device: Device to use ('cuda', 'cpu', or None for auto)
            use_prefilter: must be False (per-lens prefilters deleted 2026-10-01, NexusMind#284)
        """
        self._model_path = model_path
        self._probe_path = probe_path or (
            Path(__file__).parent / "probe" / "embedding_probe_e5small.pkl"
        )
        self._threshold = threshold

        super().__init__(device=device, use_prefilter=use_prefilter)

    def _create_stage2_scorer(self):
        """Create the existing BelongingScorer as Stage 2.

        Built with use_prefilter=False, the only value accepted since the per-lens
        prefilters were deleted (NexusMind#284, decision 0, 2026-10-01).
        """
        return BelongingScorer(
            model_path=self._model_path,
            device=self.device_str,
            use_prefilter=False,
        )

    def _get_embedding_stage_config(self) -> Dict:
        """Return EmbeddingStage configuration for belonging v1."""
        return {
            "embedding_model_name": "intfloat/multilingual-e5-small",
            "probe_path": str(self._probe_path),
            "threshold": self._threshold,
        }


def main():
    """CLI interface for hybrid batch scoring."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Score articles with belonging hybrid scorer (two-stage pipeline)"
    )
    parser.add_argument(
        "--input", "-i", type=Path, help="Input JSONL file with articles"
    )
    parser.add_argument(
        "--output", "-o", type=Path, help="Output JSONL file for results"
    )
    parser.add_argument(
        "--no-prefilter", action="store_true", help="No effect: per-lens prefilters were deleted (NexusMind#284, decision 0); kept so old invocations still parse"
    )
    parser.add_argument(
        "--batch-size", type=int, default=16, help="Batch size for inference"
    )
    parser.add_argument(
        "--threshold", type=float, default=DEFAULT_THRESHOLD,
        help=f"Stage 1 threshold (default: {DEFAULT_THRESHOLD})"
    )
    parser.add_argument(
        "--compare", action="store_true",
        help="Also run standard scorer and compare results"
    )

    args = parser.parse_args()

    print("Initializing hybrid scorer...")
    scorer = BelongingHybridScorer(
        threshold=args.threshold,
        use_prefilter=False,
    )

    if args.input:
        print(f"Loading articles from {args.input}")
        articles = []
        with open(args.input, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    articles.append(json.loads(line))

        print(f"Scoring {len(articles)} articles with hybrid pipeline...")
        import time
        start = time.time()
        results = scorer.score_batch(articles, batch_size=args.batch_size)
        hybrid_time = time.time() - start

        stage1_low = sum(1 for r in results if r.get("stage_used") == "stage1_low")
        stage2 = sum(1 for r in results if r.get("stage_used") == "stage2")
        prefilter_blocked = sum(1 for r in results if not r.get("passed_prefilter", True))

        print(f"\nHybrid results ({hybrid_time:.2f}s):")
        print(f"  Prefilter blocked: {prefilter_blocked}")
        print(f"  Stage 1 LOW (skipped model): {stage1_low}")
        print(f"  Stage 2 (full model): {stage2}")
        print(f"  Avg time per article: {hybrid_time/len(articles)*1000:.1f}ms")

        tiers = {}
        for r in results:
            tier = r.get("tier")
            if tier:
                tiers[tier] = tiers.get(tier, 0) + 1
        print(f"\nTier distribution:")
        for tier, count in sorted(tiers.items()):
            print(f"  {tier}: {count}")

        # Optional comparison with standard scorer
        if args.compare:
            print(f"\nRunning standard scorer for comparison...")
            standard_scorer = BelongingScorer(
                use_prefilter=False,
            )
            start = time.time()
            standard_results = standard_scorer.score_batch(
                articles, batch_size=args.batch_size
            )
            standard_time = time.time() - start

            print(f"Standard scorer: {standard_time:.2f}s ({standard_time/len(articles)*1000:.1f}ms/article)")
            print(f"Speedup: {standard_time/hybrid_time:.2f}x")

            # Check agreement on MEDIUM+ articles
            disagreements = 0
            for i, (h, s) in enumerate(zip(results, standard_results)):
                if s.get("tier") in ("medium", "high") and h.get("stage_used") == "stage1_low":
                    disagreements += 1
                    print(
                        f"  FALSE NEGATIVE #{disagreements}: article {i} "
                        f"(standard={s.get('tier')}, stage1_est={h.get('stage1_estimate', 0):.2f})"
                    )

            print(f"\nFalse negatives (MEDIUM+ classified as LOW by Stage 1): {disagreements}")

        if args.output:
            print(f"\nWriting results to {args.output}")
            with open(args.output, "w", encoding="utf-8") as f:
                for article, result in zip(articles, results):
                    article_id = article.get("id") or article.get("article_id", "")
                    output = {"article_id": article_id, **result}
                    f.write(json.dumps(output) + "\n")
    else:
        print("\n--- Hybrid Scorer Demo ---")
        demo_article = {
            "title": "The Last Weaver: How One Village Keeps a 400-Year Tradition Alive",
            "content": (
                "In a small village in Oaxaca, 78-year-old Elena Vasquez rises before dawn "
                "to prepare her loom. Her granddaughter Maria, 14, sits beside her — as she "
                "has every morning since she was six. The patterns carry our history."
            ),
        }

        print(f"\nDemo article: {demo_article['title']}")
        result = scorer.score_article(demo_article)

        print(f"\nResults:")
        print(f"  Stage used: {result.get('stage_used')}")
        print(f"  Stage 1 estimate: {result.get('stage1_estimate', 'N/A')}")
        if result["scores"]:
            print(f"  Scores:")
            for dim, score in result["scores"].items():
                print(f"    {dim}: {score:.2f}")
            print(f"  Weighted average: {result['weighted_average']:.2f}")
            print(f"  Tier: {result['tier']}")


if __name__ == "__main__":
    main()
