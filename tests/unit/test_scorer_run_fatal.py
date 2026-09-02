"""`scripts/score_deepseek_production.py` must stop on a run-fatal status, and must not
report a catastrophe with exit 0.

2026-09-01, on a real 6,590-row corpus pass: the DeepSeek balance ran out mid-run.
`402 Insufficient Balance` fell through to the generic per-row error branch, so the next pass
made **6,586 doomed calls in 11 minutes**, wrote 6,586 error rows, printed
`Successful: 0  Errors: 6586` — and **exited 0**.

Every test here seeds the positive it looks for. A scorer that silently degrades to all-errors
produces an output file that looks exactly like a completed one to `wc -l`, and the only thing
that caught it downstream was `aggregate_k_runs.py` refusing partial coverage.
"""
import json, subprocess, sys, tempfile, textwrap, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "score_deepseek_production.py"
CONFIG = REPO / "filters" / "human_thriving" / "v8" / "config.yaml"
PROMPT = REPO / "filters" / "human_thriving" / "v8" / "prompt-candidate-tail.md"

# A stub `requests` whose post() returns a scripted status, injected ahead of the real one on
# sys.path. Deliberately NOT mocking call_deepseek itself: the defect lived in how a STATUS
# CODE was routed, so the test has to exercise that routing.
STUB = '''
import json as _json
STATUSES = {statuses!r}
CALLS = {{"n": 0}}

class _Resp:
    def __init__(self, code):
        self.status_code = code
        self.text = "{{\\"error\\":{{\\"message\\":\\"Insufficient Balance\\"}}}}" if code == 402 else "boom"
    def json(self):
        return {{"choices": [{{"message": {{"content": _json.dumps({{
                    "dominant_subject": "d", "scope_verdict": "in_scope", "content_type": "c",
                    "human_wellbeing_impact": {{"score": 5, "evidence": "e"}},
                    "social_cohesion_impact": {{"score": 5, "evidence": "e"}},
                    "justice_rights_impact": {{"score": 5, "evidence": "e"}},
                    "evidence_level": {{"score": 5, "evidence": "e"}},
                    "benefit_distribution": {{"score": 5, "evidence": "e"}},
                    "change_durability": {{"score": 5, "evidence": "e"}}}})}}}}],
                "usage": {{"prompt_tokens": 10, "completion_tokens": 5,
                          "prompt_cache_hit_tokens": 8, "prompt_cache_miss_tokens": 2}}}}

class exceptions:
    class RequestException(Exception):
        pass

def post(url, headers=None, json=None, timeout=None):
    i = CALLS["n"]
    CALLS["n"] += 1
    return _Resp(STATUSES[i] if i < len(STATUSES) else STATUSES[-1])
'''


class TestRunFatal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    _seq = 0

    def _run(self, statuses, n_rows=6, extra=()):
        # ⛔ A FRESH DIRECTORY PER INVOCATION, and it is not tidiness. Reusing one made the
        # 403 case report `FATAL: HTTP 401`: Python served a cached `__pycache__` copy of the
        # previous stub (same path, same coarse mtime), and the scorer additionally RESUMED
        # from the earlier run's output. Two different stale-state bugs in one fixture, and
        # both made the test read as a defect in the code under test.
        TestRunFatal._seq += 1
        d = self.d / f"r{TestRunFatal._seq}"
        d.mkdir()
        (d / "requests.py").write_text(STUB.format(statuses=statuses), encoding="utf-8")
        inp = d / "in.jsonl"
        inp.write_text("\n".join(json.dumps({
            "id": f"a{i}", "title": "t", "url": f"http://e/{i}",
            "content": "A community garden opened in the old rail yard. " * 20,
            "source": "s", "published_date": "2026-01-01", "language": "en"})
            for i in range(n_rows)) + "\n", encoding="utf-8")
        out = d / "out.jsonl"
        env = {"PYTHONPATH": f"{d}:{REPO}", "PATH": "/usr/bin:/bin",
               "HOME": str(d)}
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--input", str(inp), "--output", str(out),
             "--config", str(CONFIG), "--prompt", str(PROMPT), "--concurrency", "1", *extra],
            capture_output=True, text=True, cwd=str(REPO), env=env)
        rows = [json.loads(l) for l in out.read_text().splitlines()] if out.exists() else []
        return r, rows

    def test_a_402_aborts_the_run_and_exits_2(self):
        r, rows = self._run([200, 402], n_rows=6)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("FATAL: HTTP 402", r.stdout)
        self.assertIn("ABORTED, not completed", r.stdout)
        self.assertIn("Insufficient Balance", r.stdout)

    def test_the_abort_stops_further_CALLS_not_just_the_exit_code(self):
        """The 11 wasted minutes were 6,586 requests made after the account was empty."""
        r, rows = self._run([200, 402], n_rows=6)
        after = [x for x in rows if "error" in x and "aborted:" in x["error"]]
        self.assertTrue(after, "rows after the first 402 must be short-circuited, not re-sent")
        self.assertIn("on an earlier row", after[0]["error"])

    def test_401_and_403_take_the_same_path(self):
        for code in (401, 403):
            with self.subTest(code=code):
                r, _ = self._run([200, code], n_rows=4)
                self.assertEqual(r.returncode, 2)
                self.assertIn(f"FATAL: HTTP {code}", r.stdout)

    def test_a_clean_run_still_exits_0(self):
        """The control. Without it a guard that always fails would pass every test above."""
        r, rows = self._run([200], n_rows=4)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("FATAL", r.stdout)
        self.assertEqual(sum("human_thriving_analysis" in x for x in rows), 4)

    def test_ordinary_errors_exit_1_rather_than_0(self):
        """A 404 is a per-row failure, not run-fatal — but it must not read as success."""
        r, rows = self._run([200, 404, 200, 404], n_rows=4)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("row(s) errored", r.stdout)
        self.assertNotIn("FATAL", r.stdout)

    def test_cost_is_not_priced_for_a_non_deepseek_endpoint(self):
        r, _ = self._run([200], n_rows=2,
                         extra=("--base-url", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"))
        self.assertIn("NOT PRICED", r.stdout)
        self.assertNotIn("off-peak /", r.stdout)

    def test_cost_is_priced_for_deepseek(self):
        r, _ = self._run([200], n_rows=2)
        self.assertIn("off-peak /", r.stdout)


if __name__ == "__main__":
    unittest.main()
