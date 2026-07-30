"""
Obituary Detector v5 - Embedding + MLP Classifier

Uses frozen paraphrase-multilingual-mpnet-base-v2 embeddings with a trained
MLP classifier. Same architecture as commerce_prefilter v2. Detects obituaries
and death-memorial pieces upstream of lens scoring.

v5 corrective retrain (LD#83 FN-delta gate failure): 21 panel-graded hard
positives added — real obituaries v3@0.95 caught but v4@0.90 missed (4-model
panel, 12 unanimous). Balances v4's 12 hard negatives, which all remain
correctly rejected (max 0.44). Heldout (n=1529, 33 panel-graded rows excluded):
v5@0.90 precision 0.983 / recall 0.750 vs v4@0.90 1.000 / 0.744 and
v3@0.95 0.987 / 0.722 — but v4's recall there omits the 21 confirmed misses.
Evidence: validation/artifacts/v5_eval_2026-07-30.json.

Shadow-deployed via NexusMind NM#185: stamps _obituary_score / _is_obituary,
drops nothing. Enforcement is a separate owner-signed-off step.

Usage:
    from filters.common.obituary_detector.v5.inference import ObituaryDetectorV5

    detector = ObituaryDetectorV5(threshold=0.90)
    result = detector.is_obituary(article)
    # {"is_obituary": True, "score": 0.97, "version": "v5"}
"""

import pickle
import time
from pathlib import Path
from typing import Optional, Union

from sentence_transformers import SentenceTransformer


class ObituaryDetectorV5:
    """
    Obituary detection using frozen embeddings + MLP classifier.

    Architecture:
        Article text -> [Frozen Embedder] -> 768-dim vector -> [MLP] -> score (0-1)

    Attributes:
        threshold: Score above which article is classified as obituary
        embedder: SentenceTransformer model for generating embeddings
        classifier: Trained MLP classifier
        scaler: StandardScaler for normalizing embeddings
    """

    def __init__(
        self,
        threshold: float = 0.90,
        model_dir: Optional[Path] = None,
        device: str = 'cpu'
    ):
        """
        Initialize the obituary detector.

        Args:
            threshold: Classification threshold (default 0.90 — LD#83 op-point;
                0.95 was the pre-LD#83 June-holdout recommendation)
            model_dir: Path to directory containing classifier and scaler
            device: Device for embedder ('cpu' or 'cuda')
        """
        self.threshold = threshold
        self.device = device

        # Set model directory
        if model_dir is None:
            model_dir = Path(__file__).parent / 'models'
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

        if not self.model_dir.is_dir():
            raise FileNotFoundError(
                f"Model directory not found: {self.model_dir}\n"
                f"Train the model first (see filters/common/obituary_detector/training/train_v1.py) "
                f"or copy artifacts from gpu-server."
            )

        # Load embedder
        self._embedder = SentenceTransformer(
            'paraphrase-multilingual-mpnet-base-v2',
            device=self.device
        )

        # Load classifier (with optional integrity check)
        from filters.common.embedding_stage import _verify_pickle_integrity
        classifier_path = self.model_dir / 'mlp_classifier.pkl'
        if not classifier_path.exists():
            raise FileNotFoundError(
                f"Classifier not found: {classifier_path}\n"
                f"Expected artifact contract: mlp_classifier.pkl + scaler.pkl in {self.model_dir}"
            )
        _verify_pickle_integrity(classifier_path)
        with open(classifier_path, 'rb') as f:
            self._classifier = pickle.load(f)

        # Load scaler (with optional integrity check)
        scaler_path = self.model_dir / 'scaler.pkl'
        if not scaler_path.exists():
            raise FileNotFoundError(
                f"Scaler not found: {scaler_path}\n"
                f"Expected artifact contract: mlp_classifier.pkl + scaler.pkl in {self.model_dir}"
            )
        _verify_pickle_integrity(scaler_path)
        with open(scaler_path, 'rb') as f:
            self._scaler = pickle.load(f)

        self._loaded = True

    def _prepare_text(self, article: Union[dict, str]) -> str:
        """
        Prepare text from article for embedding.

        Args:
            article: Article dict with 'title' and 'content', or raw text string

        Returns:
            Combined text for embedding. Note: the embedder has a 128-token limit,
            so only the first ~100 words of content are seen by the model.

        Raises:
            TypeError: if article is not a dict or str
        """
        if isinstance(article, str):
            return article.strip()

        if not isinstance(article, dict):
            raise TypeError(
                f"Expected dict or str for article, got {type(article).__name__}. "
                f"Article dict should have 'title' and 'content' keys."
            )

        # Coerce None values to empty strings (avoids "None" token in embedding)
        title = article.get('title') or ''
        content = article.get('content') or ''

        # Coerce non-string values to strings
        title = str(title) if not isinstance(title, str) else title
        content = str(content) if not isinstance(content, str) else content

        return f"{title} {content}".strip()

    def is_obituary(self, article: Union[dict, str]) -> dict:
        """
        Check if an article is an obituary/death-memorial piece.

        Args:
            article: Article dict with 'title' and 'content', or raw text

        Returns:
            Dict with:
                - is_obituary: bool
                - score: float (0-1)
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
            'is_obituary': bool(score >= self.threshold),
            'score': float(score),
            'inference_time_ms': inference_time_ms,
            'version': 'v5'
        }

    def batch_predict(self, articles: list, batch_size: int = 32) -> list:
        """
        Predict obituary scores for multiple articles.

        Args:
            articles: List of article dicts or text strings
            batch_size: Batch size for embedding generation

        Returns:
            List of result dicts (same format as is_obituary)
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
            show_progress_bar=False
        )

        # Scale
        embeddings_scaled = self._scaler.transform(embeddings)

        # Predict
        scores = self._classifier.predict_proba(embeddings_scaled)[:, 1]

        total_time_ms = (time.perf_counter() - start_time) * 1000
        avg_time_ms = total_time_ms / len(articles)

        results = []
        for score in scores:
            results.append({
                'is_obituary': bool(score >= self.threshold),
                'score': float(score),
                'inference_time_ms': avg_time_ms,
                'version': 'v5'
            })

        return results

    def get_score(self, article: Union[dict, str]) -> float:
        """
        Get raw obituary score without threshold application.

        Note: First call triggers lazy model loading (~1-2 seconds for the
        SentenceTransformer embedder). Subsequent calls are fast (~1-5ms).

        Args:
            article: Article dict or text string

        Returns:
            Obituary probability (0-1)
        """
        result = self.is_obituary(article)
        return result['score']


# Convenience function for quick checks
def is_obituary(article: Union[dict, str], threshold: float = 0.90) -> bool:
    """
    Quick check if article is an obituary.

    Note: Creates new detector instance each call. For batch processing,
    use ObituaryDetectorV5 class directly.
    """
    detector = ObituaryDetectorV5(threshold=threshold)
    return detector.is_obituary(article)['is_obituary']
