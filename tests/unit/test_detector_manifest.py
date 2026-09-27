"""ADR-024 step 1: detector package manifests (scripts/deployment/detector_manifest.py + verify_detector_package.py).

Pins: the package boundary (a detector's manifest never reaches outside its own dir, #165 review), that a
missing runtime file raises instead of shrinking the manifest, that verify tells missing / mismatch / extra
apart, the remote-path quoting that broke the first backfill (`~` quoted into a literal directory name), and the
CLI's exit codes, because a guard's tests must break the CALL SITE too (gotcha 2026-09-27).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.deployment.detector_manifest import (
    COMMON, PACKAGES, build, listing_local, parse_listing, remote_path, select, verify)

REPO = Path(__file__).resolve().parents[2]
CLI = REPO / "scripts" / "deployment" / "verify_detector_package.py"


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def test_package_set_is_the_owner_ruling():
    """ADR-024, 2026-09-27: harm v1, obituary v5, violence v1, commerce v1; obit v3/v4 and commerce v2 retired."""
    assert sorted(PACKAGES) == ["commerce_prefilter/v1", "harm_detector/v1", "obituary_detector/v5",
                                "violence_promotion/v1"]


@pytest.mark.parametrize("pkg", sorted(PACKAGES))
def test_patterns_stay_inside_the_package(pkg):
    for pat in PACKAGES[pkg]:
        assert not pat.startswith(("/", "..")) and ".." not in pat.split("/"), pat
        assert "embedding_stage" not in pat and "model_loading" not in pat, pat


def test_select_raises_on_a_missing_runtime_file():
    listing = {"inference.py": ("a" * 64, 1)}
    with pytest.raises(ValueError, match="no file matches"):
        select("obituary_detector/v5", listing)


def test_select_takes_exactly_the_runtime_files():
    names = ["__init__.py", "inference.py", "README.md", "calibration_report.json", "config.yaml",
             "models/training_config.json", "models/scaler.pkl", "models/scaler.pkl.sha256",
             "models/mlp_classifier_seed0.pkl", "models/mlp_classifier_seed0.pkl.sha256",
             "models/mlp_classifier_seed1.pkl", "models/sub/mlp_classifier_seed9.pkl"]
    got = select("harm_detector/v1", {n: ("a" * 64, 1) for n in names})
    assert sorted(got) == sorted(n for n in names if n not in
                                 {"README.md", "calibration_report.json", "config.yaml",
                                  "models/sub/mlp_classifier_seed9.pkl"})   # `*` never crosses a `/`


def test_commerce_v1_ships_only_distilbert():
    names = ["__init__.py", "inference.py"] + [f"models/{m}/{f}" for m in ("distilbert", "minilm", "xlm-roberta")
                                               for f in ("config.json", "model.safetensors", "tokenizer.json",
                                                         "tokenizer_config.json", "special_tokens_map.json",
                                                         "vocab.txt")]
    got = select("commerce_prefilter/v1", {n: ("a" * 64, 1) for n in names})
    assert all(p.startswith("models/distilbert/") for p in got if p.startswith("models/"))


def test_verify_separates_missing_mismatch_extra():
    m = build("obituary_detector/v5", {"a.py": (_sha(b"a"), 1), "m.pkl": (_sha(b"m"), 1)}, "src", {}, "abc")
    res = verify(m, {"a.py": (_sha(b"a"), 1), "m.pkl": (_sha(b"X"), 1), "README.md": (_sha(b"r"), 1)})
    assert res["missing"] == [] and len(res["mismatch"]) == 1 and res["extra"] == ["README.md"]
    res = verify(m, {"a.py": (_sha(b"a"), 1)})
    assert res["missing"] == ["m.pkl"]


def test_build_marks_origin_and_unrecorded_stack():
    m = build("violence_promotion/v1", {"inference.py": ("a" * 64, 3), "models/m.pkl": ("b" * 64, 9)},
              "src", {"embedder_model": "e5"}, "abc")
    assert {f["path"]: f["origin"] for f in m["files"]} == {"inference.py": "git", "models/m.pkl": "hub"}
    assert m["build_stack_unrecorded"] == ["sklearn_version"] and m["hub"] is None


def test_remote_path_keeps_tilde_expandable():
    assert remote_path("~/local_dev/NexusMind") == '"$HOME"/local_dev/NexusMind'
    assert remote_path("/home/x/a b") == "'/home/x/a b'"


def test_parse_listing_strips_dot_slash_and_rejects_garbage():
    assert parse_listing(f"{'a' * 64} 12 ./models/x.pkl\n") == {"models/x.pkl": ("a" * 64, 12)}
    with pytest.raises(ValueError):
        parse_listing("nothex 12 ./x\n")


def test_listing_local_hashes_and_skips_pycache(tmp_path):
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.pyc").write_bytes(b"c")
    (tmp_path / "a.py").write_bytes(b"abc")
    assert listing_local(tmp_path) == {"a.py": (_sha(b"abc"), 3)}


@pytest.mark.parametrize("pkg", sorted(PACKAGES))
def test_committed_manifests_are_well_formed(pkg):
    m = json.loads((COMMON / pkg / "MANIFEST.json").read_text())
    assert (m["detector"], m["version"]) == tuple(pkg.split("/"))
    assert m["files"] and all(len(f["sha256"]) == 64 and f["bytes"] > 0 or f["path"].endswith("__init__.py")
                              for f in m["files"])
    assert select(pkg, {f["path"]: (f["sha256"], f["bytes"]) for f in m["files"]})   # every pattern covered


def _run(*args):
    return subprocess.run([sys.executable, str(CLI), *args], capture_output=True, text=True, cwd=REPO)


def test_cli_exit_codes_on_a_tree_missing_the_package(tmp_path):
    (tmp_path / "filters" / "common" / "violence_promotion" / "v1").mkdir(parents=True)
    report = _run("verify", "violence_promotion/v1", "--target", str(tmp_path))
    assert report.returncode == 0 and "MISSING" in report.stdout and "reporting mode" in report.stdout
    strict = _run("verify", "violence_promotion/v1", "--target", str(tmp_path), "--strict")
    assert strict.returncode == 1 and "FAIL" in strict.stdout


def test_cli_strict_passes_on_a_matching_tree(tmp_path):
    """Presence control: the same harness passes when the bytes match, so the failure above is the check.
    harm v1, because it adopts nothing: obituary v5 / violence v1 name OUR training_config.json (owner ruling
    2026-09-27) and legitimately MISMATCH NexusMind until step 3 ships it."""
    m = json.loads((COMMON / "harm_detector" / "v1" / "MANIFEST.json").read_text())
    assert not m.get("adopted_from_this_repo")
    nm = REPO.parent / "NexusMind" / "filters" / "common" / "harm_detector" / "v1"
    if not all((nm / f["path"]).is_file() for f in m["files"]):
        pytest.skip("needs the NexusMind checkout beside this repo")
    r = _run("verify", "harm_detector/v1", "--target", str(REPO.parent / "NexusMind"), "--strict")
    assert r.returncode == 0 and "OK" in r.stdout, r.stdout


def test_a_pattern_never_matches_a_deeper_path():
    """Segment count must agree: without it, `inference.py` matches `inference.py/x` (zip stops early)."""
    from scripts.deployment.detector_manifest import _match
    assert _match("models/*.pkl", "models/a.pkl")
    assert not _match("inference.py", "inference.py/x")
    assert not _match("models/*.pkl", "models/a.pkl/b")


def test_cli_missing_local_target_exits_2(tmp_path):
    """Review 2026-09-27: a mistyped local path read as 26 MISSING lines and exit 0."""
    r = _run("verify", "--all", "--target", str(tmp_path / "typo"))
    assert r.returncode == 2 and "not a directory" in r.stderr


# --- step 2: Hub record ------------------------------------------------------------------------------------

from scripts.deployment.upload_detector_to_hub import find_local, repo_id_for  # noqa: E402


def test_repo_id_is_one_repo_per_detector():
    assert repo_id_for("harm_detector") == "jeergrvgreg/harm-detector"
    assert repo_id_for("commerce_prefilter") == "jeergrvgreg/commerce-detector"
    assert repo_id_for("violence_promotion") == "jeergrvgreg/violence-promotion-detector"
    assert all(n.endswith("-detector") for n in (repo_id_for(d) for d in ("harm_detector", "obituary_detector",
                                                                           "violence_promotion", "commerce_prefilter")))
    with pytest.raises(KeyError):
        repo_id_for("new_detector")   # an unnamed detector must not get an invented name


def test_find_local_refuses_a_copy_whose_hash_differs(tmp_path):
    """Nothing may be uploaded in the manifest's name unless its bytes are the manifest's bytes."""
    p = tmp_path / "filters" / "common" / "x" / "v1" / "m.pkl"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"retrained")
    with pytest.raises(FileNotFoundError, match="no local copy"):
        find_local("x/v1", "m.pkl", _sha(b"served"), 6, roots=(tmp_path,))
    assert find_local("x/v1", "m.pkl", _sha(b"retrained"), 9, roots=(tmp_path,)) == p


@pytest.mark.parametrize("pkg", sorted(PACKAGES))
def test_committed_manifests_pin_a_hub_revision(pkg):
    """A manifest with hub-origin files and no pinned revision is what step 3 must refuse (ADR-024)."""
    m = json.loads((COMMON / pkg / "MANIFEST.json").read_text())
    assert m["hub"]["repo_id"] == repo_id_for(m["detector"])
    assert len(m["hub"]["revision"]) == 40 and m["hub"]["path_prefix"] == m["version"]


def test_adopt_refuses_an_untracked_file(tmp_path):
    r = _run("adopt", "harm_detector/v1", "models/scaler.pkl", "--why", "test")
    assert r.returncode == 2 and "not a git-origin file" in r.stderr


def test_adopt_refuses_an_untracked_git_origin_file(tmp_path, monkeypatch):
    """The path the CLI actually refused on 2026-09-27 (obituary v5's config before it was committed).
    Review: the earlier test hit the hub-origin branch, and deleting the ls-files guard left the suite green."""
    import scripts.deployment.verify_detector_package as v
    pkg = tmp_path / "filters" / "common" / "violence_promotion" / "v1"
    (pkg / "models").mkdir(parents=True)
    (pkg / "models" / "training_config.json").write_text("{}")
    m = build("violence_promotion/v1", {"models/training_config.json": (_sha(b"x"), 1)}, "s", {}, "c")
    (pkg / "MANIFEST.json").write_text(json.dumps(m))
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    monkeypatch.setattr(v, "COMMON", tmp_path / "filters" / "common")
    monkeypatch.setattr(v, "REPO", tmp_path)
    with pytest.raises(ValueError, match="not tracked here"):
        v.cmd_adopt("violence_promotion/v1", "models/training_config.json", "test")


def test_adopt_refreshes_the_build_stack_from_the_adopted_config(tmp_path, monkeypatch):
    import scripts.deployment.verify_detector_package as v
    pkg = tmp_path / "filters" / "common" / "violence_promotion" / "v1"
    (pkg / "models").mkdir(parents=True)
    (pkg / "models" / "training_config.json").write_text(json.dumps({"sklearn_version": "1.8.0"}))
    m = build("violence_promotion/v1", {"models/training_config.json": (_sha(b"x"), 1),
                                        "models/m.pkl": (_sha(b"m"), 1)}, "s", {"embedder_model": "e"}, "c")
    assert m["build_stack_unrecorded"] == ["sklearn_version"]
    (pkg / "MANIFEST.json").write_text(json.dumps(m))
    g = ["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(g + ["add", "-A"], check=True)
    monkeypatch.setattr(v, "COMMON", tmp_path / "filters" / "common")
    monkeypatch.setattr(v, "REPO", tmp_path)
    v.cmd_adopt("violence_promotion/v1", "models/training_config.json", "test")
    out = json.loads((pkg / "MANIFEST.json").read_text())
    assert out["build_stack"] == {"sklearn_version": "1.8.0"} and out["build_stack_unrecorded"] == []
