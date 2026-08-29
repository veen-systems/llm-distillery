"""Tests for scripts/corpus/draw_v8_corpus.py against a SYNTHETIC archive whose composition
is known by construction.

⚠️ TWO MUTATIONS SURVIVE THIS SUITE AND ARE EQUIVALENT, NOT HOLES — recorded so nobody
re-chases them: (a) computing the manifest from `drawn` rather than from the rows read back
off disk, and (b) deleting the read-back row-count check. JSON round-trips faithfully, so both
are observationally identical unless the WRITE itself is broken, which is the only thing the
read-back exists to catch. Testing them would need a fault-injected filesystem.

Every test here seeds the positive it is looking for. A draw script that silently under-fills
a quota produces a corpus that looks exactly like one that hit it — so the tests that matter
are the ones asserting it RAISES.
"""
import json, os, random, subprocess, sys, tempfile, unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "corpus" / "draw_v8_corpus.py"

LATIN_TITLE = "Community garden opens in the old rail yard"
NONLATIN_TITLE = "地域の庭が古い操車場に開園しました"
HARM_TITLE = "Three killed in crash as court hears abuse case"


def make_archive(path, n=4000, seed=5, gn_share=0.22, nonlatin_share=0.20,
                 harm_share=0.05, short_share=0.10):
    """Write cycle files whose composition we control exactly."""
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        gn = rng.random() < gn_share
        nl = rng.random() < nonlatin_share
        harm = rng.random() < harm_share
        short = rng.random() < short_share
        # score shape: mostly low, a tail above the op-point
        r = rng.random()
        score = (rng.uniform(0, 1.5) if r < 0.45 else
                 rng.uniform(1.5, 3.5) if r < 0.75 else
                 rng.uniform(3.5, 4.5) if r < 0.90 else
                 rng.uniform(4.5, 5.5) if r < 0.965 else rng.uniform(5.5, 9.0))
        stage = "stage2" if rng.random() < 0.88 else "stage1_low"
        body = ("私たちの町の物語。" * 60) if nl else ("A local story about people. " * 40)
        if short:
            body = body[:120]
        rows.append({
            "id": f"art_{i:06d}",
            "title": (NONLATIN_TITLE if nl else HARM_TITLE if harm else LATIN_TITLE),
            "content": body,
            "url": f"https://{'news.google.com' if gn else f'site{i % 40}.example'}/a/{i}",
            "source": f"src_{i % 40}", "language": "ja" if nl else "en",
            "published_date": "2026-08-20T10:00:00",
            "nexus_mind_attributes": {"uplifting": {
                "raw_weighted_average": score, "stage_used": stage}},
        })
    rng.shuffle(rows)
    for c in range(4):                       # four cycle files, like the real archive
        with open(Path(path) / f"filtered_2026082{c}_120000.jsonl", "w") as f:
            for r in rows[c::4]:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return rows


def run(args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT)] + args, capture_output=True,
                          text=True, cwd=cwd)


class DrawTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.arch = Path(self.tmp.name) / "archive"
        self.out = Path(self.tmp.name) / "out"
        self.arch.mkdir()
        self.rows = make_archive(self.arch)

    def tearDown(self):
        self.tmp.cleanup()

    def test_draw_hits_every_target_and_manifest_reconciles(self):
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "400"], REPO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        corpus = [json.loads(l) for l in open(self.out / "corpus.jsonl", encoding="utf-8")]
        man = json.load(open(self.out / "corpus_manifest.json"))
        # the manifest describes THE FILE, not the request
        self.assertEqual(man["realised"]["rows"], len(corpus), "manifest count != file count")
        self.assertEqual(len(corpus), 400)
        self.assertEqual(len({c["id"] for c in corpus}), 400, "duplicate ids in the draw")
        self.assertTrue(man["all_targets_met"])
        for name, c in man["checks"].items():
            self.assertTrue(c["pass"], f"{name} failed: {c}")

    def test_google_news_is_excluded_and_the_exclusion_is_counted(self):
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "400"], REPO)
        self.assertEqual(r.returncode, 0, r.stderr)
        corpus = [json.loads(l) for l in open(self.out / "corpus.jsonl", encoding="utf-8")]
        self.assertFalse([c for c in corpus if "news.google.com" in (c["url"] or "")])
        man = json.load(open(self.out / "corpus_manifest.json"))
        self.assertGreater(man["exclusions"]["google_news"], 0,
                           "the archive HAS Google News rows; a zero here means the exclusion "
                           "never fired, not that it worked")

    def test_short_form_rows_are_dropped_by_default_and_the_count_is_recorded(self):
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "400"], REPO)
        corpus = [json.loads(l) for l in open(self.out / "corpus.jsonl", encoding="utf-8")]
        self.assertFalse([c for c in corpus if c["content_length"] < 300])
        man = json.load(open(self.out / "corpus_manifest.json"))
        self.assertGreater(man["exclusions"]["short_form_dropped"], 0)

    def test_oversized_request_RAISES_rather_than_under_filling(self):
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "999999"], REPO)
        self.assertNotEqual(r.returncode, 0, "an unfillable quota must not exit 0")
        # ⛔ Pin WHICH failure. A mutation that made take() pad instead of raise still exited
        # non-zero -- via a different FATAL further down -- so `assertIn("FATAL")` alone let it
        # through. A test that cannot say which mechanism fired is not testing that mechanism.
        # ⛔ MENTION IS NOT USE. This assertion first read `assertIn("quota", ...)` and a
        # mutation that padded quotas instead of raising SURVIVED -- because the script prints
        # a per-stratum table with the header "quota" on every successful run, so the word was
        # present whatever happened. Match a phrase that exists ONLY in the failure.
        self.assertIn("do NOT let this pass silently", r.stdout + r.stderr,
                      "expected the per-stratum quota check to be the thing that fails")

    def test_class_a_supplement_carries_TPs_not_only_FPs(self):
        """The owner ruling is 3:1 TP:FP (2026-08-28 spec §3), and it is load-bearing: an
        FP-only supplement teaches "harm words -> suppress" and destroys the §5b no-regression
        set. A mutation setting the TP count to zero survived until this test existed."""
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "400"], REPO)
        self.assertEqual(r.returncode, 0, r.stderr)
        corpus = [json.loads(l) for l in open(self.out / "corpus.jsonl", encoding="utf-8")]
        harm = [c for c in corpus if c["harm_title"]]
        tp = [c for c in harm if c["v7_score"] is not None and c["v7_score"] >= 4.5]
        self.assertGreater(len(tp), 0, "class-A supplement is FP-only — the ruling is 3:1")
        # the drawn supplement is 75% TP by construction; the natural draw adds more of both,
        # so assert the floor the ruling implies rather than an exact ratio
        n_supp = 3                                    # ceil(400 * 0.0070) = 3
        self.assertGreaterEqual(len(tp), round(n_supp * 0.75),
                                "fewer harm-answered rows than the 3:1 split requires")

    def test_manifest_fields_recompute_from_the_written_file(self):
        """The manifest must describe the FILE. `rows` alone cannot show that -- the script
        asserts len(drawn)==size, so rows and the request are provably equal and a mutation
        swapping one for the other is unobservable. These fields are not."""
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "400"], REPO)
        self.assertEqual(r.returncode, 0, r.stderr)
        corpus = [json.loads(l) for l in open(self.out / "corpus.jsonl", encoding="utf-8")]
        man = json.load(open(self.out / "corpus_manifest.json"))["realised"]
        n = len(corpus)
        self.assertAlmostEqual(man["non_latin_share"],
                               sum(c["non_latin"] for c in corpus) / n, places=9)
        self.assertAlmostEqual(man["class_a_share"],
                               sum(c["harm_title"] for c in corpus) / n, places=9)
        self.assertAlmostEqual(man["under_oracle_floor"],
                               sum(c["content_length"] < 300 for c in corpus) / n, places=9)
        self.assertEqual(man["distinct_domains"], len({c["domain"] for c in corpus}))

    def test_topup_fires_when_the_pool_is_poor_in_a_constrained_class(self):
        """Seeded positive for the constraint-repair path. The default archive is 20%
        non-Latin, so a 9.76% target is met by luck and the top-up never runs -- a mutation
        deleting it survived until this test existed."""
        poor = Path(self.tmp.name) / "poor"
        poor.mkdir()
        make_archive(poor, n=4000, seed=9, nonlatin_share=0.04)
        out = Path(self.tmp.name) / "poor_out"
        r = run(["--archive", str(poor), "--out", str(out), "--size", "400",
                 "--nonlatin-min", "0.15"], REPO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        man = json.load(open(out / "corpus_manifest.json"))
        self.assertGreaterEqual(man["realised"]["non_latin_share"], 0.15,
                                "the pool is 4% non-Latin against a 15% target -- meeting it "
                                "requires the allocator to over-draw non-Latin rows in every "
                                "stratum, not to get lucky")
        self.assertIn("allocated by construction", man["constraint_method"])

    def test_unreachable_constraint_RAISES(self):
        """⚠️ The first version of this test asked for 90% non-Latin from a 20% non-Latin
        archive and asserted a failure. That premise was WRONG: at --size 400 the draw needs
        360 non-Latin rows and the pool holds ~566, so 90% is perfectly reachable. It passed
        only because the old repair-based code raised for an unrelated reason. Unreachability
        is about the ABSOLUTE count against supply, not the share."""
        poor = Path(self.tmp.name) / "poor2"
        poor.mkdir()
        make_archive(poor, n=4000, seed=11, nonlatin_share=0.04)     # ~110 non-Latin drawable
        r = run(["--archive", str(poor), "--out", str(self.out), "--size", "400",
                 "--nonlatin-min", "0.90"], REPO)                     # needs 360 > supply
        self.assertNotEqual(r.returncode, 0, "an unreachable target must not pass silently")
        self.assertIn("cannot meet the non-Latin target", r.stdout + r.stderr)

    def test_a_reachable_high_target_is_actually_reached(self):
        """The control for the test above: same mechanism, a target the pool CAN meet. Without
        this, a raise-always bug would look like correct behaviour."""
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "400",
                 "--nonlatin-min", "0.90"], REPO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        man = json.load(open(self.out / "corpus_manifest.json"))
        self.assertGreaterEqual(man["realised"]["non_latin_share"], 0.90)

    def test_seeded_draw_is_deterministic(self):
        out2 = Path(self.tmp.name) / "out2"
        a = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "300"], REPO)
        b = run(["--archive", str(self.arch), "--out", str(out2), "--size", "300"], REPO)
        self.assertEqual(a.returncode, 0)
        self.assertEqual(b.returncode, 0)
        ids_a = [json.loads(l)["id"] for l in open(self.out / "corpus.jsonl")]
        ids_b = [json.loads(l)["id"] for l in open(out2 / "corpus.jsonl")]
        self.assertEqual(ids_a, ids_b, "same seed must give the same corpus")

    def test_empty_archive_RAISES(self):
        empty = Path(self.tmp.name) / "empty"
        empty.mkdir()
        r = run(["--archive", str(empty), "--out", str(self.out), "--size", "10"], REPO)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("FATAL", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
