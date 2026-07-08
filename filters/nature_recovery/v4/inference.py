"""
Nature Recovery Filter v2 - Production Inference Pipeline

Scores articles for evidence of measurable ecosystem recovery:
species rebounds, habitat restoration, pollution reversal.

Pipeline: Article -> Prefilter -> Model -> Calibration -> Gatekeeper -> Tier

Usage:
    # Python API
    from filters.nature_recovery.v2.inference import NatureRecoveryScorer
    scorer = NatureRecoveryScorer()
    result = scorer.score_article(article)

    # CLI
    python filters/nature_recovery/v2/inference.py --input articles.jsonl --output results.jsonl
"""

import json
import logging
from pathlib import Path
from typing import Optional

from filters.common.model_loading import load_lora_local
from filters.nature_recovery.v2.base_scorer import BaseNatureRecoveryScorer

logger = logging.getLogger(__name__)


class NatureRecoveryScorer(BaseNatureRecoveryScorer):
    """
    Production scorer for nature recovery filter v1.

    Loads the trained LoRA model from local files and provides scoring with:
    - Optional prefiltering for efficiency
    - Per-dimension scores (6 dimensions)
    - Score calibration (isotonic regression)
    - Recovery evidence gatekeeper logic
    - Tier assignment (high/medium/low)

    For loading from HuggingFace Hub, use NatureRecoveryScorerHub instead.
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

    parser = argparse.ArgumentParser(
        description="Score articles with nature recovery filter v1"
    )
    parser.add_argument("--input", "-i", type=Path, help="Input JSONL file with articles")
    parser.add_argument("--output", "-o", type=Path, help="Output JSONL file for results")
    parser.add_argument("--no-prefilter", action="store_true", help="Skip prefilter")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size for inference")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    scorer = NatureRecoveryScorer(use_prefilter=not args.no_prefilter)

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
            "title": "Wolves Return to Yellowstone: 25 Years of Ecosystem Recovery",
            "content": """
            Twenty-five years after wolves were reintroduced to Yellowstone National
            Park, the results have exceeded all expectations. Elk populations have
            stabilized, allowing willow and aspen groves to regenerate along stream
            banks. Beaver colonies, which depend on these trees, have increased from
            one to twelve. The beavers' dams have created ponds that support fish,
            amphibians, and songbirds not seen in the park for decades.

            Researchers measured a 43% increase in riparian vegetation cover and a
            significant reduction in stream bank erosion. "This is a textbook trophic
            cascade," says lead ecologist Dr. Sarah Chen. "One species triggered
            recovery across the entire ecosystem."
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
                print(f"  Note: Recovery evidence gatekeeper applied")


if __name__ == "__main__":
    main()
