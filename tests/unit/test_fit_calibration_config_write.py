"""`fit_calibration.py` must not write `score_scale_factor` into a filter that has no
`normalization.json`.

WHY THIS IS A TEST AND NOT A COMMENT. `score_scale_factor` is superseded by percentile
normalization (ADR-014). A factor != 1.0 on a filter with **no** `normalization.json`
stretches every NORMALIZED score — the quantity that feeds cross-filter ranking and
NexusMind's `pipeline.enrichment.min_score: 4.0` gate. Visibility is decided on the RAW
score (NM#280), so the op-point does not move and **the change has no symptom**.

⚠️ And it is worse than inert-config: NexusMind's `_check_required_artifacts` treats the
mere PRESENCE of `score_scale_factor` in `scoring` as "uses scale factor" and then stops
warning about a missing `normalization.json`. So the write silences the one guard that
would have flagged the absent artifact.

Measured on `human_thriving v8`, 2026-09-04: the script computed **1.3787** — a 1.38×
stretch on a filter with no normalization fitted — and would have written it. It was caught
by hand, which is not a mechanism.

The decision is exercised in all four directions rather than described, because the
alternative proof costs a 32-minute inference run and the ONE thing this repo has learned
repeatedly is that an unexercised branch is indistinguishable from an absent one
(llm-distillery#144).
"""

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load():
    path = REPO_ROOT / "scripts" / "calibration" / "fit_calibration.py"
    spec = importlib.util.spec_from_file_location("fit_calibration_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fit_calibration_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod


fc = _load()


def test_refuses_when_normalization_absent(tmp_path):
    """The default, and the case that matters."""
    write, reason = fc.score_scale_factor_decision(tmp_path, False, False)
    assert write is False
    assert "normalization.json" in reason


def test_writes_when_normalization_present(tmp_path):
    """Unchanged behaviour for every filter that has one — there the factor is inert."""
    (tmp_path / "normalization.json").write_text("{}", encoding="utf-8")
    write, reason = fc.score_scale_factor_decision(tmp_path, False, False)
    assert write is True
    assert "inert" in reason


def test_force_overrides_the_refusal(tmp_path):
    write, reason = fc.score_scale_factor_decision(tmp_path, False, True)
    assert write is True
    assert "force" in reason


def test_no_config_update_wins_over_force(tmp_path):
    """`--no-config-update` is the explicit "don't touch my config" flag; it must not be
    overridable by a flag whose only job is to relax a safety default."""
    (tmp_path / "normalization.json").write_text("{}", encoding="utf-8")
    write, _ = fc.score_scale_factor_decision(tmp_path, True, True)
    assert write is False


def test_the_shipped_v8_package_would_be_refused():
    """The concrete case: v8 has a calibration.json and no normalization.json, so a
    re-run at Phase D without any flag must not write 1.3787 into its config."""
    v8 = REPO_ROOT / "filters" / "human_thriving" / "v8"
    assert (v8 / "calibration.json").exists(), "precondition: v8 is calibrated"
    assert not (v8 / "normalization.json").exists(), (
        "precondition changed: v8 now HAS a normalization.json, so this test no longer "
        "covers the dangerous case — point it at a filter that does not."
    )
    write, _ = fc.score_scale_factor_decision(v8, False, False)
    assert write is False


def test_deployed_filters_with_normalization_are_unaffected():
    """A behaviour change is only acceptable if it does not change behaviour for the
    packages that were already correct. Every deployed filter carrying a
    normalization.json must still get the write."""
    checked = 0
    for norm in sorted(REPO_ROOT.glob("filters/*/v*/normalization.json")):
        write, reason = fc.score_scale_factor_decision(norm.parent, False, False)
        assert write is True, f"{norm.parent} would now be refused"
        assert "inert" in reason
        checked += 1
    # A zero here would make every assertion above vacuous — the shape this repo calls
    # "the instrument could not have said no".
    assert checked >= 3, f"only {checked} filters with normalization.json found"
