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
import shutil
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

# The fit-sample bias bound, which is a GAP above the op-point and NOT the consumer
# bound above (#154, ruled 2026-09-22). These must stay two names: sharing one made
# the sample test a density test at a 4.5 op-point. Imported rather than restated so
# the fitter and this invariant cannot drift apart.
MAX_SAMPLE_GAP = _fitter.MAX_SAMPLE_GAP

# Filters allowed to violate the invariant, each with the incident that made it
# permanent. Every entry must remain a REAL violation — test_no_stale_normalization_exemptions
# fails if someone refits one and forgets to remove its exemption.
EXEMPTIONS = {
    # ("foresight", "v1") removed 2026-08-03 along with the filter package
    # itself — retirement into solutions (#43) completed, so there is no
    # normalization.json left to exempt. #64 (refit foresight normalization)
    # is superseded by that removal.
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

    The second disjunct mirrors the fitter's post-fit guard exactly. ⚠️ It was
    annotated "unreachable for today's op-points (3.75/4.0, both far below 4.5)"
    until 2026-09-22, when `human_thriving v8` joined this parametrization AT 4.5
    — reachable now, with ZERO margin (the comparison is a strict `>`). Without it an
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
        sample_gap = sample_min - op_point
        assert sample_gap <= MAX_SAMPLE_GAP, (
            f"{filter_name}/{version}: stats.sample_min={sample_min} sits {sample_gap:.4f} "
            f"above the op-point {op_point}, over MAX_SAMPLE_GAP ({MAX_SAMPLE_GAP}): no "
            f"article in the fit population reaches down to the visibility threshold, so the "
            f"CDF ranks against a population production never sees (the NexusMind#205 root "
            f"cause — foresight was fitted from oracle-biased output). Refit from a "
            f"production-representative slice (playbook §6)."
        )


def _write_synthetic_package(root: Path, sample_min: float, op_point: float = 3.75):
    """A minimal anchored-fit package: raw_min pinned to the op-point (as the
    fitter guarantees by construction), sample_min set by the caller. op_point is
    a parameter because the guard's whole defect (#154) was that it behaved
    differently at 4.5 than at the 3.75/4.0 it was written for."""
    pkg = root / "filters" / "synthetic" / "v1"
    pkg.mkdir(parents=True)
    (pkg / "base_scorer.py").write_text(
        f'TIER_THRESHOLDS = [("high", 7.0), ("medium", {op_point}), ("low", 0.0)]\n',
        encoding="utf-8",
    )
    (pkg / "normalization.json").write_text(
        json.dumps({"stats": {"raw_min": op_point, "sample_min": sample_min}}),
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


def test_sample_gap_admits_a_sparse_needle_fit_at_a_4_5_op_point(tmp_path, monkeypatch):
    """llm-distillery#154, the regression this guard's own constant caused. At an
    op-point of 4.5 the OLD rule (sample_min <= MAX_NORMALIZATION_RAW_MIN, also 4.5)
    could not be satisfied by any correct fit: the population is filtered AT 4.5, so
    its minimum is always above it. It hard-blocked `human_thriving v8`'s 202-row
    Phase E fit at sample_min 4.5069 — a gap of 0.0069 against the 0.5 the advisory tier
    then used (and which is now the hard limit), i.e. the signature it names absent by
    ~70x. ⚠️ Mutation, stated precisely because the count depends on which one you apply:
    replacing ONLY the predicate with `sample_min <= MAX_RAW_MIN` and keeping the message
    reddens THIS test alone (verified); replacing the predicate AND the message reddens
    three, because two others match on `MAX_SAMPLE_GAP` appearing in the text."""
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", tmp_path)
    _write_synthetic_package(tmp_path, sample_min=4.5069, op_point=4.5)
    test_normalization_fitted_at_the_tier_threshold("synthetic", "v1")


def test_sample_gap_still_fires_at_a_4_5_op_point(tmp_path, monkeypatch):
    """...and the #205 ROOT CAUSE must still be caught at that same op-point, or the
    fix traded a false block for a missing one. 5.2 against a 4.5 anchor is a gap of
    0.7: the [4.5, 5.2) band was never observed and would normalize onto a
    0-percentile ramp."""
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", tmp_path)
    _write_synthetic_package(tmp_path, sample_min=5.2, op_point=4.5)
    with pytest.raises(AssertionError, match="MAX_SAMPLE_GAP"):
        test_normalization_fitted_at_the_tier_threshold("synthetic", "v1")


def test_sample_gap_is_identical_at_op_point_4_0_only(tmp_path, monkeypatch):
    """⛔ At 4.0 AND NOWHERE ELSE. The name is the assertion, and an earlier version of it
    said "at the op_points the guard was written for" while testing 4.0 alone — the 2026-07-16
    promise it quoted was "no false-block possible for any real op-point (3.75/4.0)", and 3.75
    is exactly where the new rule is NOT identical. At 4.0, `sample_min > 4.5` and
    `gap > 0.5` are the same predicate: 4.51 fails, 4.49 passes."""
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", tmp_path)
    _write_synthetic_package(tmp_path, sample_min=4.49, op_point=4.0)
    test_normalization_fitted_at_the_tier_threshold("synthetic", "v1")

    shutil.rmtree(tmp_path / "filters")
    _write_synthetic_package(tmp_path, sample_min=4.51, op_point=4.0)
    with pytest.raises(AssertionError, match="MAX_SAMPLE_GAP"):
        test_normalization_fitted_at_the_tier_threshold("synthetic", "v1")


def test_sample_gap_is_deliberately_STRICTER_below_op_point_4_0(tmp_path, monkeypatch):
    """The other half of the same change, pinned so it is a decision and not a surprise.
    The old rule fired at `sample_min > 4.5`, i.e. at `gap > (4.5 - op_point)`, so below 4.0
    it was LOOSER than the new flat 0.5 — at `nature_recovery v4`'s 3.75 the old tolerance
    was 0.75 and only WARNED in (4.25, 4.5]; it now hard-fails. `solutions v4/v6` sit at 2.25,
    where the old tolerance was 2.25. No committed package is affected (largest gap on disk is
    nature_recovery v4 at 0.0438), but `nature_recovery v5` (#71) is the filter that would meet
    this. If this test ever becomes inconvenient, that is the policy question surfacing — do
    not relax it silently."""
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", tmp_path)
    # 4.3 at op-point 3.75: gap 0.55. OLD rule passed it (4.3 <= 4.5, advisory only).
    _write_synthetic_package(tmp_path, sample_min=4.3, op_point=3.75)
    with pytest.raises(AssertionError, match="MAX_SAMPLE_GAP"):
        test_normalization_fitted_at_the_tier_threshold("synthetic", "v1")

    # ...and the band that stays acceptable there is unchanged in kind: gap 0.3 passes.
    shutil.rmtree(tmp_path / "filters")
    _write_synthetic_package(tmp_path, sample_min=4.05, op_point=3.75)
    test_normalization_fitted_at_the_tier_threshold("synthetic", "v1")


def test_sample_gap_is_LOOSER_above_op_point_4_0(tmp_path, monkeypatch):
    """And the third direction, which no other test covers. At `investment_risk v6`'s 4.25
    the old bound fired at gap > 0.25; the flat 0.5 now admits up to 4.75. That filter is
    retired downstream (NexusMind ADR-025) so nothing is at risk today — this exists so the
    widening is on the record rather than discovered by the next filter to sit above 4.0."""
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", tmp_path)
    # 4.6 at op-point 4.25: gap 0.35. OLD rule HARD-ERRORED (4.6 > 4.5). Now accepted.
    _write_synthetic_package(tmp_path, sample_min=4.6, op_point=4.25)
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
