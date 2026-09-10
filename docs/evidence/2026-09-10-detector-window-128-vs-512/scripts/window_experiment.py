#!/usr/bin/env python3
"""128 vs 512 token window for the frozen-mpnet pre-scorer detectors.

Arms differ ONLY in SentenceTransformer.max_seq_length. Same box, same venv, same
seeds, same hyperparameters as the shipped trainers -> the library/box terms that
CLAUDE.md warns about (ST-version skew, |0.16| on this exact detector) cancel.

Judged on RECALL + SPECIFICITY at the operating point (ADR-023), never MAE, and
across 5 seeds so a difference is only claimed when the bands separate.

Positive control: the shipped v5 pickle re-scored at 128 must reproduce the
recorded v5_score in heldout_v3v4v5_scored_2026-07-30.jsonl.
"""
import json, pickle, time, sys
from pathlib import Path
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import StratifiedKFold
from sentence_transformers import SentenceTransformer

EMBEDDER = "paraphrase-multilingual-mpnet-base-v2"
HIDDEN = (256, 128)
SEEDS = [42, 7, 13, 101, 2026]
WINDOWS = [128, 512]
ROOT = Path.home() / "llm-distillery"
OBIT = ROOT / "filters/common/obituary_detector"
VP = ROOT / "filters/common/violence_promotion"
OUT = Path.home() / "window_experiment_results.json"

def rows(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]

def text_of(r):
    return f"{r.get('title') or ''} {r.get('content') or ''}".strip()

def make_mlp(seed):
    return MLPClassifier(hidden_layer_sizes=HIDDEN, max_iter=400,
                         early_stopping=True, n_iter_no_change=15, random_state=seed)

def metrics(y, p, th):
    pred = (p >= th).astype(int)
    tp = int(((pred==1)&(y==1)).sum()); fp = int(((pred==1)&(y==0)).sum())
    fn = int(((pred==0)&(y==1)).sum()); tn = int(((pred==0)&(y==0)).sum())
    return dict(threshold=th, tp=tp, fp=fp, fn=fn, tn=tn,
                recall = tp/(tp+fn) if (tp+fn) else 0.0,
                specificity = tn/(tn+fp) if (tn+fp) else 0.0,
                precision = tp/(tp+fp) if (tp+fp) else 0.0)

def band(vals):
    return dict(mean=float(np.mean(vals)), min=float(np.min(vals)), max=float(np.max(vals)),
                sd=float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0)

print("loading embedder on cuda ...", flush=True)
model = SentenceTransformer(EMBEDDER, device="cuda")
tok = model.tokenizer
results = {"embedder": EMBEDDER, "seeds": SEEDS, "windows": WINDOWS, "hidden": list(HIDDEN)}

CACHE = Path.home() / "window_emb_cache"; CACHE.mkdir(exist_ok=True)
def embed(texts, W, bs=64, tag=None):
    f = CACHE / f"{tag}_{W}.npy" if tag else None
    if f is not None and f.exists():
        return np.load(f), 0.0
    model.max_seq_length = W
    t0 = time.perf_counter()
    X = np.asarray(model.encode(texts, batch_size=bs, show_progress_bar=False))
    dt = time.perf_counter() - t0
    if f is not None: np.save(f, X)
    return X, dt

def token_census(texts, name):
    n = [len(tok(t, add_special_tokens=False, truncation=False)["input_ids"]) for t in texts]
    n = np.array(n)
    c = {"n": len(n), "median_tokens": float(np.median(n)),
         "pct_over_128": float(100*(n>128).mean()), "pct_over_512": float(100*(n>512).mean()),
         "median_share_seen_at_128": float(np.median(np.minimum(1.0, 128/np.maximum(n,1)))),
         "median_share_seen_at_512": float(np.median(np.minimum(1.0, 512/np.maximum(n,1))))}
    print(f"  [{name}] {c}", flush=True)
    return c

# ============================ OBITUARY ============================
print("\n=== OBITUARY (train on v5_train_seed, evaluate on heldout) ===", flush=True)
tr = rows(OBIT/"training/data/v5_train_seed.jsonl")
ho = rows(OBIT/"validation/heldout_v3v4v5_scored_2026-07-30.jsonl")
tr_t = [text_of(r) for r in tr]; tr_y = np.array([1 if r["label"]=="positive" else 0 for r in tr])
ho_t = [text_of(r) for r in ho]; ho_y = np.array([1 if r["label"]=="positive" else 0 for r in ho])
print(f"train {len(tr)} ({tr_y.sum()} pos) | heldout {len(ho)} ({ho_y.sum()} pos, "
      f"{100*ho_y.mean():.1f}% positive rate)", flush=True)
results["obituary"] = {"n_train": len(tr), "n_heldout": len(ho),
                       "heldout_positive_rate": float(ho_y.mean())}
results["obituary"]["token_census_heldout"] = token_census(ho_t, "obit heldout")

emb = {}
for W in WINDOWS:
    X_tr, t_tr = embed(tr_t, W, tag='obit_train'); X_ho, t_ho = embed(ho_t, W, tag='obit_heldout')
    emb[W] = (X_tr, X_ho)
    print(f"  embedded @{W}: train {t_tr:.1f}s ({len(tr)/t_tr:.0f} rows/s), "
          f"heldout {t_ho:.1f}s ({len(ho)/t_ho:.0f} rows/s)", flush=True)

# --- POSITIVE CONTROL: shipped v5 pickle @128 vs recorded v5_score ---
rec = np.array([r["v5_score"] for r in ho])
sc5 = pickle.load(open(OBIT/"v5/models/scaler.pkl","rb"))
clf5 = pickle.load(open(OBIT/"v5/models/mlp_classifier.pkl","rb"))
repro = clf5.predict_proba(sc5.transform(emb[128][1]))[:,1]
d = np.abs(repro-rec)
flips = int(((repro>=0.85)!=(rec>=0.85)).sum())
results["positive_control"] = {"max_abs_delta": float(d.max()), "mean_abs_delta": float(d.mean()),
                               "verdict_flips_at_0.85": flips, "n": len(rec)}
print(f"\n  POSITIVE CONTROL shipped-v5 @128 vs recorded: mean|d|={d.mean():.6f} "
      f"max|d|={d.max():.6f} flips@0.85={flips}/{len(rec)}", flush=True)

for W in WINDOWS:
    X_tr, X_ho = emb[W]
    per_seed = []
    for s in SEEDS:
        sc = StandardScaler().fit(X_tr)
        clf = make_mlp(s).fit(sc.transform(X_tr), tr_y)
        p = clf.predict_proba(sc.transform(X_ho))[:,1]
        per_seed.append({f"{th:.2f}": metrics(ho_y, p, th) for th in (0.85, 0.90, 0.95)})
        print(f"  @{W} seed {s}: "
              + " | ".join(f"th{th:.2f} rec {per_seed[-1][f'{th:.2f}']['recall']:.4f} "
                           f"spec {per_seed[-1][f'{th:.2f}']['specificity']:.4f}"
                           for th in (0.85, 0.90, 0.95)), flush=True)
    agg = {}
    for th in ("0.85","0.90","0.95"):
        agg[th] = {m: band([ps[th][m] for ps in per_seed]) for m in ("recall","specificity","precision")}
    results["obituary"][f"window_{W}"] = {"per_seed": per_seed, "band": agg}

# ============================ VIOLENCE PROMOTION ============================
print("\n=== VIOLENCE PROMOTION (5-fold stratified OOF, the shipped protocol) ===", flush=True)
vr = [r for r in rows(VP/"training/training_scored.jsonl") if r.get("label") in ("positive","negative")]
v_t = [text_of(r) for r in vr]; v_y = np.array([1 if r["label"]=="positive" else 0 for r in vr])
print(f"  n={len(vr)} positives={int(v_y.sum())} ({100*v_y.mean():.1f}% positive rate)", flush=True)
results["violence_promotion"] = {"n": len(vr), "positive_rate": float(v_y.mean())}
results["violence_promotion"]["token_census"] = token_census(v_t, "violence corpus")

for W in WINDOWS:
    Xv, tv = embed(v_t, W, tag='violence')
    print(f"  embedded @{W}: {tv:.1f}s ({len(v_t)/tv:.0f} rows/s)", flush=True)
    per_seed = []
    for s in SEEDS:
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=s)
        oof = np.zeros(len(v_y))
        for trn, tst in skf.split(Xv, v_y):
            sc = StandardScaler().fit(Xv[trn])
            clf = make_mlp(s).fit(sc.transform(Xv[trn]), v_y[trn])
            oof[tst] = clf.predict_proba(sc.transform(Xv[tst]))[:,1]
        per_seed.append({f"{th:.2f}": metrics(v_y, oof, th) for th in (0.90, 0.95)})
        print(f"  @{W} seed {s}: "
              + " | ".join(f"th{th:.2f} rec {per_seed[-1][f'{th:.2f}']['recall']:.4f} "
                           f"spec {per_seed[-1][f'{th:.2f}']['specificity']:.4f} "
                           f"prec {per_seed[-1][f'{th:.2f}']['precision']:.4f}"
                           for th in (0.90, 0.95)), flush=True)
    agg = {}
    for th in ("0.90","0.95"):
        agg[th] = {m: band([ps[th][m] for ps in per_seed]) for m in ("recall","specificity","precision")}
    results["violence_promotion"][f"window_{W}"] = {"per_seed": per_seed, "band": agg}

json.dump(results, open(OUT,"w"), indent=1)
print(f"\nwrote {OUT}", flush=True)
