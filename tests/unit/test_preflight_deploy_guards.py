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
    ProbeUnavailable,
    _ssh_weights_probe,
    check_cutover,
    check_manifest_scope,
    check_tiers_documented,
    check_weights_backed_up,
    check_weights_channel,
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


# --- Guard D: the weights channel -------------------------------------------
#
# The defect: `deploy_filters.sh` excludes `model/` from BOTH rsync passes, so a
# code deploy never carries LoRA weights. Landing a version whose weights are not
# already on gpu-server makes the scorer refuse to START (it validates every
# discovered filter), so the cycle scores nothing for all six filters — unattended,
# because that deploy runs as ExecStartPre every four hours. Documented as
# FILTER_PLAYBOOK checklist item 5 since #67 closed; never enforced until now.


def _probe(answer):
    """Build a probe stub. `answer` is True/False, or an exception to raise."""

    def probe(gpu_host, filter_name, version):
        if isinstance(answer, Exception):
            raise answer
        return answer

    return probe


def test_absent_weights_abort_the_deploy():
    """The defect: code ships, weights don't, scorer never starts."""
    with pytest.raises(GuardFailure) as exc:
        check_weights_channel("cultural_discovery", "v6", probe=_probe(False))
    msg = str(exc.value)
    assert "NO weights" in msg
    # The remedy must be in the failure, not in a doc the reader has to find.
    assert "scp" in msg and "mkdir -p" in msg


def test_present_weights_stay_quiet():
    """The healthy case. A guard only tested on the defect can still be a guard
    that fires on everything."""
    notes = check_weights_channel("cultural_discovery", "v5", probe=_probe(True))
    assert any("weights present" in n for n in notes)


def test_unreachable_probe_fails_CLOSED():
    """'Could not ask' must not read as 'present'. This is the case that decides
    whether the guard is a safety device or a formality."""
    with pytest.raises(GuardFailure) as exc:
        check_weights_channel(
            "cultural_discovery", "v6", probe=_probe(ProbeUnavailable("no route to host"))
        )
    msg = str(exc.value)
    assert "Failing CLOSED" in msg
    assert "--weights-preplaced" in msg  # the documented way out is named


def test_unreachable_is_distinguishable_from_absent():
    """Two different facts with two different remedies. Collapsing them would
    make a VPN blip look like a missing adapter, and vice versa."""
    with pytest.raises(GuardFailure) as absent:
        check_weights_channel("f", "v2", probe=_probe(False))
    with pytest.raises(GuardFailure) as unreachable:
        check_weights_channel("f", "v2", probe=_probe(ProbeUnavailable("timeout")))
    assert str(absent.value) != str(unreachable.value)
    assert "Failing CLOSED" not in str(absent.value)


def test_ack_skips_the_probe_but_says_so_loudly():
    """The override exists for the offline case. It must not be able to pass
    silently — an override that reads like a pass is how a checkbox replaces a
    check."""
    called = []

    def probe(*a):
        called.append(a)
        return False

    notes = check_weights_channel("f", "v9", probe=probe, preplaced_ack=True)
    assert called == []  # the probe genuinely did not run
    assert any("SKIPPED" in n for n in notes)
    assert any("scores nothing" in n for n in notes)


# --- Guard D: the real ssh probe's answer parsing ---------------------------


def _fake_run(stdout="", returncode=0, exc=None):
    def run(*args, **kwargs):
        if exc is not None:
            raise exc
        class R:
            pass
        r = R()
        r.stdout = stdout
        r.stderr = ""
        r.returncode = returncode
        return r

    return run


@pytest.mark.parametrize(
    "stdout,expected",
    [("PRESENT\n", True), ("ABSENT\n", False)],
)
def test_ssh_probe_reads_both_answers(monkeypatch, stdout, expected):
    import subprocess

    monkeypatch.setattr(subprocess, "run", _fake_run(stdout=stdout))
    assert _ssh_weights_probe("gpu-host", "f", "v1") is expected


@pytest.mark.parametrize(
    "stdout,returncode",
    [
        ("", 255),            # ssh could not connect
        ("PRESENT\n", 255),   # exit code disagrees with the payload — trust neither
        ("bash: line 1: x\n", 0),  # a shell that answered something else entirely
        ("", 0),              # answered nothing at all
    ],
)
def test_ssh_probe_refuses_to_guess(monkeypatch, stdout, returncode):
    """Anything that is not exactly PRESENT/ABSENT with exit 0 is 'could not ask'.
    A probe that guesses on ambiguous output is worse than no probe, because it
    reports a verification that did not happen."""
    import subprocess

    monkeypatch.setattr(subprocess, "run", _fake_run(stdout=stdout, returncode=returncode))
    with pytest.raises(ProbeUnavailable):
        _ssh_weights_probe("gpu-host", "f", "v1")


def test_ssh_probe_maps_transport_errors(monkeypatch):
    """OSError (no ssh binary) and TimeoutExpired must not escape as themselves —
    the caller distinguishes ProbeUnavailable from every other exception."""
    import subprocess

    monkeypatch.setattr(subprocess, "run", _fake_run(exc=OSError("no ssh binary")))
    with pytest.raises(ProbeUnavailable):
        _ssh_weights_probe("gpu-host", "f", "v1")

    monkeypatch.setattr(
        subprocess, "run", _fake_run(exc=subprocess.TimeoutExpired("ssh", 30))
    )
    with pytest.raises(ProbeUnavailable):
        _ssh_weights_probe("gpu-host", "f", "v1")


def test_probe_asks_about_the_adapter_specifically(monkeypatch):
    """The remote command must name adapter_model.safetensors. An earlier draft
    tested the model/ DIRECTORY, which exists on gpu-server for a version whose
    weights were never pushed — the exact state this guard exists to catch."""
    import subprocess

    seen = {}

    def run(argv, **kwargs):
        seen["argv"] = argv
        class R:
            stdout, stderr, returncode = "PRESENT\n", "", 0
        return R()

    monkeypatch.setattr(subprocess, "run", run)
    _ssh_weights_probe("gpu-host", "cultural_discovery", "v6")
    remote = seen["argv"][-1]
    assert "adapter_model.safetensors" in remote
    assert "cultural_discovery/v6/model/" in remote
    assert "BatchMode=yes" in seen["argv"]  # never hang on a password prompt


# --- Caller parity ----------------------------------------------------------
#
# The 2026-08-12 review found `deploy_to_nexusmind.ps1` had NO Step 0.5 at all
# while the guard module's docstring called the `.sh` "the ONE chokepoint" — a
# documented alternative deploy path, one keystroke from bypassing every guard.
# That was fixed by hand, and nothing has since stopped the two from drifting
# apart again. These tests are that stop.


def _callers():
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    return (
        (repo / "scripts" / "deploy_to_nexusmind.sh").read_text(encoding="utf-8"),
        (repo / "scripts" / "deploy_to_nexusmind.ps1").read_text(encoding="utf-8"),
    )


def test_both_callers_invoke_the_guards():
    """The original defect: a second deploy path that skipped Step 0.5 entirely."""
    sh, ps1 = _callers()
    assert "preflight_deploy_guards.py" in sh
    assert "preflight_deploy_guards.py" in ps1


def test_callers_expose_the_same_guard_flags():
    """Derived from the parser, not restated. Any guard-weakening flag reachable
    from one deploy path must be reachable from the other — otherwise the two
    paths enforce different things and the weaker one wins by being available."""
    from scripts.deployment.preflight_deploy_guards import build_parser

    known = {
        opt
        for action in build_parser()._actions
        for opt in action.option_strings
        if opt.startswith("--")
    }
    sh, ps1 = _callers()
    in_sh = {f for f in known if f in sh}
    in_ps1 = {f for f in known if f in ps1}
    assert in_sh == in_ps1, (
        f"deploy caller drift — only in .sh: {sorted(in_sh - in_ps1)}, "
        f"only in .ps1: {sorted(in_ps1 - in_sh)}"
    )


# --- Guard E: weights exist in the backed-up tree ---------------------------
#
# The defect: three of six LIVE filters had no local copy of their adapter at
# all, so their only homes were employer hardware and a single-account private
# Hub repo — nothing Veen-owned, nothing off-site. Found by an infra session
# doing DR inventory, not by anyone here, because `filters/**/model/` is
# gitignored: two sessions searched and concluded the weights were absent. The
# four filters that WERE protected were protected by accident (restic walks the
# filesystem), not by decision. This guard replaces the accident.


def test_absent_weights_abort_the_deploy(tmp_path):
    """The defect state: a version whose weights live nowhere we control."""
    d = tmp_path / "filters" / "demo" / "v3"
    (d / "model").mkdir(parents=True)
    with pytest.raises(GuardFailure) as exc:
        check_weights_backed_up(d)
    msg = str(exc.value)
    assert "no local copy" in msg
    # The failure must name why the usual checks won't show it, or the reader
    # re-runs `git status`, sees nothing, and concludes the guard is wrong.
    assert "gitignored" in msg
    assert "hf_hub_download" in msg or "huggingface_hub" in msg  # remedy included


def test_present_weights_stay_quiet(tmp_path):
    d = tmp_path / "filters" / "demo" / "v3"
    (d / "model").mkdir(parents=True)
    (d / "model" / "adapter_model.safetensors").write_bytes(b"x" * 2048)
    notes = check_weights_backed_up(d)
    assert any("weights present locally" in n for n in notes)


def test_empty_adapter_is_worse_than_absent(tmp_path):
    """A zero-length file satisfies every presence check and restores as a
    corrupt model. It must not read as protected.

    Not hypothetical: the same session that created this guard left sixteen
    zero-length .lock files behind while mirroring the weights, and its own
    size-based check passed because the real files were fine alongside them.
    """
    d = tmp_path / "filters" / "demo" / "v3"
    (d / "model").mkdir(parents=True)
    (d / "model" / "adapter_model.safetensors").write_bytes(b"")
    with pytest.raises(GuardFailure) as exc:
        check_weights_backed_up(d)
    assert "EMPTY" in str(exc.value)


def test_missing_model_dir_is_the_same_failure(tmp_path):
    """No model/ dir at all was the actual shape of all three real gaps."""
    d = tmp_path / "filters" / "demo" / "v3"
    d.mkdir(parents=True)
    with pytest.raises(GuardFailure):
        check_weights_backed_up(d)


@pytest.mark.parametrize(
    "name,version",
    [
        ("solutions", "v6"),
        ("uplifting", "v7"),
        ("cultural_discovery", "v6"),
        ("investment_risk", "v6"),
        ("belonging", "v1"),
        ("nature_recovery", "v4"),
    ],
)
def test_every_live_filter_has_a_backed_up_copy(name, version):
    """Regression lock on the real tree, not a fixture.

    Three of these six failed this on 2026-08-13 and were fixed the same day.
    Pinned because the failure mode is silent by construction — nothing in git,
    nothing in a grep, and the backup keeps succeeding while covering less.
    """
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    d = repo / "filters" / name / version
    if not d.is_dir():
        pytest.skip(f"{name} {version} not on disk")
    check_weights_backed_up(d)  # raises GuardFailure if it regresses
