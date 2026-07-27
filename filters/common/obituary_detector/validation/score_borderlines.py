#!/usr/bin/env python3
"""Score the ovr.news borderlines with the v3 obituary detector MLP."""
import json, pickle, sys
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

EMBEDDER = "paraphrase-multilingual-mpnet-base-v2"
MODEL_DIR = Path("~/llm-distillery/filters/common/obituary_detector/v3/models").expanduser()
WORKSHEET = sys.argv[1] if len(sys.argv) > 1 else "worksheet_obit.jsonl"
OUT = sys.argv[2] if len(sys.argv) > 2 else "worksheet_scored.jsonl"

rows = [json.loads(l) for l in open(WORKSHEET, encoding="utf-8") if l.strip()]
print(f"loading {len(rows)} articles...")

emb = SentenceTransformer(EMBEDDER, device="cuda")
scaler = pickle.load(open(MODEL_DIR / "scaler.pkl", "rb"))
clf = pickle.load(open(MODEL_DIR / "mlp_classifier.pkl", "rb"))

texts = [f"{r.get('title') or ''} {r.get('content') or ''}".strip() for r in rows]
X = emb.encode(texts, show_progress_bar=True, batch_size=64)
scores = clf.predict_proba(scaler.transform(np.asarray(X)))[:, 1]

for r, s in zip(rows, scores):
    r["obit_score"] = round(float(s), 6)

with open(OUT, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# Summary
scores_arr = np.array(scores)
print(f"\nscored {len(rows)} articles")
print(f"score range: {scores_arr.min():.4f} - {scores_arr.max():.4f}")
for th in [0.90, 0.95, 0.97, 0.99]:
    n = int((scores_arr >= th).sum())
    print(f"  >= {th}: {n}/{len(rows)} ({100*n/len(rows):.1f}%)")
print(f"-> {OUT}")
