"""Tests for the deploy pre-flight guards.

Every guard here exists because a real defect got past documentation on
2026-08-12. So each one is tested BOTH ways: it must fire on the defect it was
built for, and it must stay quiet on the corresponding healthy case. A guard
only verified on the healthy case is indistinguishable from a disabled guard —
which is the exact failure mode (`use_prefilter=False`, NM#284) this repo has
already shipped once for six months.
"""

from __future__ import annotations

import textwrap

import pytest

from scripts.deployment.preflight_deploy_guards import (
    GuardFailure,
    check_cutover,
    check_manifest_scope,
    check_tiers_documented,
)

BASE_SCORER = textwrap.dedent(
    '''
    class Scorer:
        TIER_THRESHOLDS = [
            ("high", 7.0, "high desc"),
            ("medium", 4.0, "medium desc"),
            ("low", 0.0, "low desc"),
        ]
    '''
)

CONFIG_WITH_TIERS = textwrap.dedent(
    """
    scoring:
      dimensions:
        a: {weight: 1.0}
      tiers:
        high:
          threshold: 7.0
          description: high desc
        medium:
          threshold: 4.0
          description: medium desc
        low:
          threshold: 0.0
          description: low desc
    """
)

CONFIG_NO_TIERS = textwrap.dedent(
    """
    scoring:
      dimensions:
        a: {weight: 1.0}
    """
)


def _mkfilter(tmp_path, config_text, base_scorer_text=BASE_SCORER):
    d = tmp_path / "filters" / "demo" / "v3"
    d.mkdir(parents=True)
    (d / "config.yaml").write_text(config_text)
    if base_scorer_text is not None:
        (d / "base_scorer.py").write_text(base_scorer_text)
    return d


# --- Guard A: manifest scope ------------------------------------------------


def test_manifest_rejects_per_filter_entry(tmp_path):
    """The defect: an entry under filters/{name}/v{N}/ is accepted and does nothing."""
    m = tmp_path / ".nexusmind-owns"
    m.write_text("filters/cultural_discovery/v5/config.yaml\n")
    with pytest.raises(GuardFailure, match="CANNOT protect"):
        check_manifest_scope(m)


def test_manifest_rejects_non_common_filters_path(tmp_path):
    m = tmp_path / ".nexusmind-owns"
    m.write_text("filters/investment_risk/prefilter.py\n")
    with pytest.raises(GuardFailure, match="CANNOT protect"):
        check_manifest_scope(m)


def test_manifest_allows_common_entry(tmp_path):
    """Control: filters/common/ IS honoured, so it must not fire."""
    m = tmp_path / ".nexusmind-owns"
    m.write_text("filters/common/hybrid_scorer.py\n")
    assert check_manifest_scope(m)  # returns notes, does not raise


def test_manifest_rejects_windows_separators(tmp_path):
    """Found by review 2026-08-12: the denylist accepted backslash paths, and the
    default box IS the Windows one. The consumer compares POSIX paths."""
    m = tmp_path / ".nexusmind-owns"
    m.write_text("filters\\cultural_discovery\\v5\\config.yaml\n")
    with pytest.raises(GuardFailure, match="CANNOT protect"):
        check_manifest_scope(m)


def test_manifest_rejects_leading_dot_slash(tmp_path):
    """`./filters/common/x.py` was ACCEPTED by the guard but the consumer does an
    exact string match, so it protected nothing. The guard must not be more
    permissive than the thing it guards."""
    m = tmp_path / ".nexusmind-owns"
    m.write_text("./filters/common/hybrid_scorer.py\n")
    with pytest.raises(GuardFailure, match="CANNOT protect"):
        check_manifest_scope(m)


@pytest.mark.parametrize("entry", ["src/scoring/production_scorer.py", "docs/NORMALIZATION_METHOD.md"])
def test_manifest_rejects_paths_outside_filters_common(tmp_path, entry):
    """These are not per-filter paths, so a denylist keyed on filters/ missed
    them — and they protect nothing either."""
    m = tmp_path / ".nexusmind-owns"
    m.write_text(entry + "\n")
    with pytest.raises(GuardFailure, match="CANNOT protect"):
        check_manifest_scope(m)


def test_manifest_ignores_comments_and_blanks(tmp_path):
    m = tmp_path / ".nexusmind-owns"
    m.write_text("# filters/demo/v1/config.yaml\n\n   \nfilters/common/x.py\n")
    assert check_manifest_scope(m)


def test_manifest_absent_is_not_a_failure(tmp_path):
    assert check_manifest_scope(tmp_path / ".nexusmind-owns")


# --- Guard B: tiers documented ---------------------------------------------


def test_missing_tiers_block_fails(tmp_path):
    """The cultural_discovery v5/v6 defect, reproduced."""
    d = _mkfilter(tmp_path, CONFIG_NO_TIERS)
    with pytest.raises(GuardFailure, match="no `scoring.tiers` block"):
        check_tiers_documented(d)


def test_tiers_disagreeing_with_runtime_fails(tmp_path):
    """A block that exists but lies is worse than one that is absent."""
    bad = CONFIG_WITH_TIERS.replace("threshold: 4.0", "threshold: 3.0")
    d = _mkfilter(tmp_path, bad)
    with pytest.raises(GuardFailure, match="DISAGREES"):
        check_tiers_documented(d)


def test_matching_tiers_pass(tmp_path):
    """Control: the healthy case must stay quiet, and report the op-point."""
    d = _mkfilter(tmp_path, CONFIG_WITH_TIERS)
    notes = check_tiers_documented(d)
    assert any("4.0" in n for n in notes), notes


def test_base_scorer_without_thresholds_fails(tmp_path):
    d = _mkfilter(tmp_path, CONFIG_WITH_TIERS, base_scorer_text="class S:\n    pass\n")
    with pytest.raises(GuardFailure, match="no TIER_THRESHOLDS"):
        check_tiers_documented(d)


def test_two_differing_threshold_blocks_abort(tmp_path):
    """The regex version silently took the FIRST block, so a legacy class above
    the live one would be blessed as 'what actually runs'. fit_normalization.py
    already fails closed on exactly this; the guard must too."""
    two = BASE_SCORER + textwrap.dedent(
        '''
        class Legacy:
            TIER_THRESHOLDS = [
                ("high", 7.0, "x"),
                ("medium", 2.25, "x"),
                ("low", 0.0, "x"),
            ]
        '''
    )
    d = _mkfilter(tmp_path, CONFIG_WITH_TIERS, base_scorer_text=two)
    with pytest.raises(GuardFailure, match="MULTIPLE differing"):
        check_tiers_documented(d)


def test_two_identical_threshold_blocks_are_fine(tmp_path):
    """Control: duplication is only a problem when the values disagree."""
    two = BASE_SCORER + BASE_SCORER.replace("class Scorer", "class Same")
    d = _mkfilter(tmp_path, CONFIG_WITH_TIERS, base_scorer_text=two)
    assert check_tiers_documented(d)


def test_single_quoted_thresholds_are_read_not_silently_empty(tmp_path):
    """The regex required double quotes, so single quotes parsed to {} and — when
    the config also parsed to {} — the two empties compared EQUAL and passed."""
    d = _mkfilter(tmp_path, CONFIG_WITH_TIERS, base_scorer_text=BASE_SCORER.replace('"', "'"))
    assert check_tiers_documented(d)


def test_tier_entry_without_threshold_key_fails(tmp_path):
    """A declared-but-thresholdless tier is how investment_risk v6's phantom
    `medium_high: 5.0` survived."""
    bad = CONFIG_WITH_TIERS + "    medium_high:\n      description: phantom\n"
    d = _mkfilter(tmp_path, bad)
    with pytest.raises(GuardFailure, match="malformed|DIFFERENT SET"):
        check_tiers_documented(d)


def test_extra_tier_in_config_fails_on_key_set(tmp_path):
    extra = CONFIG_WITH_TIERS + "    medium_high:\n      threshold: 5.0\n      description: phantom\n"
    d = _mkfilter(tmp_path, extra)
    with pytest.raises(GuardFailure, match="DIFFERENT SET"):
        check_tiers_documented(d)


def test_scalar_tier_shape_does_not_traceback(tmp_path):
    """`tiers: {high: 7.0, ...}` used to raise an uncaught TypeError, which is
    off-contract (documented exits are 0/1/2). fit_normalization handles it."""
    scalar = textwrap.dedent(
        """
        scoring:
          dimensions:
            a: {weight: 1.0}
          tiers: {high: 7.0, medium: 4.0, low: 0.0}
        """
    )
    d = _mkfilter(tmp_path, scalar)
    assert check_tiers_documented(d)  # values match runtime; must not raise


def test_no_base_scorer_skips_rather_than_passing_silently(tmp_path):
    d = _mkfilter(tmp_path, CONFIG_NO_TIERS, base_scorer_text=None)
    notes = check_tiers_documented(d)
    assert any("skipped" in n for n in notes), notes


# --- Guard C: cutover -------------------------------------------------------


def _mk_nexusmind(tmp_path, versions):
    root = tmp_path / "nm"
    d = root / "filters" / "demo"
    d.mkdir(parents=True)
    for v in versions:
        (d / v).mkdir()
    return root


def test_higher_version_is_flagged_as_cutover(tmp_path):
    root = _mk_nexusmind(tmp_path, ["v4", "v5"])
    notes = check_cutover("demo", "v6", root)
    assert any("VERSION CUTOVER" in n for n in notes), notes
    # It must NOT claim the deploy itself reaches readers — deploy_filters.sh
    # still has to ship it. Overclaiming that was a review blocker on 2026-08-12.
    assert any("not live yet" in n for n in notes), notes


def test_lower_version_ABORTS_rather_than_warning(tmp_path):
    """The inverse trap: deploying below the highest provably does nothing.

    It used to print a note and exit 0, so the script went on to `cp -r`, commit,
    optionally push, and print '=== Done ==='. A deploy that cannot take effect
    must fail, not narrate."""
    root = _mk_nexusmind(tmp_path, ["v4", "v7"])
    with pytest.raises(GuardFailure, match="BELOW NexusMind's highest"):
        check_cutover("demo", "v5", root)


def test_missing_nexusmind_root_aborts(tmp_path):
    """A typo'd NEXUSMIND_ROOT used to yield a confident 'this CREATES it'."""
    with pytest.raises(GuardFailure, match="does not exist"):
        check_cutover("demo", "v1", tmp_path / "nope")


def test_non_version_shaped_aborts(tmp_path):
    root = _mk_nexusmind(tmp_path, ["v4"])
    with pytest.raises(GuardFailure, match="not vN-shaped"):
        check_cutover("demo", "latest", root)


def test_equal_version_is_in_place_replacement(tmp_path):
    root = _mk_nexusmind(tmp_path, ["v4", "v5"])
    notes = check_cutover("demo", "v5", root)
    assert any("in place" in n for n in notes), notes


def test_absent_filter_dir_reports_creation(tmp_path):
    root = tmp_path / "nm"
    (root / "filters").mkdir(parents=True)
    notes = check_cutover("demo", "v1", root)
    assert any("CREATES" in n for n in notes), notes


# --- The real packages ------------------------------------------------------


@pytest.mark.parametrize(
    "name,version",
    [
        ("solutions", "v6"),
        ("uplifting", "v7"),
        ("cultural_discovery", "v5"),
        ("cultural_discovery", "v6"),
        ("investment_risk", "v6"),
        ("belonging", "v1"),
        ("nature_recovery", "v4"),
    ],
)
def test_deployed_packages_document_their_tiers(name, version):
    """Regression lock: cultural_discovery v5 and v6 both failed this on
    2026-08-12 and were fixed the same day. v6 is included deliberately — it is
    not yet in NexusMind, and `_find_latest_version()` would make it live on
    arrival, so there is no later moment to catch it."""
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    d = repo / "filters" / name / version
    if not d.is_dir():
        pytest.skip(f"{name} {version} not on disk")
    check_tiers_documented(d)  # raises GuardFailure if it regresses


def test_repo_manifest_scope_is_valid():
    """The live `.nexusmind-owns` must never name a path it cannot protect."""
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    check_manifest_scope(repo / ".nexusmind-owns")
