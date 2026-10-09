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


@pytest.fixture
def adapter(tmp_path):
    p = tmp_path / "adapter_model.safetensors"
    p.write_bytes(b"weights")
    return p


def run(monkeypatch, adapter, hub):
    def fake(repo_id, token):
        if isinstance(hub, Exception):
            raise hub
        return hub
    monkeypatch.setattr(mod, "hub_sha256", fake)
    monkeypatch.setattr(mod, "token_from_secrets", lambda: None)
    return mod.main(["x", "v1", "--local", str(adapter)])


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


def test_default_paths_name_the_package(monkeypatch):
    seen = {}
    monkeypatch.setattr(mod, "hub_sha256", lambda r, t: seen.setdefault("repo", r))
    monkeypatch.setattr(mod, "token_from_secrets", lambda: None)
    assert mod.main(["nosuchfilter", "v9"]) == 1          # adapter missing in this checkout
    assert "repo" not in seen                             # and the Hub is not asked first
