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


def _baseline(cfg, sha=SHA):
    (cfg / "f.baseline.json").write_text(json.dumps({"filter": "f", "prompt_sha256": sha}))


def _record(verdict, age_h, now):
    rec = oc.write_record("f", SHA, {"verdict": verdict, "flips": 9, "shift": -0.9}, set(),
                          now=now - age_h * 3600)
    return rec


class TestGate:
    def test_no_set_stamps_and_never_refuses(self, dirs):
        assert oc.gate(SHA) == {"verdict": "no-set"}

    def test_skip_is_stamped_with_its_reason(self, dirs):
        _baseline(dirs[0])
        assert oc.gate(SHA, "vendor outage") == {"skipped": "vendor outage"}

    def test_a_guarded_prompt_with_no_record_is_REFUSED(self, dirs):
        _baseline(dirs[0])
        with pytest.raises(oc.CanaryRefused, match="no canary run on record"):
            oc.gate(SHA)

    def test_a_FAILED_latest_record_is_REFUSED_even_when_fresh(self, dirs):
        _baseline(dirs[0]); now = time.time()
        _record("PASS", 3, now)
        _record("FAIL", 1, now)                   # the latest wins
        with pytest.raises(oc.CanaryRefused, match="FAILED"):
            oc.gate(SHA, now=now)

    def test_a_stale_PASS_is_REFUSED(self, dirs):
        _baseline(dirs[0]); now = time.time()
        _record("PASS", oc.FRESH_HOURS + 0.5, now)
        with pytest.raises(oc.CanaryRefused, match="h old"):
            oc.gate(SHA, now=now)

    def test_a_fresh_PASS_lets_the_run_through_and_names_its_record(self, dirs):
        _baseline(dirs[0]); now = time.time()
        rec = _record("PASS", 1, now)
        st = oc.gate(SHA, now=now)
        assert st["verdict"] == "PASS" and st["record"] == rec["record"]

    def test_a_record_for_ANOTHER_prompt_does_not_count(self, dirs):
        _baseline(dirs[0]); now = time.time()
        oc.write_record("f", "cd" * 32, {"verdict": "PASS", "flips": 0, "shift": 0.0}, set(), now=now)
        with pytest.raises(oc.CanaryRefused):
            oc.gate(SHA, now=now)


class TestComparison:
    def test_flips_count_verdict_changes_at_the_op_point_only(self):
        base = {"a": 4.6, "b": 4.4, "c": 1.0}
        assert oc.compare({"a": 4.4, "b": 4.6, "c": 3.0}, base)["flips"] == 2

    def test_shift_is_the_mean_signed_delta(self):
        assert oc.compare({"a": 2.0, "b": 2.0}, {"a": 3.0, "b": 3.0})["shift"] == -1.0

    def test_verdict_uses_the_preregistered_margins(self):
        bar = {"F": 3, "S": 0.10}
        assert oc.verdict({"flips": 4, "shift": 0.0}, bar) == "PASS"      # 3 + 1
        assert oc.verdict({"flips": 5, "shift": 0.0}, bar) == "FAIL"
        assert oc.verdict({"flips": 0, "shift": -0.26}, bar) == "FAIL"    # 0.10 + 0.15
        assert oc.verdict({"flips": 0, "shift": -0.24}, bar) == "PASS"

    def test_noise_k3_takes_each_split_of_six_once(self):
        runs = [{"a": float(i), "b": 4.5} for i in range(6)]
        assert len(oc.noise(runs)["k3"]["each"]) == 10

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
    _baseline(dirs[0], hashlib.sha256(prompt.read_text().strip().encode()).hexdigest())  # batch_scorer strips
    built = []
    monkeypatch.setattr(bs.GenericBatchScorer, "_init_llm_client", lambda self, k: built.append(1))
    with pytest.raises(oc.CanaryRefused):
        bs.GenericBatchScorer(prompt_path=str(prompt), llm_provider="gemini-flash", api_key="k",
                              output_dir=str(tmp_path / "o"), filter_name="f")
    assert built == []
    s = bs.GenericBatchScorer(prompt_path=str(prompt), llm_provider="gemini-flash", api_key="k",
                              output_dir=str(tmp_path / "o"), filter_name="f", skip_canary="test")
    assert s.canary_stamp == {"skipped": "test"} and built == [1]
