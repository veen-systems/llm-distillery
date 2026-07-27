"""
Embedding Stage - Fast screening using frozen embeddings + MLP probe.

Stage 1 of the hybrid inference pipeline. Uses sentence-transformer embeddings
and a trained MLP probe to quickly estimate article scores. Articles with
low estimated scores skip the expensive fine-tuned model (Stage 2).

Usage:
    from filters.common.embedding_stage import EmbeddingStage

    stage = EmbeddingStage(
        embedding_model_name="intfloat/multilingual-e5-large",
        probe_path="filters/uplifting/v7/probe/embedding_probe.pkl",
        threshold=3.0,
        dimension_weights={"human_wellbeing_impact": 0.25, ...},
        dimension_names=["human_wellbeing_impact", ...],
    )

    results = stage.screen_batch(articles)
    # -> [(needs_stage2=False, weighted_avg=1.2, scores={...}), ...]
"""

import logging
import pickle
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


def _verify_pickle_integrity(pkl_path: Path):
    """Verify pickle file integrity using companion .sha256 file if present.

    If a .sha256 file exists alongside the pickle, computes the SHA-256 hash
    and raises ValueError on mismatch. If no hash file exists, logs a warning.
    """
    import hashlib
    hash_path = pkl_path.with_suffix(pkl_path.suffix + ".sha256")
    if hash_path.exists():
        expected = hash_path.read_text().strip().split()[0]
        actual = hashlib.sha256(pkl_path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(
                f"Pickle integrity check failed for {pkl_path}:\n"
                f"  expected: {expected}\n"
                f"  actual:   {actual}"
            )
        logger.debug(f"Pickle integrity verified: {pkl_path.name}")
    else:
        logger.debug(
            f"No .sha256 hash file for {pkl_path.name} — skipping integrity check"
        )


class MLPProbe(nn.Module):
    """Two-layer MLP probe for regression on frozen embeddings."""

    def __init__(
        self,
        input_dim: int,
        output_dim: int,
        hidden_sizes: List[int] = [256, 128],
        dropout: float = 0.2,
    ):
        super().__init__()

        layers = []
        prev_dim = input_dim

        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_dim, hidden_size),
                nn.ReLU(),
                nn.Dropout(dropout),
            ])
            prev_dim = hidden_size

        layers.append(nn.Linear(prev_dim, output_dim))
        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)


@dataclass
class ScreeningResult:
    """Result from Stage 1 embedding screening."""
    needs_stage2: bool
    weighted_avg: float
    scores: Dict[str, float]


class EmbeddingStage:
    """
    Stage 1 of the hybrid inference pipeline.

    Uses a sentence-transformer embedding model and a trained MLP probe
    to quickly estimate article scores. Articles below the threshold
    are classified as LOW without running the expensive Stage 2 model.

    The embedding model is loaded lazily as a singleton (shared across
    all EmbeddingStage instances using the same model name).
    """

    # Singleton cache for embedding models (shared across instances)
    _embedding_models: Dict[str, object] = {}
    _embedding_models_lock = threading.Lock()

    def __init__(
        self,
        embedding_model_name: str,
        probe_path: str,
        threshold: float,
        dimension_weights: Dict[str, float],
        dimension_names: List[str],
        device: Optional[str] = None,
    ):
        """
        Initialize the embedding stage.

        Args:
            embedding_model_name: HuggingFace model name for sentence-transformers
            probe_path: Path to trained MLP probe pickle file
            threshold: Weighted average below this -> skip Stage 2
            dimension_weights: Weight per dimension for weighted average
            dimension_names: Ordered list of dimension names
            device: Device to use ('cuda', 'cpu', or None for auto)
        """
        self.embedding_model_name = embedding_model_name
        self.probe_path = Path(probe_path)
        self.threshold = threshold
        self.dimension_weights = dimension_weights
        self.dimension_names = dimension_names

        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Load probe (small, always loaded eagerly)
        self._load_probe()

        # Embedding model loaded lazily on first use
        self._embedder = None

    # Lock for the torch storage monkeypatch during probe loading
    _probe_load_lock = threading.Lock()

    def _load_probe(self):
        """Load the trained MLP probe from pickle."""
        if not self.probe_path.exists():
            raise FileNotFoundError(
                f"Probe file not found: {self.probe_path}\n"
                f"Train a probe first with: PYTHONPATH=. python scripts/train_probe.py --filter <filter_path> --data-dir <data_dir> --objective recall"
            )

        # Verify probe file integrity if SHA-256 hash file exists
        _verify_pickle_integrity(self.probe_path)

        # Pickle contains non-tensor Python objects (sklearn scalers, config dicts)
        # so weights_only=False is required. Temporarily patch torch storage
        # loading to map CUDA tensors to CPU.
        # Lock required: monkeypatch is global and not thread-safe.
        with self._probe_load_lock:
            import torch.storage as _ts
            _original_load = _ts._load_from_bytes

            def _cpu_load_from_bytes(b):
                import io
                return torch.load(io.BytesIO(b), map_location="cpu", weights_only=False)

            _ts._load_from_bytes = _cpu_load_from_bytes
            try:
                with open(self.probe_path, "rb") as f:
                    data = pickle.load(f)
            finally:
                _ts._load_from_bytes = _original_load

        # Load scaler
        self.scaler = data["scaler"]

        # Reconstruct MLP from saved state
        config = data["model_config"]
        self.probe = MLPProbe(
            input_dim=config["input_dim"],
            output_dim=config["output_dim"],
        )
        self.probe.load_state_dict(data["state_dict"])
        self.probe.to(self.device)
        self.probe.eval()

        logger.info(
            f"Loaded MLP probe from {self.probe_path} "
            f"(input_dim={config['input_dim']}, output_dim={config['output_dim']})"
        )

    def _ensure_embedder_loaded(self):
        """Lazy-load the embedding model (singleton per model name).

        Thread-safe using double-checked locking pattern.
        """
        if self._embedder is not None:
            return

        model_name = self.embedding_model_name

        # Fast path: already loaded by another instance
        if model_name in self._embedding_models:
            self._embedder = self._embedding_models[model_name]
            return

        # Slow path: need to load, acquire lock
        with self._embedding_models_lock:
            # Double-check after acquiring lock
            if model_name in self._embedding_models:
                self._embedder = self._embedding_models[model_name]
                return

            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {model_name}")
            embedder = SentenceTransformer(model_name, device=self.device)
            self._embedding_models[model_name] = embedder
            self._embedder = embedder
            logger.info(f"Embedding model loaded: {model_name}")

    @staticmethod
    def _prepare_text(article: Dict) -> str:
        """Prepare article text for embedding."""
        title = article.get("title", "")
        content = article.get("content", "")

        if title and content:
            return f"{title}\n\n{content}"
        return title or content

    def _compute_weighted_avg(self, scores: Dict[str, float]) -> float:
        """Compute weighted average from dimension scores."""
        return sum(
            scores[dim] * self.dimension_weights[dim]
            for dim in self.dimension_names
        )

    def screen_batch(
        self,
        articles: List[Dict],
        batch_size: int = 32,
    ) -> List[ScreeningResult]:
        """
        Screen a batch of articles using embedding + MLP probe.

        Args:
            articles: List of article dicts with 'title' and 'content'
            batch_size: Batch size for embedding generation

        Returns:
            List of ScreeningResult with needs_stage2 flag, weighted_avg, and scores
        """
        if not articles:
            return []

        self._ensure_embedder_loaded()

        # Generate embeddings
        texts = [self._prepare_text(article) for article in articles]
        embeddings = self._embedder.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        # Scale embeddings
        embeddings_scaled = self.scaler.transform(embeddings)

        # Run MLP probe
        with torch.no_grad():
            inputs = torch.FloatTensor(embeddings_scaled).to(self.device)
            predictions = self.probe(inputs).cpu().numpy()

        # Process results
        results = []
        for i in range(len(articles)):
            raw_scores = predictions[i]

            # Clamp to 0-10
            scores = {
                dim: float(max(0.0, min(10.0, raw_scores[j])))
                for j, dim in enumerate(self.dimension_names)
            }

            weighted_avg = self._compute_weighted_avg(scores)
            needs_stage2 = weighted_avg >= self.threshold

            results.append(ScreeningResult(
                needs_stage2=needs_stage2,
                weighted_avg=weighted_avg,
                scores=scores,
            ))

        return results

    def screen_article(self, article: Dict) -> ScreeningResult:
        """Screen a single article. Convenience wrapper around screen_batch."""
        return self.screen_batch([article])[0]
