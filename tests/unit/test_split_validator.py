"""#179: the shared split validator -- each rule refuses, legacy rows pass as "unknown", and all four readers run it."""
import ast
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

from training import split_validator as sv

REPO = Path(__file__).resolve().parents[2]
DIMS = ["a", "b"]
NEW = "2026-10-21T09:00:00Z"
OLD = "2026-09-01T09:00:00Z"


def _row(i="r1", labels=(1.0, 2.0), names=DIMS, **meta):
    r = {"id": i, "labels": list(labels), "dimension_names": list(names)}
    if meta:
        r["oracle_meta"] = meta
    return r


class TestRefuses:
    @pytest.mark.parametrize("bad", [-0.1, 10.01, math.nan, math.inf, None, "5", True])
    def test_a_score_that_is_not_finite_in_0_10(self, bad):
        with pytest.raises(sv.SplitInvalid, match="finite score"):
            sv.validate_rows([_row(labels=(1.0, bad))], DIMS)

    def test_the_bounds_themselves_pass(self):
        sv.validate_rows([_row(labels=(0, 10))], DIMS)

    def test_a_duplicate_id_within_a_file(self):
        with pytest.raises(sv.SplitInvalid, match="duplicate id"):
            sv.validate_rows([_row("x"), _row("x")], DIMS)

    def test_a_duplicate_id_ACROSS_splits(self, tmp_path):
        for part in ("train", "test"):
            (tmp_path / f"{part}.jsonl").write_text(json.dumps(_row("x")) + "\n")
        with pytest.raises(sv.SplitInvalid, match="duplicate id 'x'"):
            sv.validate_split_dir(tmp_path, DIMS)

    @pytest.mark.parametrize("rid", [None, ""])
    def test_a_row_with_no_id(self, rid):
        with pytest.raises(sv.SplitInvalid, match="no usable id"):
            sv.validate_rows([_row(rid)], DIMS)

    def test_dimensions_in_ANOTHER_ORDER_than_the_filter(self):
        with pytest.raises(sv.SplitInvalid, match="dimension_names"):
            sv.validate_rows([_row(names=["b", "a"])], DIMS)

    def test_rows_that_disagree_with_each_other_with_no_config(self):
        with pytest.raises(sv.SplitInvalid, match="dimension_names"):
            sv.validate_rows([_row("1"), _row("2", names=["b", "a"])])

    def test_a_label_count_that_differs_from_the_dimensions(self):
        with pytest.raises(sv.SplitInvalid, match="1 labels for 2"):
            sv.validate_rows([_row(labels=(1.0,))], DIMS)

    @pytest.mark.parametrize("row", [["not", "a", "row"], {"id": [1], "labels": [1, 2], "dimension_names": DIMS},
                                     {"id": True, "labels": [1, 2], "dimension_names": DIMS},
                                     {"id": "x", "labels": [10 ** 400, 1], "dimension_names": DIMS},
                                     {"id": "x", "labels": [1, 2], "dimension_names": "ab"}])
    def test_MALFORMED_input_raises_SplitInvalid_not_a_crash(self, row):
        with pytest.raises(sv.SplitInvalid):
            sv.validate_rows([row], DIMS)

    def test_an_empty_file(self):
        with pytest.raises(sv.SplitInvalid, match="no rows"):
            sv.validate_rows([], DIMS)


class TestProvenance:
    def test_a_LEGACY_row_with_nothing_passes_as_explicit_unknown(self):
        r = sv.validate_rows([_row()], DIMS)
        assert r["provenance_unknown"] == 1 and sv.provenance_of(_row()) == "unknown"

    def test_a_legacy_row_with_stamps_is_known(self):
        row = _row(prompt_hash="003cd35a5122", analyzed_at=OLD)
        assert sv.validate_rows([row], DIMS)["provenance_known"] == 1
        assert sv.provenance_of(row) == {"prompt_hash": "003cd35a5122", "analyzed_at": OLD}

    def test_a_legacy_row_missing_served_model_still_passes(self):
        sv.validate_rows([_row(prompt_hash="abc", analyzed_at=OLD)], DIMS)

    @pytest.mark.parametrize("missing,match", [("served_model", "no served_model"), ("prompt_sha256", "no prompt digest")])
    def test_a_NEW_row_missing_provenance_is_refused(self, missing, match):
        meta = {"served_model": "deepseek-flash", "prompt_sha256": "ab" * 32, "analyzed_at": NEW}
        del meta[missing]
        with pytest.raises(sv.SplitInvalid, match=match):
            sv.validate_rows([_row(**meta)], DIMS)

    def test_a_NEW_row_whose_served_model_is_the_ABSENT_marker_is_refused(self):
        with pytest.raises(sv.SplitInvalid, match="no served_model"):
            sv.validate_rows([_row(served_model="__absent__", prompt_sha256="ab" * 32, analyzed_at=NEW)], DIMS)

    @pytest.mark.parametrize("when", ["2026-10-21 09:00:00", "2026-10-21", "2026-10-19T23:00:00-05:00",
                                      1792573200, "1792573200", "1792573200.0"])
    def test_a_NEW_date_in_ANY_format_is_new(self, when):
        # each sorted BELOW the cutoff as a string (review 10-19); -05:00 at 23:00 is 04:00Z on the 20th
        with pytest.raises(sv.SplitInvalid, match="no served_model"):
            sv.validate_rows([_row(prompt_sha256="ab" * 32, analyzed_at=when)], DIMS)

    @pytest.mark.parametrize("when", ["2026-10-19 23:59:59", "2026-10-19", "2026-10-20T01:00:00+02:00", 1760000000])
    def test_an_OLD_date_in_any_format_stays_legacy(self, when):
        sv.validate_rows([_row(prompt_hash="abc", analyzed_at=when)], DIMS)

    def test_an_UNPARSEABLE_date_raises(self):
        with pytest.raises(sv.SplitInvalid, match="is not a date"):
            sv.validate_rows([_row(analyzed_at="last tuesday")], DIMS)

    @pytest.mark.parametrize("blank", [" ", "unknown"])
    def test_a_NEW_row_with_a_BLANK_or_unknown_stamp_is_refused(self, blank):
        with pytest.raises(sv.SplitInvalid, match="no served_model"):
            sv.validate_rows([_row(served_model=blank, prompt_sha256="ab" * 32, analyzed_at=NEW)], DIMS)
        with pytest.raises(sv.SplitInvalid, match="no prompt digest"):
            sv.validate_rows([_row(served_model="m", prompt_sha256=blank, analyzed_at=NEW)], DIMS)

    def test_a_complete_NEW_row_passes(self):
        sv.validate_rows([_row(served_model="deepseek-flash", prompt_sha256="ab" * 32, analyzed_at=NEW)], DIMS)

    def test_a_provenance_dict_with_no_oracle_stamp_is_NOT_trusted(self):
        row = _row(served_model="qwen3:14b", prompt_hash="abc")
        row["provenance"] = {"source": "someone else's field"}
        assert sv.provenance_of(row)["served_model"] == "qwen3:14b"
        assert sv.provenance_of({"provenance": {"x": 1}}) == "unknown"

    def test_record_root_stamps_are_read_score_ollama_oracle_style(self):
        row = _row()
        row.update(prompt_sha256="cd" * 32, served_model="qwen3:14b")
        assert sv.provenance_of(row)["served_model"] == "qwen3:14b"


# --- the four readers run it ------------------------------------------------------------------------------------

def _prepare(tmp_path, rows):
    labels = tmp_path / "labels.jsonl"
    labels.write_text("".join(json.dumps(r) + "\n" for r in rows))
    out = tmp_path / "out"
    r = subprocess.run([sys.executable, str(REPO / "training" / "prepare_data.py"), "--filter",
                        str(REPO / "filters" / "belonging" / "v3"), "--input", str(labels), "--output-dir", str(out)],
                       capture_output=True, text=True, cwd=REPO, timeout=120,
                       env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"})
    return r, out


BELONGING = ["intergenerational_bonds", "community_fabric", "reciprocal_care", "rootedness",
             "purpose_beyond_self", "slow_presence"]


def _scored(i, score=5.0, **meta):
    return {"id": f"a{i}", "title": "t", "content": "c",
            "belonging_analysis": {**{d: score for d in BELONGING}, **meta}}


def test_prepare_data_refuses_an_out_of_range_label_and_writes_nothing(tmp_path):
    r, out = _prepare(tmp_path, [_scored(i) for i in range(29)] + [_scored(29, score=11.0)])
    assert r.returncode == 1 and "is not a finite score in [0, 10]" in r.stderr, r.stderr[-400:]
    assert not (out / "train.jsonl").exists()


def test_prepare_data_writes_per_row_provenance_known_or_explicitly_unknown(tmp_path):
    rows = [_scored(i) for i in range(15)] + [
        _scored(i, served_model="deepseek-flash", prompt_sha256="ab" * 32, analyzed_at=NEW) for i in range(15, 30)]
    r, out = _prepare(tmp_path, rows)
    assert r.returncode == 0, r.stderr[-400:]
    prov = [json.loads(l)["provenance"] for p in ("train", "val", "test") for l in open(out / f"{p}.jsonl")]
    assert prov.count("unknown") == 15
    assert sum(isinstance(p, dict) and p["served_model"] == "deepseek-flash" for p in prov) == 15
    sv.validate_split_dir(out, BELONGING)        # what it wrote, its own readers accept


def test_prepare_data_refuses_a_NEW_label_without_a_served_model(tmp_path):
    rows = [_scored(i) for i in range(29)] + [_scored(29, prompt_sha256="ab" * 32, analyzed_at=NEW)]
    r, _ = _prepare(tmp_path, rows)
    assert r.returncode == 1 and "no served_model" in r.stderr


def test_the_gate_refuses_a_duplicate_id_it_used_to_overwrite(tmp_path):
    sys.path.insert(0, str(REPO / "scripts" / "gate"))
    import ground_truth_gate as g
    p = tmp_path / "test.jsonl"
    rows = [_row("x", labels=[1.0] * len(g.DIMS), names=g.DIMS), _row("x", labels=[9.0] * len(g.DIMS), names=g.DIMS)]
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    with pytest.raises(sv.SplitInvalid, match="duplicate id"):
        g.load_labels(p)
    p.write_text(json.dumps(rows[0]) + "\n")
    assert list(g.load_labels(p)) == ["x"]              # the control
    p.write_text(json.dumps(_row("x", labels=[1.0] * len(g.DIMS), names=[d + "_x" for d in g.DIMS])) + "\n")
    with pytest.raises(ValueError, match="not this filter's"):
        g.load_labels(p)


def _calls_before(path, func, first_name, before_name):
    """In `func`'s body, the first call to `first_name` comes before the first call to `before_name`."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == func)
    lines = {}
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            name = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            lines.setdefault(name, n.lineno)
            lines[name] = min(lines[name], n.lineno)
    assert first_name in lines, f"{path.name}:{func} never calls {first_name}"
    assert lines[first_name] < lines[before_name]


def test_train_validates_every_split_before_building_a_dataset():
    _calls_before(REPO / "training" / "train.py", "main", "validate_split_dir", "FilterDataset")


def test_train_probe_validates_before_embedding():
    _calls_before(REPO / "scripts" / "train_probe.py", "main", "validate_split_dir", "generate_embeddings")


def test_fit_calibration_validates_before_loading_the_scorer_and_no_longer_adopts_the_files_order():
    p = REPO / "scripts" / "calibration" / "fit_calibration.py"
    _calls_before(p, "main", "validate_file", "load_scorer")
    assert "Using data dimension order" not in p.read_text(encoding="utf-8")
