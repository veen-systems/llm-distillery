"""Seeded positives for the experiment-registry checker.

⛔ The reason each case exists: a registry whose numbers drift reads MORE authoritative than no
registry at all, and augur -- whose method this repo adopted -- had to run an audit (its EXP-031)
that found 19 untraceable numbers. The check that prevents that is only worth having if it can be
shown to fail, so every guard below is exercised with a planted defect.
"""
import hashlib, json, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CHECK = REPO / "scripts" / "verification" / "check_experiment_registry.py"
REG = REPO / "experiments" / "registry.jsonl"


def run_against(lines, *extra):
    """Run the checker against a planted registry in a temp dir. ⛔ Never write the tracked file:
    the old swap-and-restore left it corrupted whenever a run was killed (llm-distillery#162)."""
    with tempfile.TemporaryDirectory() as d:
        planted = Path(d) / "registry.jsonl"
        planted.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in lines) + "\n",
                           encoding="utf-8")
        return subprocess.run([sys.executable, str(CHECK), "--registry", str(planted), *extra],
                              capture_output=True, text=True)


def entries():
    return [json.loads(l) for l in REG.read_text(encoding="utf-8").splitlines() if l.strip()]


class RegistryTest(unittest.TestCase):

    def test_the_committed_registry_passes(self):
        r = subprocess.run([sys.executable, str(CHECK)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("untraceable 0", r.stdout)

    def test_it_checks_a_nonzero_number_of_metrics(self):
        """A traceability check over zero metrics passes vacuously. Prove it looked at some."""
        r = subprocess.run([sys.executable, str(CHECK)], capture_output=True, text=True)
        checked = int(r.stdout.split("metrics checked")[1].split()[0])
        self.assertGreater(checked, 10, "the checker examined almost nothing — a vacuous pass")

    def test_an_INVENTED_number_FAILS(self):
        e = entries()
        e[0]["metrics"]["invented_figure"] = "99.9999%"
        r = run_against(e)
        self.assertNotEqual(r.returncode, 0, "an invented metric must not pass")
        self.assertIn("NOT traceable", r.stdout)

    def test_a_PLAUSIBLE_but_wrong_number_FAILS(self):
        """The dangerous case is not 99.9999% — it is a number one digit off the real one."""
        e = entries()
        e[0]["metrics"]["residual_k3_prodmix_reordered"] = "2.462%"   # real value is 2.452%
        r = run_against(e)
        self.assertNotEqual(r.returncode, 0, "a one-digit-off metric must not pass")
        self.assertIn("NOT traceable", r.stdout)

    def test_null_is_allowed(self):
        e = entries()
        e[0]["metrics"]["unrecoverable"] = None
        r = run_against(e)
        self.assertEqual(r.returncode, 0, "null must pass — it is how an unrecoverable value is "
                                          "recorded honestly")

    def test_a_missing_artifact_path_FAILS(self):
        e = entries()
        e[0]["artifacts"] = e[0]["artifacts"] + ["docs/evidence/does-not-exist"]
        r = run_against(e)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("artifact does not exist", r.stdout)

    def test_an_unknown_decision_value_FAILS(self):
        e = entries()
        e[0]["decision"] = "probably-fine"
        r = run_against(e)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not in", r.stdout)

    def test_out_of_order_or_duplicate_ids_FAIL(self):
        e = entries()
        e[0], e[1] = e[1], e[0]
        r = run_against(e)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ascending order", r.stdout)
        e = entries()
        e[1]["id"] = e[0]["id"]
        r2 = run_against(e)
        self.assertNotEqual(r2.returncode, 0)
        self.assertIn("duplicate ids", r2.stdout)

    def test_a_missing_required_field_FAILS(self):
        e = entries()
        del e[0]["spend_usd"]
        r = run_against(e)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("missing required field", r.stdout)

    def test_planting_a_defect_never_writes_the_tracked_registry(self):
        """#162: a restore in `finally` does not run under SIGKILL or a `timeout`, so the only safe
        helper is one that never writes REG at all. Byte-equality alone cannot see a
        write-then-restore; the mtime can. (A digest, not the bytes: rendering a difflib diff of
        a 180 KB mismatch ran >2 minutes without finishing.)"""
        state = lambda: (REG.stat().st_mtime_ns, hashlib.sha256(REG.read_bytes()).hexdigest())
        before = state()
        e = entries()
        e[0]["metrics"]["invented_figure"] = "99.9999%"
        r = run_against(e)
        self.assertNotEqual(r.returncode, 0, "the planted defect must still be caught")
        self.assertEqual(state(), before,
                         "planting a defect wrote the tracked experiments/registry.jsonl")

    def test_the_checker_reads_the_registry_it_is_given(self):
        """The helper is only safe if the checker honours `--registry`; were the flag ignored, it
        would check the clean tracked file and every planted defect would silently pass."""
        e = entries()
        e[0]["metrics"]["invented_figure"] = "99.9999%"
        with tempfile.TemporaryDirectory() as d:
            planted = Path(d) / "registry.jsonl"
            planted.write_text("\n".join(json.dumps(x) for x in e) + "\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(CHECK), "--registry", str(planted)],
                               capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("`invented_figure` = 99.9999% is NOT traceable", r.stdout)

    def test_the_lab_field_is_shape_and_existence_checked(self):
        """Optional `lab` (2026-10-13): a pre-registered run's data must have a home -- never
        inbox/ -- and the path must exist on situla."""
        with tempfile.TemporaryDirectory() as lab:
            for d in ("experiments/2026-10-12-x", "inbox/b650-gpu/2026-10-12/x"):
                (Path(lab) / d).mkdir(parents=True)          # bad SHAPES exist, so only the shape check can fail them
            for value, why in [(["experiments/2026-10-12-x"], None),
                               ([], None),
                               (["experiments/2026-10-12-gone"], "does not exist"),
                               (["inbox/b650-gpu/2026-10-12/x"], "not under experiments/"),
                               (["datasets/../inbox"], "not under experiments/"),
                               ("experiments/2026-10-12-x", "must be a list")]:
                with self.subTest(value=value):
                    e = [{k: v for k, v in x.items() if k != "lab"} for x in entries()]   # only the planted one
                    e[0]["lab"] = value
                    r = run_against(e, "--lab-root", lab)
                    self.assertEqual(r.returncode == 0, why is None, r.stdout)
                    if why:
                        self.assertIn(why, r.stdout)
            e = [{k: v for k, v in x.items() if k != "lab"} for x in entries()]
            e[0]["lab"] = ["experiments/2026-10-12-gone"]
            r = run_against(e, "--lab-root", str(Path(lab) / "absent"))          # no lab root: shape only,
            self.assertEqual(r.returncode, 0, r.stdout)                          # and it says so
            self.assertIn("existence SKIPPED", r.stdout)

    def test_every_entry_states_its_spend(self):
        """`0` is a claim a reader can check; absent is not."""
        for e in entries():
            self.assertIn("spend_usd", e, f"{e['id']} does not state spend")
            self.assertIsNotNone(e["spend_usd"], f"{e['id']} spend is null — say 0 if it was free")


if __name__ == "__main__":
    unittest.main(verbosity=2)


sys.path.insert(0, str(REPO / "scripts" / "verification"))
import check_experiment_registry as cer  # noqa: E402


class TraceableTokenTest(unittest.TestCase):
    """#171 / #175 (2026-10-21): the substring test passed a one-digit metric against any artifact holding the digit.
    Hardening it found three registry numbers that only matched by accident (EXP-015, -023, -025)."""

    def assertNot(self, value, text):
        self.assertFalse(cer.traceable(value, text)[0], f"{value!r} must NOT match {text!r}")

    def assertYes(self, value, text):
        self.assertTrue(cer.traceable(value, text)[0], f"{value!r} must match {text!r}")

    def test_a_number_inside_a_DATE_ID_or_LONGER_number_does_not_count(self):
        for t in ("labelled 2026-10-04", "see #41", "EXP-041 says", "v4 shipped", "v8-4 prompt", "1.40 shift",
                  "112 rows", "111%", "11.68x", "run 20261004T1430Z", "at 4:14"):
            self.assertNot(4 if "4" in t and "11" not in t else 11, t)
        self.assertNot("0.65", '"mae": 0.6541358828544617')      # EXP-015's accidental match
        self.assertNot("19", "publishing 19.0% and 4.798%")      # EXP-025's

    def test_a_standalone_number_still_counts_including_with_a_UNIT(self):
        for v, t in ((4, "checks added: 4"), (4, "**4** of 30"), ("26.46", "52%  26.46ms"), ("3.82", "3.82x slower"),
                     ("3083.8", "handler 3083.8s"), ("4:14", "| **4:14** |"), (-0.27, "shift -0.27 median"),
                     (1234, "1,234 rows")):
            self.assertYes(v, t)

    def test_a_ROUNDED_quote_counts_only_at_four_significant_digits(self):
        self.assertYes("0.5715", '"best_val_mae": 0.5715025663375854,')
        self.assertYes("0.01948", '"discordant_pair_share": 0.019484519046355227,')
        self.assertNot("0.57", '"best_val_mae": 0.5715025663375854,')

    def test_an_UNTRACKED_artifact_FAILS_even_though_it_exists_on_disk(self):
        with tempfile.NamedTemporaryFile(dir=REPO / "docs" / "evidence", suffix=".md", delete=False) as f:
            f.write(b"the number 7\n")
        try:
            rel = str(Path(f.name).relative_to(REPO))
            e = entries()
            e[0]["artifacts"] = e[0]["artifacts"] + [rel]
            r = run_against(e)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("not tracked by git", r.stdout)
        finally:
            Path(f.name).unlink()

    def test_a_path_naming_the_ROOT_FAILS(self):
        e = entries()
        e[0]["artifacts"] = e[0]["artifacts"] + ["."]
        r = run_against(e)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("names the root", r.stdout)
