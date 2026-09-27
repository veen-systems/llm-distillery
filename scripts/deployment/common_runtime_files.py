"""Which files under filters/common/ ship to NexusMind (deploy_to_nexusmind.sh step 2).

Owner ruling, llm-distillery#164 (2026-09-26): NexusMind carries RUNTIME files only, not
ground-truth, training or validation material.

The rule excludes by DIRECTORY plus two labelling-only file names. It deliberately does NOT
use `git ls-files`: the model files of an UNPACKAGED detector are gitignored here and would
reach NexusMind only through this copy. (Retired versions, RETIRED_DIRS, do not ship at all.) The four packaged detectors
(ADR-024) ship by MANIFEST.json through deploy_detectors.py instead; `--unpackaged` leaves them out. Nor does it exclude by names such
as `training_config.json` or `SHA256SUMS.txt`: `harm_detector/v1/inference.py` reads both at
load time. `tests/unit/test_common_runtime_files.py` pins both facts on the real tree.

Usage:
    python scripts/deployment/common_runtime_files.py [COMMON_DIR]
        prints one shipped path per line, relative to filters/common, sorted
    python scripts/deployment/common_runtime_files.py --unpackaged [COMMON_DIR]
        the same, WITHOUT the packaged detector dirs (ADR-024): what step 2 still copies file by file
    python scripts/deployment/common_runtime_files.py --check-sidecars NEXUSMIND_COMMON [COMMON_DIR]
        exits 1 if a shipped .pkl would sit next to a .sha256 sidecar that does not match it
        (unpackaged files only: a packaged detector's sidecars are checked by deploy_detectors.py stage)
    python scripts/deployment/common_runtime_files.py --check-filter-sidecars NEXUSMIND_FILTER_DIR FILTER_DIR
        the same check for step 1, which copies EVERY file of the filter package (probe pickles)

Why the sidecar check: NexusMind keeps per-file `.sha256` sidecars this repo does not have,
and the deploy only copies, so they survive every deploy. A retrained pickle shipped next to
a stale sidecar makes the detector refuse to load (embedding_stage._verify_pickle_integrity,
harm_detector's _verify_hashes, where a sidecar overrides SHA256SUMS.txt). The real fix is
llm-distillery#165; this makes the failure happen at deploy time instead of in production.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.deployment.detector_manifest import PACKAGES  # noqa: E402

# A path with any of these as a directory component is not shipped.
EXCLUDED_DIRS = frozenset({"training", "validation", "docs", "tests", "__pycache__"})
# Labelling/training-only files outside those directories: the detectors' oracles and the
# prompt.md each oracle reads (commerce_prefilter/v1, violence_promotion/v1;
# violence's oracle.py imports `ground_truth`, which NexusMind lacks), and detector_seeds.py,
# the #158 seed-band helper that only training code imports.
EXCLUDED_NAMES = frozenset({"oracle.py", "prompt.md", "detector_seeds.py"})
# Retired detector versions: kept here as history, never shipped (owner, 2026-09-27). NexusMind
# loads none of them (commerce.py pins v1, obituary.py pins v5; gpu-server's /commerce/predict
# serves its own deploy/gpu-server/models copy) and deletes its copies in the same change.
RETIRED_DIRS = frozenset({("obituary_detector", "v3"), ("obituary_detector", "v4"),
                          ("commerce_prefilter", "v2")})


def is_runtime(rel: Path) -> bool:
    """True when `rel` (relative to filters/common) ships to NexusMind."""
    if EXCLUDED_DIRS.intersection(rel.parts[:-1]):
        return False
    if tuple(rel.parts[:2]) in RETIRED_DIRS:
        return False
    return rel.name not in EXCLUDED_NAMES


def runtime_files(common_dir: Path) -> list[Path]:
    """Every file under `common_dir` that ships, relative to it, sorted."""
    return sorted(
        p.relative_to(common_dir)
        for p in common_dir.rglob("*")
        if p.is_file() and is_runtime(p.relative_to(common_dir))
    )


def unpackaged_runtime_files(common_dir: Path) -> list[Path]:
    """`runtime_files` minus every packaged detector dir (ADR-024 step 3). Those ship ONLY through
    deploy_detectors.py, from their MANIFEST.json: never from this working tree's copy."""
    packaged = [tuple(p.split("/")) for p in PACKAGES]
    return [r for r in runtime_files(common_dir) if not any(r.parts[:len(p)] == p for p in packaged)]


def _sidecar_digest(path: Path) -> str:
    parts = path.read_text(encoding="utf-8").split()
    return parts[0] if parts else ""


def all_files(src_dir: Path) -> list[Path]:
    """Every file under `src_dir`, relative to it: what step 1's `cp -r` ships."""
    return sorted(p.relative_to(src_dir) for p in src_dir.rglob("*") if p.is_file())


def stale_sidecars(common_dir: Path, nexusmind_common: Path,
                   shipped: list[Path] | None = None) -> list[str]:
    """Shipped .pkl files that would sit next to a non-matching .sha256 after the copy.

    A sidecar that ships from this repo overwrites NexusMind's, so it is the one checked;
    otherwise NexusMind's existing sidecar is. No sidecar on either side: nothing to check
    (the loaders then skip or use SHA256SUMS.txt). `shipped` defaults to every runtime file
    (`runtime_files`); step 1 passes `all_files`, and step 0.6's common check `unpackaged_runtime_files`.
    """
    shipped = set(runtime_files(common_dir) if shipped is None else shipped)
    problems = []
    for rel in sorted(shipped):
        if rel.suffix != ".pkl":
            continue
        side_rel = rel.with_name(rel.name + ".sha256")
        side = common_dir / side_rel if side_rel in shipped else nexusmind_common / side_rel
        if not side.is_file():
            continue
        actual = hashlib.sha256((common_dir / rel).read_bytes()).hexdigest()
        expected = _sidecar_digest(side)
        if actual != expected:
            problems.append(f"{rel.as_posix()}: sha256 {actual[:12]} but {side} says {expected[:12] or '(empty)'}")
    return problems


def main(argv: list[str]) -> int:
    default_common = Path(__file__).resolve().parents[2] / "filters" / "common"
    if len(argv) > 1 and argv[1] == "--check-filter-sidecars":
        if len(argv) != 4:
            print("ERROR: --check-filter-sidecars needs NEXUSMIND_FILTER_DIR FILTER_DIR", file=sys.stderr)
            return 1
        src = Path(argv[3])
        if not src.is_dir():
            print(f"ERROR: not a directory: {src}", file=sys.stderr)
            return 1
        problems = stale_sidecars(src, Path(argv[2]), all_files(src))
        for p in problems:
            print(f"STALE SIDECAR: {p}", file=sys.stderr)
        return 1 if problems else 0
    if len(argv) > 1 and argv[1] == "--check-sidecars":
        if len(argv) < 3:
            print("ERROR: --check-sidecars needs NEXUSMIND_COMMON", file=sys.stderr)
            return 1
        common = Path(argv[3]) if len(argv) > 3 else default_common
        if not common.is_dir():
            print(f"ERROR: not a directory: {common}", file=sys.stderr)
            return 1
        problems = stale_sidecars(common, Path(argv[2]), unpackaged_runtime_files(common))
        for p in problems:
            print(f"STALE SIDECAR: {p}", file=sys.stderr)
        return 1 if problems else 0
    unpackaged = len(argv) > 1 and argv[1] == "--unpackaged"
    rest = argv[2:] if unpackaged else argv[1:]
    common = Path(rest[0]) if rest else default_common
    if not common.is_dir():
        print(f"ERROR: not a directory: {common}", file=sys.stderr)
        return 1
    for rel in (unpackaged_runtime_files if unpackaged else runtime_files)(common):
        print(rel.as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
