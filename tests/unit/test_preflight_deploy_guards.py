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
    # It must NOT claim the deploy itself reaches readers — NexusMind still has to
    # rebuild the scorer image (#395). Overclaiming that was a review blocker on 2026-08-12.
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


# --- Guard D: this checkout's adapter vs its Hub copy -----------------------
#
# Since NexusMind#395 (2026-09-29) production scores from a container image that
# NexusMind's `deploy/scorer-image/stage.py` builds from an llm-distillery checkout's
# adapters, refusing one that differs from the Hub. A mismatch here would fail their
# build after merge. Until 2026-10-09 this guard asked gpu-server over ssh instead
# (FILTER_PLAYBOOK item 5, #67); that probe and its tests are in git history.


def _pkg(tmp_path, repo_id="jeergrvgreg/demo-filter-v3"):
    """A package dir with an adapter and (unless None) an inference_hub.py repo_id."""
    (tmp_path / "model").mkdir(exist_ok=True)
    (tmp_path / "model" / "adapter_model.safetensors").write_bytes(b"w")
    if repo_id is not None:
        (tmp_path / "inference_hub.py").write_text(f'    repo_id: str = "{repo_id}"\n')
    return tmp_path


def _probe(answer):
    """Probe stub. `answer` is (local, hub), or an exception to raise."""

    def probe(filter_dir, filter_name, version):
        if isinstance(answer, Exception):
            raise answer
        return answer

    return probe


def test_mismatch_aborts_the_deploy(tmp_path):
    with pytest.raises(GuardFailure) as exc:
        check_weights_channel("f", "v2", _pkg(tmp_path), probe=_probe(("a" * 64, "b" * 64)))
    msg = str(exc.value)
    assert "DIFFERS" in msg
    assert "upload_to_huggingface.py" in msg  # the remedy is in the failure


def test_match_stays_quiet(tmp_path):
    notes = check_weights_channel("f", "v2", _pkg(tmp_path), probe=_probe(("a" * 64, "a" * 64)))
    assert any("matches its Hub copy" in n for n in notes)


def test_unreachable_hub_fails_CLOSED(tmp_path):
    with pytest.raises(GuardFailure) as exc:
        check_weights_channel("f", "v2", _pkg(tmp_path), probe=_probe(ProbeUnavailable("404")))
    msg = str(exc.value)
    assert "Failing CLOSED" in msg
    assert "--weights-preplaced" in msg
    assert "check_adapter_matches_hub.py f v2" in msg


def test_unreachable_is_distinguishable_from_mismatch(tmp_path):
    with pytest.raises(GuardFailure) as differs:
        check_weights_channel("f", "v2", _pkg(tmp_path), probe=_probe(("a" * 64, "b" * 64)))
    with pytest.raises(GuardFailure) as unreachable:
        check_weights_channel("f", "v2", _pkg(tmp_path), probe=_probe(ProbeUnavailable("timeout")))
    assert "Failing CLOSED" not in str(differs.value)
    assert "DIFFERS" not in str(unreachable.value)


def test_ack_skips_the_comparison_but_says_so_loudly(tmp_path):
    called = []

    def probe(*a):
        called.append(a)
        return ("a" * 64, "b" * 64)

    notes = check_weights_channel("f", "v9", _pkg(tmp_path), probe=probe, preplaced_ack=True)
    assert called == []
    assert any("SKIPPED" in n for n in notes)
    assert any("refuses the build" in n for n in notes)


def test_no_hub_version_is_not_compared(tmp_path):
    """uplifting v7 has no Hub copy; the guard must neither ask nor fail."""
    _pkg(tmp_path, repo_id=None)
    (tmp_path / "NO_HUB").write_text("")
    called = []
    notes = check_weights_channel("uplifting", "v7", tmp_path, probe=lambda *a: called.append(a))
    assert called == []
    assert any("NO_HUB" in n for n in notes)


def test_default_probe_reads_the_repo_id_from_the_package(tmp_path, monkeypatch):
    """The real probe hashes filter_dir/model/adapter_model.safetensors and asks the Hub
    repo the package's inference_hub.py names (as NexusMind's stage.py does), never one
    derived from the directory name: human_thriving's repo is human-thriving-filter-v9,
    and the derived name 404'd for three live filters (review 2026-10-09)."""
    import hashlib

    from scripts.deployment import check_adapter_matches_hub as cam

    pkg = _pkg(tmp_path, repo_id="jeergrvgreg/human-thriving-filter-v9")
    seen = {}

    def hub(repo, tok):
        seen["repo"] = repo
        return hashlib.sha256(b"w").hexdigest()

    monkeypatch.setattr(cam, "hub_sha256", hub)
    monkeypatch.setattr(cam, "token_from_secrets", lambda: None)
    assert check_weights_channel("human_thriving", "v9", pkg) == [
        f"adapter matches its Hub copy for human_thriving/v9 ({hashlib.sha256(b'w').hexdigest()[:12]})"
    ]
    assert seen["repo"] == "jeergrvgreg/human-thriving-filter-v9"

    monkeypatch.setattr(cam, "hub_sha256", lambda repo, tok: None)
    with pytest.raises(GuardFailure, match="Failing CLOSED"):
        check_weights_channel("human_thriving", "v9", pkg)

    def boom(repo, tok):
        raise OSError("no route")

    monkeypatch.setattr(cam, "hub_sha256", boom)
    with pytest.raises(GuardFailure, match="Failing CLOSED"):
        check_weights_channel("human_thriving", "v9", pkg)


def test_no_repo_id_and_no_NO_HUB_fails_closed(tmp_path, monkeypatch):
    """stage.py would stage such an adapter UNCHECKED; the guard must not pass it."""
    from scripts.deployment import check_adapter_matches_hub as cam

    monkeypatch.setattr(cam, "hub_sha256", lambda r, t: pytest.fail("Hub must not be asked"))
    with pytest.raises(GuardFailure, match="names no `repo_id"):
        check_weights_channel("demo", "v3", _pkg(tmp_path, repo_id=None))


def test_missing_adapter_is_a_guard_failure_not_a_traceback(tmp_path):
    """Review 2026-10-09: hashing an absent file raised FileNotFoundError past main()."""
    (tmp_path / "inference_hub.py").write_text('    repo_id: str = "jeergrvgreg/demo-filter-v3"\n')
    with pytest.raises(GuardFailure, match="no local adapter_model.safetensors"):
        check_weights_channel("demo", "v3", tmp_path, probe=lambda *a: pytest.fail("not reached"))


def test_every_hub_backed_package_names_a_repo_id():
    """Every filters/*/v*/ with an inference_hub.py must yield a repo id by stage.py's
    rule — else guard D (and NexusMind's staging check) cannot run for it."""
    from pathlib import Path

    from scripts.deployment import check_adapter_matches_hub as cam

    repo = Path(__file__).resolve().parents[2]
    pkgs = sorted(p.parent for p in repo.glob("filters/*/v*/inference_hub.py"))
    assert len(pkgs) >= 6, pkgs  # the instrument must see the live packages
    missing = [str(p.relative_to(repo)) for p in pkgs
               if not (p / "NO_HUB").exists() and not cam.hub_repo_id(p)]
    assert missing == []


def test_guard_D_no_longer_reaches_for_a_host():
    """The pre-#395 probe ssh'd gpu-server. Nothing in the guard module may now."""
    from pathlib import Path

    src = (Path(__file__).resolve().parents[2] / "scripts" / "deployment"
           / "preflight_deploy_guards.py").read_text(encoding="utf-8")
    assert "subprocess" not in src
    assert '"ssh"' not in src


def test_rollback_advice_never_says_remove_a_version(tmp_path):
    """Since #395 removing vN from NexusMind stops the scorer for every filter."""
    root = _mk_nexusmind(tmp_path, ["v4", "v7"])
    with pytest.raises(GuardFailure) as exc:
        check_cutover("demo", "v5", root)
    msg = str(exc.value)
    assert "do NOT remove" in msg
    assert "kept previous image" in msg


# --- Single caller ----------------------------------------------------------
#
# The 2026-08-12 review found `deploy_to_nexusmind.ps1` had NO Step 0.5 at all: a
# documented second deploy path, one keystroke from bypassing every guard. Parity tests
# kept the two in step until 2026-09-26, when the PowerShell twin was deleted (Linux only;
# it also bypassed the #164 runtime-only rule). What stops a second path from coming back
# is `tests/unit/test_common_runtime_files.py::test_no_second_deploy_route_copies_filters_common`.


def test_the_only_caller_invokes_the_guards():
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    sh = (repo / "scripts" / "deploy_to_nexusmind.sh").read_text(encoding="utf-8")
    assert "preflight_deploy_guards.py" in sh
    assert not (repo / "scripts" / "deploy_to_nexusmind.ps1").exists()


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
    with open(d / "model" / "adapter_model.safetensors", "wb") as f:
        f.truncate(2_000_000)  # sparse: real-adapter size without writing 2 MB
    notes = check_weights_backed_up(d)
    assert any("weights present locally" in n for n in notes)


def test_lfs_pointer_sized_adapter_is_refused(tmp_path):
    """Review 2026-10-09: a git-LFS pointer passed `size > 0`, and guard D would then
    advise re-uploading it over the real Hub copy."""
    d = tmp_path / "filters" / "demo" / "v3"
    (d / "model").mkdir(parents=True)
    (d / "model" / "adapter_model.safetensors").write_text(
        "version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 52254448\n")
    with pytest.raises(GuardFailure, match="git-LFS pointer"):
        check_weights_backed_up(d)


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
