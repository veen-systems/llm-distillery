"""
Thriving Content Filter v1 - HuggingFace Hub Inference

Loads the model directly from HuggingFace Hub for inference.
Use this when you don't have local model files or want to use a shared model.

Usage:
    from filters.thriving.v1.inference_hub import ThrivingScorerHub

    scorer = ThrivingScorerHub(
        repo_id="jeergrvgreg/thriving-filter-v1",
        token="hf_..."  # Only needed for private repos
    )
    result = scorer.score_article(article)
"""

import logging
from typing import Optional

import torch

from filters.common.model_loading import load_lora_hub
from filters.thriving.v1.base_scorer import BaseThrivingScorer

logger = logging.getLogger(__name__)


class ThrivingScorerHub(BaseThrivingScorer):
    """
    Scorer that loads model from HuggingFace Hub.

    Inherits all scoring logic from BaseThrivingScorer.
    Only implements Hub-specific model loading.

    For loading from local files, use ThrivingScorer instead.
    """

    def __init__(
        self,
        repo_id: str = "jeergrvgreg/thriving-filter-v1",
        token: Optional[str] = None,
        device: Optional[str] = None,
        use_prefilter: bool = False,
        torch_dtype=None,
    ):
        """
        Initialize scorer from HuggingFace Hub.

        Args:
            repo_id: HuggingFace repo ID (e.g., "username/model-name")
            token: HuggingFace token (required for private repos)
            device: Device to use ('cuda', 'cpu', or None for auto)
            use_prefilter: Whether to apply prefilter
            torch_dtype: Model dtype (e.g., torch.float16). If None, uses model
                default. Use torch.float16 as workaround on hardware without
                bfloat16 support.
        """
        self.repo_id = repo_id
        self.token = token
        self.torch_dtype = torch_dtype

        super().__init__(device=device, use_prefilter=use_prefilter)
        self._load_model()

    def _load_model(self):
        """Load model from HuggingFace Hub."""
        self.model, self.tokenizer = load_lora_hub(
            self.repo_id, len(self.DIMENSION_NAMES), self.device,
            token=self.token, torch_dtype=self.torch_dtype,
        )


def main():
    """Demo loading from HuggingFace Hub."""
    import os

    token = os.environ.get("HF_TOKEN")
    if not token:
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read("config/credentials/secrets.ini")
            token = config.get("api_keys", "huggingface_token", fallback=None)
        except Exception:
            pass

    print("Loading thriving scorer from HuggingFace Hub...")
    scorer = ThrivingScorerHub(token=token)

    demo_article = {
        "title": "Community Garden Feeds 500 Families in Food Desert",
        "content": """
        A volunteer-led community garden in Detroit has grown to feed over 500 families
        in what was previously a food desert. The project, started three years ago on
        abandoned lots, now spans 2 acres and produces 10,000 pounds of fresh vegetables
        annually. Local residents volunteer their time, and all produce is distributed
        free to neighborhood families.
        """
    }

    print(f"\nScoring demo article: {demo_article['title']}")
    result = scorer.score_article(demo_article)

    print(f"\nResults:")
    print(f"  Passed prefilter: {result['passed_prefilter']}")
    if result['scores']:
        print(f"  Scores:")
        for dim, score in result['scores'].items():
            print(f"    {dim}: {score:.2f}")
        print(f"  Weighted average: {result['weighted_average']:.2f}")
        print(f"  Tier: {result['tier']}")


if __name__ == "__main__":
    main()
