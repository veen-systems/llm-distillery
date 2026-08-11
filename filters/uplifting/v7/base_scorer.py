"""
Uplifting Content Filter v7 - Base Scorer Class

Inherits all shared logic from FilterBaseScorer.
Defines filter-specific constants and prefilter loading.
"""

from filters.common.filter_base_scorer import FilterBaseScorer


class BaseUpliftingScorer(FilterBaseScorer):
    """
    Abstract base class for uplifting content scoring.

    Subclasses must implement:
        - _load_model(): Load model from local files or Hub
    """

    FILTER_NAME = "uplifting"
    FILTER_VERSION = "7.0"

    DIMENSION_NAMES = [
        "human_wellbeing_impact",
        "social_cohesion_impact",
        "justice_rights_impact",
        "evidence_level",
        "benefit_distribution",
        "change_durability",
    ]

    DIMENSION_WEIGHTS = {
        "human_wellbeing_impact": 0.30,
        "social_cohesion_impact": 0.20,
        "justice_rights_impact": 0.15,
        "evidence_level": 0.10,
        "benefit_distribution": 0.10,
        "change_durability": 0.15,
    }

    # TIER_THRESHOLDS is the SOLE RUNTIME SOURCE of the operating point.
    # config.yaml scoring.tiers is documentation and does NOT drive scoring --
    # changing it alone is a no-op in production. Keep the two in sync.
    # medium 4.0 -> 4.5 on 2026-08-10 (llm-distillery#102, ADR-023); see the
    # decision record in config.yaml and
    # docs/evidence/2026-08-10-uplifting-v7-threshold-sweep-102.md.
    TIER_THRESHOLDS = [
        ("high", 7.0, "Verified, broadly beneficial, lasting positive change"),
        ("medium", 4.5, "Documented benefits with moderate reach or durability"),
        ("low", 0.0, "Speculation, elite-only benefits, or no documented wellbeing impact"),
    ]

    GATEKEEPER_DIMENSION = "evidence_level"
    GATEKEEPER_MIN = 3.0
    GATEKEEPER_CAP = 3.0

    def _load_prefilter(self):
        from filters.uplifting.v7.prefilter import UpliftingPreFilterV7
        self.prefilter = UpliftingPreFilterV7()
