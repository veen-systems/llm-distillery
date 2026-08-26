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


# ---------------------------------------------------------------------------
# The project-file target (`--target project`), added 2026-08-26 by
# /audit-context. The guard covered memory/MEMORY.md only, while CLAUDE.md sat 45
# BYTES under its 40,000 ceiling with nothing watching it.
# ---------------------------------------------------------------------------


@pytest.fixture
def project_guard(tmp_path, monkeypatch):
    """The real script, pointed at a temp CLAUDE.md."""
    spec = importlib.util.spec_from_file_location("check_index_budget_proj", GUARD)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_index_budget_proj"] = mod
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "PROJECT", str(tmp_path / "CLAUDE.md"))
    mod._tmp = tmp_path
    return mod


def _project(guard, size):
    open(guard.PROJECT, "w", encoding="utf-8").write("# P\n" + "x" * size)


def test_a_small_project_file_passes_quietly(project_guard, capsys):
    _project(project_guard, 1_000)
    assert project_guard.main(["--target", "project"]) == 0
    out = capsys.readouterr().out
    assert "PASS CLAUDE.md" in out and "WARN" not in out


def test_the_project_file_warns_between_soft_and_hard(project_guard, capsys):
    """The soft stage is the whole point: a warning at the wall is the FAIL with
    extra steps (the #123 argument, applied to the other file)."""
    _project(project_guard, 36_000)
    assert project_guard.main(["--target", "project"]) == 0  # WARN must not block
    out = capsys.readouterr().out
    assert "WARN" in out and "40,000 hard limit" in out


def test_the_project_file_fails_over_hard(project_guard, capsys):
    _project(project_guard, 41_000)
    assert project_guard.main(["--target", "project"]) == 1
    out = capsys.readouterr().out
    assert "FAIL" in out
    # The remedy must be the project file's, not the index's. Telling someone to
    # move a session entry out of CLAUDE.md names a thing that is not there.
    assert "Before You Start" in out
    assert "session entries" not in out


def test_the_project_target_has_no_session_entry_check(project_guard, capsys):
    """A dated bullet in CLAUDE.md must not be counted as a session entry: the
    project file legitimately carries dates, and borrowing the index's rule would
    invent a finding on every one."""
    open(project_guard.PROJECT, "w", encoding="utf-8").write(
        "# P\n" + "\n".join(f"- **2026-08-{25 - i:02d} — a dated row**" for i in range(9))
    )
    assert project_guard.main(["--target", "project"]) == 0
    assert "session entries" not in capsys.readouterr().out


def test_an_unknown_target_cannot_verify(project_guard, capsys):
    """Fail closed. A typo'd target must never read as a pass."""
    assert project_guard.main(["--target", "nope"]) == 1
    assert "CANNOT VERIFY" in capsys.readouterr().out


def test_main_ignores_the_host_processes_argv(project_guard, capsys):
    """THE DEFECT THIS FILE CAUGHT ON 2026-08-26. main() read sys.argv directly,
    so an imported caller got pytest's arguments and the guard answered 'unknown
    argument' to five tests that had never passed one."""
    monkey = list(sys.argv)
    sys.argv[:] = ["pytest", "tests/unit/test_index_budget_guard.py", "-q"]
    try:
        _project(project_guard, 1_000)
        assert project_guard.main(["--target", "project"]) == 0
        assert "CANNOT VERIFY" not in capsys.readouterr().out
    finally:
        sys.argv[:] = monkey


def test_the_target_table_resolves_paths_lazily(project_guard):
    """THE SECOND DEFECT. Freezing PROJECT's value into TARGETS at import time made
    monkeypatching it a no-op, so the guard measured the REAL repo file while the
    test believed it had redirected it."""
    attr = project_guard.TARGETS["project"][0]
    assert isinstance(attr, str), "TARGETS must hold an attribute NAME, not a path"
    assert getattr(project_guard, attr) == str(project_guard._tmp / "CLAUDE.md")


def test_the_shipped_project_file_obeys_its_own_rule():
    """The real CLAUDE.md, not a fixture."""
    spec = importlib.util.spec_from_file_location("check_index_budget_real2", GUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert os.path.isfile(mod.PROJECT)
    assert len(open(mod.PROJECT, "rb").read()) < mod.PROJECT_HARD


def test_main_works_when_the_module_is_not_in_sys_modules(tmp_path, monkeypatch):
    """Found by the adversarial lens, 2026-08-26. `sys.modules[__name__]` raises
    KeyError for a caller that execs the module without registering it — which is
    what the two 'shipped file' tests above already do. globals() has no such
    dependency."""
    spec = importlib.util.spec_from_file_location("cib_unregistered", GUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)          # deliberately NOT put in sys.modules
    assert "cib_unregistered" not in sys.modules
    monkeypatch.setattr(mod, "PROJECT", str(tmp_path / "CLAUDE.md"))
    open(mod.PROJECT, "w", encoding="utf-8").write("# P\n" + "x" * 500)
    assert mod.main(["--target", "project"]) == 0
