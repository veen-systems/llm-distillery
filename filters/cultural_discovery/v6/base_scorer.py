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

NOT changed here, deliberately — these belong to #87, not #98:
  - dimensions, weights, tier thresholds, gatekeeper values
  - the 4.0 op-point (its provenance gap and re-derivation are blocked on #95)

The evidence_quality gatekeeper below is inert on this label set: MIN 3.0 never
binds in any of the 8,551 labelled articles, and CAP 4.0 equals the medium tier
threshold, so it could not demote an article out of the visible band even if it
did bind. See #94 — it is carried forward unchanged rather than removed, because
removing it is a separate decision the owner has not made.
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

    GATEKEEPER_DIMENSION = "evidence_quality"
    GATEKEEPER_MIN = 3.0
    GATEKEEPER_CAP = 4.0  # Preserved from v4 (#23 — raised from 3.0 to avoid excessive false gating)

    def _load_prefilter(self):
        import importlib.util
        prefilter_path = self._get_filter_dir() / "prefilter.py"
        spec = importlib.util.spec_from_file_location("prefilter", prefilter_path)
        prefilter_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prefilter_module)
        self.prefilter = prefilter_module.CulturalDiscoveryPreFilterV6()
