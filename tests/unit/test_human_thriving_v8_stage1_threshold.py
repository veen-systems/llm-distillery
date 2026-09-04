"""The Stage-1 threshold for human_thriving v8 must come from config.yaml.

WHAT THIS GUARDS, and why a test on `load_stage1_config` alone would not be enough:

Every other filter's `inference_hybrid.py` carries a module-level `DEFAULT_THRESHOLD`, and
nothing passes `config.yaml`'s `hybrid_inference.stage1.threshold` into the constructor
(verified 2026-08-21 -- no consumer in `filters/common/` or NexusMind's loader), so editing
the config there is a silent no-op. On `nature_recovery v4` the config says 3.225 and the
runtime uses 0.75 -- it has been lying for months, and that is the shape this file guards
against: a key that reads as an enforcement point and enforces nothing.
llm-distillery#144's sibling defect (`--select-metric` parsed and inert, 17th occurrence
of the working rule) shipped past 573 green tests because none of them REACHED the
changed module.

So these tests do not check that the reader works. They check the OUTCOME: mutate the
config file, and the config the constructor hands to `EmbeddingStage` -- the object that
actually screens -- follows it. Three directions:

  1. present and different  -> the runtime value changes with the file
  2. present but malformed  -> raises, never falls back to a number nobody chose
  3. mentioned but ABSENT   -> no module-level DEFAULT_THRESHOLD can reintroduce a
                               second place for the number to live

`HybridScorer.__init__` is stubbed because it loads Gemma-3-1B; the wiring under test is
in v8's own `__init__` body, which runs in full before that call.
"""

import importlib
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
V8_DIR = REPO_ROOT / "filters" / "human_thriving" / "v8"

hybrid_mod = importlib.import_module("filters.human_thriving.v8.inference_hybrid")


@pytest.fixture
def no_model_load(monkeypatch):
    """Stub HybridScorer.__init__ so no model is loaded, and capture the Stage-1 config
    the way the real base does: by calling _get_embedding_stage_config()."""
    from filters.common.hybrid_scorer import HybridScorer

    captured = {}

    def fake_init(self, device=None, use_prefilter=True):
        self.device_str = device or "cpu"
        self.use_prefilter = use_prefilter
        captured["stage1"] = self._get_embedding_stage_config()
        self.threshold = captured["stage1"]["threshold"]

    monkeypatch.setattr(HybridScorer, "__init__", fake_init)
    return captured


def _shipped_probe() -> Path:
    return REPO_ROOT / "filters" / "human_thriving" / "v8" / "probe" / "embedding_probe_e5small.pkl"


def _write_config(tmp_path: Path, stage1: dict | None) -> Path:
    """A minimal config.yaml carrying only what the reader needs."""
    body: dict = {"filter": {"name": "human_thriving", "version": "8.0"}}
    if stage1 is not None:
        body["hybrid_inference"] = {"stage1": stage1, "stage2": {"model": "current"}}
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(body), encoding="utf-8")
    return path


# --- direction 1: the runtime follows the file ---------------------------------------

@pytest.mark.parametrize("configured", [0.25, 1.75, 3.5])
def test_embedding_stage_threshold_follows_config(no_model_load, tmp_path, configured):
    cfg = _write_config(tmp_path, {
        "embedding_model": "intfloat/multilingual-e5-small",
        "probe_path": "probe/embedding_probe_e5small.pkl",
        "threshold": configured,
    })
    scorer = hybrid_mod.HumanThrivingHybridScorer(config_path=cfg, device="cpu")
    # The number that reaches EmbeddingStage -- the object that screens -- not just the
    # number the reader returned.
    assert no_model_load["stage1"]["threshold"] == configured
    assert scorer.threshold == configured
    assert scorer._threshold_source == str(cfg)


def test_embedding_model_and_probe_path_follow_config(no_model_load, tmp_path):
    cfg = _write_config(tmp_path, {
        "embedding_model": "some/other-encoder",
        "probe_path": "probe/alternative.pkl",
        "threshold": 1.75,
    })
    hybrid_mod.HumanThrivingHybridScorer(config_path=cfg, device="cpu")
    assert no_model_load["stage1"]["embedding_model_name"] == "some/other-encoder"
    assert no_model_load["stage1"]["probe_path"].endswith("probe/alternative.pkl")


def test_explicit_threshold_overrides_config_and_says_so(no_model_load, tmp_path):
    """Sweeps need an override; it must be visible in the provenance, not silent."""
    cfg = _write_config(tmp_path, {"threshold": 1.75})
    scorer = hybrid_mod.HumanThrivingHybridScorer(
        config_path=cfg, threshold=2.825, device="cpu"
    )
    assert no_model_load["stage1"]["threshold"] == 2.825
    assert scorer._threshold_source == "constructor override"


# --- direction 2: malformed raises, never defaults ------------------------------------

def test_missing_hybrid_inference_block_raises(tmp_path):
    cfg = _write_config(tmp_path, None)
    with pytest.raises(KeyError, match="hybrid_inference.stage1"):
        hybrid_mod.load_stage1_config(cfg)


def test_stage1_block_without_threshold_raises(tmp_path):
    cfg = _write_config(tmp_path, {"embedding_model": "intfloat/multilingual-e5-small"})
    with pytest.raises(KeyError, match="threshold"):
        hybrid_mod.load_stage1_config(cfg)


def test_missing_config_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        hybrid_mod.load_stage1_config(tmp_path / "nope.yaml")


# --- direction 3: no second place for the number to live ------------------------------

def test_module_defines_no_default_threshold_constant():
    """A module-level DEFAULT_THRESHOLD is exactly how the other 13 filter packages ended
    up with an inert config key -- and on two of them (nature_recovery v4, thriving v1) the
    config and the constant now disagree. If someone adds one back, this fails."""
    assert not hasattr(hybrid_mod, "DEFAULT_THRESHOLD"), (
        "inference_hybrid.py must not carry a module-level DEFAULT_THRESHOLD -- the "
        "threshold lives in config.yaml only. Two copies of a number disagree the "
        "moment one is edited."
    )


# --- the shipped package ---------------------------------------------------------------

def test_shipped_config_carries_a_usable_stage1_threshold():
    """The real package must be loadable, and its screen must sit BELOW the surfacing
    op-point: a Stage-1 threshold at or above the tier threshold would screen out
    articles the filter is meant to surface, with no output to notice it in.

    Deliberately does NOT pin 1.75 -- that would recreate the second copy this file
    exists to prevent. The re-derivation record is the config comment and
    docs/evidence/2026-09-04-v8-probe-calibration/.
    """
    stage1 = hybrid_mod.load_stage1_config(V8_DIR / "config.yaml")
    from filters.human_thriving.v8.base_scorer import BaseHumanThrivingScorer

    op_point = min(t for _n, t, _d in BaseHumanThrivingScorer.TIER_THRESHOLDS if t > 0)
    assert isinstance(stage1["threshold"], float)
    assert 0.0 < stage1["threshold"] < op_point, (
        f"Stage-1 threshold {stage1['threshold']} must sit strictly between 0 and the "
        f"{op_point} surfacing op-point."
    )
    assert stage1["embedding_model"] == "intfloat/multilingual-e5-small"


# --- the threshold is pinned to the probe it was derived against -----------------------
#
# Measured 2026-09-04: the same data, objective and code with --seed 7 instead of 42
# produced a probe on which the configured 1.75 routes 0.7406 (val) / 0.7567 (test)
# weighted instead of 0.8876 / 0.8935 -- ~14 pp fewer articles reaching Stage 2, from the
# seed alone, with FN@MEDIUM+ still 0 on both. Stage 1 is silent, so nothing surfaces this.

def test_shipped_probe_matches_the_hash_recorded_with_the_threshold():
    stage1 = hybrid_mod.load_stage1_config(V8_DIR / "config.yaml")
    assert stage1["probe_sha256"], (
        "config.yaml must pin `probe_sha256` beside the threshold, or a retrained probe "
        "silently inherits a threshold derived for a different one."
    )
    hybrid_mod.verify_probe_matches_threshold(_shipped_probe(), stage1["probe_sha256"])


def test_unpaired_probe_refuses_to_construct(no_model_load, tmp_path):
    """The outcome, not the predicate: a config whose probe hash does not match must
    make the SCORER refuse, not merely make a helper return False."""
    import shutil

    probe_copy = tmp_path / "embedding_probe_e5small.pkl"
    shutil.copy(_shipped_probe(), probe_copy)
    cfg = _write_config(tmp_path, {
        "threshold": 1.75,
        "probe_path": "embedding_probe_e5small.pkl",
        "probe_sha256": "0" * 64,
    })
    with pytest.raises(ValueError, match="RE-DERIVED threshold"):
        hybrid_mod.HumanThrivingHybridScorer(config_path=cfg, device="cpu")


def test_explicit_threshold_override_skips_the_pin(no_model_load, tmp_path):
    """A sweep deliberately points a chosen threshold at some other probe. Pinning there
    would block the very measurement that re-derives the threshold."""
    import shutil

    probe_copy = tmp_path / "embedding_probe_e5small.pkl"
    shutil.copy(_shipped_probe(), probe_copy)
    cfg = _write_config(tmp_path, {
        "threshold": 1.75,
        "probe_path": "embedding_probe_e5small.pkl",
        "probe_sha256": "0" * 64,
    })
    scorer = hybrid_mod.HumanThrivingHybridScorer(
        config_path=cfg, threshold=2.55, device="cpu"
    )
    assert scorer.threshold == 2.55


def test_unpinned_config_still_constructs(no_model_load, tmp_path):
    """`probe_sha256` absent means unpinned, not invalid -- other filters have no such
    key and this module's reader is shared with nothing, but the default must not be a
    crash for a config that predates the pin."""
    import shutil

    probe_copy = tmp_path / "embedding_probe_e5small.pkl"
    shutil.copy(_shipped_probe(), probe_copy)
    cfg = _write_config(tmp_path, {
        "threshold": 1.75,
        "probe_path": "embedding_probe_e5small.pkl",
    })
    scorer = hybrid_mod.HumanThrivingHybridScorer(config_path=cfg, device="cpu")
    assert scorer.threshold == 1.75


def test_missing_probe_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        hybrid_mod.verify_probe_matches_threshold(tmp_path / "nope.pkl", "0" * 64)


# --- the no-prefilter refusal must fire on the path that SCORES -----------------------
#
# `base_scorer._load_prefilter` raising was NOT sufficient: `HybridScorer`'s
# `_create_stage2_scorer` hardcodes use_prefilter=False, so the Stage-2 scorer never
# reaches that raise, and before 2026-09-04 a hybrid built with use_prefilter=True
# constructed happily with `self.use_prefilter = True` and no prefilter -- the documented
# refusal was unreachable on the only path that matters. Found by review, not by the suite.

def test_hybrid_refuses_use_prefilter():
    with pytest.raises(NotImplementedError, match="no per-lens prefilter"):
        hybrid_mod.HumanThrivingHybridScorer(use_prefilter=True, device="cpu")


def test_hybrid_refusal_precedes_the_config_read(tmp_path):
    """It must fire even on a package whose config.yaml is missing -- otherwise the error
    a caller sees is FileNotFoundError and the real problem is masked."""
    with pytest.raises(NotImplementedError):
        hybrid_mod.HumanThrivingHybridScorer(
            config_path=tmp_path / "does-not-exist.yaml", use_prefilter=True, device="cpu"
        )
