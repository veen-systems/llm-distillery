"""
Human Thriving Filter v8 - Base Scorer Class

The v8 rename of `uplifting` v7 (ADR-012 as amended). Inherits all shared logic
from FilterBaseScorer; this file holds only the filter-specific constants.

⛔ TIER_THRESHOLDS below is the SOLE RUNTIME SOURCE of the operating point.
`config.yaml scoring.tiers` is documentation and does NOT drive scoring — editing
it alone is a no-op in production (NM#161, NM#205 were both this drift). The op-point
lives in FOUR places and moves in ONE commit:
    1. TIER_THRESHOLDS here                          <- what actually scores
    2. config.yaml scoring.tiers.medium.threshold    <- documentation
    3. normalization.json stats.raw_min              <- Phase E, does not exist yet
    4. tests/unit/test_normalization_op_point.py     <- the parametrized assertion

⚠️ 4.5 is INHERITED from uplifting v7 (#102, 2026-08-10, ADR-023), not re-derived on
v8's own held-out oracle split. Phase D must re-derive it, and on TWO grounds:

  1. v8's score distribution is not v7's, and inheriting a number is not measuring it.
  2. ⛔ v8 now ships a `calibration.json`, and **4.5 on the calibrated scale is a
     STRICTER operating point than 4.5 on the raw scale** — it flags 17 test rows where
     raw flags 26, a 34.6% cut in surfaced volume, with the arms indistinguishable as
     rankers (Spearman 0.9977, AUC 0.9474 -> 0.9488). Carrying the number across is not
     "keeping the op-point"; it is silently tightening it.

⚠️ No single recall figure belongs in this file, because the one you would quote depends
on the DEVICE and on whether calibration is applied. Test @4.5, n=660, 35 positives:
raw 0.486 / spec 0.9856 and calibrated 0.343 / spec 0.9920, both on b650-gpu CPU
(EXP-016); EXP-015 reported raw 0.514 on b650-CUDA, which is the same split and one
article. Numbers, bands and the sweep:
`docs/evidence/2026-09-04-v8-probe-calibration/` and `calibration_report.md`.

⚠️ 4.5 is exactly MAX_NORMALIZATION_RAW_MIN, accepted with ZERO margin (strict `>`),
so this op-point cannot rise without raising that constant in BOTH repos.
"""

from filters.common.filter_base_scorer import FilterBaseScorer


class BaseHumanThrivingScorer(FilterBaseScorer):
    """
    Abstract base class for human thriving scoring.

    Subclasses must implement:
        - _load_model(): Load model from local files or Hub
    """

    FILTER_NAME = "human_thriving"
    FILTER_VERSION = "8.0"

    # Dimension KEYS and WEIGHTS are v7's, carried verbatim (config.yaml `scoring`).
    # Plan §9 Q4 asks whether social_cohesion_impact at 0.20 is right for Thriving;
    # carrying v7's weights is the null option, not an answer. A weight change needs
    # NO re-labelling (ADR-001).
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

    TIER_THRESHOLDS = [
        ("high", 7.0, "Verified, broadly beneficial, lasting positive change"),
        ("medium", 4.5, "Documented benefits with moderate reach or durability"),
        ("low", 0.0, "No documented thriving outcome, or the dominant subject is a harm"),
    ]

    GATEKEEPER_DIMENSION = "evidence_level"
    GATEKEEPER_MIN = 3.0
    GATEKEEPER_CAP = 3.0

    def _load_prefilter(self):
        """v8 ships NO per-lens prefilter — ADR-018/019 *Amendment 2026-08-21*.

        Keyword screening is Latin-script only; the multilingual e5 probe (Stage 1)
        replaces it. Raising here rather than silently no-op'ing: a scorer constructed
        with use_prefilter=True is asking for a screen that does not exist, and a
        silent pass-through would read as "the prefilter ran and let everything
        through" in exactly the way NM#284 did for six months.
        """
        raise NotImplementedError(
            "human_thriving v8 ships no per-lens prefilter (ADR-018/019 Amendment "
            "2026-08-21). Construct the scorer with use_prefilter=False; Stage-1 "
            "screening is the e5 probe, not keyword rules."
        )
