"""
Belonging Filter v1 - HuggingFace Hub Inference

Loads the model directly from HuggingFace Hub for inference.
Use this when you don't have local model files or want to use a shared model.

Usage:
    from filters.belonging.v1.inference_hub import BelongingScorerHub

    scorer = BelongingScorerHub(
        repo_id="jeergrvgreg/belonging-filter-v1",
        token="hf_..."  # Only needed for private repos
    )
    result = scorer.score_article(article)
"""

import logging
from typing import Optional

import torch

from filters.common.model_loading import load_lora_hub
from filters.belonging.v1.base_scorer import BaseBelongingScorer

logger = logging.getLogger(__name__)


class BelongingScorerHub(BaseBelongingScorer):
    """
    Scorer that loads model from HuggingFace Hub.

    Inherits all scoring logic from BaseBelongingScorer.
    Only implements Hub-specific model loading.

    For loading from local files, use BelongingScorer instead.
    """

    def __init__(
        self,
        repo_id: str = "jeergrvgreg/belonging-filter-v1",
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

    print("Loading belonging scorer from HuggingFace Hub...")
    scorer = BelongingScorerHub(token=token)

    demo_article = {
        "title": "The Last Weaver: How One Village Keeps a 400-Year Tradition Alive",
        "content": """
        In a small village in Oaxaca, 78-year-old Elena Vasquez rises before dawn
        to prepare her loom. Her granddaughter Maria, 14, sits beside her — as she
        has every morning since she was six. "My grandmother taught me," Elena says,
        "and her grandmother taught her. The patterns carry our history."
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
