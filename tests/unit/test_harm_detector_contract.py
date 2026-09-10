"""The harm detector's shipped contract: a SCORE, never a verdict (#156, ADR-022).

These tests are deliberately about SHAPE and REFUSAL, not accuracy. Accuracy lives in
`EXP-037`; what can rot silently here is the stamp growing a threshold, or a partial
ensemble being averaged as though it were the measured model.

No model artifacts are loaded — the pickles are gitignored (out-of-band, like every other
detector here) and these tests must pass in CI on a bare checkout.
"""

import ast
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PKG = REPO / "filters" / "common" / "harm_detector"
INFERENCE = PKG / "v1" / "inference.py"
CONFIG = PKG / "v1" / "models" / "training_config.json"


def test_inference_module_exists():
    assert INFERENCE.exists(), "harm detector v1 has no inference module"


def test_no_threshold_anywhere_in_the_inference_module():
    """`obituary v3` takes `threshold=0.95` in its constructor. This one must not.

    A threshold in the artifact is a decision baked into a stamp, and ADR-022 puts the
    decision in per-lens config instead. This test is the thing that notices if someone
    adds a convenient default later.
    """
    tree = ast.parse(INFERENCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.arg) and "threshold" in node.arg.lower():
            pytest.fail(f"inference.py takes a `{node.arg}` argument — the stamp must not "
                        f"carry a decision (ADR-022; see the module docstring)")
        if isinstance(node, ast.Name) and node.id.lower() == "threshold":
            pytest.fail("inference.py references a `threshold` name")


def test_stamp_keys_are_score_and_version_only():
    src = INFERENCE.read_text(encoding="utf-8")
    assert "harm_is_subject_score" in src
    assert "harm_detector_version" in src
    for forbidden in ("is_harm", "harm_verdict", "should_block", "blocked"):
        assert f'"{forbidden}"' not in src, f"stamp must not carry `{forbidden}`"


@pytest.mark.skipif(not CONFIG.exists(), reason="artifact not built in this checkout")
def test_built_config_declares_stamp_only_and_no_threshold():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert cfg["stamp_only"] is True
    assert cfg["threshold"] is None, "a threshold reached the shipped artifact"
    assert cfg["ensemble_seeds"] == [0, 1, 2, 3, 4], (
        "the ensemble is the H-DET2 fix — a single seed ships a lottery ticket"
    )
    assert cfg["provenance"]["worktree"] in {"clean", "untracked-only"}, (
        f"artifact built from a modified tree: {cfg['provenance']['modified_tracked_files']}"
    )


@pytest.mark.skipif(not CONFIG.exists(), reason="artifact not built in this checkout")
def test_every_declared_head_has_a_recorded_hash():
    """A declared seed with no artifact is a DIFFERENT model, not a degraded one."""
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    sums = (PKG / "v1" / "models" / "SHA256SUMS.txt").read_text(encoding="utf-8")
    for seed in cfg["ensemble_seeds"]:
        assert f"mlp_classifier_seed{seed}.pkl" in sums, f"seed {seed} declared but unhashed"
    assert "scaler.pkl" in sums
