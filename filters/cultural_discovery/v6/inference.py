"""
Cultural Discovery Filter v6 - Production Inference Pipeline

Loads the trained LoRA adapter from local files and scores articles through:
Article -> Prefilter -> Model -> Calibration -> Tier

THE MODEL IS v5's, UNCHANGED. v6 is an architecture migration (#98), not a
retrain: the student weights, dimensions, weights, and op-point are identical to
v5. What changed is that topic screening moved from 453 keyword stems to a
multilingual e5 probe (see inference_hybrid.py), and the rule prefilter was
reduced to a commerce-only pass-through. The dimension/op-point strand is #87.

Consequences worth holding onto:
  - `calibration.json` here is byte-identical to v5's, and that is CORRECT — a
    calibration maps a specific model's logits to scores, and the model did not
    change. If the student is ever retrained, this file must be refitted.
  - There is deliberately NO `normalization.json`. A fresh version ships without
    one (ADR-014, docs/FILTER_PLAYBOOK.md §6), and v5's cannot be inherited even
    though the student is the same: the probe now screens most of the firehose
    BEFORE the student runs, so the surviving population — and therefore the
    production CDF — is not v5's.

Usage:
    from filters.cultural_discovery.v6.inference import CulturalDiscoveryScorer
    scorer = CulturalDiscoveryScorer()
    result = scorer.score_article(article)

    # CLI
    python filters/cultural_discovery/v6/inference.py --input articles.jsonl --output results.jsonl
"""

import logging
from pathlib import Path
from typing import Optional

from filters.common.model_loading import load_lora_local
from .base_scorer import BaseCulturalDiscoveryScorer

logger = logging.getLogger(__name__)


class CulturalDiscoveryScorer(BaseCulturalDiscoveryScorer):
    """Production scorer for cultural discovery v6 (local-file model load)."""

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
        self.model, self.tokenizer = load_lora_local(
            self.model_path, len(self.DIMENSION_NAMES), self.device
        )


def main():
    from filters.common.cli import run_scorer_cli
    run_scorer_cli(
        CulturalDiscoveryScorer,
        "cultural discovery filter v6",
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
