"""
Human Thriving Filter v8 - Hybrid Inference Pipeline

Stage 1: multilingual-e5-small embeddings + MLP probe (recall-first objective).
Stage 2: the fine-tuned Gemma-3-1B student, via HumanThrivingScorer.

⭐ THE STAGE-1 THRESHOLD IS READ FROM config.yaml, NOT HARDCODED HERE.

Every other filter's `inference_hybrid.py` carries a module-level `DEFAULT_THRESHOLD`, and
nothing passes `config.yaml`'s `hybrid_inference.stage1.threshold` into the constructor
(verified 2026-08-21: no consumer in `filters/common/` or NexusMind's `filter_loader` /
`production_scorer`). ⚠️ The VALUE varies -- measured across the 13 other packages on
2026-09-04: 0.75 (nature_recovery v1/v2/v4), 1.00 (belonging v1, uplifting v7), 1.225
(solutions v5/v6), 1.25 (cultural_discovery v4/v5), 1.50 (investment_risk v6), 2.25
(uplifting v6, thriving v1), 2.50 (cultural_discovery v6). Only two are 1.00.

⛔ And it is NOT harmless: config and code agree on nine of eleven, but
`nature_recovery v4` ships `threshold: 3.225` against a runtime 0.75 -- a 4.3x divergence,
the very "3.225-vs-0.75 shape" this repo names -- and `thriving v1` ships `threshold: null`.
Editing the config value alone does nothing, and on nr v4 the config has been lying for
months.

v8 wires the config to the runtime instead of duplicating the number: `threshold=None`
(the default, and what NexusMind's `scorer_class(**kwargs)` passes) reads the config, and
a missing key RAISES rather than falling back to a number nobody chose. There is exactly
one place the operating threshold lives.

⚠️ NOT the same as the TIER op-point (4.5), which lives in `base_scorer.py`'s
TIER_THRESHOLDS. Stage 1 screens; the op-point decides surfacing. Different numbers,
different files, do not reconcile them.

⛔ NO PREFILTER. v8 ships none (ADR-018/019 Amendment 2026-08-21) and the e5 probe is what
replaces it, so `use_prefilter` defaults to False here.

Usage:
    from filters.human_thriving.v8.inference_hybrid import HumanThrivingHybridScorer

    scorer = HumanThrivingHybridScorer()
    result = scorer.score_article(article)
    # result["stage_used"] -> "stage1_low" or "stage2"
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

import yaml

from filters.common.hybrid_scorer import HybridScorer
from filters.human_thriving.v8.inference import HumanThrivingScorer

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_stage1_config(config_path: Path = CONFIG_PATH) -> Dict:
    """Read `hybrid_inference.stage1` from config.yaml.

    Raises rather than defaulting. A Stage-1 screen running at a threshold nobody
    chose is worse than one that refuses to start: the screen is silent by design
    (a screened-out article produces no output to inspect), so a wrong threshold
    has no symptom. See `memory/working-rules.md` -- make the missing case raise.
    """
    if not config_path.exists():
        raise FileNotFoundError(
            f"human_thriving v8 hybrid inference needs {config_path}; it carries the "
            f"Stage-1 threshold, which is not duplicated in code."
        )
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    stage1 = (config.get("hybrid_inference") or {}).get("stage1")
    if not stage1:
        raise KeyError(
            f"{config_path} has no `hybrid_inference.stage1` block. The Stage-1 "
            f"threshold lives there and nowhere else for this filter."
        )
    threshold = stage1.get("threshold")
    if threshold is None:
        raise KeyError(
            f"{config_path} `hybrid_inference.stage1` has no `threshold`. Refusing to "
            f"screen at a default: v7's 1.00 was calibrated for a 4.0 op-point on a "
            f"different corpus and a different probe."
        )
    return {
        "threshold": float(threshold),
        "embedding_model": stage1.get("embedding_model",
                                      "intfloat/multilingual-e5-small"),
        "probe_path": stage1.get("probe_path", "probe/embedding_probe_e5small.pkl"),
        # None = unpinned. Present = the threshold above was derived against exactly
        # this probe file and nothing else may be screened with it.
        "probe_sha256": stage1.get("probe_sha256"),
    }


def verify_probe_matches_threshold(probe_path: Path, expected_sha256: str) -> None:
    """Refuse to screen with a probe the configured threshold was not derived against.

    ⛔ THE THRESHOLD IS NOT A PROPERTY OF THE RECIPE. Measured 2026-09-04: the same
    training data, objective and code with `--seed 7` instead of 42 produced a probe on
    which the configured 1.75 routes 0.7406 (val) / 0.7567 (test) instead of 0.8876 /
    0.8935 -- ~14 pp fewer articles reaching Stage 2, from the seed alone. FN@MEDIUM+
    stayed 0 on both, so recall-safety is seed-robust and ROUTING is not.

    Stage 1 is silent by design: a screened-out article produces no output to inspect,
    so this change has no symptom. Hence a crash rather than a warning.

    ⚠️ Not the same check as `EmbeddingStage._verify_pickle_integrity`, which compares
    against a `.pkl.sha256` companion FILE. That companion is regenerated by a retrain
    and so cannot notice a legitimate-but-unpaired probe; this hash lives beside the
    threshold in config.yaml and notices exactly that.
    """
    import hashlib

    if not probe_path.exists():
        raise FileNotFoundError(f"Stage-1 probe not found: {probe_path}")
    actual = hashlib.sha256(probe_path.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise ValueError(
            f"Stage-1 probe does not match the probe the configured threshold was "
            f"derived against.\n"
            f"  probe:    {probe_path}\n"
            f"  expected: {expected_sha256}\n"
            f"  actual:   {actual}\n"
            f"A different probe needs a RE-DERIVED threshold -- the same numeric "
            f"threshold moves Stage-2 routing by ~14 percentage points across probe "
            f"seeds, with no symptom. Re-run "
            f"scripts/analysis/probe_recall_report.py, pick the threshold that holds "
            f"the routing the owner ruled on (2026-08-28: near pass-through), then "
            f"update BOTH `threshold` and `probe_sha256` in config.yaml.\n"
            f"⚠️ A rerun with the SAME seed produces bit-identical probe CONTENT but a "
            f"different FILE hash -- torch embeds storage keys derived from memory "
            f"addresses (134 bytes, measured). So a hash mismatch is not by itself "
            f"proof the probe differs; compare the state_dicts before assuming it does."
        )


class HumanThrivingHybridScorer(HybridScorer):
    """
    Two-stage hybrid scorer for human_thriving v8.

    - Stage 1: multilingual-e5-small + MLP probe, threshold from config.yaml
    - Stage 2: HumanThrivingScorer (Gemma-3-1B + LoRA, isotonic-calibrated)
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        probe_path: Optional[Path] = None,
        threshold: Optional[float] = None,
        device: Optional[str] = None,
        use_prefilter: bool = False,
        config_path: Optional[Path] = None,
    ):
        """
        Args:
            model_path: Stage-2 model directory (default: ./model)
            probe_path: Stage-1 probe pickle (default: from config.yaml)
            threshold: Stage-1 threshold. None (the default, and what NexusMind's
                loader passes) means READ IT FROM config.yaml. An explicit value
                overrides the config -- used by sweeps, never by production.
            device: 'cuda', 'cpu', or None for auto
            use_prefilter: v8 ships no prefilter; True raises from base_scorer
            config_path: override config.yaml location (tests)
        """
        resolved_config = config_path or CONFIG_PATH
        # ⛔ v8 ships no prefilter, and `base_scorer._load_prefilter` raising was NOT
        # enough: `HybridScorer._create_stage2_scorer` below hardcodes
        # `use_prefilter=False`, so the Stage-2 scorer never reaches that raise and a
        # hybrid constructed with use_prefilter=True ran happily with
        # `self.use_prefilter = True` and `prefilter = None`. That is the same
        # documented-refusal-that-cannot-fire shape the raise was written to prevent
        # (found by review, 2026-09-04). Refuse here, on the path that actually scores.
        if use_prefilter:
            raise NotImplementedError(
                "human_thriving v8 ships no per-lens prefilter (ADR-018/019 Amendment "
                "2026-08-21); Stage-1 screening is the e5 probe. Construct with "
                "use_prefilter=False -- which is this class's default, and what "
                "NexusMind's loader passes."
            )

        stage1 = load_stage1_config(resolved_config)

        self._model_path = model_path
        # `probe_path` in the config is relative TO THE CONFIG, not to this module.
        # In the shipped package they are the same directory; keeping them tied to the
        # config is what makes the pin testable against a fixture config.
        self._probe_path = probe_path or (resolved_config.parent / stage1["probe_path"])
        self._embedding_model = stage1["embedding_model"]

        if threshold is None:
            self._threshold = stage1["threshold"]
            self._threshold_source = str(resolved_config)
        else:
            self._threshold = float(threshold)
            self._threshold_source = "constructor override"

        logger.info(
            f"human_thriving v8 Stage-1 threshold {self._threshold} "
            f"(from {self._threshold_source})"
        )

        # Only pinned when the threshold came from the config. An explicit override is
        # a deliberate sweep against some other probe, and pinning would block it.
        if threshold is None and stage1["probe_sha256"]:
            verify_probe_matches_threshold(self._probe_path, stage1["probe_sha256"])

        super().__init__(device=device, use_prefilter=use_prefilter)

    def _create_stage2_scorer(self):
        """Stage 2 is the local-files scorer. Prefilter off: HybridScorer owns that."""
        return HumanThrivingScorer(
            model_path=self._model_path,
            device=self.device_str,
            use_prefilter=False,
        )

    def _get_embedding_stage_config(self) -> Dict:
        return {
            "embedding_model_name": self._embedding_model,
            "probe_path": str(self._probe_path),
            "threshold": self._threshold,
        }


def main():
    """CLI interface for hybrid batch scoring."""
    import argparse
    import time

    parser = argparse.ArgumentParser(
        description="Score articles with the human_thriving v8 hybrid pipeline"
    )
    parser.add_argument("--input", "-i", type=Path, required=True)
    parser.add_argument("--output", "-o", type=Path, default=None)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument(
        "--threshold", type=float, default=None,
        help="Override the Stage-1 threshold from config.yaml (sweeps only). "
             "Omit to use the configured value -- which is the point of this filter's "
             "wiring; do not pass it to reproduce production.",
    )
    args = parser.parse_args()

    scorer = HumanThrivingHybridScorer(threshold=args.threshold, device=args.device)
    print(f"Stage-1 threshold: {scorer._threshold} (from {scorer._threshold_source})")

    articles = []
    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                articles.append(json.loads(line))

    start = time.time()
    results = scorer.score_batch(articles, batch_size=args.batch_size)
    elapsed = time.time() - start

    stage1_low = sum(1 for r in results if r.get("stage_used") == "stage1_low")
    stage2 = sum(1 for r in results if r.get("stage_used") == "stage2")
    print(f"\n{len(articles)} articles in {elapsed:.2f}s "
          f"({elapsed / max(len(articles), 1) * 1000:.1f} ms/article)")
    print(f"  Stage 1 LOW (model skipped): {stage1_low}")
    print(f"  Stage 2 (full model):        {stage2}  "
          f"({stage2 / max(len(articles), 1):.4f} routing rate)")

    tiers = {}
    for r in results:
        if r.get("tier"):
            tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1
    print("Tier distribution:")
    for tier, count in sorted(tiers.items()):
        print(f"  {tier}: {count}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            for article, result in zip(articles, results):
                article_id = article.get("id") or article.get("article_id", "")
                f.write(json.dumps({"article_id": article_id, **result}) + "\n")
        print(f"\nWrote {args.output}")


if __name__ == "__main__":
    main()
