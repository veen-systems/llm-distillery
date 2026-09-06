"""
Unit tests for scripts/gate/ground_truth_gate.py pure functions.

Backs the corrected deploy-gate methodology (judge each model against held-out
oracle ground truth, not against the prior generous model). Covers the
confusion-matrix metrics, the gatekeepered label WA, and spearman.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
_spec = importlib.util.spec_from_file_location(
    "ground_truth_gate", ROOT / "scripts" / "gate" / "ground_truth_gate.py")
gt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gt)


def test_label_wa_weights_sum_to_one():
    assert abs(sum(gt.WEIGHTS.values()) - 1.0) < 1e-9


def test_label_wa_gatekeeper_caps_low_evidence():
    # recovery_evidence=0, everything else 10 -> capped at 3.5
    assert gt.label_wa([0, 10, 10, 10, 10, 10]) == pytest.approx(3.5)


def test_label_wa_no_cap_when_evidence_present():
    assert gt.label_wa([3, 10, 10, 10, 10, 10]) > 3.5


def test_evaluate_perfect_prediction():
    truth = {"a": 6.0, "b": 5.0, "c": 1.0, "d": 0.5}
    pred = dict(truth)
    m = gt.evaluate(truth, pred)
    assert m["recall"] == 1.0 and m["precision"] == 1.0
    assert m["specificity"] == 1.0 and m["f1"] == 1.0


def test_evaluate_confusion_counts():
    truth = {"a": 6.0, "b": 5.0, "c": 1.0, "d": 4.5}   # 3 positives (a,b,d), 1 neg (c)
    pred = {"a": 6.0, "b": 2.0, "c": 5.0, "d": 4.5}    # a TP, b FN, c FP, d TP
    m = gt.evaluate(truth, pred)
    assert (m["tp"], m["fn"], m["fp"], m["tn"]) == (2, 1, 1, 0)
    assert m["recall"] == pytest.approx(2 / 3)
    assert m["precision"] == pytest.approx(2 / 3)


def test_evaluate_only_scores_common_ids():
    truth = {"a": 6.0, "b": 5.0}
    pred = {"a": 6.0}  # b missing from predictions
    m = gt.evaluate(truth, pred)
    assert m["n"] == 1


def test_evaluate_threshold_boundary_is_inclusive():
    # exactly 4.0 counts as surfaced/positive (>=)
    truth = {"a": 4.0}
    pred = {"a": 4.0}
    m = gt.evaluate(truth, pred)
    assert m["tp"] == 1 and m["fn"] == 0


def test_noise_floor_is_the_measured_value_not_rounded_up():
    # #95 measured max |delta| 0.1617; the stated floor is 0.16. An earlier draft
    # of the memory file rounded to 0.17 — that was wrong and must not come back.
    assert gt.NOISE_FLOOR == 0.16


def test_indeterminate_counts_articles_within_the_floor_of_the_threshold():
    # d is 0.05 below the op-point, e is 0.10 above it -> both indeterminate.
    # a and c sit well clear -> neither is.
    truth = {"a": 6.0, "c": 1.0, "d": 5.0, "e": 1.0}
    pred = {"a": 6.0, "c": 1.0, "d": 3.95, "e": 4.10}
    m = gt.evaluate(truth, pred)
    assert m["n_indeterminate"] == 2


def test_band_brackets_the_point_estimate():
    truth = {"a": 6.0, "b": 5.0, "c": 1.0, "d": 0.5}
    pred = {"a": 6.0, "b": 4.05, "c": 3.95, "d": 0.5}
    m = gt.evaluate(truth, pred)
    # specificity included deliberately: ADR-023 makes it THE objective, it is
    # what the DISJOINT/OVERLAP verdict is computed from, and it was the one band
    # shipped without a test (found by review battery, 2026-08-10).
    for key in ("recall", "precision", "specificity", "f1"):
        lo, hi = m[f"{key}_band"]
        assert lo <= m[key] <= hi


def test_specificity_band_stays_in_unit_interval_and_denominator_is_invariant():
    """tn+fp cannot move under the flips the band models -- both cells are truth-negatives."""
    truth = {"a": 6.0, "b": 5.0, "c": 1.0, "d": 0.5, "e": 1.0}
    pred = {"a": 6.0, "b": 4.05, "c": 3.95, "d": 0.5, "e": 4.02}
    m = gt.evaluate(truth, pred)
    lo, hi = m["specificity_band"]
    assert 0.0 <= lo <= m["specificity"] <= hi <= 1.0
    cells = m["indeterminate_by_cell"]
    assert sum(cells.values()) == m["n_indeterminate"]
    assert cells["fp"] + cells["tn"] <= m["fp"] + m["tn"]


def test_truth_threshold_pins_the_positive_set_while_the_bar_sweeps():
    """Without pinning, sweeping `medium` changes WHICH articles count as on-lens,
    so recall at one threshold is not comparable to recall at another (#102)."""
    truth = {"a": 6.0, "b": 4.2, "c": 4.6, "d": 1.0}
    pred = {"a": 6.0, "b": 4.2, "c": 4.6, "d": 1.0}
    pinned = [gt.evaluate(truth, pred, medium=t, truth_threshold=4.0) for t in (4.0, 4.5, 5.0)]
    assert {m["positives"] for m in pinned} == {3}, "pinned truth must hold the positive set fixed"
    assert [m["tp"] for m in pinned] == [3, 2, 1], "only the prediction side may move"

    unpinned = [gt.evaluate(truth, pred, medium=t) for t in (4.0, 4.5, 5.0)]
    assert [m["positives"] for m in unpinned] == [3, 2, 1], "unpinned, the positive set moves too"


def test_default_truth_threshold_is_tied_to_medium():
    """Back-compat: omitting truth_threshold must reproduce every pre-2026-08-10 run."""
    truth = {"a": 6.0, "b": 4.2, "c": 1.0}
    pred = {"a": 5.9, "b": 3.0, "c": 4.4}
    assert gt.evaluate(truth, pred, medium=4.5) == gt.evaluate(truth, pred, medium=4.5,
                                                               truth_threshold=4.5)


def test_band_collapses_to_the_point_estimate_when_nothing_is_borderline():
    truth = {"a": 6.0, "b": 5.0, "c": 1.0, "d": 0.5}
    pred = dict(truth)
    m = gt.evaluate(truth, pred)
    assert m["n_indeterminate"] == 0
    assert m["recall_band"] == [m["recall"], m["recall"]]
    assert m["f1_band"] == [m["f1"], m["f1"]]


def test_borderline_true_positive_can_fall_out_of_recall():
    # one positive, predicted 0.05 above the threshold: recall reads 1.0, but the
    # band must admit 0.0 because the batch alone decided it.
    truth = {"a": 5.0}
    pred = {"a": 4.05}
    m = gt.evaluate(truth, pred)
    assert m["recall"] == 1.0
    assert m["recall_band"] == [0.0, 1.0]


def test_noise_floor_zero_reproduces_the_pre_2026_08_06_behaviour():
    truth = {"a": 5.0, "b": 1.0}
    pred = {"a": 4.05, "b": 3.95}
    m = gt.evaluate(truth, pred, noise_floor=0.0)
    assert m["n_indeterminate"] == 0
    assert m["recall_band"] == [m["recall"], m["recall"]]


def test_spearman_monotonic():
    assert gt.spearman([1, 2, 3, 4], [2, 4, 6, 8]) == pytest.approx(1.0)
    assert gt.spearman([1, 2, 3, 4], [8, 6, 4, 2]) == pytest.approx(-1.0)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))


# --- the report writer: attribution, and not deleting what it cannot regenerate ---
#
# These invoke main() as a subprocess rather than calling the pure functions, because the
# thing under test IS the file the gate leaves behind. A report that cannot be attributed
# to a device is what made every v8 accuracy number carry #104's caveat, and a rewrite
# that silently drops a hand-written `provenance` block destroys the one fact a sha256
# cannot recover.

import json
import subprocess


def _tiny_gate_inputs(tmp_path):
    """One positive and one negative, scored perfectly. The numbers are not the point."""
    labels = tmp_path / "labels.jsonl"
    labels.write_text(
        json.dumps({"id": "a", "labels": [10, 10, 10, 10, 10, 10]}) + "\n"
        + json.dumps({"id": "b", "labels": [0, 0, 0, 0, 0, 0]}) + "\n")
    scores = tmp_path / "scores.jsonl"
    scores.write_text(
        json.dumps({"id": "a", "weighted_average": 9.0}) + "\n"
        + json.dumps({"id": "b", "weighted_average": 0.5}) + "\n")
    return labels, scores


def _run_gate(tmp_path, labels, scores, report):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "gate" / "ground_truth_gate.py"),
         "--labels", str(labels), "--model", f"m={scores}", "--report", str(report)],
        cwd=ROOT, capture_output=True, text=True)


def test_report_records_the_sha256_of_every_input_it_read(tmp_path):
    import hashlib
    labels, scores = _tiny_gate_inputs(tmp_path)
    report = tmp_path / "gate.json"
    proc = _run_gate(tmp_path, labels, scores, report)
    assert proc.returncode == 0, proc.stderr

    got = json.loads(report.read_text())["inputs"]
    assert got["labels"]["sha256"] == hashlib.sha256(labels.read_bytes()).hexdigest()
    assert got["models"]["m"]["sha256"] == hashlib.sha256(scores.read_bytes()).hexdigest()
    assert got["models"]["m"]["path"] == str(scores)


def test_the_recorded_sha256_actually_tracks_the_file(tmp_path):
    """A presence control: a hash that never changes is a constant, not a hash."""
    labels, scores = _tiny_gate_inputs(tmp_path)
    report = tmp_path / "gate.json"
    _run_gate(tmp_path, labels, scores, report)
    first = json.loads(report.read_text())["inputs"]["models"]["m"]["sha256"]

    scores.write_text(scores.read_text().replace("9.0", "8.0"))
    _run_gate(tmp_path, labels, scores, report)
    second = json.loads(report.read_text())["inputs"]["models"]["m"]["sha256"]
    assert first != second


def test_rerunning_the_gate_keeps_a_hand_written_provenance_block(tmp_path):
    """The block says which box, venv and DEVICE produced the dump -- nothing else in
    the report can say that, and nothing regenerates it."""
    labels, scores = _tiny_gate_inputs(tmp_path)
    report = tmp_path / "gate.json"
    _run_gate(tmp_path, labels, scores, report)

    written = json.loads(report.read_text())
    written["provenance"] = {"box": "b650", "device": "cuda"}
    report.write_text(json.dumps(written, indent=2))

    _run_gate(tmp_path, labels, scores, report)
    after = json.loads(report.read_text())
    assert after["provenance"] == {"box": "b650", "device": "cuda"}
    assert after["inputs"]["labels"]["path"] == str(labels)   # and it still rewrote the rest


def test_a_corrupt_prior_report_does_not_stop_the_gate_writing(tmp_path):
    labels, scores = _tiny_gate_inputs(tmp_path)
    report = tmp_path / "gate.json"
    report.write_text("{not json")
    proc = _run_gate(tmp_path, labels, scores, report)
    assert proc.returncode == 0, proc.stderr
    assert "provenance" not in json.loads(report.read_text())


# --- ADR-023: the priority travels with the number ---
#
# A recall figure met cold is read as a grade. In this repo a low one is usually the
# decision working (specificity at the op-point is the criterion), and the reader most
# likely to misread it is a future session of this project. So the gate states the
# priority itself rather than depending on whoever writes the summary around it.

def test_the_table_states_the_priority_above_the_numbers(tmp_path):
    labels, scores = _tiny_gate_inputs(tmp_path)
    proc = _run_gate(tmp_path, labels, scores, tmp_path / "gate.json")
    assert proc.returncode == 0, proc.stderr

    out = proc.stdout
    assert "HIGH CERTAINTY over HIGH DETECTION" in out
    # Above the numbers, not in a trailer nobody scrolls to.
    assert out.index("HIGH CERTAINTY") < out.index("recall"), \
        "the priority must precede the metric table, or it is a footnote"


def test_the_report_artifact_carries_the_priority_too(tmp_path):
    """The JSON outlives the terminal, and it is what gets read months later."""
    labels, scores = _tiny_gate_inputs(tmp_path)
    report = tmp_path / "gate.json"
    _run_gate(tmp_path, labels, scores, report)
    assert "HIGH CERTAINTY over HIGH DETECTION" in json.loads(report.read_text())["priority"]


# --- the hole a review found in the four tests above ---
#
# None of them varied the SCORES between the two gate invocations, so none could tell
# "carried the provenance key" from "carried the whole prior report". Mutating
# `report["provenance"] = prior["provenance"]` into `report.update(prior)` — which reverts
# every freshly computed metric to the previous file's — passed all four. The failure that
# escapes is the worst one this file can have: a retrained model's gate report keeping the
# old model's recall.

def test_a_rerun_with_new_scores_reports_the_NEW_numbers(tmp_path):
    labels, scores = _tiny_gate_inputs(tmp_path)
    report = tmp_path / "gate.json"
    _run_gate(tmp_path, labels, scores, report)
    first = json.loads(report.read_text())
    assert first["models"]["m"]["recall"] == 1.0, "fixture should start perfect"

    # Give the report a hand-written provenance block, which is what arms the carry-over.
    first["provenance"] = {"box": "b650", "device": "cuda"}
    report.write_text(json.dumps(first, indent=2))

    # Now the model gets worse: the positive drops below the bar.
    scores.write_text(
        json.dumps({"id": "a", "weighted_average": 0.5}) + "\n"
        + json.dumps({"id": "b", "weighted_average": 0.5}) + "\n")
    _run_gate(tmp_path, labels, scores, report)

    after = json.loads(report.read_text())
    assert after["models"]["m"]["recall"] == 0.0, \
        "the rerun must report the NEW model's numbers, not carry the prior report over"
    assert after["provenance"] == {"box": "b650", "device": "cuda"}, \
        "and it must still keep the hand-written block"


def test_provenance_is_marked_stale_when_the_inputs_it_described_changed(tmp_path):
    """Kept, never deleted — but it must not read as describing this run."""
    labels, scores = _tiny_gate_inputs(tmp_path)
    report = tmp_path / "gate.json"
    _run_gate(tmp_path, labels, scores, report)
    d = json.loads(report.read_text())
    d["provenance"] = {"box": "b650", "device": "cuda"}
    report.write_text(json.dumps(d, indent=2))
    _run_gate(tmp_path, labels, scores, report)   # stamps it with these inputs

    scores.write_text(scores.read_text().replace("9.0", "8.0"))   # a different dump
    proc = _run_gate(tmp_path, labels, scores, report)

    after = json.loads(report.read_text())
    assert after["provenance"] == {"box": "b650", "device": "cuda"}, "never deleted"
    assert "STALE" in after.get("provenance_status", ""), \
        "prose written against other inputs must be marked, or it reads as current"
    assert "WARNING" in proc.stdout


def test_unchanged_inputs_do_not_cry_stale(tmp_path):
    """A warning that fires on every rerun is noise, and noise is ignored within a day."""
    labels, scores = _tiny_gate_inputs(tmp_path)
    report = tmp_path / "gate.json"
    _run_gate(tmp_path, labels, scores, report)
    d = json.loads(report.read_text())
    d["provenance"] = {"box": "b650"}
    report.write_text(json.dumps(d, indent=2))
    _run_gate(tmp_path, labels, scores, report)          # arms provenance_applies_to
    proc = _run_gate(tmp_path, labels, scores, report)   # identical inputs again

    after = json.loads(report.read_text())
    assert "provenance_status" not in after
    assert "STALE" not in proc.stdout
    assert "UNVERIFIED" not in proc.stdout


def test_a_hand_written_block_with_no_fingerprint_is_UNVERIFIED_not_stale(tmp_path):
    """The distinction is the whole point: 'nobody recorded what this described' is not
    'this describes something else'. Conflating them makes the warning noise."""
    labels, scores = _tiny_gate_inputs(tmp_path)
    report = tmp_path / "gate.json"
    _run_gate(tmp_path, labels, scores, report)
    d = json.loads(report.read_text())
    d["provenance"] = {"box": "b650"}
    d.pop("provenance_applies_to", None)
    report.write_text(json.dumps(d, indent=2))

    proc = _run_gate(tmp_path, labels, scores, report)
    after = json.loads(report.read_text())
    assert "UNVERIFIED" in after["provenance_status"]
    assert "STALE" not in after["provenance_status"]
    assert after["provenance_applies_to"], "and it is stamped, so the next run converges"


def test_a_config_that_does_not_exist_is_refused_not_defaulted(tmp_path):
    """load_scoring_spec swallows every exception and falls back to nature_recovery v4's
    constants, so a typo'd path printed a full table at someone else's operating point
    and exited 0."""
    labels, scores = _tiny_gate_inputs(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "gate" / "ground_truth_gate.py"),
         "--labels", str(labels), "--model", f"m={scores}",
         "--config", str(tmp_path / "no_such_config.yaml"),
         "--report", str(tmp_path / "gate.json")],
        cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode != 0
    assert "does not exist" in (proc.stdout + proc.stderr)
    assert not (tmp_path / "gate.json").exists(), "and it must not write a report"
