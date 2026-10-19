"""#177 oracle canary: the gate's branches, the comparison, and a scorer refusing BEFORE its first paid call."""
import json
import sys
import time
from pathlib import Path

import pytest

from ground_truth import oracle_canary as oc

ROOT = Path(__file__).resolve().parents[2]
SHA = "ab" * 32


@pytest.fixture
def dirs(tmp_path, monkeypatch):
    cfg, data = tmp_path / "config", tmp_path / "data"
    cfg.mkdir()
    monkeypatch.setattr(oc, "CONFIG_DIR", cfg)
    monkeypatch.setattr(oc, "DATA_DIR", data)
    return cfg, data


ORACLE = "https://api.deepseek.com/v1/chat/completions|deepseek-chat"


def _baseline(cfg, sha=SHA, stripped=None, oracle=ORACLE):
    (cfg / "f.baseline.json").write_text(json.dumps({"filter": "f", "prompt_sha256": sha,
                                                    "prompt_sha256_stripped": stripped, "oracle": oracle}))


def _record(verdict, age_h, now):
    rec = oc.write_record("f", SHA, {"verdict": verdict, "flips": 9, "shift": -0.9}, set(),
                          now=now - age_h * 3600)
    return rec


class TestGate:
    def test_no_set_stamps_and_never_refuses(self, dirs):
        assert oc.gate(SHA, oracle=ORACLE) == {"verdict": "no-set"}

    def test_skip_is_stamped_with_its_reason(self, dirs):
        _baseline(dirs[0])
        assert oc.gate(SHA, "vendor outage") == {"skipped": "vendor outage"}

    def test_a_guarded_prompt_with_no_record_is_REFUSED(self, dirs):
        _baseline(dirs[0])
        with pytest.raises(oc.CanaryRefused, match="no canary run on record"):
            oc.gate(SHA, oracle=ORACLE)

    def test_a_FAILED_latest_record_is_REFUSED_even_when_fresh(self, dirs):
        _baseline(dirs[0]); now = time.time()
        _record("PASS", 3, now)
        _record("FAIL", 1, now)                   # the latest wins
        with pytest.raises(oc.CanaryRefused, match="is FAIL "):
            oc.gate(SHA, now=now, oracle=ORACLE)

    def test_a_stale_PASS_is_REFUSED(self, dirs):
        _baseline(dirs[0]); now = time.time()
        _record("PASS", oc.FRESH_HOURS + 0.5, now)
        with pytest.raises(oc.CanaryRefused, match="h old"):
            oc.gate(SHA, now=now, oracle=ORACLE)

    def test_a_fresh_PASS_lets_the_run_through_and_names_its_record(self, dirs):
        _baseline(dirs[0]); now = time.time()
        rec = _record("PASS", 1, now)
        st = oc.gate(SHA, now=now, oracle=ORACLE)
        assert st["verdict"] == "PASS" and st["record"] == rec["record"]

    def test_a_PASS_admits_ONE_labelling_run(self, dirs):
        """Owner 2026-10-16: the canary runs before EVERY labelling run, so a PASS is consumed by the run it admits."""
        _baseline(dirs[0]); now = time.time()
        _record("PASS", 0.1, now)
        oc.gate(SHA, now=now, oracle=ORACLE)
        with pytest.raises(oc.CanaryRefused, match="already used"):
            oc.gate(SHA, now=now, oracle=ORACLE)

    def test_a_NO_VERDICT_after_a_PASS_is_REFUSED(self, dirs):
        _baseline(dirs[0]); now = time.time()
        _record("PASS", 1, now)
        oc.write_record("f", SHA, {"verdict": "NO-VERDICT", "reason": "x"}, set(), now=now)
        with pytest.raises(oc.CanaryRefused, match="NO-VERDICT"):
            oc.gate(SHA, now=now, oracle=ORACLE)

    def test_ANOTHER_oracle_is_REFUSED_even_with_a_fresh_PASS(self, dirs):
        _baseline(dirs[0]); now = time.time()
        _record("PASS", 1, now)
        with pytest.raises(oc.CanaryRefused, match="no canary covers it"):
            oc.gate(SHA, now=now, oracle="https://generativelanguage.googleapis.com|gemini-2.5-flash")

    def test_the_STRIPPED_digest_is_recognised_as_the_same_prompt(self, dirs):
        """batch_scorer hashes the stripped template; matching only the raw digest left it unguarded (review)."""
        _baseline(dirs[0], stripped="cd" * 32)
        with pytest.raises(oc.CanaryRefused):
            oc.gate("cd" * 32, oracle="batch_scorer|gemini-flash")

    def test_a_record_for_ANOTHER_prompt_does_not_count(self, dirs):
        _baseline(dirs[0]); now = time.time()
        oc.write_record("f", "cd" * 32, {"verdict": "PASS", "flips": 0, "shift": 0.0}, set(), now=now)
        with pytest.raises(oc.CanaryRefused):
            oc.gate(SHA, now=now, oracle=ORACLE)


class TestComparison:
    def test_flips_count_verdict_changes_at_the_op_point_only(self):
        base = {"a": 4.6, "b": 4.4, "c": 1.0}
        assert oc.compare({"a": 4.4, "b": 4.6, "c": 3.0}, base, 4.5)["flips"] == 2

    def test_flips_are_counted_at_THIS_filters_op_point(self):
        """nature_recovery's op-point is 3.75: at a hard-coded 4.5 this pair would count 0 flips."""
        assert oc.compare({"a": 3.7}, {"a": 3.8}, 3.75)["flips"] == 1
        assert oc.compare({"a": 3.7}, {"a": 3.8}, 4.5)["flips"] == 0

    def test_shift_is_the_mean_signed_delta(self):
        assert oc.compare({"a": 2.0, "b": 2.0}, {"a": 3.0, "b": 3.0}, 4.5)["shift"] == -1.0

    def test_verdict_uses_the_preregistered_margins(self):
        bar = {"F": 3, "S": 0.10}
        assert oc.verdict({"flips": 4, "shift": 0.0}, bar) == "PASS"      # 3 + 1
        assert oc.verdict({"flips": 5, "shift": 0.0}, bar) == "FAIL"
        assert oc.verdict({"flips": 0, "shift": -0.26}, bar) == "FAIL"    # 0.10 + 0.15
        assert oc.verdict({"flips": 0, "shift": -0.24}, bar) == "PASS"

    def test_noise_k3_takes_each_split_of_six_once(self):
        runs = [{"a": float(i), "b": 4.5} for i in range(6)]
        assert len(oc.noise(runs, 4.5)["k3"]["each"]) == 10

    def test_a_missing_scoring_spec_RAISES_not_falls_back(self, tmp_path):
        bad = tmp_path / "c.yaml"; bad.write_text("filter: {name: x}\n")
        with pytest.raises(ValueError):
            oc.spec_for(bad)


class TestSet:
    def test_a_set_whose_bytes_drift_from_the_manifest_is_refused(self, dirs):
        cfg, data = dirs
        (data / "f").mkdir(parents=True)
        (data / "f" / "set.jsonl").write_text('{"id": "a"}\n')
        (cfg / "f.json").write_text(json.dumps({"set_sha256": "0" * 64}))
        with pytest.raises(oc.CanaryRefused, match="!= manifest"):
            oc.verify_set("f")

    def test_the_real_manifest_matches_the_real_set_when_present(self):
        if not (ROOT / "datasets/canary/human_thriving/set.jsonl").exists():
            pytest.skip("set not restored on this box (it is gitignored; restore from the lab)")
        p, man = oc.verify_set("human_thriving")
        assert man["n"] == 100


def test_the_deepseek_scorer_refuses_BEFORE_its_first_call(dirs, tmp_path, monkeypatch):
    """The refusal has to land before money is spent, not after the first row."""
    import hashlib
    sys.path.insert(0, str(ROOT / "scripts"))
    import score_deepseek_production as sdp
    prompt = ROOT / "filters/human_thriving/v8/prompt-candidate.md"
    _baseline(dirs[0], hashlib.sha256(prompt.read_text(encoding="utf-8").encode()).hexdigest())
    calls = []
    monkeypatch.setattr(sdp, "call_deepseek", lambda *a, **k: calls.append(1) or {"error": "x"})
    monkeypatch.setattr(sdp, "get_deepseek_key", lambda *a, **k: "sk-test")
    inp = tmp_path / "in.jsonl"
    inp.write_text(json.dumps({"id": "r", "title": "t", "content": "word " * 100}) + "\n")
    monkeypatch.setattr(sys, "argv", ["x", "--input", str(inp), "--output", str(tmp_path / "o.jsonl"),
                                      "--config", str(ROOT / "filters/uplifting/v7/config.yaml"),
                                      "--prompt", str(prompt), "--concurrency", "1"])
    with pytest.raises(oc.CanaryRefused):
        sdp.main()
    assert calls == []
    assert not (tmp_path / "o.jsonl").exists()


def test_batch_scorer_refuses_before_its_client_exists(dirs, tmp_path, monkeypatch):
    """Mutation 2026-10-16: replacing batch_scorer's gate call with a constant survived every other test."""
    import hashlib
    from ground_truth import batch_scorer as bs
    prompt = tmp_path / "p.md"
    prompt.write_text("  Score this. [Paste the summary of the article here]  \n")
    raw = prompt.read_text()
    _baseline(dirs[0], hashlib.sha256(raw.encode()).hexdigest(),          # as canary.py baseline writes it
              stripped=hashlib.sha256(raw.strip().encode()).hexdigest())  # batch_scorer hashes this one
    built = []
    monkeypatch.setattr(bs.GenericBatchScorer, "_init_llm_client", lambda self, k: built.append(1))
    with pytest.raises(oc.CanaryRefused):
        bs.GenericBatchScorer(prompt_path=str(prompt), llm_provider="gemini-flash", api_key="k",
                              output_dir=str(tmp_path / "o"), filter_name="f")
    assert built == []
    s = bs.GenericBatchScorer(prompt_path=str(prompt), llm_provider="gemini-flash", api_key="k",
                              output_dir=str(tmp_path / "o"), filter_name="f", skip_canary="test")
    assert s.canary_stamp == {"skipped": "test"} and built == [1]


def test_canary_run_resumes_a_parse_error_instead_of_refusing_forever(dirs, monkeypatch, capsys):
    """2026-10-16: 16 malformed-JSON rows in 1,500 calls. Without a resume, one bad reply leaves the set incomplete,
    `evaluate` raises, and every labelling run of the filter is refused. The first pass here errors one row."""
    import hashlib
    import subprocess
    sys.path.insert(0, str(ROOT / "scripts" / "oracle"))
    import canary as cli
    cfg, data = dirs
    (data / "f").mkdir(parents=True)
    body = '{"id": "a"}\n{"id": "b"}\n'
    (data / "f" / "set.jsonl").write_text(body)
    (cfg / "f.json").write_text(json.dumps({"set_sha256": hashlib.sha256(body.encode()).hexdigest()}))
    dims = ["human_wellbeing_impact", "social_cohesion_impact", "justice_rights_impact", "evidence_level",
            "benefit_distribution", "change_durability"]
    (cfg / "f.baseline.json").write_text(json.dumps({
        "filter": "f", "prompt_sha256": SHA, "k_ship": 1, "items": {"a": 6.0, "b": 1.0}, "op": 4.5,
        "oracle": ORACLE, "served_model": "m",
        "config": str(ROOT / "filters/human_thriving/v9/config.yaml"), "prompt": "p.md",
        "noise": {"k1": {"F": 0, "S": 0.0}, "k3": {"F": 0, "S": 0.0}}}))

    def row(i, score):
        return {"id": i, "human_thriving_analysis": dict({d: {"score": score} for d in dims},
                                                         prompt_sha256=SHA, served_model="m")}
    calls = []

    def fake_run(argv, **kw):
        out = Path(argv[argv.index("--output") + 1])
        rows = [row("a", 6.0), {"id": "b", "error": "Parse failed"}] if not calls else [row("b", 1.0)]
        with open(out, "a") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows)
        calls.append(1)
        return subprocess.CompletedProcess(argv, 1 if len(calls) == 1 else 0)
    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["canary.py", "run", "--filter", "f"])
    with pytest.raises(SystemExit) as ex:
        cli.main()
    assert ex.value.code == 0 and len(calls) == 2
    assert "CANARY PASS" in capsys.readouterr().out
    assert oc.latest_record("f", SHA)["verdict"] == "PASS"


def _run_cli(dirs, monkeypatch, rows_per_call, served="m", oracle=ORACLE, stripped=None):
    """Drive `canary.py run` with the scorer stubbed: rows_per_call[i] is what the i-th scorer call appends."""
    import hashlib
    import subprocess
    sys.path.insert(0, str(ROOT / "scripts" / "oracle"))
    import canary as cli
    cfg, data = dirs
    (data / "f").mkdir(parents=True, exist_ok=True)
    body = '{"id": "a"}\n{"id": "b"}\n'
    (data / "f" / "set.jsonl").write_text(body)
    (cfg / "f.json").write_text(json.dumps({"set_sha256": hashlib.sha256(body.encode()).hexdigest()}))
    (cfg / "f.baseline.json").write_text(json.dumps({
        "filter": "f", "prompt_sha256": SHA, "prompt_sha256_stripped": stripped, "k_ship": 1,
        "items": {"a": 6.0, "b": 1.0}, "op": 4.5, "oracle": oracle, "served_model": served, "config": "filters/human_thriving/v9/config.yaml", "prompt": "p.md",
        "noise": {"k1": {"F": 0, "S": 0.0}, "k3": {"F": 0, "S": 0.0}}}))
    calls = []

    def fake_run(argv, **kw):
        if "--output-dir" in argv:      # batch_scorer: <dir>/<filter>/scored_batch_001.jsonl, appended per pass
            d = Path(argv[argv.index("--output-dir") + 1]) / "human_thriving"
            d.mkdir(parents=True, exist_ok=True)
            out = d / "scored_batch_001.jsonl"
        else:
            out = Path(argv[argv.index("--output") + 1])
        rows = rows_per_call[min(len(calls), len(rows_per_call) - 1)]
        with open(out, "a") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows)
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0)
    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["canary.py", "run", "--filter", "f"])
    with pytest.raises(SystemExit) as ex:
        cli.main()
    return ex.value.code, calls


DIMS = ["human_wellbeing_impact", "social_cohesion_impact", "justice_rights_impact", "evidence_level",
        "benefit_distribution", "change_durability"]


def _row(i, score, served="m", sha=SHA):
    return {"id": i, "human_thriving_analysis": dict({d: {"score": score} for d in DIMS},
                                                     prompt_sha256=sha, served_model=served)}


def test_a_canary_served_by_ANOTHER_model_FAILS_even_with_zero_flips(dirs, monkeypatch):
    code, _ = _run_cli(dirs, monkeypatch, [[_row("a", 6.0, "deepseek-v4-pro"), _row("b", 1.0, "deepseek-v4-pro")]],
                       served="deepseek-flash")
    rec = oc.latest_record("f", SHA)
    assert code == 1 and rec["verdict"] == "FAIL" and "served" in rec["reason"]


def test_an_unfinishable_canary_records_NO_VERDICT_so_an_older_PASS_cannot_stand(dirs, monkeypatch):
    oc.write_record("f", SHA, {"verdict": "PASS", "flips": 0, "shift": 0.0}, set(), now=time.time() - 60)
    code, calls = _run_cli(dirs, monkeypatch, [[_row("a", 6.0), {"id": "b", "error": "Parse failed"}]])
    assert "NO-VERDICT" in str(code) and len(calls) == 4      # MAX_PASSES tries, then gives up
    assert oc.latest_record("f", SHA)["verdict"] == "NO-VERDICT"


def test_the_canary_requests_the_baselines_own_model_and_endpoint(dirs, monkeypatch):
    _, calls = _run_cli(dirs, monkeypatch, [[_row("a", 6.0), _row("b", 1.0)]])
    argv = calls[0]
    assert argv[argv.index("--model") + 1] == "deepseek-chat"
    assert argv[argv.index("--base-url") + 1] == "https://api.deepseek.com/v1/chat/completions"


STRIPPED = "cd" * 32


def test_a_batch_scorer_canary_drives_batch_scorer_and_accepts_its_STRIPPED_digest(dirs, monkeypatch):
    """Gemini filters label through ground_truth.batch_scorer, which hashes the stripped template. A canary that
    re-ran the DeepSeek scorer would measure a different oracle; one that demanded the raw digest would never PASS."""
    code, calls = _run_cli(dirs, monkeypatch, [[_row("a", 6.0, sha=STRIPPED), _row("b", 1.0, sha=STRIPPED)]],
                           oracle="batch_scorer|gemini-flash", stripped=STRIPPED)
    argv = calls[0]
    assert code == 0 and argv[1:3] == ["-m", "ground_truth.batch_scorer"]
    assert argv[argv.index("--llm") + 1] == "gemini-flash" and "--skip-canary" in argv
    assert oc.latest_record("f", SHA)["verdict"] == "PASS"


def test_a_batch_scorer_canary_resumes_and_reads_every_pass(dirs, monkeypatch):
    """batch_scorer appends per pass; the canary must see the first pass's rows AND the resumed one."""
    code, calls = _run_cli(dirs, monkeypatch, [[_row("a", 6.0, sha=STRIPPED)], [_row("b", 1.0, sha=STRIPPED)]],
                           oracle="batch_scorer|gemini-flash", stripped=STRIPPED)
    assert code == 0 and len(calls) == 2


def test_a_digest_that_is_neither_raw_nor_stripped_is_NO_VERDICT(dirs, monkeypatch):
    code, _ = _run_cli(dirs, monkeypatch, [[_row("a", 6.0, sha="ef" * 32), _row("b", 1.0, sha="ef" * 32)]],
                       oracle="batch_scorer|gemini-flash", stripped=STRIPPED)
    assert "NO-VERDICT" in str(code) and oc.latest_record("f", SHA)["verdict"] == "NO-VERDICT"


class TestBaselineOp:
    def _cli(self):
        sys.path.insert(0, str(ROOT / "scripts" / "oracle"))
        import canary as cli
        return cli

    def test_the_op_point_must_match_the_packages_normalization(self):
        cli = self._cli()
        cfg = ROOT / "filters/nature_recovery/v4/config.yaml"
        assert cli.checked_op(cfg, 3.75) == 3.75
        with pytest.raises(SystemExit, match="raw_min"):
            cli.checked_op(cfg, 4.5)          # the old hard-coded value, wrong for this filter

    def test_cd_v5s_raw_min_is_within_tolerance_of_its_tier_threshold(self):
        assert self._cli().checked_op(ROOT / "filters/cultural_discovery/v5/config.yaml", 4.0) == 4.0

    def test_a_package_without_normalization_RAISES(self, tmp_path):
        (tmp_path / "config.yaml").write_text("filter: {name: x}\n")
        with pytest.raises(SystemExit, match="missing"):
            self._cli().checked_op(tmp_path / "config.yaml", 4.5)

    def test_a_baseline_without_op_cannot_be_evaluated(self, dirs, tmp_path):
        """No silent default: a baseline missing `op` must raise, not compare at 4.5."""
        (dirs[0] / "f.baseline.json").write_text(json.dumps({
            "config": "filters/human_thriving/v9/config.yaml", "items": {"a": 1.0},
            "noise": {"k1": {"F": 0, "S": 0.0}}}))
        run = tmp_path / "r.jsonl"; run.write_text(json.dumps(_row("a", 1.0)) + "\n")
        with pytest.raises(KeyError):
            self._cli().evaluate("f", [run])


# ---- review 2026-10-19 ------------------------------------------------------------------------------------------

def test_a_junk_skip_row_is_not_done_so_the_older_PASS_cannot_stand(dirs, monkeypatch):
    """A scrape-junk row ({"skipped": ...}) has no "error" key; counted as done, `evaluate` then raised
    "incomplete" WITHOUT a record, and the older unused PASS kept admitting labelling runs."""
    oc.write_record("f", SHA, {"verdict": "PASS", "flips": 0, "shift": 0.0}, set(), now=time.time() - 60)
    code, calls = _run_cli(dirs, monkeypatch, [[_row("a", 6.0), {"id": "b", "skipped": "junk"}]])
    assert "NO-VERDICT" in str(code) and len(calls) == 4
    assert oc.latest_record("f", SHA)["verdict"] == "NO-VERDICT"
    with pytest.raises(oc.CanaryRefused):
        oc.gate(SHA, oracle=ORACLE)


def test_a_canary_that_CRASHES_records_NO_VERDICT(dirs, monkeypatch):
    sys.path.insert(0, str(ROOT / "scripts" / "oracle"))
    import canary as cli

    def boom(*a, **k):
        raise KeyError("op")
    monkeypatch.setattr(cli, "evaluate", boom)
    oc.write_record("f", SHA, {"verdict": "PASS", "flips": 0, "shift": 0.0}, set(), now=time.time() - 60)
    code, _ = _run_cli(dirs, monkeypatch, [[_row("a", 6.0), _row("b", 1.0)]])
    assert "NO-VERDICT" in str(code) and "KeyError" in str(code)
    assert oc.latest_record("f", SHA)["verdict"] == "NO-VERDICT"


def test_a_thinking_budget_is_ANOTHER_oracle_for_batch_scorer(dirs, tmp_path, monkeypatch):
    """A PASS for gemini-flash at the default budget 0 must not admit a run with --thinking-budget 8192."""
    import hashlib
    from ground_truth import batch_scorer as bs
    prompt = tmp_path / "p.md"
    prompt.write_text("Score this. [Paste the summary of the article here]\n")
    raw = prompt.read_text()
    sha = hashlib.sha256(raw.encode()).hexdigest()
    _baseline(dirs[0], sha, stripped=hashlib.sha256(raw.strip().encode()).hexdigest(), oracle="batch_scorer|gemini-flash")
    monkeypatch.setattr(bs.GenericBatchScorer, "_init_llm_client", lambda self, k: None)
    kw = dict(prompt_path=str(prompt), llm_provider="gemini-flash", api_key="k", output_dir=str(tmp_path / "o"),
              filter_name="f")
    oc.write_record("f", sha, {"verdict": "PASS", "flips": 0, "shift": 0.0}, set(), now=time.time() - 60)
    with pytest.raises(oc.CanaryRefused, match="no canary covers it"):
        bs.GenericBatchScorer(thinking_budget=8192, **kw)
    assert bs.GenericBatchScorer(**kw).canary_stamp["verdict"] == "PASS"     # positive control: budget 0 admitted


BASELINES = sorted(Path(ROOT / "config/canary").glob("*.baseline.json"))


@pytest.mark.parametrize("path", BASELINES, ids=[p.name.split(".")[0] for p in BASELINES])
def test_each_committed_baseline_matches_its_package(path):
    """`checked_op` runs only when a baseline is written; this catches an op-point, prompt or endpoint moving after."""
    import hashlib
    sys.path.insert(0, str(ROOT / "scripts"))
    import score_deepseek_production as sdp
    sys.path.insert(0, str(ROOT / "scripts" / "oracle"))
    import canary as cli
    b = json.loads(path.read_text())
    raw_min = json.loads((ROOT / b["config"]).with_name("normalization.json").read_text())["stats"]["raw_min"]
    assert abs(b["op"] - raw_min) <= cli.OP_TOLERANCE
    assert hashlib.sha256((ROOT / b["prompt"]).read_bytes()).hexdigest() == b["prompt_sha256"]
    endpoint, _ = b["oracle"].rsplit("|", 1)
    assert endpoint in (cli.BATCH_SCORER, sdp.DEEPSEEK_URL)
    if endpoint == cli.BATCH_SCORER:
        # batch_scorer's gate looks the baseline up by ITS digest of the loaded template; a miss is `no-set`, unguarded
        from ground_truth import batch_scorer as bs
        s = object.__new__(bs.GenericBatchScorer)
        s.prompt_path = ROOT / b["prompt"]
        assert bs.prompt_sha256(s._load_prompt_template()) == b["prompt_sha256_stripped"]


def test_the_baseline_census_is_not_empty():
    assert len(BASELINES) >= 5
