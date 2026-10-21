"""#146: the embedding cache must not hand a model on one device to a consumer that asked for another.
NexusMind's story_dedup.py reads `_embedding_models[model_name]` directly, so the FIRST load keeps the bare key."""
import sys
import types

import pytest

from filters.common.embedding_stage import EmbeddingStage

LOADS = []


class _FakeST:
    def __init__(self, name, device=None):
        import torch
        self.name, self.device = name, torch.device(device)
        LOADS.append((name, device))


@pytest.fixture(autouse=True)
def stub(monkeypatch):
    monkeypatch.setitem(sys.modules, "sentence_transformers", types.SimpleNamespace(SentenceTransformer=_FakeST))
    monkeypatch.setattr(EmbeddingStage, "_embedding_models", {})
    LOADS.clear()


def _stage(device, name="m"):
    st = object.__new__(EmbeddingStage)            # skip __init__: it loads a probe from disk
    st.embedding_model_name, st.device, st._embedder = name, device, None
    st._ensure_embedder_loaded()
    return st


def test_a_second_consumer_on_ANOTHER_device_gets_its_own_model():
    gpu, cpu = _stage("cuda"), _stage("cpu")
    assert str(gpu._embedder.device).startswith("cuda") and str(cpu._embedder.device) == "cpu"
    assert LOADS == [("m", "cuda"), ("m", "cpu")]


def test_the_same_device_shares_one_model_and_cuda_matches_cuda0():
    a, b, c = _stage("cuda"), _stage("cuda"), _stage("cuda:0")
    assert a._embedder is b._embedder is c._embedder and len(LOADS) == 1


def test_the_FIRST_load_keeps_the_bare_name_key_story_dedup_reads():
    _stage("cpu")
    assert set(EmbeddingStage._embedding_models) == {"m"}
    _stage("cuda")
    assert set(EmbeddingStage._embedding_models) == {"m", "m@cuda"}
    assert str(EmbeddingStage._embedding_models["m"].device) == "cpu"     # story_dedup still sees the first load
