"""
Unit tests for the scope-gate stamp in scripts/score_deepseek_production.py.

human_thriving v8's STEP 1 emits `scope_verdict` + `dominant_subject` ahead of the
six dimensions, and a non-`in_scope` verdict zeroes all six. Before 2026-08-29 the
production scorer parsed neither, so every analysis of the gate INFERRED it from
"all six dims <= 2" -- which cannot distinguish a scope refusal from a genuinely
dull in-scope article. #135 (the 13% re-run flip rate) needs the recorded verdict,
not the inference.

The three properties that matter, and the reason each is here:

1. A v8 response's verdict reaches the persisted row *verbatim* (not re-derived).
2. A pre-v8 response yields the sentinel "absent" -- a THIRD state, never confused
   with a verdict. Reading silence as `in_scope` would count every cultural_discovery
   v5 row as in-scope for a gate its prompt never had.
3. The stamp is INERT: adding it does not move a dimension score or the parse
   verdict. Nothing may cap a score on it (cf. content_type_caps, declared in
   filters/uplifting/v7/config.yaml and never applied because v7 ships no
   postfilter.py).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import importlib.util

_SPEC = importlib.util.spec_from_file_location(
    "score_deepseek_production",
    Path(__file__).parent.parent.parent / "scripts" / "score_deepseek_production.py",
)
sdp = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(sdp)

# The real six, from filters/uplifting/v7/config.yaml `scoring.dimensions` and
# filters/human_thriving/v8/prompt-candidate.md's output schema (v8 changes no
# dimension names or weights). Invented names would pass this file just as well and
# would stop telling the reader what the v8 run actually emits.
V8_DIMENSIONS = [
    "human_wellbeing_impact",
    "social_cohesion_impact",
    "justice_rights_impact",
    "evidence_level",
    "benefit_distribution",
    "change_durability",
]


def _resp(payload: dict) -> dict:
    """Shape an OpenAI-compatible chat-completions response around a JSON body."""
    return {
        "choices": [{"message": {"content": json.dumps(payload)}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 10},
    }


def _v8_payload(verdict: str, subject: str, score: float = 6.0) -> dict:
    body = {d: {"score": score, "evidence": "e"} for d in V8_DIMENSIONS}
    body["content_type"] = "news"
    body["dominant_subject"] = subject
    body["scope_verdict"] = verdict
    return body


class TestVerdictIsRecorded:
    def test_in_scope_verdict_survives_parse(self, monkeypatch):
        monkeypatch.setattr(sdp, "DIMENSIONS", V8_DIMENSIONS)
        out = sdp.parse_response(_resp(_v8_payload("in_scope", "farmers restoring land")))
        assert "error" not in out
        assert out["scope_verdict"] == "in_scope"
        assert out["dominant_subject"] == "farmers restoring land"

    def test_refusal_verdict_survives_parse(self, monkeypatch):
        """The case the inference could not see: a refusal, verbatim, not re-derived
        from the zeroed dimensions."""
        monkeypatch.setattr(sdp, "DIMENSIONS", V8_DIMENSIONS)
        payload = _v8_payload("harm_is_subject", "the abuse of a child", score=1.0)
        out = sdp.parse_response(_resp(payload))
        assert out["scope_verdict"] == "harm_is_subject"

    def test_low_scores_alone_do_not_manufacture_a_verdict(self, monkeypatch):
        """All six dims <= 2 with an `in_scope` verdict: the OLD inference reads this
        as a refusal, the stamp reads it as what the oracle actually said."""
        monkeypatch.setattr(sdp, "DIMENSIONS", V8_DIMENSIONS)
        out = sdp.parse_response(_resp(_v8_payload("in_scope", "a dull council meeting", score=1.5)))
        assert out["scope_verdict"] == "in_scope"
        assert all(v <= 2.0 for v in out["dims"].values())


class TestAbsentIsItsOwnState:
    def test_pre_v8_prompt_yields_absent_not_in_scope(self, monkeypatch):
        """cultural_discovery v5 and every other pre-v8 prompt emit neither key."""
        monkeypatch.setattr(sdp, "DIMENSIONS", V8_DIMENSIONS)
        body = {d: {"score": 5.0, "evidence": "e"} for d in V8_DIMENSIONS}
        body["content_type"] = "news"
        out = sdp.parse_response(_resp(body))
        assert out["scope_verdict"] == "absent"
        assert out["scope_verdict"] != "in_scope"
        assert out["dominant_subject"] == ""

    def test_malformed_verdict_is_still_recordable(self, monkeypatch):
        """A non-string emission must not crash the run nor vanish -- it is a
        diagnostic, and an anomaly is exactly what it exists to surface."""
        monkeypatch.setattr(sdp, "DIMENSIONS", V8_DIMENSIONS)
        payload = _v8_payload("in_scope", "x")
        payload["scope_verdict"] = ["in_scope"]
        payload["dominant_subject"] = {"phrase": "y"}
        out = sdp.parse_response(_resp(payload))
        assert isinstance(out["scope_verdict"], str)
        assert isinstance(out["dominant_subject"], str)
        # Truncation applied at record-build time must be safe on the coerced value.
        assert len(out["dominant_subject"][:200]) <= 200


class TestStampIsInert:
    def test_dimension_scores_are_untouched_by_the_verdict(self, monkeypatch):
        """Same dimensions, two different verdicts -> identical dims. The scope rule
        acts through the six scores; the stamp must never be a second lever."""
        monkeypatch.setattr(sdp, "DIMENSIONS", V8_DIMENSIONS)
        a = sdp.parse_response(_resp(_v8_payload("in_scope", "s", score=7.0)))
        b = sdp.parse_response(_resp(_v8_payload("out_of_scope", "s", score=7.0)))
        assert a["dims"] == b["dims"]

    def test_missing_dimension_still_errors_with_a_verdict_present(self, monkeypatch):
        """A present verdict must not rescue a response that is missing a dimension."""
        monkeypatch.setattr(sdp, "DIMENSIONS", V8_DIMENSIONS)
        payload = _v8_payload("in_scope", "s")
        del payload["change_durability"]
        out = sdp.parse_response(_resp(payload))
        assert "error" in out and "change_durability" in out["error"]
