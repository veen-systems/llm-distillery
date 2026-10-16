"""tests/conftest.py turns bytecode writing off for the whole suite (see the comment there, 2026-10-16)."""
import importlib
import sys


def test_the_suite_writes_no_bytecode(tmp_path, monkeypatch):
    assert sys.dont_write_bytecode is True
    (tmp_path / "fresh_mod_for_pyc_check.py").write_text("X = 1\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.import_module("fresh_mod_for_pyc_check")
    assert not (tmp_path / "__pycache__").exists()
