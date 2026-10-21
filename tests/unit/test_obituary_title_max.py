"""#159 (owner ruling 2026-10-21): ObituaryDetectorV5(title_max=True) scores max(title, full). OFF by default, and
with it off the output must be exactly what v5 returned before. Stubbed models: no embedder download."""
import sys
import types

import numpy as np
import pytest

# The embedder is stubbed below, so the module only needs to import: situla's venv has no sentence_transformers.
sys.modules.setdefault("sentence_transformers", types.SimpleNamespace(SentenceTransformer=None))
from filters.common.obituary_detector.v5.inference import ObituaryDetectorV5  # noqa: E402


class _Emb:
    def encode(self, texts, batch_size=32, show_progress_bar=False):
        return np.array([[float(len(t))] for t in texts])


class _Scaler:
    def transform(self, x):
        return x


class _Clf:
    # "score" = a fixed table by text, so title and full can disagree on purpose
    TABLE = {}

    def predict_proba(self, x):
        p = np.array([_Clf.TABLE.get(int(v[0]), 0.1) for v in x])
        return np.stack([1 - p, p], axis=1)


def _det(**kw):
    d = ObituaryDetectorV5(threshold=0.85, **kw)
    d._embedder, d._scaler, d._classifier, d._loaded = _Emb(), _Scaler(), _Clf(), True
    return d


ART = {"title": "Dame X obituary", "content": "long body text " * 3}     # full len 61, title len 15


@pytest.fixture(autouse=True)
def table():
    full = len(f"{ART['title']} {ART['content']}".strip())
    _Clf.TABLE = {full: 0.65, len(ART["title"]): 0.9997}
    yield


def test_OFF_by_default_returns_the_full_text_score_and_the_old_keys_only():
    r = _det().is_obituary(ART)
    assert r == {"is_obituary": False, "score": 0.65, "inference_time_ms": r["inference_time_ms"], "version": "v5"}


def test_ON_takes_the_title_when_it_is_higher_and_stamps_both_parts():
    r = _det(title_max=True).is_obituary(ART)
    assert r["score"] == pytest.approx(0.9997) and r["is_obituary"] is True
    assert r["score_full"] == pytest.approx(0.65) and r["score_title"] == pytest.approx(0.9997)
    assert r["rule"] == "max_title_full"


def test_ON_an_EMPTY_title_has_no_title_score():
    a = {"title": "   ", "content": "long body text " * 3}
    r = _det(title_max=True).is_obituary(a)
    assert r["score_title"] is None and r["score"] == r["score_full"]


def test_batch_and_single_agree_with_title_max():
    d = _det(title_max=True)
    arts = [ART, {"title": None, "content": "x"}, "raw text only"]
    b = d.batch_predict(arts)
    for a, r in zip(arts, b):
        s = d.is_obituary(a)
        assert (r["score"], r["score_title"]) == (s["score"], s["score_title"])
    assert b[1]["score_title"] is None and b[2]["score_title"] is None
