"""
Shared CLI utilities for filter inference modules.

Eliminates ~480 lines of duplicated main() functions across 8 inference files.
Each filter's inference.py and inference_hub.py delegate their CLI to these helpers.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def get_hf_token() -> Optional[str]:
    """
    Get HuggingFace token from environment or secrets.ini.

    Priority:
        1. HF_TOKEN environment variable
        2. config/credentials/secrets.ini [api_keys] huggingface_token
    """
    import os

    token = os.environ.get("HF_TOKEN")
    if token:
        return token

    try:
        import configparser
        config = configparser.ConfigParser()
        config.read("config/credentials/secrets.ini")
        token = config.get("api_keys", "huggingface_token", fallback=None)
    except Exception:
        pass

    return token


def run_scorer_cli(scorer_class, filter_name: str, demo_article: Dict):
    """
    Shared CLI for local inference.py modules.

    Handles:
    - --input / --output for batch scoring from JSONL files
    - --no-prefilter to skip keyword prefilter
    - --batch-size for batched inference
    - Interactive demo when no --input is provided

    Args:
        scorer_class: The local scorer class to instantiate
        filter_name: Display name for the filter (e.g., "sustainability_technology filter v3")
        demo_article: Dict with 'title' and 'content' for the interactive demo
    """
    import argparse

    parser = argparse.ArgumentParser(
        description=f"Score articles with {filter_name}"
    )
    parser.add_argument(
        "--input", "-i", type=Path, help="Input JSONL file with articles"
    )
    parser.add_argument(
        "--output", "-o", type=Path, help="Output JSONL file for results"
    )
    parser.add_argument(
        "--no-prefilter", action="store_true", help="No effect: per-lens prefilters were deleted (NexusMind#284, decision 0); kept so old invocations still parse"
    )
    parser.add_argument(
        "--batch-size", type=int, default=16, help="Batch size for inference"
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    scorer = scorer_class(use_prefilter=False)

    if args.input:
        _score_from_file(scorer, args.input, args.output, args.batch_size)
    else:
        _run_demo(scorer, demo_article)


def run_hub_scorer_demo(hub_class, filter_name: str, demo_article: Dict):
    """
    Shared CLI for inference_hub.py modules.

    Loads a HuggingFace Hub scorer and runs an interactive demo.

    Args:
        hub_class: The Hub scorer class to instantiate
        filter_name: Display name for the filter
        demo_article: Dict with 'title' and 'content' for the demo
    """
    token = get_hf_token()

    print(f"Loading {filter_name} from HuggingFace Hub...")
    scorer = hub_class(token=token)

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


def _score_from_file(scorer, input_path: Path, output_path: Optional[Path],
                     batch_size: int):
    """Score articles from a JSONL file."""
    logger.info(f"Loading articles from {input_path}")
    articles = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            articles.append(json.loads(line))

    logger.info(f"Scoring {len(articles)} articles...")
    results = scorer.score_batch(articles, batch_size=batch_size)

    if output_path:
        logger.info(f"Writing results to {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            for article, result in zip(articles, results):
                article_id = article.get("id") or article.get("article_id", "")
                output = {"article_id": article_id, **result}
                f.write(json.dumps(output) + "\n")
    else:
        passed = sum(1 for r in results if r["passed_prefilter"])
        print(f"\nResults: {passed}/{len(results)} passed prefilter")

        if passed > 0:
            tiers = {}
            for r in results:
                if r["tier"]:
                    tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1
            print("Tier distribution:")
            for tier, count in sorted(tiers.items()):
                print(f"  {tier}: {count}")


def _run_demo(scorer, demo_article: Dict):
    """Run interactive demo with a single article."""
    print("\n--- Interactive Demo ---")
    print(f"\nDemo article: {demo_article['title']}")
    result = scorer.score_article(demo_article)

    print(f"\nResults:")
    print(f"  Passed prefilter: {result['passed_prefilter']}")
    if result["scores"]:
        print(f"  Scores:")
        for dim, score in result["scores"].items():
            print(f"    {dim}: {score:.2f}")
        print(f"  Weighted average: {result['weighted_average']:.2f}")
        print(f"  Tier: {result['tier']} ({result['tier_description']})")
        if result["gatekeeper_applied"]:
            print(f"  Note: Gatekeeper applied")
