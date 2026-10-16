"""Tests for scripts/oracle/aggregate_k_runs.py.

The script exists because `average_oracle_runs.py` joins on `url`, DELETES `scope_verdict`,
and silently intersects partial runs. Every test here seeds the positive it looks for: an
aggregator that quietly drops rows produces a label file that looks exactly like one that
kept them, so the tests that matter are the ones asserting it REFUSES.

⚠️ The flip-rate line is the point of the script, not decoration — #135 measured the v8 scope
gate as a Bernoulli that zeroes all six dimensions, and `1/√k` does not describe it.
"""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "oracle" / "aggregate_k_runs.py"
CONFIG = REPO / "filters" / "human_thriving" / "v8" / "config.yaml"
DIMS = ["human_wellbeing_impact", "social_cohesion_impact", "justice_rights_impact",
        "evidence_level", "benefit_distribution", "change_durability"]


def row(rid, verdict, scores, field="human_thriving_analysis", **stamps):
    a = {d: {"score": s, "evidence": "q"} for d, s in zip(DIMS, scores)}
    a.update({"scope_verdict": verdict, "dominant_subject": "x", "content_type": "y",
              "filter_version": "8.0-deepseek", "analyzed_by": "deepseek-chat",
              "prompt_hash": "abc123", "prompt_file": "p.md"})
    a.update(stamps)
    return {"id": rid, "title": "t", "url": f"http://e/{rid}", "content": "c", field: a}


def write(p, rows):
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return str(p)


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          capture_output=True, text=True, cwd=str(REPO))


class TestAggregateKRuns(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _runs(self, spec):
        """spec: list of per-run [(id, verdict, scores), ...]"""
        return [write(self.d / f"r{i}.jsonl", [row(*t) for t in rs])
                for i, rs in enumerate(spec, 1)]

    def test_stable_rows_average_and_report_zero_flips(self):
        s = [6.0] * 6
        paths = self._runs([[("a", "in_scope", s)], [("a", "in_scope", [7.0] * 6)],
                            [("a", "in_scope", [8.0] * 6)]])
        out = self.d / "o.jsonl"
        r = run("--runs", *paths, "--config", str(CONFIG), "--out", str(out))
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn("FLIP RATE: 0/1", r.stdout)
        a = json.loads(out.read_text())["human_thriving_analysis"]
        self.assertEqual(a["human_wellbeing_impact"], 7.0)
        self.assertFalse(a["scope_flipped"])
        self.assertEqual(a["weighted_mean_all"], a["weighted_mean_major"])

    def test_a_gate_flip_is_reported_and_the_two_aggregates_diverge(self):
        hi, lo = [8.0] * 6, [1.0] * 6
        paths = self._runs([[("a", "in_scope", hi)], [("a", "harm_is_subject", lo)],
                            [("a", "harm_is_subject", lo)]])
        out = self.d / "o.jsonl"
        r = run("--runs", *paths, "--config", str(CONFIG), "--out", str(out))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("FLIP RATE: 1/1", r.stdout)
        a = json.loads(out.read_text())["human_thriving_analysis"]
        self.assertTrue(a["scope_flipped"])
        self.assertEqual(a["scope_verdict"], "harm_is_subject")          # majority
        self.assertEqual(a["scope_verdicts_per_run"],
                         ["in_scope", "harm_is_subject", "harm_is_subject"])
        # the whole reason the script exists: the choice moves the label
        self.assertAlmostEqual(a["weighted_mean_all"], (8 + 1 + 1) / 3, places=3)
        self.assertAlmostEqual(a["weighted_mean_major"], 1.0, places=3)
        self.assertEqual(len(a["runs"]), 3)                              # evidence kept

    def test_majority_mode_puts_the_majority_mean_on_the_dimension_keys(self):
        hi, lo = [8.0] * 6, [1.0] * 6
        paths = self._runs([[("a", "in_scope", hi)], [("a", "harm_is_subject", lo)],
                            [("a", "harm_is_subject", lo)]])
        o1, o2 = self.d / "all.jsonl", self.d / "maj.jsonl"
        run("--runs", *paths, "--config", str(CONFIG), "--out", str(o1))
        run("--runs", *paths, "--config", str(CONFIG), "--out", str(o2), "--aggregate", "majority")
        a1 = json.loads(o1.read_text())["human_thriving_analysis"]
        a2 = json.loads(o2.read_text())["human_thriving_analysis"]
        self.assertAlmostEqual(a1["human_wellbeing_impact"], 10 / 3, places=3)
        self.assertAlmostEqual(a2["human_wellbeing_impact"], 1.0, places=3)
        self.assertEqual(a1["aggregate_used"], "all")
        self.assertEqual(a2["aggregate_used"], "majority")

    def test_partial_coverage_refuses_and_writes_nothing(self):
        s = [5.0] * 6
        paths = self._runs([[("a", "in_scope", s), ("b", "in_scope", s)],
                            [("a", "in_scope", s), ("b", "in_scope", s)],
                            [("a", "in_scope", s)]])                      # b missing
        out = self.d / "o.jsonl"
        r = run("--runs", *paths, "--config", str(CONFIG), "--out", str(out))
        self.assertEqual(r.returncode, 1)
        self.assertIn("not in every run", r.stdout + r.stderr)
        self.assertFalse(out.exists(), "a refusal must not leave a partial label file")

    def test_allow_missing_lets_a_partial_row_through_when_asked(self):
        s = [5.0] * 6
        paths = self._runs([[("a", "in_scope", s), ("b", "in_scope", s)],
                            [("a", "in_scope", s), ("b", "in_scope", s)],
                            [("a", "in_scope", s)]])
        out = self.d / "o.jsonl"
        r = run("--runs", *paths, "--config", str(CONFIG), "--out", str(out), "--allow-missing", "1")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(len(out.read_text().strip().splitlines()), 1)    # only the common id

    def test_single_run_refuses(self):
        paths = self._runs([[("a", "in_scope", [5.0] * 6)]])
        r = run("--runs", *paths, "--config", str(CONFIG), "--out", str(self.d / "o.jsonl"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("at least 2 runs", r.stdout + r.stderr)

    def test_wrong_config_names_the_field_instead_of_writing_zeros(self):
        """The failure `prepare_data.py` turns into 0 examples with exit 0 must be loud HERE."""
        paths = self._runs([[("a", "in_scope", [5.0] * 6)], [("a", "in_scope", [5.0] * 6)]])
        r = run("--runs", *paths, "--config", str(REPO / "filters/uplifting/v7/config.yaml"),
                "--out", str(self.d / "o.jsonl"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("uplifting_analysis", r.stdout + r.stderr)

    def test_a_missing_dimension_refuses_rather_than_defaulting_to_zero(self):
        """prepare_data defaults a missing dimension to 0 — a wrong label, not a missing one."""
        r1 = [row("a", "in_scope", [5.0] * 6)]
        r2 = [row("a", "in_scope", [5.0] * 6)]
        del r2[0]["human_thriving_analysis"]["change_durability"]
        paths = [write(self.d / "r1.jsonl", r1), write(self.d / "r2.jsonl", r2)]
        r = run("--runs", *paths, "--config", str(CONFIG), "--out", str(self.d / "o.jsonl"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("change_durability", r.stdout + r.stderr)
        self.assertIn("silently score it 0", r.stdout + r.stderr)

    def test_error_and_skipped_rows_are_excluded_not_averaged(self):
        s = [5.0] * 6
        good = [row("a", "in_scope", s), {"id": "b", "error": "boom"}]
        paths = [write(self.d / "r1.jsonl", good),
                 write(self.d / "r2.jsonl", [row("a", "in_scope", s), {"id": "b", "skipped": "junk"}])]
        out = self.d / "o.jsonl"
        r = run("--runs", *paths, "--config", str(CONFIG), "--out", str(out))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("1 error", r.stdout)
        self.assertIn("1 skipped", r.stdout)
        self.assertEqual(len(out.read_text().strip().splitlines()), 1)

    def test_join_is_by_id_not_url(self):
        """average_oracle_runs.py keys by url; two rows sharing a url must not collide."""
        s = [4.0] * 6
        a, b = row("a", "in_scope", s), row("b", "in_scope", [6.0] * 6)
        a["url"] = b["url"] = "http://same"
        paths = [write(self.d / "r1.jsonl", [a, b]), write(self.d / "r2.jsonl", [a, b])]
        out = self.d / "o.jsonl"
        r = run("--runs", *paths, "--config", str(CONFIG), "--out", str(out))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        ids = {json.loads(l)["id"] for l in out.read_text().strip().splitlines()}
        self.assertEqual(ids, {"a", "b"}, "a shared url must not merge two articles")



class TestProvenance(unittest.TestCase):
    """#157: the k runs must be ONE labelling function. Each refusal is seeded."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _agg(self, *per_run_stamps):
        paths = [write(self.d / f"r{i}.jsonl", [row("a", "in_scope", [6.0] * 6, **st)])
                 for i, st in enumerate(per_run_stamps, 1)]
        out = self.d / "o.jsonl"
        r = run("--runs", *paths, "--config", str(CONFIG), "--out", str(out))
        return r, out

    def test_two_served_models_are_refused_with_nothing_written(self):
        r, out = self._agg({"served_model": "deepseek-flash"}, {"served_model": "deepseek-v4-pro"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("served_model", r.stderr + r.stdout)
        self.assertFalse(out.exists())

    def test_two_prompts_are_refused(self):
        r, out = self._agg({"prompt_hash": "aaaaaaaaaaaa"}, {"prompt_hash": "bbbbbbbbbbbb"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("prompt_hash", r.stderr + r.stdout)
        self.assertFalse(out.exists())

    def test_a_pre_157_run_beside_a_stamped_one_is_PARTIAL_in_either_order(self):
        """Not a disagreement, so not refused -- but the row must not claim the stamped
        run's provenance for a mean half made of an unstamped run (review 2026-10-16:
        the stamp used to be run 1's, so it flipped with the order of --runs)."""
        for order in (({}, {"served_model": "deepseek-flash"}),
                      ({"served_model": "deepseek-flash"}, {})):
            r, out = self._agg(*order)
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            a = json.loads(out.read_text())["human_thriving_analysis"]
            self.assertEqual(a["served_model"], "__partial__")
            self.assertEqual(a["prompt_sha256"], "__absent__")

    def test_NO_provenance_field_depends_on_the_order_of_runs(self):
        """Round 2 of the 2026-10-16 review: prompt_hash survived the first fix. Every
        provenance field, both orders, one stamped run and one bare run."""
        stamped = {"prompt_hash": "abc123abc123", "prompt_file": "q.md", "analyzed_by": "x",
                   "filter_version": "9", "served_model": "m", "system_fingerprint": "fp"}
        bare = {"prompt_hash": "", "prompt_file": "", "analyzed_by": "", "filter_version": ""}
        outs = []
        for order in ((stamped, bare), (bare, stamped)):
            r, out = self._agg(*order)
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            a = json.loads(out.read_text())["human_thriving_analysis"]
            outs.append({k: a[k] for k in ("prompt_hash", "prompt_file", "analyzed_by",
                                           "filter_version", "served_model",
                                           "system_fingerprints")})
        self.assertEqual(outs[0], outs[1])
        self.assertEqual(outs[0]["prompt_hash"], "__partial__")
        self.assertEqual(outs[0]["system_fingerprints"], ["__absent__", "fp"])

    def test_two_full_digests_with_one_12_hex_prefix_are_refused(self):
        r, out = self._agg({"prompt_sha256": "abc123" + "0" * 58},
                           {"prompt_sha256": "abc123" + "1" * 58})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("prompt_sha256", r.stderr + r.stdout)

    def test_a_malformed_stamp_is_refused_with_the_message_not_a_traceback(self):
        r, out = self._agg({"served_model": ["x"]}, {"served_model": "deepseek-flash"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("FATAL", r.stderr + r.stdout)
        self.assertNotIn("Traceback", r.stderr)

    def test_a_fingerprint_split_is_kept_and_counted_not_refused(self):
        r, out = self._agg({"served_model": "deepseek-flash", "system_fingerprint": "fp1",
                            "prompt_sha256": "f" * 64},
                           {"served_model": "deepseek-flash", "system_fingerprint": "fp2",
                            "prompt_sha256": "f" * 64})
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn("1/1 rows whose runs disagree", r.stdout)
        a = json.loads(out.read_text())["human_thriving_analysis"]
        self.assertEqual(a["system_fingerprints"], ["fp1", "fp2"])
        self.assertEqual(a["served_model"], "deepseek-flash")
        self.assertEqual(a["prompt_sha256"], "f" * 64)
        self.assertEqual([x["system_fingerprint"] for x in a["runs"]], ["fp1", "fp2"])


if __name__ == "__main__":
    unittest.main()
