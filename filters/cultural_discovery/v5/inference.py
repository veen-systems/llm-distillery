"""
Cultural Discovery Filter v5 - Production Inference Pipeline

Loads the trained LoRA adapter from local files and scores articles through:
Article -> Prefilter -> Model -> Calibration -> Gatekeeper -> Tier

Usage:
    from filters.cultural_discovery.v5.inference import CulturalDiscoveryScorer
    scorer = CulturalDiscoveryScorer()
    result = scorer.score_article(article)

    # CLI
    python filters/cultural_discovery/v5/inference.py --input articles.jsonl --output results.jsonl
"""

import logging
from pathlib import Path
from typing import Optional

from filters.common.model_loading import load_lora_local
from .base_scorer import BaseCulturalDiscoveryScorer

logger = logging.getLogger(__name__)


class CulturalDiscoveryScorer(BaseCulturalDiscoveryScorer):
    """Production scorer for cultural discovery v5 (local-file model load)."""

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
        self.model, self.tokenizer = load_lora_local(
            self.model_path, len(self.DIMENSION_NAMES), self.device
        )


def main():
    from filters.common.cli import run_scorer_cli
    run_scorer_cli(
        CulturalDiscoveryScorer,
        "cultural discovery filter v5",
        {
            "title": "Ancient Silk Road Temple Reveals Unexpected Buddhist-Zoroastrian Syncretism",
            "content": (
                "Excavations at a 4th-century temple in Uzbekistan have uncovered evidence "
                "of an unprecedented religious synthesis. The site contains Buddhist statues "
                "with distinctly Zoroastrian fire altar iconography, suggesting practitioners "
                "of both faiths worshipped together during the height of Silk Road trade. "
                "Lead archaeologist Dr. Kamila Akhmedova noted: 'We found prayer inscriptions "
                "in both Sanskrit and Middle Persian, side by side. This challenges our "
                "understanding of how these religions interacted.'"
            ),
        },
    )


if __name__ == "__main__":
    main()
