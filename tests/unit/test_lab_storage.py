"""Seeded defects for the situla-as-source-of-truth machinery (scripts/lab/lab.py and
scripts/verification/check_lab_manifests.py; docs/decisions/2026-10-10-situla-single-source-of-truth.md).

Each guard is only worth having if it can be shown to fail, so each one gets a planted defect,
in a temp lab root and a temp evidence tree, never the real ones. `pull` runs for real against a
fake `ssh` placed first on PATH: it runs the "remote" command locally with HOME pointed at a temp
dir, and rsync reaches it through the same shim. The cases are the ones the 2026-10-10 review
found by hand: re-pull overwriting a cited copy, symlinks whose data never arrived, a dir holding
one same-named file, a source tree carrying a lab manifest, odd file names, `~/` paths.

The last test runs the check on the REAL docs/evidence tree (`--no-lab`), so a new evidence dir
that cites a GPU host without a manifest fails the suite, not just a hand run.
"""
import json, os, stat, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LAB = REPO / "scripts" / "lab" / "lab.py"
CHECK = REPO / "scripts" / "verification" / "check_lab_manifests.py"
I = "inbox/h/2026-10-11/"   # a dest that follows the lab layout

FAKE_SSH = """#!/bin/bash
# test shim: drop ssh options, drop the host, run the rest locally
while [[ "$1" == -* ]]; do shift; done
shift
cd "$HOME"          # a real ssh login starts in HOME; rsync's relative paths depend on it
exec bash -c "$*"
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.lab, self.ev, self.home, self.bin = t / "lab", t / "evidence", t / "home", t / "bin"
        for d in (self.lab, self.ev, self.home, self.bin):
            d.mkdir()
        ssh = self.bin / "ssh"
        ssh.write_text(FAKE_SSH)
        ssh.chmod(ssh.stat().st_mode | stat.S_IEXEC)
        self.env = dict(os.environ, LD_LAB=str(self.lab), HOME=str(self.home),
                        PATH=f"{self.bin}:{os.environ['PATH']}")

    def tearDown(self):
        self.tmp.cleanup()

    def run_tool(self, *args, script=LAB):
        return subprocess.run([sys.executable, str(script), *args], capture_output=True,
                              text=True, env=self.env)

    def check(self, *extra, baseline=None):
        b = baseline or (Path(self.tmp.name) / "baseline.json")   # absent file = empty baseline
        return self.run_tool("--evidence", str(self.ev), "--baseline", str(b), *extra, script=CHECK)

    def host_tree(self, name, files):
        """Create files under the fake host's HOME; values are bytes, or ('link', target)."""
        root = self.home / name
        for rel, v in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(v, tuple):
                p.symlink_to(v[1])
            else:
                p.write_bytes(v)
        return root

    def evidence_dir(self, name, text):
        d = self.ev / name
        d.mkdir()
        (d / "README.md").write_text(text)
        return d


class Pull(Base):
    def test_local_source_pulls_without_ssh_and_verifies(self):
        """`local:/abs/path` (2026-10-16): data already on situla, which cannot ssh to itself. ssh is made to FAIL
        here, so the pull passes only if the local branch is taken; the manifest must still carry every hash."""
        (self.bin / "ssh").write_text("#!/bin/sh\necho ssh-was-called >&2\nexit 99\n")
        src = Path(self.tmp.name) / "scratch" / "runs"
        src.mkdir(parents=True)
        (src / "a.jsonl").write_bytes(b"one\n")
        (src / "b.jsonl").write_bytes(b"two\n")
        r = self.run_tool("pull", f"local:{src}", "experiments/2026-10-16-x/runs")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("ssh-was-called", r.stderr)
        man = json.loads((self.lab / "experiments/2026-10-16-x/runs/_LAB_MANIFEST.json").read_text())
        self.assertEqual(sorted(man["files"]), ["a.jsonl", "b.jsonl"])
        self.assertTrue(man["origin"].startswith("local:"))
        self.assertEqual(self.run_tool("verify", "experiments/2026-10-16-x/runs").returncode, 0)

    def test_local_source_must_be_absolute(self):
        """A relative or ~ local path is listed against $HOME but copied relative to the cwd (review 2026-10-16)."""
        for src in ("local:scratch/runs", "local:~/scratch/runs"):
            r = self.run_tool("pull", src, "experiments/2026-10-16-y/runs")
            self.assertNotEqual(r.returncode, 0, src)
            self.assertIn("ABSOLUTE", r.stderr + r.stdout)
            self.assertFalse((self.lab / "experiments/2026-10-16-y/runs").exists())

    def test_pull_verify_and_odd_names(self):
        self.host_tree("run", {"model.bin": b"w", "dir with space/b c.txt": b"b",
                               "back\\slash": b"x", "nl\nname": b"y", "sub/x.pyc": b"skip",
                               "sub/_LAB_MANIFEST.json": b"{}", "inlink": ("link", "model.bin")})
        r = self.run_tool("pull", "host:run", I + "run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("4 files, 1 links", r.stdout)            # pyc and nested manifest excluded
        self.assertEqual(self.run_tool("verify", I + "run").returncode, 0)

    def test_tilde_path(self):
        self.host_tree("run", {"a": b"a"})
        self.assertEqual(self.run_tool("pull", "host:~/run", I + "x").returncode, 0)

    def test_refuses_existing_dest_so_a_cited_copy_survives(self):
        src = self.host_tree("run", {"model.bin": b"v1"})
        self.assertEqual(self.run_tool("pull", "host:run", I + "x").returncode, 0)
        (src / "model.bin").write_bytes(b"v2-retrained")
        r = self.run_tool("pull", "host:run", I + "x")
        self.assertEqual(r.returncode, 1)
        self.assertIn("REFUSED", r.stderr)
        self.assertEqual((self.lab / I / "x" / "model.bin").read_bytes(), b"v1")

    def test_refuses_links_whose_data_is_not_in_the_copy(self):
        self.host_tree("outside", {"secret.bin": b"s"})
        for target in ("../outside/secret.bin", "/etc/hostname", "nowhere"):
            with self.subTest(target=target):
                name = "t" + str(abs(hash(target)))
                self.host_tree(name, {"metrics.json": b"m", "weights.bin": ("link", target)})
                r = self.run_tool("pull", f"host:{name}", I + name)
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn("REFUSED", r.stdout)
                self.assertFalse((self.lab / I / name).exists())

    def test_allow_external_links_records_and_warns(self):
        self.host_tree("t", {"m": b"m", "w": ("link", "../elsewhere")})
        r = self.run_tool("pull", "host:t", I + "t", "--allow-external-links")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARNING", r.stdout)
        m = json.loads((self.lab / I / "t" / "_LAB_MANIFEST.json").read_text())
        self.assertEqual(m["links"], {"w": "../elsewhere"})
        self.assertEqual(len(m["link_warnings"]), 1)

    def test_dir_holding_one_same_named_file(self):
        self.host_tree("same", {"same": b"s"})
        self.assertEqual(self.run_tool("pull", "host:same", I + "same").returncode, 0)
        self.assertTrue((self.lab / I / "same" / "same").is_file())
        self.assertEqual(self.run_tool("verify", I + "same").returncode, 0)

    def test_single_file_lands_inside_a_new_dir(self):
        self.host_tree("d", {"one.bin": b"1", "two.bin": b"2"})
        self.assertEqual(self.run_tool("pull", "host:d/one.bin", I + "one").returncode, 0)
        self.assertEqual(sorted(p.name for p in (self.lab / I / "one").iterdir()), ["_LAB_MANIFEST.json", "one.bin"])

    def test_refuses_dest_outside_lab_or_inside_a_pulled_tree(self):
        self.host_tree("run", {"a": b"a"})
        for dest in ("../escaped", str(Path(self.tmp.name) / "abs")):
            with self.subTest(dest=dest):
                r = self.run_tool("pull", "host:run", dest)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("outside the lab root", r.stderr)
        self.assertEqual(self.run_tool("pull", "host:run", I + "x").returncode, 0)
        r = self.run_tool("pull", "host:run", I + "x/sub")
        self.assertIn("inside the pulled tree", r.stderr)

    def test_special_file_fails_instead_of_hanging(self):
        self.host_tree("run", {"a": b"a"})
        os.mkfifo(self.home / "run" / "pipe")
        r = subprocess.run([sys.executable, str(LAB), "pull", "host:run", I + "x"], capture_output=True,
                           text=True, env=self.env, timeout=60)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("pipe", r.stdout)

    def test_rsync_failure_says_how_to_recover(self):
        self.host_tree("run", {"a": b"a"})
        shim = self.bin / "rsync"
        shim.write_text("#!/bin/bash\nexit 12\n")
        shim.chmod(0o755)
        r = self.run_tool("pull", "host:run", I + "x")
        self.assertEqual(r.returncode, 1)
        self.assertIn("PARTIAL", r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_single_top_level_file_origin(self):
        (self.home / "top.jsonl").write_bytes(b"t")
        self.assertEqual(self.run_tool("pull", "host:top.jsonl", I + "t").returncode, 0)
        d = self.evidence_dir("2026-10-11-x", "")
        self.run_tool("cite", str(d), I + "t/top.jsonl")
        self.assertEqual(json.loads((d / "MANIFEST.json").read_text())["entries"][0]["origin"], "host:top.jsonl")

    def test_refuses_empty_tree(self):
        self.host_tree("e", {"venv/v": b"v"})
        r = self.run_tool("pull", "host:e", I + "e")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("nothing to pull", r.stderr)


class Adopt(Base):
    def test_adopt_writes_manifest_only_when_identical(self):
        self.host_tree("run", {"a": b"a", "sub/b": b"b"})
        copy = self.lab / I / "run"
        (copy / "sub").mkdir(parents=True)
        (copy / "a").write_bytes(b"a")
        (copy / "sub" / "b").write_bytes(b"B-differs")
        r = self.run_tool("adopt", "host:run", I + "run")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertFalse((copy / "_LAB_MANIFEST.json").exists())
        (copy / "sub" / "b").write_bytes(b"b")
        r = self.run_tool("adopt", "host:run", I + "run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK adopted", r.stdout)
        self.assertEqual(self.run_tool("verify", I + "run").returncode, 0)
        self.assertNotEqual(self.run_tool("adopt", "host:run", I + "run").returncode, 0)   # has a manifest now

    def test_adopt_replace_manifest_and_hidden_entries(self):
        self.host_tree("run", {"a": b"a"})
        self.assertEqual(self.run_tool("pull", "host:run", I + "x").returncode, 0)
        (self.lab / I / "x" / "_LAB_MANIFEST.json").write_text('{"origin": "host:run", "files": {}}')  # an old format
        self.assertNotEqual(self.run_tool("adopt", "host:run", I + "x").returncode, 0)
        r = self.run_tool("adopt", "host:run", I + "x", "--replace-manifest")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.run_tool("verify", I + "x").returncode, 0)
        (self.lab / I / "x" / ".git").mkdir()
        (self.lab / I / "x" / ".git" / "HEAD").write_text("x")
        r = self.run_tool("adopt", "host:run", I + "x", "--replace-manifest")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("excluded entries", r.stderr)

    def test_adopt_refuses_missing_dest(self):
        self.host_tree("run", {"a": b"a"})
        self.assertNotEqual(self.run_tool("adopt", "host:run", I + "nothere").returncode, 0)


class VerifyCite(Base):
    def setUp(self):
        super().setUp()
        self.host_tree("run", {"model.bin": b"weights", "sub/log.txt": b"log"})
        assert self.run_tool("pull", "host:run", I + "run").returncode == 0
        self.tree = self.lab / I / "run"

    def test_verify_fails_on_changed_extra_or_missing(self):
        (self.tree / "sub" / "log.txt").write_text("edited")
        r = self.run_tool("verify", I + "run")
        self.assertEqual(r.returncode, 1)
        self.assertIn("sub/log.txt", r.stdout)
        (self.tree / "sub" / "log.txt").write_text("log")
        (self.tree / "stray").write_text("x")
        self.assertEqual(self.run_tool("verify", I + "run").returncode, 1)
        (self.tree / "stray").unlink()
        (self.tree / "model.bin").unlink()
        self.assertEqual(self.run_tool("verify", I + "run").returncode, 1)

    def test_cite_records_origin_and_hash(self):
        d = self.evidence_dir("2026-10-11-x", "rests on b650-gpu:run/model.bin")
        r = self.run_tool("cite", str(d), I + "run/model.bin")
        self.assertEqual(r.returncode, 0, r.stderr)
        e = json.loads((d / "MANIFEST.json").read_text())["entries"][0]
        self.assertEqual(e["origin"], "host:run/model.bin")

    def test_cite_single_file_origin_is_the_file(self):
        self.host_tree("d", {"one.bin": b"1"})
        self.run_tool("pull", "host:d/one.bin", I + "one")
        d = self.evidence_dir("2026-10-11-x", "")
        self.run_tool("cite", str(d), I + "one/one.bin")
        self.assertEqual(json.loads((d / "MANIFEST.json").read_text())["entries"][0]["origin"], "host:d/one.bin")

    def test_cite_refusals(self):
        d = self.evidence_dir("2026-10-11-x", "")
        (self.lab / "loose.txt").write_text("x")
        outside = Path(self.tmp.name) / "outside.txt"
        outside.write_text("x")
        for path in ("loose.txt", str(outside), "../outside.txt"):
            with self.subTest(path=path):
                self.assertNotEqual(self.run_tool("cite", str(d), path).returncode, 0)
        # a pulled-looking tree OUTSIDE the lab root: both the root guard and the manifest
        # search must refuse it (either alone suffices; removing both must fail this test)
        fake = Path(self.tmp.name) / "fakelab" / "t"
        fake.mkdir(parents=True)
        (fake / "m.json").write_text("x")
        (fake / "_LAB_MANIFEST.json").write_text(json.dumps({"origin": "h:t", "pulled_at": "x", "files": {
            "m.json": {"sha256": "2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881", "size": 1}}}))
        r = self.run_tool("cite", str(d), str(fake / "m.json"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("outside the lab root", r.stderr)        # a refusal, not a crash
        (self.tree / "model.bin").write_bytes(b"other")
        self.assertNotEqual(self.run_tool("cite", str(d), I + "run/model.bin").returncode, 0)


class Check(Base):
    def cited_dir(self, name, text, *paths):
        self.host_tree("run", {"model.bin": b"weights"})
        if not (self.lab / I / "run").exists():
            assert self.run_tool("pull", "b650-gpu:run", I + "run").returncode == 0
        d = self.evidence_dir(name, text)
        for p in paths:
            assert self.run_tool("cite", str(d), p).returncode == 0
        return d

    def test_citation_forms_without_manifest_fail(self):
        forms = ["b650-gpu:~/llm-distillery/dump/", "b650-gpu:llm-distillery/x/v1",
                 "b650-gpu:'~/llm-distillery/x/training_*.json'", "`b650-gpu`:`~/dump`",
                 "ssh b650-gpu 'python3 run.py'", "results on b650-gpu", "(b650 only, untracked)",
                 "gpu-server:/tmp/x", "sadaltager:~/backup"]
        for i, form in enumerate(forms):
            with self.subTest(form=form):
                d = self.evidence_dir(f"2026-10-11-f{i}", f"text {form} more")
                r = self.check("--no-lab")
                self.assertEqual(r.returncode, 1, r.stdout)
                self.assertIn(f"FAIL 2026-10-11-f{i}", r.stdout)
                (d / "README.md").unlink(); d.rmdir()

    def test_covered_citation_passes_uncovered_fails(self):
        self.cited_dir("2026-10-11-x", "rests on b650-gpu:~/run/model.bin", I + "run/model.bin")
        self.assertEqual(self.check().returncode, 0, self.check().stdout)
        (self.ev / "2026-10-11-x" / "README.md").write_text("b650-gpu:~/run/model.bin and b650-gpu:~/other/x")
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("b650-gpu:other/x", r.stdout)

    def test_empty_manifest_fails(self):
        d = self.evidence_dir("2026-10-11-x", "no host named here")   # only the empty manifest can fail it
        (d / "MANIFEST.json").write_text('{"entries": []}')
        r = self.check("--no-lab")
        self.assertEqual(r.returncode, 1)
        self.assertIn("has no entries", r.stdout)

    def test_baseline_is_per_item_not_per_date(self):
        d = self.evidence_dir("2026-09-01-x", "the dump is at b650-gpu:~/dump/")
        b = Path(self.tmp.name) / "bl.json"
        self.assertEqual(self.check("--no-lab", "--write-baseline", baseline=b).returncode, 0)
        r = self.check("--no-lab", baseline=b)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("BACKLOG 2026-09-01-x", r.stdout)
        (d / "README.md").write_text("the dump is at b650-gpu:~/dump/ and now b650-gpu:~/new/x")   # added to an OLD dir
        r = self.check("--no-lab", baseline=b)
        self.assertEqual(r.returncode, 1)
        fail_line = [l for l in r.stdout.splitlines() if l.startswith("FAIL")][0]
        self.assertIn("b650-gpu:new/x", fail_line)
        self.assertNotIn("b650-gpu:dump", fail_line)

    def test_top_level_file_and_undated_dir_are_checked(self):
        (self.ev / "note.md").write_text("ran on b650-gpu")
        r = self.check("--no-lab")
        self.assertEqual(r.returncode, 1)
        self.assertIn("make it a dir", r.stdout)
        (self.ev / "note.md").unlink()
        self.evidence_dir("v9-gate", "ssh b650-gpu 'x'")
        self.assertEqual(self.check("--no-lab").returncode, 1)

    def test_more_citation_forms_fail(self):
        forms = ["ssh -o BatchMode=yes b650-gpu 'x'", "ssh -p 2222 b650-gpu", 'b650-gpu:"$HOME/run"',
                 "b650-gpu:$HOME/run/x", "B650-GPU:~/run/x"]
        for i, form in enumerate(forms):
            with self.subTest(form=form):
                d = self.evidence_dir(f"2026-10-11-g{i}", f"text {form} more")
                self.assertEqual(self.check("--no-lab").returncode, 1, form)
                (d / "README.md").unlink(); d.rmdir()
        d = self.evidence_dir("2026-10-11-log", "")
        (d / "README.md").unlink()
        (d / "run.log").write_text("output at b650-gpu:~/llm-distillery/out/")
        self.assertEqual(self.check("--no-lab").returncode, 1)

    def test_false_positives_stay_quiet(self):
        self.evidence_dir("2026-10-11-a", "metrics at http://b650-gpu:8080/metrics")
        self.evidence_dir("2026-10-11-b", "read from Sadalsuud's production tree")
        self.evidence_dir("2026-10-11-c", "scp scripts/*.py b650-gpu:~/")
        r = self.check("--no-lab")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_glob_coverage_has_a_boundary(self):
        self.cited_dir("2026-10-11-x", "b650-gpu:~/r*", I + "run/model.bin")
        self.assertEqual(self.check().returncode, 0, self.check().stdout)   # run/model.bin matches r*
        (self.ev / "2026-10-11-x" / "README.md").write_text("b650-gpu:~/q*")
        self.assertEqual(self.check().returncode, 1)

    def test_lab_mode_catches_a_forged_origin(self):
        d = self.cited_dir("2026-10-11-x", "b650-gpu:~/run/model.bin", I + "run/model.bin")
        m = json.loads((d / "MANIFEST.json").read_text())
        m["entries"][0]["origin"] = "b650-gpu:v9_corpus/made_up.json"
        (d / "MANIFEST.json").write_text(json.dumps(m))
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("disagrees with its pulled tree", r.stdout)

    def test_opt_out_needs_a_reason_and_is_reported(self):
        self.evidence_dir("2026-10-11-inv", "inventory of b650-gpu:~/x\n<!-- lab-check: not-host-data: an inventory of the hosts -->")
        r = self.check("--no-lab")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("EXEMPT 2026-10-11-inv: an inventory of the hosts", r.stdout)
        self.evidence_dir("2026-10-11-bare", "on b650-gpu\n<!-- lab-check: not-host-data -->")
        r = self.check("--no-lab")
        self.assertEqual(r.returncode, 1)
        self.assertIn("marker with no reason", r.stdout)

    def test_exemption_is_an_anchored_prefix(self):
        self.evidence_dir("2026-10-11-a", "read sadalsuud:~/local_dev/NexusMind/data/filtered/x on sadalsuud")
        self.assertEqual(self.check("--no-lab").returncode, 0)
        self.evidence_dir("2026-10-11-b", "rows at sadalsuud:/tmp/local_dev/x.jsonl")
        self.assertEqual(self.check("--no-lab").returncode, 1)
        (self.ev / "2026-10-11-b" / "README.md").write_text("rows at sadalsuud:~/local_dev_old/x.jsonl")
        self.assertEqual(self.check("--no-lab").returncode, 1)

    def test_exempt_and_hosts_are_parameters(self):
        self.evidence_dir("2026-10-11-x", "replica at ct102:~/local_dev/NexusMind/data/x")
        self.assertEqual(self.check("--no-lab", "--hosts", "ct102").returncode, 1)
        self.assertEqual(self.check("--no-lab", "--hosts", "ct102", "--exempt", "ct102:local_dev/").returncode, 0)
        self.evidence_dir("2026-10-11-y", "read sadalsuud:~/local_dev/x")
        self.assertEqual(self.check("--no-lab", "--exempt").returncode, 1)

    def test_lab_side_detects_changed_and_missing_files(self):
        self.cited_dir("2026-10-11-x", "b650-gpu:~/run/model.bin", I + "run/model.bin")
        f = self.lab / I / "run" / "model.bin"
        f.write_bytes(b"weightz")                                   # same size: only sha256 sees it
        self.assertEqual(self.check().returncode, 1)
        self.assertEqual(self.check("--fast").returncode, 0)         # documents what --fast gives up
        f.unlink()
        self.assertEqual(self.check("--fast").returncode, 1)

    def test_lab_root_flag_and_missing_lab_root(self):
        self.cited_dir("2026-10-11-x", "b650-gpu:~/run/model.bin", I + "run/model.bin")
        self.env["LD_LAB"] = str(Path(self.tmp.name) / "nowhere")
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not exist", r.stdout)
        self.assertEqual(self.check("--lab-root", str(self.lab)).returncode, 0)
        self.assertEqual(self.run_tool("--lab-root", str(self.lab), "verify", I + "run").returncode, 0)


class Layout(Base):
    """2026-10-12: a pull landed at `b650-gpu/...` in the lab root, and a pre-registered run in
    inbox/. pull/adopt/move refuse a dest outside the layout in the lab README.md."""
    def test_pull_refuses_dests_outside_the_layout(self):
        self.host_tree("run", {"a": b"a"})
        for dest in ("b650-gpu/2026-10-12/run", "run", "inbox/run", "inbox/h/run",
                     "inbox/h/12-10-2026/run", "experiments/c2c", "experiments/2026-10-12",
                     "datasets/corpus", "datasets/corpus/1", "datasets/corpus/version1",
                     "experiments/2026-10-11-x\n", "experiments/\u0662\u0660\u0662\u0666-10-11-x",
                     "experiments/2026-99-99-x", "inbox/h/2026-13-01/run"):
            with self.subTest(dest=dest):
                r = self.run_tool("pull", "host:run", dest)
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertIn("REFUSED", r.stderr)
                self.assertFalse((self.lab / dest).exists())
        for dest in ("inbox/h/2026-10-12/run", "experiments/2026-10-12-c2c",
                     "experiments/2026-10-12-d/s42", "datasets/corpus/v1", "datasets/corpus/v2/part"):
            with self.subTest(dest=dest):
                r = self.run_tool("pull", "host:run", dest)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_adopt_refuses_dests_outside_the_layout(self):
        self.host_tree("run", {"a": b"a"})
        (self.lab / "loose").mkdir()
        (self.lab / "loose" / "a").write_bytes(b"a")
        r = self.run_tool("adopt", "host:run", "loose")
        self.assertEqual(r.returncode, 1)
        self.assertIn("not under inbox/", r.stderr)
        self.assertFalse((self.lab / "loose" / "_LAB_MANIFEST.json").exists())


class Move(Base):
    def setUp(self):
        super().setUp()
        self.host_tree("run", {"model.bin": b"weights", "sub/log.txt": b"log"})
        self.host_tree("draw", {"rows.jsonl": b"rows"})
        assert self.run_tool("pull", "host:run", I + "run").returncode == 0
        assert self.run_tool("pull", "host:draw", I + "draw").returncode == 0
        self.d = self.evidence_dir("2026-10-11-x", "reads ~/lab/llm-distillery/inbox/h/2026-10-11/run/model.bin")
        assert self.run_tool("cite", str(self.d), I + "run/model.bin", I + "draw/rows.jsonl").returncode == 0

    def move(self, src, dest):
        return self.run_tool("move", src, dest, "--evidence", str(self.ev))

    def entries(self):
        return [e["path"] for e in json.loads((self.d / "MANIFEST.json").read_text())["entries"]]

    def test_move_rewrites_citations_and_records_the_move(self):
        self.evidence_dir("2026-10-11-sib", "a sibling: ~/lab/llm-distillery/inbox/h/2026-10-11/run2/x")
        r = self.move(I + "run", "experiments/2026-10-11-x/run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.entries(), ["experiments/2026-10-11-x/run/model.bin", I + "draw/rows.jsonl"])
        self.assertFalse((self.lab / I / "run").exists())
        m = json.loads((self.lab / "experiments/2026-10-11-x/run/_LAB_MANIFEST.json").read_text())
        self.assertEqual(m["moves"][0]["from"], I + "run")
        self.assertEqual(m["origin"], "host:run")                      # origin is the HOST path, unchanged
        self.assertIn("STILL NAMES THE OLD PATH", r.stdout)            # the README text: listed, not edited
        self.assertNotIn("2026-10-11-sib", r.stdout)                    # `run2` is not `run`
        (self.ev / "2026-10-11-sib" / "README.md").unlink(); (self.ev / "2026-10-11-sib").rmdir()
        self.assertIn("inbox/h/2026-10-11/run/model.bin", (self.d / "README.md").read_text())
        self.assertEqual(self.run_tool("verify", "experiments/2026-10-11-x/run").returncode, 0)
        self.assertEqual(self.check("--no-lab").returncode, 0)
        r = self.check()                                               # lab mode: the stale README path fails
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("lab path(s) that do not exist", r.stdout)
        (self.d / "README.md").write_text("reads ~/lab/llm-distillery/experiments/2026-10-11-x/run/model.bin")
        self.assertEqual(self.check().returncode, 0, self.check().stdout)

    def test_move_a_dir_of_trees_and_clean_empty_parents(self):
        r = self.move("inbox/h/2026-10-11", "experiments/2026-10-11-x")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.entries(), ["experiments/2026-10-11-x/draw/rows.jsonl",
                                          "experiments/2026-10-11-x/run/model.bin"])
        self.assertFalse((self.lab / "inbox" / "h").exists())          # emptied host dir removed
        self.assertTrue((self.lab / "inbox").is_dir())                 # the area itself stays

    def test_move_refusals(self):
        before = self.entries()
        (self.lab / "experiments/2026-10-11-x").mkdir(parents=True)
        cases = [(I + "run", "experiments/2026-10-11-x", "exists"),       # never merges
                 (I + "run", "elsewhere/run", "not under inbox/"),         # layout
                 (I + "run/sub", "experiments/2026-10-12-y", "inside the pulled tree"),
                 (I + "draw", I + "run/draw", "inside the pulled tree"),   # into another tree
                 ("inbox/h/2026-10-11/nothere", "experiments/2026-10-12-y", "not a directory"),
                 ("../x", "experiments/2026-10-12-y", "outside the lab root")]
        for src, dest, why in cases:
            with self.subTest(src=src, dest=dest):
                r = self.move(src, dest)
                self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
                self.assertIn(why, r.stderr)
        r = self.move("inbox", "experiments/2026-10-12-everything")          # a whole area
        self.assertIn("whole lab area", r.stderr)
        (self.lab / I / "run" / "lnk").symlink_to("../draw/rows.jsonl")      # escapes its tree
        r = self.move(I + "run", "experiments/2026-10-12-y/run")
        self.assertIn("pointing outside", r.stderr)
        (self.lab / I / "run" / "lnk").unlink()
        (self.lab / I / "stray.txt").write_text("unpulled")               # a dir that is not all trees
        r = self.move("inbox/h/2026-10-11", "experiments/2026-10-12-y")
        self.assertIn("outside any pulled tree", r.stderr)
        (self.lab / I / "stray.txt").unlink()
        (self.lab / I / "run" / "model.bin").write_bytes(b"tampered")    # a broken tree is not carried
        r = self.move(I + "run", "experiments/2026-10-12-y/run")
        self.assertIn("does not verify", r.stderr)
        self.assertEqual(self.entries(), before)
        self.assertTrue((self.lab / I / "run").is_dir())


class PreregisteredInbox(Base):
    def test_preregistered_dir_citing_inbox_fails(self):
        self.host_tree("run", {"model.bin": b"weights"})
        self.run_tool("pull", "host:run", I + "run")
        d = self.evidence_dir("2026-10-11-x", "")
        self.run_tool("cite", str(d), I + "run/model.bin")
        self.assertEqual(self.check("--no-lab").returncode, 0)          # not pre-registered: inbox is fine
        (d / "PREREGISTRATION.md").write_text("bar fixed before scores")
        r = self.check("--no-lab")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("pre-registered, but cites 1 inbox/", r.stdout)
        self.assertEqual(self.run_tool("move", I + "run", "experiments/2026-10-11-x/run",
                                       "--evidence", str(self.ev)).returncode, 0)
        self.assertEqual(self.check().returncode, 0, self.check().stdout)

    def test_stale_text_path_forms(self):
        self.host_tree("run", {"model.bin": b"weights"})
        self.run_tool("pull", "host:run", I + "run")
        for text, bad in [("~/lab/llm-distillery/inbox/h/2026-10-11/gone/x.jsonl", True),
                          ("`inbox/h/2026-10-11/gone/`", True),
                          ("`inbox/h/2026-10-09/`: `a`, `b`", True),               # a date dir that is gone
                          ("~/lab/llm-distillery/datasets/nope/v1", True),
                          ("~/lab/llm-distillery/inbox/h/2026-10-11/run/model.bin.", False),   # sentence full stop
                          ("`~/lab/llm-distillery/inbox/<host>/2026-10-10/`", False),          # a placeholder
                          # the pre-2026-10-16 prefix: texts written before the move keep it and must
                          # still be checked, against the CURRENT root
                          ("~/ld-lab/inbox/h/2026-10-11/gone/x.jsonl", True),
                          ("~/ld-lab/inbox/h/2026-10-11/run/model.bin", False),
                          ("lab/models/x", False),                                # not a lab prefix
                          ("datasets/training/belonging_c2b", False),             # a REPO path
                          ("experiments/registry.jsonl", False)]:
            with self.subTest(text=text):
                d = self.evidence_dir("2026-10-11-s", text)
                r = self.check()
                self.assertEqual(r.returncode, 1 if bad else 0, r.stdout)
                (d / "README.md").unlink(); d.rmdir()


class RealTree(unittest.TestCase):
    def test_real_evidence_tree_has_no_uncovered_host_citation(self):
        """The half of the check that needs no lab root, on the real tree and the committed
        baseline: this is what makes a new host citation fail the suite rather than wait for a
        hand run. Needs no git history (baseline, not dates), so a shallow clone runs it too."""
        r = subprocess.run([sys.executable, str(CHECK), "--no-lab"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)

    @unittest.skipUnless(Path(os.environ.get("LD_LAB", Path.home() / "lab" / "llm-distillery")).expanduser().is_dir(),
                         "no lab root on this machine (only situla has one)")
    def test_real_manifests_match_the_lab(self):
        r = subprocess.run([sys.executable, str(CHECK), "--fast"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()
