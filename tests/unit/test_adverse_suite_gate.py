"""Gate B-A as an executable gate: the three-valued verdict, and the refusals.

The gate exists because on 2026-09-03 a k=3 mean of 4.400 against a 3.85 bar was reported as
criterion 1 FAILING. The row's own sd is 2.560, so that margin never cleared its band; at k=6
and k=12 the same row passes. These tests pin the behaviour that would have caught it.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from scripts.gate.adverse_suite_gate import (  # noqa: E402
    EXIT_FAIL, EXIT_INDETERMINATE, EXIT_OK, EXIT_PLUMBING, DIMS, judge, weighted_average)

GATE = "scripts/gate/adverse_suite_gate.py"


def row(bar=3.85, assertion=None, rid="r1"):
    r = {"id": rid, "title": "t"}
    if bar is not None:
        r["max_acceptable_wa"] = bar
    if assertion:
        r["assertion"] = assertion
    return r


# ---------- the three-valued verdict ----------

def test_pass_when_below_bar_with_margin_clearing_the_band():
    v, mean, sd, band, margin, kn, rule = judge(row(), [0.9, 0.9, 0.9], t=2.0)
    assert v == "PASS" and margin > band and rule == "raw < 3.85"


def test_fail_when_above_bar_with_margin_clearing_the_band():
    v, *_ = judge(row(), [5.9, 5.9, 6.0], t=2.0)
    assert v == "FAIL"


def test_indeterminate_when_margin_is_inside_the_band():
    """The 2026-09-03 case: mean 4.400 against 3.85, from runs spread 6.1/0.9/6.2."""
    v, mean, sd, band, margin, k_needed, _ = judge(row(), [6.10, 0.90, 6.20], t=2.0)
    assert v == "INDETERMINATE"
    assert round(mean, 3) == 4.4 and margin < band
    assert k_needed and k_needed > 12, "must say a much larger k is required, not k=12"


def test_indeterminate_is_returned_even_when_the_row_would_pass():
    """A row whose mean is BELOW the bar but inside the band is still not certifiable."""
    v, *_ = judge(row(), [0.5, 7.0, 3.0], t=2.0)
    assert v == "INDETERMINATE"


def test_delta_assertion_is_skipped_not_silently_passed():
    v, *_ = judge(row(bar=None, assertion="DELTA, not a band: v8 must not score lower than v7"),
                  [4.1, 4.2, 4.3], t=2.0)
    assert v == "SKIP"


def test_greater_than_assertion_is_judged_in_the_other_direction():
    v, *_ = judge(row(bar=None, assertion="raw_weighted_average > 4.5"), [6.2, 6.3, 6.1], t=2.0)
    assert v == "PASS"
    v, *_ = judge(row(bar=None, assertion="raw_weighted_average > 4.5"), [1.0, 1.1, 0.9], t=2.0)
    assert v == "FAIL"


# ---------- the bar and the band come from the DATA, not from this file ----------

def test_bar_is_read_off_the_row():
    """Same samples, different declared bar, opposite verdict."""
    assert judge(row(bar=3.85), [2.0, 2.0, 2.0], t=2.0)[0] == "PASS"
    assert judge(row(bar=1.00), [2.0, 2.0, 2.0], t=2.0)[0] == "FAIL"


def test_band_scales_with_the_rows_own_spread_not_a_constant():
    tight = judge(row(), [4.40, 4.40, 4.41], t=2.0)
    wide = judge(row(), [6.10, 0.90, 6.20], t=2.0)
    assert tight[0] == "FAIL", "a tight spread just above the bar is a real failure"
    assert wide[0] == "INDETERMINATE", "the same mean with a wide spread is not resolvable"
    assert wide[3] > tight[3], "band must grow with sd"


def test_band_shrinks_as_k_grows():
    three = judge(row(), [6.1, 0.9, 6.2], t=2.0)[3]
    twelve = judge(row(), [6.1, 0.9, 6.2] * 4, t=2.0)[3]
    assert twelve < three


def test_unjudgeable_row_is_fatal_never_a_pass():
    with pytest.raises(SystemExit) as e:
        judge({"id": "x", "title": "t"}, [1.0, 1.0, 1.0], t=2.0)
    assert e.value.code == EXIT_PLUMBING


# ---------- exit codes: a gate that never ran must not look like a gate that failed ----------

def _run(pattern):
    return subprocess.run([sys.executable, GATE, pattern], cwd=REPO, capture_output=True,
                          text=True, env={"PYTHONPATH": ".", "PATH": "/usr/bin:/bin"}).returncode


@pytest.mark.parametrize("pattern,expected", [
    ("docs/evidence/2026-09-03-v8-1-gate/runs/k12_v84_*.jsonl", EXIT_OK),
    ("docs/evidence/2026-09-03-v8-1-gate/runs/k12_v82_*.jsonl", EXIT_FAIL),
    ("docs/evidence/2026-09-03-v8-1-gate/runs/v81b_*.jsonl", EXIT_OK),
    ("docs/evidence/2026-09-01-v8-oracle-choice/runs/ds_*.jsonl", EXIT_INDETERMINATE),
    ("docs/evidence/does-not-exist/*.jsonl", EXIT_PLUMBING),
    ("docs/evidence/2026-09-03-v8-1-gate/runs/k12_v8[24]_1.jsonl", EXIT_PLUMBING),
])
def test_exit_codes_on_real_runs(pattern, expected):
    """⛔ Every code distinct. Plumbing is 3, never 1 — and check it without a pipe."""
    assert _run(pattern) == expected


def test_ragged_k_is_plumbing_not_a_verdict(tmp_path):
    src = REPO / "docs/evidence/2026-09-03-v8-1-gate/runs/k12_v84_1.jsonl"
    rows = [json.loads(l) for l in open(src, encoding="utf-8")]
    d = tmp_path / "r"; d.mkdir()
    (d / "a.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    (d / "b.jsonl").write_text(json.dumps(rows[0]), encoding="utf-8")   # one row only
    assert _run(str(d / "*.jsonl")) == EXIT_PLUMBING


def test_weighted_average_applies_the_gatekeeper_cap():
    low = {d: 9.0 for d in DIMS}
    low["evidence_level"] = 0.0
    assert weighted_average(low) <= 3.0
