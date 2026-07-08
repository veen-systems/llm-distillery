"""
Train an e5-small MLP probe for hybrid inference.

Generates embeddings from training data, trains a 2-layer MLP probe,
and saves the probe pickle in the format expected by EmbeddingStage.

Usage:
    PYTHONPATH=. python scripts/train_probe.py \
        --filter filters/cultural-discovery/v4 \
        --data-dir datasets/training/cultural-discovery_v4 \
        --embedding-model intfloat/multilingual-e5-small

⚠️ KNOWN DEFECT FOR NEEDLE FILTERS (nature_recovery v4, H3) — DO NOT USE AS-IS:
This trainer minimizes L1Loss on the raw 6-dim labels (an L1 REGRESSION) and
selects on val_mae. On a ~85% zero-floor corpus that collapses to a floor
predictor — exactly the recall bug v4 exists to fix (see
docs/agents/filter-development-guide.md Issue 4). The e5 probe for
nature_recovery v4 MUST be a RECALL-FIRST CLASSIFIER instead:
  - target: BINARY  y = 1 if weighted-avg (gatekeepered) >= 4.0 (MEDIUM+), else 0
  - loss:   class-weighted BCE (or balanced sampling) — positives are ~14%
  - select: threshold from the VAL RECALL CURVE at a target FN rate on MEDIUM+
            (uplifting hit ~0.9% FN at threshold 1.00), NOT val_mae
  - validate: FN rate on the 129 known-blocked positives (recall-side)
  - embedding: intfloat/multilingual-e5-small (multilingual screening)
Implementation + validation is a gpu-server step (needs torch + embeddings +
the 129 cohort). Full spec and commands: docs/nature_recovery_v4_RUNBOOK.md.
The threshold-from-recall-curve and FN-rate logic should be written as pure
functions and unit-tested (as done for agreement_gate.py) before the gpu run.
"""

import argparse
import json
import logging
import pickle
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class MLPProbe(nn.Module):
    """Two-layer MLP probe for regression on frozen embeddings."""

    def __init__(self, input_dim, output_dim, hidden_sizes=[256, 128], dropout=0.2):
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

    def forward(self, x):
        return self.network(x)


def load_data(path):
    """Load JSONL training data."""
    articles = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                articles.append(json.loads(line))
    return articles


def generate_embeddings(articles, model_name, device="cpu", batch_size=64):
    """Generate sentence embeddings for articles."""
    from sentence_transformers import SentenceTransformer

    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name, device=device)

    texts = [f"{a['title']}\n\n{a['content']}" for a in articles]
    logger.info(f"Encoding {len(texts)} articles...")
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True, convert_to_numpy=True)

    return embeddings


def train_mlp_probe(train_X, train_y, val_X, val_y, device="cpu", epochs=100, patience=10, lr=0.001):
    """Train MLP probe with early stopping."""
    scaler = StandardScaler()
    train_X_scaled = scaler.fit_transform(train_X)
    val_X_scaled = scaler.transform(val_X)

    train_dataset = TensorDataset(
        torch.FloatTensor(train_X_scaled),
        torch.FloatTensor(train_y),
    )
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)

    input_dim = train_X.shape[1]
    output_dim = train_y.shape[1]
    model = MLPProbe(input_dim=input_dim, output_dim=output_dim).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.L1Loss()

    val_X_t = torch.FloatTensor(val_X_scaled).to(device)
    val_y_t = torch.FloatTensor(val_y).to(device)

    best_val_mae = float("inf")
    best_state = None
    patience_counter = 0

    for epoch in range(epochs):
        model.train()
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            optimizer.zero_grad()
            loss = criterion(model(batch_X), batch_y)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_pred = model(val_X_t)
            val_mae = torch.mean(torch.abs(val_pred - val_y_t)).item()

        if val_mae < best_val_mae:
            best_val_mae = val_mae
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1

        if patience_counter >= patience:
            logger.info(f"Early stopping at epoch {epoch + 1}")
            break

        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch + 1}: Val MAE = {val_mae:.4f}")

    model.load_state_dict(best_state)
    logger.info(f"Best Val MAE: {best_val_mae:.4f}")

    return model, scaler, best_val_mae


def main():
    parser = argparse.ArgumentParser(description="Train e5-small MLP probe for hybrid inference")
    parser.add_argument("--filter", type=Path, required=True, help="Filter directory")
    parser.add_argument("--data-dir", type=Path, required=True, help="Training data directory")
    parser.add_argument("--embedding-model", type=str, default="intfloat/multilingual-e5-small")
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--output", type=Path, default=None, help="Output path (default: <filter>/probe/embedding_probe_e5small.pkl)")
    args = parser.parse_args()

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Device: {device}")

    # Load data
    train_articles = load_data(args.data_dir / "train.jsonl")
    val_articles = load_data(args.data_dir / "val.jsonl")
    logger.info(f"Train: {len(train_articles)}, Val: {len(val_articles)}")

    # Generate embeddings
    all_articles = train_articles + val_articles
    embeddings = generate_embeddings(all_articles, args.embedding_model, device=device)
    train_emb = embeddings[: len(train_articles)]
    val_emb = embeddings[len(train_articles) :]
    logger.info(f"Embedding dim: {embeddings.shape[1]}")

    # Extract labels
    train_labels = np.array([a["labels"] for a in train_articles], dtype=np.float32)
    val_labels = np.array([a["labels"] for a in val_articles], dtype=np.float32)

    # Train probe
    logger.info("Training MLP probe...")
    model, scaler, val_mae = train_mlp_probe(train_emb, train_labels, val_emb, val_labels, device=device)

    # Save in EmbeddingStage format
    output_path = args.output or (args.filter / "probe" / "embedding_probe_e5small.pkl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    probe_data = {
        "probe_type": "mlp",
        "scaler": scaler,
        "state_dict": model.state_dict(),
        "model_config": {
            "input_dim": model.network[0].in_features,
            "output_dim": model.network[-1].out_features,
        },
        "metrics": {"val_mae": val_mae},
    }

    with open(output_path, "wb") as f:
        pickle.dump(probe_data, f)

    logger.info(f"Probe saved to {output_path}")
    logger.info(f"Probe MAE: {val_mae:.4f}")


if __name__ == "__main__":
    main()
