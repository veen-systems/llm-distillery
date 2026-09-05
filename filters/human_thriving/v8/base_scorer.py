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

✅ RE-DERIVED AND RATIFIED BY THE OWNER, 2026-09-05: 4.5 STANDS, ON THE CALIBRATED
SCALE. `docs/decisions/2026-09-05-v8-op-point.md`. It is no longer inherited — the
sweep was computed on v8's own held-out split and the number happens to be the same one.

⛔ THE ARGUMENT IS THE SHAPE OF THE TRADE, NOT THE LEVEL. On the calibrated arm, from
3.75 upward every step costs almost exactly ONE agreed-good article per junk article
removed (4.00->4.25 is -2/-2; 4.25->4.50 is -4/-4). ADR-023 breaks a 1:1 trade toward
specificity — *a false positive costs a reader, a false negative costs nothing visible* —
so the strictest reachable bar wins. The frontier bends at 3.50, where -3 good buys -11
junk; anyone who wants materially more volume should move THERE, not to 4.0 or 4.25,
because the intermediate bars buy volume at exactly par.

⚠️ Held-out, calibrated: 4.50 removes 94.3% of what the v8 oracle says v7 was wrong to
surface and keeps 12 of the 30 both definitions call good (spec 0.9920). Design-weighted
on the same rows: 95.0% / 40.2%. The weighting does not move the decision — junk-removed
shifts at most +2.44 pp and good-kept +0.20 pp over all 7 bars and both arms.

⛔ **4.5 IS THE COMPARISON THE CALIBRATED SCORE MEETS, and that is verified by the code
path, not assumed**: `filter_base_scorer._process_raw_scores` applies `calibration.json`
BEFORE computing `weighted_avg` (`:315-317`), and `_assign_tier` sees that value
(`:340`). v8 ships a `calibration.json`, so the runtime comparison is calibrated-vs-4.5.
Executed at the boundary: 4.4999 -> `low`, 4.5000 -> `medium`.

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
