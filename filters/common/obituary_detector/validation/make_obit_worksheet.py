#!/usr/bin/env python3
"""
Build the obituary held-out grading worksheet (NM#185 validation).

Scores UNSEEN warm-DB articles (excludes the training seed ids) with the
obituary_detector v1 model, then samples a decision-relevant worksheet:

  - block      : obit_score >= 0.90  (would be dropped if enforced) -> block precision
  - boundary   : 0.70 <= score < 0.90                               -> contested middle
  - recall_chk : score < 0.70 AND death-adjacent text               -> false-negative check

belonging is oversampled in the block bucket (the over-block-risk lens).
Worksheet stores obit_score + gate label for the ROLL-UP, but the panel harness
shows panelists only title+content (blind).
"""
import argparse, json, re, random
from pathlib import Path
import numpy as np

SEED = 42
random.seed(SEED)
EMBEDDER = "paraphrase-multilingual-mpnet-base-v2"
DEATH_RE = re.compile(
    r"obituar|died|death|passed away|funeral|memorial|remembrance|laid to rest|"
    r"dies at|in memoriam|overled|gestorven|verstorben|fallec|décès|obsèques",
    re.IGNORECASE,
)

ap = argparse.ArgumentParser()
ap.add_argument("--candidates", required=True)
ap.add_argument("--seed-corpus", required=True, help="training seed jsonl (ids to exclude)")
ap.add_argument("--model-dir", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--n-block", type=int, default=22)
ap.add_argument("--n-boundary", type=int, default=10)
ap.add_argument("--n-recall", type=int, default=10)
ap.add_argument("--device", default="cuda")
args = ap.parse_args()

train_ids = {json.loads(l)["id"] for l in open(args.seed_corpus, encoding="utf-8") if l.strip()}
cands = [json.loads(l) for l in open(args.candidates, encoding="utf-8") if l.strip()]
cands = [c for c in cands if c["id"] not in train_ids]
print(f"unseen candidates: {len(cands)} (excluded {len(train_ids)} training ids)")

# ---- score ----
import pickle
from sentence_transformers import SentenceTransformer
emb = SentenceTransformer(EMBEDDER, device=args.device)
texts = [f"{c.get('title') or ''} {c.get('content') or ''}".strip() for c in cands]
X = emb.encode(texts, show_progress_bar=True, batch_size=64)
mdir = Path(args.model_dir)
scaler = pickle.load(open(mdir / "scaler.pkl", "rb"))
clf = pickle.load(open(mdir / "mlp_classifier.pkl", "rb"))
scores = clf.predict_proba(scaler.transform(np.asarray(X)))[:, 1]
for c, s in zip(cands, scores):
    c["obit_score"] = float(s)

def death_adjacent(c):
    t = f"{c.get('title','')} {c.get('content','')}".lower()
    return bool(DEATH_RE.search(t))

block = [c for c in cands if c["obit_score"] >= 0.90]
boundary = [c for c in cands if 0.70 <= c["obit_score"] < 0.90]
recall_chk = [c for c in cands if c["obit_score"] < 0.70 and death_adjacent(c)]
print(f"pool sizes -> block={len(block)} boundary={len(boundary)} recall_chk={len(recall_chk)}")

def sample_block(pool, n):
    # oversample belonging: take all belonging up to n//2, fill rest random
    bel = [c for c in pool if c.get("filter") == "belonging"]
    rest = [c for c in pool if c.get("filter") != "belonging"]
    random.shuffle(bel); random.shuffle(rest)
    pick = bel[: max(1, n // 2)] + rest
    random.shuffle(pick)
    return pick[:n]

def samp(pool, n):
    random.shuffle(pool)
    return pool[:n]

ws = []
for c in sample_block(block, args.n_block): c["bucket"] = "block"; ws.append(c)
for c in samp(boundary, args.n_boundary): c["bucket"] = "boundary"; ws.append(c)
for c in samp(recall_chk, args.n_recall): c["bucket"] = "recall_chk"; ws.append(c)

# stable order, dedup by id
seen = set(); final = []
for c in ws:
    if c["id"] in seen: continue
    seen.add(c["id"]); final.append(c)

with open(args.out, "w", encoding="utf-8") as f:
    for c in final:
        f.write(json.dumps({
            "id": c["id"], "title": c.get("title"), "content": c.get("content"),
            "filter": c.get("filter"), "published_date": c.get("published_date"),
            "gate_decision": c.get("gate_decision"), "gate_reason": c.get("gate_reason"),
            "obit_score": round(c["obit_score"], 4), "bucket": c["bucket"],
        }, ensure_ascii=False) + "\n")

from collections import Counter
print(f"\nworksheet rows: {len(final)} -> {args.out}")
print("by bucket:", dict(Counter(c['bucket'] for c in final)))
print("by lens:  ", dict(Counter(c.get('filter') for c in final)))
