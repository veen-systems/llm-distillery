"""Pins train.py's refusal of a copied package that still imports its source (gotcha log 2026-10-12, recurred 2026-10-15).

The seeded positive is a real `cp -r` of a committed package into a sibling name, which is exactly how c2c and c2d
were built: the copy's inference*.py keep the source's absolute imports, so scoring loads the SOURCE's model.
"""
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from training.train import assert_package_imports_self  # noqa: E402

PACKAGES = sorted({p.parent for p in ROOT.glob("filters/*/*/inference*.py")})


def test_there_are_packages_to_check():
    assert len(PACKAGES) >= 10, PACKAGES             # an empty glob would make the next test vacuous


@pytest.mark.parametrize("pkg", PACKAGES, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_committed_packages_import_only_themselves(pkg):
    assert_package_imports_self(pkg)


def _copy(tmp_path, src="filters/belonging/v3", name="v1_copy"):
    dst = tmp_path / "filters" / "belonging" / name
    shutil.copytree(ROOT / src, dst, ignore=shutil.ignore_patterns("model", "probe", "*.safetensors", "__pycache__"))
    return dst


def test_a_cp_r_copy_is_refused(tmp_path):
    dst = _copy(tmp_path)
    with pytest.raises(SystemExit, match="filters.belonging.v3"):
        assert_package_imports_self(dst)


def test_the_rewritten_copy_passes(tmp_path):
    dst = _copy(tmp_path)
    for f in dst.glob("inference*.py"):
        f.write_text(f.read_text(encoding="utf-8").replace("filters.belonging.v3.", "filters.belonging.v1_copy."),
                     encoding="utf-8")
    assert_package_imports_self(dst)


def test_a_copy_across_filters_is_refused(tmp_path):
    dst = _copy(tmp_path, src="filters/solutions/v6", name="v6")      # same version name, different filter
    with pytest.raises(SystemExit, match="filters.solutions.v6"):
        assert_package_imports_self(dst)
