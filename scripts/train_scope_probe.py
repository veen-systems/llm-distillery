"""
Train a logistic regression scope probe on E5-small embeddings, then
screen the master dataset to find likely MEDIUM+ candidates for batch labeling.

This is a temporary utility for the belonging filter's ADR-003 (Screen + Merge)
strategy. The probe ranks master dataset articles by likelihood of being MEDIUM+,
letting us prioritize likely positives for oracle scoring instead of wasting
budget on obvious LOWs.

Why logistic regression instead of the MLP probe (train_probe.py)?
  - Only 152 scored articles (19 MEDIUM+) — MLP would overfit
  - LR with class_weight='balanced' handles class imbalance
  - 384 features → 1 output vs 384→256→128→6 (~100K params)

Usage:
    PYTHONPATH=. python scripts/train_scope_probe.py \
        --filter filters/belonging/v1 \
        --scored-dir datasets/belonging \
        --master-dataset datasets/raw/master_dataset_20251009_20251124.jsonl \
        --output datasets/belonging/scope_candidates.jsonl \
        --top-n 5000
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneOut

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_scored_articles(scored_dir: Path) -> list[dict]:
    """Load all scored_batch_*.jsonl files from a directory."""
    files = sorted(scored_dir.glob("scored_batch_*.jsonl"))
    if not files:
        raise FileNotFoundError(f"No scored_batch_*.jsonl files in {scored_dir}")

    articles = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    articles.append(json.loads(line))

    logger.info(f"Loaded {len(articles)} scored articles from {len(files)} files")
    return articles


def load_filter_config(filter_dir: Path) -> dict:
    """Load config.yaml from filter directory."""
    config_path = filter_dir / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def extract_dimension_info(config: dict) -> tuple[list[str], dict[str, float], float]:
    """Extract dimension names, weights, and medium threshold from config."""
    dimensions = config["scoring"]["dimensions"]
    dim_names = list(dimensions.keys())
    dim_weights = {name: dim["weight"] for name, dim in dimensions.items()}

    tiers = config["scoring"].get("tiers", {})
    medium_threshold = 4.0
    if "medium" in tiers:
        tier_def = tiers["medium"]
        medium_threshold = tier_def.get("threshold", tier_def.get("min_score", 4.0))

    return dim_names, dim_weights, medium_threshold


def extract_gatekeeper_info(config: dict) -> tuple[str | None, float, float]:
    """Extract gatekeeper dimension, threshold, and max_score from config."""
    gatekeepers = config["scoring"].get("gatekeepers", {})
    if not gatekeepers:
        return None, 0.0, 0.0

    # Take the first gatekeeper
    gk = next(iter(gatekeepers.values()))
    return gk["dimension"], gk["threshold"], gk["max_score"]


# ---------------------------------------------------------------------------
# Scoring logic (mirrors filter_base_scorer.py)
# ---------------------------------------------------------------------------

def compute_weighted_avg(
    dim_scores: dict[str, float],
    dim_names: list[str],
    dim_weights: dict[str, float],
) -> float:
    """Compute weighted average from dimension scores."""
    return sum(dim_scores.get(dim, 0) * dim_weights[dim] for dim in dim_names)


def apply_gatekeeper(
    weighted_avg: float,
    dim_scores: dict[str, float],
    gk_dim: str | None,
    gk_threshold: float,
    gk_cap: float,
) -> float:
    """Apply gatekeeper cap: if gatekeeper dim < threshold, cap the score."""
    if gk_dim is None:
        return weighted_avg
    if dim_scores.get(gk_dim, 0) < gk_threshold:
        return min(weighted_avg, gk_cap)
    return weighted_avg


def label_articles(
    articles: list[dict],
    analysis_key: str,
    dim_names: list[str],
    dim_weights: dict[str, float],
    medium_threshold: float,
    gk_dim: str | None,
    gk_threshold: float,
    gk_cap: float,
) -> list[int]:
    """
    Label articles as 1 (MEDIUM+) or 0 (LOW) based on weighted avg + gatekeeper.

    Returns list of binary labels aligned with input articles.
    """
    labels = []
    for article in articles:
        analysis = article.get(analysis_key, {})
        dim_scores = {}
        for dim in dim_names:
            dim_data = analysis.get(dim, {})
            if isinstance(dim_data, dict):
                dim_scores[dim] = dim_data.get("score", 0)
            else:
                dim_scores[dim] = float(dim_data) if dim_data else 0

        weighted_avg = compute_weighted_avg(dim_scores, dim_names, dim_weights)
        weighted_avg = apply_gatekeeper(weighted_avg, dim_scores, gk_dim, gk_threshold, gk_cap)
        labels.append(1 if weighted_avg >= medium_threshold else 0)

    return labels


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------

def generate_embeddings(articles: list[dict], model_name: str, device: str = "cpu", batch_size: int = 64) -> np.ndarray:
    """Generate E5-small embeddings for articles. Same text format as train_probe.py."""
    from sentence_transformers import SentenceTransformer

    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name, device=device)

    texts = [f"{a.get('title', '')}\n\n{a.get('content', '')}" for a in articles]
    logger.info(f"Encoding {len(texts)} articles...")
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True, convert_to_numpy=True)
    return embeddings


# ---------------------------------------------------------------------------
# Probe training + LOOCV
# ---------------------------------------------------------------------------

def run_loocv(X: np.ndarray, y: np.ndarray) -> dict:
    """
    Leave-one-out cross-validation for logistic regression.

    Returns dict with predictions, recall, precision, and missed indices.
    """
    loo = LeaveOneOut()
    predictions = np.zeros(len(y), dtype=int)

    for train_idx, test_idx in loo.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        clf = LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            solver="lbfgs",
            random_state=42,
        )
        clf.fit(X_train, y_train)
        predictions[test_idx] = clf.predict(X_test)

    # Metrics on MEDIUM+ class
    positive_mask = y == 1
    n_positive = positive_mask.sum()
    true_positives = ((predictions == 1) & (y == 1)).sum()
    predicted_positive = (predictions == 1).sum()
    false_positives = ((predictions == 1) & (y == 0)).sum()

    recall = true_positives / n_positive if n_positive > 0 else 0
    precision = true_positives / predicted_positive if predicted_positive > 0 else 0

    missed_indices = np.where((y == 1) & (predictions == 0))[0].tolist()

    return {
        "predictions": predictions,
        "recall": recall,
        "precision": precision,
        "true_positives": int(true_positives),
        "false_positives": int(false_positives),
        "n_positive": int(n_positive),
        "predicted_positive": int(predicted_positive),
        "missed_indices": missed_indices,
    }


def train_final_probe(X: np.ndarray, y: np.ndarray) -> LogisticRegression:
    """Train final logistic regression on all data."""
    clf = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        solver="lbfgs",
        random_state=42,
    )
    clf.fit(X, y)
    return clf


# ---------------------------------------------------------------------------
# Master dataset screening
# ---------------------------------------------------------------------------

def load_prefilter(filter_dir: Path):
    """The oracle-path gate batch_scorer applies, as an `apply_filter` object.

    Per-lens prefilters were deleted 2026-10-01 (NexusMind#284, decision 0); this
    used to import `filters.<name>.<ver>.prefilter`. Screening for the oracle now
    uses the very gate the oracle run applies (#93 length floor + validation),
    reused rather than re-implemented so the two cannot drift.
    """
    from ground_truth.batch_scorer import load_filter_package, make_oracle_prefilter

    lens_obj, _, _ = load_filter_package(filter_dir)
    gate = make_oracle_prefilter(lens_obj)

    class _OracleGate:
        def apply_filter(self, article):
            return (True, "passed") if gate(article) else (False, "oracle_gate")

    return _OracleGate()


def stream_master_dataset(path: Path):
    """Stream articles from master dataset JSONL."""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def screen_master_dataset(
    master_path: Path,
    prefilter,
    probe: LogisticRegression,
    embedding_model_name: str,
    device: str,
    top_n: int,
    batch_size: int = 256,
) -> tuple[list[dict], dict]:
    """
    Screen master dataset: prefilter → embed → score → rank → top-N.

    Returns (top_n_articles, stats_dict).
    """
    from sentence_transformers import SentenceTransformer

    logger.info(f"Loading embedding model for screening: {embedding_model_name}")
    embed_model = SentenceTransformer(embedding_model_name, device=device)

    # Phase 1: prefilter
    logger.info("Streaming master dataset through prefilter...")
    passed_articles = []
    total = 0
    blocked = 0
    block_reasons = {}

    for article in stream_master_dataset(master_path):
        total += 1
        should_pass, reason = prefilter.apply_filter(article)
        if should_pass:
            passed_articles.append(article)
        else:
            blocked += 1
            block_reasons[reason] = block_reasons.get(reason, 0) + 1

        if total % 25000 == 0:
            logger.info(f"  Processed {total:,} articles, {len(passed_articles):,} passed prefilter")

    logger.info(f"Prefilter: {len(passed_articles):,} passed / {total:,} total ({blocked:,} blocked)")

    # Phase 2: embed in batches and score
    logger.info(f"Embedding {len(passed_articles):,} articles in batches of {batch_size}...")
    all_scores = []

    for i in range(0, len(passed_articles), batch_size):
        batch = passed_articles[i:i + batch_size]
        texts = [f"{a.get('title', '')}\n\n{a.get('content', '')}" for a in batch]
        embeddings = embed_model.encode(texts, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True)
        batch_scores = probe.predict_proba(embeddings)[:, 1]
        all_scores.extend(batch_scores.tolist())

        if (i // batch_size + 1) % 50 == 0:
            logger.info(f"  Scored {i + len(batch):,} / {len(passed_articles):,} articles")

    # Phase 3: rank and select top-N
    scored_pairs = list(zip(all_scores, range(len(passed_articles))))
    scored_pairs.sort(key=lambda x: x[0], reverse=True)

    actual_top_n = min(top_n, len(scored_pairs))
    top_articles = []
    for score, idx in scored_pairs[:actual_top_n]:
        article = passed_articles[idx]
        article["_probe_score"] = round(score, 6)
        top_articles.append(article)

    # Stats
    all_scores_arr = np.array(all_scores)
    top_scores_arr = np.array([a["_probe_score"] for a in top_articles])

    stats = {
        "total_articles": total,
        "prefilter_passed": len(passed_articles),
        "prefilter_blocked": blocked,
        "prefilter_block_rate": blocked / total if total > 0 else 0,
        "block_reasons": dict(sorted(block_reasons.items(), key=lambda x: -x[1])),
        "top_n_actual": actual_top_n,
        "top_scores_min": float(top_scores_arr.min()) if len(top_scores_arr) > 0 else 0,
        "top_scores_median": float(np.median(top_scores_arr)) if len(top_scores_arr) > 0 else 0,
        "top_scores_max": float(top_scores_arr.max()) if len(top_scores_arr) > 0 else 0,
        "all_scores_mean": float(all_scores_arr.mean()),
        "all_scores_std": float(all_scores_arr.std()),
    }

    return top_articles, stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Train scope probe and screen master dataset for batch labeling candidates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--filter", type=Path, required=True, help="Filter directory (e.g. filters/belonging/v1)")
    parser.add_argument("--scored-dir", type=Path, required=True, help="Directory with scored_batch_*.jsonl")
    parser.add_argument("--master-dataset", type=Path, required=True, help="Master dataset JSONL to screen")
    parser.add_argument("--output", type=Path, required=True, help="Output JSONL for top candidates")
    parser.add_argument("--top-n", type=int, default=5000, help="Number of top candidates to output (default: 5000)")
    parser.add_argument("--embedding-model", type=str, default="intfloat/multilingual-e5-small")
    parser.add_argument("--device", type=str, default=None, help="Device (cuda or cpu, default: auto)")
    parser.add_argument("--screen-only", action="store_true", help="Skip training, just screen (requires prior probe)")
    args = parser.parse_args()

    if args.device is None:
        import torch
        args.device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Device: {args.device}")

    # -----------------------------------------------------------------------
    # Load config
    # -----------------------------------------------------------------------
    config = load_filter_config(args.filter)
    dim_names, dim_weights, medium_threshold = extract_dimension_info(config)
    gk_dim, gk_threshold, gk_cap = extract_gatekeeper_info(config)

    filter_name = config["filter"]["name"]
    analysis_key = f"{filter_name}_analysis"

    logger.info(f"Filter: {filter_name}")
    logger.info(f"Dimensions: {dim_names}")
    logger.info(f"Weights: {dim_weights}")
    logger.info(f"Medium threshold: {medium_threshold}")
    logger.info(f"Gatekeeper: {gk_dim} < {gk_threshold} -> cap {gk_cap}")

    # -----------------------------------------------------------------------
    # Phase A: Train probe
    # -----------------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print("=== Scope Probe Training ===")
    print(f"{'=' * 60}")

    # Load scored articles
    scored_articles = load_scored_articles(args.scored_dir)

    # Label them
    labels = label_articles(
        scored_articles, analysis_key, dim_names, dim_weights,
        medium_threshold, gk_dim, gk_threshold, gk_cap,
    )
    y = np.array(labels)
    n_positive = y.sum()
    n_negative = len(y) - n_positive

    print(f"\nScored articles: {len(scored_articles)} ({n_positive} MEDIUM+, {n_negative} LOW)")

    if n_positive < 5:
        print(f"\nERROR: Only {n_positive} MEDIUM+ articles. Need at least 5 for a meaningful probe.")
        sys.exit(1)

    # Show label distribution detail
    print(f"\nWeighted average distribution (using config weights + gatekeeper):")
    weighted_avgs = []
    for article in scored_articles:
        analysis = article.get(analysis_key, {})
        dim_scores = {}
        for dim in dim_names:
            dim_data = analysis.get(dim, {})
            if isinstance(dim_data, dict):
                dim_scores[dim] = dim_data.get("score", 0)
            else:
                dim_scores[dim] = float(dim_data) if dim_data else 0
        wavg = compute_weighted_avg(dim_scores, dim_names, dim_weights)
        wavg = apply_gatekeeper(wavg, dim_scores, gk_dim, gk_threshold, gk_cap)
        weighted_avgs.append(wavg)

    wavg_arr = np.array(weighted_avgs)
    for threshold in [3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0]:
        count = (wavg_arr >= threshold).sum()
        print(f"  >= {threshold}: {count} articles ({count/len(wavg_arr)*100:.1f}%)")

    # Embed scored articles
    t0 = time.time()
    embeddings = generate_embeddings(scored_articles, args.embedding_model, device=args.device)
    embed_time = time.time() - t0
    logger.info(f"Embedding dim: {embeddings.shape[1]}, took {embed_time:.1f}s")

    # LOOCV
    print(f"\nRunning leave-one-out cross-validation...")
    t0 = time.time()
    loocv = run_loocv(embeddings, y)
    loocv_time = time.time() - t0

    print(f"LOOCV completed in {loocv_time:.1f}s")
    print(f"LOOCV recall on MEDIUM+:    {loocv['true_positives']}/{loocv['n_positive']} ({loocv['recall']:.1%})")
    print(f"LOOCV precision on pred M+: {loocv['true_positives']}/{loocv['predicted_positive']} ({loocv['precision']:.1%})")
    print(f"False positives (LOW predicted as M+): {loocv['false_positives']}")

    # Show which MEDIUM+ articles the probe misses
    if loocv["missed_indices"]:
        print(f"\nMissed MEDIUM+ articles ({len(loocv['missed_indices'])}):")
        for idx in loocv["missed_indices"]:
            article = scored_articles[idx]
            wavg = weighted_avgs[idx]
            print(f"  [{idx}] wavg={wavg:.2f} | {article.get('title', 'untitled')[:80]}")
    else:
        print(f"\nNo MEDIUM+ articles missed — perfect recall!")

    # Train final probe
    print(f"\nTraining final probe on all {len(scored_articles)} articles...")
    probe = train_final_probe(embeddings, y)

    # Sanity check: score the training set
    train_proba = probe.predict_proba(embeddings)[:, 1]
    train_pred = (train_proba >= 0.5).astype(int)
    train_acc = (train_pred == y).mean()
    print(f"Training set accuracy: {train_acc:.1%}")
    print(f"Training set probe scores — MEDIUM+ mean: {train_proba[y == 1].mean():.3f}, LOW mean: {train_proba[y == 0].mean():.3f}")

    # -----------------------------------------------------------------------
    # Phase B: Screen master dataset
    # -----------------------------------------------------------------------
    if not args.master_dataset.exists():
        print(f"\nWARNING: Master dataset not found: {args.master_dataset}")
        print("Skipping screening phase. Probe training complete.")
        return

    print(f"\n{'=' * 60}")
    print("=== Master Dataset Screening ===")
    print(f"{'=' * 60}")

    # Load prefilter
    prefilter = load_prefilter(args.filter)
    logger.info(f"Prefilter loaded: {type(prefilter).__name__}")

    t0 = time.time()
    top_articles, stats = screen_master_dataset(
        master_path=args.master_dataset,
        prefilter=prefilter,
        probe=probe,
        embedding_model_name=args.embedding_model,
        device=args.device,
        top_n=args.top_n,
    )
    screen_time = time.time() - t0

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for article in top_articles:
            f.write(json.dumps(article, ensure_ascii=False) + "\n")

    # Print report
    print(f"\nTotal articles: {stats['total_articles']:,}")
    print(f"Prefilter passed: {stats['prefilter_passed']:,} ({1 - stats['prefilter_block_rate']:.1%})")
    print(f"Prefilter blocked: {stats['prefilter_blocked']:,} ({stats['prefilter_block_rate']:.1%})")

    print(f"\nBlock reasons:")
    for reason, count in stats["block_reasons"].items():
        print(f"  {reason}: {count:,}")

    print(f"\nTop {stats['top_n_actual']:,} probe scores:")
    print(f"  min={stats['top_scores_min']:.4f}, median={stats['top_scores_median']:.4f}, max={stats['top_scores_max']:.4f}")
    print(f"All scores: mean={stats['all_scores_mean']:.4f}, std={stats['all_scores_std']:.4f}")

    # Estimate MEDIUM+ in top-N using LOOCV precision
    if loocv["precision"] > 0:
        estimated_positives = int(stats["top_n_actual"] * loocv["precision"])
        print(f"\nEstimated MEDIUM+ in top {stats['top_n_actual']:,}: ~{estimated_positives} (based on LOOCV precision {loocv['precision']:.1%})")

    print(f"\nScreening completed in {screen_time / 60:.1f} minutes")
    print(f"Output: {args.output} ({stats['top_n_actual']:,} articles)")

    print(f"\n{'=' * 60}")
    print("=== Recommended Batch Labeling Strategy ===")
    print(f"{'=' * 60}")
    print(f"1. Score scope_candidates.jsonl (enriched positives): ~{stats['top_n_actual']:,} articles")
    print(f"2. Score random sample from master dataset (negatives): ~5,000 articles")
    print(f"3. Merge both + {len(scored_articles)} already scored -> ~{stats['top_n_actual'] + 5000 + len(scored_articles):,} total training articles")


if __name__ == "__main__":
    main()
