"""
Uplifting Content Filter v7 - Production Inference Pipeline

This module provides the complete inference pipeline for scoring articles
using the trained uplifting content filter with local model files.

Pipeline: Article -> Prefilter -> Model -> Gatekeeper -> Tier

Usage:
    # Python API
    from filters.uplifting.v7.inference import UpliftingScorer

    scorer = UpliftingScorer()
    result = scorer.score_article(article)

    # CLI
    python filters/uplifting/v7/inference.py --input articles.jsonl --output results.jsonl
"""

import json
import logging
from pathlib import Path
from typing import Optional

from filters.common.model_loading import load_lora_local
from filters.uplifting.v7.base_scorer import BaseUpliftingScorer

logger = logging.getLogger(__name__)


class UpliftingScorer(BaseUpliftingScorer):
    """
    Production scorer for uplifting content filter v7.

    Loads the trained LoRA model from local files and provides scoring with:
    - Optional prefiltering for efficiency
    - Per-dimension scores (6 orthogonal dimensions)
    - Evidence gatekeeper logic
    - Tier assignment (high/medium/low)
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        device: Optional[str] = None,
        use_prefilter: bool = False,
    ):
        if model_path is None:
            model_path = Path(__file__).parent / "model"
        self.model_path = Path(model_path)

        super().__init__(device=device, use_prefilter=use_prefilter)
        self._load_model()

    def _load_model(self):
        """Load the trained LoRA model from local files."""
        self.model, self.tokenizer = load_lora_local(
            self.model_path, len(self.DIMENSION_NAMES), self.device
        )


def main():
    """CLI interface for batch scoring."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Score articles with uplifting content filter v7"
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

    args = parser.parse_args()

    print("Initializing scorer...")
    scorer = UpliftingScorer(use_prefilter=False)

    if args.input:
        print(f"Loading articles from {args.input}")
        articles = []
        with open(args.input, "r", encoding="utf-8") as f:
            for line in f:
                articles.append(json.loads(line))

        print(f"Scoring {len(articles)} articles...")
        results = scorer.score_batch(articles, batch_size=args.batch_size)

        if args.output:
            print(f"Writing results to {args.output}")
            with open(args.output, "w", encoding="utf-8") as f:
                for article, result in zip(articles, results):
                    article_id = article.get("id") or article.get("article_id", "")
                    output = {"article_id": article_id, **result}
                    f.write(json.dumps(output) + "\n")
        else:
            passed = sum(1 for r in results if r["passed_prefilter"])
            print(f"\nResults: {passed}/{len(results)} passed prefilter")

            if passed > 0:
                tiers = {}
                for r in results:
                    if r["tier"]:
                        tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1
                print("Tier distribution:")
                for tier, count in sorted(tiers.items()):
                    print(f"  {tier}: {count}")
    else:
        print("\n--- Interactive Demo ---")
        demo_article = {
            "title": "Community Garden Feeds 500 Families in Food Desert",
            "content": """
            A volunteer-led community garden in Detroit has grown to feed over 500 families
            in what was previously a food desert. The project, started three years ago on
            abandoned lots, now spans 2 acres and produces 10,000 pounds of fresh vegetables
            annually. Local residents volunteer their time, and all produce is distributed
            free to neighborhood families. The city has since allocated funding to expand
            the model to five additional neighborhoods, with plans for year-round growing
            in greenhouses.
            """
        }

        print(f"\nDemo article: {demo_article['title']}")
        result = scorer.score_article(demo_article)

        print(f"\nResults:")
        print(f"  Passed prefilter: {result['passed_prefilter']}")
        if result["scores"]:
            print(f"  Scores:")
            for dim, score in result["scores"].items():
                print(f"    {dim}: {score:.2f}")
            print(f"  Weighted average: {result['weighted_average']:.2f}")
            print(f"  Tier: {result['tier']} ({result['tier_description']})")
            if result["gatekeeper_applied"]:
                print(f"  Note: Evidence gatekeeper applied (speculation capped)")


if __name__ == "__main__":
    main()
