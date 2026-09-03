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
# ⛔ Must match the PRODUCTION class-A instrument (v7 prefilter crime_violence), not a
# plausible-looking harm sentence. The first fixture read "Three killed in crash as court
# hears abuse case" and matched ZERO of its 37 patterns -- "killed" and bare "abuse" are
# not among them ("child abuse" is) -- so every class-A assertion below was inert against
# the instrument that actually runs. This title matches three patterns.
HARM_TITLE = "Man convicted of murder after domestic violence case"


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
        # ⛔ Each body must be UNIQUE. The first fixture gave every Latin row the same text,
        # which was invisible until content-dedup was added -- then the whole pool collapsed to
        # two rows and every test failed with "no negative rows". A fixture whose rows are
        # accidentally identical tests nothing about a population.
        body = (f"記事番号{i}。私たちの町の物語。" + "私たちの町の物語。" * 60) if nl else \
               (f"Story {i}. A local story about people. " + "A local story about people. " * 40)
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
    # ⛔ The fixture must exercise BOTH dedup branches or they are inert: 20 ids repeated in a
    # later cycle file (the real archive rescores articles), and 10 rows that are the same TEXT
    # under a DIFFERENT id (ids are source-scoped, so id-dedup is not text-dedup). A mutation
    # inverting the dedup rule survived the suite until these existed.
    repeats = [dict(r) for r in rows[:20]]
    text_twins = []
    for i, r in enumerate(rows[20:30]):
        t = dict(r)
        t["id"] = r["id"] + "_twin"
        t["url"] = r["url"] + "?twin"
        text_twins.append(t)
    for c in range(4):                       # four cycle files, like the real archive
        chunk = rows[c::4]
        if c == 3:
            chunk = chunk + repeats + text_twins
        with open(Path(path) / f"filtered_2026082{c}_120000.jsonl", "w") as f:
            for r in chunk:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return rows


def run(args, cwd):
    return subprocess.run([sys.executable, str(SCRIPT)] + args, capture_output=True,
                          text=True, cwd=cwd)


class FixtureSanityTest(unittest.TestCase):
    """A fixture that the production instrument does not recognise makes every class-A
    assertion in this file vacuously true. Check the fixture itself."""

    def test_harm_fixture_matches_the_production_class_a_instrument(self):
        sys.path.insert(0, str(REPO))
        from filters.uplifting.v7.prefilter import UpliftingPreFilterV7
        pats = UpliftingPreFilterV7()._compiled_exclusions["crime_violence"]
        self.assertGreater(sum(1 for p in pats if p.search(HARM_TITLE)), 0,
                           "the harm fixture matches none of the 37 crime_violence patterns — "
                           "every class-A test here would pass on an empty class")
        self.assertEqual(sum(1 for p in pats if p.search(LATIN_TITLE)), 0,
                         "the benign fixture matches the harm instrument — the control is dirty")


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
        # present whatever happened. Match a phrase that exists ONLY in a failure.
        # ⚠️ Which failure fires FIRST changed when the class-A arm moved above the op-point:
        # the supplement's supply is now the binding constraint at absurd sizes. Both
        # mechanisms are pinned, here and in the test below, rather than accepting any FATAL.
        self.assertIn("class-A supplement needs", r.stdout + r.stderr,
                      "at this size the class-A supply is the first binding constraint")

    def test_per_stratum_quota_RAISES_when_class_a_is_not_the_binding_constraint(self):
        """The other raise path: ask for more rows than a score stratum holds, with the
        class-A floor set low enough that it is satisfiable."""
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "9999",
                 "--class-a-min", "0.0001", "--nonlatin-min", "0.0"], REPO)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("do NOT let this pass silently", r.stdout + r.stderr)

    def test_class_a_supplement_is_drawn_ABOVE_the_op_point(self):
        """⛔ Spec, verbatim: "Sample the supplement ABOVE the op-point (ADR-023): that is
        where junk reaches readers. Do not hunt the cheap error below it." The first version
        drew its FP arm from harm-title rows scoring BELOW 3.85 -- rows the student already
        gets right, so the supplement taught nothing. No test caught it."""
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "400"], REPO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        man = json.load(open(self.out / "corpus_manifest.json"))
        lo, hi = man["class_a"]["supplement"]["score_range"]
        self.assertGreaterEqual(lo, 4.5,
                                "a supplement row scored below the op-point — the spec forbids it")
        corpus = [json.loads(l) for l in open(self.out / "corpus.jsonl", encoding="utf-8")]
        # and the supplement must not be drawn from stage1_low, whose score is a probe estimate
        supp_like = [c for c in corpus if c["harm_title"] and c["v7_score"] is not None
                     and c["v7_score"] >= 4.5]
        self.assertFalse([c for c in supp_like if c["v7_stage_used"] == "stage1_low"],
                         "a stage1_low row entered the class-A pool — that score is an e5 "
                         "probe estimate, not a Gemma score")

    def test_recall_cohort_is_reserved_and_disjoint(self):
        """Spec clause (d): the FN check needs a production-mix cohort, and the corpus IS the
        probe's training set — so a cohort carved out later overlaps it. Reserving it at draw
        time is the only moment it can be disjoint by construction."""
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "400",
                 "--recall-cohort", "80"], REPO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        corpus = {json.loads(l)["id"] for l in open(self.out / "corpus.jsonl", encoding="utf-8")}
        cohort = [json.loads(l) for l in open(self.out / "recall_cohort.jsonl", encoding="utf-8")]
        self.assertEqual(len(cohort), 80)
        self.assertFalse(corpus & {c["id"] for c in cohort}, "cohort overlaps the corpus")
        man = json.load(open(self.out / "corpus_manifest.json"))
        self.assertEqual(man["recall_cohort"]["rows"], 80)
        # its positive rate must be PRODUCTION's, not the corpus's enriched 19.5%
        self.assertLess(man["recall_cohort"]["positive_rate"], man["realised"]["positive_rate"],
                        "the cohort is enriched like the corpus — then it cannot measure "
                        "production recall")

    def test_class_a_ratio_is_declared_as_UNSET_not_silently_reported(self):
        """The ruled 3:1 is a shape judgement ("harm answered" vs "harm dominant") within the
        above-op population. A score cannot make it. The manifest must SAY so rather than
        report a score-proxy ratio that reads like compliance."""
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "400"], REPO)
        self.assertEqual(r.returncode, 0)
        man = json.load(open(self.out / "corpus_manifest.json"))["class_a"]
        self.assertIn("adjudicat", man["supplement"]["tp_fp_status"].lower())
        self.assertEqual(man["supplement"]["ruled_tp_fp"], 3.0)
        # ⛔ The key was CALLED corpus_level_tp_fp until 2026-08-30, and being called a TP:FP
        # is what made it get read as one: 47/33 was quoted as "1.42:1 against a ruled 3:1",
        # producing an "unreachable, needs 62 of 59" conclusion the owner ruling retired. The
        # old name must not come back, and the note must name the quantity it actually is.
        self.assertNotIn("corpus_level_tp_fp", man,
                         "the misleading key name is back; it is above-op : below-op, not TP:FP")
        self.assertIn("corpus_level_above_below_op_ratio", man)
        note = man["corpus_level_note"]
        self.assertIn("NOT the ruled", note)
        self.assertIn("above-op", note)
        self.assertIn("below-op", note)

    def test_dedup_removes_repeated_ids_AND_repeated_text_under_new_ids(self):
        """Both branches, each with a seeded positive. The fixture plants 20 repeated ids and
        10 same-text-different-id rows."""
        r = run(["--archive", str(self.arch), "--reduce", str(Path(self.tmp.name) / "p.jsonl")],
                REPO)
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = open(Path(self.tmp.name) / "p.jsonl", encoding="utf-8").read().splitlines()
        prov = json.loads(lines[0])["__provenance__"]["counts"]
        self.assertGreaterEqual(prov["dup_rows"], 20, "repeated ids were not deduplicated")
        self.assertGreaterEqual(prov["dup_text_other_id"], 10,
                                "same text under a different id survived — id-dedup is not "
                                "text-dedup, and a duplicate straddling the train/test split "
                                "inflates the test metric")
        rows = [json.loads(x) for x in lines[1:]]
        self.assertEqual(len(rows), len({x["id"] for x in rows}))
        self.assertEqual(len(rows), len({x["content_sha256"] for x in rows}))

    def test_realised_rates_match_values_the_TEST_computes(self):
        """`all_targets_met` is the script grading its own homework. These numbers are
        recomputed here, from the corpus file, against the ruled literals."""
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "400"], REPO)
        self.assertEqual(r.returncode, 0, r.stderr)
        corpus = [json.loads(l) for l in open(self.out / "corpus.jsonl", encoding="utf-8")]
        s2 = [c for c in corpus if c["v7_stage_used"] == "stage2" and c["v7_score"] is not None]
        pos = [c for c in s2 if c["v7_score"] >= 4.5]
        self.assertAlmostEqual(len(pos) / len(corpus), 0.195, delta=0.02)
        marg = [c for c in pos if c["v7_score"] < 5.5]
        self.assertAlmostEqual(len(marg) / len(pos), 0.635, delta=0.05)
        man = json.load(open(self.out / "corpus_manifest.json"))["realised"]
        self.assertAlmostEqual(man["positive_rate"], len(pos) / len(corpus), places=9)
        self.assertAlmostEqual(man["positive_rate_stage2"], len(pos) / len(s2), places=9,
                               msg="the manifest must carry BOTH denominators — reporting only "
                                   "the all-rows one hid a 2.20x-vs-2.0x enrichment error")

    def test_stage1_low_coverage_tracks_the_pool(self):
        """The plan: "draw from the FULL pool, including stage1_low — the probe must not shape
        the draw". Nothing asserted it, so halving the stage1_low quota passed the suite."""
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "400"], REPO)
        self.assertEqual(r.returncode, 0)
        man = json.load(open(self.out / "corpus_manifest.json"))
        pool = man["pool_strata"]
        pool_share = pool["stage1_low"] / sum(v for k, v in pool.items()
                                              if k != "unstratifiable")
        self.assertAlmostEqual(man["realised"]["stage1_low_share"], pool_share, delta=0.02,
                               msg="stage1_low coverage does not track the pool — the probe is "
                                   "shaping the draw")

    def test_non_latin_is_the_census_instrument_not_a_local_one(self):
        """A hand-written script test (50%/400 chars) shipped under a comment claiming it was
        the census's (15%/2000). On the same rows the two differ by ~0.45pp — the same size as
        a claim it was used to support."""
        sys.path.insert(0, str(REPO / "scripts" / "analysis"))
        sys.path.insert(0, str(REPO / "scripts" / "corpus"))
        from prefilter_removal_probe import script_of
        import draw_v8_corpus as D
        for text in ("Ολυμπιακός Πειραιώς ποδόσφαιρο πρωτάθλημα αγώνας",
                     "A perfectly ordinary English sentence about a garden.",
                     "日本語のテキストがここにあります、これは長い文章です"):
            self.assertEqual(D.script_is_non_latin(text), script_of(text) == "non_latin",
                             f"drawer and census disagree on: {text[:30]}")

    def test_per_stratum_non_latin_shares_track_the_pool(self):
        """The script x score association production has must survive the draw. Two earlier
        allocation rules broke it in opposite directions (flattened to 0.994x, then 0.434x
        against a pool value of 0.917x)."""
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "400"], REPO)
        self.assertEqual(r.returncode, 0)
        na = json.load(open(self.out / "corpus_manifest.json"))["non_latin_allocation"]
        for k, pool_share in na["per_stratum_pool_share"].items():
            if pool_share == 0:
                continue
            self.assertAlmostEqual(na["per_stratum_drawn"][k], pool_share, delta=0.05,
                                   msg=f"{k}: drawn non-Latin share departs from the pool's")

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


MATERIALISE = REPO / "scripts" / "corpus" / "materialise_corpus.py"


class ReduceDrawMaterialiseTest(unittest.TestCase):
    """The three-phase pipeline: reduce where the data is, draw where the repo is (so the
    op-point is imported, not copied), materialise the winners back."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.arch = Path(self.tmp.name) / "archive"
        self.arch.mkdir()
        make_archive(self.arch)
        self.pool = Path(self.tmp.name) / "pool.jsonl"
        self.out = Path(self.tmp.name) / "out"

    def tearDown(self):
        self.tmp.cleanup()

    def _reduce(self):
        r = run(["--archive", str(self.arch), "--reduce", str(self.pool)], REPO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def test_reduced_pool_carries_no_article_text(self):
        self._reduce()
        rows = [json.loads(l) for l in open(self.pool, encoding="utf-8")][1:]
        self.assertGreater(len(rows), 0)
        self.assertFalse([r for r in rows if "content" in r],
                         "the reduced pool must not carry article text")
        self.assertTrue(all(r["content_sha256"] for r in rows))
        self.assertTrue(all(r["content_length"] > 0 for r in rows))

    def test_draw_from_pool_then_materialise_round_trips(self):
        self._reduce()
        r = run(["--pool", str(self.pool), "--out", str(self.out), "--size", "300"], REPO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        man = json.load(open(self.out / "corpus_manifest.json"))
        self.assertIn("metadata only", man["provenance"]["drawn_from"])
        full = Path(self.tmp.name) / "full.jsonl"
        m = subprocess.run([sys.executable, str(MATERIALISE), "--corpus",
                            str(self.out / "corpus.jsonl"), "--archive", str(self.arch),
                            "--out", str(full)], capture_output=True, text=True)
        self.assertEqual(m.returncode, 0, m.stdout + m.stderr)
        rows = [json.loads(l) for l in open(full, encoding="utf-8")]
        self.assertEqual(len(rows), 300)
        self.assertTrue(all(len(r["content"]) == r["content_length"] for r in rows),
                        "materialised text must match the length recorded at reduction")

    def test_materialise_REFUSES_when_the_archive_text_changed(self):
        """Seeded positive for the sha guard. An id is not proof you rejoined the same
        article — the archive rolls and rows get rewritten."""
        self._reduce()
        run(["--pool", str(self.pool), "--out", str(self.out), "--size", "300"], REPO)
        # rewrite ONE archived article's text, keeping its id
        victim = json.loads(open(self.out / "corpus.jsonl", encoding="utf-8").readline())["id"]
        touched = False
        for f in sorted(self.arch.glob("filtered_*.jsonl")):
            rows = [json.loads(l) for l in open(f, encoding="utf-8")]
            for r in rows:
                if r["id"] == victim:
                    r["content"] = r["content"] + " (edited after the draw)"
                    touched = True
            with open(f, "w", encoding="utf-8") as fh:
                for r in rows:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        self.assertTrue(touched, "the victim id was not found in the archive — test is inert")
        full = Path(self.tmp.name) / "full2.jsonl"
        m = subprocess.run([sys.executable, str(MATERIALISE), "--corpus",
                            str(self.out / "corpus.jsonl"), "--archive", str(self.arch),
                            "--out", str(full)], capture_output=True, text=True)
        self.assertNotEqual(m.returncode, 0, "changed text must be fatal, not a warning")
        self.assertIn("text has CHANGED", m.stdout + m.stderr)

    def test_materialise_REFUSES_a_corpus_that_already_has_text(self):
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "100"], REPO)
        self.assertEqual(r.returncode, 0)
        m = subprocess.run([sys.executable, str(MATERIALISE), "--corpus",
                            str(self.out / "corpus.jsonl"), "--archive", str(self.arch),
                            "--out", str(Path(self.tmp.name) / "x.jsonl")],
                           capture_output=True, text=True)
        self.assertNotEqual(m.returncode, 0)
        self.assertIn("already carries article text", m.stdout + m.stderr)


class NoRegressionExclusionTest(unittest.TestCase):
    """The acceptance-test rows must never be drawn into the corpus they are meant to judge.

    ⛔ Nothing enforced this until 2026-08-30, and the first real draw came out disjoint only
    because every row then in the set had aged out of the archive window -- so the pool could
    not contain them. That is a negative carrying no information: the instrument could not
    have said yes. Every test here therefore SEEDS ids that are genuinely in the pool, and the
    first assertion is that they were reachable before checking that they were removed.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.arch = Path(self.tmp.name) / "arch"
        self.arch.mkdir()
        make_archive(self.arch)
        self.out = Path(self.tmp.name) / "out"
        self.nr = Path(self.tmp.name) / "nr.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def _write_set(self, ids):
        with open(self.nr, "w", encoding="utf-8") as fh:
            for i in ids:
                fh.write(json.dumps({"id": i, "label": "no_regression"}) + "\n")

    def _drawable_ids(self, n):
        """Ids that survive every other exclusion, so the test is not silently asserting
        against rows the Google News or short-form filters removed anyway."""
        probe_out = Path(self.tmp.name) / "probe"
        r = run(["--archive", str(self.arch), "--out", str(probe_out), "--size", "400",
                 "--no-regression-set", str(self.nr)], REPO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        ids = [json.loads(l)["id"] for l in open(probe_out / "corpus.jsonl", encoding="utf-8")]
        return ids[:n]

    def test_seeded_rows_are_reachable_and_then_removed(self):
        self._write_set(["art_999999"])          # a placeholder so the probe draw can run
        victims = self._drawable_ids(2)
        self.assertEqual(len(victims), 2, "fixture produced no drawable rows to seed with")

        self._write_set(victims)
        out2 = Path(self.tmp.name) / "out2"
        r = run(["--archive", str(self.arch), "--out", str(out2), "--size", "400",
                 "--no-regression-set", str(self.nr)], REPO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

        drawn = {json.loads(l)["id"] for l in open(out2 / "corpus.jsonl", encoding="utf-8")}
        for v in victims:
            self.assertNotIn(v, drawn, f"{v} is in the no-regression set and was drawn anyway")

        man = json.load(open(out2 / "corpus_manifest.json"))
        self.assertEqual(man["exclusions"]["no_regression_ids_declared"], 2)
        self.assertEqual(man["exclusions"]["no_regression_rows_removed"], 2,
                         "declared and removed must agree when both seeded rows are in the pool")

    def test_declared_and_removed_are_reported_separately(self):
        """An id that is not in the window must not be counted as a removal. 'Declared' and
        'removed' differing is the normal case once the archive rolls, and only the second
        number is evidence the filter did anything."""
        self._write_set(["art_999999"])
        victims = self._drawable_ids(1)
        self._write_set(victims + ["art_999999", "art_999998"])
        out2 = Path(self.tmp.name) / "out3"
        r = run(["--archive", str(self.arch), "--out", str(out2), "--size", "400",
                 "--no-regression-set", str(self.nr)], REPO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        man = json.load(open(out2 / "corpus_manifest.json"))
        self.assertEqual(man["exclusions"]["no_regression_ids_declared"], 3)
        self.assertEqual(man["exclusions"]["no_regression_rows_removed"], 1)

    def test_draw_REFUSES_when_the_set_is_missing(self):
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "200",
                 "--no-regression-set", str(Path(self.tmp.name) / "absent.jsonl")], REPO)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no-regression set not found", r.stdout + r.stderr)
        self.assertFalse(self.out.exists(), "a refusal must not leave an output directory")

    def test_draw_REFUSES_when_the_set_is_empty(self):
        self.nr.write_text("", encoding="utf-8")
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "200",
                 "--no-regression-set", str(self.nr)], REPO)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("holds no rows", r.stdout + r.stderr)
        self.assertFalse(self.out.exists())

    def test_draw_REFUSES_when_a_row_has_no_id(self):
        with open(self.nr, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"title": "a row with no id"}) + "\n")
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "200",
                 "--no-regression-set", str(self.nr)], REPO)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("has no id", r.stdout + r.stderr)

    def test_draw_REFUSES_the_ADVERSE_set_pointed_at_this_flag(self):
        """⛔ Seeded positive for the wrong-file hazard. datasets/adverse/uplifting.jsonl sits
        in the same directory with the same shape and 18 rows labelled "adverse". An id-only
        loader would run clean and strip 18 adverse training examples out of the corpus."""
        with open(self.nr, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"id": "art_000001", "label": "adverse"}) + "\n")
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "200",
                 "--no-regression-set", str(self.nr)], REPO)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not 'no_regression'", r.stdout + r.stderr)
        self.assertFalse(self.out.exists())

    def test_the_real_adverse_set_would_be_refused(self):
        """The hazard named against the file that actually exists, not a fixture of it."""
        adverse = REPO / "datasets" / "adverse" / "uplifting.jsonl"
        self.assertTrue(adverse.exists())
        r = run(["--archive", str(self.arch), "--out", str(self.out), "--size", "200",
                 "--no-regression-set", str(adverse)], REPO)
        self.assertNotEqual(r.returncode, 0, "the adverse set was accepted as an exclusion list")
        self.assertIn("ACCEPTANCE-TEST set", r.stdout + r.stderr)

    def test_a_SHORT_guard_row_is_still_counted_as_removed(self):
        """⛔ Order regression test. The exclusion ran AFTER the short-form filter until
        2026-08-30: a guard row under the 300-char floor was dropped as short, counted as ZERO
        removals, and reported as 'not in the drawable pool' -- a message asserting a reason it
        had not established. The fixture plants short rows, so this seeds its own positive."""
        self._write_set(["art_999999"])
        probe_out = Path(self.tmp.name) / "probe_short"
        r = run(["--archive", str(self.arch), "--out", str(probe_out), "--size", "400",
                 "--short-form", "include", "--no-regression-set", str(self.nr)], REPO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        shorts = [json.loads(l) for l in open(probe_out / "corpus.jsonl", encoding="utf-8")]
        short_ids = [d["id"] for d in shorts if d["content_length"] < 300]
        self.assertTrue(short_ids, "fixture produced no short rows to seed with")

        self._write_set([short_ids[0]])
        out2 = Path(self.tmp.name) / "out_short"
        r = run(["--archive", str(self.arch), "--out", str(out2), "--size", "400",
                 "--short-form", "exclude", "--no-regression-set", str(self.nr)], REPO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        man = json.load(open(out2 / "corpus_manifest.json"))
        self.assertEqual(man["exclusions"]["no_regression_rows_removed"], 1,
                         "a short guard row was dropped as short and never counted as removed")

    def test_the_shipped_set_is_loadable_and_every_row_has_an_id(self):
        """The default path is the one the real draw uses. A set that cannot be parsed makes
        every draw refuse, so this is a live dependency, not a fixture."""
        real = REPO / "datasets" / "adverse" / "uplifting_no_regression.jsonl"
        self.assertTrue(real.exists(), f"{real} is the drawer's default input")
        rows = [json.loads(l) for l in open(real, encoding="utf-8") if l.strip()]
        self.assertGreater(len(rows), 0)
        self.assertTrue(all(r.get("id") for r in rows))
        self.assertEqual(len({r["id"] for r in rows}), len(rows), "duplicate ids in the set")
        self.assertTrue(all(r.get("label") == "no_regression" for r in rows),
                        "the loader refuses any row not labelled no_regression")
        # A retired row must not silently reappear in the live set.
        retired = REPO / "datasets" / "adverse" / "uplifting_no_regression_retired.jsonl"
        if retired.exists():
            gone = {json.loads(l)["id"] for l in open(retired, encoding="utf-8") if l.strip()}
            self.assertFalse(gone & {r["id"] for r in rows},
                             "a retired row is back in the live no-regression set")


if __name__ == "__main__":
    unittest.main(verbosity=2)



class HardNegativeDrawabilityReportTest(unittest.TestCase):
    """A drawn hard negative gets an ORACLE label instead of its editorial `negative`.

    ⛔ `datasets/adverse/uplifting.jsonl` is deliberately NOT a guard set: 7 of its 18 rows
    carry `training_use: HARD NEGATIVE ... §4b`, so they are INTENDED training inputs, and
    load_no_regression_ids() refuses that file on purpose. Widening the exclusion to cover it
    was tried on 2026-09-03 and correctly KILLED by NoRegressionExclusionTest above — the
    tests were the control working.

    What was missing is that the two paths disagree silently. A designated hard negative is
    ADDED with an editorial `negative`; a row DRAWN is labelled BY THE ORACLE, and these rows
    are adverse precisely because a scorer read them as positive. Measured that day: 3 of the
    18 were drawable at p = 0.0810 / 0.0794 / 0.0794, none drawn, P(all escaped) = 0.7787.
    So the draw REPORTS (ADR-022) and does not exclude. These tests pin the report.
    """

    @staticmethod
    def _hard_negative_ids():
        ids = []
        with open(os.path.join(REPO, "datasets/adverse/uplifting.jsonl"), encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    row = json.loads(line)
                    if row.get("training_use"):
                        ids.append(row["id"])
        return ids

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.arch = Path(self.tmp.name) / "arch"
        self.arch.mkdir()
        make_archive(self.arch)
        self.nr = Path(self.tmp.name) / "nr.jsonl"
        with open(self.nr, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"id": "art_999999", "label": "no_regression"}) + "\n")

    def tearDown(self):
        self.tmp.cleanup()

    def _seed(self, rid):
        """Put `rid` into the archive as a drawable, above-op, Latin, long-body row."""
        row = {
            "id": rid, "title": LATIN_TITLE,
            "content": "Seeded body about people. " * 60,
            "url": "https://seed.example/a/1", "source": "src_seed", "language": "en",
            "published_date": "2026-08-20T10:00:00",
            "nexus_mind_attributes": {"uplifting": {
                "raw_weighted_average": 6.4, "stage_used": "stage2"}},
        }
        with open(self.arch / "filtered_20260829_999999.jsonl", "w", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")

    def _run(self):
        out = Path(self.tmp.name) / f"out{random.randint(0, 10**9)}"
        r = run(["--archive", str(self.arch), "--out", str(out), "--size", "400",
                 "--no-regression-set", str(self.nr)], REPO)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout + r.stderr, out

    def test_reports_zero_and_does_not_warn_when_none_is_drawable(self):
        out, _ = self._run()
        self.assertIn("designated hard negatives", out)
        self.assertIn("0 of them DRAWABLE", out)
        self.assertNotIn("receive an ORACLE label", out,
                         "must not warn when the collision cannot happen")

    def test_names_a_drawable_hard_negative_and_warns(self):
        hn = self._hard_negative_ids()
        self.assertTrue(hn, "fixture assumption: the suite declares hard negatives")
        self._seed(hn[0])
        out, outdir = self._run()
        self.assertIn("1 of them DRAWABLE", out)
        self.assertIn("receive an ORACLE label", out)
        self.assertIn(hn[0], out)
        man = json.load(open(outdir / "corpus_manifest.json"))
        self.assertEqual(man["exclusions"]["hard_negatives_drawable"], [hn[0]])

    def test_a_drawable_hard_negative_is_REPORTED_NOT_REMOVED(self):
        """The deliberate design: these rows stay eligible. Reporting must not exclude them."""
        hn = self._hard_negative_ids()
        self._seed(hn[0])
        out, outdir = self._run()
        man = json.load(open(outdir / "corpus_manifest.json"))
        self.assertEqual(man["exclusions"]["no_regression_rows_removed"], 0,
                         "the adverse row must NOT be counted as a guard removal")
        self.assertGreater(man["exclusions"]["hard_negatives_declared"], 0)

    def test_declared_count_matches_the_suite_on_disk(self):
        out, _ = self._run()
        n = len(self._hard_negative_ids())
        self.assertIn(f"{n} declared", out,
                      "the reported count must come from the file, not a constant")
