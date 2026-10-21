"""#178: the generated half of a DATASHEET.md. It must describe the split the model was trained on, at the
runtime op-point, and say NOT RECORDED / UNKNOWN rather than print a reassuring zero."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
import datasheet_facts as df  # noqa: E402

DIMS = ["a", "b"]
CONFIG = """scoring:
  dimensions:
    a: {weight: 0.5}
    b: {weight: 0.5}
"""


def _pkg(tmp_path, train_rows=3, meta_train=3, raw_min=4.5):
    f = tmp_path / "filters" / "x" / "v1"
    f.mkdir(parents=True)
    (f / "config.yaml").write_text(CONFIG)
    (f / "normalization.json").write_text(json.dumps({"stats": {} if raw_min is None else {"raw_min": raw_min}}))
    (f / "training_metadata.json").write_text(json.dumps({"train_examples": meta_train, "val_examples": 1,
                                                           "git_commit": "c" * 40}))
    s = tmp_path / "split"
    s.mkdir()
    row = lambda i, v: {"id": f"src_name_{i:012x}", "title": "t", "content": "x" * 400,
                        "url": f"https://www.example.org/{i}", "labels": [v, v], "dimension_names": DIMS}
    (s / "train.jsonl").write_text("".join(json.dumps(row(i, 6.0 if i == 0 else 1.0)) + "\n"
                                           for i in range(train_rows)))
    (s / "val.jsonl").write_text(json.dumps(row(99, 5.0)) + "\n")
    return f, s


def _spec_ok(monkeypatch):
    monkeypatch.setattr(df.gate, "load_scoring_spec",
                        lambda p: {"dims": DIMS, "weights": {"a": 0.5, "b": 0.5}, "gk_dim": None, "gk_min": 0, "gk_cap": 10})


def test_positives_are_counted_at_the_normalization_op_point(tmp_path, monkeypatch):
    _spec_ok(monkeypatch)
    f, s = _pkg(tmp_path)
    out = df.facts(f, s)
    assert out["op"] == 4.5
    assert out["parts"]["train"] == {"rows": 3, "positive": 1, "provenance_known": 0, "provenance_unknown": 3}
    assert out["parts"]["val"]["positive"] == 1


def test_a_split_that_is_not_the_models_RAISES(tmp_path, monkeypatch):
    _spec_ok(monkeypatch)
    f, s = _pkg(tmp_path, train_rows=3, meta_train=4)
    with pytest.raises(ValueError, match="not this model's split"):
        df.facts(f, s)


def test_no_runtime_op_point_RAISES(tmp_path, monkeypatch):
    _spec_ok(monkeypatch)
    f, s = _pkg(tmp_path, raw_min=None)
    with pytest.raises(ValueError, match="raw_min"):
        df.facts(f, s)


def test_unrecorded_fields_are_SAID_and_a_GN_zero_is_not_evidence(tmp_path, monkeypatch):
    _spec_ok(monkeypatch)
    f, s = _pkg(tmp_path)
    text = df.render(df.facts(f, s))
    assert "NOT RECORDED in the split" in text and "Google News share: UNKNOWN" in text


def test_write_replaces_only_the_generated_block(tmp_path, monkeypatch):
    _spec_ok(monkeypatch)
    f, s = _pkg(tmp_path)
    sheet = tmp_path / "DATASHEET.md"
    sheet.write_text(f"# hand\n\nkeep me\n\n{df.BEGIN}\nold\n{df.END}\n\nand me\n")
    monkeypatch.setattr(sys, "argv", ["x", "--filter", str(f), "--split", str(s), "--write", str(sheet)])
    df.main()
    t = sheet.read_text()
    assert "keep me" in t and "and me" in t and "old" not in t and "| train | 3 |" in t


def test_metadata_WITHOUT_the_count_keys_RAISES(tmp_path, monkeypatch):
    _spec_ok(monkeypatch)
    f, s = _pkg(tmp_path)
    (f / "training_metadata.json").write_text("{}")
    with pytest.raises(ValueError, match="cannot tie the split"):
        df.facts(f, s)
