"""
Static invariant: a declared gatekeeper must be able to change an outcome.

Owner decision, 2026-08-06 (#94): fix the dead-gatekeeper class with a static
invariant rather than case-by-case removal, so the next filter that copies the
template cannot inherit the same inert config.

THE INVARIANT
-------------
    GATEKEEPER_CAP < the medium (surfacing) tier threshold

Under ADR-016 filters emit pass/block + a continuous score — tiers were dropped
as an output. Under ADR-022 visibility is `raw >= op-point` and the normalized
score is rank/badge only. So the ONLY outcome a gatekeeper can change is
**visibility**, and it can only change visibility if capping an article pushes
it below the surfacing threshold. A cap at or above that threshold demotes a
badge and nothing else.

Both values are read from the scorer class, never from config.yaml. A config
value read by no code is inert, and grepping for it verifies nothing — that is
how nature_recovery v4 ran a whole deploy at 4.0 while every doc said 3.75
(docs/FILTER_PLAYBOOK.md §8). `TIER_THRESHOLDS` and `GATEKEEPER_CAP` on the
scorer class are what `filters/common/filter_base_scorer.py` actually executes.

EXEMPTIONS
----------
Same contract as tests/unit/test_filter_config_schema.py: each entry must match
a REAL violation. Removing an entry while the drift still exists fails the test;
fixing the drift while leaving the entry in place also fails. The allow-list and
the cleanup stay in lockstep — an exemption cannot quietly become permanent.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Versions NexusMind currently deploys — same list as test_filter_config_schema.py.
ACTIVE_FILTERS = [
    ("solutions", "v6"),
    ("uplifting", "v7"),
    ("cultural_discovery", "v5"),
    ("investment_risk", "v6"),
    ("belonging", "v1"),
    ("nature_recovery", "v4"),
]

# (filter, version, issue) -> why it violates, and what closes it.
EXEMPTIONS = {
    ("cultural_discovery", "v5", "#94"): (
        "GATEKEEPER_CAP 4.0 == medium threshold 4.0, so a gatekept article stays "
        "exactly at the op-point and remains visible. The gatekeeper fires on 34.8% "
        "of articles and has never changed an outcome. "
        "ALREADY FIXED IN v6 — that package declares no GATEKEEPER_DIMENSION at all "
        "(owner decision 2026-08-06, at the version bump). This entry survives only "
        "because v5 is still the version NexusMind runs; delete it in the same commit "
        "that moves cultural_discovery to v6 in ACTIVE_FILTERS."
    ),
    ("solutions", "v6", "#94"): (
        "GATEKEEPER_CAP 3.0 > medium threshold 2.25. The scorer's own comment calls "
        "this intentional ('caps at 3.0 and DOES surface as medium') — that reasoning "
        "predates ADR-016/ADR-022, under which a tier is a badge and not an outcome. "
        "Measured: 0 binds in 191,616 production articles (#94). Closed by removing "
        "the gatekeeper block at the next solutions version bump, documenting that "
        "concreteness self-enforces via its 0.20 weight."
    ),
}


def _scorer_class(name, version):
    """Load the filter's scorer class from its base_scorer.py without importing the
    package (filter dirs are not importable modules)."""
    path = REPO_ROOT / "filters" / name / version / "base_scorer.py"
    spec = importlib.util.spec_from_file_location(f"{name}_{version}_base_scorer", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for attr in vars(mod).values():
        if (isinstance(attr, type) and attr.__name__ != "FilterBaseScorer"
                and hasattr(attr, "TIER_THRESHOLDS") and attr.__module__ == spec.name):
            return attr
    raise AssertionError(f"no scorer class with TIER_THRESHOLDS in {path}")


def _medium_threshold(cls):
    for tier_name, threshold, _desc in cls.TIER_THRESHOLDS:
        if tier_name == "medium":
            return float(threshold)
    raise AssertionError(f"{cls.__name__} has no 'medium' tier — op-point is undefined")


def _violates(name, version):
    """(violates, cap, medium) for one filter. A filter with no gatekeeper never
    violates: declaring nothing is not the failure mode this guards."""
    cls = _scorer_class(name, version)
    if getattr(cls, "GATEKEEPER_DIMENSION", None) is None:
        return False, None, None
    cap = float(cls.GATEKEEPER_CAP)
    medium = _medium_threshold(cls)
    return cap >= medium, cap, medium


@pytest.mark.parametrize("name,version", ACTIVE_FILTERS)
def test_gatekeeper_cap_is_below_the_surfacing_threshold(name, version):
    violates, cap, medium = _violates(name, version)
    exempt = any(k[0] == name and k[1] == version for k in EXEMPTIONS)
    if exempt:
        pytest.skip(f"{name} {version}: known-inert gatekeeper, exempted under #94")
    assert not violates, (
        f"{name} {version}: GATEKEEPER_CAP {cap} >= medium threshold {medium}. "
        f"Capping an article at {cap} leaves it at or above the op-point, so the "
        f"gatekeeper can never change visibility — the only outcome a filter has "
        f"under ADR-016/ADR-022. Either lower the cap below {medium} (needs a "
        f"measured recall check first, ADR-021) or remove the gatekeeper and "
        f"document that the dimension self-enforces via its weight."
    )


@pytest.mark.parametrize("key", sorted(EXEMPTIONS, key=str))
def test_every_exemption_matches_a_real_violation(key):
    """An exemption that no longer describes a live violation must be deleted, or the
    allow-list silently outlives the drift it was granted for."""
    name, version, issue = key
    violates, cap, medium = _violates(name, version)
    assert violates, (
        f"{name} {version} no longer violates the invariant (cap {cap}, medium "
        f"{medium}) — delete its {issue} entry from EXEMPTIONS."
    )


def test_exemptions_only_cover_active_filters():
    active = {(n, v) for n, v in ACTIVE_FILTERS}
    for name, version, issue in EXEMPTIONS:
        assert (name, version) in active, (
            f"{name} {version} ({issue}) is exempted but is not in ACTIVE_FILTERS — "
            f"an exemption for an undeployed filter guards nothing."
        )


def test_the_invariant_actually_fires_on_the_known_dead_gatekeepers():
    """Guards the guard: if a refactor made _violates() always return False, every
    parametrized case above would pass vacuously and the test would look green."""
    for name, version, _issue in EXEMPTIONS:
        violates, _cap, _medium = _violates(name, version)
        assert violates, f"{name} {version} should still trip the invariant"


def test_a_gatekeeper_that_can_exclude_passes():
    """nature_recovery v4 is the shape the invariant is written for: cap 3.5 sits
    below the 3.75 op-point, so a gatekept article is actually hidden."""
    violates, cap, medium = _violates("nature_recovery", "v4")
    assert not violates
    assert cap < medium


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
