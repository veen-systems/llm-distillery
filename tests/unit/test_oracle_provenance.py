"""#157 / veen-systems/pipeline-atlas#169 phase 1: what scored an oracle label.

The DeepSeek production scorer and batch_scorer are driven end to end in
test_scope_verdict_stamp.py and test_batch_scorer.py; this file covers the shared
module and the three provider branches of scripts/score_ollama_oracle.py."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from ground_truth.oracle_provenance import (
    ABSENT, MissingServedModel, ollama_tag_digest, prompt_sha256, served_openai_compat,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def sool():
    spec = importlib.util.spec_from_file_location(
        "score_ollama_oracle_prov", ROOT / "scripts" / "score_ollama_oracle.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(autouse=True)
def _fresh_run_fatal(request, monkeypatch):
    """RUN_FATAL is a module global: one test's abort must not poison the next."""
    if "sool" in request.fixturenames:
        monkeypatch.setattr(request.getfixturevalue("sool"), "RUN_FATAL",
                            {"status": None, "body": ""})


BODY = json.dumps({"d1": {"score": 5}, "scope_verdict": "in_scope"})


def test_prompt_sha256_is_the_full_digest_of_the_content():
    assert prompt_sha256("abc") == hashlib.sha256(b"abc").hexdigest()


def test_openai_compat_reads_the_response_not_a_default():
    assert served_openai_compat({"model": "m1", "system_fingerprint": "f"}) == \
        {"served_model": "m1", "system_fingerprint": "f"}
    assert served_openai_compat({"model": "m1"})["system_fingerprint"] == ABSENT
    for bad in ({}, {"model": ""}, {"model": None}):
        with pytest.raises(MissingServedModel):
            served_openai_compat(bad)


def test_ollama_digest_is_the_listed_tags_and_a_missing_tag_raises():
    tags = {"models": [{"name": "a:1", "digest": "d_a"}, {"name": "b:2", "digest": "d_b"}]}
    assert ollama_tag_digest(tags, "b:2") == "d_b"
    with pytest.raises(MissingServedModel):
        ollama_tag_digest(tags, "c:3")


@pytest.mark.parametrize("provider,resp,want", [
    ("ollama", {"model": "qwen3:14b", "message": {"content": BODY}},
     ("qwen3:14b", ABSENT)),
    ("deepseek", {"model": "deepseek-flash", "system_fingerprint": "fp9",
                  "choices": [{"message": {"content": BODY}}]},
     ("deepseek-flash", "fp9")),
    ("gemini", {"_text": BODY, "_model_version": "gemini-2.5-flash-x"},
     ("gemini-2.5-flash-x", ABSENT)),
])
def test_each_provider_branch_stamps_what_was_served(sool, provider, resp, want):
    out = sool.parse_response(resp, ["d1"], provider)
    assert (out["served_model"], out["system_fingerprint"]) == want


@pytest.mark.parametrize("provider,resp", [
    ("ollama", {"message": {"content": BODY}}),
    ("deepseek", {"choices": [{"message": {"content": BODY}}]}),
    ("gemini", {"_text": BODY, "_model_version": None}),
])
def test_each_provider_branch_errors_when_nothing_names_the_model(sool, provider, resp):
    out = sool.parse_response(resp, ["d1"], provider)
    assert "Provenance" in out["error"]
    assert sool.RUN_FATAL["status"] == "NO-SERVED-MODEL"   # the run stops, not just the row


def test_the_ollama_record_on_disk_carries_every_stamp(sool, tmp_path, monkeypatch):
    """main() end to end, network stubbed, read back off disk: the parse tests above
    passed with the record-write lines deleted (mutation, 2026-10-16)."""
    import sys
    from types import SimpleNamespace
    prompt = tmp_path / "p.md"
    prompt.write_text(f"Score this.\n{sool.PROMPT_PLACEHOLDER}\n", encoding="utf-8")
    inp = tmp_path / "in.jsonl"
    inp.write_text(json.dumps({"id": "r1", "title": "t", "content": "word " * 80}) + "\n")
    tags = {"models": [{"name": "qwen3:14b", "digest": "sha256:dead"}]}
    monkeypatch.setattr(sool.requests, "get",
                        lambda *a, **k: SimpleNamespace(json=lambda: tags))
    body = json.dumps({d: {"score": 5} for d in sool.DEFAULT_DIMENSIONS})
    monkeypatch.setattr(sool, "call_ollama", lambda *a, **k: {
        "model": "qwen3:14b", "message": {"content": body}})
    monkeypatch.setattr(sys, "argv", ["x", "--model", "qwen3:14b", "--prompt", str(prompt),
                                      "--input", str(inp), "--output-dir", str(tmp_path / "o"),
                                      "--concurrency", "1"])
    try:
        sool.main()
    except SystemExit as e:
        assert not e.code
    rec = json.loads((tmp_path / "o" / "results.jsonl").read_text().splitlines()[0])
    assert rec["prompt_sha256"] == hashlib.sha256(prompt.read_bytes()).hexdigest()
    assert rec["prompt_hash"] == rec["prompt_sha256"][:12]
    assert rec["served_model"] == "qwen3:14b"
    assert rec["model_digest"] == "sha256:dead"
    assert rec["system_fingerprint"] == ABSENT


def test_an_ollama_run_with_no_served_model_stops_and_exits_2(sool, tmp_path, monkeypatch):
    import sys
    from types import SimpleNamespace
    prompt = tmp_path / "p.md"
    prompt.write_text(f"Score this.\n{sool.PROMPT_PLACEHOLDER}\n", encoding="utf-8")
    inp = tmp_path / "in.jsonl"
    inp.write_text("".join(json.dumps({"id": f"r{i}", "title": "t", "content": "word " * 80}) + "\n"
                           for i in range(5)))
    tags = {"models": [{"name": "qwen3:14b", "digest": "sha256:dead"}]}
    monkeypatch.setattr(sool.requests, "get", lambda *a, **k: SimpleNamespace(json=lambda: tags))
    body = json.dumps({d: {"score": 5} for d in sool.DEFAULT_DIMENSIONS})
    calls = []
    monkeypatch.setattr(sool, "call_ollama", lambda *a, **k: calls.append(1) or {
        "message": {"content": body}})                     # no "model" key
    monkeypatch.setattr(sys, "argv", ["x", "--model", "qwen3:14b", "--prompt", str(prompt),
                                      "--input", str(inp), "--output-dir", str(tmp_path / "o"),
                                      "--concurrency", "1"])
    with pytest.raises(SystemExit) as ex:
        sool.main()
    assert ex.value.code == 2
    assert len(calls) == 1


# --- the two detector oracles (junk-gate training labels) --------------------

class _FakeHTTP:
    def __init__(self, envelope):
        self._b = json.dumps(envelope).encode()

    def read(self):
        return self._b


def _envelope(content: dict, model="deepseek-flash", fp="fp_d"):
    env = {"choices": [{"message": {"content": json.dumps(content)}}], "system_fingerprint": fp}
    if model is not None:
        env["model"] = model
    return env


def _violence(monkeypatch, envelope):
    from filters.common.violence_promotion.v1 import oracle as vo
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setattr(vo.urllib.request, "urlopen", lambda *a, **k: _FakeHTTP(envelope))
    return vo.ViolencePromotionOracle()


def test_violence_oracle_rows_carry_the_stamps(monkeypatch, tmp_path):
    o = _violence(monkeypatch, _envelope(
        {"violence_score": 2, "reasoning": "r", "key_signals": []}, model="deepseek-v4-pro"))
    out = tmp_path / "v.jsonl"
    o.score_batch([{"id": "a", "title": "t", "content": "c"}], str(out), workers=1)
    row = json.loads(out.read_text().splitlines()[0])
    assert row["served_model"] == "deepseek-v4-pro"          # from the envelope
    assert row["system_fingerprint"] == "fp_d"
    assert row["prompt_sha256"] == hashlib.sha256(o._user_template.encode()).hexdigest()


def test_violence_oracle_halts_with_no_served_model(monkeypatch, tmp_path):
    o = _violence(monkeypatch, _envelope({"violence_score": 2}, model=None))
    out = tmp_path / "v.jsonl"
    out.write_text("")      # _print_tally reads the file; a halt on row 1 leaves none
    o.score_batch([{"id": f"r{i}", "title": "t", "content": "c"} for i in range(3)],
                  str(out), workers=1)
    assert out.read_text().strip() == ""                      # no label written


def _obit(monkeypatch, envelope):
    import importlib
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    m = importlib.import_module("filters.common.obituary_detector.validation.relabel_deepseek")
    monkeypatch.setattr(m.urllib.request, "urlopen", lambda *a, **k: _FakeHTTP(envelope))
    return m


def test_obituary_relabel_rows_carry_the_stamps(monkeypatch, tmp_path):
    import sys
    m = _obit(monkeypatch, _envelope({"verdict": "obituary", "reason": "r"}))
    inp, out = tmp_path / "in.jsonl", tmp_path / "out.jsonl"
    inp.write_text(json.dumps({"id": "a", "title": "t", "content": "c"}) + "\n")
    monkeypatch.setattr(sys, "argv", ["x", "--in", str(inp), "--out", str(out), "--workers", "1"])
    m.main()
    row = json.loads(out.read_text().splitlines()[0])
    assert (row["served_model"], row["system_fingerprint"]) == ("deepseek-flash", "fp_d")
    assert row["prompt_sha256"] == hashlib.sha256(m.PROMPT.encode()).hexdigest()


def test_obituary_relabel_halts_with_no_served_model(monkeypatch, tmp_path):
    import sys
    m = _obit(monkeypatch, _envelope({"verdict": "obituary", "reason": "r"}, model=None))
    inp, out = tmp_path / "in.jsonl", tmp_path / "out.jsonl"
    inp.write_text("".join(json.dumps({"id": f"r{i}", "title": "t", "content": "c"}) + "\n"
                           for i in range(3)))
    monkeypatch.setattr(sys, "argv", ["x", "--in", str(inp), "--out", str(out), "--workers", "1"])
    m.main()
    assert out.read_text().strip() == ""                      # no label written
