"""What deploy_to_nexusmind.sh step 2 ships from filters/common (#164: runtime files only).

Each rule is tested both ways, on a synthetic tree (so the untracked-model case is covered
even where the .pkl files are absent) and on the real tree. The two failure modes this guards:
- shipping training/validation/GT material again, which the owner ruled out;
- dropping a file a detector reads at load time. Excluding by NAME (`training_config.json`)
  or switching to `git ls-files` would each do that: harm_detector/v1/inference.py reads
  training_config.json and SHA256SUMS.txt, and every *.pkl is gitignored here.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.deployment.common_runtime_files import is_runtime, runtime_files, stale_sidecars

REPO = Path(__file__).resolve().parents[2]
COMMON = REPO / "filters" / "common"

SHIPS = [
    "model_loading.py",
    "harm_detector/v1/inference.py",
    "harm_detector/v1/models/training_config.json",   # read at load: the seed ensemble
    "harm_detector/v1/models/SHA256SUMS.txt",         # read at load: pickle integrity
    "harm_detector/v1/models/mlp_classifier_seed0.pkl",  # gitignored in this repo
    "obituary_detector/v5/models/scaler.pkl",
    "obituary_detector/v5/models/scaler.pkl.sha256",  # _verify_pickle_integrity sidecar
    "violence_promotion/v1/config.yaml",
    "commerce_prefilter/v1/models/distilbert/model.safetensors",
]
STAYS = [
    "harm_detector/training/train_v1.py",
    "obituary_detector/validation/panel_obit.py",
    "obituary_detector/validation/artifacts/rollup_june.json",
    "commerce_prefilter/docs/TRAINING_PLAN.md",
    "commerce_prefilter/v1/tests/test_inference.py",
    "violence_promotion/v1/oracle.py",   # imports ground_truth, absent in NexusMind
    "commerce_prefilter/v1/prompt.md",   # read only by commerce's oracle.py
    "harm_detector/v1/__pycache__/inference.cpython-312.pyc",
    "detector_seeds.py",                 # #158 seed-band helper; only training imports it
]


@pytest.mark.parametrize("rel", SHIPS)
def test_runtime_file_ships(rel):
    assert is_runtime(Path(rel))


@pytest.mark.parametrize("rel", STAYS)
def test_non_runtime_file_stays(rel):
    assert not is_runtime(Path(rel))


def test_synthetic_tree_selects_exactly_the_runtime_files(tmp_path):
    for rel in SHIPS + STAYS:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")
    assert [r.as_posix() for r in runtime_files(tmp_path)] == sorted(SHIPS)


def test_real_tree_ships_every_tracked_runtime_read():
    selected = {r.as_posix() for r in runtime_files(COMMON)}
    for rel in ("harm_detector/v1/models/training_config.json",
                "harm_detector/v1/models/SHA256SUMS.txt",
                "harm_detector/v1/inference.py",
                "obituary_detector/v5/inference.py",
                "violence_promotion/v1/inference.py",
                "commerce_prefilter/v2/inference.py"):
        assert rel in selected, rel


def test_real_tree_ships_every_local_model_file():
    """The weights travel only through this copy; any present locally must be selected."""
    selected = {r.as_posix() for r in runtime_files(COMMON)}
    models = [p.relative_to(COMMON).as_posix() for p in COMMON.rglob("*")
              if p.suffix in {".pkl", ".safetensors"} and "__pycache__" not in p.parts]
    for rel in models:
        assert rel in selected, rel


def test_real_tree_ships_no_training_validation_or_docs():
    for rel in runtime_files(COMMON):
        assert not {"training", "validation", "docs", "tests"}.intersection(rel.parts), rel
        assert rel.name not in {"oracle.py", "prompt.md"}, rel


def test_deploy_script_uses_the_module_not_find():
    script = (REPO / "scripts" / "deploy_to_nexusmind.sh").read_text()
    assert "scripts/deployment/common_runtime_files.py" in script
    assert 'find "$COMMON_SOURCE"' not in script
    assert 'done <<< "$COMMON_LIST"' in script      # the copy loop reads the module's list


def test_deploy_script_checks_sidecars_before_copying_anything():
    script = (REPO / "scripts" / "deploy_to_nexusmind.sh").read_text()
    assert "--check-sidecars" in script
    assert script.index("--check-sidecars") < script.index("# Step 1: Copy filter folder")


def test_no_second_deploy_route_copies_filters_common():
    """The PowerShell twin copied the whole tree and bypassed the rule (review of 356cd70)."""
    assert not (REPO / "scripts" / "deploy_to_nexusmind.ps1").exists()
    for other in REPO.joinpath("scripts").rglob("*"):
        if other.suffix in {".ps1", ".sh"} and other.name != "deploy_to_nexusmind.sh":
            assert "filters/common" not in other.read_text(errors="ignore"), other


def _tree(root, files):
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def test_stale_nexusmind_sidecar_is_reported(tmp_path):
    src, nm = tmp_path / "src", tmp_path / "nm"
    _tree(src, {"det/v1/models/scaler.pkl": b"retrained"})
    _tree(nm, {"det/v1/models/scaler.pkl.sha256": (_sha(b"old") + "\n").encode()})
    problems = stale_sidecars(src, nm)
    assert len(problems) == 1 and "det/v1/models/scaler.pkl" in problems[0]


def test_matching_or_absent_sidecar_passes(tmp_path):
    src, nm = tmp_path / "src", tmp_path / "nm"
    _tree(src, {"a/v1/models/x.pkl": b"same", "b/v1/models/y.pkl": b"no sidecar anywhere"})
    _tree(nm, {"a/v1/models/x.pkl.sha256": (_sha(b"same") + "  x.pkl\n").encode()})
    assert stale_sidecars(src, nm) == []


def test_a_shipped_sidecar_is_the_one_checked(tmp_path):
    """A sidecar that ships overwrites NexusMind's, so NexusMind's stale one must not fail it."""
    src, nm = tmp_path / "src", tmp_path / "nm"
    _tree(src, {"d/v1/models/m.pkl": b"new", "d/v1/models/m.pkl.sha256": _sha(b"new").encode()})
    _tree(nm, {"d/v1/models/m.pkl.sha256": _sha(b"old").encode()})
    assert stale_sidecars(src, nm) == []
    _tree(src, {"d/v1/models/m.pkl.sha256": _sha(b"wrong").encode()})
    assert len(stale_sidecars(src, nm)) == 1


def test_sidecar_check_on_the_real_trees_when_nexusmind_is_present():
    nm = REPO.parent / "NexusMind" / "filters" / "common"
    if not nm.is_dir():
        pytest.skip("no NexusMind checkout beside this repo")
    assert stale_sidecars(COMMON, nm) == []


# --- The guard as the deploy runs it (round-2 review of 054a0a3) -------------------------
# The tests above prove the predicate. These prove the WIRING: the CLI's exit code, the
# argument order, and that the real deploy_to_nexusmind.sh stops before step 1. Four
# mutants (exit code forced to 0, arguments swapped in Python or in the .sh, `exit 1`
# dropped) passed every test above.

import os
import shutil
import subprocess
import sys

MODULE = REPO / "scripts" / "deployment" / "common_runtime_files.py"
DEPLOY = REPO / "scripts" / "deploy_to_nexusmind.sh"


def _cli(*args):
    return subprocess.run([sys.executable, str(MODULE), *map(str, args)],
                          capture_output=True, text=True)


@pytest.mark.parametrize("flag", ["--check-sidecars", "--check-filter-sidecars"])
def test_cli_exit_code_and_argument_order(tmp_path, flag):
    src, nm = tmp_path / "src", tmp_path / "nm"
    _tree(src, {"m/s.pkl": b"retrained"})
    _tree(nm, {"m/s.pkl": b"old", "m/s.pkl.sha256": (_sha(b"old") + "\n").encode()})
    stale = _cli(flag, nm, src)
    assert stale.returncode == 1 and "STALE SIDECAR" in stale.stderr
    # Swapped, NexusMind's own pickle matches its own sidecar: the guard would be blind.
    # Pinning that the swap passes is what makes the order above load-bearing.
    assert _cli(flag, src, nm).returncode == 0
    (nm / "m/s.pkl.sha256").write_text(_sha(b"retrained") + "\n")
    assert _cli(flag, nm, src).returncode == 0


def test_filter_check_covers_files_the_common_rule_excludes(tmp_path):
    """Step 1 copies the whole package with `cp -r`, so no runtime-file rule applies."""
    src, nm = tmp_path / "src", tmp_path / "nm"
    _tree(src, {"training/p.pkl": b"new"})
    _tree(nm, {"training/p.pkl.sha256": (_sha(b"old") + "\n").encode()})
    assert _cli("--check-sidecars", nm, src).returncode == 0
    assert _cli("--check-filter-sidecars", nm, src).returncode == 1


def _git_repo(root, files):
    _tree(root, files)
    g = ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(g + ["add", "-A"], check=True)
    subprocess.run(g + ["commit", "-qm", "init"], check=True)


@pytest.mark.skipif(shutil.which("bash") is None or shutil.which("git") is None,
                    reason="needs bash and git")
@pytest.mark.parametrize("where", ["filter", "common", "none"])
def test_real_deploy_script_stops_before_step1_on_a_stale_sidecar(tmp_path, where):
    """Runs the shipped .sh against throwaway trees; steps 0 and 0.5 are stubbed to pass."""
    dist, nm = tmp_path / "dist root", tmp_path / "nm root"   # spaces on purpose
    ok = b"import sys; sys.exit(0)\n"
    _git_repo(dist, {
        "filters/x/v1/probe/p.pkl": b"new probe",
        "filters/common/det/v1/models/s.pkl": b"new detector",
        "scripts/deployment/verify_filter_package.py": ok,
        "scripts/deployment/preflight_deploy_guards.py": ok,
        "scripts/deployment/common_runtime_files.py": MODULE.read_bytes(),
        "scripts/deployment/detector_manifest.py": (MODULE.parent / "detector_manifest.py").read_bytes(),
        "scripts/deployment/deploy_detectors.py": ok,   # step 0.7 / 2a: tested in test_deploy_detectors.py
    })
    stale = (_sha(b"old") + "\n").encode()
    nm_files = {"README": b"nm\n"}
    if where == "filter":
        nm_files["filters/x/v1/probe/p.pkl.sha256"] = stale
    elif where == "common":
        nm_files["filters/common/det/v1/models/s.pkl.sha256"] = stale
    _git_repo(nm, nm_files)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "python").symlink_to(sys.executable)
    (bin_dir / "python3").symlink_to(sys.executable)
    env = {**os.environ, "DISTILLERY_ROOT": str(dist), "NEXUSMIND_ROOT": str(nm),
           "HF_TOKEN": "unused", "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}
    r = subprocess.run(["bash", str(DEPLOY), "x", "v1", "--dry-run"],
                       capture_output=True, text=True, env=env, timeout=120)
    out = r.stdout + r.stderr
    if where == "none":   # presence control: the same harness reaches the copy
        assert "1. Copying filter" in out, out
        return
    assert r.returncode == 1, out
    assert "STALE SIDECAR" in out and "1. Copying filter" not in out, out
    status = subprocess.run(["git", "-C", str(nm), "status", "--porcelain"],
                            capture_output=True, text=True, check=True).stdout
    assert status == "", status
