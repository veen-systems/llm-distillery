"""
FilterBaseScorer - Abstract base class for all filter scorers.

Extracted from the 4 production base_scorer.py files (uplifting v6,
sustainability_technology v3, investment_risk v6, cultural_discovery v4)
which were ~400 lines each with ~350 lines identical.

Subclasses define constants and _load_prefilter(); everything else lives here.

See GitHub issue #10.
"""

import hashlib
import inspect
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
import yaml

logger = logging.getLogger(__name__)


class FilterBaseScorer(ABC):
    """
    Abstract base class for filter scoring.

    Provides shared logic for both local model loading and HuggingFace Hub
    loading. Subclasses must define class constants and implement:
        - _load_model(): Load model from local files or Hub
        - _load_prefilter(): Load the filter-specific prefilter
    """

    # --- Subclasses MUST define these ---
    FILTER_NAME: str
    FILTER_VERSION: str
    DIMENSION_NAMES: List[str]
    DIMENSION_WEIGHTS: Dict[str, float]
    TIER_THRESHOLDS: List[Tuple[str, float, str]]

    # --- Gatekeeper (subclasses MAY override; None = no gatekeeper) ---
    GATEKEEPER_DIMENSION: Optional[str] = None
    GATEKEEPER_MIN: float = 0.0
    GATEKEEPER_CAP: float = 0.0

    # --- Fixed constants ---
    MAX_TOKEN_LENGTH = 512
    DEFAULT_BATCH_SIZE = 16

    def __init__(
        self,
        device: Optional[str] = None,
        use_prefilter: bool = True,
    ):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self.use_prefilter = use_prefilter
        self.prefilter = None
        self.model = None
        self.tokenizer = None

        self._load_preprocessing_config()
        self._load_calibration()
        self._compute_prompt_hash()

        if use_prefilter:
            self._load_prefilter()

    # --- Directory resolution ---

    @property
    def filter_dir(self) -> Path:
        """The concrete subclass's directory (not the common/ dir).

        Public API for wrappers (e.g. NexusMind's ProductionScorer) that need
        to find sibling artifacts like normalization.json or config.yaml without
        relying on the FILTER_NAME constant. See gotcha-log "Manifest as
        Anti-Pattern" (2026-05-04) for why this is exposed publicly.
        """
        return Path(inspect.getfile(type(self))).parent

    def _get_filter_dir(self) -> Path:
        """The concrete subclass's directory (not the common/ dir).

        Originally introduced as a backward-compat alias for the `filter_dir`
        property, but post-`18ab194` on NexusMind this method is *also* a
        load-bearing patch site for cross-repo test fixtures: NexusMind's
        `_build_scorer` (in `tests/unit/test_shared_infrastructure.py`) has to
        patch both this method *and* the property to redirect filter-dir
        resolution at test time, because the property body returns
        `inspect.getfile(...)` directly rather than delegating through here.
        Six per-filter `base_scorer.py` subclasses also call this directly.

        Do not remove without coordinating with NexusMind's test fixtures.
        See gotcha-log "Manifest as Anti-Pattern" closure note (2026-05-05)
        for full context.
        """
        return self.filter_dir

    # --- Property for HybridScorer compatibility ---

    @property
    def device_str(self) -> str:
        """Return string representation of device."""
        return str(self.device)

    # --- Prompt hash ---

    def _compute_prompt_hash(self):
        """Compute a short hash of the prompt file for provenance tracking."""
        self.prompt_hash = None
        filter_dir = self.filter_dir
        for name in ("prompt-compressed.md", "prompt.md"):
            prompt_path = filter_dir / name
            if prompt_path.exists():
                content = prompt_path.read_text(encoding="utf-8")
                self.prompt_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
                break

    # --- Scoring metadata ---

    def scoring_metadata(self) -> Dict:
        """Return provenance metadata for this scorer.

        Useful for active learning: knowing which model version and prompt
        produced a score, so stale scores can be identified and re-scored.
        """
        return {
            "filter_name": self.FILTER_NAME,
            "filter_version": self.FILTER_VERSION,
            "prompt_hash": self.prompt_hash,
            "calibrated": self.calibration is not None,
        }

    # --- Calibration ---

    def _load_calibration(self):
        """Load score calibration if calibration.json exists in the filter directory."""
        self.calibration = None
        cal_path = self.filter_dir / "calibration.json"
        if cal_path.exists():
            from filters.common.score_calibration import load_calibration
            self.calibration = load_calibration(str(cal_path))
            if self.calibration:
                dims_in_file = set(self.calibration.get("dimensions", {}).keys())
                expected_dims = set(self.DIMENSION_NAMES)
                missing = expected_dims - dims_in_file
                if missing:
                    logger.warning(
                        f"Calibration file missing dimensions: {missing}. "
                        f"Those dimensions will not be calibrated."
                    )
                logger.info(
                    f"Score calibration loaded ({self.calibration.get('n_samples', '?')} samples)"
                )

    # --- Preprocessing config ---

    def _load_preprocessing_config(self):
        """Load preprocessing config from config.yaml."""
        config_path = self.filter_dir / "config.yaml"

        self.use_head_tail = False
        self.head_tokens = 256
        self.tail_tokens = 256
        self.head_tail_separator = " [...] "

        # #93 short-content cap — off unless config.yaml opts in.
        self.short_content_min_chars = 300
        self.short_content_cap = None

        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            preprocessing = config.get("preprocessing", {})
            head_tail = preprocessing.get("head_tail", {})

            self.use_head_tail = head_tail.get("enabled", False)
            self.head_tokens = head_tail.get("head_tokens", 256)
            self.tail_tokens = head_tail.get("tail_tokens", 256)
            self.head_tail_separator = head_tail.get("separator", " [...] ")

            if self.use_head_tail:
                logger.info(
                    f"Head+tail preprocessing enabled: {self.head_tokens} + {self.tail_tokens} tokens"
                )

            self._load_short_content_config(config)

    def _load_short_content_config(self, config: Dict):
        """Load the #93 short-content cap from config.yaml.

        ADR-022 shape: content length is stamped on every result unconditionally
        (see `score_article`); this is the single config-gated decision point
        that acts on it. Default is no cap — the floor was measured to discard
        as much genuine content as bad, and only `solutions v6` has a candidate
        short-content defect, which is not yet identified (see #92: the DiD is
        confounded with a selection artifact). Do not set `cap` on any filter
        until that measurement separates the two.

        config.yaml shape:
            short_content:
              min_chars: 300   # what counts as short
              cap: 2.0         # raw weighted score ceiling; omit/null = off
        """
        short_content = config.get("short_content") or {}
        self.short_content_min_chars = short_content.get("min_chars", 300)
        self.short_content_cap = short_content.get("cap")

        if self.short_content_cap is not None:
            logger.info(
                f"Short-content cap active: content < {self.short_content_min_chars} "
                f"chars capped at {self.short_content_cap}"
            )

    # --- Abstract methods ---

    @abstractmethod
    def _load_model(self):
        """Load the model. Implemented by subclasses."""
        pass

    @abstractmethod
    def _load_prefilter(self):
        """Load the filter-specific prefilter. Implemented by subclasses."""
        pass

    # --- Validation ---

    def _validate_article(self, article: Dict) -> None:
        if not isinstance(article, dict):
            raise TypeError(f"article must be dict, got {type(article).__name__}")

        if "title" not in article:
            raise ValueError("article must contain 'title' key")
        if "content" not in article:
            raise ValueError("article must contain 'content' key")

        if not article.get("title"):
            raise ValueError("article 'title' cannot be empty")
        if not article.get("content"):
            raise ValueError("article 'content' cannot be empty")

    def _create_empty_result(self) -> Dict:
        """Create an empty result dict structure."""
        return {
            "passed_prefilter": True,
            "prefilter_reason": None,
            "scores": None,
            "weighted_average": None,
            "tier": None,
            "tier_description": None,
            "gatekeeper_applied": False,
            # #93 — stamped on every result, including prefilter-blocked ones
            # (None until _stamp_content_length runs for that article).
            "content_length": None,
            "short_content_cap_applied": False,
        }

    def _stamp_content_length(self, article: Dict, result: Dict) -> Dict:
        """Record the article's content length on the result (ADR-022: stamp always).

        Unconditional and independent of any enforcement decision — the cap in
        `_process_raw_scores` reads this, and so can any downstream consumer
        that wants to reason about short content without re-deriving it.
        """
        from filters.common.base_prefilter import BasePreFilter

        result["content_length"] = BasePreFilter.content_length(article)
        return result

    def _apply_short_content_cap(self, weighted_avg: float, result: Dict) -> float:
        """The #93 short-content rule — the one place it is decided.

        Off unless `config.yaml` sets `short_content.cap`. Reads the stamp on
        `result` rather than the article, so every scoring path that stamps
        reaches the same verdict; HybridScorer's Stage-1 branch calls this
        directly for the same reason (a second inline copy is exactly the
        second-drop-point shape ADR-022's Risks section warns about).

        Returns the (possibly capped) weighted average and records
        `short_content_cap_applied` on the result.
        """
        if self.short_content_cap is None:
            return weighted_avg

        length = result.get("content_length")
        if length is None or length >= self.short_content_min_chars:
            return weighted_avg

        if weighted_avg > self.short_content_cap:
            result["short_content_cap_applied"] = True
            return self.short_content_cap

        return weighted_avg

    # --- Tier assignment ---

    def _assign_tier(self, weighted_avg: float) -> Tuple[str, str]:
        for tier_name, threshold, description in self.TIER_THRESHOLDS:
            if weighted_avg >= threshold:
                return (tier_name, description)
        return ("low", "No tier matched")

    # --- Score processing ---

    def _process_raw_scores(self, raw_scores, result: Dict) -> Dict:
        """Process raw model output into final scores with gatekeeper logic."""
        if self.calibration is not None:
            from filters.common.score_calibration import apply_calibration
            raw_scores = apply_calibration(raw_scores, self.calibration, self.DIMENSION_NAMES)

        scores = {
            dim: float(max(0.0, min(10.0, raw_scores[i])))
            for i, dim in enumerate(self.DIMENSION_NAMES)
        }
        result["scores"] = scores

        weighted_avg = sum(
            scores[dim] * self.DIMENSION_WEIGHTS[dim]
            for dim in self.DIMENSION_NAMES
        )

        if self.GATEKEEPER_DIMENSION is not None:
            if scores[self.GATEKEEPER_DIMENSION] < self.GATEKEEPER_MIN:
                if weighted_avg > self.GATEKEEPER_CAP:
                    weighted_avg = self.GATEKEEPER_CAP
                    result["gatekeeper_applied"] = True

        weighted_avg = self._apply_short_content_cap(weighted_avg, result)

        result["weighted_average"] = weighted_avg

        tier, tier_desc = self._assign_tier(weighted_avg)
        result["tier"] = tier
        result["tier_description"] = tier_desc

        return result

    # --- Single article scoring ---

    def score_article(
        self,
        article: Dict,
        skip_prefilter: bool = False,
    ) -> Dict:
        """
        Score a single article.

        Args:
            article: Dict with 'title' and 'content' keys
            skip_prefilter: Force skip prefilter even if enabled

        Returns:
            Dict with scores, tier, gatekeeper info
        """
        self._validate_article(article)

        result = self._create_empty_result()
        self._stamp_content_length(article, result)

        if self.use_prefilter and not skip_prefilter:
            passed, reason = self.prefilter.apply_filter(article)
            if not passed:
                result["passed_prefilter"] = False
                result["prefilter_reason"] = reason
                return result

        text = f"{article['title']}\n\n{article['content']}"

        if self.use_head_tail:
            from filters.common.text_preprocessing import extract_head_tail
            text = extract_head_tail(
                text,
                self.tokenizer,
                self.head_tokens,
                self.tail_tokens,
                self.head_tail_separator,
            )

        inputs = self.tokenizer(
            text,
            max_length=self.MAX_TOKEN_LENGTH,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            # .float() before .numpy() — BFloat16 models (sustainability_technology v3,
            # others trained with bf16) would otherwise raise TypeError: Got unsupported
            # ScalarType BFloat16. Originally fixed in 68e3d5d; regressed 2026-04-19 via
            # deploy_to_nexusmind.sh overwriting with stale llm-distillery copy.
            raw_scores = outputs.logits[0].float().cpu().numpy()

        return self._process_raw_scores(raw_scores, result)

    # --- Batch scoring ---

    def score_batch(
        self,
        articles: List[Dict],
        batch_size: int = None,
        skip_prefilter: bool = False,
    ) -> List[Dict]:
        """
        Score a batch of articles efficiently.

        Args:
            articles: List of article dicts
            batch_size: Batch size for inference (default: DEFAULT_BATCH_SIZE)
            skip_prefilter: Skip prefilter for all articles

        Returns:
            List of result dicts (same structure as score_article)
        """
        if not articles:
            return []

        if batch_size is None:
            batch_size = self.DEFAULT_BATCH_SIZE

        if batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {batch_size}")

        results = []
        articles_to_score = []
        article_indices = []

        for i, article in enumerate(articles):
            result = self._create_empty_result()

            try:
                self._validate_article(article)
            except (TypeError, ValueError) as e:
                result["passed_prefilter"] = False
                result["prefilter_reason"] = f"Invalid article: {e}"
                results.append(result)
                continue

            self._stamp_content_length(article, result)

            if self.use_prefilter and not skip_prefilter:
                passed, reason = self.prefilter.apply_filter(article)
                if not passed:
                    result["passed_prefilter"] = False
                    result["prefilter_reason"] = reason
                    results.append(result)
                    continue

            articles_to_score.append(article)
            article_indices.append(i)
            results.append(result)

        if articles_to_score:
            for batch_start in range(0, len(articles_to_score), batch_size):
                batch_end = min(batch_start + batch_size, len(articles_to_score))
                batch = articles_to_score[batch_start:batch_end]
                batch_indices = article_indices[batch_start:batch_end]

                texts = [f"{a['title']}\n\n{a['content']}" for a in batch]

                if self.use_head_tail:
                    from filters.common.text_preprocessing import extract_head_tail
                    texts = [
                        extract_head_tail(
                            t,
                            self.tokenizer,
                            self.head_tokens,
                            self.tail_tokens,
                            self.head_tail_separator,
                        )
                        for t in texts
                    ]

                inputs = self.tokenizer(
                    texts,
                    max_length=self.MAX_TOKEN_LENGTH,
                    padding="max_length",
                    truncation=True,
                    return_tensors="pt",
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                with torch.no_grad():
                    outputs = self.model(**inputs)
                    # See single-article path above — BFloat16 → float32 cast required.
                    batch_scores = outputs.logits.float().cpu().numpy()

                for j, idx in enumerate(batch_indices):
                    raw_scores = batch_scores[j]
                    self._process_raw_scores(raw_scores, results[idx])

        return results
