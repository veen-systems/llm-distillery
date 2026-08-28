"""
Unit tests for the scope-gate stamp in scripts/score_deepseek_production.py.

human_thriving v8's STEP 1 emits `scope_verdict` + `dominant_subject` ahead of the
six dimensions, and a non-`in_scope` verdict zeroes all six. Before 2026-08-29 the
production scorer parsed neither, so every analysis of the gate INFERRED it from
"all six dims <= 2" -- which cannot distinguish a scope refusal from a genuinely
dull in-scope article. #135 needs the recorded verdict, not the inference.

⚠️ HISTORY, because it is the reason for the shape of this file. The first version
tested `parse_response` ONLY. A review on 2026-08-29 seeded two mutations on the
RECORD-WRITE lines -- deleting the `analysis["scope_verdict"] = ...` assignment, and
narrowing `[:200]` to `[:20]` -- and BOTH left the suite green. The thing this file
exists to prevent, the stamp not reaching the persisted row, passed. Two assertions
were also tautological (`isinstance(x, str)` after an unconditional `str()`).
`TestRecordWrite` closes that: it drives `main()` end to end with the network
stubbed and asserts on bytes read back off disk.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

_SPEC = importlib.util.spec_from_file_location(
    "score_deepseek_production", ROOT / "scripts" / "score_deepseek_production.py")
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


def _v8_payload(verdict="in_scope", subject="a phrase", score: float = 6.0) -> dict:
    body = {d: {"score": score, "evidence": "e"} for d in V8_DIMENSIONS}
    body["content_type"] = "news"
    body["dominant_subject"] = subject
    body["scope_verdict"] = verdict
    return body


@pytest.fixture
def v8_dims(monkeypatch):
    monkeypatch.setattr(sdp, "DIMENSIONS", V8_DIMENSIONS)


class TestVerdictIsRecorded:
    def test_in_scope_verdict_survives_parse(self, v8_dims):
        out = sdp.parse_response(_resp(_v8_payload("in_scope", "farmers restoring land")))
        assert "error" not in out
        assert out["scope_verdict"] == "in_scope"
        assert out["dominant_subject"] == "farmers restoring land"

    def test_refusal_verdict_survives_parse(self, v8_dims):
        """The case the inference could not see: a refusal, verbatim, not re-derived
        from the zeroed dimensions."""
        out = sdp.parse_response(_resp(_v8_payload("harm_is_subject", "the abuse of a child", 1.0)))
        assert out["scope_verdict"] == "harm_is_subject"

    def test_low_scores_alone_do_not_manufacture_a_verdict(self, v8_dims):
        """All six dims <= 2 with an `in_scope` verdict: the OLD inference reads this
        as a refusal, the stamp reads it as what the oracle actually said."""
        out = sdp.parse_response(_resp(_v8_payload("in_scope", "a dull council meeting", 1.5)))
        assert out["scope_verdict"] == "in_scope"
        assert all(v <= 2.0 for v in out["dims"].values())


class TestTheFourStatesAreDistinguishable:
    """The sentinel must not be a value the model can emit, and each non-verdict
    state must be its own string. `str(parsed.get(k, "absent"))` failed both."""

    def test_key_absent_is_its_own_state(self, v8_dims):
        """cultural_discovery v5 and every other pre-v8 prompt emit neither key."""
        body = {d: {"score": 5.0, "evidence": "e"} for d in V8_DIMENSIONS}
        body["content_type"] = "news"
        out = sdp.parse_response(_resp(body))
        assert out["scope_verdict"] == sdp.VERDICT_ABSENT
        assert out["dominant_subject"] == ""

    def test_a_model_emitting_absent_does_not_look_like_silence(self, v8_dims):
        """The defect that motivated the sentinel change: with "absent" as the
        default, this row was indistinguishable from a pre-v8 prompt."""
        out = sdp.parse_response(_resp(_v8_payload("absent")))
        assert out["scope_verdict"] == "absent"
        assert out["scope_verdict"] != sdp.VERDICT_ABSENT

    def test_json_null_is_not_a_refusal(self, v8_dims):
        """`str(None)` gave "None", which every `v == "in_scope"` test reads as a
        refusal -- a confidently wrong label, worse than a missing one."""
        payload = _v8_payload()
        payload["scope_verdict"] = None
        payload["dominant_subject"] = None
        out = sdp.parse_response(_resp(payload))
        assert out["scope_verdict"] == sdp.VERDICT_NULL
        assert out["scope_verdict"] not in ("None", sdp.VERDICT_ABSENT, "in_scope")
        assert out["dominant_subject"] == ""

    def test_non_string_emission_is_flagged_not_stringified(self, v8_dims):
        payload = _v8_payload()
        payload["scope_verdict"] = ["in_scope"]
        payload["dominant_subject"] = {"phrase": "y"}
        out = sdp.parse_response(_resp(payload))
        assert out["scope_verdict"] == sdp.VERDICT_MALFORMED
        assert out["dominant_subject"] == ""

    def test_all_four_states_are_pairwise_distinct(self, v8_dims):
        seen = set()
        for payload, _ in (
                (_v8_payload("in_scope"), "verdict"),
                ({**_v8_payload(), "scope_verdict": None}, "null"),
                ({**_v8_payload(), "scope_verdict": 3}, "malformed"),
        ):
            seen.add(sdp.parse_response(_resp(payload))["scope_verdict"])
        body = {d: {"score": 5.0, "evidence": "e"} for d in V8_DIMENSIONS}
        seen.add(sdp.parse_response(_resp(body))["scope_verdict"])
        assert len(seen) == 4, seen


class TestTruncation:
    def test_dominant_subject_is_truncated_at_parse(self, v8_dims):
        """Truncation lives in parse_response so it has ONE home and a test can
        reach it. It used to live inline at the record write, where nothing could."""
        out = sdp.parse_response(_resp(_v8_payload(subject="x" * 500)))
        assert len(out["dominant_subject"]) == 200


class TestStampIsInert:
    def test_dimension_scores_are_untouched_by_the_verdict(self, v8_dims):
        """Same dimensions, two different verdicts -> identical dims. The scope rule
        acts through the six scores; the stamp must never be a second lever."""
        a = sdp.parse_response(_resp(_v8_payload("in_scope", "s", 7.0)))
        b = sdp.parse_response(_resp(_v8_payload("out_of_scope", "s", 7.0)))
        assert a["dims"] == b["dims"]

    def test_missing_dimension_still_errors_with_a_verdict_present(self, v8_dims):
        """A present verdict must not rescue a response missing a dimension."""
        payload = _v8_payload()
        del payload["change_durability"]
        out = sdp.parse_response(_resp(payload))
        assert "error" in out and "change_durability" in out["error"]


class TestRecordWrite:
    """Drives main() end to end with the network stubbed, and asserts on the bytes
    read back off disk. Everything above this class passed while the record-write
    lines were deleted."""

    def _run(self, tmp_path, monkeypatch, payload):
        art = {
            "id": "test_row_1",
            "title": "A clinic reopens",
            "content": ("A community clinic in the eastern district reopened this week after "
                        "eighteen months of repairs funded by local subscriptions. Staff say "
                        "roughly four thousand residents had been travelling to the next "
                        "province for routine care. The nursing rota is now filled and the "
                        "pharmacy has been restocked. " * 3),
            "url": "https://example.org/a", "source": "example.org",
            "published_date": "2026-08-29", "language": "en",
        }
        inp, outp = tmp_path / "in.jsonl", tmp_path / "out.jsonl"
        inp.write_text(json.dumps(art) + "\n", encoding="utf-8")
        monkeypatch.setattr(sdp, "get_deepseek_key", lambda *a, **k: "sk-test")
        monkeypatch.setattr(sdp, "call_deepseek", lambda *a, **k: _resp(payload))
        monkeypatch.setattr(sys, "argv", [
            "score_deepseek_production.py",
            "--input", str(inp), "--output", str(outp),
            "--config", str(ROOT / "filters" / "uplifting" / "v7" / "config.yaml"),
            "--prompt", str(ROOT / "filters" / "human_thriving" / "v8" / "prompt-candidate.md"),
            "--concurrency", "1",
        ])
        sdp.main()
        return json.loads(outp.read_text(encoding="utf-8").strip())

    def test_both_stamps_reach_the_persisted_row(self, tmp_path, monkeypatch):
        rec = self._run(tmp_path, monkeypatch, _v8_payload("out_of_scope", "a funding round"))
        analysis = rec["uplifting_analysis"]
        assert analysis["scope_verdict"] == "out_of_scope"
        assert analysis["dominant_subject"] == "a funding round"

    def test_truncation_reaches_the_persisted_row(self, tmp_path, monkeypatch):
        rec = self._run(tmp_path, monkeypatch, _v8_payload(subject="y" * 500))
        assert len(rec["uplifting_analysis"]["dominant_subject"]) == 200

    def test_the_persisted_row_names_the_prompt_that_produced_it(self, tmp_path, monkeypatch):
        """Both arms of the 2026-08-29 two-prompt run persisted an identical
        filter_version while running DIFFERENT prompts that produced DIFFERENT
        labels. Arm identity rested on the operator's filenames alone."""
        rec = self._run(tmp_path, monkeypatch, _v8_payload())
        analysis = rec["uplifting_analysis"]
        assert analysis["prompt_file"] == "prompt-candidate.md"
        assert len(analysis["prompt_hash"]) == 12
        assert analysis["prompt_hash"] != "unset"

    def test_a_different_prompt_gives_a_different_hash(self, tmp_path, monkeypatch):
        """The property that actually distinguishes the two arms."""
        import hashlib
        a = (ROOT / "filters/human_thriving/v8/prompt-candidate.md").read_text(encoding="utf-8")
        b = (ROOT / "filters/human_thriving/v8/prompt-candidate-tail.md").read_text(encoding="utf-8")
        ha = hashlib.sha256(a.encode()).hexdigest()[:12]
        hb = hashlib.sha256(b.encode()).hexdigest()[:12]
        assert ha != hb
        rec = self._run(tmp_path, monkeypatch, _v8_payload())
        assert rec["uplifting_analysis"]["prompt_hash"] == ha
