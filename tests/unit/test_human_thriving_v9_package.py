"""human_thriving v9 is v8's package with a retrained student. These tests pin what is
PACKAGE-SPECIFIC; the shared mechanics (threshold wiring, prefilter refusal, probe loading)
are v8's code unchanged and stay covered by the v8 test files.

The version-bump failure this guards: an inference module in vN that still imports vN-1
crashed the real entrypoint (FILTER_PLAYBOOK §8), and a stale Hub repo_id default loads the
previous model under the new name.
"""
import hashlib
import importlib
import json
import re
import struct
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
V8 = REPO_ROOT / "filters" / "human_thriving" / "v8"
V9 = REPO_ROOT / "filters" / "human_thriving" / "v9"
CODE = ["inference.py", "inference_hub.py", "inference_hybrid.py", "base_scorer.py"]


@pytest.mark.parametrize("name", CODE)
def test_v9_code_imports_no_v8_module(name):
    text = (V9 / name).read_text(encoding="utf-8")
    assert not re.search(r"filters[./]human_thriving[./]v8\b", text), (
        f"{name} still references the v8 package path; the real entrypoint would load v8 code"
    )


def test_hub_repo_id_default_is_v9():
    text = (V9 / "inference_hub.py").read_text(encoding="utf-8")
    ids = set(re.findall(r'"jeergrvgreg/([^"]+)"', text))
    assert ids == {"human-thriving-filter-v9"}, ids


def test_config_version_and_scale_factor():
    cfg = yaml.safe_load((V9 / "config.yaml").read_text(encoding="utf-8"))
    assert cfg["filter"]["name"] == "human_thriving"
    assert cfg["filter"]["version"] == "9.0"
    assert cfg["scoring"]["score_scale_factor"] == 1.0


def test_base_scorer_filter_version_is_9():
    """Production stamps this on every scored row; left at 8.0 (as it was on 2026-09-25 until
    verify_filter_package.py caught it), v9's output is labelled as v8's."""
    base = importlib.import_module("filters.human_thriving.v9.base_scorer")
    assert base.BaseHumanThrivingScorer.FILTER_VERSION == "9.0"


def test_op_point_is_4_5_and_normalization_is_anchored_on_it():
    base = importlib.import_module("filters.human_thriving.v9.base_scorer")
    op = min(t for _n, t, _d in base.BaseHumanThrivingScorer.TIER_THRESHOLDS if t > 0)
    assert op == 4.5
    norm = json.loads((V9 / "normalization.json").read_text())
    assert norm["stats"]["raw_min"] == op


def test_normalization_is_v9s_own_not_a_copy_of_v8s():
    """ADR-014: a copied CDF normalizes the new model through the old model's distribution."""
    assert (V9 / "normalization.json").read_bytes() != (V8 / "normalization.json").read_bytes()


def test_probe_is_v8s_probe_and_its_pin_holds():
    """v9 keeps v8's Stage-1 probe on purpose (only the student was retrained), so the
    threshold derived for that probe still applies. Byte-identity makes that explicit."""
    probe = V9 / "probe" / "embedding_probe_e5small.pkl"
    assert probe.read_bytes() == (V8 / "probe" / "embedding_probe_e5small.pkl").read_bytes()
    recorded = (V9 / "probe" / "embedding_probe_e5small.pkl.sha256").read_text().split()[0]
    assert hashlib.sha256(probe.read_bytes()).hexdigest() == recorded
    hybrid = importlib.import_module("filters.human_thriving.v9.inference_hybrid")
    stage1 = hybrid.load_stage1_config(V9 / "config.yaml")
    assert 0.0 < stage1["threshold"] < 4.5
    hybrid.verify_probe_matches_threshold(probe, stage1["probe_sha256"])


def test_calibration_is_v9s_own():
    assert (V9 / "calibration.json").read_bytes() != (V8 / "calibration.json").read_bytes()


def test_adapter_keys_are_old_format_if_weights_present():
    """Hard Constraint: `.lora_A.weight`, never `.lora_A.default.weight`. The weights are
    gitignored, so this runs only where a local copy exists (it must, per deploy guard E)."""
    path = V9 / "model" / "adapter_model.safetensors"
    if not path.exists():
        pytest.skip("no local weights")
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        keys = [k for k in json.loads(f.read(n)) if k != "__metadata__"]
    assert keys and not any(".default." in k for k in keys)
    assert any(k.endswith("score.weight") for k in keys)
