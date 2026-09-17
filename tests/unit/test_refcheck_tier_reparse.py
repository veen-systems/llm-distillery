"""Guard tests for scripts/analysis/refcheck_tier_reparse.py — llm-distillery#134 step 2.

Why these exist: this script produced the historical half of the drift table in
`docs/decisions/2026-09-17-refcheck-docs-tier.md`, and it shipped with **no test at
all** — a number in a decision record, from an instrument nobody had probed. Round 2 of
the review then found it reproducing, in the companion tool, the very defect the same
commit fixed in the checker (a `0` printed for a tier that was never scanned), plus a
reconciliation it claimed without performing.

⛔ Both tests below are about the instrument's ability to say NO. A re-parser that
cannot fail cannot confirm.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "analysis" / "refcheck_tier_reparse.py"
AUGUST_LOG = (REPO_ROOT / "docs" / "evidence" / "2026-08-28-refcheck-docs"
              / "refcheck_docs_run.log")


def _run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *[str(a) for a in args]],
                          capture_output=True, text=True, cwd=REPO_ROOT)


def test_it_reproduces_the_checkers_own_tier_line():
    """The script and the checker must agree, or one of them is wrong.

    This is the cross-check that makes the historical number trustworthy: the script
    is pointed at a log the checker just wrote, and must land on the line the checker
    printed itself. Anything else means the rule diverged from the one it imports.
    """
    checker = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tests" / "fixtures" / "reference-integrity"
                             / "refcheck.py"), "--docs"],
        capture_output=True, text=True, cwd=REPO_ROOT)
    assert checker.returncode == 0, checker.stderr
    own = {p[0].lower(): int(p[1]) for p in
           (l.split() for l in checker.stdout.splitlines())
           if p[:1] in (["LIVE"], ["FROZEN"]) and len(p) > 1 and p[1].isdigit()}

    log = REPO_ROOT / "tests" / "unit" / "_reparse_tmp.log"
    log.write_text(checker.stdout)
    try:
        res = _run(log)
    finally:
        log.unlink()
    assert res.returncode == 0, res.stderr
    got = {p[0].lower(): int(p[1]) for p in
           (l.split() for l in res.stdout.splitlines())
           if p[:1] in (["LIVE"], ["FROZEN"]) and len(p) > 1 and p[1].isdigit()}
    assert got == own, f"script says {got}, the checker said {own}"


def test_a_tier_that_was_not_scanned_is_not_reported_as_zero(tmp_path):
    """The checker's own rule, applied to the companion tool.

    A `--docs-live` log contains no frozen files, so `FROZEN 0` would be a verdict over
    a population that has none — the zero carrying no information that this whole
    change exists to stop printing.
    """
    checker = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tests" / "fixtures" / "reference-integrity"
                             / "refcheck.py"), "--docs-live"],
        capture_output=True, text=True, cwd=REPO_ROOT)
    log = tmp_path / "live.log"
    log.write_text(checker.stdout)
    res = _run(log)
    assert res.returncode == 0, res.stderr
    assert "FROZEN    not scanned" in res.stdout
    assert "FROZEN       0" not in res.stdout


def test_it_refuses_a_log_it_cannot_reconcile(tmp_path):
    """No independent counter ⇒ no verdict. The first version printed one anyway.

    `reconciles against the log's own header` was printed unconditionally while the
    mismatch check was guarded by `if header and ...`, so a trimmed excerpt, a
    grep-filtered log or upstream's checker got a reconciliation that never ran.
    """
    log = tmp_path / "noheader.log"
    log.write_text("docs scanned: 3 files   flags: --docs   working-tree files: 1\n"
                   "### FINDINGS\n  docs/TODO.md  x/y.py  unresolved\n### RESOLVED\n")
    res = _run(log)
    assert res.returncode != 0
    assert "NO `### FINDINGS (N unique` HEADER" in res.stderr
    assert "reconciles" not in res.stdout


def test_it_refuses_a_log_with_no_flags_line(tmp_path):
    """Without the flags line the scan set is unknown, so no tier count may be printed."""
    log = tmp_path / "noflags.log"
    log.write_text("### FINDINGS (1 unique, 1 occurrences)\n"
                   "  docs/TODO.md  x/y.py  unresolved\n### RESOLVED\n")
    res = _run(log)
    assert res.returncode != 0
    assert "no `flags:` line" in res.stderr


def test_a_mismatched_header_is_refused(tmp_path):
    """The reconciliation must be able to fail, or it confirms nothing."""
    log = tmp_path / "bad.log"
    log.write_text("docs scanned: 3 files   flags: --docs   working-tree files: 1\n"
                   "### FINDINGS (99 unique, 99 occurrences)\n"
                   "  docs/TODO.md  x/y.py  unresolved\n### RESOLVED\n")
    res = _run(log)
    assert res.returncode != 0
    assert "MISMATCH" in res.stderr


def test_the_august_log_still_reparses():
    """The stored log the decision record's historical column comes from."""
    res = _run(AUGUST_LOG)
    assert res.returncode == 0, res.stderr
    assert "reconciles against the log's own header" in res.stdout
    assert "parsed 339 unique findings" in res.stdout
