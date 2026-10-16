"""#176 step 3 (owner 2026-10-16: WARN, do not restructure): prepare_data reports cross-split near-duplicates."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "training"))
import prepare_data as pd  # noqa: E402


VOCAB = ["alpha", "beta", "gamma", "a"]


def fake_encode(rows):
    """Unit vectors keyed on the title: same title -> cosine 1.0, different titles -> orthogonal.
    A fixed vocabulary, not hash(): str hashing is salted per process, so hash() % n collides at random."""
    out = np.zeros((len(rows), len(VOCAB)))
    for i, r in enumerate(rows):
        out[i, VOCAB.index(r["title"])] = 1.0
    return out


def rows(*titles, prefix):
    return [{"id": f"{prefix}{i}", "title": t, "content": "x"} for i, t in enumerate(titles)]


def test_a_planted_cross_split_twin_is_counted_and_named(tmp_path):
    train = rows("alpha", "beta", prefix="tr")
    test = rows("alpha", "gamma", prefix="te")          # te0 is a twin of tr0 under another id
    out = pd.report_cross_split_near_dups(train, [], test, tmp_path, encode=fake_encode)
    assert out["test"] == {"n": 2, "near_dups": 1, "ids": ["te0"]}
    assert json.loads((tmp_path / "near_dup_report.json").read_text())["test"]["near_dups"] == 1


def test_no_twin_reads_zero_measured_not_absent(tmp_path):
    out = pd.report_cross_split_near_dups(rows("alpha", prefix="tr"), rows("beta", prefix="va"),
                                          rows("gamma", prefix="te"), tmp_path, encode=fake_encode)
    assert out["status"] == "measured" and out["test"]["near_dups"] == 0 and out["val"]["near_dups"] == 0


def test_without_the_model_it_says_NOT_RUN_never_a_silent_zero(tmp_path, monkeypatch, capsys):
    import builtins
    real = builtins.__import__
    monkeypatch.setattr(builtins, "__import__", lambda n, *a, **k: (_ for _ in ()).throw(ImportError())
                        if n == "sentence_transformers" else real(n, *a, **k))
    assert pd.report_cross_split_near_dups(rows("a", prefix="t"), [], rows("a", prefix="x"), tmp_path) is None
    assert json.loads((tmp_path / "near_dup_report.json").read_text())["status"] == "not_run"
    assert "NOT RUN" in capsys.readouterr().out
