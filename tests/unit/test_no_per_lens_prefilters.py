"""Decision 0 (NexusMind#284, ruled 2026-09-28, executed 2026-10-01): the per-lens
rule prefilters are DELETED.

They never ran in production after 2026-02-10 (NexusMind's scorer builds every
scorer with use_prefilter=False); they only gated what the oracle labelled. A
`prefilter.py` that reappears in a package would silently start gating oracle
labelling again via `ground_truth.batch_scorer.load_filter_package`, so its
absence is checked here rather than stated in prose.

`ai-engineering-practice` is a separate product, not an ovr lens, and is not
covered by NexusMind#284 — it keeps its prefilter.
"""

from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
FILTERS = REPO / "filters"
ALLOWED = {"ai-engineering-practice"}  # top-level filter dir names


def _package_dirs():
    return sorted({p.parent for p in FILTERS.rglob("config.yaml")})


def _allowed(path: Path) -> bool:
    return path.relative_to(FILTERS).parts[0] in ALLOWED


def test_the_package_walk_finds_packages():
    # presence control: an empty walk would pass both checks below vacuously
    names = {p.relative_to(FILTERS).as_posix() for p in _package_dirs()}
    assert {"uplifting/v7", "cultural_discovery/v5", "solutions/v6"} <= names


def test_no_package_ships_a_prefilter_py():
    offenders = [
        p.relative_to(REPO).as_posix()
        for p in FILTERS.rglob("prefilter.py")
        if not _allowed(p)
    ]
    assert not offenders, (
        f"per-lens prefilters were deleted (NexusMind#284, decision 0); found {offenders}"
    )


def test_no_config_declares_a_prefilter_block():
    offenders = []
    for d in _package_dirs():
        if _allowed(d):
            continue
        cfg = yaml.safe_load((d / "config.yaml").read_text(encoding="utf-8")) or {}
        if "prefilter" in cfg:
            offenders.append(d.relative_to(REPO).as_posix())
    assert not offenders, f"config.yaml still declares `prefilter:` in {offenders}"


def test_the_oracle_gate_loads_no_lens_object_for_a_live_package():
    from ground_truth.batch_scorer import load_filter_package

    obj, _, _ = load_filter_package(FILTERS / "cultural_discovery" / "v5")
    assert obj is None


def test_scorers_refuse_use_prefilter_true():
    pytest.importorskip("torch")
    from filters.common.filter_base_scorer import FilterBaseScorer

    class _Probe(FilterBaseScorer):
        def _load_model(self):
            pass

    with pytest.raises(ValueError, match="decision 0"):
        # __init__ refuses before loading config, calibration or any model
        _Probe(device="cpu", use_prefilter=True)


def test_every_package_base_scorer_still_defines_load_prefilter():
    """Cross-repo compatibility, not dead code.

    NexusMind's copy of FilterBaseScorer (until it syncs this repo's) declares
    `_load_prefilter` an @abstractmethod. A package whose base_scorer drops it
    cannot be constructed there, so NO filter scores. Measured 2026-10-01: with
    the method removed from uplifting v7, `UpliftingScorer` is abstract against
    NexusMind's base and concrete against ours.
    """
    import ast

    missing = []
    found = 0
    for p in sorted(FILTERS.rglob("base_scorer.py")):
        if _allowed(p) or p.parent.name == "common":
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
            bases = {getattr(b, "id", getattr(b, "attr", "")) for b in cls.bases}
            if "FilterBaseScorer" not in bases:
                continue
            found += 1
            if not any(isinstance(n, ast.FunctionDef) and n.name == "_load_prefilter"
                       for n in cls.body):
                missing.append(p.relative_to(REPO).as_posix())
    assert found >= 7, f"walked only {found} FilterBaseScorer subclasses"
    assert not missing, f"_load_prefilter missing (breaks NexusMind's abstract base): {missing}"


def test_hybrid_scorer_refuses_use_prefilter_true():
    pytest.importorskip("torch")
    from filters.common.hybrid_scorer import HybridScorer

    class _Probe(HybridScorer):
        def _create_stage2_scorer(self):
            raise AssertionError("refusal must fire before stage 2 is built")

        def _get_embedding_stage_config(self):
            raise AssertionError("refusal must fire before stage 1 is built")

    with pytest.raises(ValueError, match="decision 0"):
        _Probe(device="cpu", use_prefilter=True)


def test_no_caller_asks_for_use_prefilter_true():
    """Review 2026-10-01 found three callers the deletion missed (a #95 diagnostic that
    then raised, an ML test whose `except: skip` would have hidden the raise, and
    verify_belonging_v1.py). Catches the literal keyword only — not positional,
    **kwargs or a variable (none exist as of 2026-10-01).
    Only the refusal tests may pass True on purpose. AST, so error messages and
    docstrings that mention the keyword do not count."""
    import ast

    allowed = {
        "tests/unit/test_no_per_lens_prefilters.py",
        "tests/unit/test_human_thriving_v8_stage1_threshold.py",
    }
    hits, scanned = [], 0
    for root in ("scripts", "tests", "training", "ground_truth", "filters"):
        for p in (REPO / root).rglob("*.py"):
            rel = p.relative_to(REPO).as_posix()
            if rel in allowed or rel.startswith("filters/ai-engineering-practice/"):
                continue
            try:
                tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                continue
            scanned += 1
            for node in ast.walk(tree):
                if (isinstance(node, ast.keyword) and node.arg == "use_prefilter"
                        and isinstance(node.value, ast.Constant) and node.value.value is True):
                    hits.append(f"{rel}:{node.value.lineno}")
    assert scanned > 100, f"scanned only {scanned} files"
    assert not hits, f"use_prefilter=True raises since decision 0: {hits}"
