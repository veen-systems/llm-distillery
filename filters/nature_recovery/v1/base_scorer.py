"""
Nature Recovery Filter v1 - Base Scorer Class

Inherits all shared logic from FilterBaseScorer.
Defines filter-specific constants.
"""

from filters.common.filter_base_scorer import FilterBaseScorer


class BaseNatureRecoveryScorer(FilterBaseScorer):
    """
    Abstract base class for nature recovery scoring.

    Subclasses must implement:
        - _load_model(): Load model from local files or Hub
    """

    FILTER_NAME = "nature_recovery"
    FILTER_VERSION = "1.0"

    DIMENSION_NAMES = [
        "recovery_evidence",
        "measurable_outcomes",
        "ecological_significance",
        "restoration_scale",
        "human_agency",
        "protection_durability",
    ]

    DIMENSION_WEIGHTS = {
        "recovery_evidence": 0.25,
        "measurable_outcomes": 0.20,
        "ecological_significance": 0.20,
        "restoration_scale": 0.15,
        "human_agency": 0.10,
        "protection_durability": 0.10,
    }

    TIER_THRESHOLDS = [
        ("high", 7.0, "Strong documented ecosystem recovery with measurable outcomes"),
        ("medium", 4.0, "Some recovery evidence, partial data or limited scope"),
        ("low", 0.0, "No recovery evidence, doom/decline only, or non-ecological content"),
    ]

    GATEKEEPER_DIMENSION = "recovery_evidence"
    GATEKEEPER_MIN = 3.0
    GATEKEEPER_CAP = 3.5

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
