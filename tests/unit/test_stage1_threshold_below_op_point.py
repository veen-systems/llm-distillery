"""stage1_low rows must never enter a normalization fit (NM#721, 2026-10-24).

A stage1_low row's raw_weighted_average is the e5 probe's estimate, not a model
score. fit_normalization.py keeps it out only because the fit drops rows below the
op-point and every hybrid filter's Stage-1 threshold sits below its op-point. Two
checks hold that:

- the config invariant: each package's RUNTIME Stage-1 threshold is below its op-point
  (`DEFAULT_THRESHOLD` in inference_hybrid.py; human_thriving v8/v9 read config.yaml,
  whose `hybrid_inference.stage1.threshold` is inert everywhere else);
- the fit-time refusal: both loaders raise if a stage1_low row clears min_score.

Measured on NM#721: 0 of 922,542 production stage1_low rows reach an op-point.
"""

import ast
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_fitter():
    path = REPO_ROOT / "scripts" / "normalization" / "fit_normalization.py"
    spec = importlib.util.spec_from_file_location("fit_normalization", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["fit_normalization"] = module
    spec.loader.exec_module(module)
    return module


fitter = _load_fitter()

HYBRID_PACKAGES = sorted(
    p.parent for p in (REPO_ROOT / "filters").glob("*/v*/inference_hybrid.py")
)


def runtime_stage1_threshold(package: Path) -> float:
    """The Stage-1 threshold the package actually runs at. Raises if unresolvable."""
    source = (package / "inference_hybrid.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "DEFAULT_THRESHOLD" for t in node.targets
        ):
            return float(ast.literal_eval(node.value))
    if any(isinstance(n, ast.FunctionDef) and n.name == "load_stage1_config" for n in tree.body):
        config = yaml.safe_load((package / "config.yaml").read_text(encoding="utf-8")) or {}
        return float(config["hybrid_inference"]["stage1"]["threshold"])
    raise AssertionError(
        f"{package}: no module-level DEFAULT_THRESHOLD and no load_stage1_config — "
        f"cannot tell what Stage-1 threshold this package runs at."
    )


def test_hybrid_packages_found():
    # An empty glob would make the parametrized test below vacuous.
    assert len(HYBRID_PACKAGES) >= 10


@pytest.mark.parametrize("package", HYBRID_PACKAGES, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_stage1_threshold_below_op_point(package):
    op_point = fitter._op_point_from_base_scorer(package)
    assert op_point is not None, f"{package}: op-point does not resolve from base_scorer.py"
    threshold = runtime_stage1_threshold(package)
    assert threshold < op_point, (
        f"{package}: Stage-1 threshold {threshold} is not below op-point {op_point}, so "
        f"stage1_low rows (probe estimates) can clear the normalization fit's floor."
    )


def test_runtime_threshold_reads_the_live_source():
    # The two packages that wire config.yaml to the runtime; config is inert elsewhere
    # (nature_recovery v4 config says 3.225, runtime 0.75).
    assert runtime_stage1_threshold(REPO_ROOT / "filters/human_thriving/v9") == 1.75
    assert runtime_stage1_threshold(REPO_ROOT / "filters/nature_recovery/v4") == 0.75


def _row(stage_used, raw, lens="uplifting", version="7.0"):
    return {"nexus_mind_attributes": {lens: {
        "version": version, "weighted_average": raw, "raw_weighted_average": raw,
        "stage_used": stage_used,
    }}}


def _write(tmp_path, rows):
    with open(tmp_path / "filtered_2026-10-24.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


ROWS_OK = [_row("stage2", 5.0), _row("stage2", 6.5), _row("stage1_low", 0.9)]
ROWS_BAD = ROWS_OK + [_row("stage1_low", 4.6)]


class TestLocalLoader:
    def test_below_floor_stage1_low_is_excluded_silently(self, tmp_path):
        _write(tmp_path, ROWS_OK)
        assert fitter.load_weighted_averages_local(tmp_path, "uplifting", 4.5) == [5.0, 6.5]

    def test_stage1_low_above_floor_raises(self, tmp_path):
        _write(tmp_path, ROWS_BAD)
        with pytest.raises(fitter.Stage1LowInFitError, match="1 stage_used=stage1_low"):
            fitter.load_weighted_averages_local(tmp_path, "uplifting", 4.5)


class TestSshLoader:
    """Runs the real embedded remote script locally in place of scp/ssh."""

    @pytest.fixture
    def fake_ssh(self, monkeypatch, tmp_path):
        staged = {}
        real_run = subprocess.run  # fitter.subprocess IS this module; patching it patches us

        def run(args, **kwargs):
            if args[0] == "scp":
                staged["script"] = tmp_path / "remote_script.py"
                shutil.copy(args[1], staged["script"])
                return subprocess.CompletedProcess(args, 0, "", "")
            if args[0] == "ssh" and args[2] == "python3":
                return real_run(
                    [sys.executable, str(staged["script"]), *args[4:]],
                    capture_output=True, text=True,
                )
            return subprocess.CompletedProcess(args, 0, "", "")  # remote rm

        monkeypatch.setattr(fitter.subprocess, "run", run)

    def test_below_floor_stage1_low_is_excluded_silently(self, tmp_path, fake_ssh):
        _write(tmp_path, ROWS_OK)
        got = fitter.load_weighted_averages_ssh("host", str(tmp_path), "uplifting", 4.5)
        assert got == [5.0, 6.5]

    def test_stage1_low_above_floor_raises(self, tmp_path, fake_ssh):
        _write(tmp_path, ROWS_BAD)
        with pytest.raises(fitter.Stage1LowInFitError, match="1 stage_used=stage1_low"):
            fitter.load_weighted_averages_ssh("host", str(tmp_path), "uplifting", 4.5)
