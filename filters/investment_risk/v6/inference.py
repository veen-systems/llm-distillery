"""
Investment Risk Filter v6 - Production Inference Pipeline

This module provides the complete inference pipeline for scoring articles
using the trained investment risk filter with local model files.

Pipeline: Article -> Prefilter -> Model -> Calibration -> Gatekeeper -> Tier

Usage:
    from filters.investment_risk.v6.inference import InvestmentRiskScorer
    scorer = InvestmentRiskScorer()
    result = scorer.score_article(article)

    # CLI
    python filters/investment_risk/v6/inference.py --input articles.jsonl --output results.jsonl
"""

import logging
from pathlib import Path
from typing import Optional

from filters.common.model_loading import load_lora_local
from .base_scorer import BaseInvestmentRiskScorer

logger = logging.getLogger(__name__)


class InvestmentRiskScorer(BaseInvestmentRiskScorer):
    """
    Production scorer for investment risk filter v6.

    Loads the trained LoRA model from local files and provides scoring with:
    - Optional prefiltering for efficiency
    - Per-dimension scores (6 orthogonal dimensions)
    - Score calibration (isotonic regression)
    - Evidence gatekeeper logic
    - Tier assignment (high/medium/low)

    For loading from HuggingFace Hub, use InvestmentRiskScorerHub instead.
    """

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
        """Load the trained LoRA model from local files."""
        self.model, self.tokenizer = load_lora_local(
            self.model_path, len(self.DIMENSION_NAMES), self.device
        )


def main():
    from filters.common.cli import run_scorer_cli
    run_scorer_cli(
        InvestmentRiskScorer,
        "investment risk filter v6",
        {
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
        },
    )


if __name__ == "__main__":
    main()
