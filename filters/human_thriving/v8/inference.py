"""
Human Thriving Filter v8 - Local Inference Pipeline

Pipeline: Article -> Model -> Gatekeeper -> Calibration -> Tier

⛔ NO PREFILTER STAGE. v8 ships no per-lens keyword prefilter (ADR-018/019
*Amendment 2026-08-21*); Stage-1 screening is the multilingual e5 probe, reached
through `inference_hybrid.py`, not through this module. `use_prefilter` therefore
defaults to False here, and passing True raises rather than silently doing nothing.

⚠️ The model weights are NOT in this repo (#97, gitignored). They live on b650-gpu at
`~/llm-distillery/filters/human_thriving/v8/model/`. Constructing this scorer without
them raises FileNotFoundError from `load_lora_local`.

Usage:
    from filters.human_thriving.v8.inference import HumanThrivingScorer

    scorer = HumanThrivingScorer()
    result = scorer.score_article(article)

    python filters/human_thriving/v8/inference.py --input articles.jsonl --output out.jsonl
"""

import json
import logging
from pathlib import Path
from typing import Optional

from filters.common.model_loading import load_lora_local
from filters.human_thriving.v8.base_scorer import BaseHumanThrivingScorer

logger = logging.getLogger(__name__)


class HumanThrivingScorer(BaseHumanThrivingScorer):
    """
    Local-files scorer for human_thriving v8.

    - Per-dimension scores (6 orthogonal dimensions, weights in base_scorer)
    - Evidence gatekeeper (evidence_level < 3 caps the weighted average at 3.0)
    - Isotonic calibration when calibration.json is present (auto-loaded by the base)
    - Tier assignment from TIER_THRESHOLDS (medium = 4.5)
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
        """Load the trained LoRA adapter from local files (old key format, #97)."""
        self.model, self.tokenizer = load_lora_local(
            self.model_path, len(self.DIMENSION_NAMES), self.device
        )


def main():
    """CLI interface for batch scoring."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Score articles with the human_thriving v8 filter"
    )
    parser.add_argument("--input", "-i", type=Path, help="Input JSONL file with articles")
    parser.add_argument("--output", "-o", type=Path, help="Output JSONL file for results")
    parser.add_argument("--model-path", type=Path, default=None, help="Override model dir")
    parser.add_argument("--device", type=str, default=None, help="cpu or cuda")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    args = parser.parse_args()

    if not args.input:
        parser.error("--input is required")

    scorer = HumanThrivingScorer(model_path=args.model_path, device=args.device)

    articles = []
    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                articles.append(json.loads(line))

    print(f"Scoring {len(articles)} articles on {scorer.device}...")
    results = scorer.score_batch(articles, batch_size=args.batch_size)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            for article, result in zip(articles, results):
                article_id = article.get("id") or article.get("article_id", "")
                f.write(json.dumps({"article_id": article_id, **result}) + "\n")
        print(f"Wrote {len(results)} results to {args.output}")
    else:
        tiers = {}
        for r in results:
            if r.get("tier"):
                tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1
        print("Tier distribution:")
        for tier, count in sorted(tiers.items()):
            print(f"  {tier}: {count}")


if __name__ == "__main__":
    main()
