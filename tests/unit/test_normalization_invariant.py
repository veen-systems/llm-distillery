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

# raw_min is the CDF's lower coverage edge. Since 2026-07-16 the fitter ANCHORS
# it to the op-point (fit_normalization's anchor_min extends the lookup table
# down to the threshold with a 0-percentile breakpoint), so a new fit satisfies
# raw_min == op_point BY CONSTRUCTION, however sparse the sample. That dissolves
# the margin question a round-3 fix wrestled with (equality false-positived on
# sample-minimum jitter; a 4.5 bound blessed silent-clamp fits; a 0.25 margin
# would have false-failed the first sparse needle fit): the invariant is
# near-equality again, and the epsilon covers only float round-tripping plus the
# pre-anchor legacy fits, whose raw_min is the sample minimum and sits within
# +0.0006 of the op-point on every conforming filter.
#
# EPS is IMPORTED from the fitter, whose post-fit guard enforces the same band —
# two independently-chosen values is exactly how the round-3 fitter and test
# came to disagree on which files are writable (round-4 finding, 2026-07-16).
EPS = _fitter.OP_POINT_EPS


def _within_invariant(raw_min, op_point):
    """The ONE place the raw_min band is defined. Both the per-filter test and the
    stale-exemptions test call this — a second inlined copy is exactly how the
    round-1 fix and its own test drifted apart within a single commit.

    The second disjunct mirrors the fitter's post-fit guard exactly: unreachable
    for today's op-points (3.75/4.0, both far below 4.5), but without it an
    op-point of e.g. 4.495 could bless raw_min 4.505 — within EPS of its op-point
    yet strictly above the consumer's reject bound, i.e. the test accepting a
    file the loader rejects."""
    return abs(raw_min - op_point) <= EPS and raw_min <= MAX_RAW_MIN


def _fitted_filters():
    """Every filter package carrying a fitted normalization.json."""
    out = []
    for path in sorted(REPO_ROOT.glob("filters/*/v*/normalization.json")):
        out.append((path.parent.parent.name, path.parent.name))
    return out


def _stat(filter_name: str, version: str, key: str):
    path = REPO_ROOT / "filters" / filter_name / version / "normalization.json"
    return json.loads(path.read_text(encoding="utf-8")).get("stats", {}).get(key)


def test_some_filters_are_fitted():
    """Guards the glob: if it silently matched nothing, every parametrized test
    below would vacuously pass."""
    assert len(_fitted_filters()) >= 5


@pytest.mark.parametrize("filter_name,version", _fitted_filters(),
                         ids=lambda x: str(x))
def test_normalization_fitted_at_the_tier_threshold(filter_name, version):
    """normalization.json's raw_min must sit AT the filter's tier threshold.

    The fitter anchors the CDF's lower edge to the op-point, so a conforming fit
    has raw_min == op_point exactly; legacy pre-anchor fits sit within +0.0006.
    EPS covers both.

    Fit BELOW op_point and you map sub-visibility content into the visible band
    (NexusMind#161). A raw_min ABOVE op_point means the CDF doesn't cover
    [op_point, raw_min): up to 4.5 the consumer ACCEPTS the file and silently
    clamps that band to ~0 (the load guard's blind spot); above 4.5 it REJECTS
    the file at load and silently falls back to score_scale_factor (#205).
    """
    if (filter_name, version) in EXEMPTIONS:
        pytest.skip(f"{filter_name}/{version}: {EXEMPTIONS[(filter_name, version)]}")

    raw_min = _stat(filter_name, version, "raw_min")
    op_point = _fitter._op_point_from_base_scorer(REPO_ROOT / "filters" / filter_name / version)

    assert raw_min is not None, f"{filter_name}/{version}: normalization.json has no stats.raw_min"
    assert op_point is not None, (
        f"{filter_name}/{version}: cannot resolve TIER_THRESHOLDS, so the fit "
        f"threshold cannot be validated. If tiers were dropped per ADR-016, this "
        f"invariant needs rewriting against whatever replaced them — do not just "
        f"exempt the filter."
    )
    if raw_min < op_point - EPS:
        regime = (
            f"Fitting BELOW the threshold maps sub-visibility articles into the "
            f"visible band — this is NexusMind#161 (v2 fitted at 1.5, doom at raw "
            f"2.2-3.3 surfaced at normalized 5.2-8.3)."
        )
    elif raw_min <= MAX_RAW_MIN:
        regime = (
            f"raw_min sits {raw_min - op_point:.2f} above the threshold, at or under the "
            f"consumer's reject bound ({MAX_RAW_MIN}): NexusMind's ProductionScorer ACCEPTS "
            f"this file and silently clamps everything in [{op_point}, {raw_min}) to ~0 via "
            f"np.interp's edge behaviour — the load-time guard's blind spot, and the silent "
            f"variant of NexusMind#205."
        )
    else:
        regime = (
            f"raw_min sits {raw_min - op_point:.2f} above the threshold, OVER the consumer's "
            f"reject bound ({MAX_RAW_MIN}): NexusMind's ProductionScorer REJECTS this file at "
            f"load and silently falls back to the linear score_scale_factor — NexusMind#205 "
            f"proper (foresight fitted at 5.01, raw 4.60 -> wavg 0.02)."
        )
    assert _within_invariant(raw_min, op_point), (
        f"{filter_name}/{version}: raw_min={raw_min} is not at the tier threshold "
        f"{op_point} (±{EPS}). {regime} Refit with scripts/normalization/"
        f"fit_normalization.py — it anchors raw_min to the op-point by construction."
    )

    # Anchoring means raw_min can no longer expose a biased fit sample (it equals
    # the op-point by construction), so the bias signal moved to stats.sample_min —
    # the lowest score actually observed. Above the consumer bound it is the #205
    # ROOT-CAUSE signature (population drawn from already-filtered output): the
    # fitter refuses to write this on the deploy path, so a package file like it
    # arrived by a route that bypassed the fitter's guards. Legacy pre-anchor fits
    # lack the field (raw_min was the sample minimum there, checked above).
    sample_min = _stat(filter_name, version, "sample_min")
    if sample_min is not None:
        assert sample_min <= MAX_RAW_MIN, (
            f"{filter_name}/{version}: stats.sample_min={sample_min} exceeds "
            f"MAX_NORMALIZATION_RAW_MIN ({MAX_RAW_MIN}): no article in the fit population "
            f"reaches the visibility threshold, so the CDF ranks against a population "
            f"production never sees (the NexusMind#205 root cause — foresight was fitted "
            f"from oracle-biased output). Refit from a production-representative slice "
            f"(playbook §6)."
        )


def _write_synthetic_package(root: Path, sample_min: float):
    """A minimal anchored-fit package: raw_min pinned to the op-point (as the
    fitter guarantees by construction), sample_min set by the caller."""
    pkg = root / "filters" / "synthetic" / "v1"
    pkg.mkdir(parents=True)
    (pkg / "base_scorer.py").write_text(
        'TIER_THRESHOLDS = [("high", 7.0), ("medium", 3.75), ("low", 0.0)]\n',
        encoding="utf-8",
    )
    (pkg / "normalization.json").write_text(
        json.dumps({"stats": {"raw_min": 3.75, "sample_min": sample_min}}),
        encoding="utf-8",
    )


def test_sample_min_guard_fires_on_biased_anchored_fit(tmp_path, monkeypatch):
    """The sample_min assertion above is dead code against the committed packages
    — all 10 are legacy pre-anchor fits without the field (2026-07-17 review
    finding), so a regression in the one guard that catches the #205 ROOT cause
    for anchored fits (biased fit population, raw_min anchored green anyway)
    would ship without any test executing it. Drive the REAL parametrized test
    body against a synthetic anchored package so the whole path runs, including
    the stats-key lookup: sample_min above the consumer bound must fail..."""
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", tmp_path)
    _write_synthetic_package(tmp_path, sample_min=MAX_RAW_MIN + 0.5)
    with pytest.raises(AssertionError, match="sample_min"):
        test_normalization_fitted_at_the_tier_threshold("synthetic", "v1")


def test_sample_min_guard_passes_a_representative_fit(tmp_path, monkeypatch):
    """...and a representative population (sample_min under the bound) must pass,
    so the guard can't rot into rejecting every anchored fit either."""
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", tmp_path)
    _write_synthetic_package(tmp_path, sample_min=3.9)
    test_normalization_fitted_at_the_tier_threshold("synthetic", "v1")


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
        raw_min = _stat(filter_name, version, "raw_min")
        op_point = _fitter._op_point_from_base_scorer(REPO_ROOT / "filters" / filter_name / version)
        if raw_min is None or op_point is None:
            continue
        if _within_invariant(raw_min, op_point):
            stale.append(
                f"{filter_name}/{version}: now conforms (raw_min={raw_min} within "
                f"±{EPS} of op-point {op_point}) — remove its EXEMPTIONS entry"
            )
    assert not stale, "Stale normalization exemptions:\n  " + "\n  ".join(stale)


def test_exemptions_name_their_incident():
    """An exemption without a reason is just a silent allowance. Each must cite
    the incident, so the next reader learns why rather than assuming it's fine."""
    for key, reason in EXEMPTIONS.items():
        assert len(reason) > 40, f"{key}: exemption reason too thin to be useful"
        assert "#" in reason, f"{key}: exemption must cite the issue that caused it"
