"""`run_verify_annotations.py`'s extractor — what counts as an annotation.

⚠️ THE SUBJECT HERE IS A DENOMINATOR. The runner's summary line is how anyone
answers "how much of this repo's memory is checked?", and on 2026-08-29 it read
`blocks found: 56` when 46 were annotations: `BLOCK` matches any
`<!-- verify: ... -->`, so every memory file that QUOTES the idiom while explaining
a lesson about it was counted as a block and tallied `skipped`. Ten of them —
eight in `memory/gotcha-log.md`, two in `memory/working-rules.md` — an 18% inflation
of the reported population, in the one report whose job is to state that population.

It was found by writing an eleventh: the count moved when a *prose* sentence was
added, which is the tell. Nothing executable was ever affected (`passed`, `failed`
and `errored` were identical before and after the fix), so no check was silently
disabled — but a report of coverage that counts mentions of coverage is the shape
this repo keeps finding, one layer out each time.
"""

import importlib.util
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUNNER = os.path.join(ROOT, "scripts", "verification", "run_verify_annotations.py")


@pytest.fixture
def runner():
    spec = importlib.util.spec_from_file_location("run_verify_annotations", RUNNER)
    m = importlib.util.module_from_spec(spec)
    sys.modules["run_verify_annotations"] = m
    spec.loader.exec_module(m)
    return m


def test_prose_quoting_the_idiom_is_matched_by_the_regex(runner):
    """The regex itself is unchanged and still matches — the fix is downstream of
    it. Pinning this stops someone 'fixing' the regex instead and quietly losing a
    real annotation whose body happens to be unusual."""
    prose = "A `<!-- verify: -->` comment must probe a stable condition."
    assert runner.BLOCK.findall(prose) == [""]


def test_a_real_annotation_still_extracts(runner):
    body = "<!-- verify: python3 scripts/x.py -->"
    assert runner.BLOCK.findall(body) == ["python3 scripts/x.py "]


def test_an_empty_body_is_what_separates_the_two(runner):
    """The discriminator is the BODY, not the surrounding text — a prose mention
    cannot carry a command, and an annotation cannot be empty and still assert."""
    assert not runner.BLOCK.findall("`<!-- verify: -->`")[0].strip()
    assert runner.BLOCK.findall("<!-- verify: echo hi -->")[0].strip()


def test_the_shipped_memory_files_still_contain_the_prose_mentions(runner):
    """A SEEDED POSITIVE FOR THE REAL CORPUS. If these ever go away the test above
    passes on a fixture while the defect it describes is untestable in place —
    so assert the corpus still has the shape the fix was written for."""
    import glob
    empties = 0
    for f in glob.glob(os.path.join(ROOT, "memory", "*.md")):
        if "project_session_" in f:
            continue
        empties += sum(1 for b in runner.BLOCK.findall(open(f, encoding="utf-8").read())
                       if not b.strip())
    assert empties >= 2, (
        "no memory file quotes the `verify:` idiom any more — this test and the "
        "empty-body branch in run_verify_annotations.py describe a corpus that no "
        "longer exists; re-read the fix before deleting either")


def test_the_runner_reports_them_instead_of_dropping_them(
        runner, capsys, monkeypatch, tmp_path):
    """⛔ NOT A SILENT SKIP. An empty annotation may also be one somebody opened and
    never filled, which is a real defect. The count and the locations print.

    ⚠️ Run against a FIXTURE, not the repo. The first version of this test called
    `runner.main()` over the real corpus and cost the suite 47 seconds — it
    executed every guard in `memory/` a second time, so a slow remote check or a
    genuine failure elsewhere would have decided this test's result. A test whose
    verdict depends on 46 unrelated checks is not testing its own subject.
    """
    body = ("Prose about `<!-- verify: -->` while explaining a rule.\n"
            "<!-- verify: echo PASS; exit 0 -->\n")
    rc, out = _run_fixture(runner, monkeypatch, capsys, tmp_path, body, ("--quiet",))
    assert "1 empty `verify:` comment(s), not executed and not counted below" in out
    assert "FIXTURE.md #1" in out
    assert "blocks found: 1" in out, "the prose mention is still in the denominator"
    assert rc == 0


def test_zero_blocks_still_aborts(runner, capsys, monkeypatch):
    """The pre-existing guarantee, re-pinned because the new `continue` sits above
    `total_blocks += 1`: a corpus of nothing but prose mentions must ABORT, not
    report a clean run over an empty population."""
    monkeypatch.setattr(runner, "docs", lambda _s: ["MEMORY_FIXTURE.md"])
    fixture = os.path.join(ROOT, "MEMORY_FIXTURE.md")
    open(fixture, "w", encoding="utf-8").write("Prose about `<!-- verify: -->` only.\n")
    try:
        monkeypatch.setattr(sys, "argv", ["run_verify_annotations.py", "--quiet"])
        assert runner.main() == 2
        assert "ABORT: 0 annotations found" in capsys.readouterr().out
    finally:
        os.remove(fixture)


# ---------------------------------------------------------------------------
# llm-distillery#137 — the ten reproduced shapes that defeated the classifier.
#
# ⛔ EVERY TEST BELOW SEEDS THE FAILURE IT CLAIMS TO CATCH, and that is the entire
# methodology here. The issue's own note is the reason: the 2026-08-29 change was
# argued partly from "0 of the 33 executable blocks emit that shape today", and
# that zero was VACUOUS — `failed=0`, so no block emitted a FAIL-bearing line at
# all and the instrument could not have said yes. A live run over this repo cannot
# distinguish a fixed classifier from a disabled one; only a fixture that IS
# broken can.
#
# Shapes 1-3 and 7 are FAIL-OPEN: a genuinely failing block reported `pass`, exit
# 0. Shapes 4-6 are SILENT: the block never ran and printed no line. Shapes 8-9
# are over-reports, which are not harmless — a check that cries wolf gets ignored.


def _run_fixture(runner, monkeypatch, capsys, tmp_path, body, extra_argv=()):
    """Run the real runner over one fixture document. Returns (rc, output)."""
    doc = tmp_path / "FIXTURE.md"
    doc.write_text(body, encoding="utf-8")
    monkeypatch.setattr(runner, "ROOT", str(tmp_path))
    monkeypatch.setattr(runner, "docs", lambda _s: ["FIXTURE.md"])
    monkeypatch.setattr(sys, "argv", ["run_verify_annotations.py", *extra_argv])
    rc = runner.main()
    return rc, capsys.readouterr().out


@pytest.mark.parametrize("prefix,name", [
    ("\\xe2\\x9b\\x94 ", "no-entry glyph"),
    ("\\xe2\\x9c\\x97 ", "ballot X"),
    ("- ", "list bullet"),
    ("**", "bold markdown"),
    ("\\xef\\xbb\\xbf", "UTF-8 BOM"),
    ("\\033[31m", "ANSI red"),
])
def test_shape_1_decoration_before_the_verdict_no_longer_hides_it(
        runner, monkeypatch, capsys, tmp_path, prefix, name):
    """A genuinely failing guard, reported `pass`, exit 0 — for six prefixes this
    repo's guards are actually written with."""
    body = f"<!-- verify: printf -- '{prefix}FAIL: 2 rows disagree\\n  uplifting v7\\n'; exit 0 -->\n"
    rc, out = _run_fixture(runner, monkeypatch, capsys, tmp_path, body)
    assert "FAIL " in out, f"{name}: the failure was not reported"
    assert rc == 1


def test_shape_2_a_midline_verdict_on_a_nonlast_line_is_found(
        runner, monkeypatch, capsys, tmp_path):
    """Verdict-then-detail-rows is the emission style the anchor was built for, and
    the retained fallback covered a mid-line verdict only on the LAST line."""
    body = '<!-- verify: echo "prod-filters table: FAIL"; echo "  uplifting v7"; exit 0 -->\n'
    rc, out = _run_fixture(runner, monkeypatch, capsys, tmp_path, body)
    assert "FAIL " in out and rc == 1


def test_shape_3_stderr_is_not_glued_onto_a_newlineless_stdout(
        runner, monkeypatch, capsys, tmp_path):
    """`r.stdout + r.stderr` produced `okFAIL: regressed`, un-anchoring the verdict.
    `check_content_length_populated.sh` writes its failure sentence to stderr."""
    body = "<!-- verify: printf 'ok'; printf 'FAIL: regressed\\nrow1\\n' >&2; exit 0 -->\n"
    rc, out = _run_fixture(runner, monkeypatch, capsys, tmp_path, body)
    assert "FAIL " in out and rc == 1


def test_shape_4_a_remote_word_in_a_COMMENT_no_longer_silences_a_local_check(
        runner, monkeypatch, capsys, tmp_path):
    """The worst of the ten: the block printed NO LINE AT ALL. The identical block
    without the trailing comment reported FAIL."""
    body = ('<!-- verify: echo "FAIL: real breakage"; exit 1 '
            '# baseline measured on b650 -->\n')
    rc, out = _run_fixture(runner, monkeypatch, capsys, tmp_path, body)
    assert "FAIL " in out and rc == 1
    assert "remote=0" in out


def test_shape_4b_a_genuine_remote_command_is_still_remote(
        runner, monkeypatch, capsys, tmp_path):
    """The control for shape 4: stripping comments must not stop real remote checks
    being skipped, or the fix trades a silence for a broken run."""
    body = '<!-- verify: ssh sadalsuud "echo FAIL"; exit 1 -->\n'
    _, out = _run_fixture(runner, monkeypatch, capsys, tmp_path, body)
    assert "remote=1" in out


@pytest.mark.parametrize("cmd", [
    ".venv/bin/python scripts/x.py",
    "pytest tests/unit/test_x.py",
    "scripts/verification/check_x.sh",
    "PYTHONPATH=. .venv/bin/python scripts/x.py",
])
def test_shape_5_delegating_invocations_are_recognised(runner, cmd):
    """Silently downgraded to NO-ASSERTION — never executed. ⚠️ `memory/`'s own
    instruction is to prefer the venv python over `python3`, so following this
    repo's advice DISABLED the annotation."""
    kind, reason = runner.classify(cmd)
    assert kind == "run", f"{cmd!r} classified {kind} ({reason})"


def test_shape_5b_a_bare_value_printer_is_still_noassert(runner):
    """The control for shape 5: a widened DELEGATES must not start calling
    everything runnable, or NO-ASSERTION stops meaning anything."""
    assert runner.classify("wc -l datasets/x.jsonl")[0] == "noassert"


def test_shape_6_an_arrow_inside_the_command_is_refused_not_executed(
        runner, monkeypatch, capsys, tmp_path):
    """`BLOCK` is non-greedy, so a `-->` inside the command severs it: the runner
    executed `echo "count 3 `, which exits 0 and reports pass. Widening the regex
    would swallow the next annotation whole; refusing the fragment is the fix."""
    body = '<!-- verify: echo "count 3 --> expected 5"; echo FAIL; exit 1 -->\n'
    rc, out = _run_fixture(runner, monkeypatch, capsys, tmp_path, body)
    assert "TRUNCATED" in out
    assert "truncated=1" in out
    assert rc == 1


def test_shape_7_no_output_at_all_is_labelled_not_silently_a_pass(
        runner, monkeypatch, capsys, tmp_path):
    """It stays a pass — the exit code is the assertion for scripts that work that
    way — but it must not read like a verdict."""
    body = "<!-- verify: bash -c 'exit 0' # asserts by exit code -->\n"
    rc, out = _run_fixture(runner, monkeypatch, capsys, tmp_path, body)
    assert "[no output — exit code only]" in out
    assert rc == 0


def test_shape_8_cannot_verify_with_a_nonzero_exit_is_not_a_FAIL(
        runner, monkeypatch, capsys, tmp_path):
    """`r.returncode != 0` was tested first, so an unreachable box read as a broken
    invariant. `check_index_budget.py` returns 1 alongside CANNOT VERIFY in five
    branches; `check_content_length_populated.sh` exits 2 on an unreachable host."""
    body = '<!-- verify: echo "CANNOT VERIFY: host unreachable"; exit 2 -->\n'
    rc, out = _run_fixture(runner, monkeypatch, capsys, tmp_path, body)
    assert "CANNOT VERIFY " in out
    assert "  FAIL  " not in out
    assert "errored=1" in out and "failed=0" in out


def test_shape_9_a_real_FAIL_under_a_cannot_verify_line_stays_a_FAIL(
        runner, monkeypatch, capsys, tmp_path):
    """`next()` took the first match of either word, downgrading a real regression
    to 'could not check' — the direction that gets a defect closed unread."""
    body = ('<!-- verify: echo "CANNOT VERIFY: optional probe absent"; '
            'echo "FAIL: 2 rows disagree"; exit 1 -->\n')
    rc, out = _run_fixture(runner, monkeypatch, capsys, tmp_path, body)
    assert "failed=1" in out and "errored=0" in out
    assert rc == 1


def test_the_word_FAIL_in_healthy_prose_is_not_a_verdict(
        runner, monkeypatch, capsys, tmp_path):
    """⛔ THE COST OF FIXING SHAPES 1-3, AND THE REASON THE MATCH IS NOT A BARE
    SUBSTRING. A guard reporting `0 FAILures` or `no FAIL lines found` is healthy;
    calling it broken teaches everyone to ignore the report."""
    body = ('<!-- verify: echo "PASS: 0 FAILures over 660 rows"; '
            'echo "no FAIL lines found"; exit 0 -->\n')
    rc, out = _run_fixture(runner, monkeypatch, capsys, tmp_path, body)
    assert "passed=1" in out and "failed=0" in out
    assert rc == 0


@pytest.mark.parametrize("line,hit", [
    ("FAIL: 2 rows", True),
    ("prod-filters table: FAIL", True),
    ("check X: FAIL.", True),
    ("PASS: 0 FAILures", False),
    ("no FAIL lines found", False),
    ("FAILED to open", False),
])
def test_the_verdict_shapes_are_exactly_three(runner, line, hit):
    """Opens the line, introduces a detail, or closes one. Pinned so a later
    widening has to argue with the false positives it re-admits."""
    assert bool(runner.VERDICT_HIT["FAIL"].search(runner.normalise(line))) is hit


@pytest.mark.parametrize("cmd,truncated", [
    ('echo "count 3 ', True),                      # the real severed fragment
    ("echo 'count 3 ", True),
    ('echo "it\'s fine"; exit 1', False),          # apostrophe INSIDE double quotes
    ("echo \"don't\"; echo \"won't\"", False),
    ('echo "a"; echo "b"', False),
])
def test_truncation_is_detected_by_quote_STATE_not_by_counting(runner, cmd, truncated):
    """⛔ THE FIRST VERSION COUNTED QUOTES and would have refused to run
    `echo "it's fine"` — one apostrophe, odd count, declared severed. A quote inside
    the other kind of quote is not a quote. Caught in self-review, before it could
    silence a healthy annotation, which is the direction that matters here: a false
    TRUNCATED is a check that stops running."""
    assert runner.looks_truncated(cmd) is truncated
