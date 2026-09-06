"""The training-provenance guard, and the four ways it could be theatre.

⛔ WHAT IT IS FOR. `human_thriving v8`'s first adapter was trained by a tree that
`git commit --amend` then orphaned: the sha that built it is reachable from no
branch. Nothing caught it because `training_metadata.json` recorded no commit.
The owner's 2026-09-06 ruling was *no exception* — retrain under a real commit —
so the mechanism has to actually fire, not merely exist.

⚠️ Each test seeds a REAL git repository rather than a fixture dict, because the
property under test is reachability, which only git can answer. A stub that
returns "unreachable" would test the stub.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

GUARD = (Path(__file__).resolve().parents[2]
         / "scripts" / "verification" / "check_training_provenance.py")
TRAIN = Path(__file__).resolve().parents[2] / "training" / "train.py"


def _run(*args, cwd):
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True,
                          check=True)


@pytest.fixture
def repo(tmp_path):
    """A real git repo with one commit on `main` and no metadata files yet."""
    _run("git", "init", "-q", "-b", "main", ".", cwd=tmp_path)
    _run("git", "config", "user.email", "t@example.com", cwd=tmp_path)
    _run("git", "config", "user.name", "T", cwd=tmp_path)
    (tmp_path / "seed.txt").write_text("x\n", encoding="utf-8")
    _run("git", "add", "seed.txt", cwd=tmp_path)
    _run("git", "commit", "-q", "-m", "seed", cwd=tmp_path)
    return tmp_path


@pytest.fixture
def mod(repo, monkeypatch):
    spec = importlib.util.spec_from_file_location("check_training_provenance", GUARD)
    m = importlib.util.module_from_spec(spec)
    sys.modules["check_training_provenance"] = m
    spec.loader.exec_module(m)
    monkeypatch.setattr(m, "ROOT", str(repo))
    monkeypatch.setattr(m, "UNSTAMPED_BASELINE", frozenset())
    m._repo = repo
    return m


def _write_meta(repo, rel, payload):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def _head(repo):
    return _run("git", "rev-parse", "HEAD", cwd=repo).stdout.strip()


# ───────────────────────────────────────────────── the guard fires

def test_a_clean_stamped_checkpoint_passes(mod, capsys):
    _write_meta(mod._repo, "filters/f/v1/training_metadata.json",
                {"git_commit": _head(mod._repo), "git_dirty": False})
    assert mod.check()[0] == 0


def test_a_commit_on_no_branch_fails(mod):
    """⛔ THE ACTUAL v8 SHAPE. A real commit, a valid sha, reachable from nothing —
    which is what `git commit --amend` leaves behind."""
    repo = mod._repo
    _run("git", "checkout", "-q", "--detach", cwd=repo)
    (repo / "orphan.txt").write_text("y\n", encoding="utf-8")
    _run("git", "add", "orphan.txt", cwd=repo)
    _run("git", "commit", "-q", "-m", "orphan", cwd=repo)
    dangling = _head(repo)
    _run("git", "checkout", "-q", "main", cwd=repo)

    _write_meta(repo, "filters/f/v1/training_metadata.json",
                {"git_commit": dangling, "git_dirty": False})
    rc, lines = mod.check()
    assert rc == 1
    assert any("reachable from NO BRANCH" in ln for ln in lines)


def test_a_nonexistent_commit_fails(mod):
    _write_meta(mod._repo, "filters/f/v1/training_metadata.json",
                {"git_commit": "0" * 40, "git_dirty": False})
    rc, lines = mod.check()
    assert rc == 1 and any("does not exist" in ln for ln in lines)


def test_a_dirty_tree_stamp_fails(mod):
    """A valid sha plus uncommitted edits does not identify a tree — the same
    failure wearing a valid-looking commit id."""
    _write_meta(mod._repo, "filters/f/v1/training_metadata.json",
                {"git_commit": _head(mod._repo), "git_dirty": True})
    rc, lines = mod.check()
    assert rc == 1 and any("git_dirty=true" in ln for ln in lines)


def test_the_opt_out_is_recorded_and_still_fails(mod):
    """`--allow-missing-git-provenance` lets training proceed; it must not let the
    CHECK pass, or the opt-out silently becomes the default."""
    _write_meta(mod._repo, "filters/f/v1/training_metadata.json",
                {"git_commit": None, "git_dirty": None,
                 "git_provenance": "UNAVAILABLE: not a git work tree"})
    rc, lines = mod.check()
    assert rc == 1 and any("origin is unrecorded" in ln for ln in lines)


def test_a_new_unstamped_file_fails(mod):
    """The baseline is frozen. A metadata file that is neither stamped nor in it
    means training ran from a tree nobody can name."""
    _write_meta(mod._repo, "filters/f/v1/training_metadata.json",
                {"epochs": 6})
    rc, lines = mod.check()
    assert rc == 1 and any("NOT in the frozen baseline" in ln for ln in lines)


def test_a_baselined_unstamped_file_is_a_note_not_a_failure(mod, monkeypatch):
    monkeypatch.setattr(mod, "UNSTAMPED_BASELINE",
                        frozenset({"filters/f/v1/training_metadata.json"}))
    _write_meta(mod._repo, "filters/f/v1/training_metadata.json", {"epochs": 6})
    rc, lines = mod.check()
    assert rc == 0 and any("predates the stamp" in ln for ln in lines)


# ───────────────────────────────────────────────── the guard cannot be theatre

def test_no_metadata_files_is_cannot_verify_not_pass(mod):
    """⛔ THE FAILURE MODE OF EVERY CHECKER HERE. A glob that matches nothing
    passes forever, and a green check nobody can distinguish from a live one is
    worse than no check."""
    rc, lines = mod.check()
    assert rc == 1
    assert any("matched no files" in ln for ln in lines)


def test_outside_a_work_tree_is_cannot_verify(mod, monkeypatch, tmp_path_factory):
    # ⚠️ NOT `tmp_path`: the `repo` fixture git-inits it, so a subdirectory of it
    # IS inside a work tree and git walks up to find it. The first version of this
    # test asserted rc == 1 and got it — from "matched no files", not from the
    # branch under test. A shared tmp dir made the two indistinguishable.
    plain = tmp_path_factory.mktemp("outside_any_repo")
    monkeypatch.setattr(mod, "ROOT", str(plain))
    rc, lines = mod.check()
    assert rc == 1 and any("not a git work tree" in ln for ln in lines)


def test_the_real_baseline_matches_the_real_tree(monkeypatch):
    """⚠️ THE BASELINE MAY ONLY SHRINK. If a file is listed that no longer exists
    the list has gone stale; if an unlisted unstamped file appears the real run
    fails, which is the point. This asserts the frozen list still describes the
    repository it was frozen against."""
    spec = importlib.util.spec_from_file_location("cp_real", GUARD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    import glob
    import os
    found = {os.path.relpath(p, m.ROOT).replace(os.sep, "/")
             for p in glob.glob(os.path.join(m.ROOT, m.SCAN_GLOB))}
    assert m.UNSTAMPED_BASELINE <= found, (
        "baseline names files that are gone: "
        f"{sorted(m.UNSTAMPED_BASELINE - found)}")


def test_argv_is_a_parameter_not_sys_argv():
    """Imported by pytest, `main()` must not read pytest's own arguments."""
    spec = importlib.util.spec_from_file_location("cp_argv", GUARD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.main([]) == 0


# ───────────────────────────────────────────────── the producing half

@pytest.fixture
def train_mod():
    spec = importlib.util.spec_from_file_location("train_for_provenance", TRAIN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_train_refuses_outside_a_checkout(train_mod, monkeypatch, tmp_path):
    """b650 held a COPY of the repo, not a checkout, for the whole v8 build. A
    copy cannot name the commit that trains, and training anyway is what produced
    an artifact nobody could trace."""
    plain = tmp_path / "copy"
    plain.mkdir()
    monkeypatch.setattr(train_mod, "__file__", str(plain / "training" / "train.py"))
    with pytest.raises(RuntimeError, match="not a git work tree"):
        train_mod.resolve_git_provenance()


def test_train_opt_out_records_the_gap_rather_than_hiding_it(train_mod,
                                                             monkeypatch, tmp_path):
    plain = tmp_path / "copy"
    plain.mkdir()
    monkeypatch.setattr(train_mod, "__file__", str(plain / "training" / "train.py"))
    got = train_mod.resolve_git_provenance(allow_missing=True)
    assert got["git_commit"] is None
    assert got["git_provenance"].startswith("UNAVAILABLE:")
