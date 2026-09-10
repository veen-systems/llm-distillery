"""Harm detector v1 — is the article's dominant subject a HARM? (llm-distillery#156)

⛔ **STAMP ONLY. THIS CLASS HAS NO THRESHOLD AND MUST NOT GROW ONE.** It returns a score in
[0,1] and nothing else. ADR-022: *stamp always, decide once — exactly one config-gated drop
point per concern, and every enforcement decision is a config flip.* Whether a lens acts on
the stamp is that lens's config, read where the lens decides, never here.

⛔ **A cross-lens BLOCKER would be wrong, not merely premature.** The same article is harmful
under one lens's promise and constitutive of another's: *"Community kitchens, boat ambulances:
Bihar copes with floods"* betrays Thriving's *"lives getting better"* and is arguably exactly
right under Solutions; Nature Recovery is **about** recovering from damage. Measured: of the 9
articles both judges called harmful, **6 were already surfaced by another lens**.

Architecture (matching `obituary v5`, `violence_promotion v1`, `commerce v2`):

    text -> [frozen paraphrase-multilingual-mpnet-base-v2] -> 768-d -> [scaler] -> 5x MLP -> mean

⭐ **The five heads are not an accuracy trick — they are the fix for `H-DET2`.** With everything
else held fixed, `early_stopping=True` lets `random_state` choose the internal validation split,
and this detector's catch count on the held-out panel spanned **0-3** across five seeds. Shipping
one seed ships a lottery ticket; the mean of five removes the choice. Cost is negligible because
the embedding pass — the expensive part — is shared.

⚠️ **Scores are NOT comparable across library stacks.** The measured **stack** noise floor of
**0.2008** was taken on exactly this architecture (mpnet + sklearn MLP, differing
sentence-transformers versions). Compare scores only within one environment.

Numbers, the shuffled-label null arm, and two refuted predictions: `EXP-037`,
`docs/evidence/2026-09-10-harm-detector/`. ⚠️ Its panel is `uplifting v7` / `human_thriving v8`
display-eligible rows only — it says **nothing** about solutions, belonging, nature_recovery or
cultural_discovery.

Usage:
    from filters.common.harm_detector.v1.inference import HarmDetectorV1

    detector = HarmDetectorV1()
    detector.score(article)              # -> 0.0-1.0
    detector.batch_score(articles)       # -> [float, ...]
"""

import json
import pickle
from pathlib import Path
from typing import Optional, Union

MODEL_VERSION = "v1"
EMBEDDER = "paraphrase-multilingual-mpnet-base-v2"


class HarmDetectorV1:
    """Frozen-embedding + 5-head MLP ensemble. Returns a score; decides nothing."""

    def __init__(self, model_dir: Optional[Path] = None, device: str = "cpu"):
        self.device = device
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).parent / "models"
        self.version = MODEL_VERSION
        self._embedder = None
        self._scaler = None
        self._classifiers = None
        self._config = None

    # ---- lazy loading -----------------------------------------------------
    def _load(self):
        if self._classifiers is not None:
            return
        from sentence_transformers import SentenceTransformer

        cfg_path = self.model_dir / "training_config.json"
        if not cfg_path.exists():
            raise FileNotFoundError(
                f"{cfg_path} missing — the ensemble's seed list lives there and guessing it "
                f"would silently ship a different model than the one that was measured"
            )
        self._config = json.loads(cfg_path.read_text(encoding="utf-8"))

        with (self.model_dir / "scaler.pkl").open("rb") as f:
            self._scaler = pickle.load(f)

        clfs = []
        for seed in self._config["ensemble_seeds"]:
            p = self.model_dir / f"mlp_classifier_seed{seed}.pkl"
            if not p.exists():
                raise FileNotFoundError(
                    f"{p} missing — training_config.json declares seed {seed}. A partial "
                    f"ensemble is a DIFFERENT model, not a degraded one; refusing to average "
                    f"whatever happens to be on disk."
                )
            with p.open("rb") as f:
                clfs.append(pickle.load(f))
        self._classifiers = clfs
        self._embedder = SentenceTransformer(EMBEDDER, device=self.device)

    # ---- text -------------------------------------------------------------
    @staticmethod
    def _text(article: Union[dict, str]) -> str:
        """Title + content, exactly as the trainer built it. Any drift here is a silent
        distribution shift — the model never sees the field names, only this string."""
        if isinstance(article, str):
            return article.strip()
        return f"{article.get('title') or ''} {article.get('content') or ''}".strip()

    # ---- scoring ----------------------------------------------------------
    def batch_score(self, articles: list, batch_size: int = 32) -> list:
        if not articles:
            return []
        self._load()
        texts = [self._text(a) for a in articles]
        emb = self._embedder.encode(texts, batch_size=batch_size, show_progress_bar=False)
        z = self._scaler.transform(emb)
        stacked = [c.predict_proba(z)[:, 1] for c in self._classifiers]
        return [float(sum(col) / len(col)) for col in zip(*stacked)]

    def score(self, article: Union[dict, str]) -> float:
        return self.batch_score([article])[0]

    def stamp(self, article: Union[dict, str]) -> dict:
        """The row-shaped stamp. No verdict key, deliberately — see the module docstring."""
        return {
            "harm_is_subject_score": round(self.score(article), 6),
            "harm_detector_version": self.version,
        }
