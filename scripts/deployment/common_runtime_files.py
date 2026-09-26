"""Which files under filters/common/ ship to NexusMind (deploy_to_nexusmind.sh step 2).

Owner ruling, llm-distillery#164 (2026-09-26): NexusMind carries RUNTIME files only, not
ground-truth, training or validation material.

The rule excludes by DIRECTORY plus two labelling-only file names. It deliberately does NOT
use `git ls-files`: the detector model files (`*/models/*.pkl`, `*.safetensors`) are
gitignored here and reach NexusMind only through this copy. Nor does it exclude by names such
as `training_config.json` or `SHA256SUMS.txt`: `harm_detector/v1/inference.py` reads both at
load time. `tests/unit/test_common_runtime_files.py` pins both facts on the real tree.

Usage (prints one path per line, relative to filters/common, sorted):
    python scripts/deployment/common_runtime_files.py [COMMON_DIR]
"""

from __future__ import annotations

import sys
from pathlib import Path

# A path with any of these as a directory component is not shipped.
EXCLUDED_DIRS = frozenset({"training", "validation", "docs", "tests", "__pycache__"})
# Labelling-only: the detectors' oracles and the prompt `commerce_prefilter/v1/oracle.py`
# reads. `violence_promotion/v1/oracle.py` imports `ground_truth`, which NexusMind lacks.
EXCLUDED_NAMES = frozenset({"oracle.py", "prompt.md"})


def is_runtime(rel: Path) -> bool:
    """True when `rel` (relative to filters/common) ships to NexusMind."""
    if EXCLUDED_DIRS.intersection(rel.parts[:-1]):
        return False
    return rel.name not in EXCLUDED_NAMES


def runtime_files(common_dir: Path) -> list[Path]:
    """Every file under `common_dir` that ships, relative to it, sorted."""
    return sorted(
        p.relative_to(common_dir)
        for p in common_dir.rglob("*")
        if p.is_file() and is_runtime(p.relative_to(common_dir))
    )


def main(argv: list[str]) -> int:
    common = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parents[2] / "filters" / "common"
    if not common.is_dir():
        print(f"ERROR: not a directory: {common}", file=sys.stderr)
        return 1
    for rel in runtime_files(common):
        print(rel.as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
