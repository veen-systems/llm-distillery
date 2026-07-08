"""
Nature Recovery Filter v2 - HuggingFace Hub Inference

Loads the model directly from HuggingFace Hub for inference.
Use this when you don't have local model files or want to use a shared model.

Usage:
    from filters.nature_recovery.v2.inference_hub import NatureRecoveryScorerHub

    scorer = NatureRecoveryScorerHub(
        repo_id="jeergrvgreg/nature-recovery-filter-v2",
        token="hf_..."  # Only needed for private repos
    )
    result = scorer.score_article(article)
"""

import logging
from typing import Optional

import torch

from filters.common.model_loading import load_lora_hub
from filters.nature_recovery.v2.base_scorer import BaseNatureRecoveryScorer

logger = logging.getLogger(__name__)


class NatureRecoveryScorerHub(BaseNatureRecoveryScorer):
    """
    Scorer that loads model from HuggingFace Hub.

    Inherits all scoring logic from BaseNatureRecoveryScorer.
    Only implements Hub-specific model loading.

    For loading from local files, use NatureRecoveryScorer instead.
    """

    def __init__(
        self,
        repo_id: str = "jeergrvgreg/nature-recovery-filter-v2",
        token: Optional[str] = None,
        device: Optional[str] = None,
        use_prefilter: bool = True,
        torch_dtype=None,
    ):
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

    print("Loading nature recovery scorer from HuggingFace Hub...")
    scorer = NatureRecoveryScorerHub(token=token)

    demo_article = {
        "title": "Wolves Return to Yellowstone: 25 Years of Ecosystem Recovery",
        "content": """
        Twenty-five years after wolves were reintroduced to Yellowstone National
        Park, the results have exceeded all expectations. Elk populations have
        stabilized, allowing willow and aspen groves to regenerate along stream banks.
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
