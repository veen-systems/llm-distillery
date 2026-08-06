"""
Cultural Discovery Filter v6 - Base Scorer Class

Inherits all shared logic from FilterBaseScorer.
Defines filter-specific constants and prefilter loading.

v6 vs v5 deltas (#98 — architecture migration, "probe first, dimensions later"):
  - FILTER_VERSION bumped to "6.0"
  - Adds a multilingual-e5-small Stage-1 probe (hybrid_inference in config.yaml),
    so topic screening becomes a semantic judgement instead of keyword stems and
    cannot carry a per-language coverage gap by construction (the #86 defect).
  - Loads the v6 prefilter, which carries v5's rules UNCHANGED so the probe can
    be A/B'd against the existing gate on identical rows (#98 criteria 1-3).

  - Loads the v6 prefilter, now a commerce-only pass-through: the keyword gate,
    the four exclusion categories and the three domain blocklists are gone
    (#98 criterion 4, executed after the probe beat the gate on held-out oracle
    ground truth — FN 0/75 vs 10/75).
  - DROPS the evidence_quality gatekeeper (#94, owner decision at this bump).
    See the block below TIER_THRESHOLDS for why that is a no-op.

NOT changed here, deliberately — these belong to #87, not #98:
  - dimensions, weights, tier thresholds
  - the 4.0 op-point (its provenance gap and re-derivation are #87; #95 no
    longer blocks that work — the noise band shipped 2026-08-06)

The student model is UNCHANGED from v5. v6 is an architecture migration: same
weights, same calibration, new screening. That is why calibration.json is a
byte-identical copy of v5's (correct — a calibration belongs to a model) and why
there is deliberately NO normalization.json (the probe changes which articles
survive to the student, so the production CDF is not v5's).
"""

from filters.common.filter_base_scorer import FilterBaseScorer


class BaseCulturalDiscoveryScorer(FilterBaseScorer):
    """Abstract base class for cultural discovery v6 scoring. Subclasses implement _load_model()."""

    FILTER_NAME = "cultural_discovery"
    FILTER_VERSION = "6.0"

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

    # NO GATEKEEPER (#94, owner decision at this version bump). v5 carried
    # GATEKEEPER_DIMENSION = "evidence_quality", MIN 3.0, CAP 4.0. It was dead
    # twice over:
    #   - MIN never bound in any of the 8,551 labelled articles, and
    #   - CAP 4.0 EQUALLED the medium threshold above, so even when it fired
    #     (34.8% of production articles) a capped article stayed at exactly the
    #     op-point and remained visible. Under ADR-016/ADR-022 visibility is the
    #     only outcome a filter has — a tier is a badge — so it could not change
    #     an outcome at all.
    # Removing it is a no-op by definition, not a behaviour change. evidence_quality
    # continues to self-enforce through its 0.15 weight. Lowering the cap so it
    # COULD bind is a real behaviour change and needs a measured recall check
    # against held-out oracle labels first (ADR-021) — that is not this version.
    # tests/unit/test_gatekeeper_invariant.py enforces CAP < medium threshold for
    # any filter that declares one.

    def _load_prefilter(self):
        import importlib.util
        prefilter_path = self._get_filter_dir() / "prefilter.py"
        spec = importlib.util.spec_from_file_location("prefilter", prefilter_path)
        prefilter_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prefilter_module)
        self.prefilter = prefilter_module.CulturalDiscoveryPreFilterV6()
