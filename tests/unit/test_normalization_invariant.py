"""The normalization fit-convention, as an executable invariant.

ADR-014 says the CDF is fitted from "production MEDIUM+ data" — i.e. articles at
or above the filter's own tier threshold. Every filter followed that convention;
nobody wrote it down; nothing checked it. The two filters that drifted off it are
the only two normalization incidents this project has had:

    foresight v1        raw_min 5.01  drifted HIGH -> NexusMind #205
                        Production articles at raw 4.60 clamped to wavg 0.02 via
                        np.interp's edge behaviour. Guarded after the fact by
                        MAX_NORMALIZATION_RAW_MIN = 4.5 in production_scorer.py,
                        which now rejects the fit at load and falls back to
                        score_scale_factor.

    nature_recovery v2  raw_min 1.50  drifted LOW  -> NexusMind #161
                        Fit-set median 2.19, so doom articles the model had
                        correctly scored 2.2-3.3 mapped to normalized 5.2-8.3 and
                        reached the Recovery lens at up to 8.34/10 "high". Was
                        misdiagnosed as a model failure and patched with a
                        keyword cap that took 14 months to retire.

Both are the same defect — raw_min off the tier threshold — in opposite
directions, and this one assertion catches both. There was a guard for the high
side (added reactively after #205) and none for the low side until 2026-07-14.

Deliberately globs the filesystem rather than reading a hand-maintained list:
tests/unit/test_filter_config_schema.py's ACTIVE_FILTERS is stale (it still names
cultural_discovery v4 and nature_recovery v2 while v5 and v4 are deployed), which
is exactly the rot this test must not inherit.
"""

import ast
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent

# Filters allowed to violate the invariant, each with the incident that made it
# permanent. Every entry must remain a REAL violation — test_no_stale_normalization_exemptions
# fails if someone refits one and forgets to remove its exemption.
EXEMPTIONS = {
    ("foresight", "v1"): (
        "raw_min 5.01 — NexusMind#205. Fit from already-filtered output rather "
        "than a representative production slice. PARKED (#43, merging into "
        "solutions v4) and rejected at load by MAX_NORMALIZATION_RAW_MIN=4.5, so "
        "it cannot reach production. Do not refit; the filter is being retired."
    ),
    ("nature_recovery", "v1"): (
        "raw_min 1.51 — the original NexusMind#161 defect. Superseded by v4 "
        "(deployed 2026-07-10). Package retained for history only."
    ),
    ("nature_recovery", "v2"): (
        "raw_min 1.50 — NexusMind#161. Superseded by v4 but kept as the "
        "rollback fallback, so the file must stay as-is: refitting it would "
        "change what a rollback restores."
    ),
}

# Tolerance for the float compare. The convention is an exact match in practice
# (7/9 files sit at exactly 4.0); this only absorbs float round-tripping.
TOL = 0.01


def _op_point(filter_dir: Path):
    """Lowest non-zero TIER_THRESHOLDS entry — the filter's visibility threshold.

    AST-parsed rather than imported: base_scorer.py pulls in torch transitively.
    Mirrors resolve_op_point() in scripts/normalization/fit_normalization.py.
    """
    path = filter_dir / "base_scorer.py"
    if not path.exists():
        return None
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "TIER_THRESHOLDS":
                try:
                    tiers = ast.literal_eval(node.value)
                    thresholds = [t[1] for t in tiers]
                except (ValueError, SyntaxError, TypeError, KeyError, IndexError):
                    return None
                nonzero = [t for t in thresholds if isinstance(t, (int, float)) and t > 0]
                return min(nonzero) if nonzero else None
    return None


def _fitted_filters():
    """Every filter package carrying a fitted normalization.json."""
    out = []
    for path in sorted(REPO_ROOT.glob("filters/*/v*/normalization.json")):
        out.append((path.parent.parent.name, path.parent.name))
    return out


def _raw_min(filter_name: str, version: str):
    path = REPO_ROOT / "filters" / filter_name / version / "normalization.json"
    return json.loads(path.read_text(encoding="utf-8")).get("stats", {}).get("raw_min")


def test_some_filters_are_fitted():
    """Guards the glob: if it silently matched nothing, every parametrized test
    below would vacuously pass."""
    assert len(_fitted_filters()) >= 5


@pytest.mark.parametrize("filter_name,version", _fitted_filters(),
                         ids=lambda x: str(x))
def test_normalization_fitted_at_the_tier_threshold(filter_name, version):
    """normalization.json's raw_min must equal the filter's tier threshold.

    Fit BELOW it and you map sub-visibility content into the visible band
    (NexusMind#161). Fit ABOVE it and everything between the threshold and
    raw_min clamps to ~0 via np.interp's edge behaviour (NexusMind#205).
    """
    if (filter_name, version) in EXEMPTIONS:
        pytest.skip(f"{filter_name}/{version}: {EXEMPTIONS[(filter_name, version)]}")

    raw_min = _raw_min(filter_name, version)
    op_point = _op_point(REPO_ROOT / "filters" / filter_name / version)

    assert raw_min is not None, f"{filter_name}/{version}: normalization.json has no stats.raw_min"
    assert op_point is not None, (
        f"{filter_name}/{version}: cannot resolve TIER_THRESHOLDS, so the fit "
        f"threshold cannot be validated. If tiers were dropped per ADR-016, this "
        f"invariant needs rewriting against whatever replaced them — do not just "
        f"exempt the filter."
    )
    assert abs(raw_min - op_point) < TOL, (
        f"{filter_name}/{version}: normalization fitted at raw_min={raw_min} but "
        f"the tier threshold is {op_point}. "
        + (
            f"Fitting BELOW the threshold maps sub-visibility articles into the "
            f"visible band — this is NexusMind#161 (v2 fitted at 1.5, doom at raw "
            f"2.2-3.3 surfaced at normalized 5.2-8.3)."
            if raw_min < op_point else
            f"Fitting ABOVE the threshold clamps everything in [{op_point}, "
            f"{raw_min}) to ~0 — this is NexusMind#205 (foresight fitted at 5.01, "
            f"raw 4.60 -> wavg 0.02). Note production_scorer.py rejects raw_min > "
            f"4.5 at load, so such a fit is silently inert."
        )
        + f" Refit with --min-score {op_point} (the fitter now defaults to this)."
    )


def test_no_stale_normalization_exemptions():
    """Every exemption must still describe a real violation. Refit a filter and
    forget to drop its exemption, and the allow-list silently rots — the same
    decay this whole test exists to prevent."""
    stale = []
    for (filter_name, version), reason in EXEMPTIONS.items():
        path = REPO_ROOT / "filters" / filter_name / version / "normalization.json"
        if not path.exists():
            stale.append(f"{filter_name}/{version}: exempted but has no normalization.json")
            continue
        raw_min = _raw_min(filter_name, version)
        op_point = _op_point(REPO_ROOT / "filters" / filter_name / version)
        if raw_min is None or op_point is None:
            continue
        if abs(raw_min - op_point) < TOL:
            stale.append(
                f"{filter_name}/{version}: now conforms (raw_min={raw_min} == "
                f"op_point={op_point}) — remove its EXEMPTIONS entry"
            )
    assert not stale, "Stale normalization exemptions:\n  " + "\n  ".join(stale)


def test_exemptions_name_their_incident():
    """An exemption without a reason is just a silent allowance. Each must cite
    the incident, so the next reader learns why rather than assuming it's fine."""
    for key, reason in EXEMPTIONS.items():
        assert len(reason) > 40, f"{key}: exemption reason too thin to be useful"
        assert "#" in reason, f"{key}: exemption must cite the issue that caused it"
