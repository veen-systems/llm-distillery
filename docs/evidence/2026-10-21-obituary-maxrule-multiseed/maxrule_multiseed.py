#!/usr/bin/env python3
"""#159 / H-DET5: EXP-035's title-max rules re-measured over SEED_SET with v5's head retrained per seed
(EXP-034's protocol). Runs on b650 (paths under ~/llm-distillery). Writes ~/maxrule_multiseed.json."""
import json
from pathlib import Path
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sentence_transformers import SentenceTransformer

SEEDS = (42, 7, 13, 101, 2026)          # filters/common/detector_seeds.py SEED_SET
OP, GATE, HIDDEN, WINDOW = 0.85, 0.99, (256, 128), 128
OBIT = Path.home() / "llm-distillery/filters/common/obituary_detector"
CORPORA = ["train_split_corpus.jsonl", "v4b_train_seed.jsonl", "v5_train_seed.jsonl"]   # EXP-034's leak set
rows = lambda p: [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
text_of = lambda r: f"{r.get('title') or ''} {r.get('content') or ''}".strip()

m = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2", device="cuda"); m.max_seq_length = WINDOW
enc = lambda t: np.asarray(m.encode(t, batch_size=64, show_progress_bar=False))
train = rows(OBIT / "training/data" / "v5_train_seed.jsonl")
leak = set().union(*[{r["id"] for r in rows(OBIT / "training/data" / c)} for c in CORPORA])
ho = rows(OBIT / "validation/heldout_v3v4v5_scored_2026-07-30.jsonl")
ev = [r for r in ho if r["id"] not in leak]
y = np.array([r["label"] == "positive" for r in ev])
Xt, yt = enc([text_of(r) for r in train]), np.array([r["label"] == "positive" for r in train]).astype(int)
Xf, Xh = enc([text_of(r) for r in ev]), enc([(r.get("title") or "").strip() for r in ev])
Xho = enc([text_of(r) for r in ho])

def met(p):
    pred = p >= OP
    tp, fp = int((pred & y).sum()), int((pred & ~y).sum())
    fn, tn = int((~pred & y).sum()), int((~pred & ~y).sum())
    return {"recall": tp / (tp + fn), "specificity": tn / (tn + fp), "fp": fp, "tp": tp}

out = {"eval_n": len(ev), "leaked_dropped": len(ho) - len(ev), "positives": int(y.sum()), "seeds": SEEDS, "per_seed": {}}
for s in SEEDS:
    sc = StandardScaler().fit(Xt)
    clf = MLPClassifier(hidden_layer_sizes=HIDDEN, max_iter=400, early_stopping=True, n_iter_no_change=15,
                        random_state=s).fit(sc.transform(Xt), yt)
    pf, pt = clf.predict_proba(sc.transform(Xf))[:, 1], clf.predict_proba(sc.transform(Xh))[:, 1]
    rules = {"full": pf, "max_title_full": np.maximum(pt, pf), "max_title099_full": np.maximum(np.where(pt >= GATE, pt, 0), pf)}
    out["per_seed"][s] = {k: met(v) for k, v in rules.items()}
    if s == 42:
        shipped = np.array([r["v5_score"] for r in ho]); p42 = clf.predict_proba(sc.transform(Xho))[:, 1]
        out["control_seed42_vs_shipped"] = {"corr": float(np.corrcoef(p42, shipped)[0, 1]),
                                            "flips_at_0.85": int(((p42 >= OP) != (shipped >= OP)).sum()), "n": len(ho)}
    print(s, {k: (round(v["recall"], 4), round(v["specificity"], 4), v["fp"]) for k, v in out["per_seed"][s].items()}, flush=True)
json.dump(out, open(Path.home() / "maxrule_multiseed.json", "w"), indent=1)
print("DONE", flush=True)
