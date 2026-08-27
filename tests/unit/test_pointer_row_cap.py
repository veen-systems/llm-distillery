"""The pointer-table row cap (llm-distillery#133).

`CLAUDE.md`'s byte budget measures the symptom. What grows is the "Before You
Start" table: a session appends its lesson to the row nearest its topic, an audit
trims the file back to the wall, repeat — ~486 bytes/day measured over 25 commits
(2026-08-16 → 08-26, 35,094 → 39,955). A budget cannot win that race; a per-row
cap makes the table unable to grow at all.

These tests exist because the cap is only worth having if it FIRES. Each one
seeds the failure it claims to catch and asserts a non-zero exit — a guard whose
tests only ever feed it valid input is indistinguishable from one that cannot
fail, which is this repo's signature defect.
"""

import importlib.util
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GUARD = os.path.join(ROOT, "scripts", "verification", "check_index_budget.py")


@pytest.fixture
def guard(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("check_index_budget", GUARD)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_index_budget"] = mod
    spec.loader.exec_module(mod)
    # PROJECT is resolved through globals() at call time, which is what makes this
    # monkeypatch take effect — a table frozen at import made it a silent no-op once.
    monkeypatch.setattr(mod, "PROJECT", str(tmp_path / "CLAUDE.md"))
    mod._tmp = tmp_path
    return mod


def _write(guard, rows, header=None):
    head = guard.POINTER_HEADER if header is None else header
    body = "\n".join(rows)
    (guard._tmp / "CLAUDE.md").write_text(
        f"# Project\n\nsome prose\n\n{head}\n|---|---|\n{body}\n\nafter the table\n",
        encoding="utf-8",
    )


def _row(trigger, pad=0):
    return f"| **{trigger}** | `memory/x.md` — {'x' * pad} |"


def test_passes_when_every_row_is_under_the_cap(guard, monkeypatch):
    # No carve-outs declared, so none can be stale — that arm is tested separately.
    monkeypatch.setattr(guard, "POINTER_CARVEOUTS", {})
    _write(guard, [_row("Doing a thing", 10), _row("Doing another", 20)])
    assert guard._check_pointers()[0] == 0


def test_an_over_long_ordinary_row_fails(guard, monkeypatch):
    """The cap itself. Seeded over, not merely near."""
    monkeypatch.setattr(guard, "POINTER_CARVEOUTS", {})
    _write(guard, [_row("Doing a thing", guard.POINTER_CAP + 50)])
    rc, out = guard._check_pointers()
    assert rc == 1
    assert "over the 250 cap" in "\n".join(out)


def test_a_carveout_row_may_exceed_the_ordinary_cap(guard, monkeypatch):
    """The carve-out is real: a prohibition that must fire without opening the target."""
    frag = next(iter(guard.POINTER_CARVEOUTS))
    monkeypatch.setattr(guard, "POINTER_CARVEOUTS", {frag: "reason"})
    over = guard.POINTER_CAP + 40
    assert over <= guard.POINTER_CARVEOUT_CAP
    _write(guard, [f"| **{frag} etc** | `memory/x.md` — {'x' * over} |"])
    assert guard._check_pointers()[0] == 0


def test_a_carveout_row_still_has_a_ceiling(guard, monkeypatch):
    """An exemption is not a licence. Above the higher cap it fails like any row."""
    frag = next(iter(guard.POINTER_CARVEOUTS))
    monkeypatch.setattr(guard, "POINTER_CARVEOUTS", {frag: "reason"})
    _write(guard, [f"| **{frag} etc** | `memory/x.md` — {'x' * (guard.POINTER_CARVEOUT_CAP + 50)} |"])
    rc, out = guard._check_pointers()
    assert rc == 1
    assert "carve-out" in "\n".join(out)


def test_a_carveout_matching_no_row_fails(guard):
    """A stale exemption is dead weight AND it hides growth: the next reader
    counts four exemptions against three rows and cannot tell which is missing."""
    _write(guard, [_row("Doing a thing", 10)])
    rc, out = guard._check_pointers()
    assert rc == 1
    assert "stale exemption" in "\n".join(out)


def test_too_many_carveouts_fails(guard, monkeypatch):
    """The exemption must not become the rule."""
    rows = [f"| **carve {i}** | `memory/x.md` — short |" for i in range(6)]
    monkeypatch.setattr(guard, "POINTER_CARVEOUTS",
                        {f"carve {i}": "reason" for i in range(6)})
    _write(guard, rows)
    rc, out = guard._check_pointers()
    assert rc == 1
    assert "over the 5 allowed" in "\n".join(out)


def test_a_missing_header_is_cannot_verify_not_a_pass(guard, monkeypatch):
    """⛔ The failure that matters most. Renaming the header would otherwise
    retire the whole check while reporting success — a guard that cannot fire."""
    monkeypatch.setattr(guard, "POINTER_CARVEOUTS", {})
    _write(guard, [_row("Doing a thing", 10)], header="| Some other heading | x |")
    rc, out = guard._check_pointers()
    assert rc == 1
    assert "CANNOT VERIFY" in "\n".join(out)
    assert "examined nothing" in "\n".join(out)


def test_a_table_with_no_rows_is_cannot_verify(guard):
    (guard._tmp / "CLAUDE.md").write_text(
        f"# P\n\n{guard.POINTER_HEADER}\n|---|---|\n\nafter\n", encoding="utf-8")
    rc, out = guard._check_pointers()
    assert rc == 1
    assert "CANNOT VERIFY" in "\n".join(out)


def test_the_delimiter_row_is_not_counted_as_a_row(guard, monkeypatch):
    """⛔ THIS ASSERTION WAS VACUOUS AS FIRST WRITTEN, in a file whose docstring
    says every test seeds the failure it claims. It read

        assert "1 rows" in out or "38 rows" not in out

    and the second disjunct is true whenever the output does not mention 38 — so
    it passed against a mutant that deleted the delimiter-row skip entirely.
    Measured: mutant applied, test green. Now it counts the exact quantity, and
    the same mutant turns it red."""
    monkeypatch.setattr(guard, "POINTER_CARVEOUTS", {})
    _write(guard, [_row("A", 10), _row("B", 10), _row("C", 10)])
    rc, out = guard._check_pointers()
    assert rc == 0, "\n".join(out)
    assert "3 rows" in "\n".join(out), "\n".join(out)


def test_the_real_project_file_passes(guard, monkeypatch):
    """The outcome check: the shipped CLAUDE.md, not a fixture."""
    monkeypatch.setattr(guard, "PROJECT", os.path.join(ROOT, "CLAUDE.md"))
    rc, out = guard._check_pointers()
    assert rc == 0, "\n".join(out)


def test_main_dispatches_the_pointers_target(guard, monkeypatch, capsys):
    monkeypatch.setattr(guard, "PROJECT", os.path.join(ROOT, "CLAUDE.md"))
    assert guard.main(["--target", "pointers"]) == 0
    assert "pointer rows" in capsys.readouterr().out
