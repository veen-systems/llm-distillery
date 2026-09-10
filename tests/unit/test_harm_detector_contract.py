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

    ⛔ **Widened 2026-09-10 after review: the first version did not do what this docstring
    says.** It walked `ast.arg` and `ast.Name` only, so the most natural way to add a
    threshold — `self.threshold = 0.85`, an `ast.Attribute` whose Name is `self` — passed in
    silence, as did a differently-named argument like `cut=0.85`. A guard that names its own
    purpose and then checks a narrower predicate is worse than no guard: it is read as
    covering the thing it does not cover.
    """
    src = INFERENCE.read_text(encoding="utf-8")
    tree = ast.parse(src)

    def _is_threshold_ish(name: str) -> bool:
        n = name.lower()
        return any(t in n for t in ("threshold", "cutoff", "cut_off", "min_score"))

    for node in ast.walk(tree):
        if isinstance(node, ast.arg) and _is_threshold_ish(node.arg):
            pytest.fail(f"inference.py takes a `{node.arg}` argument — the stamp must not "
                        f"carry a decision (ADR-022; see the module docstring)")
        if isinstance(node, ast.Name) and _is_threshold_ish(node.id):
            pytest.fail(f"inference.py references a `{node.id}` name")
        # `self.threshold = ...` — the shape the original test missed entirely.
        if isinstance(node, ast.Attribute) and _is_threshold_ish(node.attr):
            pytest.fail(f"inference.py sets or reads `.{node.attr}` — a threshold on the "
                        f"object is still a decision in the artifact")
        # A bare float default on __init__ is how a threshold arrives wearing another name.
        if isinstance(node, ast.FunctionDef) and node.name == "__init__":
            for d in node.args.defaults:
                if isinstance(d, ast.Constant) and isinstance(d.value, float):
                    pytest.fail(f"inference.py's __init__ has a float default ({d.value}) — "
                                f"the stamp-only contract admits no numeric knob")


def test_stamp_returns_exactly_two_keys_parsed_not_grepped():
    """The companion hole: the key test below matches SUBSTRINGS in the source.

    A new key added to the returned dict passes it as long as the key's name is not on a
    hand-written forbidden list — which is the denylist shape this repo removed from the
    DeepSeek guard on the same day. Parse the returned dict instead and require exactly the
    two keys, so an ADDITION fails rather than only a known-bad name.
    """
    tree = ast.parse(INFERENCE.read_text(encoding="utf-8"))
    stamps = [n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "stamp"]
    assert len(stamps) == 1, "expected exactly one stamp() in inference.py"
    returns = [n for n in ast.walk(stamps[0]) if isinstance(n, ast.Return)]
    assert len(returns) == 1 and isinstance(returns[0].value, ast.Dict), (
        "stamp() must return a single dict literal, so its keys are statically checkable"
    )
    keys = {k.value for k in returns[0].value.keys if isinstance(k, ast.Constant)}
    assert keys == {"_harm_is_subject_score", "_harm_detector_model"}, (
        f"stamp() returns {sorted(keys)} — the stamp-only contract is exactly a score and a "
        f"version; anything else is a decision or an unreviewed field"
    )


def test_stamp_keys_are_score_and_version_only():
    src = INFERENCE.read_text(encoding="utf-8")
    assert "_harm_is_subject_score" in src
    assert "_harm_detector_model" in src
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


# ---- the loader's refusals, added 2026-09-10 after review found each one one-directional ----

@pytest.mark.skipif(not CONFIG.exists(), reason="artifact not built in this checkout")
@pytest.mark.parametrize("declared,why", [
    ([0, 1], "fewer heads than on disk — silently loaded 2 of 5 with an identical version stamp"),
    ([0, 1, 2, 3, 4, 5], "more heads than on disk"),
])
def test_load_refuses_an_ensemble_that_disagrees_with_the_directory(tmp_path, declared, why):
    """⛔ Both directions. The first version checked only that every DECLARED seed existed.

    Measured before the fix: `ensemble_seeds: [0,1]` loaded two heads out of five, produced a
    0.083 score shift on identical input, and stamped the SAME version string.
    """
    import json as _json
    import shutil as _shutil

    from filters.common.harm_detector.v1.inference import HarmDetectorV1

    src = PKG / "v1" / "models"
    dst = tmp_path / "models"
    dst.mkdir()
    for f in src.iterdir():
        if f.is_file():
            _shutil.copy2(f, dst / f.name)
    cfg = _json.loads((dst / "training_config.json").read_text(encoding="utf-8"))
    cfg["ensemble_seeds"] = declared
    (dst / "training_config.json").write_text(_json.dumps(cfg), encoding="utf-8")

    with pytest.raises(ValueError, match="ensemble mismatch"):
        HarmDetectorV1(model_dir=dst)._load()


@pytest.mark.skipif(not CONFIG.exists(), reason="artifact not built in this checkout")
def test_load_refuses_a_pickle_whose_hash_does_not_match(tmp_path):
    """SHA256SUMS.txt existed and nothing read it — any pickle could be swapped silently."""
    import shutil as _shutil

    from filters.common.harm_detector.v1.inference import HarmDetectorV1

    src = PKG / "v1" / "models"
    dst = tmp_path / "models"
    dst.mkdir()
    for f in src.iterdir():
        if f.is_file():
            _shutil.copy2(f, dst / f.name)
    target = dst / "mlp_classifier_seed0.pkl"
    target.write_bytes(target.read_bytes() + b"\x00")     # one byte is enough

    with pytest.raises(ValueError, match="integrity check FAILED"):
        HarmDetectorV1(model_dir=dst)._load()


@pytest.mark.skipif(not CONFIG.exists(), reason="artifact not built in this checkout")
def test_load_refuses_when_no_hash_is_recorded_at_all(tmp_path):
    """A missing manifest must raise, not silently skip the check — an unverified pickle is
    arbitrary code, and 'no expectation' is exactly how a hash guard becomes decoration."""
    import shutil as _shutil

    from filters.common.harm_detector.v1.inference import HarmDetectorV1

    src = PKG / "v1" / "models"
    dst = tmp_path / "models"
    dst.mkdir()
    for f in src.iterdir():
        if f.is_file() and not f.name.endswith(".sha256") and f.name != "SHA256SUMS.txt":
            _shutil.copy2(f, dst / f.name)

    with pytest.raises(ValueError, match="no recorded hash"):
        HarmDetectorV1(model_dir=dst)._load()


def test_batch_score_raises_rather_than_returning_an_empty_list_for_a_full_input():
    """⛔ Added because a mutation survived: `_load` now refuses an empty ensemble, so this
    guard is unreachable through it — and therefore untested until it is tested directly.

    Measured before the fix: `zip(*[])` is empty for ANY input, so 100 articles in returned 0
    scores out with no error, and a caller doing `zip(articles, batch_score(articles))` stamped
    nothing and reported success.
    """
    from filters.common.harm_detector.v1.inference import HarmDetectorV1

    d = HarmDetectorV1()
    d._classifiers = []                       # bypass _load: the state a refactor could reach
    d._scaler = object()
    d._embedder = object()
    with pytest.raises(RuntimeError, match="no classifier heads"):
        d.batch_score([{"title": "t", "content": "c"}] * 100)


def test_batch_score_refuses_a_score_list_shorter_than_its_input():
    """The second half of the same defect: a length mismatch must not reach the caller."""
    import numpy as np

    from filters.common.harm_detector.v1.inference import HarmDetectorV1

    class _ShortHead:
        def predict_proba(self, z):
            return np.zeros((1, 2))           # one row, whatever the input length

    class _PassthroughScaler:
        def transform(self, x):
            return x

    class _Embedder:
        def encode(self, texts, **kw):
            return np.zeros((len(texts), 8))

    d = HarmDetectorV1()
    d._classifiers = [_ShortHead()]
    d._scaler = _PassthroughScaler()
    d._embedder = _Embedder()
    with pytest.raises(RuntimeError, match="refusing to return a list"):
        d.batch_score([{"title": "t", "content": "c"}] * 5)
