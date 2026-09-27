"""ADR-024 step 3: manifest-driven detector deploy (scripts/deployment/deploy_detectors.py).

Pins every refusal `stage` owes before NexusMind is touched, the prune rule (ONLY what the previous manifest
listed; no readable previous manifest = no prune), that `--plan` writes nothing, that the post-check re-hashes
the target, and the call sites in deploy_to_nexusmind.sh. The real-tree tests pin that every packaged detector
can actually be staged: manifest present and pinned, every git-origin file tracked.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts.deployment.common_runtime_files import runtime_files, unpackaged_runtime_files
from scripts.deployment.deploy_detectors import Refused, check_owns, place, stage
from scripts.deployment.detector_manifest import COMMON, MANIFEST, PACKAGES

REPO = Path(__file__).resolve().parents[2]
PKG = "harm_detector/v1"   # any PACKAGES key; the tests build their own trees
PKL, SIDE, PY = b"weights", None, b"print('x')\n"


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _entry(path, data, origin):
    return {"path": path, "sha256": _sha(data), "bytes": len(data), "origin": origin}


def _manifest(files: dict[str, tuple[bytes, str]], hub=True, detector="harm_detector", version="v1"):
    return {"schema": 1, "detector": detector, "version": version,
            "hub": {"repo_id": "o/r", "revision": "abc123", "path_prefix": version} if hub else None,
            "files": [_entry(p, d, o) for p, (d, o) in files.items()]}


def _files(pkl=PKL):
    return {"inference.py": (PY, "git"), "models/s.pkl": (pkl, "hub"),
            "models/s.pkl.sha256": ((_sha(pkl) + "\n").encode(), "git")}


def _src(tmp: Path, files, manifest=None, on_disk=None) -> Path:
    common = tmp / "src"
    d = common / PKG
    for rel, (data, origin) in files.items():
        if origin == "git":
            (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / rel).write_bytes((on_disk or {}).get(rel, data))
    d.mkdir(parents=True, exist_ok=True)
    (d / MANIFEST).write_text(json.dumps(manifest or _manifest(files)))
    return common


def _fetcher(tmp: Path, blobs: dict[str, bytes]):
    calls = []

    def fetch(repo_id, path_in_repo, revision):
        calls.append((repo_id, path_in_repo, revision))
        p = tmp / "hub" / path_in_repo
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(blobs[path_in_repo])
        return p
    fetch.calls = calls
    return fetch


def _staged(tmp: Path, files=None) -> Path:
    files = files or _files()
    common = _src(tmp, files)
    blobs = {f"v1/{p}": d for p, (d, o) in files.items() if o == "hub"}
    stage(PKG, tmp / "stg", _fetcher(tmp, blobs), common=common, git_root=None)
    return tmp / "stg"


def _snapshot(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


# ---- stage: every refusal happens before the target exists in the story at all ----

def test_stage_fetches_hub_files_at_the_pinned_revision(tmp_path):
    files = _files()
    fetch = _fetcher(tmp_path, {"v1/models/s.pkl": PKL})
    stage(PKG, tmp_path / "stg", fetch, common=_src(tmp_path, files), git_root=None)
    assert fetch.calls == [("o/r", "v1/models/s.pkl", "abc123")]
    assert (tmp_path / "stg" / PKG / "models/s.pkl").read_bytes() == PKL
    assert (tmp_path / "stg" / PKG / MANIFEST).is_file()


def test_stage_never_reads_the_working_tree_pickle(tmp_path):
    files = _files()
    common = _src(tmp_path, files)
    (common / PKG / "models/s.pkl").write_bytes(b"stale local pickle")
    stage(PKG, tmp_path / "stg", _fetcher(tmp_path, {"v1/models/s.pkl": PKL}), common=common, git_root=None)
    assert (tmp_path / "stg" / PKG / "models/s.pkl").read_bytes() == PKL


def test_stage_refuses_an_unpinned_hub(tmp_path):
    files = _files()
    common = _src(tmp_path, files, _manifest(files, hub=False))
    with pytest.raises(Refused, match="not pinned"):
        stage(PKG, tmp_path / "stg", _fetcher(tmp_path, {}), common=common, git_root=None)


def test_stage_refuses_hub_bytes_that_differ_from_the_manifest(tmp_path):
    with pytest.raises(Refused, match="does not match"):
        stage(PKG, tmp_path / "stg", _fetcher(tmp_path, {"v1/models/s.pkl": b"tampered"}),
              common=_src(tmp_path, _files()), git_root=None)


def test_stage_refuses_a_git_file_that_differs_from_the_manifest(tmp_path):
    common = _src(tmp_path, _files(), on_disk={"inference.py": b"edited\n"})
    with pytest.raises(Refused, match="inference.py .git. does not match"):
        stage(PKG, tmp_path / "stg", _fetcher(tmp_path, {"v1/models/s.pkl": PKL}), common=common, git_root=None)


def test_stage_refuses_a_sidecar_that_does_not_carry_its_pickles_digest(tmp_path):
    files = _files()
    files["models/s.pkl.sha256"] = ((_sha(b"other") + "\n").encode(), "git")   # self-consistent, wrong content
    with pytest.raises(Refused, match="sidecar"):
        stage(PKG, tmp_path / "stg", _fetcher(tmp_path, {"v1/models/s.pkl": PKL}),
              common=_src(tmp_path, files), git_root=None)


def test_stage_refuses_a_sidecar_whose_pickle_is_not_listed(tmp_path):
    files = {"inference.py": (PY, "git"), "models/x.pkl.sha256": ((_sha(b"x") + "\n").encode(), "git")}
    with pytest.raises(Refused, match="does not list"):
        stage(PKG, tmp_path / "stg", _fetcher(tmp_path, {}), common=_src(tmp_path, files), git_root=None)


def test_owns_entry_inside_a_packaged_detector_is_refused(tmp_path):
    owns = tmp_path / ".nexusmind-owns"
    owns.write_text("# comment\nfilters/common/embedding_stage.py\n")
    check_owns(owns)                                   # presence control: an unpackaged entry is fine
    check_owns(tmp_path / "absent")
    owns.write_text(f"filters/common/{PKG}/inference.py  # owned\n")
    with pytest.raises(Refused, match="packaged detector"):
        check_owns(owns)


def test_stage_refuses_a_missing_manifest(tmp_path):
    (tmp_path / "src" / PKG).mkdir(parents=True)
    with pytest.raises(Refused, match="no MANIFEST.json"):
        stage(PKG, tmp_path / "stg", _fetcher(tmp_path, {}), common=tmp_path / "src", git_root=None)


def test_stage_refuses_a_manifest_for_another_package(tmp_path):
    files = _files()
    common = _src(tmp_path, files, _manifest(files, version="v2"))
    with pytest.raises(Refused, match="manifest names"):
        stage(PKG, tmp_path / "stg", _fetcher(tmp_path, {}), common=common, git_root=None)


@pytest.mark.parametrize("bad", ["../escape.py", "/abs.py", "a/../../b.py"])
def test_stage_refuses_an_unsafe_path(tmp_path, bad):
    files = {bad: (PY, "git")}
    common = _src(tmp_path, {"inference.py": (PY, "git")}, _manifest(files))
    with pytest.raises(Refused, match="unsafe path"):
        stage(PKG, tmp_path / "stg", _fetcher(tmp_path, {}), common=common, git_root=None)


def _git(root: Path, *args):
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


@pytest.mark.parametrize("defect", ["manifest_modified", "manifest_untracked", "git_file_untracked",
                                    "git_file_staged_only", "manifest_staged_only"])
def test_stage_refuses_what_git_has_not_recorded(tmp_path, defect):
    """Staged-but-uncommitted must refuse too: `git ls-files` passed it (round-1 review, three lenses)."""
    files = _files()
    common = _src(tmp_path, files)
    _git(tmp_path, "init", "-q")
    keep_out = {"manifest_untracked": MANIFEST, "git_file_untracked": "models/s.pkl.sha256",
                "manifest_staged_only": MANIFEST, "git_file_staged_only": "models/s.pkl.sha256"}.get(defect)
    for p in (common / PKG).rglob("*"):
        if p.is_file() and p.relative_to(common / PKG).as_posix() != keep_out:
            _git(tmp_path, "add", str(p))
    _git(tmp_path, "commit", "-qm", "init")
    if defect.endswith("staged_only"):
        _git(tmp_path, "add", str(common / PKG / keep_out))
    if defect == "manifest_modified":
        with (common / PKG / MANIFEST).open("a") as f:
            f.write("\n")
    with pytest.raises(Refused, match="not in HEAD|modified"):
        stage(PKG, tmp_path / "stg", _fetcher(tmp_path, {"v1/models/s.pkl": PKL}), common=common, git_root=tmp_path)


def test_stage_passes_a_committed_package(tmp_path):
    """Presence control for the test above: the same harness, nothing withheld, stages."""
    common = _src(tmp_path, _files())
    _git(tmp_path, "init", "-q"); _git(tmp_path, "add", "-A"); _git(tmp_path, "commit", "-qm", "init")
    stage(PKG, tmp_path / "stg", _fetcher(tmp_path, {"v1/models/s.pkl": PKL}), common=common, git_root=tmp_path)


# ---- place: prune only by the previous manifest; prove the outcome ----

def _target(tmp: Path, files: dict[str, bytes], prev_manifest=None) -> Path:
    t = tmp / "nm"
    for rel, data in files.items():
        (t / PKG / rel).parent.mkdir(parents=True, exist_ok=True)
        (t / PKG / rel).write_bytes(data)
    if prev_manifest is not None:
        (t / PKG).mkdir(parents=True, exist_ok=True)
        (t / PKG / MANIFEST).write_text(prev_manifest if isinstance(prev_manifest, str) else json.dumps(prev_manifest))
    return t


def test_first_deploy_prunes_nothing_and_reports_extras(tmp_path):
    stg = _staged(tmp_path)
    t = _target(tmp_path, {"models/s.pkl": PKL, "README.md": b"r", "models/old.pkl": b"o"})
    r = place(PKG, stg, t)
    assert r["pruned"] == [] and r["errors"] == []
    assert r["extra"] == ["README.md", "models/old.pkl"]
    assert (t / PKG / "models/old.pkl").is_file() and (t / PKG / MANIFEST).is_file()
    assert r["same"] == ["models/s.pkl"] and sorted(r["written"]) == ["inference.py", "models/s.pkl.sha256"]


def test_prune_removes_exactly_what_the_previous_manifest_listed_and_the_new_one_does_not(tmp_path):
    stg = _staged(tmp_path)
    prev = _manifest({**_files(), "models/old.pkl": (b"o", "hub")})
    t = _target(tmp_path, {"models/old.pkl": b"o", "models/unlisted.pkl": b"u"}, prev)
    r = place(PKG, stg, t)
    assert r["pruned"] == ["models/old.pkl"] and r["errors"] == []
    assert not (t / PKG / "models/old.pkl").exists()
    assert (t / PKG / "models/unlisted.pkl").is_file()            # never listed = never deleted
    assert r["extra"] == ["models/unlisted.pkl"]


@pytest.mark.parametrize("prev", ["{not json", json.dumps(_manifest(_files(), version="v2")), "[]",
                                  json.dumps({**_manifest(_files()), "files": ["models/old.pkl"]}),
                                  json.dumps({**_manifest(_files()), "files": [{}]})])
def test_an_unreadable_or_foreign_previous_manifest_prunes_nothing(tmp_path, prev):
    stg = _staged(tmp_path)
    t = _target(tmp_path, {"models/old.pkl": b"o"}, prev)
    r = place(PKG, stg, t)
    assert r["pruned"] == [] and (t / PKG / "models/old.pkl").is_file()
    assert "nothing pruned" in r["prune_basis"]


def test_an_unsafe_path_in_the_previous_manifest_is_not_followed(tmp_path):
    stg = _staged(tmp_path)
    (tmp_path / "nm" / "victim.txt").parent.mkdir(parents=True)
    (tmp_path / "nm" / "victim.txt").write_text("keep")
    prev = _manifest(_files())
    prev["files"].append({"path": "../../victim.txt", "sha256": "0" * 64, "bytes": 1, "origin": "git"})
    t = _target(tmp_path, {}, prev)
    r = place(PKG, stg, t)
    assert (tmp_path / "nm" / "victim.txt").read_text() == "keep"
    assert any("unsafe path" in e for e in r["errors"])


def test_a_symlinked_dir_in_the_target_carries_no_write_or_delete_out(tmp_path):
    stg = _staged(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "precious.pkl").write_bytes(b"p")
    prev = _manifest({**_files(), "models/precious.pkl": (b"p", "hub")})
    t = _target(tmp_path, {}, prev)
    (t / PKG / "models").symlink_to(outside, target_is_directory=True)
    r = place(PKG, stg, t)
    assert (outside / "precious.pkl").read_bytes() == b"p"
    assert not (outside / "s.pkl").exists()
    assert any("outside" in e for e in r["errors"])


def test_a_failed_prune_keeps_the_old_manifest_so_the_rerun_retries_it(tmp_path):
    stg = _staged(tmp_path)
    prev = _manifest({**_files(), "sub/old.py": (b"o", "git")})
    t = _target(tmp_path, {"sub/old.py": b"o"}, prev)
    (t / PKG / "sub").chmod(0o500)
    try:
        r = place(PKG, stg, t)
        assert any(e.startswith("prune sub/old.py") for e in r["errors"])
        assert json.loads((t / PKG / MANIFEST).read_text()) == prev      # old manifest still the prune basis
    finally:
        (t / PKG / "sub").chmod(0o700)
    r = place(PKG, stg, t)
    assert r["pruned"] == ["sub/old.py"] and r["errors"] == [] and not (t / PKG / "sub/old.py").exists()


def test_plan_writes_nothing(tmp_path):
    stg = _staged(tmp_path)
    prev = _manifest({**_files(), "models/old.pkl": (b"o", "hub")})
    t = _target(tmp_path, {"models/old.pkl": b"o", "models/s.pkl": b"older weights"}, prev)
    before = _snapshot(t)
    r = place(PKG, stg, t, plan=True)
    assert _snapshot(t) == before
    assert r["pruned"] == ["models/old.pkl"] and "models/s.pkl" in r["written"] and r["manifest"] == "write"


def test_the_post_check_rehashes_the_target(tmp_path):
    stg = _staged(tmp_path)
    (stg / PKG / "inference.py").write_bytes(b"corrupted after staging\n")
    r = place(PKG, stg, _target(tmp_path, {}))
    assert any(e.startswith("MISMATCH inference.py") for e in r["errors"])


def test_a_second_identical_deploy_changes_nothing(tmp_path):
    stg = _staged(tmp_path)
    t = _target(tmp_path, {})
    place(PKG, stg, t)
    before = _snapshot(t)
    r = place(PKG, stg, t)
    assert r["written"] == [] and r["pruned"] == [] and r["manifest"] == "unchanged" and _snapshot(t) == before


# ---- the real tree and the call sites ----

@pytest.mark.parametrize("pkg", sorted(PACKAGES))
def test_every_packaged_detector_is_stageable_from_git(pkg):
    """Pinned revision, and every git-origin file COMMITTED (in HEAD) with the manifest's bytes: what `stage`
    demands. Reads HEAD, not `ls-files`, which passes a staged-only file (round-1 review)."""
    m = json.loads((COMMON / pkg / MANIFEST).read_text())
    assert (m.get("hub") or {}).get("revision"), pkg
    for f in m["files"]:
        if f["origin"] == "git":
            rel = f"filters/common/{pkg}/{f['path']}"
            head = subprocess.run(["git", "-C", str(REPO), "show", f"HEAD:{rel}"], capture_output=True)
            assert head.returncode == 0, f"{rel} is not in HEAD"
            assert _sha(head.stdout) == f["sha256"], rel


def test_unpackaged_list_excludes_exactly_the_packaged_dirs():
    all_, unpk = {r.as_posix() for r in runtime_files(COMMON)}, {r.as_posix() for r in unpackaged_runtime_files(COMMON)}
    assert unpk and not any(r.startswith(tuple(p + "/" for p in PACKAGES)) for r in unpk)
    assert all_ - unpk == {r for r in all_ if r.startswith(tuple(p + "/" for p in PACKAGES))}
    assert "harm_detector/__init__.py" in unpk      # the detector's top-level package file is not in a manifest


def test_deploy_script_stages_before_copying_and_places_in_step_2():
    s = (REPO / "scripts" / "deploy_to_nexusmind.sh").read_text()
    step1, step2 = s.index("# Step 1: Copy filter folder"), s.index("# Step 2:")
    assert 0 < s.index("deploy_detectors.py\" stage") < step1
    assert step2 < s.index("deploy_detectors.py\" place") < s.index('done <<< "$COMMON_LIST"')
    assert "common_runtime_files.py\" --unpackaged" in s
    assert "PLACE_FLAGS+=(--plan)" in s
