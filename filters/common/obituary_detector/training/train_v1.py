#!/usr/bin/env python3
"""
Obituary detector v1 — trainer + calibration report (NM#185 / llm-distillery#51).

Mirrors commerce_prefilter v2: frozen multilingual embedder
(paraphrase-multilingual-mpnet-base-v2) -> StandardScaler -> sklearn MLPClassifier
-> predict_proba. Produces the SAME artifact contract (mlp_classifier.pkl +
scaler.pkl) so v2's inference.py pattern can be reused verbatim.

Methodology (thin corpus, ~777 rows): 5-fold stratified CV collects one honest
out-of-fold probability per article; the precision/recall/threshold table and the
per-lens false-positive analysis are computed on those OOF predictions (far more
stable than a single ~155-row test split). The saved artifact is then refit on
ALL data.

NOT a deployment step: writes model + report only. No NexusMind wiring, no
enforcement. Threshold/enforce decision is the owner's, on the calibration table.

Usage (on gpu-server):
    python3 train_obituary_v1.py \
        --seed obituary-seed-bootstrap.jsonl \
        --out-dir ~/llm-distillery/filters/common/obituary_detector/v1/models \
        --report-dir ~/llm-distillery/filters/common/obituary_detector
"""
import argparse, json, sys
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import f1_score, precision_score, recall_score, confusion_matrix

SEED = 42
EMBEDDER = "paraphrase-multilingual-mpnet-base-v2"
HIDDEN = (256, 128)

ap = argparse.ArgumentParser()
ap.add_argument("--seed", required=True, help="corpus jsonl")
ap.add_argument("--out-dir", required=True, help="model artifact dir")
ap.add_argument("--report-dir", required=True, help="dir for calibration report")
ap.add_argument("--device", default="cuda")
args = ap.parse_args()

out_dir = Path(args.out_dir).expanduser()
report_dir = Path(args.report_dir).expanduser()
out_dir.mkdir(parents=True, exist_ok=True)
report_dir.mkdir(parents=True, exist_ok=True)

# ---- load corpus -----------------------------------------------------------
rows = [json.loads(l) for l in open(args.seed, encoding="utf-8") if l.strip()]
texts, y, lenses = [], [], []
for r in rows:
    title = r.get("title") or ""
    content = r.get("content_start") or r.get("content") or ""
    texts.append(f"{title} {content}".strip())
    y.append(1 if r.get("label") == "positive" else 0)
    lenses.append(r.get("filter") or "unknown")
y = np.array(y)
lenses = np.array(lenses)
print(f"loaded {len(texts)} rows | positives={int(y.sum())} negatives={int((1-y).sum())}")

# ---- embed once ------------------------------------------------------------
from sentence_transformers import SentenceTransformer
print(f"embedding with {EMBEDDER} on {args.device} ...")
embedder = SentenceTransformer(EMBEDDER, device=args.device)
X = embedder.encode(texts, show_progress_bar=True, batch_size=64)
X = np.asarray(X)
print(f"embeddings: {X.shape}")

def make_mlp():
    return MLPClassifier(hidden_layer_sizes=HIDDEN, max_iter=400,
                         early_stopping=True, n_iter_no_change=15,
                         random_state=SEED)

# ---- 5-fold OOF probabilities ---------------------------------------------
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
oof = np.zeros(len(y), dtype=float)
for fold, (tr, te) in enumerate(skf.split(X, y)):
    sc = StandardScaler().fit(X[tr])
    clf = make_mlp().fit(sc.transform(X[tr]), y[tr])
    oof[te] = clf.predict_proba(sc.transform(X[te]))[:, 1]
    print(f"  fold {fold}: train={len(tr)} test={len(te)}")

# ---- threshold sweep on OOF ------------------------------------------------
def at(th):
    pred = (oof >= th).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    return dict(threshold=th, precision=round(prec, 4), recall=round(rec, 4),
                tp=tp, fp=fp, fn=fn, tn=tn)

sweep = [at(t) for t in [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.92, 0.95, 0.97, 0.99]]

# ---- per-lens FP analysis (over-block risk) --------------------------------
# Among TRUE-NEGATIVE articles, how many each lens loses (false positive) at th.
neg_mask = y == 0
per_lens = {}
for th in [0.8, 0.9, 0.95, 0.97]:
    flagged = (oof >= th) & neg_mask
    d = {}
    for lens in sorted(set(lenses[neg_mask])):
        lm = neg_mask & (lenses == lens)
        d[lens] = dict(neg_total=int(lm.sum()), false_positives=int((flagged & (lenses == lens)).sum()))
    per_lens[str(th)] = d

# ---- final artifact: refit on ALL data ------------------------------------
scaler = StandardScaler().fit(X)
final = make_mlp().fit(scaler.transform(X), y)

import pickle
with open(out_dir / "mlp_classifier.pkl", "wb") as f:
    pickle.dump(final, f)
with open(out_dir / "scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

# headline metrics at the commerce-default 0.95 for orientation
m95 = at(0.95)
training_config = {
    "embedder_model": EMBEDDER,
    "embedding_dim": int(X.shape[1]),
    "classifier_type": "MLPClassifier",
    "hidden_layers": list(HIDDEN),
    "n_samples": len(y),
    "n_positive": int(y.sum()),
    "n_negative": int((1 - y).sum()),
    "cv": "5-fold stratified OOF",
    "oof_f1_at_0.95": round(f1_score(y, (oof >= 0.95).astype(int)), 4),
    "oof_precision_at_0.95": m95["precision"],
    "oof_recall_at_0.95": m95["recall"],
    "note": "AUDIT-ONLY baseline. Do not enforce before threshold sign-off.",
}
with open(out_dir / "training_config.json", "w") as f:
    json.dump(training_config, f, indent=2)

report = {"threshold_sweep": sweep, "per_lens_false_positives": per_lens,
          "training_config": training_config}
with open(report_dir / "calibration_report.json", "w") as f:
    json.dump(report, f, indent=2)

# ---- console summary -------------------------------------------------------
print("\n=== threshold sweep (5-fold OOF) ===")
print(f"{'thresh':>7} {'prec':>7} {'recall':>7} {'tp':>4} {'fp':>4} {'fn':>4} {'tn':>4}")
for s in sweep:
    print(f"{s['threshold']:>7} {s['precision']:>7} {s['recall']:>7} {s['tp']:>4} {s['fp']:>4} {s['fn']:>4} {s['tn']:>4}")
print("\n=== per-lens false positives among true negatives ===")
for th, d in per_lens.items():
    print(f"-- threshold {th} --")
    for lens, v in d.items():
        print(f"   {lens:<26} {v['false_positives']:>3} / {v['neg_total']:>3} negatives flagged")
print(f"\nartifacts -> {out_dir}")
print(f"report    -> {report_dir / 'calibration_report.json'}")
