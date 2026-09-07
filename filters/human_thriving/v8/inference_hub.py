"""
Human Thriving Filter v8 - HuggingFace Hub Inference

Loads the LoRA adapter directly from HuggingFace Hub. This is how NexusMind
production scoring reaches the student: sadalsuud holds no weights, and
`deploy_filters.sh` excludes every `model/` directory from both rsync passes,
so the code path that ships is this one.

Pipeline: Article -> Model -> Gatekeeper -> Calibration -> Tier

⛔ NO PREFILTER STAGE. v8 ships no per-lens keyword prefilter (ADR-018/019
*Amendment 2026-08-21*); Stage-1 screening is the multilingual e5 probe, reached
through `inference_hybrid.py`, not through this module. `use_prefilter` therefore
defaults to False here, matching `inference.py`.

⚠️ The repo is PRIVATE, so `repo_info()` returns 404 rather than 403 for a token
that cannot see it — a missing token reads as "repo not found", not as an auth
error. Pass one.

Usage:
    from filters.human_thriving.v8.inference_hub import HumanThrivingScorerHub

    scorer = HumanThrivingScorerHub(
        repo_id="jeergrvgreg/human-thriving-filter-v8",
        token="hf_...",  # required: the repo is private
    )
    result = scorer.score_article(article)
"""

import logging
from typing import Optional

from filters.common.model_loading import load_lora_hub
from filters.human_thriving.v8.base_scorer import BaseHumanThrivingScorer

logger = logging.getLogger(__name__)


class HumanThrivingScorerHub(BaseHumanThrivingScorer):
    """
    Scorer that loads the model from HuggingFace Hub.

    Inherits all scoring logic from BaseHumanThrivingScorer (6 dimensions, the
    evidence_level gatekeeper capping the weighted average at 3.0, isotonic
    calibration auto-loaded from calibration.json, tier assignment from
    TIER_THRESHOLDS with medium = 4.5). Only Hub-specific model loading is
    implemented here.

    For loading from local files, use HumanThrivingScorer (inference.py) instead.
    """

    def __init__(
        self,
        repo_id: str = "jeergrvgreg/human-thriving-filter-v8",
        token: Optional[str] = None,
        device: Optional[str] = None,
        use_prefilter: bool = False,
        torch_dtype=None,
    ):
        self.repo_id = repo_id
        self.token = token
        self.torch_dtype = torch_dtype

        super().__init__(device=device, use_prefilter=use_prefilter)
        self._load_model()

    def _load_model(self):
        """Load the LoRA adapter from HuggingFace Hub.

        ⚠️ OLD PEFT key format (`.lora_A.weight` / `score.weight`) — a CLAUDE.md
        Hard Constraint, see `memory/gemma3-model.md`. Never run
        `resave_adapter.py` against this repo: it rewrites the keys into the new
        format and breaks `PeftModel.from_pretrained()`.
        """
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

    print("Loading human_thriving scorer from HuggingFace Hub...")
    scorer = HumanThrivingScorerHub(token=token)

    demo_article = {
        "title": "Community land trust brings 180 vacant homes back into use",
        "content": """
        A resident-led land trust has restored and re-let 180 long-vacant homes in
        the city's eastern districts, housing 412 people who had been on the waiting
        list for more than two years. Rents are set at 28 percent of median local
        income and are held there by the trust's charter, which requires a two-thirds
        member vote to change. An independent housing researcher tracked the first
        cohort for eighteen months and found 94 percent still housed, with reported
        financial stress down sharply against a matched comparison group. Two
        neighbouring councils have since adopted the trust's governance model.
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
