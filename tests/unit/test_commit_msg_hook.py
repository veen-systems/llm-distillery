"""The commit-msg deploy guard (`.githooks/commit-msg`) and its two #136 gaps.

Gap 1, the verifier: a directory holding only prose (`.md`/`.txt`) is not a deployable
package. The verifier skipped `inference_hub.py` and `config.yaml` as absent and then
FAILED the hub check on "no repo_id extracted from inference_hub.py", a failure derived
from a file it had just recorded as legitimately absent. That is what blocked the
2026-08-28 commit (a prompt file staged under `filters/human_thriving/v8/`). Weights, any
`*.py`, a `model/` dir or a `config.yml` still make it a package (PR #167 review).

Gap 2, the word test: every session commit here says "Nothing deployed" / "deploy N/A".
The guard matched the bare word and ran the verifier. The documented way out is
`--no-verify`, and that override caused #44. A guard that fires on correct messages
trains the override it exists to prevent. The message now passes only when every
deploy-class word sits in one of three anchored phrases taken from `git log`; a free
negator window admitted success reports ("No regressions deployed v7").

⛔ The other direction matters more. The hook is a shell script, and a shell hook that
breaks FAILS OPEN: `if ! grep ...` is true when grep errors. So every negated-message
test is paired with a claim that must still BLOCK. That includes claims with a negator
nearby that does not govern the deploy word ("No regressions deployed v7"), a run with
no Python interpreter at all, a deploy word grep sees and Python does not, and a real
package with no repo_id to check.

HERMETIC: each test builds a throwaway git repo with a copy of the real hook. The
gap-2 tests use a stub verifier that always FAILS, so a blocked commit means the verifier
ran and a passed commit means the message check found no claim. The gap-1 tests copy
the REAL verifier; both of their branches return before any Hub call.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HOOK = REPO / ".githooks" / "commit-msg"
VERIFIER = REPO / "scripts" / "deployment" / "verify_filter_package.py"

pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None or shutil.which("git") is None,
    reason="needs bash and git",
)

STUB_VERIFIER = "import sys\nprint('stub verifier: FAIL')\nsys.exit(1)\n"


def make_repo(root, verifier_text, staged):
    """A git repo with the real hook, the given verifier and `staged` files staged."""
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    hook = root / ".githooks" / "commit-msg"
    hook.parent.mkdir()
    shutil.copy(HOOK, hook)
    # The hook execs the forbidden-name guard (added 2026-10-02) and fails closed without it. The copy has no
    # denylist (config/credentials/ is absent here), so the guard passes with a note; these tests stay on the deploy check.
    shutil.copy(HOOK.parent / "check_forbidden_names.sh", hook.parent / "check_forbidden_names.sh")
    verifier = root / "scripts" / "deployment" / "verify_filter_package.py"
    verifier.parent.mkdir(parents=True)
    verifier.write_text(verifier_text)
    for rel, text in staged.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        subprocess.run(["git", "add", rel], cwd=root, check=True)
    return root


@pytest.fixture
def repo(tmp_path):
    return make_repo(tmp_path, STUB_VERIFIER,
                     {"filters/demo/v1/config.yaml": "filter: {version: '1'}\n"})


def run_hook(repo, message, env=None):
    msg = repo / "MSG"
    msg.write_text(message)
    return subprocess.run(
        ["bash", str(repo / ".githooks" / "commit-msg"), str(msg)],
        cwd=repo, capture_output=True, text=True, env=env,
    )


# --- Gap 1: the verifier, run for real -------------------------------------------------

def _hook_python_has_yaml():
    py = shutil.which("python3") or shutil.which("python")
    return bool(py) and subprocess.run([py, "-c", "import yaml"]).returncode == 0


needs_real_verifier = pytest.mark.skipif(
    not _hook_python_has_yaml(), reason="the hook's python3 cannot import yaml")


@needs_real_verifier
def test_non_package_directory_is_not_a_failed_verification(tmp_path):
    """The 2026-08-28 shape: only a prompt file staged under filters/*/v*/. The message
    is a genuine claim, so the negation reader cannot be what lets it through."""
    r_repo = make_repo(tmp_path, VERIFIER.read_text(encoding="utf-8"),
                       {"filters/demo/v1/prompt-candidate-tail.md": "draft\n"})
    r = run_hook(r_repo, "Deployed the prompt tail")
    assert r.returncode == 0, f"non-package dir failed verification:\n{r.stdout}{r.stderr}"
    assert "cannot check" not in r.stdout


@needs_real_verifier
def test_package_without_repo_id_still_fails(tmp_path):
    """Control for the N/A branch: a directory WITH config.yaml is a package. With no
    inference_hub.py and no NO_HUB there is nothing to check the Hub against, and that
    must still block."""
    r_repo = make_repo(tmp_path, VERIFIER.read_text(encoding="utf-8"),
                       {"filters/demo/v1/config.yaml": "filter: {version: '1'}\n"})
    r = run_hook(r_repo, "Deployed demo v1")
    assert r.returncode == 1, f"package with no repo_id got through:\n{r.stdout}{r.stderr}"
    assert "hub: cannot check" in r.stdout


def _load_verifier():
    import importlib.util
    spec = importlib.util.spec_from_file_location("vfp", VERIFIER)
    vfp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vfp)
    return vfp


@pytest.mark.parametrize("files", [
    ["prompt-candidate-tail.md"],
    ["STATUS.md", "notes/draft.txt"],
    ["NOTES.MD"],
])
def test_check_hub_na_for_a_prose_only_directory(tmp_path, files):
    d = tmp_path / "filters" / "demo" / "v1"
    for rel in files:
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text("x")
    [(ok, msg)] = _load_verifier().check_hub(d, None, None)
    assert ok and "N/A" in msg


# A package in progress is not prose (PR #167 review): each of these once passed as N/A,
# because the first version only asked for config.yaml and inference_hub.py to be absent.
@pytest.mark.parametrize("files", [
    ["prompt.md", "config.yaml"],
    ["prompt.md", "adapter_model.safetensors"],
    ["prompt.md", "base_scorer.py"],
    ["prompt.md", "inference.py"],
    ["prompt.md", "config.yml"],
    ["prompt.md", "model/adapter_config.json"],
    ["prompt.md", "NO_HUB_TYPO"],
    [],
])
def test_check_hub_fails_for_a_package_in_progress(tmp_path, files):
    d = tmp_path / "filters" / "demo" / "v1"
    d.mkdir(parents=True)
    for rel in files:
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text("x")
    [(ok, msg)] = _load_verifier().check_hub(d, None, None)
    assert not ok and "cannot check" in msg


@pytest.mark.parametrize("link", ["dir", "dangling"])
def test_check_hub_fails_when_a_symlink_hides_a_package(tmp_path, link):
    """PR #167 review round 2: rglob does not descend into a linked model/ dir, and a
    dangling x.safetensors is not is_file(), so prose plus either read as N/A."""
    d = tmp_path / "filters" / "demo" / "v1"
    d.mkdir(parents=True)
    (d / "README.md").write_text("x")
    if link == "dir":
        real = tmp_path / "real" / "model"
        real.mkdir(parents=True)
        (real / "adapter_model.safetensors").write_text("w")
        (d / "model").symlink_to(real, target_is_directory=True)
    else:
        (d / "x.safetensors").symlink_to(tmp_path / "missing")
    [(ok, msg)] = _load_verifier().check_hub(d, None, None)
    assert not ok and "cannot check" in msg


# --- Gap 2: the word test --------------------------------------------------------------

# The three allowlisted phrases, in the forms this repo's commits actually use. The first
# block is lifted from `git log` (commit hashes as of 2026-09-29).
NEGATED = [
    "Nothing deployed",                                                   # the 2026-08-28 rejection
    "EXP-037, $0, nothing deployed",                                      # 481d35f
    "No spend, no model, no filter, nothing deployed",                    # 34c8a3c
    "No model, no threshold, nothing in filters/, nothing\ndeployed. 6,590 rows",  # 11ead23
    "NOTHING DEPLOYED, and nothing needs a rerun",                        # d047f9d
    "Tripwires: nothing shipped, so there was no outcome",                # 6b9b39b
    "No oracle, no GPU, nothing in filters/ -- deploy N/A",               # 6a35dca
    "Deploy: N/A (no filter or model)",                                   # 734b806
    "No oracle calls, nothing in filters/, deploy N/A -- inapplicable",   # cae6998
    "No spend -- nothing deployed",
    "Deploy N/A, not skipped: nothing reached NexusMind",                 # 577c3d8
    "Docs only. Nothing deployed.",
    "Fix typo\n\n$0, no oracle, nothing in filters/, deploy N/A \u2014 inapplicable, not skipped.",
    "Prepare v2 package; not deployed",
    "Nothing has been deployed",
    "Nothing was deployed.",
    "Package built, not yet uploaded",
    "Checked the diff; not re-deployed",
]

# Real negations OUTSIDE the allowlist. They block, and that is the price of an anchored
# list: rewording costs a sentence, while a free window admitted success reports.
# Widening the allowlist to pass any of these is a decision, so it must turn a test red.
OUTSIDE_ALLOWLIST = [
    "Nothing deployed and deploy N/A, not skipped",
    "Prepare v2 package (not yet uploaded to the Hub)",
    "We didn't ship v2 yet",
    "Never deployed, see #44",
    "Neither uploaded nor deployed",
    "Deploy is N/A rather than skipped",
    "Merged without uploading.",
    "No deploy.",
    # Round 2: "not" and "<word>: n/a" must OPEN the clause, and "none"/"skipped" are
    # gone. These two were real passes in git log, and the anchor costs them.
    "Opened NexusMind PR #474, not merged and not deployed",              # 4d89aa4
    "Held at v7 - v7 NOT deployed: MAE 0.61",                             # b2705df
    "Weights were not uploaded",
    "Update config: deploy: none",
]

CLAIMS = [
    "Deploy demo v1 to HuggingFace Hub",
    "Deployed demo v1",
    "Deployed v7",
    "Uploaded weights",
    "No regressions, deployed v1",
    "No regressions; deployed v1",
    "No regressions. Deployed v1",
    "No regressions and deployed v1",
    "Not only fixed but deployed",
    "Nothing broke\n\nDeployed v1",
    "Nothing broke \u2014 deployed v1",
    "Fixed the not-a-number bug, deployed v1",
    "Nothing deployed yesterday; deployed v1 today",
    "Deployed v1, nothing else",
    "No new tests needed before we deployed v1",
    "No-op deploy of v1",
    # Every message the PR #167 review got to LAND through the first version's window.
    "No regressions deployed v7",
    "v7 uploaded: none skipped",
    "no failures deploying v7",
    "No drift uploading v7 to Hub",
    "Without a hitch deployed v7",
    "without regressions shipped v7",
    "No rollback needed shipped v2",
    "Hotfix with no downtime deployed v9",
    "Not only deployed v1 to Hub",
    "Nothing else changed deploy v7",
    "No new deps deploy v7",
    "Released: none of the known bugs",
    "deployed: none of the old weights remain",
    "Uploaded none-the-less, v1 to Hub",
    # Each allowlisted phrase followed by more than the end of its clause.
    "Nothing deployed v7 to Hub",
    "Not deployed v7 by hand, by the script",
    "Deploy N/A for v6, done for v7",
    # "nothing" must open the clause.
    "Fixed nothing deployed v7",
    # PR #167 review round 2: rules 2 and 3 were not anchored at clause start, and
    # "none"/"skipped" after a deploy word admitted status lines.
    "Errors during deploy: none",
    "Pending deploys: none",
    "Files that failed to upload: none",
    "Blockers to deploy: none.",
    "Steps skipped during deploy: none",
    "v7 to Hub, failures during upload: none",
    "Rollbacks after deploy: none; v7 is on the Hub",
    "Outstanding uploads: none",
    "Uploaded: none, all 12 files verified",
    "Items not yet uploaded: none",
    "Rumour that v7 was not uploaded: debunked",
    "Not deployed? False.",
    "(not deployed)",
    "Errors during deploy: n/a",
    # Not in the word list before round 2, so these skipped the gate entirely.
    "Redeployed v7",
    "v7 ships today",
    "Regressed nothing deployed.",
    # Only was/is/has been may sit between "nothing" and the word.
    "Nothing broke when we deployed.",
]

@pytest.mark.parametrize("message", NEGATED)
def test_negated_deploy_word_passes(repo, message):
    r = run_hook(repo, message)
    assert r.returncode == 0, f"negated claim was blocked:\n{r.stdout}{r.stderr}"
    assert "stub verifier" not in r.stdout, "verifier ran on a negated claim"


@pytest.mark.parametrize("message", CLAIMS)
def test_real_claim_still_blocks(repo, message):
    r = run_hook(repo, message)
    assert r.returncode == 1, f"unverified deploy claim got through:\n{r.stdout}{r.stderr}"
    assert "stub verifier: FAIL" in r.stdout, "blocked, but not by the verifier"


@pytest.mark.parametrize("message", OUTSIDE_ALLOWLIST)
def test_negation_outside_the_allowlist_still_blocks(repo, message):
    r = run_hook(repo, message)
    assert r.returncode == 1, f"passed outside the allowlist:\n{r.stdout}{r.stderr}"
    assert "stub verifier: FAIL" in r.stdout


def test_word_grep_sees_but_python_does_not_is_a_claim(repo):
    """PR #167 review: under LC_ALL=C grep's \\b sees "deployed" in "édeployed"
    (é is two non-word bytes) while Python's Unicode \\b does not, so Python found ZERO
    deploy words. Zero matches used to print "negated". It must be a claim."""
    env = dict(os.environ, LC_ALL="C")
    r = run_hook(repo, "\u00e9deployed v1", env=env)
    assert r.returncode == 1, f"zero-match message got through:\n{r.stdout}{r.stderr}"
    assert "stub verifier: FAIL" in r.stdout


def test_no_deploy_word_passes_without_verifying(repo):
    r = run_hook(repo, "Refactor scorer")
    assert r.returncode == 0
    assert "stub verifier" not in r.stdout


def test_comment_lines_are_ignored(repo):
    r = run_hook(repo, "Refactor scorer\n# Deployed v1\n")
    assert r.returncode == 0


def test_no_interpreter_fails_closed(repo, tmp_path_factory):
    """With no python on PATH the negation reader cannot run. That must count as a
    CLAIM (block), never as "negated" (pass). Before #136 there was no negation reader;
    this pins the direction of its failure."""
    bindir = tmp_path_factory.mktemp("bin")
    for tool in ("bash", "git", "grep", "cat", "awk", "sort", "sed", "mktemp", "rm"):
        path = shutil.which(tool)
        assert path, f"{tool} missing"
        os.symlink(path, bindir / tool)
    env = {"PATH": str(bindir), "HOME": os.environ.get("HOME", str(repo))}
    r = run_hook(repo, "Nothing deployed", env=env)
    assert r.returncode == 1, f"passed with no interpreter:\n{r.stdout}{r.stderr}"
