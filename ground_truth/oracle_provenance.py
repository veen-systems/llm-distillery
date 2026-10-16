"""What scored an oracle label: the full prompt hash and the model the provider SERVED.

llm-distillery#157, phase 1 of veen-systems/pipeline-atlas#169. Every label written
without these is history that cannot be repaired later.

Four stamps, added beside (never replacing) the existing 12-hex ``prompt_hash``. Writers:
``ground_truth/batch_scorer.py``, ``scripts/score_deepseek_production.py``,
``scripts/score_ollama_oracle.py`` (at the record ROOT, not in an analysis field),
``filters/common/violence_promotion/v1/oracle.py`` and
``filters/common/obituary_detector/validation/relabel_deepseek.py``. Reader that acts on
them: ``scripts/oracle/aggregate_k_runs.py`` (refuses k runs that disagree).

``prompt_sha256``
    The FULL sha256 of the prompt template. ``prompt_hash`` stays the first 12 hex
    characters of the same digest, so ``prompt_sha256.startswith(prompt_hash)`` holds
    and every reader that compares against a 12-char literal keeps working.
    ⚠️ It hashes the TEMPLATE each scorer loads (before the article is filled in), and
    the scorers load differently: ``batch_scorer`` hashes the ``.strip()``-ed file (or,
    for a legacy ``## PROMPT TEMPLATE`` file, only that section); the two
    ``scripts/score_*`` hash the raw file; the detector oracles hash their full
    user-message template. One prompt file therefore stamps two digests — measured
    2026-10-16 on 3 smoke rows each, belonging v3 ``prompt-compressed.md``:
    ``99ea1765…`` (batch_scorer) vs ``27dc0591…`` (both scripts). Never join rows from
    different scorers on it; compare within one scorer.

``served_model``
    The model id in the provider's RESPONSE, not the one we requested. ⚠️ For DeepSeek
    this is the TIER, not the version: every flash request reads ``deepseek-flash``
    whatever was sent, and the V4 -> V4.1 swap of 2026-09-10 would not have shown here
    (#157, measured 2026-09-10). It catches a flash <-> pro reroute, nothing finer.
    Gemini's ``model_version`` read a bare ``gemini-2.5-flash`` (3 rows, 2026-10-16), so
    it is no finer. ollama's ``model`` read back the requested tag (3 rows, same day).

``system_fingerprint``
    DeepSeek's (OpenAI-compatible) backend fingerprint — the only candidate in the
    envelope that might move on a silent version swap. ⚠️ UNKNOWN whether it does, or
    whether it also moves for reasons that are not a model change (#157, 2026-10-12).
    Optional in the OpenAI spec, so its absence is stamped as ``ABSENT``, not raised.
    Read ``aeb56401ca74e127821c4f9126dcb669`` on 3 rows 2026-10-16, the value the
    ovr.news session reported on 2026-10-12 (reported there, not verified here).

``model_digest`` (ollama only)
    The tag's digest from ``/api/tags`` at run START — the weights' content identity.
    A re-pull mid-run would not show.

A missing ``served_model`` RAISES, and every writer turns that into a RUN-FATAL stop, not a
per-row error: it is a property of the endpoint, so a per-row error would bill every row
again on every resume (review 2026-10-16).
"""

import hashlib

ABSENT = "__absent__"


class MissingServedModel(ValueError):
    """The response carried no model id; the row must not be written as a label."""


def prompt_sha256(prompt_template: str) -> str:
    return hashlib.sha256(prompt_template.encode("utf-8")).hexdigest()


def require_served(value, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MissingServedModel(f"no served model id in the {where} response: {value!r}")
    return value


def served_openai_compat(resp: dict) -> dict:
    """DeepSeek / any chat/completions JSON envelope -> the two stamps."""
    fp = resp.get("system_fingerprint")
    return {
        "served_model": require_served(resp.get("model"), "chat/completions"),
        "system_fingerprint": fp if isinstance(fp, str) and fp else ABSENT,
    }


def served_gemini(response) -> dict:
    """google-genai ``GenerateContentResponse`` -> stamps (``model_version``)."""
    return {"served_model": require_served(getattr(response, "model_version", None), "Gemini"),
            "system_fingerprint": ABSENT}


def served_sdk_object(response, where: str) -> dict:
    """anthropic ``Message`` / openai ``ChatCompletion`` objects (``.model``)."""
    fp = getattr(response, "system_fingerprint", None)
    return {"served_model": require_served(getattr(response, "model", None), where),
            "system_fingerprint": fp if isinstance(fp, str) and fp else ABSENT}


def served_ollama(resp: dict) -> dict:
    """ollama ``/api/chat`` JSON. ⚠️ ``model`` only echoes the TAG; the content identity
    is the tag's digest from ``/api/tags``, which the caller stamps as ``model_digest``."""
    return {"served_model": require_served(resp.get("model"), "ollama"),
            "system_fingerprint": ABSENT}


def ollama_tag_digest(tags: dict, model: str) -> str:
    """The digest ``/api/tags`` lists for ``model``; raises when the tag is not listed."""
    for m in tags.get("models", []):
        if m.get("name") == model and m.get("digest"):
            return m["digest"]
    raise MissingServedModel(f"ollama /api/tags lists no digest for {model!r}")
