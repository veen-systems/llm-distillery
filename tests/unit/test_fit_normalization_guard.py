"""The fit guard's DEPLOY PATH, executed end-to-end — not its predicate re-implemented.

⛔ Why this file exists. `tests/unit/test_normalization_invariant.py` checks the same rule
over committed packages, but it REIMPLEMENTS the comparison; nothing executed
`fit_normalization.py`'s own `sys.exit(1)`. The llm-distillery#154 fix was proven by two
hand-run CLI fixtures that lived only in a scratch directory — so the proof of the guard
that actually blocks a deploy could not be re-run by a later session, and a future edit
could break the branch with a green suite. *The verified artifact must be the shipped one.*

The three cases are the three outcomes the guard must distinguish at a 4.5 op-point, which
before #154 it could not — it hard-errored on all three:

  legitimate sparse needle fit   gap 0.007, 0.4% of span   -> written, silent
  sample drawn from ENRICHED     gap 0.294, 13%  of span   -> written, ADVISORY
  output (#205's root cause,
  shallow: NexusMind's
  enrichment bar for v8 is
  raw 4.794)
  population never reaches the   gap 0.700, 28%  of span   -> REFUSED, nothing written
  bar (#205 proper)
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FITTER = REPO_ROOT / "scripts" / "normalization" / "fit_normalization.py"
# op-point 4.5 — the value that made the old absolute bound a density test (#154).
FILTER_DIR = REPO_ROOT / "filters" / "human_thriving" / "v8"


def _fixture(tmp_path: Path, lowest: float, highest: float, n: int = 250) -> Path:
    """A flat filtered_*.jsonl the fitter's local loader accepts, with a PINNED minimum.

    The minimum is placed explicitly rather than drawn, because the quantity under test is
    the minimum itself — leaving it to a random draw would make the assertion depend on the
    seed, which is the defect #154 is about (a verdict decided at the 5th decimal).
    """
    import random

    rng = random.Random(154)
    vals = [lowest] + [rng.uniform(lowest, highest) for _ in range(n - 1)]
    d = tmp_path / f"data_{lowest}"
    d.mkdir()
    (d / "filtered_fixture.jsonl").write_text(
        "\n".join(
            json.dumps({"nexus_mind_attributes": {"human_thriving": {
                "version": "8.0", "weighted_average": v, "raw_weighted_average": v}}})
            for v in vals
        ) + "\n",
        encoding="utf-8",
    )
    return d


def _run(tmp_path: Path, lowest: float, highest: float):
    out = tmp_path / f"out_{lowest}.json"
    proc = subprocess.run(
        [sys.executable, str(FITTER), "--filter", str(FILTER_DIR),
         "--data-dir", str(_fixture(tmp_path, lowest, highest)), "--out", str(out)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
        env={**__import__("os").environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    return proc, out


def test_a_sparse_needle_fit_at_a_4_5_op_point_is_written(tmp_path):
    """llm-distillery#154 itself: the population is filtered AT 4.5, so its minimum is
    always above 4.5 and the old `sample_min > 4.5` rule could not be satisfied by any
    correct fit. Phase E was blocked by this and not by the data."""
    proc, out = _run(tmp_path, 4.5069, 6.22)
    assert proc.returncode == 0, proc.stderr
    assert out.exists(), "a legitimate sparse fit must be WRITTEN"
    assert json.loads(out.read_text())["stats"]["raw_min"] == 4.5
    assert "WARNING" not in proc.stderr, "a 0.4%-of-span gap must not warn"


def test_a_sample_starting_at_the_enrichment_bar_is_written_but_warns(tmp_path):
    """The band the #154 fix opens must not be SILENT. Raising the hard limit to a 0.5 raw
    gap admits everything between 0 and 0.5 at a 4.5 op-point, where the old code errored
    on every gap. A fit whose sample starts at NexusMind's enrichment bar (raw 4.794 for
    v8) has a gap of just 0.294 — it clears the hard limit while missing 13% of the fitted
    span, and that is #205's literal root cause, 'sample drawn from already-filtered
    output'. Delete the advisory and this test goes red."""
    proc, out = _run(tmp_path, 4.794, 6.752)
    assert proc.returncode == 0, proc.stderr
    assert out.exists(), "this shape is under the hard limit and must still be written"
    assert "WARNING" in proc.stderr and "never observed" in proc.stderr, (
        "a 13%-of-span unobserved band must produce an advisory"
    )


def test_a_population_that_never_reaches_the_bar_is_refused(tmp_path):
    """NexusMind#205 proper. The fix must not trade a false block for a missing one."""
    proc, out = _run(tmp_path, 5.2, 7.0)
    assert proc.returncode == 1, "the #205 root-cause shape must HARD-ERROR"
    assert not out.exists(), "nothing may be written on the deploy path"
    assert "MAX_SAMPLE_GAP" in proc.stderr


def test_analysis_only_downgrades_the_refusal_but_still_writes_nothing_deployable(tmp_path):
    """The documented bypass, pinned so it cannot silently become a way to write a package
    file: it warns instead of exiting, and says never to deploy the result."""
    out = tmp_path / "analysis.json"
    proc = subprocess.run(
        [sys.executable, str(FITTER), "--filter", str(FILTER_DIR),
         "--data-dir", str(_fixture(tmp_path, 5.2, 7.0)), "--out", str(out),
         "--analysis-only"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
        env={**__import__("os").environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    assert proc.returncode == 0
    assert "never " in proc.stderr and "deploy" in proc.stderr
