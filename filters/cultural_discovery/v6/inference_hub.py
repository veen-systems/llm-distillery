"""
Cultural Discovery Filter v6 - HuggingFace Hub Inference

Loads the model directly from HuggingFace Hub for inference. This is cd's normal
path — unlike nature_recovery v4, cultural_discovery ships no local `model/`
directory, so this module (not inference.py) is what production uses.

PREREQUISITE BEFORE CUTOVER — the v6 Hub repo does not exist yet
----------------------------------------------------------------
`jeergrvgreg/cultural-discovery-filter-v6` must be created by copying the v5
adapter verbatim. **There is no retrain in v6** (#98 is an architecture
migration); the weights are byte-identical to
`jeergrvgreg/cultural-discovery-filter-v5`.

Why a duplicate repo rather than pointing at v5's:
`scripts/deployment/verify_filter_package.py` requires the default `repo_id` to
end in `-v{N}` matching the directory. That guard exists because of #44 — three
days of production scoring against v_new config x v_old weights. Pointing v6 at
the v5 repo is *literally* that configuration, even though here it is
intentional, and defeating the guard to express an intention is how the guard
stops working for the case where it is not intentional. A v6 repo makes the
provenance unambiguous instead.

Upload with the OLD PEFT key format (`.lora_A.weight` / `score.weight`). Never
run resave_adapter.py first — it breaks PeftModel.from_pretrained() (ADR-007).

Usage:
    from filters.cultural_discovery.v6.inference_hub import CulturalDiscoveryScorerHub
    scorer = CulturalDiscoveryScorerHub(
        repo_id="jeergrvgreg/cultural-discovery-filter-v6",
        token="hf_..."  # Only needed for private repos
    )
    result = scorer.score_article(article)
"""

import logging
from typing import Optional

from filters.common.model_loading import load_lora_hub
from .base_scorer import BaseCulturalDiscoveryScorer

logger = logging.getLogger(__name__)


class CulturalDiscoveryScorerHub(BaseCulturalDiscoveryScorer):
    """
    Scorer that loads model from HuggingFace Hub.

    Inherits all scoring logic from BaseCulturalDiscoveryScorer.
    Only implements Hub-specific model loading.

    For loading from local files, use CulturalDiscoveryScorer instead.
    """

    def __init__(
        self,
        repo_id: str = "jeergrvgreg/cultural-discovery-filter-v6",
        token: Optional[str] = None,
        device: Optional[str] = None,
        use_prefilter: bool = True,
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

    print("Loading cultural discovery scorer from HuggingFace Hub...")
    scorer = CulturalDiscoveryScorerHub(token=token)

    # Demo article
    demo_article = {
        "title": "Ancient Silk Road Temple Reveals Unexpected Buddhist-Zoroastrian Syncretism",
        "content": """
        Excavations at a 4th-century temple in Uzbekistan have uncovered evidence
        of an unprecedented religious synthesis. The site contains Buddhist statues
        with distinctly Zoroastrian fire altar iconography, suggesting practitioners
        of both faiths worshipped together during the height of Silk Road trade.
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
