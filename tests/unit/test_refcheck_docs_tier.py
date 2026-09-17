"""Guard tests for refcheck.py's docs/ TIER — llm-distillery#134 step 2.

Why these exist: the tier decides which documents the reference checker even OPENS,
and a scan-set defect is invisible in the one place people look. A narrowed scan set
reports FEWER findings, which reads exactly like a repo that got cleaner. Both
widenings of this instrument (2026-08-16 to memory/*.md, 2026-08-28 to docs/) followed
a clean-but-narrow result that nobody doubted, and each found dozens of real defects.

So no assertion here rests on a bare absence. Where a test asserts a fragment is NOT
reported, the fragment is unresolvable BY CONSTRUCTION and the same run is asserted to
report it under the other flag — absence and presence are checked as a pair, in the two
runs that must disagree. What is asserted positively is what was opened, which tier it
landed in, and that an untiered directory stops the run instead of picking a side.
The seed harness (tests/fixtures/reference-integrity/run.sh) cannot cover any of this —
it sets SEED, which replaces the scan set with one file by design.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REFCHECK = REPO_ROOT / "tests" / "fixtures" / "reference-integrity" / "refcheck.py"

# Each seeded document carries a reference that resolves NOWHERE, so its appearance in
# the findings section is proof the file was opened. Absence is proof it was not — but
# only because the reference is unresolvable by construction; a resolvable one would be
# silent for two different reasons and could not tell them apart.
LIVE_DOC = ("docs/adr/001-seed.md", "seed_live_reference_xyz.py")
FROZEN_DOC = ("docs/evidence/2026-01-01-seed/README.md", "seed_frozen_reference_xyz.py")
ROOT_DOC = ("docs/SEED_OVERVIEW.md", "seed_root_reference_xyz.py")


def _make_tree(tmp_path, extra=()):
    """A minimal repo refcheck can run against. HOME is redirected in _run()."""
    for rel in ("CLAUDE.md", "memory/MEMORY.md", "memory/gotcha-log.md"):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("seed\n")
    for rel, frag in (LIVE_DOC, FROZEN_DOC, ROOT_DOC) + tuple(extra):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"A reference to `{frag}` that resolves nowhere.\n")
    return tmp_path


def _run(tmp_path, *flags):
    """Run the checker against the fixture tree, isolated from the real machine.

    HOME is redirected at the tmp tree on purpose: the user-level auto-memory index is
    an ABSOLUTE path in refcheck.py, so a real HOME would drag this machine's own
    memory index into every fixture run and make the finding counts depend on it.
    """
    return subprocess.run(
        [sys.executable, str(REFCHECK), *flags],
        capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", "REFCHECK_ROOT": str(tmp_path),
             "HOME": str(tmp_path)},
    )


def _findings(out):
    return out.split("### FINDINGS")[1].split("### RESOLVED")[0]


def _tier_line(out, tier):
    """The tier's DATA line. Must not match prose that happens to start with the word.

    The report's closing paragraph used to begin "LIVE is the promotion candidate",
    which this matched — the parser then raised instead of asserting, which is luck.
    Fixed at the source too; the second field test is the belt.
    """
    for line in out.splitlines():
        parts = line.split()
        if parts[:1] == [tier] and (parts[1:2] == ["not"] or parts[1].isdigit()):
            return line
    return ""


def test_default_run_opens_no_docs_file(tmp_path):
    """The default scan set still excludes docs/ — #134 step 2 decided NOT to promote.

    Asserted on all three tiers at once: a promotion that lands by accident (a tier
    dict typo, a flag default flipped) shows up here before it shows up as 200+ extra
    findings in an audit nobody can read.
    """
    res = _run(_make_tree(tmp_path))
    assert res.returncode == 0, res.stderr
    for _rel, frag in (LIVE_DOC, FROZEN_DOC, ROOT_DOC):
        assert frag not in res.stdout
    assert "FINDINGS BY TIER" not in res.stdout, (
        "a tier verdict over a population containing no docs is a zero that carries "
        "no information")


def test_docs_live_opens_live_tier_only(tmp_path):
    res = _run(_make_tree(tmp_path), "--docs-live")
    assert res.returncode == 0, res.stderr
    f = _findings(res.stdout)
    assert LIVE_DOC[1] in f
    assert ROOT_DOC[1] in f, "a file at docs/ top level is LIVE (tier key '<root>')"
    assert FROZEN_DOC[1] not in f, "frozen records are correct as history (#123)"


def test_docs_frozen_opens_frozen_tier_only(tmp_path):
    res = _run(_make_tree(tmp_path), "--docs-frozen")
    assert res.returncode == 0, res.stderr
    f = _findings(res.stdout)
    assert FROZEN_DOC[1] in f
    assert LIVE_DOC[1] not in f
    assert ROOT_DOC[1] not in f


def test_bare_docs_still_means_all_of_docs(tmp_path):
    """`--docs` must keep meaning EVERY docs file.

    Every number on record for this flag was measured with it, across GitHub issue
    #134's comments, the step-1 evidence README and `docs/TODO.md`. Narrowing it to the
    live tier would make those readings wrong retroactively, in documents that cannot
    know it happened. ⚠️ The figures themselves are deliberately NOT restated here: a
    docstring listing measurements the test does not exercise is a hand-maintained copy
    wearing a test's authority.
    """
    res = _run(_make_tree(tmp_path), "--docs")
    assert res.returncode == 0, res.stderr
    f = _findings(res.stdout)
    for _rel, frag in (LIVE_DOC, FROZEN_DOC, ROOT_DOC):
        assert frag in f


def test_tier_counts_sum_to_the_docs_findings(tmp_path):
    """The printed split must be attribution, not two independent counts.

    Buckets that sum to the total are guaranteed by construction, so this checks the
    opposite direction as well: each tier is run SEPARATELY and must reproduce its own
    line from the combined run.
    """
    # ⛔ A CLEAN FILE IN EACH TIER, so files-scanned and files-with-findings differ.
    # Without it every fixture file had a finding, the two counts were equal, and a
    # mutant printing the scanned count in the hit column SURVIVED — which is exactly
    # the misread that put "212 findings over 103 files" (really 53) in the first draft of
    # the decision record.
    tree = _make_tree(tmp_path, extra=[])
    for rel in ("docs/adr/002-clean.md", "docs/evidence/2026-01-01-clean/README.md"):
        (tree / rel).parent.mkdir(parents=True, exist_ok=True)
        (tree / rel).write_text("No path references at all.\n")
    both = _run(tree, "--docs").stdout
    live_only = _run(tree, "--docs-live").stdout
    frozen_only = _run(tree, "--docs-frozen").stdout

    def count(out, tier):
        # "LIVE     274 unique in   65 of  120 scanned file(s)   <root>, adr, ..."
        parts = _tier_line(out, tier).split()
        return int(parts[1]), int(parts[4]), int(parts[6])   # findings, hit, scanned

    live = count(both, "LIVE")
    frozen = count(both, "FROZEN")
    assert live == count(live_only, "LIVE")
    assert frozen == count(frozen_only, "FROZEN")
    # findings, files-with-findings, files-scanned — the clean file makes the last two
    # differ, so a mutant that prints one in the other's column cannot survive.
    assert live == (2, 2, 3) and frozen == (1, 1, 2)
    # the tier NOT in scope is unmeasured, not zero — see its own test


def test_untiered_docs_directory_stops_the_run(tmp_path):
    """An unclassified docs/ subdirectory must RAISE, never default into a tier.

    Defaulting to live puts findings in the default set the day promotion happens;
    defaulting to frozen hides them forever. Neither reads as a decision anyone took,
    and a run that cannot say what its scan set excludes must not print a number.
    """
    tree = _make_tree(tmp_path, extra=[("docs/newthing/x.md", "seed_untiered_xyz.py")])
    res = _run(tree, "--docs-live")
    assert res.returncode != 0
    assert "docs/newthing/ has no tier" in res.stderr
    assert "FINDINGS" not in res.stdout, "no number may be printed for an undefined scan set"
    # and it must not fire where docs are out of scope: the default run makes no claim
    # about a directory it never opens.
    assert _run(tree).returncode == 0


@pytest.mark.parametrize("bad", [
    "--doc", "--docs-frozn",        # typos
    "--sibling-root",               # the FRAMEWORK checker's flag; this fork is a
    "-docs", "-h",                  #   different program and takes neither it nor
    "CLAUDE.md", ".",               #   positional arguments — and BOTH halves of the
    "\u2014docs",                    #   copied command must fail, not just the flag half
])
def test_an_unrecognised_argument_stops_the_run(tmp_path, bad):
    """Anything not a known flag must stop the run, not scan the default set silently.

    ⛔ "Unrecognised" is not "starts with --". The first version checked only `--`
    tokens while its own error text claimed "there are no positional arguments", so
    `refcheck.py . CLAUDE.md memory/MEMORY.md` — the /audit-context command with its one
    flag dropped — ran to exit 0 and printed the full default report. That is precisely
    the "small, reassuring findings count" the guard was written against. `-docs`, `-h`
    and an em-dash `--docs` did the same, and em dashes are everywhere in this prose.
    """
    res = _run(_make_tree(tmp_path), bad)
    assert res.returncode != 0, f"{bad!r} ran"
    assert "unrecognised argument" in res.stderr
    assert "FINDINGS" not in res.stdout, f"{bad!r} produced a findings section"


@pytest.mark.parametrize("rel,tier", [
    # LIVE by directory
    ("docs/adr/001-x.md", "live"), ("docs/agents/x.md", "live"),
    ("docs/templates/ADR-TEMPLATE.md", "live"), ("docs/SEED_ROOT.md", "live"),
    # FROZEN dirs: dated => frozen, and the date may be in the file OR the directory
    ("docs/evidence/2026-01-01-x/README.md", "frozen"),
    ("docs/decisions/2026-01-01-x.md", "frozen"),
    ("docs/reports/x_2025-11-17.md", "frozen"),
    ("docs/experiments/benchmark-2026-03-07.md", "frozen"),
    # _archive is frozen BY DEFINITION, dated or not
    ("docs/_archive/guides/x.md", "frozen"),
    # ... and an undated file in a frozen dir is an index or a running history
    ("docs/decisions/framework-adoption-history.md", "live"),
    ("docs/evidence/README.md", "live"),
])
def test_tier_membership_is_the_decided_one(tmp_path, rel, tier):
    """The #134 step-2 decision, asserted by RUNNING the checker, not by grepping it.

    ⛔ The first version of this test did `src.split("DOCS_TIER = {")[1]` and matched
    text, while its own docstring claimed it asserted "against the code". Three
    behaviour-changing mutants survived it, found by /review-changes' adversarial lens:
    a DUPLICATE dict key overriding the tier (the original text still present, so the
    grep passed while `evidence` was live at runtime), a tier added as a COMMENT inside
    the dict, and an invalid tier VALUE that turns the designed SystemExit into a
    KeyError. A name is an assertion, and that one was lying.

    `templates` is LIVE deliberately: a template is maintained, and its non-resolving
    paths are the `<!-- placeholder -->` marker's job, not a reason to stop opening it.
    """
    tree = _make_tree(tmp_path, extra=[(rel, "seed_tier_probe_xyz.py")])
    shows = {t: "seed_tier_probe_xyz.py" in _findings(_run(tree, f"--docs-{t}").stdout)
             for t in ("live", "frozen")}
    assert shows[tier] and not shows["live" if tier == "frozen" else "frozen"], (
        f"{rel} behaves as {[t for t, v in shows.items() if v] or 'neither tier'}, "
        f"not {tier}")


def test_every_docs_subdirectory_is_tiered():
    """The real tree: a new docs/ subdirectory must be classified, or the run dies.

    Asserted by RUNNING both tier flags over the repo — which is what a `KeyError`, a
    commented-out entry or an unhandled directory actually produces. A source grep
    passed on all three.

    ⚠️ This test reads the LIVE repo tree, so it is order-dependent on anything that
    transiently creates `docs/<x>/*.md` — including a mutation run in the same checkout.
    That is not a flaw to paper over: a transient untiered directory is exactly what it
    is for, and it caught one during this change's own review.
    """
    for flag in ("--docs-live", "--docs-frozen"):
        res = _run(REPO_ROOT, flag)
        assert res.returncode == 0, (
            f"{flag} over the real tree failed:\n{res.stderr[-800:]}")
        assert "FINDINGS BY TIER" in res.stdout


def test_a_routed_frozen_dir_file_is_live(tmp_path):
    """A frozen DIRECTORY must not freeze a file the always-loaded layer routes into.

    This is the defect the directory-only rule shipped with, and the whole reason the
    tier is three tests instead of one: `docs/decisions/framework-adoption-history.md`
    is cited twice from `CLAUDE.md`, was edited the same day, and carries the largest
    finding count of any single frozen file — and the first rule declared it "frozen,
    never to be edited to satisfy this checker".
    """
    rel, frag = "docs/decisions/2026-01-01-routed.md", "seed_routed_reference_xyz.py"
    tree = _make_tree(tmp_path, extra=[(rel, frag)])
    # unrouted: dated + in a frozen dir => frozen
    assert frag not in _findings(_run(tree, "--docs-live").stdout)
    assert frag in _findings(_run(tree, "--docs-frozen").stdout)
    # now route an agent into it from the always-loaded layer
    (tree / "CLAUDE.md").write_text(f"See `{rel}` for the procedure.\n")
    assert frag in _findings(_run(tree, "--docs-live").stdout), (
        "a file CLAUDE.md routes into must be LIVE whatever directory it sits in")
    assert frag not in _findings(_run(tree, "--docs-frozen").stdout)


def test_an_undated_file_in_a_frozen_dir_is_live(tmp_path):
    """An undated file in a dated directory is an index or a running history.

    `docs/decisions/README.md` and `docs/evidence/README.md` are indexes; freezing them
    by directory put the sibling of the change's own headline decay case (an index
    pointing at files that do not exist) in the tier that may never be fixed.
    """
    dated, undated = "docs/evidence/2026-01-01-x/README.md", "docs/evidence/README.md"
    tree = _make_tree(tmp_path, extra=[(dated, "seed_dated_xyz.py"),
                                       (undated, "seed_undated_xyz.py")])
    live = _findings(_run(tree, "--docs-live").stdout)
    frozen = _findings(_run(tree, "--docs-frozen").stdout)
    assert "seed_undated_xyz.py" in live and "seed_undated_xyz.py" not in frozen
    assert "seed_dated_xyz.py" in frozen and "seed_dated_xyz.py" not in live


def test_archive_is_frozen_even_undated(tmp_path):
    """`_archive/` is frozen BY DEFINITION, so the undated rule must not unfreeze it."""
    rel, frag = "docs/_archive/guides/old.md", "seed_archive_xyz.py"
    tree = _make_tree(tmp_path, extra=[(rel, frag)])
    assert frag in _findings(_run(tree, "--docs-frozen").stdout)
    assert frag not in _findings(_run(tree, "--docs-live").stdout)


def test_a_tier_not_in_scope_prints_not_scanned_never_zero(tmp_path):
    """A tier that was not scanned is UNMEASURED, and 0 is a different claim.

    The first draft printed `FROZEN 0 unique in 0 file(s)` under `--docs-live` — a tier
    verdict over a population containing none of that tier — in the two runs this change
    exists to add, with a test asserting the zero was correct.
    """
    tree = _make_tree(tmp_path)
    assert "FROZEN  not scanned" in _run(tree, "--docs-live").stdout
    assert "LIVE    not scanned" in _run(tree, "--docs-frozen").stdout
    both = _run(tree, "--docs").stdout
    assert "not scanned" not in both


def test_routing_surface_must_be_readable(tmp_path):
    """A missing routing surface must stop the run, not silently narrow the live tier.

    If `CLAUDE.md` cannot be read the override cannot fire, so files that should be live
    are tiered frozen and never scanned — a narrowing that reports FEWER findings, which
    reads exactly like a repo that got cleaner.
    """
    tree = _make_tree(tmp_path, extra=[("docs/decisions/2026-01-01-x.md", "seed_x.py")])
    (tree / "memory" / "MEMORY.md").unlink()
    res = _run(tree, "--docs-live")
    assert res.returncode != 0
    assert "cannot read memory/MEMORY.md" in res.stderr


def test_nested_undated_collection_stays_frozen(tmp_path):
    """Rule 3 is depth-restricted, and round 2 of review is why.

    Undated at ANY depth admitted six verbatim copies of other repos' ADRs and two
    training reports for a filter removed 2026-08-03 — 21 findings, 7.7% of the live
    total — into the tier whose contract is "maintained; a dead reference here costs
    something". A nested undated directory is a COLLECTION inside a frozen one; only a
    file sitting beside the dated ones is an index.
    """
    deep, beside = "docs/evidence/adr/other-repo-ADR-001.md", "docs/evidence/README.md"
    tree = _make_tree(tmp_path, extra=[(deep, "seed_deep_xyz.py"),
                                       (beside, "seed_beside_xyz.py")])
    live = _findings(_run(tree, "--docs-live").stdout)
    frozen = _findings(_run(tree, "--docs-frozen").stdout)
    assert "seed_deep_xyz.py" in frozen and "seed_deep_xyz.py" not in live
    assert "seed_beside_xyz.py" in live and "seed_beside_xyz.py" not in frozen


@pytest.mark.parametrize("mention,routes", [
    ("`docs/decisions/2026-01-01-x.md`", True),          # ours
    ("`../docs/decisions/2026-01-01-x.md`", True),       # memory/MEMORY.md writes these
    ("`NexusMind/docs/decisions/2026-01-01-x.md`", False),          # another repo's
    ("https://github.com/o/r/blob/main/docs/decisions/2026-01-01-x.md", False),
])
def test_routing_pattern_does_not_claim_another_repos_path(tmp_path, mention, routes):
    """A cross-repo path must not register as routing into OUR docs/.

    Unanchored, `NexusMind/docs/ARTICLE_RECORD.md` matched from its `docs/` onward —
    and `CLAUDE.md` carries two such paths today. They were inert only because no local
    file shared the name, which is not a property anyone chose.
    """
    rel, frag = "docs/decisions/2026-01-01-x.md", "seed_routing_xyz.py"
    tree = _make_tree(tmp_path, extra=[(rel, frag)])
    (tree / "CLAUDE.md").write_text(f"See {mention} for the procedure.\n")
    in_live = frag in _findings(_run(tree, "--docs-live").stdout)
    assert in_live is routes, (
        f"{mention} {'did not route' if routes else 'routed'} — "
        f"the left boundary is wrong")


def test_override_counts_are_printed(tmp_path):
    """Rule 2 makes the tier a function of MUTABLE text, so the count must be visible.

    `CLAUDE.md` is the most-edited file here and its pointer table is under a per-row
    cap every audit trims, so the likely edit is a REMOVAL — which moves a file
    live→frozen and makes LIVE fall. A falling LIVE count reads as "docs got cleaner".
    It cannot be prevented without a hand-kept list, so it is made visible.
    """
    tree = _make_tree(tmp_path, extra=[("docs/decisions/2026-01-01-r.md", "seed_r.py"),
                                       ("docs/evidence/README.md", "seed_u.py")])
    (tree / "CLAUDE.md").write_text("See `docs/decisions/2026-01-01-r.md`.\n")
    line = _tier_line(_run(tree, "--docs-live").stdout, "LIVE")
    assert "[+1 by routing, +1 by undated index]" in line, line
    # and it must disappear with the pointer it reports
    (tree / "CLAUDE.md").write_text("no pointers here\n")
    assert "+1 by routing" not in _tier_line(_run(tree, "--docs-live").stdout, "LIVE")
