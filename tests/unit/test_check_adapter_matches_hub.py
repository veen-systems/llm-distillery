"""check_adapter_matches_hub.py: every exit code, with the Hub stubbed (no network)."""
import hashlib
import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "check_adapter_matches_hub", REPO / "scripts" / "deployment" / "check_adapter_matches_hub.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

REPO_ID = ["--repo-id", "jeergrvgreg/x-filter-v1"]
WEIGHTS = b"weights" * 150_000  # 1.05 MB: above the stub floor, as every real adapter is


@pytest.fixture
def adapter(tmp_path):
    p = tmp_path / "adapter_model.safetensors"
    p.write_bytes(WEIGHTS)
    return p


def run(monkeypatch, adapter, hub, extra=REPO_ID):
    def fake(repo_id, token):
        if isinstance(hub, Exception):
            raise hub
        return hub
    monkeypatch.setattr(mod, "hub_sha256", fake)
    monkeypatch.setattr(mod, "token_from_secrets", lambda: None)
    return mod.main(["x", "v1", "--local", str(adapter), *extra])


def test_match(monkeypatch, adapter):
    assert run(monkeypatch, adapter, hashlib.sha256(WEIGHTS).hexdigest()) == 0


def test_mismatch(monkeypatch, adapter):
    assert run(monkeypatch, adapter, hashlib.sha256(b"other").hexdigest()) == 1


def test_missing_adapter(monkeypatch, tmp_path):
    assert run(monkeypatch, tmp_path / "absent.safetensors", "0" * 64) == 1


def test_hub_unreachable_is_not_a_match(monkeypatch, adapter):
    assert run(monkeypatch, adapter, OSError("no route")) == 2


def test_hub_without_sha_cannot_verify(monkeypatch, adapter):
    assert run(monkeypatch, adapter, None) == 2


def test_package_without_repo_id_is_exit_2_and_never_asks(monkeypatch, adapter):
    """No repo id in the package and no NO_HUB: stage.py would stage it UNCHECKED."""
    assert run(monkeypatch, adapter, pytest.fail, extra=[]) == 2


@pytest.mark.parametrize("pkg,expected", [
    ("human_thriving/v9", "jeergrvgreg/human-thriving-filter-v9"),
    ("cultural_discovery/v5", "jeergrvgreg/cultural-discovery-filter-v5"),
    ("nature_recovery/v4", "jeergrvgreg/nature-recovery-filter-v4"),
    ("belonging/v3", "jeergrvgreg/belonging-filter-v3"),
])
def test_repo_id_comes_from_the_package_not_the_directory_name(pkg, expected):
    """Review 2026-10-09: deriving `<dir>-filter-<v>` 404'd for the three underscored
    live filters. These are the packages' own inference_hub.py values."""
    assert mod.hub_repo_id(REPO / "filters" / pkg) == expected


def _no_hub_pkg(tmp_path, adapter_bytes):
    root = tmp_path / "filters" / "u" / "v7"
    (root / "model").mkdir(parents=True)
    (root / "NO_HUB").write_text("")
    if adapter_bytes is not None:
        (root / "model" / "adapter_model.safetensors").write_bytes(adapter_bytes)
    return root


def test_no_hub_package_exits_0_without_asking(monkeypatch, tmp_path):
    _no_hub_pkg(tmp_path, WEIGHTS)
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setattr(mod, "hub_sha256", lambda r, t: pytest.fail("Hub must not be asked"))
    assert mod.main(["u", "v7"]) == 0


def test_no_hub_package_WITHOUT_an_adapter_is_exit_1(monkeypatch, tmp_path):
    """Review round 2, 2026-10-09: NO_HUB returned 0 before the missing-adapter check, yet
    a NO_HUB version's local file is the only copy staging can serve (stage.py errors)."""
    _no_hub_pkg(tmp_path, None)
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setattr(mod, "hub_sha256", lambda r, t: pytest.fail("Hub must not be asked"))
    assert mod.main(["u", "v7"]) == 1


@pytest.mark.parametrize("content", [
    b"version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 52254448\n",
    b"",
])
def test_stub_adapter_is_exit_1_and_never_asks(monkeypatch, tmp_path, content, capsys):
    """Review round 2, 2026-10-09: hashing a git-LFS pointer reported MISMATCH, whose
    remedy (re-upload) would replace the real Hub copy."""
    stub = tmp_path / "adapter_model.safetensors"
    stub.write_bytes(content)
    assert run(monkeypatch, stub, pytest.fail) == 1
    out = capsys.readouterr().out
    assert "STUB" in out and "never re-upload" in out and "MISMATCH" not in out


def test_missing_package_dir_says_so(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    assert mod.main(["nope", "v1"]) == 2
    assert "NO PACKAGE" in capsys.readouterr().out


def test_stub_floor_matches_guard_E():
    from scripts.deployment import preflight_deploy_guards as g
    assert mod.MIN_ADAPTER_BYTES == g._MIN_ADAPTER_BYTES


def test_env_token_wins_over_secrets(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "from-env")
    assert mod.token_from_secrets() == "from-env"
