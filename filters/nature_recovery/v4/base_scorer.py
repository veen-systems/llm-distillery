"""
Nature Recovery Filter v2 - Base Scorer Class

Inherits all shared logic from FilterBaseScorer.
Defines filter-specific constants and prefilter loading.
"""

from filters.common.filter_base_scorer import FilterBaseScorer


class BaseNatureRecoveryScorer(FilterBaseScorer):
    """
    Abstract base class for nature recovery scoring.

    Subclasses must implement:
        - _load_model(): Load model from local files or Hub
    """

    FILTER_NAME = "nature_recovery"
    FILTER_VERSION = "2.0"

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
        import importlib.util
        prefilter_path = self._get_filter_dir() / "prefilter.py"
        spec = importlib.util.spec_from_file_location("prefilter", prefilter_path)
        prefilter_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prefilter_module)
        self.prefilter = prefilter_module.NatureRecoveryPreFilterV1()
