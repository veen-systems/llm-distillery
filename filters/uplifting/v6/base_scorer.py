"""
Uplifting Content Filter v6 - Base Scorer Class

Inherits all shared logic from FilterBaseScorer.
Defines filter-specific constants.
"""

from filters.common.filter_base_scorer import FilterBaseScorer


class BaseUpliftingScorer(FilterBaseScorer):
    """
    Abstract base class for uplifting content scoring.

    Subclasses must implement:
        - _load_model(): Load model from local files or Hub
    """

    FILTER_NAME = "uplifting"
    FILTER_VERSION = "6.0"

    DIMENSION_NAMES = [
        "human_wellbeing_impact",
        "social_cohesion_impact",
        "justice_rights_impact",
        "evidence_level",
        "benefit_distribution",
        "change_durability",
    ]

    DIMENSION_WEIGHTS = {
        "human_wellbeing_impact": 0.25,
        "social_cohesion_impact": 0.15,
        "justice_rights_impact": 0.10,
        "evidence_level": 0.20,
        "benefit_distribution": 0.20,
        "change_durability": 0.10,
    }

    TIER_THRESHOLDS = [
        ("high", 7.0, "Verified, broadly beneficial, lasting positive change"),
        ("medium", 4.0, "Documented benefits with moderate reach or durability"),
        ("low", 0.0, "Speculation, elite-only benefits, or no documented impact"),
    ]

    GATEKEEPER_DIMENSION = "evidence_level"
    GATEKEEPER_MIN = 3.0
    GATEKEEPER_CAP = 3.0

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
