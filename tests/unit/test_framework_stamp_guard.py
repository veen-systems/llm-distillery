"""The framework stamp's own probe (llm-distillery, adopting agent-ready-projects#136).

`CLAUDE.md`'s footer used to assert that the four user-global skills were byte-identical
to the stamped release. That is a claim about files OUTSIDE this repo, so no commit here
can hold it still: it was written on 2026-09-11, and on 2026-09-17 upstream had moved six
releases and the installed copies with it — the sentence was false and nothing said so.
`scripts/verification/check_framework_stamp.sh` replaces the sentence.

⛔ **The arm that matters is `test_skipped_skill_is_not_a_pass`.** Upstream's own first
draft printed "CANNOT VERIFY: <skill> is not installed" and then "byte-identical", exit 0,
because the skip left the counter alone — a false PASS with the evidence of its own failure
printed beside it. Delete the `[ "$n" = "$N_WANT" ]` gate and only that test goes red.

⚠️ **Six tests here exist because a review found the branch they cover had NO test and
proved it with a surviving mutant**: the not-a-git-repo branch, both `$HOME`-derived
defaults, an unreadable installed file, a `CLAUDE.md` naming two versions, and the count
that must be derived rather than written down. The first draft of this file claimed "six
branches executed" while one of the six it named was untested.

⚠️ Mostly HERMETIC — a temp framework clone and a temp skills directory, not
`~/repos/agent-ready-projects` and `~/.claude/skills`. A test asserting against this
machine's real installs would fail on every upstream release, which is the one moment the
probe must still be trusted. `test_real_estate_reaches_a_verdict` is the deliberate
exception: it is the only arm that can catch `WANT` drifting out of step with what is
really installed, which no hermetic test can see.
"""

import os
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GUARD = os.path.join(ROOT, "scripts", "verification", "check_framework_stamp.sh")

SKILLS = ("audit-context", "curate", "update-drift", "review-changes")
TAG = "v1.45.1"


def _git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)


@pytest.fixture
def estate(tmp_path):
    """A framework clone tagged TAG, an installed skills dir matching it, a stamped repo.

    Laid out under the DEFAULT paths relative to tmp_path, so the same fixture serves both
    the explicit-env tests and the `$HOME`-default ones.
    """
    fw = tmp_path / "repos" / "agent-ready-projects"
    (fw / ".claude" / "skills").mkdir(parents=True)
    _git(tmp_path, "init", "-q", str(fw))
    _git(fw, "config", "user.email", "t@t")
    _git(fw, "config", "user.name", "t")
    for s in SKILLS:
        d = fw / ".claude" / "skills" / s
        d.mkdir()
        (d / "SKILL.md").write_text(f"# {s}\nbody of {s}\n")
    _git(fw, "add", "-A")
    _git(fw, "commit", "-qm", "skills")
    _git(fw, "tag", TAG)

    skills = tmp_path / ".claude" / "skills"
    for s in SKILLS:
        d = skills / s
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(f"# {s}\nbody of {s}\n")

    repo = tmp_path / "project"
    repo.mkdir()
    _git(tmp_path, "init", "-q", str(repo))
    (repo / "CLAUDE.md").write_text(f"*Framework: agent-ready-projects {TAG} — stamped.*\n")
    return repo, fw, skills


def _run(estate, cwd=None, **env):
    repo, fw, skills = estate
    e = dict(os.environ, FRAMEWORK=str(fw), CLAUDE_SKILLS=str(skills))
    e.update(env)
    for k, v in list(e.items()):
        if v is None:
            del e[k]
    return subprocess.run(
        ["bash", GUARD], cwd=str(cwd or repo), env=e, capture_output=True, text=True
    )


# --- the contract ---------------------------------------------------------


def test_clean_estate_verifies(estate):
    r = _run(estate)
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"4 global skills byte-identical to {TAG}" in r.stdout


def test_drift_is_exit_1_and_names_the_skill(estate):
    _repo, _fw, skills = estate
    (skills / "curate" / "SKILL.md").write_text("# curate\nlocally edited\n")
    r = _run(estate)
    assert r.returncode == 1
    assert "DRIFT: curate" in r.stdout
    assert "byte-identical" not in r.stdout


def test_skipped_skill_is_not_a_pass(estate):
    """The false-PASS arm: 3 of 4 identical must never read as verified."""
    _repo, _fw, skills = estate
    (skills / "review-changes" / "SKILL.md").unlink()
    r = _run(estate)
    assert r.returncode == 2
    assert "compared 3 of 4 skills" in r.stdout
    assert "byte-identical" not in r.stdout


def test_drift_plus_a_hole_still_reports_the_hole(estate):
    """Drift is decidable, but a run that skipped a skill must say so either way.

    An earlier draft exited 1 on drift *before* printing the shortfall, so a caller
    keying on exit 1 was told the comparison had been complete.
    """
    _repo, _fw, skills = estate
    (skills / "curate" / "SKILL.md").write_text("# curate\nedited\n")
    (skills / "review-changes" / "SKILL.md").unlink()
    r = _run(estate)
    assert r.returncode == 1
    assert "DRIFT: curate" in r.stdout
    assert "compared 3 of 4 skills" in r.stdout


def test_count_is_derived_not_restated(estate, tmp_path):
    """The count must FOLLOW `WANT`, proven by making them disagree.

    `N_WANT=4` beside a four-name `WANT` reproduces upstream's original false PASS the
    moment the two drift apart: the mutant printed "CANNOT VERIFY: <skill> is not
    installed" and then "4 global skills byte-identical", exit 0.

    ⛔ **This test was a SPELLING CHECK until round 2 killed it.** It asserted
    `"N_WANT=$(printf" in src` and exercised only the 4-of-4 happy path, so a mutant that
    derived the count from a literal list — `printf '%s\n' a b c d | wc -l` — satisfied
    both halves and all 17 tests passed. A name is an assertion: the test claimed to prove
    derivation and proved spelling. The only thing that kills it is a run where `WANT` and
    the count MUST disagree if the count is a literal.
    """
    variant = tmp_path / "with-a-fifth-skill.sh"
    src = open(GUARD).read()
    assert 'WANT="audit-context curate update-drift review-changes"' in src
    variant.write_text(
        src.replace(
            'WANT="audit-context curate update-drift review-changes"',
            'WANT="audit-context curate update-drift review-changes not-installed-skill"',
        )
    )
    repo, fw, skills = estate
    e = dict(os.environ, FRAMEWORK=str(fw), CLAUDE_SKILLS=str(skills))
    r = subprocess.run(
        ["bash", str(variant)], cwd=str(repo), env=e, capture_output=True, text=True
    )
    # A DERIVED count says 4 of 5 and refuses; a literal 4 says "byte-identical", exit 0.
    assert r.returncode == 2, r.stdout + r.stderr
    assert "compared 4 of 5 skills" in r.stdout
    assert "byte-identical" not in r.stdout


def test_frontmatter_key_outranks_prose(estate):
    """The anchored stamp is authority; a provenance line must not outvote it.

    Round 2's refutation: unanimity over the SCAN is unanimity over what the scan could
    see. The `[^0-9]{0,40}` bound silently drops a loosely-worded stamp, and a stale
    "adopted from … v1.40.0" line then wins uncontested AND unanimously — exit 0, naming
    a tag nobody pinned. A missed stamp does not stay undecidable; it becomes invisible.
    """
    repo, fw, _skills = estate
    _git(fw, "tag", "v1.40.0")
    (repo / "CLAUDE.md").write_text(
        "---\n"
        f"framework: agent-ready-projects {TAG}\n"
        "---\n\n"
        "Adopted from `ducroq/agent-ready-projects` v1.40.0 (#136), whose curate ships it.\n"
    )
    r = _run(estate)
    assert r.returncode == 2, r.stdout + r.stderr
    assert f"stamp is {TAG} but it also names v1.40.0" in r.stdout
    assert "byte-identical" not in r.stdout


def test_frontmatter_key_agreeing_with_prose_verifies(estate):
    """The corroboration arm must not fire when everything agrees — or it cries wolf."""
    repo, _fw, _skills = estate
    (repo / "CLAUDE.md").write_text(
        "---\n"
        f"framework: agent-ready-projects {TAG}\n"
        "---\n\n"
        f"*Framework: agent-ready-projects {TAG} — triaged.*\n"
    )
    r = _run(estate)
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"4 global skills byte-identical to {TAG}" in r.stdout


def test_corroboration_cannot_silently_not_run(estate):
    """The census invariant: key matched, scan empty — impossible unless the scan failed.

    Both extractions swallow stderr, so a `grep` that FAILED is indistinguishable from one
    that matched nothing. In the key-present branch an empty scan would mean the
    corroboration never ran while the run still reported a verdict — a check reporting
    nothing wrong having checked nothing. The key pattern is a strict subset of the scan
    pattern, so this state is unreachable from data and is therefore a self-test.
    """
    src = open(GUARD).read()
    assert "the stamp scan returned nothing while the key matched" in src
    # Reachable only by breaking the scan, which is what a mutation would do.
    repo, fw, skills = estate
    broken = str(repo / "broken.sh")
    open(broken, "w").write(
        src.replace('grep -oE "agent-ready-projects[^0-9]{0,40}', 'grep -oE "NO-SUCH-TOKEN[^0-9]{0,40}')
    )
    (repo / "CLAUDE.md").write_text(
        f"---\nframework: agent-ready-projects {TAG}\n---\n"
    )
    e = dict(os.environ, FRAMEWORK=str(fw), CLAUDE_SKILLS=str(skills))
    r = subprocess.run(["bash", broken], cwd=str(repo), env=e, capture_output=True, text=True)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "scan returned nothing while the key matched" in r.stdout
    assert "byte-identical" not in r.stdout


def test_a_worktree_is_a_usable_clone(estate, tmp_path):
    """`.git` is a FILE in a worktree, so `[ -d "$FRAMEWORK/.git" ]` rejected a good clone.

    Compounded: the message it printed was in this suite's own skip list, so such a
    machine reported green-with-a-skip while the probe was permanently undecidable.
    """
    _repo, fw, _skills = estate
    wt = tmp_path / "framework-worktree"
    _git(fw, "worktree", "add", "-q", "--detach", str(wt), TAG)
    assert (wt / ".git").is_file(), "fixture precondition: a worktree's .git is a file"
    r = _run(estate, FRAMEWORK=str(wt))
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"4 global skills byte-identical to {TAG}" in r.stdout


def test_version_is_derived_from_the_stamp_not_hardcoded(estate):
    """Bumping the stamp must re-arm the probe against the NEW tag, not the old one."""
    repo, fw, _skills = estate
    _git(fw, "tag", "v9.0.0")
    (repo / "CLAUDE.md").write_text("*Framework: agent-ready-projects v9.0.0 — bumped.*\n")
    r = _run(estate)
    assert r.returncode == 0
    assert "v9.0.0" in r.stdout and TAG not in r.stdout


# --- undecidable states, which must never read as a pass ------------------


def test_missing_stamp_cannot_decide(estate):
    repo, _fw, _skills = estate
    (repo / "CLAUDE.md").write_text("no framework stamp at all\n")
    r = _run(estate)
    assert r.returncode == 2
    assert "no framework stamp" in r.stdout


def test_two_versions_in_claude_md_cannot_decide(estate):
    """A half-bump, and prose naming an older release, are the same defect.

    `head -1` took whichever came FIRST in the file and verified it with a confident
    PASS — so a footer bumped without the frontmatter, or a sentence citing the release
    an item was adopted from, silently chose the wrong tag.
    """
    repo, fw, _skills = estate
    _git(fw, "tag", "v9.0.0")
    (repo / "CLAUDE.md").write_text(
        "Adopted from agent-ready-projects v9.0.0 (#136).\n\n"
        f"*Framework: agent-ready-projects {TAG} — stamped.*\n"
    )
    r = _run(estate)
    assert r.returncode == 2
    assert "more than one framework version" in r.stdout
    assert "byte-identical" not in r.stdout


def test_tag_absent_from_clone_cannot_decide(estate):
    repo, _fw, _skills = estate
    (repo / "CLAUDE.md").write_text("*Framework: agent-ready-projects v0.0.1*\n")
    r = _run(estate)
    assert r.returncode == 2
    assert "not in the framework clone" in r.stdout


def test_skill_absent_at_that_tag_is_not_a_fetch_problem(estate):
    """`git show TAG:path` fails for a missing FILE too, and `git fetch` cannot fix that.

    Realistic: upstream renames a global skill, or the stamp is rolled back past the
    release that moved one into the global set.
    """
    repo, fw, _skills = estate
    shutil.rmtree(fw / ".claude" / "skills" / "review-changes")
    _git(fw, "add", "-A")
    _git(fw, "commit", "-qm", "drop review-changes")
    _git(fw, "tag", "v2.0.0")
    (repo / "CLAUDE.md").write_text("*Framework: agent-ready-projects v2.0.0*\n")
    r = _run(estate)
    assert r.returncode == 2
    assert "has no .claude/skills/review-changes/SKILL.md" in r.stdout
    assert "fetch tags" not in r.stdout


def test_unreadable_installed_file_cannot_decide(estate):
    """The false-PASS that `diff | grep -c` produced: a failed comparison read as 0 lines.

    With the content made completely different AND the file unreadable, the old form
    printed "4 global skills byte-identical", exit 0, with only `Permission denied` on
    stderr.
    """
    _repo, _fw, skills = estate
    target = skills / "curate" / "SKILL.md"
    target.write_text("# curate\ncompletely different content\n")
    os.chmod(target, 0o000)
    try:
        r = _run(estate)
    finally:
        os.chmod(target, 0o644)
    if os.geteuid() == 0:
        pytest.skip("running as root — chmod 000 does not deny access")
    assert r.returncode == 2
    assert "cannot compare" in r.stdout
    assert "byte-identical" not in r.stdout


def test_framework_not_a_clone_cannot_decide(estate):
    r = _run(estate, FRAMEWORK="/nonexistent-framework-path")
    assert r.returncode == 2
    assert "is not a git clone" in r.stdout


def test_outside_a_git_repo_cannot_decide(estate, tmp_path):
    """This branch had NO test and a review proved it with a surviving mutant."""
    outside = tmp_path / "not-a-repo"
    outside.mkdir()
    r = _run(estate, cwd=outside)
    assert r.returncode == 2
    assert "not in a git repo" in r.stdout


def test_home_unset_is_undecidable_not_drift(estate):
    """An environment problem must not be reported as a verdict about the skills.

    Under `set -u` a bare `$HOME` aborted the script, and an abort exits 1 — which this
    contract reads as DRIFT. A cron, container or `env -i` caller got a confident wrong
    answer.
    """
    r = _run(estate, HOME=None, FRAMEWORK=None, CLAUDE_SKILLS=None)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "HOME is unset" in r.stdout


# --- the defaults, which the first draft left entirely unasserted ---------


def test_framework_default_is_used_when_unset(estate, tmp_path):
    """Header difference #2 — "runs with no environment set up" — was dead to the suite.

    Mutating the default to a nonexistent path left all tests green.
    """
    r = _run(estate, HOME=str(tmp_path), FRAMEWORK=None)
    assert r.returncode == 0, r.stdout + r.stderr
    assert str(tmp_path / "repos" / "agent-ready-projects") in r.stdout


def test_skills_default_is_used_when_unset(estate, tmp_path):
    r = _run(estate, HOME=str(tmp_path), CLAUDE_SKILLS=None)
    assert r.returncode == 0, r.stdout + r.stderr
    assert str(tmp_path / ".claude" / "skills") in r.stdout


# --- the one non-hermetic arm --------------------------------------------


def test_real_estate_reaches_a_verdict():
    """The only arm that can catch `WANT` drifting out of step with what is installed.

    Deliberately asserts a VERDICT, not a value: 0 or 1 are both real answers about this
    machine, and pinning either would make the suite fail on the next upstream release.
    Exit 2 means the probe could not decide — a `WANT` naming a skill that no longer
    exists, or a clone without the stamped tag — and that is the state no hermetic test
    can see.
    """
    r = subprocess.run(["bash", GUARD], cwd=ROOT, capture_output=True, text=True)
    if r.returncode == 2 and "is not a git clone" in r.stdout:
        pytest.skip(f"no framework clone on this machine: {r.stdout.strip()}")
    # ⛔ "not in the framework clone" is NOT skipped, though an earlier draft skipped it.
    # That message covers an unfetched clone AND a stamp naming a release that does not
    # exist — which is the exact defect CLAUDE.md warns about in bold ("a stamp bump
    # requires the adopt items in the tree first; ahead of its content it silences the
    # check that would catch the gap"). Skipping on it made this arm silent on the one
    # state it was written to catch, while its own docstring called that state invisible
    # to every hermetic test.
    assert r.returncode in (0, 1), r.stdout + r.stderr
