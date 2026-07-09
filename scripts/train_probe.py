"""
Train an e5-small MLP probe for hybrid inference (Stage 1 screening).

Two objectives:

  --objective regression  (DEFAULT — backward compatible)
      L1 regression on the raw 6-dim labels, select on val_mae. This is the
      historical behavior used by balanced filters (e.g. cultural-discovery).

  --objective recall      (needle-in-haystack filters — nature_recovery v4, H3)
      RECALL-FIRST screen. The Stage-1 decision that actually ships is
      `weighted_avg(probe_output) >= threshold` (see
      filters/common/embedding_stage.py:298 — the evidence gatekeeper is NOT
      applied at Stage 1, hybrid_scorer.py:241). On a ~85% zero-floor corpus an
      L1 regression collapses to a floor predictor and the screen drops genuine
      positives — the exact recall bug nature_recovery v4 exists to fix
      (docs/agents/filter-development-guide.md Issue 4).

      The recall objective instead trains the probe's *weighted average* as a
      binary MEDIUM+ classifier and picks the screen threshold from the val
      recall curve:
        - target: BINARY  y = 1 if gatekeepered weighted-avg(labels) >= 4.0
        - loss:   class-weighted BCE on sigmoid(wa_scale * (wa_pred - 4.0)),
                  pos_weight = n_neg/n_pos  (positives are ~15%)
                  + light auxiliary L1 on the 6-dim labels so the per-dim
                    `scores` surfaced for Stage-1-LOW articles stay interpretable
        - select: checkpoint by min val BCE; screen threshold = highest value
                  whose FN-rate on MEDIUM+ positives (val) <= --target-fn
        - validate: FN-rate on val positives, and optionally on an external
                  known-positive cohort via --recall-check-file (e.g. the 129
                  positives the old English-only prefilter blocked)

      The saved probe is a plain 6-output MLPProbe — byte-compatible with
      filters/common/embedding_stage.py, no shared-code change. Only the
      training objective and the selected `threshold` differ.

Usage:
    # balanced filter (unchanged)
    PYTHONPATH=. python scripts/train_probe.py \
        --filter filters/cultural-discovery/v4 \
        --data-dir datasets/training/cultural-discovery_v4 \
        --embedding-model intfloat/multilingual-e5-small

    # needle filter (nature_recovery v4)
    PYTHONPATH=. python scripts/train_probe.py \
        --filter filters/nature_recovery/v4 \
        --data-dir datasets/training/nature_recovery_v4 \
        --embedding-model intfloat/multilingual-e5-small \
        --objective recall --target-fn 0.02

The threshold-from-recall-curve and FN-rate helpers are pure functions
(no torch) and are unit-tested in tests/unit/test_train_probe.py.
"""

import argparse
import json
import logging
import pickle
from pathlib import Path

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Pure functions (no torch) — unit-tested in tests/unit/test_train_probe.py
# --------------------------------------------------------------------------- #

# nature_recovery v4 surfacing definition. Mirrors scripts/gate/agreement_gate.py
# and filters/nature_recovery/v4/config.yaml (single source of truth for the
# gatekeeper + weights). These constants describe the *target* (built from the
# oracle labels); the *screen* replicates EmbeddingStage (clamp, weighted sum,
# NO gatekeeper).
MEDIUM = 4.0
GATEKEEPER_MIN, GATEKEEPER_CAP = 3.0, 3.5
DIMENSION_NAMES = [
    "recovery_evidence", "measurable_outcomes", "ecological_significance",
    "restoration_scale", "human_agency", "protection_durability",
]
WEIGHTS = {
    "recovery_evidence": 0.25, "measurable_outcomes": 0.20,
    "ecological_significance": 0.20, "restoration_scale": 0.15,
    "human_agency": 0.10, "protection_durability": 0.10,
}


def gatekeepered_wa(scores):
    """Weighted average of oracle labels WITH the recovery_evidence gatekeeper.

    `scores` is a dict keyed by dimension name or a sequence aligned to
    DIMENSION_NAMES. Used to build the binary MEDIUM+ *target* — matches the
    surfacing signal in agreement_gate.py / base_scorer.
    """
    d = scores if isinstance(scores, dict) else dict(zip(DIMENSION_NAMES, scores))
    wa = sum(float(d[k]) * WEIGHTS[k] for k in DIMENSION_NAMES)
    if float(d["recovery_evidence"]) < GATEKEEPER_MIN and wa > GATEKEEPER_CAP:
        wa = GATEKEEPER_CAP
    return wa


def labels_to_binary(labels_seq):
    """Vector of {0.,1.} MEDIUM+ targets from a list of 6-dim label vectors."""
    return np.array(
        [1.0 if gatekeepered_wa(l) >= MEDIUM else 0.0 for l in labels_seq],
        dtype=np.float32,
    )


def screen_wa(pred6):
    """Replicate EmbeddingStage.screen_batch's weighted average EXACTLY.

    Clamp each predicted dimension to [0, 10] then take the weighted sum. NO
    gatekeeper is applied — hybrid_scorer.py:241 documents that the Stage-1
    screen deliberately skips it. This is the statistic the deployed threshold
    is compared against, so threshold selection must use this, not the
    gatekeepered target WA.
    """
    d = {name: max(0.0, min(10.0, float(pred6[j])))
         for j, name in enumerate(DIMENSION_NAMES)}
    return sum(d[k] * WEIGHTS[k] for k in DIMENSION_NAMES)


def screen_wa_batch(pred6_batch):
    """Vectorized screen_wa over an [N, 6] array -> [N] weighted averages."""
    arr = np.clip(np.asarray(pred6_batch, dtype=np.float64), 0.0, 10.0)
    w = np.array([WEIGHTS[n] for n in DIMENSION_NAMES], dtype=np.float64)
    return arr @ w


def fn_rate(pred_wa, y, threshold):
    """False-negative rate on MEDIUM+ positives at a screen `threshold`.

    A positive (y==1) is a false negative when its predicted screen WA falls
    BELOW threshold (it would be classified Stage-1-LOW and never reach Stage 2).
    Returns 0.0 when there are no positives.
    """
    pred_wa = np.asarray(pred_wa, dtype=np.float64)
    y = np.asarray(y)
    pos = y >= 0.5
    n = int(pos.sum())
    if n == 0:
        return 0.0
    fn = int(((pred_wa < threshold) & pos).sum())
    return fn / n


def stage2_rate(pred_wa, threshold):
    """Fraction of articles routed to Stage 2 (predicted WA >= threshold).

    Lower is cheaper (more screened out); recall constrains how high threshold
    can go. Complement is the Stage-1-LOW screen-out rate.
    """
    pred_wa = np.asarray(pred_wa, dtype=np.float64)
    if pred_wa.size == 0:
        return 0.0
    return float((pred_wa >= threshold).mean())


def recall_curve(pred_wa, y, thresholds):
    """FN-rate / recall / stage2-rate at each candidate threshold."""
    out = []
    for t in thresholds:
        f = fn_rate(pred_wa, y, t)
        out.append({
            "threshold": float(t),
            "fn_rate": f,
            "recall": 1.0 - f,
            "stage2_rate": stage2_rate(pred_wa, t),
        })
    return out


def select_threshold(pred_wa, y, target_fn, grid=None):
    """Highest screen threshold whose FN-rate on positives <= target_fn.

    FN-rate is monotonically non-decreasing in threshold, so the highest
    admissible threshold maximizes screening savings while keeping recall loss
    within budget. Returns (threshold, achieved_fn_rate, stage2_rate). Falls
    back to 0.0 (route everything to Stage 2 — always safe) if nothing qualifies,
    which cannot happen for target_fn >= 0 since fn_rate at 0.0 is 0.0.
    """
    if grid is None:
        grid = np.round(np.arange(0.0, 6.0001, 0.025), 4)
    best = 0.0
    for t in sorted(float(x) for x in grid):
        if fn_rate(pred_wa, y, t) <= target_fn:
            best = t
        else:
            break  # monotonic: once exceeded, stays exceeded
    return best, fn_rate(pred_wa, y, best), stage2_rate(pred_wa, best)


# --------------------------------------------------------------------------- #
# Torch training (gpu-server)
# --------------------------------------------------------------------------- #

def load_data(path):
    articles = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                articles.append(json.loads(line))
    return articles


def generate_embeddings(articles, model_name, device="cpu", batch_size=64):
    from sentence_transformers import SentenceTransformer

    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name, device=device)
    texts = [f"{a['title']}\n\n{a['content']}" for a in articles]
    logger.info(f"Encoding {len(texts)} articles...")
    return model.encode(texts, batch_size=batch_size, show_progress_bar=True,
                        convert_to_numpy=True)


def _build_probe(input_dim, output_dim, device):
    """Reuse the exact MLPProbe class EmbeddingStage reconstructs, so the saved
    state_dict loads without architecture drift."""
    from filters.common.embedding_stage import MLPProbe
    return MLPProbe(input_dim=input_dim, output_dim=output_dim).to(device)


def train_regression_probe(train_X, train_y, val_X, val_y, device="cpu",
                           epochs=100, patience=10, lr=0.001):
    """Historical L1 regression on the 6-dim labels (balanced filters)."""
    import torch
    import torch.nn as nn
    from sklearn.preprocessing import StandardScaler
    from torch.utils.data import DataLoader, TensorDataset

    scaler = StandardScaler().fit(train_X)
    Xtr, Xval = scaler.transform(train_X), scaler.transform(val_X)
    loader = DataLoader(
        TensorDataset(torch.FloatTensor(Xtr), torch.FloatTensor(train_y)),
        batch_size=64, shuffle=True)
    model = _build_probe(train_X.shape[1], train_y.shape[1], device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    crit = nn.L1Loss()
    Xval_t, yval_t = torch.FloatTensor(Xval).to(device), torch.FloatTensor(val_y).to(device)

    best_mae, best_state, wait = float("inf"), None, 0
    for epoch in range(epochs):
        model.train()
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            crit(model(xb), yb).backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            val_mae = torch.mean(torch.abs(model(Xval_t) - yval_t)).item()
        if val_mae < best_mae:
            best_mae, best_state, wait = val_mae, {k: v.cpu().clone() for k, v in model.state_dict().items()}, 0
        else:
            wait += 1
        if wait >= patience:
            logger.info(f"Early stopping at epoch {epoch + 1}")
            break
        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch + 1}: Val MAE = {val_mae:.4f}")
    model.load_state_dict(best_state)
    logger.info(f"Best Val MAE: {best_mae:.4f}")
    return model, scaler, {"val_mae": best_mae}


def train_recall_probe(train_X, train_labels6, val_X, val_labels6, device="cpu",
                       epochs=150, patience=15, lr=0.001, wa_scale=2.0,
                       aux_l1_weight=0.1):
    """Recall-first: train the probe's weighted average as a MEDIUM+ classifier.

    Primary loss: class-weighted BCE on sigmoid(wa_scale*(wa_pred - MEDIUM)),
    where wa_pred is the (unclamped, training-time) weighted sum of the 6 probe
    outputs. Auxiliary: light L1 on the 6-dim labels to keep per-dim outputs in
    a sane 0-10 range (they are surfaced as `scores` for Stage-1-LOW articles).
    Checkpoint selected on min val BCE (a proper scoring rule for the boundary).
    """
    import torch
    import torch.nn as nn
    from sklearn.preprocessing import StandardScaler
    from torch.utils.data import DataLoader, TensorDataset

    scaler = StandardScaler().fit(train_X)
    Xtr, Xval = scaler.transform(train_X), scaler.transform(val_X)
    ytr, yval = labels_to_binary(train_labels6), labels_to_binary(val_labels6)
    n_pos = float(ytr.sum())
    n_neg = float(len(ytr) - n_pos)
    pos_weight = torch.tensor([n_neg / max(n_pos, 1.0)], dtype=torch.float32).to(device)
    logger.info(f"Recall objective: {int(n_pos)} positives / {len(ytr)} "
                f"({100 * n_pos / len(ytr):.1f}%), pos_weight={pos_weight.item():.2f}")

    loader = DataLoader(
        TensorDataset(torch.FloatTensor(Xtr),
                      torch.FloatTensor(train_labels6),
                      torch.FloatTensor(ytr)),
        batch_size=64, shuffle=True)
    model = _build_probe(train_X.shape[1], train_labels6.shape[1], device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    bce = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    l1 = nn.L1Loss()
    wvec = torch.tensor([WEIGHTS[n] for n in DIMENSION_NAMES], dtype=torch.float32).to(device)

    Xval_t = torch.FloatTensor(Xval).to(device)
    yval_t = torch.FloatTensor(yval).to(device)
    val_labels_t = torch.FloatTensor(val_labels6).to(device)

    best_bce, best_state, wait = float("inf"), None, 0
    for epoch in range(epochs):
        model.train()
        for xb, lb, yb in loader:
            xb, lb, yb = xb.to(device), lb.to(device), yb.to(device)
            opt.zero_grad()
            out = model(xb)                          # [B, 6]
            wa_pred = (out * wvec).sum(dim=1)        # [B]
            logit = wa_scale * (wa_pred - MEDIUM)
            loss = bce(logit, yb) + aux_l1_weight * l1(out, lb)
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            out = model(Xval_t)
            wa_pred = (out * wvec).sum(dim=1)
            val_bce = bce(wa_scale * (wa_pred - MEDIUM), yval_t).item()
        if val_bce < best_bce:
            best_bce, best_state, wait = val_bce, {k: v.cpu().clone() for k, v in model.state_dict().items()}, 0
        else:
            wait += 1
        if wait >= patience:
            logger.info(f"Early stopping at epoch {epoch + 1}")
            break
        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch + 1}: Val BCE = {val_bce:.4f}")
    model.load_state_dict(best_state)
    logger.info(f"Best Val BCE: {best_bce:.4f}")
    return model, scaler, {"val_bce": best_bce}


def _predict_screen_wa(model, scaler, X, device):
    """Predicted screen WA (clamp+weighted-sum, matching EmbeddingStage) for X."""
    import torch
    model.eval()
    with torch.no_grad():
        pred6 = model(torch.FloatTensor(scaler.transform(X)).to(device)).cpu().numpy()
    return screen_wa_batch(pred6)


def main():
    parser = argparse.ArgumentParser(description="Train e5-small MLP probe for hybrid inference")
    parser.add_argument("--filter", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--embedding-model", type=str, default="intfloat/multilingual-e5-small")
    parser.add_argument("--objective", choices=["regression", "recall"], default="regression",
                        help="recall = needle-in-haystack screen (nature_recovery v4); "
                             "regression = historical L1 (balanced filters)")
    parser.add_argument("--target-fn", type=float, default=0.02,
                        help="[recall] max FN-rate on MEDIUM+ positives when selecting the threshold")
    parser.add_argument("--wa-scale", type=float, default=2.0, help="[recall] sigmoid sharpness around MEDIUM")
    parser.add_argument("--aux-l1-weight", type=float, default=0.1, help="[recall] auxiliary per-dim L1 weight")
    parser.add_argument("--recall-check-file", type=Path, default=None,
                        help="[recall] JSONL of known positives to report FN-rate on (e.g. the 129)")
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    import torch
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Device: {device}")

    train_articles = load_data(args.data_dir / "train.jsonl")
    val_articles = load_data(args.data_dir / "val.jsonl")
    logger.info(f"Train: {len(train_articles)}, Val: {len(val_articles)}")

    all_articles = train_articles + val_articles
    embeddings = generate_embeddings(all_articles, args.embedding_model, device=device)
    train_emb = embeddings[: len(train_articles)]
    val_emb = embeddings[len(train_articles):]
    logger.info(f"Embedding dim: {embeddings.shape[1]}")

    train_labels = np.array([a["labels"] for a in train_articles], dtype=np.float32)
    val_labels = np.array([a["labels"] for a in val_articles], dtype=np.float32)

    # imbalance guard: warn if someone runs regression on a needle corpus
    pos_frac = float(labels_to_binary(train_labels).mean())
    if args.objective == "regression" and pos_frac < 0.25:
        logger.warning(
            f"Only {100 * pos_frac:.1f}% MEDIUM+ positives — this looks like a needle "
            f"filter. Regression will likely collapse to a floor predictor and drop "
            f"positives at Stage 1. Use --objective recall (see this file's header).")

    metrics = {}
    if args.objective == "recall":
        model, scaler, tm = train_recall_probe(
            train_emb, train_labels, val_emb, val_labels, device=device,
            wa_scale=args.wa_scale, aux_l1_weight=args.aux_l1_weight)
        metrics.update(tm)

        # Threshold from the val recall curve, using the EXACT deployed screen WA.
        val_pred_wa = _predict_screen_wa(model, scaler, val_emb, device)
        y_val = labels_to_binary(val_labels)
        thr, achieved_fn, s2 = select_threshold(val_pred_wa, y_val, args.target_fn)
        metrics.update({
            "objective": "recall", "selected_threshold": thr, "target_fn": args.target_fn,
            "val_fn_rate": achieved_fn, "val_recall_medium": 1.0 - achieved_fn,
            "val_stage2_rate": s2, "val_positives": int(y_val.sum()),
            "wa_scale": args.wa_scale, "aux_l1_weight": args.aux_l1_weight,
        })

        # Print the curve so the threshold choice is auditable.
        logger.info("Val recall curve (threshold -> FN-rate / recall / stage2-rate):")
        for row in recall_curve(val_pred_wa, y_val, np.round(np.arange(0.0, 3.5001, 0.25), 3)):
            logger.info(f"    t={row['threshold']:.2f}  FN={row['fn_rate']:.3f}  "
                        f"recall={row['recall']:.3f}  stage2={row['stage2_rate']:.3f}")
        logger.info("=" * 64)
        logger.info(f"SELECTED threshold = {thr:.3f}  (val FN={achieved_fn:.3f}, "
                    f"recall={1 - achieved_fn:.3f}, stage2-rate={s2:.3f})")
        logger.info(f"  -> set filters/.../config.yaml hybrid_inference.stage1.threshold: {thr:.3f}")

        # Optional: FN-rate on an external known-positive cohort (e.g. the 129).
        if args.recall_check_file and args.recall_check_file.exists():
            cohort = load_data(args.recall_check_file)
            cohort_emb = generate_embeddings(cohort, args.embedding_model, device=device)
            cohort_wa = _predict_screen_wa(model, scaler, cohort_emb, device)
            below = int((cohort_wa < thr).sum())
            logger.info(f"Recall-check cohort ({args.recall_check_file.name}): "
                        f"{len(cohort)} known positives, {below} below threshold "
                        f"(FN={below / max(len(cohort), 1):.3f}) "
                        f"[NOTE: may overlap train — a guard, not a clean test]")
            metrics["recall_check_fn"] = below / max(len(cohort), 1)
            metrics["recall_check_n"] = len(cohort)
    else:
        model, scaler, tm = train_regression_probe(
            train_emb, train_labels, val_emb, val_labels, device=device)
        metrics.update(tm)
        metrics["objective"] = "regression"

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
        "metrics": metrics,
    }
    with open(output_path, "wb") as f:
        pickle.dump(probe_data, f)
    logger.info(f"Probe saved to {output_path}")
    logger.info(f"Metrics: {json.dumps(metrics, indent=2)}")


if __name__ == "__main__":
    main()
