"""
Cultural Discovery Filter v5 - Base Scorer Class

Inherits all shared logic from FilterBaseScorer.
Defines filter-specific constants.

v5 vs v4 deltas:
  - FILTER_VERSION bumped to "5.0"
  - Loaded a cd v5 prefilter (thin subclass of v4). DELETED 2026-10-01 with every per-lens
    prefilter (NexusMind#284, decision 0); it never ran in production.
  - GATEKEEPER_CAP raised to 4.0 (preserved from v4 — evidence_quality MAE caused excessive false gating)
  - Dimensions, weights, tier thresholds, gatekeeper unchanged
"""

from filters.common.filter_base_scorer import FilterBaseScorer


class BaseCulturalDiscoveryScorer(FilterBaseScorer):
    """Abstract base class for cultural discovery v5 scoring. Subclasses implement _load_model()."""

    FILTER_NAME = "cultural_discovery"
    FILTER_VERSION = "5.0"

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
    GATEKEEPER_CAP = 4.0  # Preserved from v4 (#23 — raised from 3.0 to avoid excessive false gating)

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
