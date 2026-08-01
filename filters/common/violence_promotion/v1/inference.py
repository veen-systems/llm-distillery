"""
Violence Promotion Filter v1 - Embedding + MLP Classifier

Uses frozen sentence-transformers embeddings with a trained MLP classifier.
Mirrors commerce_prefilter v2 architecture: frozen embedder → StandardScaler
→ MLPClassifier → predict_proba.

Violence is definitionally not constructive. This filter answers: "does this
article promote, normalize, or present as desirable any form of mass violence?"

Usage:
    from filters.common.violence_promotion.v1.inference import ViolencePromotionFilterV1

    detector = ViolencePromotionFilterV1(threshold=0.95)
    result = detector.is_violence_promotion(article)
    # {"is_violence_promotion": True, "score": 0.97, "version": "v1"}
"""

import pickle
import time
from pathlib import Path
from typing import Optional, Union

from sentence_transformers import SentenceTransformer


class ViolencePromotionFilterV1:
    """
    Violence promotion detection using frozen embeddings + MLP classifier.

    Architecture:
        Article text → [Frozen Embedder] → 768-dim vector → [MLP] → score (0–1)

    Attributes:
        threshold: Score above which article is classified as violence promotion
        embedder: SentenceTransformer model for generating embeddings
        classifier: Trained MLP classifier
        scaler: StandardScaler for normalizing embeddings
    """

    # Model identity, stamped as `_violence_model` on every scored article
    # (NM#281 / ADR-022). Authoritative source for the stamp — NexusMind reads
    # it off this class rather than hardcoding, so a future v2 cannot leave
    # production rows claiming v1. Mirrors ObituaryPreprocessor.MODEL_VERSION.
    MODEL_ID = "violence_promotion_v1"
    MODEL_VERSION = "v1"

    def __init__(
        self,
        threshold: float = 0.95,
        model_dir: Optional[Path] = None,
        device: str = "cpu",
    ):
        """
        Initialize the violence promotion filter.

        Args:
            threshold: Classification threshold (default 0.95 for high precision)
            model_dir: Path to directory containing classifier and scaler
            device: Device for embedder ('cpu' or 'cuda')
        """
        self.threshold = threshold
        self.device = device

        # Set model directory
        if model_dir is None:
            model_dir = Path(__file__).parent / "models"
        self.model_dir = Path(model_dir)

        # Load models lazily
        self._embedder = None
        self._classifier = None
        self._scaler = None
        self._loaded = False

    def _load_models(self):
        """Load embedder, classifier, and scaler."""
        if self._loaded:
            return

        # Load embedder
        self._embedder = SentenceTransformer(
            "paraphrase-multilingual-mpnet-base-v2",
            device=self.device,
        )

        # Load classifier (with optional integrity check)
        from filters.common.embedding_stage import _verify_pickle_integrity

        classifier_path = self.model_dir / "mlp_classifier.pkl"
        _verify_pickle_integrity(classifier_path)
        with open(classifier_path, "rb") as f:
            self._classifier = pickle.load(f)

        # Load scaler (with optional integrity check)
        scaler_path = self.model_dir / "scaler.pkl"
        _verify_pickle_integrity(scaler_path)
        with open(scaler_path, "rb") as f:
            self._scaler = pickle.load(f)

        self._loaded = True

    def _prepare_text(self, article: Union[dict, str]) -> str:
        """
        Prepare text from article for embedding.

        Args:
            article: Article dict with 'title' and 'content', or raw text string

        Returns:
            Combined text for embedding
        """
        if isinstance(article, str):
            return article.strip()

        if not isinstance(article, dict):
            raise TypeError(
                f"Expected dict or str for article, got {type(article).__name__}. "
                f"Article dict should have 'title' and 'content' keys."
            )

        # Coerce None values to empty strings (avoids "None" token in embedding)
        title = article.get("title") or ""
        content = article.get("content") or ""

        # Coerce non-string values to strings
        title = str(title) if not isinstance(title, str) else title
        content = str(content) if not isinstance(content, str) else content

        # Combine title and content
        # Note: Embedder has 128-token limit, so title + first ~100 words is used
        return f"{title} {content}".strip()

    def is_violence_promotion(self, article: Union[dict, str]) -> dict:
        """
        Check if an article promotes or normalises violence.

        Args:
            article: Article dict with 'title' and 'content', or raw text

        Returns:
            Dict with:
                - is_violence_promotion: bool
                - score: float (0–1)
                - inference_time_ms: float
                - version: str
        """
        self._load_models()

        start_time = time.perf_counter()

        # Prepare text
        text = self._prepare_text(article)

        # Generate embedding
        embedding = self._embedder.encode([text], show_progress_bar=False)

        # Scale
        embedding_scaled = self._scaler.transform(embedding)

        # Predict
        score = self._classifier.predict_proba(embedding_scaled)[0, 1]

        inference_time_ms = (time.perf_counter() - start_time) * 1000

        return {
            "is_violence_promotion": bool(score >= self.threshold),
            "score": float(score),
            "inference_time_ms": inference_time_ms,
            "version": "v1",
        }

    def batch_predict(self, articles: list, batch_size: int = 32) -> list:
        """
        Predict violence promotion scores for multiple articles.

        Args:
            articles: List of article dicts or text strings
            batch_size: Batch size for embedding generation

        Returns:
            List of result dicts (same format as is_violence_promotion)
        """
        if not articles:
            return []

        self._load_models()

        start_time = time.perf_counter()

        # Prepare texts
        texts = [self._prepare_text(a) for a in articles]

        # Generate embeddings in batch
        embeddings = self._embedder.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
        )

        # Scale
        embeddings_scaled = self._scaler.transform(embeddings)

        # Predict
        scores = self._classifier.predict_proba(embeddings_scaled)[:, 1]

        total_time_ms = (time.perf_counter() - start_time) * 1000
        avg_time_ms = total_time_ms / len(articles)

        results = []
        for score in scores:
            results.append(
                {
                    "is_violence_promotion": bool(score >= self.threshold),
                    "score": float(score),
                    "inference_time_ms": avg_time_ms,
                    "version": "v1",
                }
            )

        return results

    def get_score(self, article: Union[dict, str]) -> float:
        """
        Get raw violence promotion score without threshold application.

        Args:
            article: Article dict or text string

        Returns:
            Violence promotion probability (0–1)
        """
        result = self.is_violence_promotion(article)
        return result["score"]


# Convenience function for quick checks
def is_violence_promotion(
    article: Union[dict, str], threshold: float = 0.95
) -> bool:
    """
    Quick check if article is violence promotion content.

    Note: Creates new detector instance each call. For batch processing,
    use ViolencePromotionFilterV1 class directly.
    """
    detector = ViolencePromotionFilterV1(threshold=threshold)
    return detector.is_violence_promotion(article)["is_violence_promotion"]
