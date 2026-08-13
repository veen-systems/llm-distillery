"""
Cultural Discovery Filter v6 - Hybrid Inference Pipeline

Two-stage scorer: a multilingual-e5-small probe screens (Stage 1), and the
trained Gemma-3-1B student scores what survives (Stage 2).

Stage 1 (~1.3ms): probe estimates the weighted average. Articles below threshold
are returned as LOW without running the expensive model.
Stage 2 (~25ms): full student scoring.

WHY THIS MODULE EXISTS (#98)
----------------------------
v5 screened with 453 keyword stems across ~25 languages. A stem list can only
screen languages someone wrote vocabulary for, which is the per-language gap #86
spent 2026-08-06 patching by hand. The probe screens on meaning, so it cannot
carry that gap by construction.

Measured on held-out ORACLE ground truth (n=857, 75 MEDIUM+ positives) before the
gate was removed, per ADR-021 — not asserted from the template:

    probe @ 2.50 (shipping)   FN 0/75   screens 51.2% of the split
    keyword gate (453 stems)  FN 10/75  screens 50.8%

THRESHOLD 2.50, NOT THE TRAINER'S 3.025
---------------------------------------
train_probe.py selected 3.025 by val FN-rate. That selection is optimistic by
construction — the val split shares the enriched distribution the probe was fit
on, while production is the raw firehose. At 3.025 the probe misses 5/75 on
held-out oracle labels; at 2.50 it misses none, for 13 points less screening.
For a needle filter, recall is the scarce quantity (docs/FILTER_PLAYBOOK.md §4).
Do not "restore" 3.025 without re-running the held-out comparison.

STAMPING-ONLY ON FIRST CUTOVER (ADR-022)
----------------------------------------
The rule prefilter has never run in NexusMind's scoring path (NexusMind#284), but
this probe DOES run. So v6 turns cultural_discovery's screening on for readers
for the first time — it is not a swap of two dormant mechanisms. Ship stamping
the stage and the estimate; make enforcement a separate config flip, after the
production numbers are in.

Usage:
    from filters.cultural_discovery.v6.inference_hybrid import CulturalDiscoveryHybridScorer
    scorer = CulturalDiscoveryHybridScorer()
    result = scorer.score_article(article)
    # result["stage_used"] -> "stage1_low" or "stage2"

    # CLI
    python filters/cultural_discovery/v6/inference_hybrid.py --input articles.jsonl --output results.jsonl
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from filters.common.hybrid_scorer import HybridScorer

logger = logging.getLogger(__name__)

# Stage 1 threshold. See the module docstring: measured on held-out oracle labels,
# NOT the trainer's val-selected 3.025. Mirrors config.yaml
# hybrid_inference.stage1.threshold — but THIS constant is what runs; the config
# field is documentation (same relationship as nature_recovery v4's 3.225 vs its
# runtime 0.75, #88 item 2).
DEFAULT_THRESHOLD = 2.50


class CulturalDiscoveryHybridScorer(HybridScorer):
    """
    Two-stage hybrid scorer for cultural_discovery v6.

    Stage 1: multilingual-e5-small embeddings + MLP probe (~1.3ms/article)
    Stage 2: CulturalDiscoveryScorer (Gemma-3-1B fine-tuned, ~25ms/article)

    Stage 2 loads from the Hub by DEFAULT, unlike nature_recovery v4's hybrid
    scorer. That is not a style difference — cultural_discovery ships no local
    `model/` directory and never has, so defaulting to a local path would wire
    this class to a directory that does not exist. Pass `model_path` to force the
    local loader (e.g. on gpu-server, where the weights are staged on disk).
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        probe_path: Optional[Path] = None,
        threshold: float = DEFAULT_THRESHOLD,
        device: Optional[str] = None,
        use_prefilter: bool = True,
        repo_id: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """
        Args:
            model_path: local Stage-2 model dir. Defaults to this package's own
                `model/` when an adapter is present there; the Hub loader is used
                only when no local adapter exists. Passing an explicit path still
                wins. (Before 2026-08-13 this defaulted to the Hub, which cannot
                work under HF_HUB_OFFLINE — see the note in __init__.)
            probe_path: Stage-1 probe (default: ./probe/embedding_probe_e5small.pkl)
            threshold: Stage-1 threshold; articles below it skip Stage 2
            device: 'cuda', 'cpu', or None for auto
            use_prefilter: whether to apply the rule prefilter (v6's is a
                commerce-only pass-through — see prefilter.py)
            repo_id: override the Hub repo for Stage 2
            token: HuggingFace token, for private repos
        """
        # Default to the package's OWN weights when they are on disk, so the Hub
        # is a FALLBACK rather than the default. Fixed 2026-08-13 after this
        # exact branch took the production pipeline down.
        #
        # The Hub branch cannot work where this filter actually runs: the
        # gpu-server scorer sets HF_HUB_OFFLINE via its EnvironmentFile, so any
        # Hub fetch raises OfflineModeIsEnabled regardless of token, repo
        # existence or privacy. `jeergrvgreg/cultural-discovery-filter-v6` does
        # exist and is private — verified authenticated, with controls — and that
        # is irrelevant on that box.
        #
        # cd v6 was the ONLY hybrid filter with a Hub branch at all: uplifting v7,
        # solutions v6 and nature_recovery v4 all return their local scorer
        # unconditionally, and this package's own inference.py already defaults to
        # Path(__file__).parent / "model". The hybrid path was the outlier.
        if model_path is None:
            _default = Path(__file__).parent / "model"
            if (_default / "adapter_model.safetensors").is_file():
                model_path = _default
        self._model_path = model_path
        self._probe_path = probe_path or (
            Path(__file__).parent / "probe" / "embedding_probe_e5small.pkl"
        )
        self._threshold = threshold
        self._repo_id = repo_id
        self._token = token

        # Deferred import keeps the heavy inference modules out of the import
        # chain at class-definition time (super().__init__ eagerly constructs the
        # embedding stage, but Stage 2 should stay lazy).
        from importlib import import_module
        if model_path is not None:
            self._scorer_module = import_module("filters.cultural_discovery.v6.inference")
        else:
            self._scorer_module = import_module("filters.cultural_discovery.v6.inference_hub")

        super().__init__(device=device, use_prefilter=use_prefilter)

    def _create_stage2_scorer(self):
        """Create the Stage-2 student scorer.

        Prefilter is disabled here: HybridScorer runs the prefilter itself, so
        Stage 2 must not load or run it a second time.
        """
        if self._model_path is not None:
            return self._scorer_module.CulturalDiscoveryScorer(
                model_path=self._model_path,
                device=self.device_str,
                use_prefilter=False,
            )
        kwargs = {"device": self.device_str, "use_prefilter": False, "token": self._token}
        if self._repo_id is not None:
            kwargs["repo_id"] = self._repo_id
        return self._scorer_module.CulturalDiscoveryScorerHub(**kwargs)

    def _get_embedding_stage_config(self) -> Dict:
        """Return EmbeddingStage configuration for cultural_discovery v6."""
        return {
            "embedding_model_name": "intfloat/multilingual-e5-small",
            "probe_path": str(self._probe_path),
            "threshold": self._threshold,
        }


def main():
    """CLI interface for hybrid batch scoring."""
    import argparse
    import time

    parser = argparse.ArgumentParser(
        description="Score articles with cultural_discovery v6 hybrid scorer (two-stage)"
    )
    parser.add_argument("--input", "-i", type=Path, help="Input JSONL file with articles")
    parser.add_argument("--output", "-o", type=Path, help="Output JSONL file for results")
    parser.add_argument("--no-prefilter", action="store_true", help="Skip prefilter")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size for inference")
    parser.add_argument(
        "--threshold", type=float, default=DEFAULT_THRESHOLD,
        help=f"Stage 1 threshold (default: {DEFAULT_THRESHOLD})"
    )
    parser.add_argument(
        "--model-path", type=Path, default=None,
        help="Local Stage-2 model dir; omit to load from the Hub"
    )
    args = parser.parse_args()

    print("Initializing hybrid scorer...")
    scorer = CulturalDiscoveryHybridScorer(
        model_path=args.model_path,
        threshold=args.threshold,
        use_prefilter=not args.no_prefilter,
    )

    if args.input:
        print(f"Loading articles from {args.input}")
        articles = []
        with open(args.input, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    articles.append(json.loads(line))

        print(f"Scoring {len(articles)} articles with hybrid pipeline...")
        start = time.time()
        results = scorer.score_batch(articles, batch_size=args.batch_size)
        elapsed = time.time() - start

        stage1_low = sum(1 for r in results if r.get("stage_used") == "stage1_low")
        stage2 = sum(1 for r in results if r.get("stage_used") == "stage2")
        blocked = sum(1 for r in results if not r.get("passed_prefilter", True))

        print(f"\nHybrid results ({elapsed:.2f}s):")
        print(f"  Prefilter blocked: {blocked}")
        print(f"  Stage 1 LOW (skipped model): {stage1_low}")
        print(f"  Stage 2 (full model): {stage2}")
        print(f"  Avg time per article: {elapsed / len(articles) * 1000:.1f}ms")

        tiers: Dict[str, int] = {}
        for r in results:
            tier = r.get("tier")
            if tier:
                tiers[tier] = tiers.get(tier, 0) + 1
        print("\nTier distribution:")
        for tier, count in sorted(tiers.items()):
            print(f"  {tier}: {count}")

        if args.output:
            print(f"\nWriting results to {args.output}")
            with open(args.output, "w", encoding="utf-8") as f:
                for article, result in zip(articles, results):
                    article_id = article.get("id") or article.get("article_id", "")
                    f.write(json.dumps({"article_id": article_id, **result}) + "\n")
    else:
        print("\n--- Hybrid Scorer Demo ---")
        demo_article = {
            "title": "Ancient Silk Road Temple Reveals Unexpected Buddhist-Zoroastrian Syncretism",
            "content": (
                "Excavations at a 4th-century temple in Uzbekistan have uncovered evidence "
                "of an unprecedented religious synthesis. The site contains Buddhist statues "
                "with distinctly Zoroastrian fire altar iconography, suggesting practitioners "
                "of both faiths worshipped together during the height of Silk Road trade."
            ),
        }
        print(f"\nDemo article: {demo_article['title']}")
        result = scorer.score_article(demo_article)
        print("\nResults:")
        print(f"  Stage used: {result.get('stage_used')}")
        print(f"  Stage 1 estimate: {result.get('stage1_estimate', 'N/A')}")
        if result["scores"]:
            for dim, score in result["scores"].items():
                print(f"    {dim}: {score:.2f}")
            print(f"  Weighted average: {result['weighted_average']:.2f}")
            print(f"  Tier: {result['tier']}")


if __name__ == "__main__":
    main()
