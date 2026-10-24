"""stage1_low rows must never enter a normalization fit (NM#721, 2026-10-24).

A stage1_low row's raw_weighted_average is the e5 probe's estimate, not a model
score. fit_normalization.py keeps it out only because the fit drops rows below the
op-point and every hybrid filter's Stage-1 threshold sits below its op-point. Two
checks hold that:

- the config invariant: each package's RUNTIME Stage-1 threshold is below its op-point
  (`DEFAULT_THRESHOLD` in inference_hybrid.py; human_thriving v8/v9 read config.yaml,
  whose `hybrid_inference.stage1.threshold` is inert everywhere else);
- the fit-time refusal: both loaders raise if a stage1_low row clears min_score at
  the op-point (below it, on an analysis fit, they exclude and warn).

The production measurement is cited once, in fit_normalization._check_stage_used.
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
    ctor_default = _init_threshold_default(package, tree)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "DEFAULT_THRESHOLD" for t in node.targets
        ):
            # A module constant the constructor does not default to is not the runtime value.
            assert isinstance(ctor_default, ast.Name) and ctor_default.id == "DEFAULT_THRESHOLD", (
                f"{package}: __init__'s threshold default is not DEFAULT_THRESHOLD"
            )
            return float(ast.literal_eval(node.value))
    if any(isinstance(n, ast.FunctionDef) and n.name == "load_stage1_config" for n in tree.body):
        assert isinstance(ctor_default, ast.Constant) and ctor_default.value is None, (
            f"{package}: config-wired package, but __init__'s threshold default is not None"
        )
        config = yaml.safe_load((package / "config.yaml").read_text(encoding="utf-8")) or {}
        return float(config["hybrid_inference"]["stage1"]["threshold"])
    raise AssertionError(
        f"{package}: no module-level DEFAULT_THRESHOLD and no load_stage1_config — "
        f"cannot tell what Stage-1 threshold this package runs at."
    )


def _init_threshold_default(package: Path, tree: ast.Module):
    """The default of the `threshold` parameter of the scorer class's __init__."""
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        for fn in cls.body:
            if isinstance(fn, ast.FunctionDef) and fn.name == "__init__":
                args = fn.args.args[-len(fn.args.defaults):] if fn.args.defaults else []
                for arg, default in zip(args, fn.args.defaults):
                    if arg.arg == "threshold":
                        return default
    raise AssertionError(f"{package}: no __init__ with a defaulted `threshold` parameter")


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
ROWS_UNKNOWN = ROWS_OK + [_row("Stage1_Low", 6.0)]


class TestLocalLoader:
    def test_below_floor_stage1_low_is_excluded_silently(self, tmp_path):
        _write(tmp_path, ROWS_OK)
        assert fitter.load_weighted_averages_local(tmp_path, "uplifting", 4.5) == [5.0, 6.5]

    def test_stage1_low_above_floor_raises(self, tmp_path):
        _write(tmp_path, ROWS_BAD)
        with pytest.raises(fitter.Stage1LowInFitError, match="1 stage_used=stage1_low"):
            fitter.load_weighted_averages_local(tmp_path, "uplifting", 4.5)

    def test_analysis_fit_below_op_point_excludes_probe_rows(self, tmp_path):
        _write(tmp_path, ROWS_OK)
        got = fitter.load_weighted_averages_local(
            tmp_path, "uplifting", 0.5, refuse_stage1_low=False,
        )
        assert got == [5.0, 6.5]

    def test_unknown_stage_used_raises_even_on_analysis_fit(self, tmp_path):
        _write(tmp_path, ROWS_UNKNOWN)
        with pytest.raises(fitter.Stage1LowInFitError, match="outside"):
            fitter.load_weighted_averages_local(
                tmp_path, "uplifting", 4.5, refuse_stage1_low=False,
            )


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

    def test_analysis_fit_below_op_point_excludes_probe_rows(self, tmp_path, fake_ssh):
        _write(tmp_path, ROWS_OK)
        got = fitter.load_weighted_averages_ssh(
            "host", str(tmp_path), "uplifting", 0.5, refuse_stage1_low=False,
        )
        assert got == [5.0, 6.5]

    def test_unknown_stage_used_raises(self, tmp_path, fake_ssh):
        _write(tmp_path, ROWS_UNKNOWN)
        with pytest.raises(fitter.Stage1LowInFitError, match="outside"):
            fitter.load_weighted_averages_ssh("host", str(tmp_path), "uplifting", 4.5)

    def test_missing_meta_line_raises(self, monkeypatch):
        def run(args, **kwargs):  # a remote that prints nothing at all
            return subprocess.CompletedProcess(args, 0, "", "")

        monkeypatch.setattr(fitter.subprocess, "run", run)
        with pytest.raises(RuntimeError, match="no META line"):
            fitter.load_weighted_averages_ssh("host", "/nowhere", "uplifting", 4.5)


class TestCliWiring:
    """main() decides refuse vs exclude from min_score vs the op-point; run the real CLI."""

    FITTER = REPO_ROOT / "scripts" / "normalization" / "fit_normalization.py"
    FILTER_DIR = REPO_ROOT / "filters" / "human_thriving" / "v8"  # op-point 4.5

    def _run(self, tmp_path, rows, *extra):
        d = tmp_path / "data"
        d.mkdir()
        _write(d, rows)
        return subprocess.run(
            [sys.executable, str(self.FITTER), "--filter", str(self.FILTER_DIR),
             "--data-dir", str(d), "--out", str(tmp_path / "out.json"), *extra],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
            env={**__import__("os").environ, "PYTHONPATH": str(REPO_ROOT)},
        )

    def test_deploy_path_refuses_a_stage1_low_row_at_the_op_point(self, tmp_path):
        rows = [_row("stage2", 4.6 + i / 100, "human_thriving", "8.0") for i in range(250)]
        rows.append(_row("stage1_low", 4.7, "human_thriving", "8.0"))
        proc = self._run(tmp_path, rows)
        assert proc.returncode != 0
        assert "Stage1LowInFitError" in proc.stderr
        assert not (tmp_path / "out.json").exists()

    def test_analysis_fit_below_op_point_excludes_and_warns(self, tmp_path):
        rows = [_row("stage2", 1.0 + i / 100, "human_thriving", "8.0") for i in range(250)]
        rows.append(_row("stage1_low", 1.5, "human_thriving", "8.0"))
        proc = self._run(tmp_path, rows, "--min-score", "1.0", "--allow-below-op-point",
                         "--analysis-only")
        assert "Stage1LowInFitError" not in proc.stderr, proc.stderr
        assert "Excluded 1 stage1_low rows" in proc.stderr
