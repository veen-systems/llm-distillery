"""
Hybrid Scorer - Two-stage inference pipeline combining embeddings and fine-tuned model.

Stage 1: Fast embedding + MLP probe screening (~8ms/article)
Stage 2: Full fine-tuned model scoring (~25ms/article, only for candidates)

Articles with low Stage 1 estimates skip Stage 2, reducing average inference
time by ~40% while maintaining accuracy on MEDIUM/HIGH tier articles.

Usage:
    # Subclass for a specific filter (see filters/uplifting/v7/inference_hybrid.py)
    class MyHybridScorer(HybridScorer):
        def _create_stage2_scorer(self):
            return MyScorer(device=self.device_str, use_prefilter=False)

        def _get_embedding_stage_config(self):
            return {
                "embedding_model_name": "intfloat/multilingual-e5-large",
                "probe_path": "path/to/probe.pkl",
                "threshold": 3.0,
            }
"""

import inspect
import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from filters.common.embedding_stage import EmbeddingStage, ScreeningResult

logger = logging.getLogger(__name__)


class HybridScorer(ABC):
    """
    Abstract two-stage hybrid scorer.

    Combines a fast embedding probe (Stage 1) with an existing fine-tuned
    model scorer (Stage 2). Articles estimated LOW by Stage 1 skip Stage 2.

    Subclasses must implement:
        - _create_stage2_scorer(): Return the existing filter scorer
        - _get_embedding_stage_config(): Return EmbeddingStage kwargs
    """

    def __init__(
        self,
        device: Optional[str] = None,
        use_prefilter: bool = True,
    ):
        """
        Initialize the hybrid scorer.

        Args:
            device: Device to use ('cuda', 'cpu', or None for auto)
            use_prefilter: Whether to apply rule-based prefilter
        """
        import torch

        if device is None:
            self.device_str = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device_str = device

        self.use_prefilter = use_prefilter

        # Load Stage 2 scorer (the existing fine-tuned model)
        self.stage2_scorer = self._create_stage2_scorer()

        # Load Stage 1 (embedding + probe)
        config = self._get_embedding_stage_config()
        self.embedding_stage = EmbeddingStage(
            device=self.device_str,
            dimension_weights=self.stage2_scorer.DIMENSION_WEIGHTS,
            dimension_names=self.stage2_scorer.DIMENSION_NAMES,
            **config,
        )

        self.threshold = config.get("threshold", 3.0)

    @property
    def filter_dir(self) -> Path:
        """The concrete subclass's directory (e.g. filters/uplifting/v7/).

        Mirrors `FilterBaseScorer.filter_dir`, so wrappers can resolve sibling
        artifacts (normalization.json, config.yaml) on either base type via the
        same public API. See gotcha-log "Manifest as Anti-Pattern" (2026-05-04).

        Assumes the HybridScorer subclass file (e.g. inference_hybrid.py) and
        its composed stage2_scorer's subclass file (inference.py) live in the
        same directory. All current subclasses satisfy this; the assumption
        would break for a hypothetical cross-version probe harness, in which
        case `self.filter_dir` and `self.stage2_scorer.filter_dir` would
        diverge — fix would be to override here.
        """
        return Path(inspect.getfile(type(self))).parent

    @property
    def FILTER_NAME(self) -> str:
        """Delegate to the composed stage2 scorer.

        Promoted from a NexusMind-side fallback chain (2026-05-04 review)
        so wrappers can call `scorer.FILTER_NAME` uniformly on either base
        type. Same shape as the existing implicit delegations
        (`stage2_scorer.DIMENSION_WEIGHTS` etc.) used internally.
        """
        return self.stage2_scorer.FILTER_NAME

    @property
    def TIER_THRESHOLDS(self) -> List[Tuple[str, float, str]]:
        """Delegate to the composed stage2 scorer.

        Promoted from a NexusMind-side fallback chain (2026-05-04 review).
        Wrappers that reassign tier on a normalized weighted average (e.g.
        ProductionScorer per ADR-014) read this directly.
        """
        return self.stage2_scorer.TIER_THRESHOLDS

    @abstractmethod
    def _create_stage2_scorer(self):
        """Create and return the Stage 2 scorer (existing fine-tuned model).

        The returned scorer should have use_prefilter=False since the
        HybridScorer handles prefiltering itself.
        """
        pass

    @abstractmethod
    def _get_embedding_stage_config(self) -> Dict:
        """Return configuration for EmbeddingStage.

        Must include:
            - embedding_model_name: str
            - probe_path: str
            - threshold: float
        """
        pass

    def score_article(
        self,
        article: Dict,
        skip_prefilter: bool = False,
    ) -> Dict:
        """
        Score a single article using the two-stage pipeline.

        Args:
            article: Dict with 'title' and 'content' keys
            skip_prefilter: Force skip prefilter

        Returns:
            Result dict matching existing scorer interface, plus:
                - stage_used: "stage1_low" or "stage2"
                - stage1_estimate: float (weighted avg from probe)
        """
        results = self.score_batch([article], skip_prefilter=skip_prefilter)
        return results[0]

    def score_batch(
        self,
        articles: List[Dict],
        batch_size: int = 16,
        skip_prefilter: bool = False,
    ) -> List[Dict]:
        """
        Score a batch of articles using the two-stage pipeline.

        Pipeline:
            1. Validate articles
            2. Apply prefilter (if enabled)
            3. Stage 1: Embedding + MLP probe screening
            4. Stage 2: Fine-tuned model (only for Stage 1 candidates)

        Args:
            articles: List of article dicts
            batch_size: Batch size for Stage 2 inference
            skip_prefilter: Skip rule-based prefilter

        Returns:
            List of result dicts with stage_used and stage1_estimate fields
        """
        if not articles:
            return []

        start_time = time.time()

        # Initialize results
        results = [None] * len(articles)

        # Phase 1: Prefilter pass (using Stage 2 scorer's prefilter)
        prefilter_passed_indices = []

        for i, article in enumerate(articles):
            # Validate
            try:
                self.stage2_scorer._validate_article(article)
            except (TypeError, ValueError) as e:
                result = self.stage2_scorer._create_empty_result()
                result["passed_prefilter"] = False
                result["prefilter_reason"] = f"Invalid article: {e}"
                result["stage_used"] = None
                result["stage1_estimate"] = None
                results[i] = result
                continue

            # Prefilter
            if self.use_prefilter and not skip_prefilter and self.stage2_scorer.prefilter:
                passed, reason = self.stage2_scorer.prefilter.apply_filter(article)
                if not passed:
                    result = self.stage2_scorer._create_empty_result()
                    self.stage2_scorer._stamp_content_length(article, result)
                    result["passed_prefilter"] = False
                    result["prefilter_reason"] = reason
                    result["stage_used"] = None
                    result["stage1_estimate"] = None
                    results[i] = result
                    continue

            prefilter_passed_indices.append(i)

        if not prefilter_passed_indices:
            return results

        # Phase 2: Stage 1 screening
        passed_articles = [articles[i] for i in prefilter_passed_indices]
        screening_results = self.embedding_stage.screen_batch(
            passed_articles, batch_size=batch_size
        )

        # Separate into Stage 1 LOW vs Stage 2 candidates
        stage2_indices = []  # indices into prefilter_passed_indices
        stage2_articles = []

        for j, (idx, screen) in enumerate(zip(prefilter_passed_indices, screening_results)):
            if screen.needs_stage2:
                stage2_indices.append(j)
                stage2_articles.append(articles[idx])
            else:
                # Stage 1 LOW: use probe scores directly.
                # Note: evidence gatekeeper is NOT applied to Stage 1 results.
                # This is safe because the Stage 1 threshold (e.g., 2.25) is well
                # below the gatekeeper cap (3.0), so any article that would be
                # capped by the gatekeeper already falls below the threshold.
                result = self.stage2_scorer._create_empty_result()
                self.stage2_scorer._stamp_content_length(articles[idx], result)
                result["passed_prefilter"] = True
                result["scores"] = screen.scores
                # Short-content cap (#93) IS applied here, unlike the evidence
                # gatekeeper: the gatekeeper is skipped because its cap sits
                # above the Stage-1 threshold, and nothing guarantees that of a
                # per-filter short-content cap. Delegates to the base scorer so
                # the rule has one implementation.
                weighted_avg = self.stage2_scorer._apply_short_content_cap(
                    screen.weighted_avg, result
                )
                result["weighted_average"] = weighted_avg
                tier, tier_desc = self.stage2_scorer._assign_tier(weighted_avg)
                result["tier"] = tier
                result["tier_description"] = tier_desc
                result["stage_used"] = "stage1_low"
                result["stage1_estimate"] = screen.weighted_avg
                results[idx] = result

        # Phase 3: Stage 2 for candidates
        if stage2_articles:
            stage2_results = self.stage2_scorer.score_batch(
                stage2_articles,
                batch_size=batch_size,
                skip_prefilter=True,  # Already prefiltered
            )

            for j, s2_result in zip(stage2_indices, stage2_results):
                idx = prefilter_passed_indices[j]
                screen = screening_results[j]
                s2_result["stage_used"] = "stage2"
                s2_result["stage1_estimate"] = screen.weighted_avg
                results[idx] = s2_result

        elapsed = time.time() - start_time
        stage1_count = sum(
            1 for r in results if r and r.get("stage_used") == "stage1_low"
        )
        stage2_count = sum(
            1 for r in results if r and r.get("stage_used") == "stage2"
        )
        prefilter_blocked = sum(
            1 for r in results if r and not r.get("passed_prefilter", True)
        )

        logger.info(
            f"Hybrid batch scored {len(articles)} articles in {elapsed:.2f}s: "
            f"prefilter_blocked={prefilter_blocked}, "
            f"stage1_low={stage1_count}, stage2={stage2_count}"
        )

        return results
