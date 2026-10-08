"""
Belonging Filter v1 - Production Inference Pipeline

Scores articles for evidence of genuine belonging: social fabric, rootedness,
and intergenerational continuity that cannot be purchased or optimized.

Pipeline: Article -> Prefilter -> Model -> Calibration -> Gatekeeper -> Tier

Usage:
    # Python API
    from filters.belonging.v3.inference import BelongingScorer
    scorer = BelongingScorer()
    result = scorer.score_article(article)

    # CLI
    python filters/belonging/v3/inference.py --input articles.jsonl --output results.jsonl
"""

import json
import logging
from pathlib import Path
from typing import Optional

from filters.common.model_loading import load_lora_local
from filters.belonging.v3.base_scorer import BaseBelongingScorer

logger = logging.getLogger(__name__)


class BelongingScorer(BaseBelongingScorer):
    """
    Production scorer for belonging filter v1.

    Loads the trained LoRA model from local files and provides scoring with:
    - Optional prefiltering for efficiency
    - Per-dimension scores (6 dimensions)
    - Score calibration (isotonic regression)
    - Community fabric gatekeeper logic
    - Tier assignment (high/medium/low)

    For loading from HuggingFace Hub, use BelongingScorerHub instead.
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
        description="Score articles with belonging filter v1"
    )
    parser.add_argument("--input", "-i", type=Path, help="Input JSONL file with articles")
    parser.add_argument("--output", "-o", type=Path, help="Output JSONL file for results")
    parser.add_argument("--no-prefilter", action="store_true", help="No effect: per-lens prefilters were deleted (NexusMind#284, decision 0); kept so old invocations still parse")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size for inference")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    scorer = BelongingScorer(use_prefilter=False)

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
            "title": "The Last Weaver: How One Village Keeps a 400-Year Tradition Alive",
            "content": """
            In a small village in Oaxaca, 78-year-old Elena Vasquez rises before dawn
            to prepare her loom. Her granddaughter Maria, 14, sits beside her — as she
            has every morning since she was six. "My grandmother taught me," Elena says,
            "and her grandmother taught her. The patterns carry our history."

            The village of San Marcos has practiced backstrap weaving for over four
            centuries. Unlike tourist-facing workshops in the city, this tradition
            remains embedded in daily life. Neighbors share dye recipes; young mothers
            weave while watching each other's children. When a family needs money,
            the community orders from them first.

            Maria has turned down a scholarship to a design school in Mexico City.
            "Everything I need to learn is here," she says. Her teacher agrees:
            "The city teaches you to make things. Here we teach you to be someone."
            """
        }

        print(f"\nDemo article: {demo_article['title']}")
        result = scorer.score_article(demo_article)
        print(f"\nResults:")
        print(f"  Passed prefilter: {result['passed_prefilter']}")
        if result["scores"]:
            for dim, score in result["scores"].items():
                print(f"    {dim}: {score:.2f}")
            print(f"  Weighted average: {result['weighted_average']:.2f}")
            print(f"  Tier: {result['tier']}")
            if result.get("gatekeeper_applied"):
                print(f"  Note: Community fabric gatekeeper applied")


if __name__ == "__main__":
    main()
