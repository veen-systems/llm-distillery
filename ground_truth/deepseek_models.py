"""Which DeepSeek model id an oracle run is allowed to send.

⛔ **ALLOWLIST, NOT A DENYLIST — that distinction IS this module.**

The rule (`memory/gotcha-log.md`, 2026-08-14): a **literal** DeepSeek model id enables
reasoning mode. Only the ``deepseek-chat`` alias serves the non-reasoning model we score
with, so the alias is not a convenience — it is the contract.

The guard this replaces was ``args.model.startswith("deepseek-v4")``: a denylist of the ids
that happened to exist the day it was written. On **2026-09-10** DeepSeek renamed the flash
line — ``GET /models`` stopped returning ``deepseek-v4-flash`` and now returns
``deepseek-flash``. The denylist did not match the new id, so **the single flash id the
vendor now advertises, the one anyone reading ``GET /models`` would reach for, walked
straight past the guard.** Enumerating the bad values is a hand-built population;
enumerating the one good value is not.

**Measured 2026-09-10** (matched prompt, matched request shape, one call each):

===========================  ===================  ==============  ==================
``--model``                  ``content``          reasoning       completion tokens
===========================  ===================  ==============  ==================
``deepseek-chat`` (alias)    ``{"score": 7}``     ``None``        6
``deepseek-flash`` (literal) ``{"score":7}``      **present**     **208**
===========================  ===================  ==============  ==================

⚠️ **THE SYMPTOM CHANGED, AND THE NEW ONE DOES NOT RAISE.** At ``max_tokens=16`` the literal
id still reproduces the 2026-08-14 empty-``content`` parser break. At the production
``max_tokens=4096`` with ``response_format=json_object`` it returns **correct** content and
merely bills ~34.7× the output tokens. ⚠️ n=1 on one trivial prompt — that is a direction and
a rough magnitude, **not a calibrated multiplier**; a real scoring prompt was not measured.
A run on the literal id therefore looks completely healthy and quietly costs many times more,
and nothing downstream would catch it.

⛔ **THERE IS NO VERSION TO PIN, so "pin it instead" is not an available fix.** ``GET /models``
returns exactly ``deepseek-flash`` and ``deepseek-v4-pro``; the response ``model`` field reads
``deepseek-flash`` whatever you send (alias, new literal, or the retired ``deepseek-v4-flash``,
which still resolves); no response header carries a version. **The served version is not
observable through this API** — see llm-distillery#157.
"""

from urllib.parse import urlparse

#: The ONLY model id an oracle run may send to DeepSeek. Adding to this set is a decision
#: about the labelling function, not a config tweak — see ADR-010 (oracle consistency).
SAFE_DEEPSEEK_MODELS = frozenset({"deepseek-chat"})

#: Hosts for which the allowlist applies. `score_deepseek_production.py` can be pointed at
#: Gemini's OpenAI-compatible endpoint via --base-url, and that call must not be blocked.
DEEPSEEK_HOSTS = frozenset({"api.deepseek.com"})


class UnsafeDeepSeekModel(ValueError):
    """Raised when a run would send a literal DeepSeek id instead of the alias."""


def is_deepseek_endpoint(base_url: str) -> bool:
    """True when `base_url` points at DeepSeek's own API host.

    ⛔ The hostname is NORMALISED first, and that is not cosmetic. A root-anchored FQDN —
    `https://api.deepseek.com./v1/...` — is legal, resolves, reaches the real API, and
    `urlparse().hostname` returns it verbatim as `api.deepseek.com.`, which is not in the set.
    Measured 2026-09-10 against the live endpoint: the trailing dot walked straight past this
    check and returned DeepSeek's own 401. `urlparse` already lowercases and strips userinfo
    and the port; the trailing dot is the part it leaves.
    """
    host = urlparse(base_url).hostname
    if not host:
        return False
    return host.rstrip(".") in DEEPSEEK_HOSTS


def assert_safe_deepseek_model(model: str, base_url: str | None = None) -> str:
    """Return `model`, or raise `UnsafeDeepSeekModel` if it would enable reasoning mode.

    `base_url=None` means "the caller already knows this is DeepSeek" and enforces
    unconditionally. A non-DeepSeek `base_url` is passed through untouched.
    """
    if base_url is not None and not is_deepseek_endpoint(base_url):
        return model
    if model in SAFE_DEEPSEEK_MODELS:
        return model
    raise UnsafeDeepSeekModel(
        f"--model {model!r} is a literal DeepSeek id, which enables reasoning mode.\n"
        f"       At the production max_tokens it still returns valid JSON but bills ~35x\n"
        f"       the output tokens (measured 2026-09-10); at a small max_tokens it returns\n"
        f"       EMPTY content and breaks the score parser silently.\n"
        f"       Use the alias: --model deepseek-chat\n"
        f"       There is NO versioned flash id to pin (llm-distillery#157, "
        f"memory/gotcha-log.md 2026-08-14)."
    )
