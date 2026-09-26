"""What deploy_to_nexusmind.sh step 2 ships from filters/common (#164: runtime files only).

Each rule is tested both ways, on a synthetic tree (so the untracked-model case is covered
even where the .pkl files are absent) and on the real tree. The two failure modes this guards:
- shipping training/validation/GT material again, which the owner ruled out;
- dropping a file a detector reads at load time. Excluding by NAME (`training_config.json`)
  or switching to `git ls-files` would each do that: harm_detector/v1/inference.py reads
  training_config.json and SHA256SUMS.txt, and every *.pkl is gitignored here.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.deployment.common_runtime_files import is_runtime, runtime_files

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
