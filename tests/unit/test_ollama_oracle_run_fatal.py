"""`scripts/score_ollama_oracle.py`'s DeepSeek path must stop on a run-fatal status.

2026-10-12: it aborted on 401/403 via `raise SystemExit` (which a ThreadPoolExecutor does not
honour until it has drained every queued future) and not at all on 402, so an exhausted
balance meant three retries per queued article. Same class as `test_scorer_run_fatal.py`.
No network: `requests.post` is replaced in-process.
"""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "score_ollama_oracle.py"


class _Resp:
    def __init__(self, code):
        self.status_code = code
        self.text = '{"error":{"message":"Insufficient Balance"}}' if code == 402 else "boom"

    def json(self):
        return {"choices": [{"message": {"content": "{}"}}]}


@pytest.fixture
def mod(monkeypatch):
    spec = importlib.util.spec_from_file_location("score_ollama_oracle_t", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.setattr(m.time, "sleep", lambda s: None)
    return m


def _stub(mod, monkeypatch, codes):
    calls = []

    def post(*a, **k):
        calls.append(1)
        return _Resp(codes[min(len(calls) - 1, len(codes) - 1)])
    monkeypatch.setattr(mod.requests, "post", post)
    return calls


@pytest.mark.parametrize("code", [401, 402, 403])
def test_a_fatal_status_is_one_call_and_stops_every_later_row(mod, monkeypatch, code):
    calls = _stub(mod, monkeypatch, [code])
    first = mod.call_deepseek("deepseek-chat", "p", "k")
    assert "error" in first and len(calls) == 1          # no retry against the account
    assert mod.RUN_FATAL["status"] == code
    for _ in range(5):                                    # the rest of the queue
        assert "aborted" in mod.call_deepseek("deepseek-chat", "p", "k")["error"]
    assert len(calls) == 1                                # ...sends nothing


def test_a_transient_error_is_still_retried_and_not_fatal(mod, monkeypatch):
    calls = _stub(mod, monkeypatch, [500, 500, 200])
    assert "error" not in mod.call_deepseek("deepseek-chat", "p", "k")
    assert len(calls) == 3 and mod.RUN_FATAL["status"] is None
