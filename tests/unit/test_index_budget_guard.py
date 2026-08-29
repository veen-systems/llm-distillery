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


# ---------------------------------------------------------------------------
# The ALWAYS-LOADED LAYER (llm-distillery#138).
#
# ⛔ WHAT THIS TARGET EXISTS TO STOP, restated because it is the thing these tests
# have to be able to catch: before 2026-08-29 the guard's two targets were
# `CLAUDE.md` (auto-loaded) and `memory/MEMORY.md` (NOT auto-loaded — reached by a
# pointer row), while 19,488 B that IS auto-loaded — the user auto-memory index —
# belonged to no target. The failure mode is therefore NOT "the number is wrong";
# it is "a member vanished from the sum and the output looked healthy". Every test
# below asserts on the MEMBERSHIP as well as the verdict, and the missing-member
# tests exist so that the guard's own silence has a seeded positive.


@pytest.fixture
def loaded_guard(tmp_path, monkeypatch):
    """The real script, with BOTH members pointed at temp files."""
    spec = importlib.util.spec_from_file_location("check_index_budget_loaded", GUARD)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_index_budget_loaded"] = mod
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "PROJECT", str(tmp_path / "CLAUDE.md"))
    monkeypatch.setattr(mod, "AUTO_MEMORY", str(tmp_path / "auto" / "MEMORY.md"))
    os.makedirs(tmp_path / "auto")
    mod._tmp = tmp_path
    return mod


def _layer(guard, project_size, auto_size):
    """Write both members. A negative size means 'do not create this file'."""
    if project_size >= 0:
        open(guard.PROJECT, "w", encoding="utf-8").write("x" * project_size)
    if auto_size >= 0:
        open(guard.AUTO_MEMORY, "w", encoding="utf-8").write("x" * auto_size)


def test_the_layer_passes_quietly_when_both_members_fit(loaded_guard, capsys):
    _layer(loaded_guard, 20_000, 10_000)
    assert loaded_guard.main(["--target", "loaded"]) == 0
    out = capsys.readouterr().out
    assert "PASS always-loaded layer 30,000 B over 2/2 files" in out
    assert "CLAUDE.md" in out and "auto-memory MEMORY.md" in out


def test_the_verdict_is_the_LAST_line_not_the_first(loaded_guard, capsys):
    """⚠️ NOT COSMETIC. `run_verify_annotations.py` anchors on a line-initial
    FAIL/CANNOT VERIFY for failures but reports the command's LAST line for a
    PASSING block. With the verdict printed first, the verify report showed this
    check's result as `auto-memory MEMORY.md 10,773 B  58 lines` — an attribution
    row standing in for a budget verdict. Observed 2026-08-29 and fixed here."""
    _layer(loaded_guard, 20_000, 10_000)
    loaded_guard.main(["--target", "loaded"])
    out = capsys.readouterr().out.strip().splitlines()
    assert out[-1].startswith("PASS always-loaded layer")
    assert not out[0].startswith(("PASS", "FAIL", "CANNOT VERIFY"))


def test_the_total_governs_even_when_no_single_file_is_large(loaded_guard, capsys):
    """THE OWNER CALL, 2026-08-29. Two files each far under their own ceiling can
    still put the layer over: 30,000 + 30,000 is under `PROJECT_HARD` on one side
    and under `HARD` on the other, and over `LOADED_HARD` together. A per-file
    budget cannot see this state, which is why the total is the governing one."""
    _layer(loaded_guard, 31_000, 30_000)
    assert loaded_guard.main(["--target", "loaded"]) == 1
    out = capsys.readouterr().out.strip().splitlines()
    assert out[-1].startswith("FAIL always-loaded layer 61,000 B")
    assert 31_000 < loaded_guard.PROJECT_HARD and 30_000 < loaded_guard.PROJECT_HARD


def test_the_layer_warns_between_soft_and_hard(loaded_guard, capsys):
    _layer(loaded_guard, loaded_guard.LOADED_SOFT, 100)
    assert loaded_guard.main(["--target", "loaded"]) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert out[-1].startswith("PASS")
    assert "WARN" in out[-1] and "left under the" in out[-1]


def test_soft_leaves_real_runway_not_a_warning_at_the_wall(loaded_guard):
    """SOFT is a runway, not a second ceiling. ~486-864 B/day was measured on
    `CLAUDE.md` alone (#133, H-CX1), so a band narrower than a few thousand bytes
    would fire with no time left to choose what goes — the hard limit with extra
    steps."""
    assert loaded_guard.LOADED_HARD - loaded_guard.LOADED_SOFT >= 4_000


def test_a_missing_member_is_reported_with_its_path_and_never_dropped(loaded_guard, capsys):
    """THE SEEDED POSITIVE FOR THE ORIGINAL DEFECT. A member that is not on disk
    must not simply leave the sum: the count says 1/2, the verdict says the total
    understates the layer, and the exact path searched is printed so the reader can
    see WHICH file was not found."""
    _layer(loaded_guard, 20_000, -1)
    rc = loaded_guard.main(["--target", "loaded"])
    out = capsys.readouterr().out
    assert "1/2 files" in out
    assert "INCOMPLETE" in out and "UNDERSTATES" in out
    assert "NOT PRESENT at " + loaded_guard.AUTO_MEMORY in out
    assert "20,000 B" in out          # the sum is of what was actually read
    assert rc == 0                    # absent is a true state, not a defect


def test_an_empty_member_counts_as_missing(loaded_guard, capsys):
    """A zero-byte file is not a member that fits; it is a member that failed to
    load. Sizing it as 0 would report a healthy 2/2."""
    _layer(loaded_guard, 20_000, 0)
    loaded_guard.main(["--target", "loaded"])
    assert "1/2 files" in capsys.readouterr().out


def test_no_members_at_all_cannot_verify(loaded_guard, capsys):
    """A guard that measured nothing must never read as a pass."""
    _layer(loaded_guard, -1, -1)
    assert loaded_guard.main(["--target", "loaded"]) == 1
    out = capsys.readouterr().out.strip().splitlines()
    assert out[-1].startswith("CANNOT VERIFY")


def test_the_members_table_resolves_paths_lazily(loaded_guard):
    """Same defect as TARGETS: a frozen path makes monkeypatching a silent no-op,
    and the test then believes it redirected a guard that measured the real files."""
    for attr, _label in loaded_guard.LOADED_MEMBERS:
        assert isinstance(attr, str)
        assert getattr(loaded_guard, attr).startswith(str(loaded_guard._tmp))


def test_the_in_repo_index_is_NOT_a_member_of_the_layer(loaded_guard):
    """It is reached by a pointer row, not auto-loaded — established 2026-08-29 by
    reading a live session's context. Adding it back would inflate the layer by a
    file that never arrives, which is #138's own warning in the mirror."""
    attrs = [a for a, _ in loaded_guard.LOADED_MEMBERS]
    assert "INDEX" not in attrs
    assert attrs == ["PROJECT", "AUTO_MEMORY"]


def test_the_auto_memory_path_is_derived_from_root_not_hardcoded(loaded_guard, monkeypatch):
    """The slug is the project path with every non-alphanumeric character replaced
    by `-`. Checked against the 40 directories in ~/.claude/projects on
    2026-08-29, including one with a dot in the path, which is why `/` alone is not
    the rule."""
    monkeypatch.setattr(loaded_guard, "ROOT", "/home/x/repos/.meta/proj-one")
    got = loaded_guard._auto_memory_index()
    assert got.endswith(os.path.join("-home-x-repos--meta-proj-one", "memory", "MEMORY.md"))
    assert "/.claude/projects/" in got.replace(os.sep, "/")


def test_loaded_is_dispatchable_and_listed_in_the_error_message(loaded_guard, capsys):
    """The argument error used to be built by hand as `TARGETS + ['pointers']`,
    which is how a message comes to omit a target the moment one is added."""
    assert "loaded" in loaded_guard._all_targets()
    loaded_guard.main(["--target", "nope"])
    out = capsys.readouterr().out
    assert out.startswith("CANNOT VERIFY")
    assert "loaded" in out and "pointers" in out


def test_the_shipped_layer_obeys_its_own_rule():
    """The REAL two files, not fixtures.

    ⚠️ It skips rather than fails when the auto-memory index is absent, because on
    a clone at another path — or a machine where Claude Code has never run — that
    file genuinely is not in anyone's context. The skip is not a fail-open: the
    tests above pin the reporting of an absent member, and this one still asserts
    the shipped total whenever the member IS there, which is the state on the
    machine that ships it."""
    spec = importlib.util.spec_from_file_location("cib_shipped_layer", GUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not os.path.isfile(mod.AUTO_MEMORY):
        pytest.skip(f"auto-memory index not present at {mod.AUTO_MEMORY}")
    assert mod.main(["--target", "loaded"]) == 0
    total = sum(len(open(getattr(mod, a), "rb").read()) for a, _ in mod.LOADED_MEMBERS)
    assert total < mod.LOADED_HARD
