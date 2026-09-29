"""The commit-msg deploy guard (`.githooks/commit-msg`) and its two #136 gaps.

Gap 1, the verifier: a directory with neither `config.yaml` nor `inference_hub.py` is not
a deployable package. The verifier skipped both files as absent and then FAILED the hub
check on "no repo_id extracted from inference_hub.py", a failure derived from a file it
had just recorded as legitimately absent. That is what blocked the 2026-08-28 commit
(a prompt file staged under `filters/human_thriving/v8/`).

Gap 2, the word test: every session commit here says "Nothing deployed" / "deploy N/A".
The guard matched the bare word and ran the verifier. The documented way out is
`--no-verify`, and that override caused #44. A guard that fires on correct messages
trains the override it exists to prevent.

⛔ The other direction matters more. The hook is a shell script, and a shell hook that
breaks FAILS OPEN: `if ! grep ...` is true when grep errors. So every negated-message
test is paired with a claim that must still BLOCK. That includes claims with a negator
nearby that does not govern the deploy word ("No regressions, deployed v9"), a run with
no Python interpreter at all, and a real package with no repo_id to check.

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


def test_check_hub_na_only_when_both_files_absent(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("vfp", VERIFIER)
    vfp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vfp)

    d = tmp_path / "filters" / "demo" / "v1"
    d.mkdir(parents=True)
    (d / "prompt.md").write_text("x")
    [(ok, msg)] = vfp.check_hub(d, None, None)
    assert ok and "N/A" in msg

    (d / "config.yaml").write_text("filter: {version: '1'}\n")
    [(ok, msg)] = vfp.check_hub(d, None, None)
    assert not ok and "cannot check" in msg


# --- Gap 2: the word test --------------------------------------------------------------

# Taken from this repo's own history: the 2026-08-28 rejection ("Nothing deployed"), the
# session preamble idiom ("deploy N/A"), and ordinary English negations of the same claim.
NEGATED = [
    "Nothing deployed",
    "Docs only. Nothing deployed.",
    "Fix typo\n\n$0, no oracle, nothing in filters/, deploy N/A — inapplicable, not skipped.",
    "Nothing deployed and deploy N/A, not skipped",
    "Prepare v2 package; not deployed",
    "Prepare v2 package (not yet uploaded to the Hub)",
    "Weights were not uploaded",
    "We didn't ship v2 yet",
    "We didn’t ship v2 yet",
    "Nothing has been deployed",
    "Never deployed, see #44",
    "Update config: deploy: none",
    "Neither uploaded nor deployed",
]

CLAIMS = [
    "Deploy demo v1 to HuggingFace Hub",
    "Deployed demo v1",
    "Uploaded weights",
    "No regressions, deployed v1",
    "No regressions; deployed v1",
    "No regressions. Deployed v1",
    "No regressions and deployed v1",
    "Not only fixed but deployed",
    "Nothing broke\n\nDeployed v1",
    "Nothing broke — deployed v1",
    "Fixed the not-a-number bug, deployed v1",
    "Nothing deployed yesterday; deployed v1 today",
    "Deployed v1, nothing else",
    "No new tests needed before we deployed v1",
    "No-op deploy of v1",
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
