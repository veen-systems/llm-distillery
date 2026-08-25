"""The memory index's own guard — the SESSION-ENTRY half (llm-distillery#123).

The character ceiling measures the symptom. What grows is the session log: 69% of
`memory/MEMORY.md` by character on 2026-08-25, ~600–900 chars per session against a
fixed 30,000. Hand-trimming recovered ~100 chars per line removed, so it lost the
race roughly 6:1 — and every trim converted a finding into a pointer, which is how
the always-loaded layer stopped being a record.

Owner call 2026-08-25: the index carries the newest four entries and the fifth is
MOVED to `memory/session-log.md`, verbatim. These tests pin the mechanism that says
so, because a rule stated only in prose is one nobody is reminded of.
"""

import importlib.util
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GUARD = os.path.join(ROOT, "scripts", "verification", "check_index_budget.py")


@pytest.fixture
def guard(tmp_path, monkeypatch):
    """The real script, pointed at a temp index."""
    spec = importlib.util.spec_from_file_location("check_index_budget", GUARD)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_index_budget"] = mod
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "INDEX", str(tmp_path / "MEMORY.md"))
    monkeypatch.setattr(mod, "SESSION_LOG", str(tmp_path / "session-log.md"))
    mod._tmp = tmp_path
    return mod


def _index(guard, n_entries, filler=""):
    entries = "\n".join(
        f"- **2026-08-{25 - i:02d} — session {i}** ([session](project_session.md)) — did things."
        for i in range(n_entries)
    )
    body = f"# Memory Index\n\n{entries}\n\n- [Filter status](filter-status.md) — state.\n{filler}\n"
    open(guard.INDEX, "w", encoding="utf-8").write(body)


def test_four_entries_pass_quietly(guard, capsys):
    _index(guard, 4)
    assert guard.main() == 0
    out = capsys.readouterr().out
    assert "4/4 session entries" in out
    assert "WARN" not in out


def test_a_fifth_entry_warns_and_says_MOVE_not_trim(guard, capsys):
    """The wording is the point. 'Trim' is what produced the loss #123 is about."""
    _index(guard, 5)
    open(guard.SESSION_LOG, "w", encoding="utf-8").write("# Session log\n")
    assert guard.main() == 0  # a WARN must not block the person writing the entry
    out = capsys.readouterr().out
    assert "5 session entries, 1 over" in out
    assert "MOVE" in out and "VERBATIM" in out
    assert "do not compress" in out


def test_the_warning_is_louder_when_the_log_does_not_exist(guard, capsys):
    """A move with nowhere to land is a deletion — the exact failure mode."""
    _index(guard, 6)
    assert not os.path.exists(guard.SESSION_LOG)
    assert guard.main() == 0
    out = capsys.readouterr().out
    assert "DOES NOT EXIST" in out


def test_both_index_bullet_shapes_are_counted(guard, capsys):
    """`- **2026-…` and `- [2026-…` are both session entries; a counter that saw
    only one shape would silently under-count and never warn."""
    open(guard.INDEX, "w", encoding="utf-8").write(
        "# Memory Index\n\n"
        "- **2026-08-25 — a** ([session](s.md)) — x.\n"
        "- [2026-08-24](s.md) — b.\n"
        "- **2026-08-23 — c** ([session](s.md)) — x.\n"
        "- [2026-08-22](s.md) — d.\n"
        "- [2026-08-21](s.md) — e.\n"
        "- [Filter status](filter-status.md) — not a session entry.\n"
    )
    open(guard.SESSION_LOG, "w", encoding="utf-8").write("# Session log\n")
    guard.main()
    assert "5 session entries" in capsys.readouterr().out


def test_the_character_ceiling_still_fails(guard, capsys):
    """Presence control: the size guard is untouched by the entry check, and a
    FAIL still carries the entry note rather than replacing it."""
    _index(guard, 4, filler="x" * 31_000)
    assert guard.main() == 1
    out = capsys.readouterr().out
    assert "FAIL" in out and "hard limit" in out
    assert "session entries" in out


def test_the_shipped_index_obeys_its_own_rule(capsys):
    """The real files, not a fixture. A guard nobody's index satisfies is decoration."""
    spec = importlib.util.spec_from_file_location("check_index_budget_real", GUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    raw = open(mod.INDEX, "rb").read()
    assert mod._session_entries(raw) <= mod.MAX_SESSION_ENTRIES
    assert os.path.isfile(mod.SESSION_LOG), "the log the rule moves entries into must exist"
