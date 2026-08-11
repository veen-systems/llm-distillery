"""
Investment Risk Filter v6 - Base Scorer Class

Inherits all shared logic from FilterBaseScorer.
Defines filter-specific constants and prefilter loading.
"""

from filters.common.filter_base_scorer import FilterBaseScorer


class BaseInvestmentRiskScorer(FilterBaseScorer):
    """
    Abstract base class for investment risk scoring.

    Subclasses must implement:
        - _load_model(): Load model from local files or Hub
    """

    FILTER_NAME = "investment_risk"
    FILTER_VERSION = "6.0"

    DIMENSION_NAMES = [
        "risk_domain_type",
        "severity_magnitude",
        "materialization_timeline",
        "evidence_quality",
        "impact_breadth",
        "retail_actionability",
    ]

    DIMENSION_WEIGHTS = {
        "risk_domain_type": 0.20,
        "severity_magnitude": 0.25,
        "materialization_timeline": 0.15,
        "evidence_quality": 0.15,
        "impact_breadth": 0.15,
        "retail_actionability": 0.10,
    }

    # TIER_THRESHOLDS is the SOLE RUNTIME SOURCE of the operating point;
    # config.yaml scoring.tiers is documentation and does not drive scoring.
    # medium 4.0 -> 4.25 on 2026-08-11 (llm-distillery#102 method, ADR-023):
    #   4.00  recall 0.761  specificity 0.955  FPR 4.5%  (40 FP, 39 FN)
    #   4.25  recall 0.724  specificity 0.974  FPR 2.6%  (23 FP, 45 FN)
    # 17 fewer false positives for 6 more false negatives.
    # CAVEAT recorded at the time: this filter's false positives are NEAR-MISSES
    # (oracle median 3.05, max 3.90) -- geopolitical/macro risk the model rates
    # above the oracle -- not reader-harming junk. So the ADR-023 argument is
    # weaker here than for uplifting v7, and 3 of the 6 lost true positives are
    # strong (oracle 5.55-5.85). Revert is a one-line change plus a refit.
    TIER_THRESHOLDS = [
        ("high", 7.0, "Critical risk signal - act now to reduce exposure"),
        ("medium", 4.25, "Moderate signal - worth tracking, limited immediate action"),
        ("low", 0.0, "Low signal - noise, not investment-relevant, or already priced in"),
    ]

    GATEKEEPER_DIMENSION = "evidence_quality"
    GATEKEEPER_MIN = 4.0
    GATEKEEPER_CAP = 2.9

    def _load_prefilter(self):
        import importlib.util
        prefilter_path = self._get_filter_dir() / "prefilter.py"
        spec = importlib.util.spec_from_file_location("prefilter", prefilter_path)
        prefilter_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prefilter_module)
        self.prefilter = prefilter_module.InvestmentRiskPreFilterV6()
