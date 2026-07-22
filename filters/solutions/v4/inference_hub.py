"""
Solutions Filter v4 - HuggingFace Hub Inference

Loads the model directly from HuggingFace Hub for inference.
Use this when you don't have local model files or want to use a shared model
(this is how NexusMind production scoring loads the student — no local weights
on sadalsuud).

Usage:
    from filters.solutions.v4.inference_hub import SolutionsScorerHub

    scorer = SolutionsScorerHub(
        repo_id="jeergrvgreg/solutions-filter-v4",
        token="hf_..."  # Only needed for private repos
    )
    result = scorer.score_article(article)
"""

import logging
from typing import Optional

from filters.common.model_loading import load_lora_hub
from filters.solutions.v4.base_scorer import BaseSolutionsScorer

logger = logging.getLogger(__name__)


class SolutionsScorerHub(BaseSolutionsScorer):
    """
    Scorer that loads the model from HuggingFace Hub.

    Inherits all scoring logic from BaseSolutionsScorer (7 dims, calibration,
    solution_concreteness gatekeeper, tiering). Only implements Hub-specific
    model loading.

    For loading from local files, use SolutionsScorer (inference.py) instead.
    """

    def __init__(
        self,
        repo_id: str = "jeergrvgreg/solutions-filter-v4",
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
        """Load the LoRA model from HuggingFace Hub."""
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

    print("Loading solutions scorer from HuggingFace Hub...")
    scorer = SolutionsScorerHub(token=token)

    demo_article = {
        "title": "City rolls out battery-swap stations for delivery riders",
        "content": """
        The municipal transport authority has installed 42 battery-swap stations
        across the city, letting delivery riders exchange a depleted battery for a
        charged one in under a minute. In the first six months, 3,100 registered
        riders completed more than 210,000 swaps. An independent evaluation found
        rider downtime fell by 38 percent and estimated a 12 percent drop in local
        delivery-fleet emissions. Two neighbouring municipalities have signed
        agreements to replicate the model next year.
        """,
    }

    print(f"\nScoring demo article: {demo_article['title']}")
    result = scorer.score_article(demo_article)

    print("\nResults:")
    print(f"  Passed prefilter: {result['passed_prefilter']}")
    if result["scores"]:
        print("  Scores:")
        for dim, score in result["scores"].items():
            print(f"    {dim}: {score:.2f}")
        print(f"  Weighted average: {result['weighted_average']:.2f}")
        print(f"  Tier: {result['tier']}")


if __name__ == "__main__":
    main()
