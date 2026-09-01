"""Tests for scripts/dataset/rehydrate_adverse.py against a SYNTHETIC archive.

The tool restores full article text to a set whose rows are 300-char excerpts, and the whole
risk is a WRONG rejoin: ids are reused when a source rewrites a URL, and the monthly archives
span months. So the tests that matter are the ones asserting it REFUSES — a tool that quietly
grafts the wrong article onto an adverse row produces a file that looks exactly like a correct
one, and Gate B-A is judged on it.
"""
import json, subprocess, sys, tarfile, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "dataset" / "rehydrate_adverse.py"
BODY = ("Elle s'appelle Sihem Djoudi, a fait ses etudes de medecine en Algerie.\n"
        "Cette structure est une clinique. " + "x" * 400)


def excerpt_row(rid, full, n=300, collapse=False):
    head = full[:n]
    if collapse:
        head = " ".join(head.split())
    return {"id": rid, "title": "t", "url": f"http://e/{rid}", "label": "adverse",
            "content": head, "content_excerpt": True, "content_original_length": len(full)}


class TestRehydrateAdverse(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.filtered = self.d / "filtered" / "uplifting"
        self.filtered.mkdir(parents=True)
        self.archived = self.d / "archived"
        self.archived.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def live(self, rows, name="filtered_20260822_120000.jsonl"):
        (self.filtered / name).write_text(
            "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    def archive(self, rows, month="2026-08", lens="belonging"):
        inner = self.d / f"nexusmind_{month}" / lens
        inner.mkdir(parents=True, exist_ok=True)
        f = inner / "scored.jsonl"
        f.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        with tarfile.open(self.archived / f"nexusmind_{month}.tar.gz", "w:gz") as tf:
            tf.add(f, arcname=f"nexusmind_{month}/{lens}/scored.jsonl")

    def run_tool(self, inp, out, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--in", str(inp), "--out", str(out),
             "--filtered-root", str(self.d / "filtered"),
             "--archive-root", str(self.archived), *extra],
            capture_output=True, text=True)

    def _write_in(self, rows):
        p = self.d / "in.jsonl"
        p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        return p

    def test_recovers_from_the_live_window(self):
        self.live([{"id": "a", "content": BODY}])
        inp = self._write_in([excerpt_row("a", BODY)])
        out = self.d / "out.jsonl"
        r = self.run_tool(inp, out)
        self.assertEqual(r.returncode, 0, r.stderr)
        got = json.loads(out.read_text())
        self.assertEqual(got["content"], BODY)
        self.assertFalse(got["content_excerpt"])
        self.assertIn("live:", got["content_rehydrated_from"])

    def test_recovers_from_a_monthly_tarball_when_the_window_has_rolled(self):
        """The premise this tool exists to correct: 'the window has rolled, so it is gone'."""
        self.live([{"id": "zzz", "content": "unrelated"}])
        self.archive([{"id": "a", "content": BODY}])
        inp = self._write_in([excerpt_row("a", BODY)])
        out = self.d / "out.jsonl"
        r = self.run_tool(inp, out)
        self.assertEqual(r.returncode, 0, r.stderr)
        got = json.loads(out.read_text())
        self.assertEqual(got["content"], BODY)
        self.assertIn("nexusmind_2026-08.tar.gz", got["content_rehydrated_from"])

    def test_whitespace_collapsed_excerpt_still_matches(self):
        """Excerpting collapsed newlines to spaces; a strict startswith rejected the RIGHT row."""
        self.live([{"id": "a", "content": BODY}])
        inp = self._write_in([excerpt_row("a", BODY, collapse=True)])
        out = self.d / "out.jsonl"
        r = self.run_tool(inp, out)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(out.read_text())["content"], BODY)
        # and the text written back keeps its real newlines, not the collapsed form
        self.assertIn("\n", json.loads(out.read_text())["content"])

    def test_length_mismatch_is_refused(self):
        self.live([{"id": "a", "content": BODY + "MORE"}])
        inp = self._write_in([excerpt_row("a", BODY)])
        out = self.d / "out.jsonl"
        r = self.run_tool(inp, out)
        self.assertEqual(r.returncode, 1)
        self.assertIn("could not be rehydrated", r.stderr)
        self.assertFalse(out.exists())

    def test_same_id_different_article_is_refused(self):
        """An id is not proof of identity — sources rewrite URLs and ids get reused."""
        other = "Completely different article of the very same length. " + "y" * (len(BODY) - 54)
        self.assertEqual(len(other), len(BODY))
        self.live([{"id": "a", "content": other}])
        inp = self._write_in([excerpt_row("a", BODY)])
        out = self.d / "out.jsonl"
        r = self.run_tool(inp, out)
        self.assertEqual(r.returncode, 1)
        self.assertIn("prefix-mismatch", r.stderr)
        self.assertFalse(out.exists())

    def test_allow_missing_lets_a_known_gap_through(self):
        self.live([{"id": "a", "content": BODY}])
        inp = self._write_in([excerpt_row("a", BODY), excerpt_row("b", BODY)])
        out = self.d / "out.jsonl"
        r = self.run_tool(inp, out, "--allow-missing", "1")
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = {json.loads(l)["id"]: json.loads(l) for l in out.read_text().splitlines()}
        self.assertFalse(rows["a"]["content_excerpt"])
        self.assertTrue(rows["b"]["content_excerpt"], "the unrecovered row stays marked")

    def test_a_set_with_no_excerpts_refuses_rather_than_silently_doing_nothing(self):
        inp = self._write_in([{"id": "a", "content": BODY, "content_excerpt": False}])
        r = self.run_tool(inp, self.d / "out.jsonl")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Nothing to rehydrate", r.stderr)

    def test_an_excerpt_without_original_length_refuses(self):
        """Without it there is nothing to verify a rejoin against."""
        row = excerpt_row("a", BODY)
        del row["content_original_length"]
        inp = self._write_in([row])
        r = self.run_tool(inp, self.d / "out.jsonl")
        self.assertEqual(r.returncode, 1)
        self.assertIn("content_original_length", r.stderr)


if __name__ == "__main__":
    unittest.main()
