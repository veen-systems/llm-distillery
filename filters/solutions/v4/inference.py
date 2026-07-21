"""
Solutions Filter v4 - Production Inference Pipeline

Scores articles for concrete solutions across tech / governance / community:
deployed practices, enacted policy, running community initiatives.

Pipeline: Article -> Prefilter -> Model -> Calibration -> Gatekeeper -> Tier

Usage:
    # Python API
    from filters.solutions.v4.inference import SolutionsScorer
    scorer = SolutionsScorer()
    result = scorer.score_article(article)

    # CLI
    python filters/solutions/v4/inference.py --input articles.jsonl --output results.jsonl

For loading from HuggingFace Hub, use SolutionsScorerHub (inference_hub.py).
"""

import json
import logging
from pathlib import Path
from typing import Optional

from filters.common.model_loading import load_lora_local
from filters.solutions.v4.base_scorer import BaseSolutionsScorer

logger = logging.getLogger(__name__)


class SolutionsScorer(BaseSolutionsScorer):
    """
    Production scorer for the solutions filter v4.

    Loads the trained LoRA model from local files and provides scoring with:
    - Optional prefiltering for efficiency (SolutionsPreFilterV4)
    - Per-dimension scores (7 dimensions)
    - Score calibration (isotonic regression, calibration.json)
    - solution_concreteness gatekeeper
    - Tier assignment (high_solution/medium_high/medium/low)

    For loading from HuggingFace Hub, use SolutionsScorerHub instead.
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        device: Optional[str] = None,
        use_prefilter: bool = True,
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

    parser = argparse.ArgumentParser(description="Score articles with the solutions filter v4")
    parser.add_argument("--input", "-i", type=Path, help="Input JSONL file with articles")
    parser.add_argument("--output", "-o", type=Path, help="Output JSONL file for results")
    parser.add_argument("--no-prefilter", action="store_true", help="Skip prefilter")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size for inference")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    scorer = SolutionsScorer(use_prefilter=not args.no_prefilter)

    if args.input:
        articles = []
        with open(args.input, "r", encoding="utf-8") as f:
            for line in f:
                articles.append(json.loads(line))

        logger.info(f"Scoring {len(articles)} articles...")
        results = scorer.score_batch(articles, batch_size=args.batch_size)

        if args.output:
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
            "title": "City rolls out battery-swap stations for delivery riders",
            "content": """
            The municipal transport authority has installed 42 battery-swap
            stations across the city, letting delivery riders exchange a depleted
            battery for a charged one in under a minute instead of waiting hours to
            recharge. In the first six months, 3,100 registered riders completed
            more than 210,000 swaps. The scheme is run jointly by the city and a
            riders' cooperative, which sets the swap price and reinvests a share of
            revenue into station maintenance.

            An independent evaluation found rider downtime fell by 38 percent and
            estimated a 12 percent drop in local delivery-fleet emissions. The city
            says two neighbouring municipalities have signed agreements to replicate
            the model next year.
            """,
        }

        print(f"\nDemo article: {demo_article['title']}")
        result = scorer.score_article(demo_article)
        print("\nResults:")
        print(f"  Passed prefilter: {result['passed_prefilter']}")
        if result["scores"]:
            for dim, score in result["scores"].items():
                print(f"    {dim}: {score:.2f}")
            print(f"  Weighted average: {result['weighted_average']:.2f}")
            print(f"  Tier: {result['tier']}")
            if result.get("gatekeeper_applied"):
                print("  Note: solution_concreteness gatekeeper applied")


if __name__ == "__main__":
    main()
