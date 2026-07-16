"""The normalization fit-convention, as an executable invariant.

ADR-014 says the CDF is fitted from "production MEDIUM+ data" — i.e. articles at
or above the filter's own tier threshold. Every filter followed that convention;
nobody wrote it down; nothing checked it. The two filters that drifted off it are
the only two normalization incidents this project has had:

    foresight v1        raw_min 5.01  drifted HIGH -> NexusMind #205
                        Production articles at raw 4.60 clamped to wavg 0.02 via
                        np.interp's edge behaviour. Guarded after the fact by
                        MAX_NORMALIZATION_RAW_MIN = 4.5 in production_scorer.py,
                        which now rejects the fit at load and falls back to
                        score_scale_factor.

    nature_recovery v2  raw_min 1.50  drifted LOW  -> NexusMind #161
                        Fit-set median 2.19, so doom articles the model had
                        correctly scored 2.2-3.3 mapped to normalized 5.2-8.3 and
                        reached the Recovery lens at up to 8.34/10 "high". Was
                        misdiagnosed as a model failure and patched with a
                        keyword cap that took 14 months to retire.

Both are the same defect — raw_min off the tier threshold — in opposite
directions, and this one assertion catches both. There was a guard for the high
side (added reactively after #205) and none for the low side until 2026-07-14.

Deliberately globs the filesystem rather than reading a hand-maintained list:
tests/unit/test_filter_config_schema.py's ACTIVE_FILTERS is stale (it still names
cultural_discovery v4 and nature_recovery v2 while v5 and v4 are deployed), which
is exactly the rot this test must not inherit.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent

# Import the REAL resolver rather than re-implementing it. The first version of
# this test carried a private copy of _op_point_from_base_scorer, and the copy had
# already drifted within the same commit — it omitted the multiple-definition
# ambiguity check added alongside it, so the two disagreed on precisely the input
# the fix targeted. A test that reimplements its subject tests the reimplementation.
_spec = importlib.util.spec_from_file_location(
    "fit_normalization", REPO_ROOT / "scripts" / "normalization" / "fit_normalization.py"
)
_fitter = importlib.util.module_from_spec(_spec)
sys.modules["fit_normalization"] = _fitter
_spec.loader.exec_module(_fitter)

# The consumer's upper bound (NexusMind production_scorer.py). Above this,
# ProductionScorer rejects the CDF at load and silently falls back to the linear
# score_scale_factor — the #205 failure mode.
MAX_RAW_MIN = _fitter.MAX_NORMALIZATION_RAW_MIN

# Filters allowed to violate the invariant, each with the incident that made it
# permanent. Every entry must remain a REAL violation — test_no_stale_normalization_exemptions
# fails if someone refits one and forgets to remove its exemption.
EXEMPTIONS = {
    ("foresight", "v1"): (
        "raw_min 5.01 — NexusMind#205. Fit from already-filtered output rather "
        "than a representative production slice. PARKED (#43, merging into "
        "solutions v4) and rejected at load by MAX_NORMALIZATION_RAW_MIN=4.5, so "
        "it cannot reach production. Do not refit; the filter is being retired."
    ),
    ("nature_recovery", "v1"): (
        "raw_min 1.51 — the original NexusMind#161 defect. Superseded by v4 "
        "(deployed 2026-07-10). Package retained for history only."
    ),
    ("nature_recovery", "v2"): (
        "raw_min 1.50 — NexusMind#161. Superseded by v4 but kept as the "
        "rollback fallback, so the file must stay as-is: refitting it would "
        "change what a rollback restores."
    ),
}

# raw_min is the SMALLEST SCORE OBSERVED in the fit set, not the --min-score
# parameter. On a dense fit it lands essentially on the threshold (invR v6:
# 4.0003, cd v5: 4.0006 — note: not exactly 4.0), but on a sparser one the lowest
# article can sit a little above it. So the invariant is a tight RANGE, not
# equality (an earlier equality form false-positived on legitimate jitter) — but
# the range must stay ANCHORED TO THE OP-POINT:
#
#   raw_min <  op_point                          -> sub-visibility content maps
#                                                   into the visible band (#161)
#   raw_min >  op_point + ABOVE_OP_POINT_MARGIN   -> the band [op_point, raw_min)
#                                                   clamps to ~0 at inference (#205)
#
# The upper bound is DELIBERATELY NOT MAX_RAW_MIN (4.5). 4.5 is the consumer's hard
# *reject* bound — above it the loader drops the file entirely. Between op_point and
# 4.5 the loader ACCEPTS the file and silently clamps the band: that gap is the blind
# spot this test exists to catch. A round-3 review (2026-07-16) found the bound had
# been set to 4.5, which for a low-op-point filter (nature_recovery op 3.75) blesses a
# fit at raw_min 4.3 that hides the entire [3.75, 4.3) medium band. Every deployed
# filter lands within +0.0006 of its op-point; 0.25 absorbs sparse-fit jitter while
# still catching real #205 drift. EPS absorbs float round-tripping at the lower bound.
EPS = 0.01
ABOVE_OP_POINT_MARGIN = 0.25


def _within_invariant(raw_min, op_point):
    """The ONE place the raw_min band is defined. Both the per-filter test and the
    stale-exemptions test call this — a second inlined copy is exactly how the
    round-1 fix and its own test drifted apart within a single commit."""
    return op_point - EPS <= raw_min <= op_point + ABOVE_OP_POINT_MARGIN


def _fitted_filters():
    """Every filter package carrying a fitted normalization.json."""
    out = []
    for path in sorted(REPO_ROOT.glob("filters/*/v*/normalization.json")):
        out.append((path.parent.parent.name, path.parent.name))
    return out


def _raw_min(filter_name: str, version: str):
    path = REPO_ROOT / "filters" / filter_name / version / "normalization.json"
    return json.loads(path.read_text(encoding="utf-8")).get("stats", {}).get("raw_min")


def test_some_filters_are_fitted():
    """Guards the glob: if it silently matched nothing, every parametrized test
    below would vacuously pass."""
    assert len(_fitted_filters()) >= 5


@pytest.mark.parametrize("filter_name,version", _fitted_filters(),
                         ids=lambda x: str(x))
def test_normalization_fitted_at_the_tier_threshold(filter_name, version):
    """normalization.json's raw_min must sit AT the filter's tier threshold.

    raw_min is the lowest score in the fit set, so it lands just above the op-point
    on a dense fit and a little higher on a sparse one — the valid band is
    [op_point, op_point + ABOVE_OP_POINT_MARGIN], NOT up to the consumer's 4.5
    reject bound.

    Fit BELOW op_point and you map sub-visibility content into the visible band
    (NexusMind#161). Fit ABOVE it and everything in [op_point, raw_min) clamps to
    ~0 via np.interp's edge behaviour (NexusMind#205).
    """
    if (filter_name, version) in EXEMPTIONS:
        pytest.skip(f"{filter_name}/{version}: {EXEMPTIONS[(filter_name, version)]}")

    raw_min = _raw_min(filter_name, version)
    op_point = _fitter._op_point_from_base_scorer(REPO_ROOT / "filters" / filter_name / version)

    assert raw_min is not None, f"{filter_name}/{version}: normalization.json has no stats.raw_min"
    assert op_point is not None, (
        f"{filter_name}/{version}: cannot resolve TIER_THRESHOLDS, so the fit "
        f"threshold cannot be validated. If tiers were dropped per ADR-016, this "
        f"invariant needs rewriting against whatever replaced them — do not just "
        f"exempt the filter."
    )
    assert _within_invariant(raw_min, op_point), (
        f"{filter_name}/{version}: raw_min={raw_min} outside the valid range "
        f"[{op_point}, {op_point + ABOVE_OP_POINT_MARGIN}] (tier threshold .. threshold "
        f"+ {ABOVE_OP_POINT_MARGIN} jitter margin). "
        + (
            f"Fitting BELOW the threshold maps sub-visibility articles into the "
            f"visible band — this is NexusMind#161 (v2 fitted at 1.5, doom at raw "
            f"2.2-3.3 surfaced at normalized 5.2-8.3)."
            if raw_min < op_point else
            f"raw_min sits {raw_min - op_point:.2f} above the threshold: everything in "
            f"[{op_point}, {raw_min}) clamps to ~0 — this is NexusMind#205 (foresight "
            f"fitted at 5.01, raw 4.60 -> wavg 0.02). The band ({op_point + ABOVE_OP_POINT_MARGIN}, "
            f"{MAX_RAW_MIN}] is the blind spot the consumer's load-time guard MISSES: it only "
            f"rejects raw_min > {MAX_RAW_MIN}, so a fit here is ACCEPTED and clamps silently."
        )
        + f" Refit with --min-score {op_point} (the fitter now defaults to this)."
    )


def test_no_stale_normalization_exemptions():
    """Every exemption must still describe a real violation. Refit a filter and
    forget to drop its exemption, and the allow-list silently rots — the same
    decay this whole test exists to prevent."""
    stale = []
    for (filter_name, version), reason in EXEMPTIONS.items():
        path = REPO_ROOT / "filters" / filter_name / version / "normalization.json"
        if not path.exists():
            stale.append(f"{filter_name}/{version}: exempted but has no normalization.json")
            continue
        raw_min = _raw_min(filter_name, version)
        op_point = _fitter._op_point_from_base_scorer(REPO_ROOT / "filters" / filter_name / version)
        if raw_min is None or op_point is None:
            continue
        if _within_invariant(raw_min, op_point):
            stale.append(
                f"{filter_name}/{version}: now conforms (raw_min={raw_min} within "
                f"[{op_point}, {op_point + ABOVE_OP_POINT_MARGIN}]) — remove its EXEMPTIONS entry"
            )
    assert not stale, "Stale normalization exemptions:\n  " + "\n  ".join(stale)


def test_exemptions_name_their_incident():
    """An exemption without a reason is just a silent allowance. Each must cite
    the incident, so the next reader learns why rather than assuming it's fine."""
    for key, reason in EXEMPTIONS.items():
        assert len(reason) > 40, f"{key}: exemption reason too thin to be useful"
        assert "#" in reason, f"{key}: exemption must cite the issue that caused it"
