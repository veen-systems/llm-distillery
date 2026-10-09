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


@pytest.fixture
def adapter(tmp_path):
    p = tmp_path / "adapter_model.safetensors"
    p.write_bytes(b"weights")
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
    assert run(monkeypatch, adapter, hashlib.sha256(b"weights").hexdigest()) == 0


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


def test_no_hub_package_exits_0_without_asking(monkeypatch, tmp_path):
    root = tmp_path / "filters" / "u" / "v7"
    root.mkdir(parents=True)
    (root / "NO_HUB").write_text("")
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setattr(mod, "hub_sha256", lambda r, t: pytest.fail("Hub must not be asked"))
    assert mod.main(["u", "v7"]) == 0


def test_env_token_wins_over_secrets(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "from-env")
    assert mod.token_from_secrets() == "from-env"
