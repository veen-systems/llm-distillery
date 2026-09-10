#!/usr/bin/env python3
"""Is the obituary v3 -> v4 -> v5 recall ORDERING real, or a single-seed artifact?

Each shipped version is retrained from ITS OWN corpus across five seeds, everything
else held fixed, and evaluated at the LIVE threshold 0.85 (plus 0.90/0.95).

Corpus identification (counts match the shipped training_config.json exactly):
    v3 = train_split_corpus.jsonl  n=11295 pos=2672 neg=8623
    v4 = v4b_train_seed.jsonl      n=11308 pos=2673 neg=8635   <- NOT v4_train_seed.jsonl (n=11304)
    v5 = v5_train_seed.jsonl       n=11329 pos=2694 neg=8635

Leakage: v4 and v5 were corrected using rows drawn FROM the heldout split, which is why
the published v5 figure quotes n=1529 rather than 1562. The evaluation set here is computed,
not hand-listed: every heldout row that appears in ANY version's training corpus is dropped,
so all three versions are judged on rows none of them ever saw.
"""
import json, pickle, time
from pathlib import Path
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sentence_transformers import SentenceTransformer

EMBEDDER = "paraphrase-multilingual-mpnet-base-v2"
HIDDEN, SEEDS, WINDOW = (256, 128), [42, 7, 13, 101, 2026], 128
THRESHOLDS = [0.85, 0.90, 0.95]
OBIT = Path.home() / "llm-distillery/filters/common/obituary_detector"
CORPUS = {"v3": "train_split_corpus.jsonl", "v4": "v4b_train_seed.jsonl", "v5": "v5_train_seed.jsonl"}
CACHE = Path.home() / "multiseed_cache"; CACHE.mkdir(exist_ok=True)
OUT = Path.home() / "multiseed_results.json"

def rows(p): return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
def text_of(r): return f"{r.get('title') or ''} {r.get('content') or ''}".strip()
def mlp(seed): return MLPClassifier(hidden_layer_sizes=HIDDEN, max_iter=400,
                                    early_stopping=True, n_iter_no_change=15, random_state=seed)

model = SentenceTransformer(EMBEDDER, device="cuda"); model.max_seq_length = WINDOW
def embed(texts, tag):
    f = CACHE / f"{tag}_{WINDOW}.npy"
    if f.exists(): return np.load(f)
    X = np.asarray(model.encode(texts, batch_size=64, show_progress_bar=False)); np.save(f, X); return X

ho = rows(OBIT / "validation/heldout_v3v4v5_scored_2026-07-30.jsonl")
train = {v: rows(OBIT / "training/data" / f) for v, f in CORPUS.items()}
for v, rs in train.items():
    print(f"  {v}: corpus n={len(rs)} pos={sum(1 for r in rs if r['label']=='positive')}", flush=True)

train_ids = set().union(*[{r["id"] for r in rs} for rs in train.values()])
clean = [r for r in ho if r["id"] not in train_ids]
leaked = len(ho) - len(clean)
print(f"\n  heldout {len(ho)} -> dropped {leaked} rows that appear in some version's training "
      f"corpus -> EVAL SET n={len(clean)}", flush=True)
print(f"  (published v5 figure uses n=1529; {len(ho)}-{leaked}={len(clean)})", flush=True)

ho_X_full = embed([text_of(r) for r in ho], "heldout")
clean_idx = np.array([i for i, r in enumerate(ho) if r["id"] not in train_ids])
X_eval = ho_X_full[clean_idx]
y_eval = np.array([1 if ho[i]["label"] == "positive" else 0 for i in clean_idx])
print(f"  eval positives={int(y_eval.sum())} negatives={int((1-y_eval).sum())} "
      f"({100*y_eval.mean():.1f}% positive rate)", flush=True)

def metrics(y, p, th):
    pred = (p >= th).astype(int)
    tp = int(((pred==1)&(y==1)).sum()); fp = int(((pred==1)&(y==0)).sum())
    fn = int(((pred==0)&(y==1)).sum()); tn = int(((pred==0)&(y==0)).sum())
    return dict(recall=tp/(tp+fn) if tp+fn else 0.0, specificity=tn/(tn+fp) if tn+fp else 0.0,
                precision=tp/(tp+fp) if tp+fp else 0.0, tp=tp, fp=fp, fn=fn, tn=tn)

res = {"eval_n": len(clean), "leaked_dropped": leaked, "seeds": SEEDS, "window": WINDOW,
       "eval_positive_rate": float(y_eval.mean()), "corpus_map": CORPUS, "versions": {}}

for v in ("v3", "v4", "v5"):
    print(f"\n=== {v} (corpus {CORPUS[v]}) ===", flush=True)
    rs = train[v]
    Xt = embed([text_of(r) for r in rs], f"train_{v}")
    yt = np.array([1 if r["label"] == "positive" else 0 for r in rs])
    # POSITIVE CONTROL: refit at the shipped seed, compare to the shipped model's scores
    sc = StandardScaler().fit(Xt); clf = mlp(42).fit(sc.transform(Xt), yt)
    p_full = clf.predict_proba(sc.transform(ho_X_full))[:, 1]
    shipped = np.array([r[f"{v}_score"] for r in ho])
    d = np.abs(p_full - shipped)
    ctl = {"mean_abs_delta": float(d.mean()), "max_abs_delta": float(d.max()),
           "corr": float(np.corrcoef(p_full, shipped)[0, 1]),
           "flips_at_0.85": int(((p_full >= 0.85) != (shipped >= 0.85)).sum()), "n": len(shipped)}
    print(f"  POSITIVE CONTROL refit@42 vs shipped {v}: mean|d|={ctl['mean_abs_delta']:.4f} "
          f"max|d|={ctl['max_abs_delta']:.4f} corr={ctl['corr']:.4f} "
          f"flips@0.85={ctl['flips_at_0.85']}/{ctl['n']}", flush=True)
    per_seed = []
    for s in SEEDS:
        sc = StandardScaler().fit(Xt); clf = mlp(s).fit(sc.transform(Xt), yt)
        p = clf.predict_proba(sc.transform(X_eval))[:, 1]
        m = {f"{th:.2f}": metrics(y_eval, p, th) for th in THRESHOLDS}
        per_seed.append(m)
        print("  seed %5d: " % s + " | ".join(
            f"th{th:.2f} rec {m[f'{th:.2f}']['recall']:.4f} spec {m[f'{th:.2f}']['specificity']:.4f}"
            for th in THRESHOLDS), flush=True)
    band = {f"{th:.2f}": {k: dict(
                mean=float(np.mean([ps[f"{th:.2f}"][k] for ps in per_seed])),
                min=float(np.min([ps[f"{th:.2f}"][k] for ps in per_seed])),
                max=float(np.max([ps[f"{th:.2f}"][k] for ps in per_seed])))
             for k in ("recall", "specificity", "precision")} for th in THRESHOLDS}
    res["versions"][v] = {"positive_control": ctl, "per_seed": per_seed, "band": band}

# ---- ordering stability, the actual question ----
print("\n=== ORDERING STABILITY (the question) ===", flush=True)
res["ordering"] = {}
for th in THRESHOLDS:
    k = f"{th:.2f}"
    orders = []
    for i, s in enumerate(SEEDS):
        r = {v: res["versions"][v]["per_seed"][i][k]["recall"] for v in ("v3","v4","v5")}
        orders.append(">".join(sorted(r, key=r.get, reverse=True)))
    uniq = {o: orders.count(o) for o in set(orders)}
    bands = {v: res["versions"][v]["band"][k]["recall"] for v in ("v3","v4","v5")}
    def overlap(a, b): return not (a["max"] < b["min"] or b["max"] < a["min"])
    pairs = {f"{a}_vs_{b}": overlap(bands[a], bands[b])
             for a, b in (("v3","v4"),("v4","v5"),("v3","v5"))}
    res["ordering"][k] = {"per_seed_orderings": orders, "counts": uniq,
                          "recall_bands": bands, "bands_overlap": pairs}
    print(f"  threshold {k}: orderings across seeds -> {uniq}")
    for v in ("v3","v4","v5"):
        print(f"    {v} recall {bands[v]['mean']:.4f} [{bands[v]['min']:.4f}-{bands[v]['max']:.4f}]")
    print(f"    bands overlap: {pairs}", flush=True)

json.dump(res, open(OUT, "w"), indent=1); print(f"\nwrote {OUT}", flush=True)
