"""
Solutions Filter v4 - Base Scorer Class

Inherits all shared logic from FilterBaseScorer (calibration loading + apply,
head+tail preprocessing, score clamping, weighted average, gatekeeper, tiering,
batch inference). Subclasses only define constants + _load_prefilter().

Lineage: renamed from sustainability_technology v3 (ADR-012). v4 replaces v3's
TRL gatekeeper with a universal `solution_concreteness` gatekeeper spanning the
tech / governance / community solution types.

The constants below MIRROR config.yaml (scoring.dimensions / scoring.tiers /
scoring.gatekeepers). Keep them in sync. TIER_THRESHOLDS is the SOLE runtime
source for tier assignment — no scoring code reads config's tiers section — so a
drift here silently changes what surfaces (FILTER_PLAYBOOK §8 F1: nature_recovery
shipped an inert config threshold for its whole deploy). medium = 3.0 is the
surfacing/operating point the ADR-021 ground-truth gate evaluates at.
"""

from filters.common.filter_base_scorer import FilterBaseScorer


class BaseSolutionsScorer(FilterBaseScorer):
    """
    Abstract base class for solutions scoring.

    Subclasses must implement:
        - _load_model(): Load model from local files (inference.py) or Hub
          (inference_hub.py).
    """

    FILTER_NAME = "solutions"
    FILTER_VERSION = "4.0"

    DIMENSION_NAMES = [
        "solution_concreteness",
        "systemic_impact",
        "evidence_strength",
        "governance_intervention_strength",
        "community_practice_strength",
        "equity_access",
        "economic_viability",
    ]

    # From config.yaml scoring.dimensions.*.weight (sum = 1.00).
    DIMENSION_WEIGHTS = {
        "solution_concreteness": 0.20,
        "systemic_impact": 0.20,
        "evidence_strength": 0.15,
        "governance_intervention_strength": 0.15,
        "community_practice_strength": 0.10,
        "equity_access": 0.10,
        "economic_viability": 0.10,
    }

    # MUST match config.yaml scoring.tiers.*.threshold (checked against the SOLE
    # runtime source rule above). Highest-first: _assign_tier returns the first
    # tier whose threshold weighted_avg >= threshold satisfies.
    TIER_THRESHOLDS = [
        ("high_solution", 7.0, "Mature, evidence-backed solution at meaningful scale"),
        ("medium_high", 5.0, "Active deployment with credible evidence"),
        ("medium", 3.0, "Concrete pilot or early-stage solution"),
        ("low", 0.0, "Aspirational, lab-stage, or no concrete action"),
    ]

    # solution_concreteness gatekeeper (config scoring.gatekeepers.
    # concreteness_gatekeeper): when concreteness < GATEKEEPER_MIN the weighted
    # average is capped at GATEKEEPER_CAP so aspirational rhetoric without a
    # concrete commitment cannot reach the higher solution tiers.
    #
    # NB boundary: GATEKEEPER_CAP (3.0) == the medium surfacing threshold (3.0),
    # so a gatekept article caps at exactly the bottom of `medium` and still
    # surfaces (contrast nature_recovery v4, where cap 3.5 sits BELOW medium 3.75
    # so gatekept content stays `low`/hidden). This is faithful to the current
    # config; flagged for review — see README / the deploy decision. It changes
    # what the ADR-021 gate counts as surfaced at 3.0.
    GATEKEEPER_DIMENSION = "solution_concreteness"
    GATEKEEPER_MIN = 3.0
    GATEKEEPER_CAP = 3.0

    def _load_prefilter(self):
        import importlib.util

        prefilter_path = self._get_filter_dir() / "prefilter.py"
        spec = importlib.util.spec_from_file_location("prefilter", prefilter_path)
        prefilter_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prefilter_module)
        self.prefilter = prefilter_module.SolutionsPreFilterV4()
