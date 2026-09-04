"""The shipped human_thriving v8 Stage-1 probe must load, and its integrity check
must actually be able to fail.

`EmbeddingStage._load_probe` calls `_verify_pickle_integrity`, which compares the pickle
against a companion `<name>.pkl.sha256` IF ONE EXISTS and only `logger.debug`s when it
does not. No filter in this repo shipped one before 2026-09-04, so the mechanism has
been dormant since it was written -- present, correct, and reachable by nothing.

v8 ships the hash file. These tests establish the two halves separately, because a
passing integrity check proves nothing on its own: it also passes when the check is
switched off.

  1. the shipped pickle's hash matches its shipped .sha256, and the probe loads
  2. a MISMATCHED .sha256 raises -- i.e. the check can say no

Direction 2 is the one that matters. Compare with the `--select-metric` defect
(llm-distillery#144): a mechanism whose negative case is never exercised is
indistinguishable from an absent one.
"""

import hashlib
import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBE = REPO_ROOT / "filters" / "human_thriving" / "v8" / "probe" / "embedding_probe_e5small.pkl"
PROBE_SHA = Path(str(PROBE) + ".sha256")


def _stage(probe_path: Path):
    from filters.common.embedding_stage import EmbeddingStage
    from filters.human_thriving.v8.base_scorer import BaseHumanThrivingScorer

    return EmbeddingStage(
        embedding_model_name="intfloat/multilingual-e5-small",
        probe_path=str(probe_path),
        threshold=1.75,
        dimension_weights=BaseHumanThrivingScorer.DIMENSION_WEIGHTS,
        dimension_names=BaseHumanThrivingScorer.DIMENSION_NAMES,
        device="cpu",
    )


def test_probe_and_hash_file_are_both_shipped():
    assert PROBE.exists(), f"{PROBE} missing -- the package is not reproducible without it"
    assert PROBE_SHA.exists(), (
        f"{PROBE_SHA} missing. Without it _verify_pickle_integrity silently skips, and "
        f"a truncated or swapped probe loads as if fine."
    )


def test_shipped_hash_matches_shipped_pickle():
    expected = PROBE_SHA.read_text().strip().split()[0]
    actual = hashlib.sha256(PROBE.read_bytes()).hexdigest()
    assert actual == expected


def test_shipped_probe_loads_through_the_real_embedding_stage():
    """Loads via the class production loads, not via pickle.load directly: the probe's
    architecture must match MLPProbe's reconstruction or the state_dict load fails."""
    stage = _stage(PROBE)
    assert stage.probe is not None
    assert stage.scaler is not None
    assert stage.threshold == 1.75


def test_recall_objective_metrics_and_seed_are_recorded():
    """Provenance the package cannot be re-derived without. The seed matters because
    probes trained before 2026-09-04 were UNSEEDED (`scripts/train_probe.py --seed`)."""
    import pickle

    with open(PROBE, "rb") as f:
        data = pickle.load(f)
    metrics = data.get("metrics", {})
    assert metrics.get("objective") == "recall", (
        "v8 must ship a recall-objective probe: an L1-regression probe floor-collapses "
        "on a 4.7%-positive corpus and drops needles at Stage 1 (ADR-023 does NOT apply "
        "to the probe -- there the FN is the expensive error)."
    )
    assert metrics.get("seed") is not None
    assert metrics.get("embedding_model") == "intfloat/multilingual-e5-small"

    # ⛔ The library stack is part of the artifact's identity, and NEITHER hash can see it:
    # the pickle carries an sklearn StandardScaler, a cross-version load only warns
    # (`InconsistentVersionWarning: ... might lead to breaking code or invalid results`),
    # and the file is byte-identical either way. This project's own measured library-stack
    # term is max |Δ| 0.2008 -- larger than the #95 batch floor.
    versions = metrics.get("versions") or {}
    assert versions.get("scikit-learn"), (
        "the probe must record the sklearn version it was pickled under -- a cross-version "
        "load warns and does not fail, so nothing else surfaces it."
    )
    assert versions.get("torch")
    assert versions.get("sentence-transformers")
    # Trained on b650-gpu's venv-prodparity, i.e. GPU-SERVER's pins (not sadalsuud's).
    assert versions["scikit-learn"] == "1.8.0", (
        f"probe pickled under sklearn {versions['scikit-learn']}, not production's 1.8.0"
    )


def test_mismatched_hash_file_raises(tmp_path):
    """The half that proves the check is live rather than merely present."""
    probe_copy = tmp_path / "embedding_probe_e5small.pkl"
    shutil.copy(PROBE, probe_copy)
    Path(str(probe_copy) + ".sha256").write_text(
        "0" * 64 + "  embedding_probe_e5small.pkl\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="integrity check failed"):
        _stage(probe_copy)


def test_absent_hash_file_still_loads(tmp_path):
    """Documents the dormant-by-default behaviour rather than asserting it is good:
    with no .sha256 the check is skipped, which is why every other filter's probe is
    unverified. If this ever starts raising, every other probe package breaks too
    (8 probe .pkl are tracked; `git ls-files '*.pkl.sha256'` returned 0 before v8)."""
    probe_copy = tmp_path / "embedding_probe_e5small.pkl"
    shutil.copy(PROBE, probe_copy)
    stage = _stage(probe_copy)
    assert stage.probe is not None
