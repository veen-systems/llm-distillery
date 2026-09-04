"""A filter package's parts must agree with each other, across every filter.

WHY THIS EXISTS. `scripts/deployment/verify_filter_package.py` passes `human_thriving v8`
7/7 with no weights, no normalization and no gate report — the "absence counts as success"
shape logged in `566254b`. It checks that parts are PRESENT and importable. It does not
check that they are CONSISTENT WITH EACH OTHER, and an inconsistent package scores
articles silently and wrongly rather than failing.

Both invariants below were found on 2026-09-04 by diffing v8 against the five deployed
packages rather than by reading it. Neither was violated at the time; they are pinned so
that stays true.

⛔ These are FLEET-WIDE on purpose. A guard that lives in one filter's test file protects
one filter and vanishes with it.
"""

import importlib
import io
import json
import pickle
import warnings
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
FILTERS = REPO_ROOT / "filters"


def _packages():
    """Every filter version that ships a config.yaml and a base_scorer.py."""
    out = []
    for cfg in sorted(FILTERS.glob("*/v*/config.yaml")):
        if (cfg.parent / "base_scorer.py").exists():
            out.append(cfg.parent)
    return out


def _scorer_class(pkg: Path):
    dotted = f"filters.{pkg.parent.name}.{pkg.name}.base_scorer"
    mod = importlib.import_module(dotted)
    for name, obj in vars(mod).items():
        if isinstance(obj, type) and name.startswith("Base") and hasattr(obj, "DIMENSION_NAMES"):
            return obj
    raise AssertionError(f"no scorer class with DIMENSION_NAMES in {dotted}")


def test_there_are_packages_to_check():
    """A zero here would make every parametrized test below vacuous — the shape this
    repo calls 'the instrument could not have said no'."""
    assert len(_packages()) >= 6, f"only {len(_packages())} packages discovered"


@pytest.mark.parametrize("pkg", _packages(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_head_tail_config_matches_what_the_model_was_trained_with(pkg):
    """⛔ INFERENCE MUST FEED THE MODEL THE SHAPE IT WAS TRAINED ON.

    `filter_base_scorer._load_preprocessing_config` reads
    `preprocessing.head_tail.enabled` and defaults it to **False when the block is
    absent**. `training_metadata.json` records `use_head_tail` for the run that produced
    the weights. If they disagree, every article is truncated differently at inference
    than in training — and nothing raises, logs or scores zero. The article just gets a
    wrong number.

    Measured 2026-09-04: all five deployed filters declare `enabled: true` and were
    trained with it; `human_thriving v8` declares no block at all and was trained without
    it — consistent, but consistent by ABSENCE, which is invisible.

    ⚠️ THE LIVE TRAP THIS GUARDS. `H-V8-15` arm (b) is literally `--use-head-tail`. If v8
    is ever retrained with it, this test fails until `config.yaml` gains the block — which
    is the point, because the alternative is a silently mis-fed model.
    """
    meta = pkg / "training_metadata.json"
    if not meta.exists():
        pytest.skip(f"{pkg.parent.name}/{pkg.name} ships no training_metadata.json — "
                    f"cannot verify (uplifting v7 is the known case, see its NO_HUB)")
    trained = json.loads(meta.read_text(encoding="utf-8")).get("use_head_tail")
    if trained is None:
        pytest.skip("training_metadata.json records no use_head_tail")

    cfg = yaml.safe_load((pkg / "config.yaml").read_text(encoding="utf-8")) or {}
    declared = bool(((cfg.get("preprocessing") or {}).get("head_tail") or {}).get("enabled", False))

    assert declared == bool(trained), (
        f"{pkg.parent.name}/{pkg.name}: config.yaml says head_tail enabled={declared} but "
        f"the model was trained with use_head_tail={trained}. Inference would feed the "
        f"model a differently-truncated article than training did, silently. Fix the "
        f"config block, or retrain."
    )


@pytest.mark.parametrize("pkg", _packages(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_probe_output_dim_matches_the_filters_dimension_count(pkg):
    """The Stage-1 probe emits one score per dimension, and `EmbeddingStage` rebuilds it
    from the pickle's own `model_config` — so a probe trained for a different dimension
    count loads without complaint and produces a weighted average over the wrong slots.

    `cultural_discovery v5` (5 dims) and `solutions v6` (7 dims) are what make this
    non-trivial: the count is not 6 everywhere, so a hardcoded 6 would pass on four
    packages and be wrong on two.
    """
    probe = pkg / "probe" / "embedding_probe_e5small.pkl"
    if not probe.exists():
        pytest.skip(f"{pkg.parent.name}/{pkg.name} ships no probe")

    # Deployed probes were pickled on CUDA; map to CPU exactly as EmbeddingStage does.
    import torch
    import torch.storage as _ts
    original = _ts._load_from_bytes
    _ts._load_from_bytes = lambda b: torch.load(io.BytesIO(b), map_location="cpu",
                                                weights_only=False)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with open(probe, "rb") as f:
                data = pickle.load(f)
    finally:
        _ts._load_from_bytes = original

    out_dim = data["model_config"]["output_dim"]
    n_dims = len(_scorer_class(pkg).DIMENSION_NAMES)
    assert out_dim == n_dims, (
        f"{pkg.parent.name}/{pkg.name}: probe emits {out_dim} scores but the filter has "
        f"{n_dims} dimensions. EmbeddingStage would weight the wrong slots and Stage 1 "
        f"would screen on a meaningless number."
    )


@pytest.mark.parametrize("pkg", _packages(), ids=lambda p: f"{p.parent.name}/{p.name}")
def test_stage1_threshold_stays_below_the_gatekeeper_cap(pkg):
    """⛔ THE STAGE-1 SCREEN SKIPS THE GATEKEEPER, AND ITS SAFETY ARGUMENT IS UNGUARDED.

    `hybrid_scorer.py`'s Stage-1-LOW branch does not apply the evidence gatekeeper, and says
    why in a comment: *"This is safe because the Stage 1 threshold (e.g., 2.25) is well below
    the gatekeeper cap (3.0), so any article that would be capped by the gatekeeper already
    falls below the threshold."*

    That is an invariant stated in prose and enforced by nothing. It matters because a
    Stage-1-LOW row does not merely get screened — the probe's number becomes the row's
    PUBLISHED score and tier (`result["scores"] = screen.scores`, then `_assign_tier`). So if
    the threshold were ever raised above the cap, articles the gatekeeper exists to cap would
    be scored and tiered by the probe with the cap never applied, silently.

    Measured 2026-09-04: every filter satisfies it, with margins from 1.25 (v8: 1.75 vs 3.0)
    to 2.75 (nature_recovery v4: 0.75 vs 3.5). Nothing was violated; this stops it starting.
    """
    ih = pkg / "inference_hybrid.py"
    if not ih.exists():
        pytest.skip(f"{pkg.parent.name}/{pkg.name} ships no inference_hybrid.py")

    cls = _scorer_class(pkg)
    if cls.GATEKEEPER_DIMENSION is None or not cls.GATEKEEPER_CAP:
        pytest.skip(f"{pkg.parent.name}/{pkg.name} has no gatekeeper — invariant N/A")

    # The threshold lives in a module constant for every filter except human_thriving v8,
    # which reads it from config.yaml (the wiring change of 2026-09-04).
    import re
    m = re.search(r"^DEFAULT_THRESHOLD\s*=\s*([\d.]+)", ih.read_text(encoding="utf-8"), re.M)
    if m:
        threshold = float(m.group(1))
    else:
        cfg = yaml.safe_load((pkg / "config.yaml").read_text(encoding="utf-8")) or {}
        threshold = ((cfg.get("hybrid_inference") or {}).get("stage1") or {}).get("threshold")
        if threshold is None:
            pytest.fail(f"{pkg.parent.name}/{pkg.name} has an inference_hybrid.py but no "
                        f"Stage-1 threshold in either a module constant or config.yaml — "
                        f"the invariant cannot be checked, which is not the same as met")
        threshold = float(threshold)

    assert threshold < cls.GATEKEEPER_CAP, (
        f"{pkg.parent.name}/{pkg.name}: Stage-1 threshold {threshold} is NOT below the "
        f"gatekeeper cap {cls.GATEKEEPER_CAP}. Stage 1 skips the gatekeeper on the argument "
        f"that anything it would cap already falls below the threshold — that argument is "
        f"now false, and Stage-1-LOW rows publish an uncapped probe score AND tier."
    )
