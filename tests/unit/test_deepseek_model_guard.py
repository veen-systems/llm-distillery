"""The DeepSeek model allowlist, and proof that all three oracle scripts enforce it.

⚠️ **A green test on the predicate proves only the predicate.** The denylist this replaces
was itself correct code on the right path — it simply stopped matching when the vendor
renamed the model on 2026-09-10. So the subprocess tests below are the point of this file:
they run each script for real and assert it exits before any network call.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from ground_truth.deepseek_models import (
    SAFE_DEEPSEEK_MODELS,
    UnsafeDeepSeekModel,
    assert_safe_deepseek_model,
    is_deepseek_endpoint,
)

REPO = Path(__file__).resolve().parents[2]
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

# Every literal id we know DeepSeek has served or listed. `deepseek-flash` is the one the
# old `startswith("deepseek-v4")` denylist missed — keep it first, it is the regression.
LITERAL_IDS = [
    "deepseek-flash",
    "deepseek-v4-flash",
    "deepseek-v4-pro",
    "deepseek-v4-flash-vision-exp",
    "deepseek-reasoner",
]


def test_alias_is_the_only_accepted_model():
    assert SAFE_DEEPSEEK_MODELS == {"deepseek-chat"}
    assert assert_safe_deepseek_model("deepseek-chat") == "deepseek-chat"


@pytest.mark.parametrize("model", LITERAL_IDS)
def test_literal_ids_are_rejected(model):
    with pytest.raises(UnsafeDeepSeekModel):
        assert_safe_deepseek_model(model)


def test_the_renamed_flash_id_would_have_passed_the_old_denylist():
    """The regression this module exists for, stated as an assertion."""
    assert not "deepseek-flash".startswith("deepseek-v4")   # old guard: no match
    with pytest.raises(UnsafeDeepSeekModel):                # new guard: blocked
        assert_safe_deepseek_model("deepseek-flash")


def test_non_deepseek_endpoint_is_passed_through():
    assert not is_deepseek_endpoint(GEMINI_URL)
    assert assert_safe_deepseek_model("gemini-2.5-flash", GEMINI_URL) == "gemini-2.5-flash"


def test_deepseek_endpoint_is_still_enforced_when_base_url_is_given():
    url = "https://api.deepseek.com/chat/completions"
    assert is_deepseek_endpoint(url)
    with pytest.raises(UnsafeDeepSeekModel):
        assert_safe_deepseek_model("deepseek-flash", url)


def _run(*args):
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO, capture_output=True, text=True, timeout=120,
        env={"PYTHONPATH": ".", "PATH": "/usr/bin:/bin", "HOME": str(Path.home())},
    )


# Each entry is a real command line that would otherwise start an oracle run.
CALL_SITES = [
    pytest.param(
        ("scripts/score_deepseek_production.py", "--model", "deepseek-flash",
         "--input", "/nonexistent.jsonl", "--output", "/nonexistent/out.jsonl"),
        id="score_deepseek_production",
    ),
    pytest.param(
        ("scripts/validate_deepseek_oracle.py", "--model", "deepseek-flash"),
        id="validate_deepseek_oracle",
    ),
    pytest.param(
        ("scripts/score_ollama_oracle.py", "--provider", "deepseek",
         "--model", "deepseek-flash"),
        id="score_ollama_oracle",
    ),
]


@pytest.mark.parametrize("argv", CALL_SITES)
def test_call_site_refuses_the_literal_id(argv):
    """The guard fires in the real script, not just in the helper."""
    r = _run(*argv)
    assert r.returncode != 0, r.stdout + r.stderr
    assert "deepseek-flash" in r.stdout, r.stdout + r.stderr
    assert "--model deepseek-chat" in r.stdout, r.stdout + r.stderr
    # It must refuse BEFORE spending anything: no prompt loaded, no key read, no call made.
    assert "Scoring with:" not in r.stdout, "guard fired too late — setup already ran"


def test_call_site_lets_the_alias_through():
    """Positive control: the guard is not simply 'always fail'.

    `--input` does not exist, so the script must get PAST the guard and fail later —
    proving the alias is accepted rather than the guard being unreachable.
    """
    r = _run("scripts/score_deepseek_production.py", "--model", "deepseek-chat",
             "--input", "/nonexistent.jsonl", "--output", "/nonexistent/out.jsonl")
    assert "is a literal DeepSeek id" not in r.stdout
    assert "Scoring with:" in r.stdout, r.stdout + r.stderr


def test_call_site_lets_a_gemini_endpoint_through():
    """Second positive control: --base-url elsewhere must not be blocked."""
    r = _run("scripts/score_deepseek_production.py", "--model", "gemini-2.5-flash",
             "--base-url", GEMINI_URL, "--key-name", "gemini_api_key",
             "--input", "/nonexistent.jsonl", "--output", "/nonexistent/out.jsonl")
    assert "is a literal DeepSeek id" not in r.stdout
    assert "Scoring with:" in r.stdout, r.stdout + r.stderr


# ---- host normalisation, added 2026-09-10 after review reached the live API around it ----

@pytest.mark.parametrize("url", [
    "https://api.deepseek.com./v1/chat/completions",     # root-anchored FQDN — the live bypass
    "https://API.DEEPSEEK.COM/v1/chat/completions",
    "https://api.deepseek.com:443/v1/chat/completions",
    "https://user:pw@api.deepseek.com/v1/chat/completions",
])
def test_deepseek_host_variants_are_all_recognised(url):
    """⛔ The trailing dot is the one that was measured reaching the real API.

    `urlparse` lowercases the host and strips userinfo and port, so those three were already
    covered; it leaves the root anchor, and `api.deepseek.com.` is not `api.deepseek.com`.
    """
    assert is_deepseek_endpoint(url), url
    with pytest.raises(UnsafeDeepSeekModel):
        assert_safe_deepseek_model("deepseek-flash", url)


@pytest.mark.parametrize("url", [
    "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
    "https://api.deepseek.com.evil.test/v1/chat/completions",   # must NOT match
    "http://localhost:11434/v1/chat/completions",
])
def test_non_deepseek_hosts_are_passed_through(url):
    assert not is_deepseek_endpoint(url), url
    assert assert_safe_deepseek_model("some-other-model", url) == "some-other-model"


# ---- coverage of the SURFACE, not just the shape (added 2026-09-10) -------------------------

def test_every_deepseek_call_site_is_guarded():
    """⛔ I claimed three entry points. Review found SIX.

    The fix's shape was right and its scope was wrong — `filters/common/violence_promotion/v1/
    oracle.py` takes the model as a CONSTRUCTOR ARGUMENT, so it was a latent surface, not merely
    an unguarded literal. This test enumerates the surface from the code rather than from my
    memory of it: any file that posts to DeepSeek must reference the allowlist.
    """
    import subprocess

    r = subprocess.run(
        ["grep", "-rl", "api.deepseek.com", "--include=*.py", str(REPO)],
        capture_output=True, text=True,
    )
    callers = [Path(p) for p in r.stdout.split() if "/docs/evidence/" not in p]
    assert callers, "grep found no DeepSeek callers — the check examined nothing"

    unguarded, latent = [], []
    for f in callers:
        if f.name == "deepseek_models.py":
            continue
        raw = f.read_text(encoding="utf-8", errors="replace")
        # ⚠️ Strip comments before deciding the file talks to DeepSeek. Two panel runners name
        # the host ONLY in a commented-out MODELS entry with no dispatch function behind it —
        # they cannot post to DeepSeek today. Narrowing the predicate to match the claim is not
        # the same as loosening the check: an uncommented entry puts the file straight back in.
        live = "\n".join(l for l in raw.splitlines() if not l.lstrip().startswith("#"))
        if "api.deepseek.com" not in live:
            latent.append(str(f.relative_to(REPO)))
            continue
        if "requests.post" not in live and "urlopen" not in live and "session.post" not in live:
            continue                                   # names the host but makes no call
        if "assert_safe_deepseek_model" not in live:
            unguarded.append(str(f.relative_to(REPO)))
    assert not unguarded, (
        "these files POST to DeepSeek without passing the model through the allowlist: "
        + ", ".join(unguarded)
    )
    # Not an assertion: a commented-out entry is a future surface, not a present defect. It is
    # printed so the count stays visible — my own count of these has been wrong twice.
    if latent:
        print(f"latent (DeepSeek named only in comments): {', '.join(latent)}")

