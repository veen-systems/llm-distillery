"""The suite names the wrong-interpreter trap itself (tests/conftest.py, 2026-10-12)."""
import importlib.util
from pathlib import Path

CONFTEST = Path(__file__).resolve().parents[1] / "conftest.py"
spec = importlib.util.spec_from_file_location("ld_root_conftest", CONFTEST)
cf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cf)


def _repo(tmp_path):
    (tmp_path / ".venv" / "bin").mkdir(parents=True)
    return tmp_path


def test_module_errors_outside_the_venv_raise_the_banner(tmp_path):
    repo = _repo(tmp_path)
    lines = cf.wrong_interpreter_hint(["E   ModuleNotFoundError: No module named 'transformers'"] * 3,
                                      "/usr/bin/python3", repo)
    assert lines and "3 failure(s)" in lines[0] and ".venv/bin/python" in lines[0]


def test_the_same_errors_inside_the_venv_are_left_alone(tmp_path):
    """Inside the venv a ModuleNotFoundError is a real missing dependency, not this trap."""
    repo = _repo(tmp_path)
    assert cf.wrong_interpreter_hint(["ModuleNotFoundError: x"],
                                     str(repo / ".venv" / "bin" / "python"), repo) == []


def test_ordinary_failures_say_nothing(tmp_path):
    assert cf.wrong_interpreter_hint(["AssertionError: 1 != 2"], "/usr/bin/python3",
                                     _repo(tmp_path)) == []


def test_a_venv_python_symlinked_outside_the_venv_is_still_inside(tmp_path):
    """uv makes .venv/bin/python a symlink to an interpreter outside the venv; resolving it misfired."""
    repo = _repo(tmp_path)
    real = tmp_path / "elsewhere" / "python3.12"
    real.parent.mkdir()
    real.write_text("")
    exe = repo / ".venv" / "bin" / "python"
    exe.symlink_to(real)
    assert cf.wrong_interpreter_hint(["ModuleNotFoundError: x"], str(exe), repo) == []
    assert cf.wrong_interpreter_hint(["ModuleNotFoundError: x"], str(real), repo,
                                     prefix=str(repo / ".venv")) == []


def test_the_live_interpreter_is_judged_by_its_prefix(tmp_path):
    repo = _repo(tmp_path)
    assert cf.wrong_interpreter_hint(["ModuleNotFoundError: x"], str(repo / ".venv" / "bin" / "python"),
                                     repo, prefix="/usr")
