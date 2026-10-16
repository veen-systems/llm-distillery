"""
Unit tests for ground_truth/batch_scorer.py

Tests the error handling components:
- ErrorType enum
- LLMError exception hierarchy
- RetryState dataclass
- extract_json_from_response()
- repair_json()
"""

import json
import pytest
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ground_truth.batch_scorer import (
    ErrorType,
    LLMError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthError,
    LLMResponseError,
    RetryState,
    extract_json_from_response,
    repair_json,
)


class TestErrorType:
    """Tests for ErrorType enum."""

    def test_all_error_types_exist(self):
        """All expected error types should exist."""
        expected = [
            "TIMEOUT", "JSON_PARSE_ERROR", "JSON_EXTRACTION_FAILED",
            "LLM_API_ERROR", "EMPTY_RESPONSE", "RATE_LIMIT", "AUTH_ERROR", "UNKNOWN"
        ]
        for error_type in expected:
            assert hasattr(ErrorType, error_type)

    def test_error_type_values(self):
        """Error types should have string values."""
        assert ErrorType.TIMEOUT.value == "timeout"
        assert ErrorType.RATE_LIMIT.value == "rate_limit"
        assert ErrorType.AUTH_ERROR.value == "auth_error"


class TestLLMExceptionHierarchy:
    """Tests for LLM exception classes."""

    def test_llm_error_base_class(self):
        """LLMError should be catchable and have expected attributes."""
        error = LLMError("test error", ErrorType.UNKNOWN, retryable=True)
        assert str(error) == "test error"
        assert error.error_type == ErrorType.UNKNOWN
        assert error.retryable is True

    def test_llm_timeout_error(self):
        """LLMTimeoutError should have timeout_seconds."""
        error = LLMTimeoutError("timeout after 60s", timeout_seconds=60)
        assert error.error_type == ErrorType.TIMEOUT
        assert error.timeout_seconds == 60
        assert error.retryable is True  # Timeouts are retryable

    def test_llm_rate_limit_error(self):
        """LLMRateLimitError should have retry_after."""
        error = LLMRateLimitError("rate limited", retry_after=30)
        assert error.error_type == ErrorType.RATE_LIMIT
        assert error.retry_after == 30
        assert error.retryable is True

    def test_llm_rate_limit_error_no_retry_after(self):
        """LLMRateLimitError should work without retry_after."""
        error = LLMRateLimitError("rate limited")
        assert error.retry_after is None

    def test_llm_auth_error(self):
        """LLMAuthError should not be retryable."""
        error = LLMAuthError("invalid API key")
        assert error.error_type == ErrorType.AUTH_ERROR
        assert error.retryable is False  # Auth errors are NOT retryable

    def test_llm_response_error(self):
        """LLMResponseError should be retryable."""
        error = LLMResponseError("empty response", ErrorType.EMPTY_RESPONSE)
        assert error.error_type == ErrorType.EMPTY_RESPONSE
        assert error.retryable is True

    def test_exception_hierarchy(self):
        """All LLM errors should be catchable as LLMError."""
        errors = [
            LLMTimeoutError("timeout", 60),
            LLMRateLimitError("rate limit"),
            LLMAuthError("auth error"),
            LLMResponseError("empty", ErrorType.EMPTY_RESPONSE),
        ]
        for error in errors:
            assert isinstance(error, LLMError)
            assert isinstance(error, Exception)


class TestRetryState:
    """Tests for RetryState dataclass."""

    def test_initial_state(self):
        """Initial state should have 0 attempts and retries available."""
        state = RetryState(article_id="test-123", max_attempts=3)
        assert state.article_id == "test-123"
        assert state.current_attempt == 0
        assert state.max_attempts == 3
        assert state.json_repaired is False
        assert state.error_type is None
        assert state.error_message is None

    def test_increment_attempt(self):
        """increment_attempt should increment and return current attempt."""
        state = RetryState(article_id="test", max_attempts=3)
        assert state.increment_attempt() == 1
        assert state.current_attempt == 1
        assert state.increment_attempt() == 2
        assert state.current_attempt == 2

    def test_has_retries_left(self):
        """has_retries_left should track retry availability."""
        state = RetryState(article_id="test", max_attempts=3)
        assert state.has_retries_left() is True

        state.increment_attempt()  # 1
        assert state.has_retries_left() is True

        state.increment_attempt()  # 2
        assert state.has_retries_left() is True

        state.increment_attempt()  # 3
        assert state.has_retries_left() is False

    def test_get_backoff_seconds(self):
        """get_backoff_seconds should return exponential backoff."""
        state = RetryState(article_id="test", max_attempts=5)

        state.increment_attempt()  # attempt 1
        assert state.get_backoff_seconds() == 1  # 2^0

        state.increment_attempt()  # attempt 2
        assert state.get_backoff_seconds() == 2  # 2^1

        state.increment_attempt()  # attempt 3
        assert state.get_backoff_seconds() == 4  # 2^2

        state.increment_attempt()  # attempt 4
        assert state.get_backoff_seconds() == 8  # 2^3

    def test_set_error(self):
        """set_error should record error details."""
        state = RetryState(article_id="test")
        state.set_error(ErrorType.TIMEOUT, "Timed out after 60s")

        assert state.error_type == ErrorType.TIMEOUT
        assert state.error_message == "Timed out after 60s"

    def test_elapsed_time(self):
        """elapsed_time should track time since creation."""
        state = RetryState(article_id="test")
        time.sleep(0.1)  # Wait 100ms
        elapsed = state.elapsed_time()
        assert elapsed >= 0.1
        assert elapsed < 1.0  # Should be less than 1 second

    def test_default_max_attempts(self):
        """Default max_attempts should be 3."""
        state = RetryState(article_id="test")
        assert state.max_attempts == 3


class TestExtractJsonFromResponse:
    """Tests for extract_json_from_response()"""

    def test_clean_json(self):
        """Clean JSON should be extracted as-is."""
        response = '{"score": 7, "reasoning": "good"}'
        result = extract_json_from_response(response)
        assert result is not None
        data = json.loads(result)
        assert data["score"] == 7

    def test_json_with_markdown_code_block(self):
        """JSON in markdown code block should be extracted."""
        response = '''Here is the analysis:
```json
{"score": 8, "tier": "high"}
```
'''
        result = extract_json_from_response(response)
        assert result is not None
        data = json.loads(result)
        assert data["score"] == 8

    def test_json_with_text_before_and_after(self):
        """JSON with surrounding text should be extracted."""
        response = '''I analyzed the article and found:
{"dimensions": {"impact": 7}}
Let me know if you need more details.'''
        result = extract_json_from_response(response)
        assert result is not None
        data = json.loads(result)
        assert "dimensions" in data

    def test_nested_json(self):
        """Nested JSON should be properly extracted."""
        response = '{"outer": {"inner": {"value": 5}}}'
        result = extract_json_from_response(response)
        assert result is not None
        data = json.loads(result)
        assert data["outer"]["inner"]["value"] == 5

    def test_json_with_arrays(self):
        """JSON with arrays should be extracted."""
        response = '{"scores": [1, 2, 3, 4, 5]}'
        result = extract_json_from_response(response)
        assert result is not None
        data = json.loads(result)
        assert data["scores"] == [1, 2, 3, 4, 5]

    def test_no_json_in_response(self):
        """Response without JSON should return original text (caller checks validity)."""
        response = "This is just plain text without any JSON."
        result = extract_json_from_response(response)
        # Returns original text, json.loads() will fail on it
        assert result == response

    def test_empty_response(self):
        """Empty response should return empty string."""
        result = extract_json_from_response("")
        assert result == ""

    def test_json_with_newlines(self):
        """JSON with newlines should be extracted."""
        response = '''{
    "score": 6,
    "reasoning": "multi-line"
}'''
        result = extract_json_from_response(response)
        assert result is not None
        data = json.loads(result)
        assert data["score"] == 6


class TestRepairJson:
    """Tests for repair_json()"""

    def test_valid_json_unchanged(self):
        """Valid JSON should pass through unchanged."""
        json_str = '{"key": "value"}'
        result = repair_json(json_str)
        assert json.loads(result) == {"key": "value"}

    def test_trailing_comma_removed(self):
        """Trailing commas should be removed."""
        json_str = '{"key": "value",}'
        result = repair_json(json_str)
        data = json.loads(result)
        assert data["key"] == "value"

    def test_trailing_comma_in_array(self):
        """Trailing commas in arrays should be removed."""
        json_str = '{"arr": [1, 2, 3,]}'
        result = repair_json(json_str)
        data = json.loads(result)
        assert data["arr"] == [1, 2, 3]

    def test_single_quotes_not_converted(self):
        """Single quotes are NOT converted (not supported by repair_json)."""
        # Note: repair_json focuses on trailing commas and comments,
        # not single-to-double quote conversion
        json_str = "{'key': 'value'}"
        result = repair_json(json_str)
        # Still has single quotes, will fail to parse
        with pytest.raises(json.JSONDecodeError):
            json.loads(result)

    def test_comments_removed(self):
        """JavaScript-style comments should be removed."""
        json_str = '''{"key": "value" // this is a comment
}'''
        result = repair_json(json_str)
        data = json.loads(result)
        assert data["key"] == "value"

    def test_whitespace_handling(self):
        """Extra whitespace should be handled."""
        json_str = '  {  "key"  :  "value"  }  '
        result = repair_json(json_str)
        data = json.loads(result)
        assert data["key"] == "value"

    def test_empty_string(self):
        """Empty string should return empty string."""
        assert repair_json("") == ""

    def test_already_valid_complex_json(self):
        """Complex valid JSON should remain valid."""
        json_str = '{"nested": {"array": [1, 2, 3], "bool": true, "null": null}}'
        result = repair_json(json_str)
        data = json.loads(result)
        assert data["nested"]["bool"] is True


class TestFailedArticlesAreNotReloaded:
    """2026-10-07: two permanently failing articles were re-loaded as 'unscored' for ~6,100 batches (~74k failed
    API calls) because a failure was never recorded. A failed id is now skipped for the rest of the run."""

    def _scorer(self):
        from ground_truth.batch_scorer import GenericBatchScorer
        s = object.__new__(GenericBatchScorer)  # the loader needs only state and the failed set
        s.state = {"processed": ["done"]}
        return s

    def test_failed_ids_are_skipped_by_the_loader(self, tmp_path):
        src = tmp_path / "a.jsonl"
        src.write_text("".join(json.dumps({"id": i, "title": "t", "content": "x"}) + "\n" for i in ("done", "bad", "ok")))
        s = self._scorer()
        assert [a["id"] for a in s.load_unscored_articles([str(src)], batch_size=10)] == ["bad", "ok"]
        s._failed_this_run().add("bad")
        assert [a["id"] for a in s.load_unscored_articles([str(src)], batch_size=10)] == ["ok"]
        s.state["processed"].append("ok")
        assert s.load_unscored_articles([str(src)], batch_size=10) == []  # the run can end

    def test_process_batch_records_a_failure(self, tmp_path):
        """The other half: process_batch must put a failed article in the per-run set (review 2026-10-08: the
        loader test alone passed with the recording line deleted)."""
        import logging
        s = self._scorer()
        s.state = {"processed": [], "total_scored": 0, "batches_completed": 0}
        s.output_dir, s.logger, s.llm_provider, s.filter_name = tmp_path, logging.getLogger("t"), "x", "x"
        s.analyze_article = lambda article: None   # a permanent failure
        s._save_state = lambda: None
        r = s.process_batch([{"id": "bad", "title": "t", "content": "x"}], 1)
        assert r["articles_failed"] == 1 and "bad" in s._failed_this_run()


class TestOracleProvenance:
    """#157 / pipeline-atlas#169 phase 1: a Gemini label names the FULL prompt digest
    and the model the provider SERVED (`model_version`), not the one requested."""

    def _scorer(self, tmp_path, model_version):
        import logging
        from types import SimpleNamespace
        from ground_truth.batch_scorer import GenericBatchScorer
        from ground_truth.oracle_provenance import prompt_sha256
        s = object.__new__(GenericBatchScorer)
        s.llm_provider, s._gemini_model, s.thinking_budget = "gemini-flash", "gemini-2.5-flash", 0
        s.filter_name, s.filter_version = "x", "1.0"
        s.prompt_sha256 = prompt_sha256("TEMPLATE")
        s.prompt_hash = s.prompt_sha256[:12]
        s.canary_stamp = {"verdict": "no-set"}
        s.output_dir, s.logger = tmp_path, logging.getLogger("t")
        s.metrics_log_path = tmp_path / "metrics.jsonl"
        s.session_stats = {"articles_attempted": 0, "articles_succeeded": 0, "articles_failed": 0,
                           "total_retries": 0, "errors_by_type": {}, "total_processing_time": 0.0}
        s.build_prompt = lambda article: "p"
        reply = SimpleNamespace(text='{"d": {"score": 5}}', model_version=model_version)
        s.llm_client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kw: reply))
        return s

    def test_the_served_model_comes_from_the_response(self, tmp_path):
        a = self._scorer(tmp_path, "gemini-2.5-flash-preview-09-2026").analyze_article({"id": "1"})
        assert a["served_model"] == "gemini-2.5-flash-preview-09-2026"   # not the requested id
        assert a["system_fingerprint"] == "__absent__"
        assert len(a["prompt_sha256"]) == 64 and a["prompt_sha256"].startswith(a["prompt_hash"])

    def test_no_model_version_STOPS_THE_RUN_after_ONE_call(self, tmp_path):
        """A missing model id is a property of the endpoint: a per-row failure would
        bill every row, and again on every resume (review 2026-10-16)."""
        from ground_truth.oracle_provenance import MissingServedModel
        s = self._scorer(tmp_path, None)
        calls = []
        inner = s.llm_client.models.generate_content
        s.llm_client.models.generate_content = lambda **kw: calls.append(1) or inner(**kw)
        with pytest.raises(MissingServedModel):
            s.analyze_article({"id": "1"})
        assert len(calls) == 1          # not retried: each retry is billed and identical
