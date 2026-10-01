"""
Cultural Discovery v1 - Production Inference Pipeline

This module provides the complete inference pipeline for scoring articles
using the trained cultural_discovery filter with local model files.

Pipeline: Article -> Prefilter -> Model -> Gatekeeper -> Tier

Usage:
    # Python API
    from filters.cultural_discovery.v1.inference import CulturalDiscoveryScorer

    scorer = CulturalDiscoveryScorer()
    result = scorer.score_article(article)

    # CLI
    python filters/cultural-discovery/v1/inference.py --input articles.jsonl --output results.jsonl
"""

import json
import logging
from pathlib import Path
from typing import Optional

from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Suppress the "should TRAIN this model" warning - we load trained weights from LoRA adapter
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)
from peft import PeftConfig, get_peft_model
from safetensors.torch import load_file

# Import base class (handle hyphen in path via importlib)
import importlib.util
_base_path = Path(__file__).parent / "base_scorer.py"
_spec = importlib.util.spec_from_file_location("base_scorer", _base_path)
_base_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base_module)
BaseCulturalDiscoveryScorer = _base_module.BaseCulturalDiscoveryScorer

logger = logging.getLogger(__name__)


class CulturalDiscoveryScorer(BaseCulturalDiscoveryScorer):
    """
    Production scorer for cultural_discovery v1 filter.

    Loads the trained LoRA model from local files and provides scoring with:
    - Optional prefiltering for efficiency
    - Per-dimension scores (5 dimensions)
    - Evidence quality gatekeeper logic
    - Tier assignment (high/medium/low)

    For loading from HuggingFace Hub, use CulturalDiscoveryScorerHub instead.
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        device: Optional[str] = None,
        use_prefilter: bool = False,
    ):
        """
        Initialize the scorer with local model files.

        Args:
            model_path: Path to model directory (default: ./model)
            device: Device to use ('cuda', 'cpu', or None for auto)
            use_prefilter: Whether to apply prefilter before scoring
        """
        # Set model path before calling super().__init__
        if model_path is None:
            model_path = Path(__file__).parent / "model"
        self.model_path = Path(model_path)

        # Initialize base class (sets device, loads prefilter)
        super().__init__(device=device, use_prefilter=use_prefilter)

        # Load the model
        self._load_model()

    def _load_model(self):
        """
        Load the trained LoRA model from local files.

        Raises:
            FileNotFoundError: If model files not found
            RuntimeError: If model loading fails
        """
        # Validate model path exists
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model directory not found: {self.model_path}\n"
                f"Please ensure the model is trained and saved."
            )

        adapter_path = self.model_path / "adapter_model.safetensors"
        if not adapter_path.exists():
            raise FileNotFoundError(
                f"Adapter weights not found: {adapter_path}\n"
                f"Please ensure the model training completed successfully."
            )

        try:
            logger.info(f"Loading model from {self.model_path}")
            logger.info(f"Device: {self.device}")
            print(f"Loading model from {self.model_path}")
            print(f"Device: {self.device}")

            # Load PEFT config
            peft_config = PeftConfig.from_pretrained(str(self.model_path))
            base_model_name = peft_config.base_model_name_or_path

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(base_model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Load base model
            base_model = AutoModelForSequenceClassification.from_pretrained(
                base_model_name,
                num_labels=len(self.DIMENSION_NAMES),
                problem_type="regression",
            )

            if base_model.config.pad_token_id is None:
                base_model.config.pad_token_id = self.tokenizer.pad_token_id

            # Create PEFT model
            self.model = get_peft_model(base_model, peft_config)

            # Load adapter weights
            adapter_state_dict = load_file(str(adapter_path))

            # Remap keys for PEFT compatibility
            # PEFT expects ".default" suffix after lora_A/lora_B weights
            remapped = {}
            for key, value in adapter_state_dict.items():
                if ".lora_A.weight" in key or ".lora_B.weight" in key:
                    new_key = key.replace(".lora_A.weight", ".lora_A.default.weight")
                    new_key = new_key.replace(".lora_B.weight", ".lora_B.default.weight")
                    remapped[new_key] = value
                elif key == "base_model.model.score.weight":
                    remapped["base_model.model.score.modules_to_save.default.weight"] = value
                elif key == "base_model.model.score.bias":
                    remapped["base_model.model.score.modules_to_save.default.bias"] = value
                else:
                    remapped[key] = value

            self.model.load_state_dict(remapped, strict=False)
            self.model = self.model.to(self.device)
            self.model.eval()

            logger.info("Model loaded successfully")
            print("Model loaded successfully")

        except FileNotFoundError:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {type(e).__name__}: {e}")


def main():
    """CLI interface for batch scoring."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Score articles with cultural_discovery filter"
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

    # Initialize scorer
    print("Initializing scorer...")
    scorer = CulturalDiscoveryScorer(use_prefilter=False)

    if args.input:
        # Score from file
        print(f"Loading articles from {args.input}")
        articles = []
        with open(args.input, "r", encoding="utf-8") as f:
            for line in f:
                articles.append(json.loads(line))

        print(f"Scoring {len(articles)} articles...")
        results = scorer.score_batch(articles, batch_size=args.batch_size)

        # Output
        if args.output:
            print(f"Writing results to {args.output}")
            with open(args.output, "w", encoding="utf-8") as f:
                for article, result in zip(articles, results):
                    article_id = article.get("id") or article.get("article_id", "")
                    output = {"article_id": article_id, **result}
                    f.write(json.dumps(output) + "\n")
        else:
            # Print summary
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
        # Interactive demo
        print("\n--- Interactive Demo ---")
        demo_article = {
            "title": "Ancient Maya Temple Discovered with Cross-Cultural Murals",
            "content": """
            Archaeologists in Guatemala have unearthed a 2,500-year-old Maya temple containing
            murals that depict artistic styles from both local Maya traditions and distant
            Olmec influences. The discovery, published in the Journal of Archaeological Science,
            suggests extensive pre-Columbian cultural exchange networks.

            Lead researcher Dr. Maria Santos from the University of Pennsylvania spent 12 years
            following local oral traditions to locate the site. "The murals show a sophistication
            of cross-cultural artistic dialogue we hadn't documented before," she said.

            The temple's preservation was aided by a collapsed roof that sealed the interior
            for millennia. Carbon dating confirmed the site predates previously known examples
            of Maya-Olmec artistic synthesis by several centuries.

            Local indigenous communities have been partners in the excavation, sharing traditional
            knowledge that helped interpret symbolic elements in the murals. The findings will
            be displayed at the National Museum of Archaeology, with replicas returning to the
            communities involved in the discovery.
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
                print(f"  Note: Evidence quality gatekeeper applied")


if __name__ == "__main__":
    main()
