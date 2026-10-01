"""
Investment Risk Filter v6 - HuggingFace Hub Inference

Loads the model directly from HuggingFace Hub for inference.
Use this when you don't have local model files or want to use a shared model.

Usage:
    from filters.investment_risk.v6.inference_hub import InvestmentRiskScorerHub
    scorer = InvestmentRiskScorerHub(
        repo_id="jeergrvgreg/investment-risk-filter-v6",
        token="hf_..."  # Only needed for private repos
    )
    result = scorer.score_article(article)
"""

import json
import logging
from pathlib import Path
from typing import Optional

import torch

from filters.common.model_loading import load_lora_hub
from .base_scorer import BaseInvestmentRiskScorer

logger = logging.getLogger(__name__)


class InvestmentRiskScorerHub(BaseInvestmentRiskScorer):
    """
    Scorer that loads model from HuggingFace Hub.

    Inherits all scoring logic from BaseInvestmentRiskScorer.
    Only implements Hub-specific model loading.

    For loading from local files, use InvestmentRiskScorer instead.
    """

    def __init__(
        self,
        repo_id: str = "jeergrvgreg/investment-risk-filter-v6",
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

        # Initialize base class (sets device, loads prefilter)
        super().__init__(device=device, use_prefilter=use_prefilter)

        # Load the model from Hub
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

    # Get token from environment or secrets
    token = os.environ.get("HF_TOKEN")
    if not token:
        # Try loading from secrets.ini
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read("config/credentials/secrets.ini")
            token = config.get("api_keys", "huggingface_token", fallback=None)
        except Exception:
            pass

    print("Loading investment-risk scorer from HuggingFace Hub...")
    scorer = InvestmentRiskScorerHub(token=token)

    # Demo article
    demo_article = {
        "title": "Fed Signals Rate Cuts May Come Later Than Expected Amid Sticky Inflation",
        "content": """
        Federal Reserve officials indicated Wednesday that interest rate cuts
        could be delayed until later in 2025 as inflation remains stubbornly
        above the central bank's 2% target. The latest FOMC minutes revealed
        concerns about persistent price pressures in services and housing.

        Markets had been pricing in cuts as early as March, but traders are
        now adjusting expectations. The S&P 500 fell 1.2% following the release.
        Bond yields rose as investors recalibrated their outlook.

        For retail investors, this suggests maintaining a defensive posture
        and avoiding long-duration bonds until the path becomes clearer.
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
