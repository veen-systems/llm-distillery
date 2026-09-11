"""refcheck.py's three-outcome exit contract (agent-ready-projects v1.40.0, Step 4).

Added 2026-09-11 by /audit-context. Until that day refcheck.py had NO `sys.exit`
anywhere: it printed its findings and always exited 0, so `refcheck.py && ...`
could never fail. Nothing wired it, so nothing broke -- but a guard that cannot
fire is this repo's signature defect, and the fix needs a test that fails if the
contract is removed again.

The block is READ FROM THE SHIPPED FILE rather than reimplemented here. A test
that re-states the logic tests the restatement; this one breaks if refcheck.py
loses the block, which is the failure being guarded against.

Exit 2 must stay NON-ZERO: a caller written `refcheck.py && ...` keeps its old
meaning, and only one that opts in (`|| [ $? -eq 2 ]`) accepts an undecided run.
"""
import pytest

from pathlib import Path

REFCHECK = Path(__file__).resolve().parents[2] / "tests/fixtures/reference-integrity/refcheck.py"
MARKER = "# --- Exit contract"


def _exit_block() -> str:
    src = REFCHECK.read_text(encoding="utf-8")
    assert MARKER in src, (
        f"{REFCHECK} no longer carries the exit contract. It was added 2026-09-11 "
        "because the script could not fail; removing it restores that."
    )
    return src[src.index(MARKER):]


def _run(findings, sibs, capsys=None):
    """Returns the exit code, or (code, stdout) when capsys is supplied."""
    ns = {"findings": findings, "SIBS": sibs}
    code = None
    try:
        exec(compile(_exit_block(), str(REFCHECK), "exec"), ns)
    except SystemExit as e:
        code = e.code
    else:
        pytest.fail("the exit block returned without calling sys.exit")
    if capsys is None:
        return code
    return code, capsys.readouterr().out


def test_defects_exit_1():
    assert _run([("doc", "frag", "UNRESOLVED")], ["sibling"]) == 1


def test_coverage_incomplete_exit_2():
    """No findings, but rung 4 had no neighbour -- undecided, NOT clean."""
    assert _run([], []) == 2


def test_clean_exit_0():
    assert _run([], ["sibling"]) == 0


def test_incomplete_is_non_zero():
    """`refcheck.py && ...` must not treat an undecided run as success."""
    assert _run([], []) != 0


def test_findings_are_deduplicated(capsys):
    """The verdict counts UNIQUE findings; the script appends one row per occurrence.

    Asserts the PRINTED COUNT, not the exit code. Five duplicates and one finding
    both exit 1, so an exit-code assertion here tests nothing -- proven by
    mutation on 2026-09-11: replacing `len(set(findings))` with `len(findings)`
    left every test in this file green until this one read the number.
    """
    dup = [("doc", "frag", "UNRESOLVED")] * 5
    code, out = _run(dup, ["sibling"], capsys)
    assert code == 1
    assert "1 unique finding(s)" in out, out


def test_defects_win_over_incomplete():
    """A real break must not be downgraded to 'undecided' when siblings are absent."""
    assert _run([("doc", "frag", "UNRESOLVED")], []) == 1
