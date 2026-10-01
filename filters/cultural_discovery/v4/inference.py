"""
Cultural Discovery Filter v4 - Production Inference Pipeline

This module provides the complete inference pipeline for scoring articles
using the trained cultural discovery filter with local model files.

Pipeline: Article -> Prefilter -> Model -> Calibration -> Gatekeeper -> Tier

Usage:
    from filters.cultural_discovery.v4.inference import CulturalDiscoveryScorer
    scorer = CulturalDiscoveryScorer()
    result = scorer.score_article(article)

    # CLI
    python filters/cultural_discovery/v4/inference.py --input articles.jsonl --output results.jsonl
"""

import logging
from pathlib import Path
from typing import Optional

from filters.common.model_loading import load_lora_local
from .base_scorer import BaseCulturalDiscoveryScorer

logger = logging.getLogger(__name__)


class CulturalDiscoveryScorer(BaseCulturalDiscoveryScorer):
    """
    Production scorer for cultural discovery filter v4.

    Loads the trained LoRA model from local files and provides scoring with:
    - Optional prefiltering for efficiency
    - Per-dimension scores (5 dimensions)
    - Score calibration (isotonic regression)
    - Evidence gatekeeper logic
    - Tier assignment (high/medium/low)

    For loading from HuggingFace Hub, use CulturalDiscoveryScorerHub instead.
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        device: Optional[str] = None,
        use_prefilter: bool = False,
    ):
        # Set model path before calling super().__init__
        if model_path is None:
            model_path = Path(__file__).parent / "model"
        self.model_path = Path(model_path)

        # Initialize base class (sets device, loads prefilter)
        super().__init__(device=device, use_prefilter=use_prefilter)

        # Load the model
        self._load_model()

    def _load_model(self):
        """Load the trained LoRA model from local files."""
        self.model, self.tokenizer = load_lora_local(
            self.model_path, len(self.DIMENSION_NAMES), self.device
        )


def main():
    from filters.common.cli import run_scorer_cli
    run_scorer_cli(
        CulturalDiscoveryScorer,
        "cultural discovery filter v4",
        {
            "title": "Ancient Silk Road Temple Reveals Unexpected Buddhist-Zoroastrian Syncretism",
            "content": """
            Excavations at a 4th-century temple in Uzbekistan have uncovered evidence
            of an unprecedented religious synthesis. The site contains Buddhist statues
            with distinctly Zoroastrian fire altar iconography, suggesting practitioners
            of both faiths worshipped together during the height of Silk Road trade.

            Lead archaeologist Dr. Kamila Akhmedova noted: "We found prayer inscriptions
            in both Sanskrit and Middle Persian, side by side. This challenges our
            understanding of how these religions interacted."

            The discovery includes a ritual basin with dual symbolism - lotus motifs
            (Buddhist) surrounding a central fire receptacle (Zoroastrian). Carbon
            dating confirms continuous use over 200 years.

            Local communities are now seeking UNESCO heritage status for the site,
            which lies near modern trade routes connecting China with Central Asia.
            """
        },
    )


if __name__ == "__main__":
    main()
