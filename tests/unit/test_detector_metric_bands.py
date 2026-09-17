"""The seed rule is enforced on the ARTIFACT and on the TRAINERS (llm-distillery#158).

`early_stopping=True` lets `random_state` pick the internal validation split, so a head trained
with everything else fixed is one draw: obituary recall at the live 0.85 op-point spans
0.6599-0.8081 across five seeds (`EXP-033`), and v3/v4/v5 finish in three different orders
(`EXP-034`).

Two surfaces, because fixing one leaves the other open:

* `check_detector_metric_bands.py` — a shipped `training_config.json` publishes a BAND, or says
  in the file that it is one draw.
* the trainers themselves — a future edit that goes back to a single hardcoded seed must fail
  here, not in six months when a version comparison reverses again.

No model artifacts are loaded; the pickles are gitignored and these must pass on a bare checkout.
"""

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CHECKER = REPO / "scripts" / "verification" / "check_detector_metric_bands.py"
TRAINERS = (
    REPO / "filters" / "common" / "obituary_detector" / "training" / "train_v1.py",
    REPO / "filters" / "common" / "violence_promotion" / "training" / "train_v1.py",
)
SHARED = REPO / "filters" / "common" / "detector_seeds.py"

BANDED = {
    "seed_set": [42, 7, 13, 101, 2026],
    "artifact_seed": 42,
    "oof_recall_at_0.95": 0.6002,
    "oof_recall_at_0.95_band": {"min": 0.6002, "median": 0.66, "max": 0.71, "spread": 0.1098,
                                "seeds": [42, 7, 13, 101, 2026], "per_seed": {}},
}
DECLARED = {
    "oof_recall_at_0.95": 0.6002,
    "single_seed": {"seed": 42, "issue": "llm-distillery#158", "why": "pre-dates the rule"},
}


def run_checker(root: Path):
    p = subprocess.run([sys.executable, str(CHECKER), "--root", str(root)],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def write_cfg(root: Path, cfg: dict, name: str = "det/v1"):
    d = root / name / "models"
    d.mkdir(parents=True, exist_ok=True)
    (d / "training_config.json").write_text(json.dumps(cfg), encoding="utf-8")
    return d / "training_config.json"


# --------------------------------------------------------------------------- the real tree

def test_the_real_tree_passes():
    rc, out = run_checker(REPO / "filters")
    assert rc == 0, out
    assert "PASS detector-metric-bands" in out


def test_the_real_tree_names_every_single_seed_artifact():
    """⛔ The census is the POINT, not a side effect. A PASS that did not name the artifacts
    publishing one draw would hide exactly what #158 is about.

    ⚠️ Enumerated from DISK, not from a list in this test: `obituary_detector/v{3,4,5}/models/`
    is gitignored, so a bare checkout has fewer sites than this workstation. A hardcoded
    expectation here would be a hand-built population that goes red in CI for being right.
    """
    rc, out = run_checker(REPO / "filters")
    assert rc == 0, out
    sys.path.insert(0, str(CHECKER.parent))
    import importlib.util
    spec = importlib.util.spec_from_file_location("cdmb", CHECKER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    declared = [p for p, _label, cfg in mod.sites(REPO / "filters")
                if isinstance(cfg, dict) and mod.published_metrics(cfg)
                and cfg.get("single_seed") is not None]
    assert declared, "no single-seed artifact on disk — has the tree changed?"
    for path in declared:
        assert str(path.relative_to(REPO)) in out, f"{path} declared but not named:\n{out}"


# --------------------------------------------------------------------------- mutations

def test_a_bare_point_metric_fails(tmp_path):
    write_cfg(tmp_path, {"oof_recall_at_0.95": 0.6002})
    rc, out = run_checker(tmp_path)
    assert rc == 1
    assert "no `seed_set`" in out


def test_a_missing_band_fails_even_with_a_seed_set(tmp_path):
    cfg = dict(BANDED)
    del cfg["oof_recall_at_0.95_band"]
    write_cfg(tmp_path, cfg)
    rc, out = run_checker(tmp_path)
    assert rc == 1
    assert "has no `oof_recall_at_0.95_band`" in out


def test_a_band_over_different_seeds_fails(tmp_path):
    """A band computed over another seed set is not comparable to the file's other bands, and
    reading them side by side is how an ordering gets published backwards (`EXP-034`)."""
    cfg = json.loads(json.dumps(BANDED))
    cfg["oof_recall_at_0.95_band"]["seeds"] = [1, 2, 3]
    write_cfg(tmp_path, cfg)
    rc, out = run_checker(tmp_path)
    assert rc == 1
    assert "declares seed_set" in out


def test_a_banded_config_passes(tmp_path):
    write_cfg(tmp_path, BANDED)
    rc, out = run_checker(tmp_path)
    assert rc == 0, out


def test_a_declared_single_seed_passes(tmp_path):
    write_cfg(tmp_path, DECLARED)
    rc, out = run_checker(tmp_path)
    assert rc == 0, out


def test_a_declaration_without_the_issue_fails(tmp_path):
    cfg = json.loads(json.dumps(DECLARED))
    cfg["single_seed"].pop("issue")
    write_cfg(tmp_path, cfg)
    rc, out = run_checker(tmp_path)
    assert rc == 1
    assert "must name llm-distillery#158" in out


def test_a_declaration_without_a_reason_fails(tmp_path):
    cfg = json.loads(json.dumps(DECLARED))
    cfg["single_seed"]["why"] = "   "
    write_cfg(tmp_path, cfg)
    rc, out = run_checker(tmp_path)
    assert rc == 1
    assert "`single_seed.why`" in out


def test_unrecorded_is_allowed_but_only_as_that_exact_string(tmp_path):
    cfg = json.loads(json.dumps(DECLARED))
    cfg["single_seed"]["seed"] = "UNRECORDED"
    write_cfg(tmp_path, cfg)
    assert run_checker(tmp_path)[0] == 0
    cfg["single_seed"]["seed"] = "unknown"
    write_cfg(tmp_path, cfg)
    rc, out = run_checker(tmp_path)
    assert rc == 1
    assert "UNRECORDED" in out


def test_a_count_is_not_a_metric(tmp_path):
    """⛔ The first version of the checker flagged `test_samples: 190` as an unbanded metric.
    `test_` is an assertion about the SPLIT, not about what the number measures."""
    write_cfg(tmp_path, {"test_samples": 190, "train_samples": 1701})
    rc, out = run_checker(tmp_path)
    assert rc == 0, out


def test_an_empty_root_cannot_verify(tmp_path):
    """A guard that examined nothing is not a passing guard — this repo's signature defect."""
    rc, out = run_checker(tmp_path)
    assert rc == 1
    assert "CANNOT VERIFY" in out


# --------------------------------------------------------------------------- the trainers

@pytest.mark.parametrize("trainer", TRAINERS, ids=lambda p: p.parents[1].name)
def test_the_trainer_computes_a_band_over_the_seed_set(trainer):
    """Reachability, not vocabulary: the call must be IN the module, not merely imported."""
    tree = ast.parse(trainer.read_text(encoding="utf-8"))
    called = {n.func.id for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "oof_by_seed" in called, f"{trainer.name} does not call oof_by_seed"
    assert "metric_bands" in called, f"{trainer.name} does not compute metric bands"


@pytest.mark.parametrize("trainer", TRAINERS, ids=lambda p: p.parents[1].name)
def test_the_trainer_cannot_build_its_own_single_seed_head(trainer):
    """⛔ The defect was `MLPClassifier(..., random_state=SEED)` inline. A trainer that
    reintroduces it — or re-adds a module-level SEED — passes the band test above while going
    straight back to one draw, because both can be true at once."""
    src = trainer.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in {"MLPClassifier", "StratifiedKFold"}:
            pytest.fail(f"{trainer.name} constructs {node.func.id} directly; the head and the "
                        f"fold split belong to detector_seeds.py")
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "SEED":
                    pytest.fail(f"{trainer.name} re-declares a module-level SEED (#158)")


def test_the_shared_module_refuses_a_one_seed_band():
    """A one-seed 'band' is the defect wearing the fix's name."""
    sys.path.insert(0, str(REPO))
    from filters.common.detector_seeds import band
    with pytest.raises(ValueError, match="at least two seeds"):
        band({42: 0.6002})


def test_make_mlp_has_no_default_seed():
    """A default would be the defect: a caller that forgets must fail loudly, not pick 42."""
    tree = ast.parse(SHARED.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "make_mlp")
    assert not fn.args.defaults, "make_mlp must require its seed"
