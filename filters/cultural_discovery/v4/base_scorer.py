"""
Cultural Discovery Filter v4 - Base Scorer Class

Inherits all shared logic from FilterBaseScorer.
Defines filter-specific constants.
"""

from filters.common.filter_base_scorer import FilterBaseScorer


class BaseCulturalDiscoveryScorer(FilterBaseScorer):
    """
    Abstract base class for cultural discovery scoring.

    Subclasses must implement:
        - _load_model(): Load model from local files or Hub
    """

    FILTER_NAME = "cultural_discovery"
    FILTER_VERSION = "4.0"

    DIMENSION_NAMES = [
        "discovery_novelty",
        "heritage_significance",
        "cross_cultural_connection",
        "human_resonance",
        "evidence_quality",
    ]

    DIMENSION_WEIGHTS = {
        "discovery_novelty": 0.25,
        "heritage_significance": 0.20,
        "cross_cultural_connection": 0.25,
        "human_resonance": 0.15,
        "evidence_quality": 0.15,
    }

    TIER_THRESHOLDS = [
        ("high", 7.0, "Significant discovery or deep cross-cultural insight, well-documented"),
        ("medium", 4.0, "Meaningful cultural content with some discovery or connection value"),
        ("low", 0.0, "Superficial, speculative, or single-culture content without insight"),
    ]

    GATEKEEPER_DIMENSION = "evidence_quality"
    GATEKEEPER_MIN = 3.0
    GATEKEEPER_CAP = 4.0  # Raised from 3.0 — evidence_quality MAE 1.31 caused excessive false gating (#23)

    def _load_prefilter(self):
        """Per-lens prefilters were deleted 2026-10-01 (NexusMind#284, decision 0).

        Defined here even though FilterBaseScorer now raises the same way: an
        older FilterBaseScorer copy (NexusMind's, until it syncs) declares this
        an @abstractmethod, and a package without it would fail to construct
        there, so no filter would score.
        """
        raise NotImplementedError(
            "per-lens prefilters were deleted (NexusMind#284, decision 0)"
        )
