#!/usr/bin/env python3
"""Obituary v5 evaluation — three-way heldout comparison + June holdout + spot checks.

Run on gpu-server from ~/llm-distillery/filters/common/obituary_detector/.
Writes validation/v5_eval_2026-07-30.json.
"""
import json, pickle
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

BASE = Path.home() / "llm-distillery/filters/common/obituary_detector"
EMBEDDER = "paraphrase-multilingual-mpnet-base-v2"

def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]

def text_of(r):
    return f"{r.get('title') or ''} {r.get('content_start') or r.get('content') or ''}".strip()

def load_model(ver):
    with open(BASE / ver / "models/mlp_classifier.pkl", "rb") as f:
        clf = pickle.load(f)
    with open(BASE / ver / "models/scaler.pkl", "rb") as f:
        sc = pickle.load(f)
    return clf, sc

def score(clf, sc, X):
    return clf.predict_proba(sc.transform(X))[:, 1]

def metrics(y, s, th):
    pred = (s >= th).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum()); fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum()); tn = int(((pred == 0) & (y == 0)).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    return dict(threshold=th, precision=round(prec, 4), recall=round(rec, 4), tp=tp, fp=fp, fn=fn, tn=tn)

emb = SentenceTransformer(EMBEDDER, device="cuda")
v3 = load_model("v3"); v4 = load_model("v4"); v5 = load_model("v5")

graded = json.load(open(BASE / "validation/graded_ids_2026-07-30.json"))
exclude = set(graded["fn_delta_ids"]) | set(graded["fp5_ids"])
hard_pos = graded["hard_positive_ids"]

out = {}

# ---- in-corpus heldout: join with pre-scored v3/v4, add v5 ----
held = load_jsonl(BASE / "validation/heldout_v3v4_scored_2026-07-30.jsonl")
Xh = np.asarray(emb.encode([text_of(r) for r in held], batch_size=64, show_progress_bar=False))
s5 = score(*v5, Xh)
for r, s in zip(held, s5):
    r["v5_score"] = float(s)
kept = [r for r in held if r["id"] not in exclude]
y = np.array([1 if r["label"] == "positive" else 0 for r in kept])
a3 = np.array([r["v3_score"] for r in kept]); a4 = np.array([r["v4_score"] for r in kept])
a5 = np.array([r["v5_score"] for r in kept])
out["heldout_excl33"] = {
    "n": len(kept), "n_excluded": len(held) - len(kept),
    "v3": [metrics(y, a3, t) for t in (0.90, 0.95)],
    "v4": [metrics(y, a4, t) for t in (0.90, 0.95)],
    "v5": [metrics(y, a5, t) for t in (0.80, 0.85, 0.90, 0.92, 0.95)],
}
# same rows, nothing excluded — for continuity with the morning numbers
yA = np.array([1 if r["label"] == "positive" else 0 for r in held])
out["heldout_full_v5"] = [metrics(yA, np.array([r["v5_score"] for r in held]), t) for t in (0.90, 0.95)]
with open(BASE / "validation/heldout_v3v4v5_scored_2026-07-30.jsonl", "w") as f:
    for r in held:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# ---- June holdout (temporally disjoint, UNLABELED — flag counts + panel-grade overlap) ----
june = load_jsonl(BASE / "training/data/june_heldout_corpus.jsonl")
Xj = np.asarray(emb.encode([text_of(r) for r in june], batch_size=64, show_progress_bar=False))
j5 = score(*v5, Xj); j4 = score(*v4, Xj); j3 = score(*v3, Xj)
grades = {}
gp = BASE / "validation/artifacts/grades_panel_v4_band_2026-07-30.jsonl"
if gp.exists():
    for r in load_jsonl(gp):
        grades[r["id"]] = r.get("majority") or r.get("panel_majority")
flag_counts = {
    "n": len(june),
    "v3@0.95": int((j3 >= 0.95).sum()),
    "v4@0.90": int((j4 >= 0.90).sum()),
    "v5": {str(t): int((j5 >= t).sum()) for t in (0.85, 0.90, 0.92, 0.95)},
}
# v5-newly-flagged vs v4@0.90, with panel grade where known
new5 = [i for i in range(len(june)) if j5[i] >= 0.90 and j4[i] < 0.90]
lost5 = [i for i in range(len(june)) if j5[i] < 0.90 and j4[i] >= 0.90]
def brief(idx):
    return [{"id": june[i]["id"], "title": (june[i].get("title") or "")[:70],
             "v3": round(float(j3[i]), 3), "v4": round(float(j4[i]), 3), "v5": round(float(j5[i]), 3),
             "panel": grades.get(june[i]["id"])} for i in idx]
out["june_holdout"] = {"flag_counts": flag_counts,
                       "v5_new_vs_v4@0.90": brief(new5),
                       "v5_lost_vs_v4@0.90": brief(lost5)}

# ---- the 21 hard positives (now in training — fit check, not generalization) ----
hp_rows = [r for r in held if r["id"] in set(hard_pos)]
out["hard_positives_21"] = {
    "n": len(hp_rows),
    "v5_ge_090": sum(1 for r in hp_rows if r["v5_score"] >= 0.90),
    "v5_ge_095": sum(1 for r in hp_rows if r["v5_score"] >= 0.95),
    "scores": {r["id"]: {"v3": r["v3_score"], "v4": r["v4_score"], "v5": round(r["v5_score"], 4)} for r in hp_rows},
}

# ---- the 13 rows v4 added (12 hard negatives + 1 positive) — regression check ----
v3_ids = {r["id"] for r in load_jsonl(BASE / "training/data/train_split_corpus.jsonl")}
v4rows = load_jsonl(BASE / "training/data/v4b_train_seed.jsonl")
added = [r for r in v4rows if r["id"] not in v3_ids]
Xa = np.asarray(emb.encode([text_of(r) for r in added], batch_size=64, show_progress_bar=False))
a5s = score(*v5, Xa); a4s = score(*v4, Xa)
out["v4_added_rows"] = [
    {"id": r["id"], "label": r["label"], "title": (r.get("title") or "")[:70],
     "v4": round(float(s4), 4), "v5": round(float(s5_), 4)}
    for r, s4, s5_ in zip(added, a4s, a5s)
]

# ---- Farouq flagged article ----
fa = load_jsonl(BASE / "validation/worksheet_ovrnews_flagged_2026-07-29_farouq.jsonl")
Xf = np.asarray(emb.encode([text_of(r) for r in fa], batch_size=8, show_progress_bar=False))
f5 = score(*v5, Xf); f4 = score(*v4, Xf); f3 = score(*v3, Xf)
out["farouq"] = [
    {"id": r.get("id"), "v3": round(float(a), 4), "v4": round(float(b), 4), "v5": round(float(c), 4)}
    for r, a, b, c in zip(fa, f3, f4, f5)
]

with open(BASE / "validation/v5_eval_2026-07-30.json", "w") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in out.items() if k != "v4_added_rows"}, indent=1)[:4000])
print("v4_added_rows:")
for r in out["v4_added_rows"]:
    print(f"  {r['label']:<9} v4={r['v4']:<7} v5={r['v5']:<7} {r['title']}")
