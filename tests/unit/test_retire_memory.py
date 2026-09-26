"""`scripts/maintenance/retire_memory.py` — the archive pass (agent-ready-projects v1.47.0/v1.48.0).

Each test seeds one defect the 2026-09-26 review found in the first draft:
a lossless check that could not fail, `~~~` fences read as prose, month names matched
inside ordinary words, entries kept under a pinned heading reported as "nothing",
quoted tool output rewritten, and an untracked file breaking `git mv` after references
had already been rewritten.
"""

import datetime
import importlib.util
import os
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "scripts", "maintenance", "retire_memory.py")


@pytest.fixture
def mod(tmp_path):
    spec = importlib.util.spec_from_file_location("retire_memory", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    (tmp_path / "memory").mkdir()
    m.ROOT = str(tmp_path)
    m.LOG = str(tmp_path / "memory" / "gotcha-log.md")
    m.ARCHIVE = str(tmp_path / "memory" / "gotcha-log-archive.md")
    return m


def _write(m, live, archive="# Archive\n"):
    open(m.LOG, "w").write(live)
    open(m.ARCHIVE, "w").write(archive)


def _run(m, *args):
    return m.main(list(args))


LOG = """# Gotcha Log
preamble
## NEW ENTRY (2026-09-20)
body new
## OLD ENTRY (2026-08-10)
body old
### sub of old
## MONTH ENTRY (Mar 2026)
body month
## The unreachable-mechanism catalogue
### PINNED OLD (2026-08-01)
## UNDATED ENTRY
body
"""


def test_moves_old_entries_in_order_and_keeps_the_rest(mod, capsys):
    _write(mod, LOG)
    assert _run(mod, "gotcha", "--before", "2026-09-01", "--apply") == 0
    live, arch = open(mod.LOG).read(), open(mod.ARCHIVE).read()
    assert "OLD ENTRY" not in live and "MONTH ENTRY" not in live and "sub of old" not in live
    assert arch.startswith("# Archive\n")
    assert arch.index("OLD ENTRY") < arch.index("sub of old") < arch.index("MONTH ENTRY")
    for kept in ("NEW ENTRY", "PINNED OLD", "UNDATED ENTRY", "preamble"):
        assert kept in live
    out = capsys.readouterr().out
    assert "kept by rule: 1 dated" in out, "a pinned old entry must be COUNTED, not silent"
    assert "UNDATED, kept" in out


def test_dry_run_writes_nothing(mod):
    _write(mod, LOG)
    assert _run(mod, "gotcha", "--before", "2026-09-01") == 0
    assert open(mod.LOG).read() == LOG


def test_tilde_fence_hides_a_heading(mod):
    body = "## OLD (2026-08-01)\n~~~\n## not a heading (2026-09-20)\n~~~\nend\n"
    _write(mod, "# L\n" + body)
    assert _run(mod, "gotcha", "--before", "2026-09-01", "--apply") == 0
    assert open(mod.ARCHIVE).read().endswith(body), "the fenced block must travel whole"


@pytest.mark.parametrize("heading,expected", [
    ("## X (Feb 2026)", datetime.date(2026, 2, 28)),         # month -> its LAST day
    ("## X (Mar 2026, recurred Apr 2026)", datetime.date(2026, 4, 30)),
    ("## X (September 2026)", datetime.date(2026, 9, 30)),
    ("## Decisions 2026 were made", None),                    # not a month
    ("## Marchand 2026", None),
    ("## bad date 2026-02-30", None),                         # invalid ISO is ignored
])
def test_heading_dates(mod, heading, expected):
    assert mod.heading_date(heading) == expected


def test_month_entry_is_not_retired_early(mod):
    _write(mod, "# L\n## SEP ENTRY (Sep 2026)\nx\n")
    assert _run(mod, "gotcha", "--before", "2026-09-15", "--apply") == 0
    assert "SEP ENTRY" in open(mod.LOG).read()


def test_reconstruction_check_can_fail(mod, monkeypatch, capsys):
    """The first draft compared multisets built from the same blocks: equal by construction.
    Mutate the split so it drops a line — the check must refuse and write nothing."""
    real = mod.split_entries

    def lossy(lines):
        pre, entries = real(lines)
        entries[1] = entries[1][:-1]           # drop the last line of OLD ENTRY
        return pre, entries
    monkeypatch.setattr(mod, "split_entries", lossy)
    _write(mod, LOG)
    assert _run(mod, "gotcha", "--before", "2026-09-01", "--apply") == 1
    assert "CHECK FAILED" in capsys.readouterr().out
    assert open(mod.LOG).read() == LOG


def _repo(tmp_path, mod, files):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)


def test_sessions_rewrite_skips_fences_and_wikilinks(tmp_path, mod):
    s = "project_session_2026_08_01.md"
    _repo(tmp_path, mod, {
        f"memory/{s}": "old session\n",
        "memory/index.md": f"see {s} and [[project_session_2026_08_01]]\n",
        "docs/plan.md": f"see memory/{s}\n```\nAuto-merging memory/{s}\n```\n",
        "docs/evidence/log.md": f"memory/{s}\n",
    })
    assert _run(mod, "sessions", "--before", "2026-09-01", "--apply") == 0
    assert (tmp_path / "memory" / "archive" / s).exists()
    assert (tmp_path / "memory/index.md").read_text() == \
        f"see archive/{s} and [[project_session_2026_08_01]]\n"
    plan = (tmp_path / "docs/plan.md").read_text()
    assert f"see memory/archive/{s}" in plan
    assert f"Auto-merging memory/{s}" in plan, "quoted tool output must stay verbatim"
    assert (tmp_path / "docs/evidence/log.md").read_text() == f"memory/{s}\n"


def test_sessions_refuses_untracked_before_touching_anything(tmp_path, mod):
    s = "project_session_2026_08_01.md"
    _repo(tmp_path, mod, {"memory/index.md": f"see {s}\n"})
    (tmp_path / "memory" / s).write_text("untracked\n")
    assert _run(mod, "sessions", "--before", "2026-09-01", "--apply") == 2
    assert (tmp_path / "memory/index.md").read_text() == f"see {s}\n"
    assert (tmp_path / "memory" / s).exists()


# --- round 2 of the 2026-09-26 review --------------------------------------------


def test_a_moved_file_that_references_another_is_not_resurrected(tmp_path, mod):
    """Round 2 BLOCKER: the edit for a moved file was written to its OLD path after
    `git mv`, recreating it there and leaving the archived copy unrewritten."""
    a, b = "project_session_2026_08_01.md", "project_session_2026_08_02.md"
    _repo(tmp_path, mod, {f"memory/{a}": f"see memory/{b}\n", f"memory/{b}": "b\n"})
    assert _run(mod, "sessions", "--before", "2026-09-01", "--apply") == 0
    assert not (tmp_path / "memory" / a).exists(), "resurrected at the old path"
    assert (tmp_path / "memory/archive" / a).read_text() == f"see memory/archive/{b}\n"


def test_parent_relative_link_is_rewritten(tmp_path, mod):
    s = "project_session_2026_08_01.md"
    _repo(tmp_path, mod, {f"memory/{s}": "x\n", "docs/a.md": f"[s](../memory/{s})\n"})
    assert _run(mod, "sessions", "--before", "2026-09-01", "--apply") == 0
    assert (tmp_path / "docs/a.md").read_text() == f"[s](../memory/archive/{s})\n"


def test_glob_reference_is_flagged_for_a_human(tmp_path, mod, capsys):
    s = "project_session_2026_08_01.md"
    _repo(tmp_path, mod, {f"memory/{s}": "x\n",
                          "memory/log.md": f"`ls memory/project_session_2026_08_0*.md memory/{s}`\n"})
    assert _run(mod, "sessions", "--before", "2026-09-01") == 0
    assert "a glob the rewrite cannot follow" in capsys.readouterr().out


def test_inline_triple_backticks_do_not_open_a_fence(mod):
    """"```inline``` code" opened a fence that never closed and carried the pinned
    catalogue into the archive, with the check passing."""
    _write(mod, "# L\n## NEW (2026-09-20)\n```inline``` code\n"
                "## The unreachable-mechanism catalogue\n## OLD (2026-08-01)\nx\n")
    assert _run(mod, "gotcha", "--before", "2026-09-01", "--apply") == 0
    live = open(mod.LOG).read()
    assert "NEW (2026-09-20)" in live and "catalogue" in live and "OLD" not in live


def test_unclosed_fence_refuses(mod, capsys):
    _write(mod, "# L\n## OLD (2026-08-01)\n```\n## NEW (2026-09-20)\n")
    assert _run(mod, "gotcha", "--before", "2026-09-01", "--apply") == 1
    assert "unclosed" in capsys.readouterr().out
    assert "OLD" in open(mod.LOG).read()
